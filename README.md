# Narrative Workbench / 叙事工作台

面向 Claude Code 与 Codex CLI 的长篇 AI 小说工程框架——不是手动工具台，而是一套自主调度 Agent、管理项目状态、追踪伏笔生命周期、校验流程完整性的写作工程系统。

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Claude%20Code%20%7C%20Codex%20CLI-green)

## 起源与定位

本项目受 **[InkOS](https://github.com/Narcooo/inkos)**（AGPL-3.0）启发——InkOS 首创了多 Agent 小说生产流水线、真相文件状态管理和 hook 生命周期追踪的方法论。Narrative Workbench 将这些模式重新构想为面向 Claude Code 与 Codex CLI 的 Markdown-native prompt 工程框架。

|  | InkOS | Narrative Workbench |
|---|---|---|
| **平台** | TypeScript CLI（npm 包） | Claude Code / Codex CLI prompt 框架 |
| **Agent 模型** | 10 Agent，3 阶段 | 5 Agent，4 阶段 + 持久会话 |
| **状态后端** | Markdown + SQLite + Zod | Markdown 账本 + JSON 镜像 + Python |
| **会话** | 无状态（每章新调用） | 持久会话（Agent 跨章存活） |
| **控制方式** | CLI 命令 | 主会话编排 + Claude Code subagent |

状态文件命名约定（`current_state.md`、`pending_hooks.md` 等）保持与 InkOS 兼容。详见 [ORIGIN.md](ORIGIN.md)。

> 本项目不是 InkOS 官方项目，也未获得 InkOS 作者背书或维护。"InkOS"名称仅用于说明灵感来源、致谢与兼容性描述。

## 核心特性

- **四 Agent 持久会话：** Writer / Polish / Review / Fixer 在同一主会话内跨章存活，首次创建后无需每章重复发送项目基线。连续处理超 8 章自动重置。
- **角色四轮设计协议：** 核心人格 → 压力测试 → 关系张力 → 声音表达，产出 Personality Lock 和 Behavioral Constraints，贯穿写作、审阅、审计全链路。
- **上下文控制：** Project Librarian 生成 Context Packet，区分可跳过/必须读原文的文件。runtime 跨卷自动归档。
- **完整状态机：** 10 状态章节生命周期，含 `needs-rewrite` 和 `needs-repair` 显式失败回路。
- **Hook 伏笔系统：** open / advance / escalate / resolve / defer 全生命周期 + 半衰期防遗忘 + 活跃预算控制。
- **去 AI 味管线：** style_blacklist 负面清单 + scene-beat 场景拆解 + Polish 润色层。
- **Skill 可插拔扩展 + Python 辅助体检：** 注册制 skill 系统 + 19 个确定性检查脚本（上下文工程、流程门禁、知识索引、文风分析、漂移检测、文风拆解、项目迁移）。

## 快速开始

四步启动，上下两行分别展示终端命令和你对 AI 说的话：

```text
$ python3 scripts/create_project.py "临安雪"     # 步骤1：创建新书目录
$ cd 临安雪 && claude                             # 步骤2：进入目录，启动 Claude Code
```

```text
你: 这是一个 AI 小说项目。请读取 CLAUDE.md 然后按"会话启动"顺序读取上下文文件。
    如果你有 Python 3，可以使用辅助脚本做确定性检查。

AI: 好的。我先确认——你已安装 Python 3 吗？是否使用脚本？

你: 已安装，使用脚本。

AI: [读取 CLAUDE.md → RUN_RULES.md → system_protocol.md → ...]
    上下文加载完成。当前项目是全新的，尚未搭建大纲。
    要开始搭建大纲吗？
```

```text
$ # 步骤3：搭建大纲（终端无操作，全部通过对话完成）
```

```text
你: 搭建大纲

AI: 好的。先确认基础定位——这本书一句话讲什么？

你: 南宋绍兴年间，一个精通医术的女子为躲避金兵追杀，
    伪装身份混入太医院，却卷入了宫廷内部的权力斗争。

AI: [五阶段推进：故事内核 → 前台/后台结构 → 分卷设计 →
    角色设计（四轮讨论）→ 世界观铁律]
    大纲搭建完成。产出 story_frame.md、volume_map.md、
    book_rules.md、角色卡、character_matrix.md。
    要开始写第 1 章吗？
```

```text
$ python3 scripts/doctor.py                        # 步骤4：体检后开始写作
$ python3 scripts/structure_report.py
```

```text
你: 写第1章

AI: [drift check] → [创建 intent/plan] →
    [Writer] 草稿 → [Polish] 润色 → [Review] 审阅 → [Fixer] 修复 →
    [gatekeeper 通过] → [final-check 通过] →
    第 1 章已写入 chapters/0001_临安雪.md

你: 继续下一章        # 复用持久 Agent，无需重发基线
你: 写接下来5章       # 流水线重叠，批末 audit
你: 继续              # 持续写作，跨卷自动归档
```

已有大纲时，将步骤 3 的 `搭建大纲` 替换为 `导入现成大纲`。

## 用户命令

| 命令 | 说明 |
|---|---|
| `搭建大纲` | 五阶段从零搭建新书设定 |
| `导入现成大纲` | 拆解已有大纲为 canon / candidate / 缺口，主动检测缺失信息 |
| `深化角色 <角色名>` | 对已有角色按四轮协议补全人格深度 |
| `规划第 N 章` | 仅创建 intent 与 plan，不启动 Agent |
| `写第 N 章` | 完整流水线：drift check → 四 Agent → final-check → 状态同步 |
| `继续下一章` | 自动确定下一章号并执行完整流水线 |
| `写接下来 3-5 章` | 批量流水线，单批最多 5 章 |
| `审阅第 N 章` | 根据章节当前状态从适当阶段切入返修 |
| `审查第 N 章` | 对作者手写章节进行一致性审查，不改正文 |
| `润色第 N 章 --模式` | 按指定模式润色手写稿（5 种模式可选） |
| `第 N 章写作简报` | 生成本章写作约束简报（必须处理/禁止/推荐写法） |

## 四 Agent 写作流水线

每章的写作由四个 Agent 串行接力，主会话统一调度：

```
主会话: drift check → intent + plan
  ↓
Writer（原始草稿）
  只管情节、角色、节奏。不润色，不审稿。
  输出: chapter-000N.writer.md + handoff 摘要
  ↓
Polish（语言二修）
  去 AI 味、校准文风、修正格式。不改变情节和事实。
  输出: chapter-000N.polish.md + handoff 摘要
  ↓
Review（审阅报告）
  检查连续性、信息边界、hook 账、人格一致性、文风。只出报告不改文。
  输出: chapter-000N.review.md
  ↓ Fixer（按报告修复）
  只修 Review 指出的问题，不自由发挥。
  输出: chapter-000N.fixer.md
  ↓
主会话: final-check → 写入 chapters/ → 同步状态
```

**持久会话：** Writer / Polish / Review / Fixer 首次创建后在同一主会话内持续存活。后续章节无需重复发送项目基线（规则、角色卡、大纲）——主会话每次只发送本章驱动文件（intent + plan + 上一章正文 + 出场角色卡）。

**失败处理：** Review 判定结构性失败 → `needs-rewrite`，Review 报告发回 Writer 重写。final-check 未通过 → `needs-repair`，final-check 报告发回 Fixer 重新修复。任何状态倒退必须写明原因。

**批量流水线：** 同一章内严格串行。多章批量时，Writer 完成 ChN 后立即收到 ChN+1 任务，同时 Polish 正在处理 ChN——不同章节的 Agent 阶段可流水线重叠。

## Skill 扩展机制

Skill 是可插拔的专项能力模块，用于扩展写作流水线的特定环节。适用场景：特定题材知识（如医学考据、古代官制）、专项文风规则、章节审校清单、战斗/悬疑/恋爱等专项构造。

**注册与调用：**

```
用户点名 skill 或 plan 声明需要
  ↓
主会话检查 skills/skill_registry.md → 已注册？→ 读取入口说明 → 创建 skill request
                                        ↓ 未注册
                                   按模板登记到 registry →
                                   运行 skill_check.py 验证 →
                                   创建 skill request
  ↓
skill 输出进入 story/runtime/chapter-000N.skill-SKILLNAME.md
  ↓
主会话 final-check 时决定采纳/拒绝
```

**边界：** skill 不直接改正文和 canonical 状态。skill 输出与项目禁令冲突时，以项目禁令为准。

## 共创模式

在"AI 全流程写作"之外，v0.2.0 新增了"作者手写 + AI 辅助"的共创模式，面向有写作能力、需要工程化辅助的作者。三种指令覆盖了写作前、写作后和修改阶段：

```
写作前：第 N 章写作简报
  ↓  系统根据该章在卷纲中的位置和当前项目状态，生成约束简报——
  ↓  本章类型、必须推进的伏笔、禁止泄露的信息、推荐写法。
  ↓  不是替作者写，而是告诉作者这一章承担什么功能。

写作后：审查第 N 章
  ↓  Review Agent 对作者手写章节进行一致性审查。
  ↓  不改正文，只出问题清单：角色人格违背、伏笔遗漏、秘密泄露风险、
  ↓  状态冲突、节奏失衡、AI 味。每条标注位置和修改方向。

修改时：润色第 N 章 --模式 <模式名>
  ↓  5 种润色模式，默认不覆盖原稿，所有改动标注位置和原因。
```

| 润色模式 | 说明 |
|---|---|
| `preserve-author-style` / `light` | 只改病句、重复、节奏，最大保留作者表达 |
| `project-style-align` / `style` | 按项目文风 profile 对齐句长、对白密度、段落形态 |
| `anti-ai-only` / `anti-ai` | 只去 AI 味：模板感、解释感、抽象情绪词 |
| `dialogue-only` / `dialogue` | 只修对白，让角色声音与角色卡的对白风味对齐 |
| `rhythm-only` / `rhythm` | 只调节奏：段落长短、高压喘息比例、章尾落点 |

## Python 辅助脚本

### 环境检测

每次会话启动时，AI 会首先询问你的 Python 环境状态。两种模式功能完整：

| 模式 | 说明 |
|---|---|
| **有 Python 3 环境** | 19 个脚本负责文件完整性、JSON 合法性、hook 半衰期、文本审计等确定性检查，AI 负责创作判断 |
| **无 Python 或不使用** | AI 手动执行等效检查（逐项验证文件、计算半衰期、扫描禁止模式等），产物标注 `(manual)`，功能完整但可靠性略低于脚本 |

### 脚本分类

19 个 Python 脚本按功能分为五组：

| 类别 | 脚本 | 说明 |
|---|---|---|
| **体检与索引** | `doctor.py` / `chapter_index.py` / `status.py` | 项目健康检查、章节索引生成、项目状态概览 |
| **Hook 审计** | `hook_report.py` / `hook_matrix.py` | 活跃 hook 预算、半衰期到期、依赖环检测 |
| **上下文与门禁** | `context_builder.py` / `prompt_compiler.py` / `gatekeeper.py` | 按 Agent 构建上下文包、三层 prompt 编译、确定性门禁检查 |
| **文风与角色** | `style_report.py` / `character_drift_report.py` / `decompose_style.py` / `text_audit.py` | 句长/对白密度分析、角色漂移预警、文风拆解、文本审计 |
| **知识与迁移** | `knowledge_index.py` / `import_inkos_project.py` / `structure_report.py` / `skill_check.py` | 项目知识索引、InkOS 项目迁移、结构覆盖检查、Skill 注册校验 |
| **共创辅助** | `review_author_chapter.py` / `polish_author_chapter.py` / `create_project.py` | 手写稿审查简报、手写稿润色简报、新项目创建 |

运行门禁见 `RUN_RULES.md`。详细说明见 [`scripts/README.md`](scripts/README.md)。

## 知识库系统

知识库用于储存小说所需的专业领域知识——医学考据、古代官制、武术流派、历史细节等。这些内容不属于"本书设定"而属于"现实世界知识"，不适合塞进角色卡或世界观铁律。

### 构建索引

```bash
python3 scripts/knowledge_index.py build
```

扫描项目文件（角色卡、大纲、章节、伏笔池），提取实体和文件元数据，生成 `.nw_index/entity_index.json`。

### 查询与生成知识包

按章节生成知识包（供 context_builder 和 prompt_compiler 使用）：

```bash
python3 scripts/knowledge_index.py query --chapter 12 --agent writer
```

按领域和关键词查询：

```bash
python3 scripts/knowledge_index.py query --domain 中医方剂 --keyword 金疮药
```

### 知识库与 Skill 的关系

知识库是领域事实的单一权威来源。Skill 是纯方法论层——它描述"怎么检查"但不拥有"用来检查的事实"。Skill 运行时通过 `knowledge_index.py --query` 获取相关事实，校验报告的每条建议都引用知识库条目编号。设计原则：**知识库是图书馆，Skill 是研究员。研究员可以查资料，但不能自己编资料。**

## 目录结构

```text
CLAUDE.md / START_HERE.md / RUN_RULES.md    启动协议、启动指令、脚本门禁
PROJECT_INTRO.md / ORIGIN.md / LICENSE       项目介绍、起源致谢、AGPL-3.0

.claude/agents/    Claude Code subagent 注册（薄路由层）
agents/            各 Agent 详细职责 prompt
story/
  outline/         故事框架、分卷地图、扩写蓝图
  runtime/         每章 intent/plan + Agent 产出 + 批量 audit
  roles/           角色卡（含 Personality Lock、压力测试）
  state/           JSON 状态镜像
  style_samples/   用户风格样本
  *.md             状态账本与风格规则（19 个文件）
skills/            可插拔 skill 接口与注册表
scripts/           19 个 Python 确定性辅助脚本
chapters/          正文章节（000N_标题.md）
```

## 使用示例

### 从零搭建到持续创作

```text
用户: 搭建大纲

AI:   好的。先确认基础定位——
      这本书一句话讲什么？

用户: 南宋绍兴年间，一个精通医术的女子为躲避金兵追杀，
      伪装身份混入太医院，却卷入了宫廷内部的权力斗争。

AI:   [... 五阶段大纲搭建完成，产出 story_frame.md、
       volume_map.md、book_rules.md、角色卡、character_matrix.md]

用户: 深化角色 林半夏

AI:   [四轮讨论完成，角色卡补全 Personality Lock、
       压力测试结论、对白风味和动作锚点]

用户: 写第1章

AI:   [drift check] → [创建 intent/plan] →
      [Writer] 草稿 → [Polish] 润色 → [Review] 审阅 → [Fixer] 修复 →
      [gatekeeper 通过] → [final-check 通过] → chapters/0001_临安雪.md

用户: 继续下一章          # 复用持久 Agent，无需重发基线
用户: 写接下来5章         # 流水线重叠，批末 audit
用户: 继续                # 跨卷自动归档 → 第 2 卷...
```

### 注册并使用 Skill

```text
用户: 我想注册一个"宋代官制审查"skill，
      用来检查小说中的官职描写是否准确。

AI:   好的。请简单描述这个 skill 的检查逻辑和触发条件。

用户: 当章节涉及官员出场时触发。检查官职名是否属于南宋、
      品级与权力是否匹配、官员称谓是否合理。

AI:   [登记到 skills/skill_registry.md] →
      [运行 skill_check.py 验证] → 注册完成

      Skill "song-dynasty-official-review" 已注册（状态: enabled）。
      后续章节中如果涉及官员出场，我会自动调用该 skill 进行审查。
      你也可以随时说"调用 song-dynasty-official-review 检查第 3 章"。
```

### 共创模式：手写章节后调 AI 审与修

```text
用户: 审查第 5 章
      # 用户手写了 Ch5，想让 AI 审查但不改原文

AI:   [读取 chapters/drafts/chapter-0005.author.md] →
      [Review 审查完成，输出问题清单] →
      发现 3 个问题：林半夏在第 3 场对陌生人透露了身份（角色约束违反）；
      H017 到期未推进；章尾使用了抽象情绪总结句。
      是否要逐条处理？

用户: 润色第 5 章 --模式 anti-ai

AI:   [Polish 按 anti-ai-only 模式处理] →
      删除了 4 处"某种难以言说的"、2 处"不是……而是……"，
      将章尾总结句改为物件落点。改动已标注位置和原因。
      原稿未覆盖，润色稿在 story/runtime/chapter-0005.author_polish_anti-ai.md。
```

### 构建知识库并用于写作

```text
用户: 我在 story/knowledge/ 下放了南宋太医院职官、
      《太平惠民和剂局方》摘要和宋代都城布局三份考据资料。
      帮我建索引。

AI:   [knowledge_index.py build] →
      索引完成：扫描到 3 个知识领域、47 条实体记录。
      已生成 .nw_index/entity_index.json。

用户: 写第 3 章     # 本章涉及太医院内部场景

AI:   [context_builder --chapter 3 --agent writer] →
      [knowledge_index query --chapter 3 --agent writer] →
      上下文包已注入：太医院职官体系（KB:F001-F012）、
      宋代方剂知识（KB:F030-F045）。
      Writer 在写作时可引用这些参考，确保医学描写准确。
```

### 文风拆解

```text
用户: 分析我手写的那章文风

AI:   [decompose_style.py --input chapters/drafts/chapter-0001.author.md] →
      生成三个文件：
      - style_analysis.md：第三人称限知，短中句为主，情绪通过动作呈现...
      - style_profile.json：{"pov": "third_person_limited", ...}
      - style_skill.md：Prefer 用动作承载情绪；Avoid 直接总结人物心理...

      是否将 style_skill.md 注册为项目 Skill？
      这样后续 AI 辅助时会自动对齐你的文风。
```

## 已知问题与限制

- **文笔上限受模型能力限制。** 框架通过 style_blacklist、scene-beat 和 Polish 层约束文笔下限，但文学品质仍取决于底层模型。
- **Python 脚本只做确定性检查，不做语义判断。** gatekeeper 通过不代表章节质量合格——只代表流程完整。创作质量的最终判断权在主会话和作者。
- **知识库第一版基于关键词和元数据，不支持语义检索。** 精确匹配可能漏掉相关但措辞不同的内容。后续版本可考虑引入 embedding 检索。
- **长篇项目状态文件随章节数线性增长。** `chapter_summaries.md` 和 `emotional_arcs.md` 已支持按卷分段，但数百章后仍需人工管理。
- **共创模式的手写稿路径约定为 `chapters/drafts/`，** 该目录需用户自行创建。AI 不会自动创建此目录。
- **InkOS 迁移器仅处理文件级映射。** SQLite memory.db、Zod JSON delta 和 `particle_ledger.md` 等 InkOS 特有组件无法自动迁移，会标记为"需手动审核"。
- **目前没有 Web UI 或后台自动调度器。** 调度完全由主会话通过 CLAUDE.md 协议完成，适合交互式使用但不适合无人值守的批量生成。

## 深入阅读

- [CLAUDE.md](CLAUDE.md) — 完整工作流协议与 Agent 架构
- [PROJECT_INTRO.md](PROJECT_INTRO.md) — 系统设计理念与组件说明
- [ORIGIN.md](ORIGIN.md) — InkOS lineage、借鉴清单、独立构建内容、架构对比
- [story/system_protocol.md](story/system_protocol.md) — 系统边界、状态机、反馈回路、定稿门禁

## 许可证

本项目以 [GNU Affero General Public License v3.0](LICENSE) 发布。简单说：你可以自由使用、修改和分发本项目，但必须以相同协议开源你的修改版本，且通过网络使用本框架的服务也需要提供源码。

InkOS 同样以 AGPL-3.0 发布。本项目的许可证选择与其保持兼容。
