# Narrative Workbench / 叙事工作台

面向 Claude Code 与 Codex CLI 的 AI 小说写作工程框架——结构化大纲搭建、四 Agent 持久会话流水线、伏笔生命周期管理、角色人格深度设计、去 AI 味文风控制。

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
- **Skill 可插拔扩展 + Python 辅助体检：** 注册制 skill 系统 + 8 个确定性检查脚本。

## 快速开始

1. 在此目录运行 `python3 scripts/create_project.py "新书名"`，进入生成的新书目录。
2. 启动 Claude Code，发送 `START_HERE.md` 中的启动指令（或让 AI 读取 `CLAUDE.md`）。
3. 对 AI 说 `搭建大纲`——AI 按五阶段推进：故事内核 → 前台/后台结构 → 分卷设计 → 角色设计（四轮讨论）→ 世界观铁律。已有大纲时说 `导入现成大纲`。
4. 大纲完成后说 `写第1章` 或 `写接下来5章`。

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

## 上下文工程

v0.2.0 引入两个脚本，将"该给 Agent 什么信息"从主模型的主观判断转变为可复现的确定性流程。

**context_builder.py — 上下文构建器：** 按 Agent 类型和章节自动构建上下文包，替代主模型手动判断"该读什么文件"。

```bash
python3 scripts/context_builder.py --chapter 12 --agent writer
```

每种 Agent 有独立的必读内容、压缩摘要和排除文件配置，内置 token 预算（Writer 18K / Polish 12K / Review 15K / Fixer 8K）。输出包含 6 个区块：必读内容 + 压缩摘要 + 禁止泄露提示 + 输出契约 + 省略文件清单 + 预算摘要。

**prompt_compiler.py — Prompt 编译器：** 将 Agent prompt 拆为三层编译，使每次输入可复现、可追溯。

```text
Layer 1: Base Prompt（agents/<agent>.md 全文，永不变更）
Layer 2: 项目规则（book_rules + style_blacklist + style_profile，极少变更）
Layer 3: 本章任务（intent + plan + context packet + 半衰期风险提示，每章更新）
```

Layer 1 在持久会话中仅在 Agent 首次创建时发送，Layer 2 在项目配置变更时更新，Layer 3 每章由 prompt_compiler 编译发送。这样持久会话的"无需重发基线"优势得以保持。

## 确定性门禁

**gatekeeper.py** 在 final-check 之前运行，检查流水线是否完整。所有检查都是确定性验证，不依赖 AI 判断。

```bash
python3 scripts/gatekeeper.py --chapter 12 --stage final
```

检查维度：流水线产物完整性（intent/plan/writer/polish/review/fixer 是否全部存在）、Review→Fixer 响应覆盖（必修问题是否被逐条处理）、hook 半衰期同步（是否有到期未处理的活跃伏笔）、禁止模式（括号内心独白、非标准引号）、AI 味高频词句（WARN 不阻塞）。

输出 `PASSED` 或 `FAILED` + 阻塞问题清单。gatekeeper 通过不代表章节质量合格——只代表流程完整。RUN_RULES 规定 gatekeeper 是 final-check 前**必须**运行的脚本，FAILED 时不得继续。

## 共创模式

在"AI 全流程写作"之外，v0.2.0 新增了"作者手写 + AI 辅助"的共创模式，面向有写作能力、需要工程化辅助的作者。

**审查第 N 章：** 对作者手写章节进行一致性审查。Review Agent 不改正文，只出问题清单——角色人格违背、伏笔遗漏、秘密泄露风险、状态冲突、节奏失衡、AI 味。每条标注位置和修改方向，是否采纳由作者决定。

**润色第 N 章：** 5 种润色模式，默认不覆盖原稿，所有改动标注位置和原因。

| 模式 | 说明 |
|---|---|
| `preserve-author-style` | 只改病句、重复、节奏，最大保留作者表达 |
| `project-style-align` | 按项目文风 profile 对齐 |
| `anti-ai-only` | 只去 AI 味 |
| `dialogue-only` | 只修对白，对齐角色卡的对白风味 |
| `rhythm-only` | 只调节奏：段落长短、喘息比例、章尾落点 |

