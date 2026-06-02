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

本框架的核心思想是：**主模型负责调度和判断，subagent 负责分工处理，Python 负责确定性检查（25 个脚本），状态文件负责长期记忆。** v0.2.0 在 v0.1.0 基础上新增了上下文编译、确定性门禁、知识库索引、文风分析、角色漂移检测、文风拆解、共创模式辅助和 Python 环境降级方案。

## 2. 系统架构

```text
用户 (自然语言命令)
  ↓
第三层：平台适配层
  ├─ CLAUDE.md / AGENTS.md — 平台入口（核心路由）
  ├─ .claude/skills/ + .agents/skills/ — 原生 Skills 入口
  └─ .codex/ — Codex Agent + hooks
  ↓
第二层：确定性脚本层 (平台无关)
  ├─ relevance_resolver.py — 精确上下文注入（替代 context_builder 核心）
  ├─ ledger_manager.py + render_views.py — 结构化账本 + 可读视图
  ├─ director_sheet.py — 章节导演表
  ├─ gatekeeper.py — 确定性门禁
  └─ 其余 18 个脚本 — 体检、索引、审计、文风、迁移
  ↓
第一层：小说项目核心数据层 (平台无关)
  ├─ chapters/ + story/outline/ — 正式正文与大纲 (canonical)
  ├─ story/ledger/ — 结构化事实账本 (JSONL, 7类)
  ├─ story/views/ — 作者可读 Markdown 视图
  ├─ story/plans/ — 章节导演表 (YAML)
  ├─ story/roles/ — 角色卡 (canonical)
  ├─ story/runtime/ — 临时任务包与审阅结果 (working)
  └─ story/state/ — JSON 状态镜像
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

25 个 Python 脚本不参与创作判断，只做确定性工作：

- 文件完整性、JSON 合法性、frontmatter 格式检查（doctor.py）
- 章节索引生成（chapter_index.py）
- 项目状态概览与漂移风险（status.py）
- 文本格式和风险词扫描（text_audit.py）
- hook 半衰期和依赖检查（hook_report.py / hook_matrix.py）
- 结构覆盖关系检查（structure_report.py）
- skill 注册表检查（skill_check.py）
- 按 Agent 构建上下文包（context_builder.py）
- 三层 prompt 编译（prompt_compiler.py）
- 确定性门禁检查（gatekeeper.py）
- 知识库索引与查询（knowledge_index.py）
- 定量文风报告（style_report.py）
- 角色漂移预警（character_drift_report.py）
- 文风拆解器（decompose_style.py）
- InkOS 项目迁移（import_inkos_project.py）
- 共创模式简报生成（review_author_chapter.py / polish_author_chapter.py）

## 3. 目录结构

```text
CLAUDE.md / AGENTS.md     Claude Code / Codex 入口协议（核心路由）
START_HERE.md             给 AI 的简短启动指令
RUN_RULES.md              Python 辅助脚本运行门禁
PROJECT_INTRO.md          本项目介绍

workflow/                 系统原则与章节生命周期
.claude/agents/           Claude Code subagent 注册（薄路由层）
.claude/skills/           Claude Code 原生 Skills 入口
.agents/skills/           Codex 原生 Skills 入口
.codex/                   Codex Agent 注册 + hooks.json
agents/                   各 Agent 详细职责 prompt
chapters/                 正文章节目录
scripts/                  25 个 Python 辅助脚本
skills/                   可插拔 skill 接口和注册表（正式来源）
story/                    大纲、状态、风格、伏笔、runtime 工作区
  ledger/                 结构化事实账本（JSONL，7 类）
  views/                  作者可读 Markdown 视图
  plans/                  章节导演表（YAML）
tests/                    回归测试
```

## 4. 启动方式

推荐做法：

1. 在模板目录运行 `python scripts/create_project.py "新书名"`。
2. 进入生成的新书目录。
3. 从新书目录根部启动 Claude Code。
4. 让 AI 先读取 `START_HERE.md` 和 `CLAUDE.md`。
5. 如可用，先调用 `project-librarian` 生成 Context Packet。
6. 如果是新项目，对 AI 说：`搭建大纲`。
7. 大纲完成后运行：

```bash
python scripts/doctor.py
python scripts/structure_report.py
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
主会话: Python 环境检测 + drift check + intent + plan
  ↓
context_builder + prompt_compiler → 上下文包 + 编译 prompt
  ↓
novel-writer / Writer → 草稿
  ↓
novel-polish / Polish → 润色稿
  ↓
novel-review / Review → 审阅报告（含人格一致性检查）
  ↓
