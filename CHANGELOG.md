# Changelog

## v0.5.0 — 作者体验增强与分层 diff 工作流

### Markdown-native 作者体验

- **新增 `story/DASHBOARD.md` 生成器** — `core.dashboard` + `scripts/dashboard.py` + `nw dashboard`，输出当前章节、上一章、到期伏笔、未揭示秘密、时间线风险和下一步操作。
- **新增分层共创 diff** — `core.diff_workflow` + `scripts/diff_workflow.py` + `nw diff`，对话只显示摘要，Markdown 承载阅读，JSONL 承载执行。
- **按编号接受/拒绝修改** — `nw diff apply --accept 01,03 --reject 02` 生成 `author.v2.md` 与 `decision_log.md`，不覆盖作者原稿。
- **新增场景卡工具** — `core.scene_cards` + `scripts/scene_card.py` + `nw scene`，生成和列出 Markdown 场景卡。
- **新增角色声音实验室** — `core.voice_lab` + `scripts/voice_lab.py` + `nw voice-lab`，生成会说/不会说/泄密风险测试任务包。
- **新增导出工具** — `core.exporter` + `scripts/export_book.py` + `nw export`，无依赖导出 Markdown、简版 DOCX 和简版 EPUB。

### 本地入口与协议化

- **新增 `nw` 统一入口** — 支持 `doctor`、`dashboard`、`gatekeeper`、`diff generate/show/apply`、`scene`、`voice-lab` 和 `export`。
- **新增 Python 项目元数据** — `pyproject.toml` 声明 Python 版本、PyYAML 运行依赖、pytest 测试依赖和 `nw` console script。
- **JSON 协议输出** — Dashboard、Gatekeeper、diff generate/apply 支持结构化输出，便于未来 TypeScript core、API 服务层和客户端复用。

### 测试覆盖

- **新增 Dashboard 测试** — 验证 Dashboard 协议数据和 Markdown 输出。
- **新增 diff workflow 测试** — 验证候选生成、单条显示、接受/拒绝应用和决策日志。
- **新增 v0.5 作者工具测试** — 验证场景卡、角色声音实验室和 DOCX/EPUB 导出。

---

## v0.4.0 — 架构优化与工作流增强

### Core 模块体系

- **新增 `core/` 包** — 抽取 project、ledger、context、chapter、gatekeeper、doctor、hooks、style、knowledge、prompt 等可复用模块
- **脚本薄包装化** — `ledger_manager.py`、`relevance_resolver.py`、`director_sheet.py`、`gatekeeper.py`、`doctor.py`、`hook_report.py`、`hook_matrix.py`、`style_report.py`、`text_audit.py`、`knowledge_index.py`、`prompt_compiler.py` 保留原命令入口，内部委托 core 模块
- **项目根目录统一** — `scripts/_project.py` 改为 `core.project` 的兼容包装，继续支持 `--project-root`

### 工作流稳定性

- **场景接力卡校验** — 新增 `core.chapter.validate_scene_handoffs`，检查 handoffs、scene_id、handoff_to、physical_state、emotional_state、required_next_scene_input 等字段
- **Gatekeeper 增强** — final gate 接入场景接力卡校验；缺失接力卡为非阻塞警告，已存在但结构不完整时为阻塞问题
- **上下文核心复用** — `core.context` 承载 Relevance Resolver 的计划解析、角色/伏笔/秘密注入、预算估算和任务包生成
- **Prompt 编译复用** — `core.prompt` 统一三层 prompt 编译、runtime 文件定位、硬约束与半衰期风险提示

### 测试覆盖

- **新增回归测试** — 覆盖 ledger、chapter、gatekeeper、doctor、hooks、style、knowledge、prompt 等 core 模块
- **CLI smoke 验证** — 保留旧命令行为验证，确保 Claude Code / Codex 用户调用方式不变

---

## v0.3.0 — 平台原生化 + 上下文引擎重构

### 平台原生化

- **CLAUDE.md 精简** — 从 513 行压缩到 103 行核心路由。流程细节移至 `workflow/` 目录
- **AGENTS.md 新增** — Codex CLI/IDE Extension 原生入口，与 CLAUDE.md 同源
- **Skills 同步系统** — `skills/sync_skills.py` 将 `skills/`（唯一正式来源）同步到 `.claude/skills/` + `.agents/skills/` 轻量入口包装
- **Codex 适配** — 新增 `.codex/agents/` + `.codex/hooks.json`（生命周期脚本绑定）
- **6 个 Skill 入口创建** — plan_chapter, write_chapter, review_chapter, polish_author_draft, import_outline, deepen_character

### 上下文引擎重构

- **结构化小说账本** — `story/ledger/` 中 7 个 JSONL 文件（facts, hooks, timeline, characters, relationships, secrets, locations）+ `scripts/ledger_manager.py` 管理脚本
- **Markdown Views 双轨** — `story/views/` + `scripts/render_views.py` 将 JSONL 渲染为作者可读 Markdown（hook_dashboard, knowledge_matrix, timeline, relationships）
- **Relevance Resolver** — `scripts/relevance_resolver.py` 替代 context_builder 的核心逻辑：根据章节 plan 的 cast_ids/hook_ids/secret_ids 精确检索，为不同 Agent 构建差异化任务包
- **Prompt Compiler 去重** — 修复 `find_runtime_file` glob 过于宽泛的问题，增加排除过滤器