**第 N 章写作简报：** 作者动笔前，系统根据该章在卷纲中的位置和当前项目状态生成约束简报——本章类型、必须推进的伏笔、禁止泄露的信息、推荐写法。不是替作者写，而是告诉作者这一章承担什么功能。

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
  *.md             状态账本与风格规则（18 个文件）
skills/            可插拔 skill 接口与注册表
scripts/           8 个 Python 辅助脚本
chapters/          正文章节（000N_标题.md）
```

## Python 辅助脚本

`doctor.py` · `create_project.py` · `chapter_index.py` · `text_audit.py` · `hook_report.py` · `hook_matrix.py` · `structure_report.py` · `skill_check.py`

脚本只做确定性检查，不做创作判断。运行门禁见 `RUN_RULES.md`。详细说明见 [`scripts/README.md`](scripts/README.md)。

## 使用示例

以下是从零搭建一本架空历史小说的实例过程。用户为 AI 提供初始构思，其余由 AI 按工作流协议推进。

```text
用户: 搭建大纲

AI:   好的。先确认基础定位——
      这本书一句话讲什么？

用户: 南宋绍兴年间，一个精通医术的女子为躲避金兵追杀，
      伪装身份混入太医院，却卷入了宫廷内部的权力斗争。

AI:   主类型是历史架空，副类型有悬疑和权谋，对吗？
      在开始之前，我想先确认主角——
      这个角色最想要什么？最害怕什么？

      [... 经过五阶段大纲搭建，产出 story_frame.md、
       volume_map.md、book_rules.md、角色卡、character_matrix.md]

用户: 深化角色 林半夏

AI:   好的。当前角色卡中林半夏只有基础标签"冷静、医术高超"。
      让我们进入 Round 1（核心人格）——
      你说她冷静，那她在什么情境下会失控？有没有一个
      让她破防的开关？

      [... 四轮讨论完成，角色卡补全 Personality Lock、
       压力测试结论、对白风味和动作锚点]

用户: 写第1章

AI:   [drift check] → [创建 intent/plan] →
      [Writer] 草稿 → [Polish] 润色 → [Review] 审阅 → [Fixer] 修复 →
      [final-check 通过] → 写入 chapters/0001_临安雪.md → 同步状态

用户: 继续下一章

AI:   [自动确定 N=2] → [复用持久 Agent 会话，无需重发基线] →
      Writer → Polish → Review → Fixer → final-check →
      chapters/0002_药引.md

用户: 写接下来5章

AI:   [批前 hook_report + drift check + batch-plan] →
      Ch3~Ch7 流水线重叠执行 →
      批末 batch-audit → doctor 体检通过

      第 1 卷还差 5 章达到卷尾节点，要继续吗？

用户: 继续

AI:   [新一轮 batch-plan，自动延续上一批的 hook 状态] →
      Ch8~Ch12 → 卷尾不可逆事件达成 →
      structure_report 确认第 1 卷结构闭环 →
      第 1 卷完成。是否进入第 2 卷？

用户: 继续

AI:   [进入新卷前：doctor + structure_report + hook_matrix 全量检查] →
      [上一卷 runtime 归档至 volume-1/] →
      创建第 2 卷首章 intent/plan →
      开始 Ch13...
```

框架处理了：大纲搭建的结构化推进、角色设计的追问深度、Agent 的持久会话复用和流水线重叠、hook 的半衰期追踪、批量续写与卷间切换的完整闭环。

## 深入阅读

- [CLAUDE.md](CLAUDE.md) — 完整工作流协议与 Agent 架构
- [PROJECT_INTRO.md](PROJECT_INTRO.md) — 系统设计理念与组件说明
- [ORIGIN.md](ORIGIN.md) — InkOS lineage、借鉴清单、独立构建内容、架构对比
- [story/system_protocol.md](story/system_protocol.md) — 系统边界、状态机、反馈回路、定稿门禁

## 许可证

本项目以 [GNU Affero General Public License v3.0](LICENSE) 发布。简单说：你可以自由使用、修改和分发本项目，但必须以相同协议开源你的修改版本，且通过网络使用本框架的服务也需要提供源码。

InkOS 同样以 AGPL-3.0 发布。本项目的许可证选择与其保持兼容。
