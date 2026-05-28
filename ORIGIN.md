# 项目起源与致谢 / Origin & Attribution

## 与 InkOS 的关系

Narrative Workbench 受 **[InkOS](https://github.com/Narcooo/inkos)** 启发——InkOS 是由 [Narcooo](https://github.com/Narcooo) 创建的多 Agent 小说生产系统，以 AGPL-3.0 协议发布。

InkOS 的核心工作流模式——多 Agent 写作流水线、真相文件状态管理、伏笔生命周期追踪、canonical/working 双区分离、去 AI 味机制——通过分析 InkOS 生成的小说项目结构而习得。

Narrative Workbench 是一个受 InkOS 启发的独立 Markdown-native 实现。本项目未复制 InkOS 源码，但有意借鉴并改造了 InkOS 的若干工作流概念与文件组织约定。因此，本项目以 AGPL-3.0 发布，并保留对 InkOS 及其贡献者的致谢。

## 借鉴自 InkOS 的概念（致谢）

以下概念受 InkOS 的开创性工作启发：

- **多 Agent 写作流水线**：不同阶段由专业化 Agent 分工协作
- **真相文件状态管理**：每本书维护一组 canonical 事实源文件
- **伏笔生命周期与半衰期机制**：伏笔的 open / advance / resolve 追踪与预算控制
- **canonical/working 边界**：规划产物与已发布事实的严格分离
- **去 AI 味规则体系**：将文笔质量控制系统化的方法论
- **状态文件命名约定**（`current_state.md`、`pending_hooks.md`、`chapter_summaries.md`、`emotional_arcs.md`、`character_matrix.md`、`current_focus.md`）——保留为兼容性设计，使 InkOS 生成的项目可迁移至 Narrative Workbench

## 独立构建的内容

以下特性在 InkOS 中没有对应项，为从零开始设计：

- **持久 Agent 会话模型：** 写作 Agent 在同一会话内跨章存活，积累跨章上下文。Agent 生命周期管理，8 章重置阈值。
- **角色设计四轮协议：** 核心人格 → 人格压力测试 → 关系性格张力 → 声音与表达。Personality Lock、Behavioral Constraints 和压力测试结论贯穿写作流水线每个阶段。
- **Context Packet 替代规则：** 差异化上下文加载——明确哪些文件在 Packet 可用时可跳过，哪些必须始终读原文。
- **Runtime 跨卷归档策略：** `volume-N/` 子目录归档 + 已归档 runtime 默认跳过规则。
- **完整状态机：** 10 状态章节生命周期，含显式失败路径（`needs-rewrite` → Writer 重试，`needs-repair` → Fixer 重试，`superseded` → 放弃）。
- **人格一致性验证链：** 角色卡压力测试 → intent/plan 交叉引用 → Review 人格检查 → batch-audit 跨章漂移检测 → final-check 门禁。
- **信息流向架构：** 主会话集中完成 hook 审计、角色审计、弧光差值分析和 drift check，将结论写入 intent/plan。Agent 只读本章驱动文件。
- **Claude Code Subagent 集成层：** `.claude/agents/` 薄路由包装器，委托到 `agents/` 中的详细 prompt。
- **Skill 协议与注册表：** 可插拔 skill 系统，含注册、校验（`skill_check.py`）和请求模板。
- **v0.2.0 上下文工程：** `context_builder.py`（按 Agent 构建上下文包 + token 预算）、`prompt_compiler.py`（三层 prompt 编译）、`gatekeeper.py`（确定性门禁检查）。
- **v0.2.0 知识库与状态：** `knowledge_index.py`（关键词+元数据项目索引）、`status.py`（项目状态概览）。
- **v0.2.0 文风与角色：** `style_report.py`（定量文风报告）、`character_drift_report.py`（角色漂移预警）、`decompose_style.py`（文风拆解器，输入文本 → analysis + profile + skill）。
- **v0.2.0 共创与兼容：** `review_author_chapter.py` / `polish_author_chapter.py`（共创模式简报生成）、`import_inkos_project.py`（InkOS 项目迁移器）。
- **Python 环境降级方案：** 无 Python 时 AI 手动执行等效检查，产物标注 `(manual)`。
- **共创模式：** 审查第N章 / 润色第N章（5种模式）/ 第N章写作简报——作者手写 + AI 辅助。
- **所有 Python 辅助脚本（19 个）** 和 **所有 Prompt 文本与模板** 均为独立编写。

## 架构对比

| | InkOS | Narrative Workbench |
|---|---|---|
| **平台** | TypeScript CLI（npm 包） | Markdown prompt 框架（Claude Code/Codex CLI） |
| **Agent 模型** | 10 Agent，3 阶段（创作→结算→质量） | 5 Agent，4 阶段流水线 + 独立上下文路由 |
| **Agent 名称** | Radar、Planner、Composer、Architect、Writer、Observer、Reflector、Normalizer、Auditor、Reviser | Project Librarian、Writer、Polish、Review、Fixer |
| **状态后端** | Markdown 真相文件 + SQLite + Zod schema 校验 | Markdown 账本 + JSON 镜像 + 19 个 Python 脚本 |
| **Agent 会话** | 无状态（每章新调用） | 持久会话（跨章存活，8 章重置阈值） |
| **上下文管理** | Composer Agent 按相关性选取上下文 | 持久会话基线 + context_builder + prompt_compiler |
| **流水线控制** | CLI 命令（`inkos write next`） | 主会话编排 + gatekeeper 门禁 + CLAUDE.md 协议 |
| **确定性检查** | 内嵌 TypeScript 逻辑 | 19 个独立 Python 脚本（无 Python 时 AI 手动等效） |
| **写作模式** | 全自动流水线 | 流水线模式 + 共创模式（作者手写 + AI 辅助） |

## 许可证兼容性

Narrative Workbench 与 InkOS 均以 **AGPL-3.0** 发布。这确保了许可证兼容性，并延续了原项目的 copyleft 原则。

## 致谢

感谢 **Narcooo** 及所有 InkOS 贡献者，率先将长篇创作工程化——证明了专业化 Agent、系统化状态追踪和严格审计循环可以规模化产出连贯的长篇小说。InkOS 展示了可能性，Narrative Workbench 因此而存在。

## 联系方式

如果你是该项目的 InkOS 贡献者并对此项目有疑虑，请提交 GitHub issue 或联系仓库所有者。