### 全章统筹基础设施

- **章节导演表** — `story/plans/_template.director_sheet.yaml` + `scripts/director_sheet.py` 生成脚本
- **场景接力卡** — `story/runtime/_template.scene_handoffs.yaml` 防止前后场景断裂
- **全章连续性审查** — `story/runtime/_template.coherence_review.md` 五链检查（因果/情绪/信息/物理/节奏）

### v0.2.2 前置修复（已包含）

- **ROOT 路径统一修复** — 全部 18 个脚本支持 `--project-root`，默认使用当前工作目录
- **context_builder 精准筛选** — 角色按 cast_ids 过滤、摘要精确提取前一章、伏笔按章节相关性筛选
- **共创脚本全文截断修复** — review_author_chapter.py 和 polish_author_chapter.py 取消 5000 字符硬截断，改为全文分块输出
- **Context Packet 输出增强** — 注入条目标注原因、省略条目标注省略原因

### 质量保障

- **回归测试** — `tests/` 目录，含 test_ledger.py（账本 CRUD）、test_context_budget.py（预算验证）、conftest.py（fixtures）

---

## v0.2.0 — 全面运行时升级

### 新增脚本（共 11 个，v0.1.0 原有 8 个 → 现共 19 个）

**上下文工程：**
- `context_builder.py` — 按 Agent 类型和章节构建上下文包，内置 token 预算。产物：`chapter-XXXX.<agent>.context.md`
- `prompt_compiler.py` — 三层 prompt 编译（Base + 项目规则 + 本章任务）。产物：`chapter-XXXX.<agent>.prompt.md`

**流程确定性：**
- `gatekeeper.py` — 确定性门禁检查（final-check 前必须运行）。检查流水线完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式。产物：`chapter-XXXX.gatekeeper.md`

**知识库与状态：**
- `knowledge_index.py` — 关键词+元数据项目索引，支持 build/query 两种模式。产物：`.nw_index/entity_index.json`、知识包
- `status.py` — 项目状态概览：章节进度、hook 统计、角色漂移风险、建议下一步

**文风与角色：**
- `style_report.py` — 定量文风报告（句长分布、对白密度、AI 味模式命中）。产物：`chapter-XXXX.style_report.md`
- `character_drift_report.py` — 对照角色约束扫描章节文本，输出疑似漂移预警。产物：`chapter-XXXX.character_drift.md`
- `decompose_style.py` — 文风拆解器。输入文本 → 输出 `style_analysis.md` + `style_profile.json` + `style_skill.md`

**共创与兼容：**
- `review_author_chapter.py` — 为手写章节生成 Review 审查简报
- `polish_author_chapter.py` — 为手写章节生成 Polish 润色简报（5 种模式）
- `import_inkos_project.py` — InkOS 项目文件映射迁移

### 共创模式

- **审查第 N 章** — 对手写章节进行一致性审查，不改正文，只出问题清单
- **润色第 N 章 --模式** — 5 种润色模式（preserve-author-style / project-style-align / anti-ai-only / dialogue-only / rhythm-only），默认不覆盖原稿
- **第 N 章写作简报** — 作者动笔前生成约束简报

### Skill 模板更新

- `_template.skill-entry.md` — 新增"知识库依赖"和"内置知识声明"字段
- `_template.skill-request.md` — 新增"知识库查询"字段

### 文档更新

- **CLAUDE.md** — 恢复 Agent 职责标题；final-check 增加 gatekeeper；新增 3 个共创命令 + 深化角色命令
- **RUN_RULES.md** — 脚本职责表新增 10 行；阶段门禁表新增 4 行；gatekeeper 失败处理规则
- **START_HERE.md** — 命令列表和脚本列表同步更新
- **system_protocol.md** — Working 区新增 3 种 runtime 文件类型
- **README.md** — 新增共创模式章节；用户命令表新增 3 个命令
- **doctor.py** — 检查范围覆盖全部 19 个脚本和 6 种新 runtime 文件类型

### 设计决策

- context_builder 和 prompt_compiler 是"建议"——主会话仍可手动准备 Agent 输入
- gatekeeper 是 Final-check 前的**必须**步骤——所有检查都是确定性验证
- 共创模式保护作者原稿——Review 不改文、Polish 默认不覆盖、所有改动标注位置和原因
- Skill 零事实原则——Skill 是纯方法论，领域事实来自知识库

---

## v0.1.0 — 首次公开发布

- 四 Agent 持久会话写作流水线（Writer / Polish / Review / Fixer）
- Project Librarian 上下文路由
- 角色设计四轮协议（核心人格 → 压力测试 → 关系张力 → 声音表达）
- Hook 伏笔生命周期管理与半衰期系统
- 章节状态机（10 状态，含 needs-rewrite / needs-repair 失败回路）
- Skill 可插拔扩展机制
- 8 个 Python 确定性检查脚本
- 导入现成大纲流程（含最低完备性检查和主动缺口检测）
- 深化角色命令
- Context Packet 替代规则
- Runtime 跨卷归档策略
- AGPL-3.0 许可证
- 受 InkOS 启发，独立 Markdown-native 实现