novel-fixer / Fixer → 修复稿
  ↓
gatekeeper → 确定性门禁（必须通过）
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

### 查看已注册的 Subagent 与分配模型

Claude Code 和 Codex CLI 会自动发现 `.claude/agents/` 中的 subagent 注册文件。你可以通过主会话查询当前可用的 subagent 列表，并根据需要为不同 Agent 分配不同模型。

**查询已注册的 subagent：**

```text
你: 当前项目有哪些可用的 subagent？列出它们的名称和职责。

AI: 当前注册了 5 个 subagent：

| Subagent | 类型 | 职责 | 会话模型 |
|---|---|---|---|
| project-librarian | 上下文路由 | 读取规则和状态，生成 Context Packet | 一次性 |
| novel-writer | Writer 阶段 | 写原始草稿 | 持久 |
| novel-polish | Polish 阶段 | 去 AI 味、校准文风 | 持久 |
| novel-review | Review 阶段 | 审阅，找 bug 和漂移 | 持久 |
| novel-fixer | Fixer 阶段 | 按 Review 报告修复 | 持久 |
```

**为不同 Agent 分配不同模型：**

Claude Code 支持按 subagent 分配模型。例如在 `.claude/settings.json` 中：

```json
{
  "permissions": {
    "allow": ["Bash(python scripts/*)"]
  }
}
```

或在对话中直接指定：

```text
你: 写第 3 章时，Writer 用速度更快的模型节省成本，Review 用精度更高的模型保证审阅质量

AI: 好的。已记录：Writer → 快速模型，Review → 高精度模型。
      Writer 草稿生成更经济高效；
      Review 审阅检查更全面细致。
```

这样可以为不同阶段选择不同性价比的模型——起草阶段用快速模型，审阅阶段用高精度模型。

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

- `story/runtime/*.writer.md` / `.polish.md` / `.review.md` / `.fixer.md`
- `story/runtime/*.intent.md` / `.plan.md`
- `story/runtime/*.context.md` / `.prompt.md` / `.gatekeeper.md`
- `story/runtime/*.knowledge_packet.md` / `.style_report.md` / `.character_drift.md`
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

脚本位于 `scripts/`，共 25 个，分为八组：

| 组 | 脚本 |
|---|---|
| 体检与索引 | `doctor.py` / `chapter_index.py` / `status.py` |
| Hook 审计 | `hook_report.py` / `hook_matrix.py` |
| 上下文引擎 | `relevance_resolver.py` / `context_builder.py` / `prompt_compiler.py` / `gatekeeper.py` |
| 账本与视图 | `ledger_manager.py` / `render_views.py` |
| 章节统筹 | `director_sheet.py` |
| 平台适配 | `sync_skills.py` |
| 文风与角色 | `style_report.py` / `character_drift_report.py` / `decompose_style.py` / `text_audit.py` |
| 知识与迁移 | `knowledge_index.py` / `import_inkos_project.py` / `structure_report.py` / `skill_check.py` |
| 共创辅助 | `review_author_chapter.py` / `polish_author_chapter.py` / `create_project.py` |

脚本只做确定性辅助，不做创作判断。所有脚本不调用 AI 模型、不自动改写正文。

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

- 文笔上限仍然受模型能力限制。框架通过负面清单和 Polish 层约束下限，但文学品质取决于底层模型。
- 主会话仍需认真执行规则。gatekeeper 能堵住流程漏洞，但无法替代主会话的创作判断。
- Python 脚本只做确定性检查，不做语义判断。gatekeeper 通过不代表章节合格。
- 知识库第一版基于关键词和元数据，不支持语义检索。
- 没有真正后台自动调度器，调度由主模型通过 CLAUDE.md 协议完成。
- 无 Python 环境时需 AI 手动执行等效检查，可靠性略低于脚本。
- 状态文件较多，适合中长篇，不适合极轻量任务。

## 15. 推荐工作方式

最推荐的实际使用节奏：

```text
搭建大纲 / 导入现成大纲
  ↓
doctor + structure_report
  ↓
规划第1章
  ↓
hook_report + hook_matrix
  ↓
context_builder + prompt_compiler（为 Agent 编译上下文和 prompt）
  ↓
Writer → Polish → Review → Fixer
  ↓
gatekeeper（必须通过）
  ↓
text_audit + final-check
  ↓
写入 chapters
  ↓
chapter_index --write + doctor
```

批量写作时，每章仍然要按顺序提交 canonical 状态，不能先写完多章再统一补状态。共创模式下，作者手写章节后可通过 `审查第N章` 或 `润色第N章 --模式` 调用 AI 辅助。

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
