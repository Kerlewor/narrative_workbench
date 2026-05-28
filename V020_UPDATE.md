# Narrative Workbench v0.2.0 更新总结

## 概述

v0.2.0 的核心主题是**从 prompt 框架到小说工程运行时**。在 v0.1.0 建立的四 Agent 持久会话流水线基础上，v0.2.0 新增了 11 个 Python 脚本、3 种共创模式命令、Python 环境降级方案和 Skill 模板扩展，将上下文构建、prompt 编译、流程门禁、知识索引、文风分析、角色漂移检测和项目迁移从主模型的主观判断转变为确定性流程。

## 新增脚本（11 个）

### 上下文工程

**`context_builder.py`** — 为每个 Agent 按章节构建上下文包。

```bash
python3 scripts/context_builder.py --chapter 12 --agent writer
```

- 5 种 Agent 各有独立的必读内容、压缩摘要和排除文件配置
- 内置 token 预算（Writer 18K / Polish 12K / Review 15K / Fixer 8K / Librarian 20K）
- 输出包含 6 个区块：必读内容、压缩摘要、禁止泄露提示、输出契约、省略文件清单、预算摘要
- 超出预算时输出 WARNING

**`prompt_compiler.py`** — 三层 prompt 编译，使每次 Agent 输入可复现、可追溯。

```bash
python3 scripts/prompt_compiler.py --chapter 12 --agent writer
```

- Layer 1（Base Prompt）：从 `agents/<agent>.md` 读取，永不改变
- Layer 2（项目规则）：从 `book_rules.md` / `style_blacklist.md` / `style_profile.md` 编译，极少变更
- Layer 3（本章任务）：intent + plan + context packet + 半衰期 hook 风险提示，每章更新
- Layer 1 和 2 在持久会话中仅首次发送，Layer 3 每章由 compiler 编译

### 流程确定性

**`gatekeeper.py`** — 确定性门禁检查。final-check 前必须运行。

```bash
python3 scripts/gatekeeper.py --chapter 12 --stage final
```

- 检查：流水线产物完整性、Review→Fixer 响应覆盖、hook 半衰期同步、禁止模式、intent 状态合法性
- 输出 `PASSED` 或 `FAILED` + 阻塞问题（BLOCKING）+ 非阻塞警告（WARN）
- FAILED 时不得继续 final-check 或写入 canonical

### 知识库与状态

**`knowledge_index.py`** — 关键词+元数据项目索引。

```bash
python3 scripts/knowledge_index.py build
python3 scripts/knowledge_index.py query --chapter 12 --agent writer
```

- build 模式：扫描项目文件，构建实体索引和文件清单
- query 模式：按关键词、领域或章节查询，生成 knowledge_packet
- 产物路径：`.nw_index/entity_index.json`、`story/runtime/chapter-XXXX.knowledge_packet.md`

**`status.py`** — 项目状态概览。

```bash
python3 scripts/status.py
python3 scripts/status.py --verbose
```

- 输出：章节进度、活跃/已回收 hook 数、超半衰期 hook 数、角色漂移风险、脚本数量、知识库索引状态
- 根据检测结果给出建议下一步操作
- `--verbose` 模式额外输出 runtime 文件详情

### 文风与角色

**`style_report.py`** — 定量文风报告。

```bash
python3 scripts/style_report.py --chapter 12
python3 scripts/style_report.py --input chapters/0012_标题.md
```

- 分析：句长分布（短/中/长句比例）、对白密度、段落形态、AI 味模式命中次数
- 输出具体的改进建议

**`character_drift_report.py`** — 角色漂移预警。

```bash
python3 scripts/character_drift_report.py --chapter 12
python3 scripts/character_drift_report.py --chapter 12 --character 林半夏
```

- 读取角色卡的 `cannot_do` 和 `speech_style` 约束
- 扫描章节文本查找疑似违背，输出预警但不做最终判断
- 每条预警标注约束内容和上下文

**`decompose_style.py`** — 文风拆解器。

```bash
python3 scripts/decompose_style.py --input chapters/drafts/author-sample.md
```

- 输入文本 → 输出三个产物：
  1. `style_analysis.md` — 人读的文风拆解报告（12 个维度）
  2. `style_profile.json` — 系统读的结构化配置
  3. `style_skill.md` — Agent 执行的风格规则

### 共创与兼容

**`review_author_chapter.py`** — 手写章节审查简报。

```bash
python3 scripts/review_author_chapter.py --chapter 12
python3 scripts/review_author_chapter.py --input chapters/drafts/my-chapter.md
```

- 读取手写稿，生成包含检查维度和原则的审查简报
- 不修改原文——输出独立于原稿

**`polish_author_chapter.py`** — 手写章节润色简报。

```bash
python3 scripts/polish_author_chapter.py --chapter 12 --mode light
python3 scripts/polish_author_chapter.py --chapter 12 --mode anti-ai
```

- 5 种润色模式，每种有独立的指令集
- 默认不覆盖原稿，所有改动标注位置和原因

**`import_inkos_project.py`** — InkOS 项目迁移器。

```bash
python3 scripts/import_inkos_project.py /path/to/inkos-book
python3 scripts/import_inkos_project.py /path/to/inkos-book --dry-run
```

- 11 个文件映射规则（直接映射 + 需手动审核）
- 章节和角色卡的批量迁移
- `--dry-run` 预览模式
- 不内置 InkOS 源码或 prompt 文本

