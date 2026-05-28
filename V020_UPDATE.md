# Narrative Workbench v0.2.0 更新总结

## 概述

v0.2.0 的核心主题是**上下文工程与流程确定性**。在 v0.1.0 建立的四 Agent 持久会话流水线基础上，v0.2.0 引入了三个新脚本、三种共创模式命令和 Skill 模板的扩展，目标是将"该给 Agent 什么信息"和"能不能提交到 canonical"从主模型的主观判断转变为可复现的确定性流程。

## 新增脚本

### context_builder.py — 上下文构建器

为每个 Agent 按章节构建上下文包，替代主模型手动判断"该读什么文件"。

```bash
python3 scripts/context_builder.py --chapter 12 --agent writer
```

**设计要点：**

- 5 种 Agent（writer/polish/review/fixer/librarian）各有独立的必读内容、压缩摘要和排除文件配置
- 内置 token 预算：Writer 18K / Polish 12K / Review 15K / Fixer 8K / Librarian 20K
- 输出包含 6 个区块：必读内容、压缩摘要、禁止泄露提示、输出契约、省略文件清单、预算摘要
- 超出预算时输出 WARNING
- 产物路径：`story/runtime/chapter-XXXX.<agent>.context.md`

### prompt_compiler.py — Prompt 编译器

将 Agent prompt 拆为三层编译，使每次输入可复现、可追溯。

```bash
python3 scripts/prompt_compiler.py --chapter 12 --agent writer
python3 scripts/prompt_compiler.py --chapter 12 --agent writer --context runtime/chapter-0012.writer.context.md
```

**三层结构：**

| 层 | 来源 | 变更频率 |
|---|---|---|
| Base Prompt | `agents/<agent>.md` 全文 | 永不 |
| 项目规则 | `book_rules.md` + `style_blacklist.md` + `style_profile.md` + 系统协议 | 极少 |
| 本章任务 | intent + plan + context packet + 半衰期风险提示 | 每章 |

**设计要点：**

- Layer 1（Base Prompt）在持久会话中仅在 Agent 首次创建时发送，后续章节不重复
- Layer 2（项目规则）仅在项目配置变更时更新
- Layer 3（本章任务）每章由 prompt_compiler 编译并发送
- 产物路径：`story/runtime/chapter-XXXX.<agent>.prompt.md`

### gatekeeper.py — 确定性门禁

在 final-check 之前运行，检查流水线是否完整。所有检查都是确定性验证，不依赖 AI 判断。

```bash
python3 scripts/gatekeeper.py --chapter 12 --stage final
```

**检查维度：**

| 检查项 | 阻塞 | 说明 |
|---|---|---|
| 流水线产物完整性 | 是 | intent/plan/writer/polish/review/fixer 是否全部存在 |
| Review→Fixer 响应覆盖 | 是 | Review 的必修问题是否被 Fixer 逐条处理 |
| hook 半衰期同步 | 是 | 是否有到期未处理的活跃伏笔 |
| 禁止模式 | 是 | 括号内心独白、非标准引号 |
| AI 味高频词句 | 否 | 作为 WARN 输出，不阻塞 |
| intent 状态合法性 | 是 | status 字段是否在允许的枚举值内 |

**输出：** `PASSED` 或 `FAILED` + 阻塞问题清单 + 非阻塞警告。gatekeeper 通过不代表章节质量合格，只代表流程完整。

**RUN_RULES 规定：** gatekeeper 是 Final-check 前**必须**运行的脚本。FAILED 时不得继续 final-check 或写入 canonical。修复阻塞问题后重新运行直到 PASSED。

## 共创模式（新增命令）

v0.2.0 在"AI 全流程写作"之外新增了"作者手写 + AI 辅助"的共创模式。

### 审查第 N 章

对作者手写章节进行一致性审查。Review Agent 不改正文，只出问题清单。

```text
审查第 N 章
审查我写的第 N 章
```

检查维度：角色人格违背、伏笔遗漏、秘密泄露风险、前文状态冲突、节奏失衡、AI 味、场景目标不清。问题按严重度排列，每条标注位置和修改方向建议。

