# Narrative Workbench / 叙事工作台项目介绍

## 1. 项目定位

`narrative_workbench` 受 [InkOS](https://github.com/Narcooo/inkos)（AGPL-3.0）多 Agent 小说生产系统启发，独立构建为面向 Claude Code 与 Codex CLI 的 Markdown-native prompt 工程框架。它是一个在不同平台上重新构想小说写作工作流工程的独立框架。目标是在 AI 参与长篇创作时解决以下问题：

- 大纲容易漂移。
- 角色弧光容易断。
- 伏笔开了不回收。
- AI 写作容易出现作文腔、主题金句、万能氛围句。
- 多章节批量写作时状态文件不同步。
- 每次启动都要读取大量规则，上下文成本高。
- Writer / Polish / Review / Fixer 职责混乱。
- Claude Code subagent、Python 检查脚本、skills 扩展之间缺少统一接口。

本框架的核心思想是：**主模型负责调度和判断，subagent 负责分工处理，Python 负责确定性检查，状态文件负责长期记忆。**

## 2. 系统架构

```text
用户
  ↓
主模型 / 主会话
  ├─ 读取 CLAUDE.md / RUN_RULES.md / system_protocol.md
  ├─ 调用 Project Librarian 生成 Context Packet
  ├─ 搭建大纲
  ├─ 调度四 Agent
  ├─ 运行 Python 辅助脚本
  ├─ final-check
  └─ 提交 canonical 状态
        ↓
Writer → Polish → Review → Fixer
        ↓
story/runtime/ working 文件
        ↓
chapters/ + story/*.md + story/state/*.json
```

### 主模型职责

- 和用户确认创作方向。
- 搭建大纲、分卷、角色卡。
- 规划章节 intent / plan。
- 调用 Writer / Polish / Review / Fixer。
- 判断 Review 是否需要 Fixer 或重写。
- 通过 final-check 后写入正文。
- 同步 Markdown 状态和 JSON 镜像。

### Subagent 职责

- Project Librarian：一次性会话，只做上下文路由，生成 Context Packet。
- Writer / Polish / Review / Fixer：持久会话，首次创建后在同一主会话内持续存活，跨章积累经验。主会话通过 intent/plan 驱动，Agent 不自行重复分析基线文件。连续处理超 8 章后主会话主动重置。
- Writer：只写草稿。
- Polish：只做语言层面的去 AI 味和文风修正。
- Review：只审阅，不改正文。对照角色卡 Personality Lock、Behavioral Constraints 和压力测试结论检查角色行为一致性。
- Fixer：只根据 Review Report 修复。

### Python 职责

Python 不参与创作判断，只做：

- 文件完整性检查。
- JSON 合法性检查。
- 章节索引生成。
- 文本格式和风险词扫描。
- hook 半衰期和依赖检查。
- 结构覆盖关系检查。
- skill 注册表检查。

## 3. 目录结构

```text
CLAUDE.md              主启动协议
START_HERE.md          给 AI 的简短启动指令
RUN_RULES.md           Python 辅助脚本运行门禁
PROJECT_INTRO.md       本项目介绍
SYSTEM_AUDIT.md        系统论审计记录

.claude/agents/        Claude Code 可发现的 subagent 注册文件
agents/                Project Librarian 与四 Agent 的详细职责提示词
chapters/              正文章节目录
scripts/               Python 辅助脚本
skills/                可插拔 skill 接口和注册表
story/                 大纲、状态、风格、伏笔、runtime 工作区
```

## 4. 启动方式

推荐做法：

1. 在模板目录运行 `python3 scripts/create_project.py "新书名"`。
2. 进入生成的新书目录。
3. 从新书目录根部启动 Claude Code。
4. 让 AI 先读取 `START_HERE.md` 和 `CLAUDE.md`。
5. 如可用，先调用 `project-librarian` 生成 Context Packet。
6. 如果是新项目，对 AI 说：`搭建大纲`。
7. 大纲完成后运行：

```bash
python3 scripts/doctor.py
python3 scripts/structure_report.py
```

8. 然后开始：

```text
写第1章
继续下一章
写接下来5章
审阅第N章
```

## 5. 大纲搭建流程

大纲搭建由 `CLAUDE.md` 和 `story/outline/_template.discovery.md` 控制。AI 会分阶段确认：

1. 故事内核：主题、基调、主角弧线、全书 Objective。
2. 前台 / 后台双层结构：明面冲突和隐藏真相如何咬合。
3. 分卷设计：每卷 Objective、KR、情绪曲线、卷尾不可逆改变。
4. 角色设计：四轮深入讨论（核心人格 → 人格压力测试 → 关系性格张力 → 声音与表达），产出的角色卡包含 Personality Lock、Behavioral Constraints 和压力测试结论，供写作和审阅阶段校验角色行为一致性。
5. 世界观铁律与禁令：不能违反的设定、类型边界、视角规则。

输出主要写入：

- `story/brief.md`
- `story/author_intent.md`
- `story/outline/story_frame.md`
- `story/outline/volume_map.md`
- `story/book_rules.md`
- `story/roles/*.md`
- `story/current_focus.md`

如果用户已有现成大纲，使用 `story/outline/_template.import-outline.md` 进入“导入现成大纲”流程。导入时，用户大纲默认是 candidate；只有用户确认的内容才进入 canonical 文件。伏笔在导入阶段通常先作为 hook candidate 记录，不直接进入 `pending_hooks.md`。

## 6. Project Librarian 与四 Agent 写作流水线

`project-librarian` 是写作前的上下文入口 agent（一次性会话）。它读取规则、状态、伏笔、分卷图和当前任务，输出 Context Packet。Context Packet 可以替代 current_state、chapter_summaries、current_focus、RUN_RULES 的读取，但不能替代系统协议和结构文件。Packet 与原文冲突时以原文为准。

它不是事实源，不写正文，不修改状态，不替代主会话判断。

单章写作流程：

```text
project-librarian / Context Packet
  ↓
主会话创建 intent + plan
  ↓
novel-writer / Writer
  ↓
novel-polish / Polish
  ↓
novel-review / Review
  ↓
novel-fixer / Fixer
  ↓
主会话 final-check
  ↓
写入 chapters/
  ↓
同步 story 状态
```

项目级 Claude Code subagent 位于：

```text
.claude/agents/project-librarian.md
.claude/agents/novel-writer.md
.claude/agents/novel-polish.md
.claude/agents/novel-review.md
.claude/agents/novel-fixer.md
```

详细职责说明位于：

```text
agents/project-librarian.md
agents/writer.md
agents/polish.md
agents/review.md
agents/fixer.md
```

## 7. Canonical 与 Working 边界

本框架严格区分 canonical 区和 working 区。

### Canonical 区

只有主会话通过 final-check 后可以更新：

- `chapters/*.md`
- `chapters/index.json`
- `story/current_state.md`
- `story/chapter_summaries.md`
- `story/pending_hooks.md`
- `story/emotional_arcs.md`
- `story/current_focus.md`
- `story/state/*.json`

### Working 区

Agent 和 skill 的输出只能进入：

- `story/runtime/*.writer.md`
- `story/runtime/*.polish.md`
- `story/runtime/*.review.md`
- `story/runtime/*.fixer.md`
- `story/runtime/*.skill-*.md`
- `story/runtime/*.final-check.md`

这样可以防止 Agent 直接污染正文事实源。

## 8. Hook 伏笔系统

Hook 系统由以下文件控制：

- `story/hook_protocol.md`
- `story/pending_hooks.md`
- `scripts/hook_report.py`
- `scripts/hook_matrix.py`

Hook 生命周期：

```text
candidate → open → progressing → escalated → resolved / dormant / dropped
```

核心规则：

- candidate 只是计划，不能进入伏笔池。
- open / advance / resolve 必须有正文证据。
- 活跃 hook 建议不超过 15 条。
- core hook 建议不超过 5 条。
- 每个 hook 有半衰期，过期必须 advance / defer / resolve / dormant / dropped。
- hook 依赖关系由 `hook_matrix.py` 辅助检查。

## 9. 文笔控制层

本框架承认文笔上限主要依赖模型能力，因此使用“约束 + 样本 + 场景施工”降低 AI 腔。

主要文件：

- `story/style_guide.md`
- `story/style_profile.md`
- `story/style_blacklist.md`
- `story/fiction_style_skill.md`
- `story/ai_writing_repair_plan.md`
- `story/style_samples/`
- `story/runtime/_template.scene-beat.md`

### style_blacklist.md

禁止：

- 抽象情绪总结。
- 主题金句。
- 万能氛围句。
- 机械句式。
- 对白同质化。
- 润色阶段乱改事实。

### scene-beat

关键场景写作前，可拆成：

- 场景目标。
- 角色欲望与阻力。
- 对白策略。
- 动作锚点。
- 情绪外化。
- 信息边界。
- hook 操作。
- 段尾落点。

这让模型少自由发挥，多按镜头施工。

## 10. Python 辅助脚本

所有运行规则集中在：

- `RUN_RULES.md`

脚本位于：

```text
scripts/doctor.py
scripts/chapter_index.py
scripts/text_audit.py
scripts/hook_report.py
scripts/hook_matrix.py
scripts/structure_report.py
scripts/skill_check.py
```

常用命令：

```bash
python3 scripts/doctor.py
python3 scripts/chapter_index.py --check
python3 scripts/chapter_index.py --write
python3 scripts/text_audit.py chapters/0001_标题.md
python3 scripts/hook_report.py --current 12
python3 scripts/hook_matrix.py --current 12
python3 scripts/structure_report.py
python3 scripts/skill_check.py
```

脚本只做确定性辅助，不做创作判断。

## 11. Skill 接口

Skill 接口位于：

```text
skills/
```

核心文件：

- `skills/skill_protocol.md`
- `skills/skill_registry.md`
- `skills/_template.skill-entry.md`
- `skills/_template.skill-request.md`

使用方式：

```text
用户点名 skill
  ↓
主会话检查 skill_registry
  ↓
未注册则先注册
  ↓
运行 scripts/skill_check.py
  ↓
创建 skill request
  ↓
skill 输出进入 story/runtime/
  ↓
final-check 决定是否采纳
```

Skill 不直接改 canonical 状态。

## 12. 适合的项目

适合：

- 长篇小说。
- 多卷结构。
- 伏笔密集。
- 群像或多关系线。
- 需要多阶段润色和审阅。
- 需要 Claude Code subagent 协作。
- 需要长期维护状态账本。

不太适合：

- 很短的短篇。
- 只想随手生成一章爽文。
- 不想维护状态文件。
- 不需要伏笔和结构管理的轻量项目。

## 13. 主要优势

- 长篇连续性更强。
- 伏笔可追踪。
- 角色弧光有账本。
- Agent 分工清楚。
- 状态污染风险低。
- Claude Code 可识别 subagent。
- Python 可辅助检查结构和格式。
- Skill 可扩展。
- 文风有负面清单和 scene-beat 控制。

## 14. 剩余限制

- 文笔上限仍然受模型能力限制。
- 主会话仍需认真执行规则。
- Python 不能替代语义判断。
- 没有真正后台自动调度器，调度由主模型完成。
- 状态文件较多，适合中长篇，不适合极轻量任务。

## 15. 推荐工作方式

最推荐的实际使用节奏：

```text
搭建大纲
  ↓
doctor + structure_report
  ↓
规划第1章
  ↓
hook_report + hook_matrix
  ↓
Writer
  ↓
Polish
  ↓
Review
  ↓
Fixer
  ↓
text_audit + final-check
  ↓
写入 chapters
  ↓
chapter_index --write
  ↓
doctor
```

批量写作时，每章仍然要按顺序提交 canonical 状态，不能先写完多章再统一补状态。

## 16. Lineage & Attribution

本框架受 [InkOS](https://github.com/Narcooo/inkos)（AGPL-3.0）启发。InkOS 首创了多 Agent 小说生产流水线、真相文件状态管理、hook 生命周期追踪和去 AI 味机制等核心方法论。

Narrative Workbench 将这些模式独立重新实现为面向 Claude Code/Codex CLI 的 Markdown-native prompt 工程框架。关键差异：

- **平台：** Claude Code subagent + Markdown prompt vs InkOS 的 TypeScript CLI + npm 包
- **Agent 架构：** 5 个持久会话 Agent（Writer/Polish/Review/Fixer + Project Librarian）vs InkOS 的 10 个 Agent 三阶段流水线
- **持久会话模型：** Agent 跨章存活、8 章重置阈值
- **角色设计：** 四轮深入讨论协议 + 人格压力测试
- **上下文控制：** Context Packet 替代规则 + runtime 跨卷归档
- **状态机：** 10 状态完整覆盖 + needs-rewrite/needs-repair 失败回路

状态文件命名约定（`current_state.md`、`pending_hooks.md` 等）遵循 InkOS 普及的组织模式，作为兼容性设计。

详见 [ORIGIN.md](ORIGIN.md)。