## 共创模式（新增命令）

v0.2.0 在"AI 全流程写作"之外新增了"作者手写 + AI 辅助"的共创模式。

### 审查第 N 章

对作者手写章节进行一致性审查。Review Agent 不改正文，只出问题清单。检查角色人格违背、伏笔遗漏、秘密泄露风险、状态冲突、节奏失衡、AI 味。问题按严重度排列，采纳与否由作者决定。

### 润色第 N 章 --模式

5 种润色模式：`preserve-author-style`（保留表达）/ `project-style-align`（对齐文风）/ `anti-ai-only`（只去 AI 味）/ `dialogue-only`（只修对白）/ `rhythm-only`（只调节奏）。默认不覆盖原稿，改动标注位置和原因。

### 第 N 章写作简报

作者动笔前，系统根据卷纲位置和项目状态生成约束简报——本章类型、必须推进的伏笔、禁止泄露的信息、推荐写法。不是替作者写，而是告诉作者这一章承担什么功能。

## Python 环境降级方案

新增会话启动时的 Python 环境检测步骤。当用户无 Python 或选择不使用时，AI 手动执行等效检查：

- `doctor.py` → AI 逐项检查文件存在性、JSON 合法性、frontmatter 格式
- `gatekeeper.py` → AI 手动执行完整门禁清单
- `hook_report.py / hook_matrix.py` → AI 人工计算半衰期和依赖关系
- `text_audit.py` → AI 扫描全文对照 style_blacklist
- `context_builder.py / prompt_compiler.py` → AI 手动收集文件并拼接
- 其余脚本 → AI 执行等效手动检查或分析

降级产物写入相同 runtime 路径并标注 `(manual)`。

## Skill 模板更新

为支持知识库集成，Skill 模板新增字段：

- `_template.skill-entry.md` — "知识库依赖"（领域、查询时机、必要性）+"内置知识声明"（是否携带模型训练数据中的领域知识）
- `_template.skill-request.md` — "知识库查询"（是否查询、查询领域和关键词、结果引用）

设计原则：Skill 是纯方法论层，不拥有事实。事实的唯一来源是知识库。

## 文档更新

- **CLAUDE.md** — 会话启动增加 Python 环境检测；final-check 增加 gatekeeper 前置检查；Agent 恢复增加 context_builder 建议；新增 3 个共创命令；恢复丢失的 `## Agent 职责` 标题；信息流向原则明确化
- **RUN_RULES.md** — 新增 Python 不可用时的降级规则表（19 个脚本逐一定义手动等效方案）；阶段门禁表新增 5 行；脚本职责表新增 11 行；gatekeeper 失败处理规则
- **START_HERE.md** — 命令列表增加 4 个新命令；增加 Python 环境检测要求；脚本列表同步更新
- **system_protocol.md** — Working 区新增 3 种 runtime 文件类型；定稿门禁扩展为 9 项
- **README.md** — 新增共创模式章节；用户命令表新增 3 个命令；脚本列表更新为 19 个；核心特性、目录结构等硬编码数量全部修正
- **doctor.py** — 检查范围覆盖全部 19 个脚本和 6 种新 runtime 文件类型
- **CHANGELOG.md** — v0.2.0 完整变更记录
- **ORIGIN.md** — 弱化否定式声明，改为正面表述独立实现关系并保留致谢
- **.gitignore** — 新增 `.nw_index/` 排除规则

## 脚本总数

| v0.1.0 | v0.2.0 |
|---|---|
| 8 个 | 19 个 |

新增 11 个：

| 类别 | 脚本 |
|---|---|
| 上下文工程 | `context_builder.py`、`prompt_compiler.py` |
| 流程确定性 | `gatekeeper.py` |
| 知识库与状态 | `knowledge_index.py`、`status.py` |
| 文风与角色 | `style_report.py`、`character_drift_report.py`、`decompose_style.py` |
| 共创与兼容 | `review_author_chapter.py`、`polish_author_chapter.py`、`import_inkos_project.py` |

## 设计决策

- **context_builder 和 prompt_compiler 是"建议"：** 主会话仍可手动准备 Agent 输入。脚本提供自动化和可复现性。在无 Python 环境下由 AI 手动等效执行。
- **gatekeeper 是 Final-check 前的"必须"步骤：** 所有检查都是确定性验证，不依赖 AI 判断。gatekeeper 通过 ≠ 章节合格，只 = 流程完整。FAILED 时不得继续。
- **Python 优先，降级保底：** 会话启动时检测 Python 环境。有 Python 时脚本负责确定性检查；无 Python 时 AI 手动执行等效验证。两种路径功能完整，可靠性差异通过标注 `(manual)` 透明化。
- **信息流向单向化：** 主会话集中做分析（hook 盘点、角色盘点、弧光差值、drift check），结论写入 intent/plan。Agent 只读本章驱动文件。
- **共创模式保护原稿：** Review 不改文、Polish 默认不覆盖、所有改动标注位置和原因。
- **Skill 零事实原则：** Skill 是纯方法论，所有领域事实来自知识库。

## 兼容性

v0.2.0 完全向后兼容 v0.1.0。所有新增脚本和命令都是增量添加，不影响现有工作流。`create_project.py` 生成的新项目自动包含全部 19 个脚本。