### 润色第 N 章

按指定模式润色作者手写章节。默认不覆盖原稿，所有改动标注位置和原因。

```text
润色第 N 章 --模式 light
润色我写的第 N 章 --mode anti-ai
```

**5 种润色模式：**

| 模式 | 别名 | 说明 |
|---|---|---|
| `preserve-author-style` | `light` | 只改病句、重复、节奏 |
| `project-style-align` | `style` | 按项目文风 profile 对齐 |
| `anti-ai-only` | `anti-ai` | 只去 AI 味 |
| `dialogue-only` | `dialogue` | 只修对白 |
| `rhythm-only` | `rhythm` | 只调节奏 |

### 第 N 章写作简报

在作者动笔前生成约束简报。不是替作者写，而是告诉作者：这一章承担什么功能、有什么约束、必须推进什么。

```text
第 N 章写作简报
写第 N 章之前提醒我
```

简报包含：本章类型、必须处理的伏笔、禁止泄露的信息、推荐写法。一屏内读完。

## Skill 模板更新

为支持知识库集成，Skill 注册模板和请求模板新增三个字段：

**`_template.skill-entry.md`：**

- **知识库依赖：** Skill 声明运行时需要查询的知识库领域、查询时机和必要性
- **内置知识声明：** 如果 Skill 通过模型训练数据携带了领域知识（而非从 KB 查询），必须在此声明来源和权威性

**`_template.skill-request.md`：**

- **知识库查询：** 本次 Skill 调用是否需要查询知识库、查询领域和关键词、查询结果引用

设计原则：Skill 是纯方法论层，不拥有事实。事实的唯一来源是知识库。

## 文档更新

- **CLAUDE.md** — 恢复丢失的 `## Agent 职责` 标题；final-check 增加 gatekeeper 前置检查；Agent 恢复增加 context_builder 建议；新增 3 个共创模式命令 + 深化角色命令；信息流向原则明确化
- **RUN_RULES.md** — 阶段门禁表新增 7 行（context_builder 4 行、prompt_compiler 1 行、gatekeeper 1 行、Final-check 更新 1 行）；脚本职责表新增 3 行；gatekeeper 失败处理规则
- **START_HERE.md** — 命令列表增加 4 个新命令；脚本列表增加 3 个新脚本
- **system_protocol.md** — Working 区新增 3 种 runtime 文件类型；定稿门禁扩展为 9 项
- **README.md** — 用户命令表新增 3 个共创模式命令
- **doctor.py** — 检查范围覆盖 3 个新脚本和 3 种新 runtime 文件类型

## 脚本总数

| v0.1.0 | v0.2.0 |
|---|---|
| 8 个 | 18 个 |

新增 10 个：
- 上下文工程：`context_builder.py`、`prompt_compiler.py`
- 流程确定性：`gatekeeper.py`
- 知识库与状态：`knowledge_index.py`、`status.py`
- 文风与角色：`style_report.py`、`character_drift_report.py`、`decompose_style.py`
- 共创与兼容：`review_author_chapter.py`、`polish_author_chapter.py`、`import_inkos_project.py`

## 设计决策

- **context_builder 和 prompt_compiler 是"建议"：** 主会话仍然可以手动准备 Agent 输入。脚本提供自动化和可复现性。
- **gatekeeper 是 Final-check 前的"必须"步骤：** 所有检查都是确定性验证。gatekeeper 通过 ≠ 章节合格，只 = 流程完整。
- **信息流向单向化：** 主会话集中做分析（hook 盘点、角色盘点、弧光差值、drift check），结论写入 intent/plan。Agent 只读本章驱动文件，不自行重复分析。
- **共创模式保护原稿：** Review 不改文、Polish 默认不覆盖、所有改动标注位置和原因。
- **Skill 零事实原则：** Skill 是纯方法论，所有领域事实来自知识库。

## 兼容性

v0.2.0 完全向后兼容 v0.1.0。所有新增脚本和命令都是增量添加，不影响现有工作流。`create_project.py` 生成的新项目自动包含新脚本。
