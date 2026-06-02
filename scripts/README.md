# Scripts

## create_project.py

```bash
python scripts/create_project.py "我的新小说"
python scripts/create_project.py "我的新小说" --target /path/to/books
```

用途：

- 从 Narrative Workbench 模板创建新书项目目录。
- 保留 `.claude/agents/`、`story/`、`scripts/`、`skills/` 等工作流文件。
- 更新 `story/state/manifest.json` 项目名。
- 生成新项目介绍文件 `PROJECT.md`。
- 避免直接污染 `_frameworks/narrative_workbench` 模板目录。

## nw

```bash
python scripts/nw doctor
python scripts/nw dashboard
python scripts/nw gatekeeper --chapter 12 --stage final
python scripts/nw diff generate --chapter 12 --original chapters/drafts/chapter-0012.author.md --revised story/runtime/chapter-0012.polish.md
python scripts/nw diff show --chapter 12 --id 03
python scripts/nw diff apply --chapter 12 --accept 01,03 --reject 02
python scripts/nw scene create --chapter 12 --id scene_01 --title "旧站台入口"
python scripts/nw voice-lab --character 林安 --line "你为什么知道这块雪牌？"
python scripts/nw export --format docx --output exports/book.docx
```

用途：

- 统一本地入口，优先服务普通作者和未来 UI。
- 保留 `scripts/*.py` 的传统调用方式，Claude Code / Codex 仍可直接运行单个脚本。
- 支持 JSON 协议输出，便于后续 TypeScript core、API 服务层和客户端复用。

## dashboard.py

```bash
python scripts/dashboard.py
python scripts/dashboard.py --json
python scripts/nw dashboard
```

用途：

- 生成 `story/DASHBOARD.md` 写作控制台。
- 汇总当前章节、上一章、到期伏笔、未揭示秘密、时间线风险和可直接输入的操作。
- 对话窗口只显示摘要，详细状态留在 Markdown 文件中。

## diff_workflow.py

```bash
python scripts/diff_workflow.py generate --chapter 12 --original chapters/drafts/chapter-0012.author.md --revised story/runtime/chapter-0012.polish.md
python scripts/diff_workflow.py show --chapter 12 --id 03
python scripts/diff_workflow.py apply --chapter 12 --accept 01,03 --reject 02
```

用途：

- 生成 `chapter-XXXX.diff_index.md` 可读索引。
- 生成 `story/runtime/diffs/chapter-XXXX/patch-XXXX.md` 单条修改详情。
- 生成 `chapter-XXXX.patch_candidates.jsonl` 执行数据。
- 按编号接受/拒绝修改，输出 `chapters/drafts/chapter-XXXX.author.v2.md` 和 `decision_log.md`。

## scene_card.py

```bash
python scripts/scene_card.py create --chapter 12 --id scene_01 --title "旧站台入口" --pov 林安 --characters 林安,周月
python scripts/scene_card.py list --chapter 12
```

用途：

- 在 `story/plans/scenes/chapter-XXXX/` 下生成 Markdown 场景卡。
- 场景卡保留 structured frontmatter，供 Relevance Resolver 和主会话读取。
- 自然语言编辑由 Claude Code/Codex 落到 Markdown 文件，不需要独立 UI。

## voice_lab.py

```bash
python scripts/voice_lab.py --character 林安 --line "你为什么知道这块雪牌？"
```

用途：

- 生成 `story/runtime/voice_lab.角色名.md`。
- 读取角色卡摘录，构造"会说/不会说/泄密风险"测试任务。
- 输出只作为候选，作者确认后才写入角色卡或正文。

## export_book.py

```bash
python scripts/export_book.py --format markdown --output exports/book.md
python scripts/export_book.py --format docx --output exports/book.docx
python scripts/export_book.py --format epub --output exports/book.epub
```

用途：

- 按章节文件名顺序收集 `chapters/*.md`。
- 使用标准库生成 Markdown、简版 DOCX 和简版 EPUB。
- 面向交付预览，不替代专业出版排版。

## doctor.py

运行：

```bash
python scripts/doctor.py
```

检查内容：

- 核心文件是否存在。
- JSON 是否可解析。
- `.claude/agents/*.md` frontmatter 是否有效。
- `chapters/index.json` 是否指向真实正文。
- `pending_hooks.md` 字段是否符合 `hook_protocol.md`。
- hook 状态、优先级、半衰期是否合法。
- runtime 状态是否在系统状态机允许范围内。
- `CLAUDE.md` 是否引用关键系统协议。

建议执行时机：

- 新书项目初始化后。
- 每批章节写作完成后。
- 手动改状态文件后。
- 长篇进入新卷前。

## chapter_index.py

```bash
python scripts/chapter_index.py --check
python scripts/chapter_index.py --write
```

用途：

- 扫描 `chapters/000N_标题.md`。
- 生成或检查 `chapters/index.json`。
- 统计每章字数和更新时间。

## text_audit.py

```bash
python scripts/text_audit.py chapters/0001_标题.md
```

用途：

- 统计字数、段落数、短段连续数、对话数量。
- 检查禁用引号 `「」『』`。
- 提示西文对话引号、括号内心独白、连续句末“了”。
- 统计高风险 AI 味词。

## hook_report.py

```bash
python scripts/hook_report.py --current 12
```

用途：

- 统计活跃 hook 和 core hook 是否超预算。
- 检查半衰期过期 hook。
- 检查活跃 hook 是否缺正文证据。

## hook_matrix.py

```bash
python scripts/hook_matrix.py --current 12
```

用途：

- 输出 hook 优先级和回收节奏分布。
- 检查上游依赖是否存在。
- 检查依赖环。
- 检查活跃 hook 是否缺预期回收或正文证据。
- 检查 resolved hook 是否缺回收证据。
- 列出被活跃依赖阻塞的 hook。

## structure_report.py

```bash
python scripts/structure_report.py
```

用途：

- 检查核心结构文件是否存在。
- 检查章节文件、章节摘要、情感弧光是否互相覆盖。
- 检查已定稿章节是否有 intent / plan / final-check。
- 检查 runtime 是否存在明显 dangling 状态。
- 检查 `chapters/index.json` 是否覆盖章节文件。

## skill_check.py

```bash
python scripts/skill_check.py
python scripts/skill_check.py --skill skill-name
```

用途：

- 检查 `skills/skill_registry.md` 表头。
- 检查 skill 名称是否合法。
- 检查状态是否为 `enabled` / `disabled` / `deprecated`。
- 检查入口文件路径是否存在。
- 在用户要求使用某 skill 时，确认该 skill 已注册。

## context_builder.py

```bash
python scripts/context_builder.py --chapter 12 --agent writer
python scripts/context_builder.py --chapter 12 --agent review
```

用途：

- 为每个 Agent 按章节构建上下文包，替代主模型手动判断该读哪些文件。
- 5 种 Agent（writer/polish/review/fixer/librarian）各有独立的必读内容、压缩摘要和排除文件配置。
- 内置 token 预算控制（Writer 18K / Polish 12K / Review 15K / Fixer 8K / Librarian 20K）。
- 输出包含必读内容、压缩摘要、禁止泄露提示、输出契约、省略文件清单和预算摘要。
- 产物路径：`story/runtime/chapter-XXXX.<agent>.context.md`

## prompt_compiler.py

```bash
python scripts/prompt_compiler.py --chapter 12 --agent writer
python scripts/prompt_compiler.py --chapter 12 --agent writer --context runtime/chapter-0012.writer.context.md
```

用途：

- 三层 prompt 编译（Base Prompt + 项目规则 + 本章任务），使每次 Agent 输入可复现、可追溯。
- Layer 1 从 `agents/<agent>.md` 读取角色定义；Layer 2 从项目规则文件编译；Layer 3 从 intent/plan/context 编译本章任务和半衰期风险提示。
- 产物路径：`story/runtime/chapter-XXXX.<agent>.prompt.md`

## gatekeeper.py

```bash
python scripts/gatekeeper.py --chapter 12 --stage final
```

用途：

- final-check 前必须运行的确定性门禁检查。所有检查不依赖 AI 判断。
- 检查流水线产物完整性（intent/plan/writer/polish/review/fixer 是否全部存在）。
- 检查 Review→Fixer 响应覆盖（必修问题是否被逐条处理）。
- 检查 hook 半衰期同步和禁止模式（括号内心独白、非标准引号）。
- 输出 PASSED/FAILED + 阻塞问题（BLOCKING）+ 非阻塞警告（WARN）。
- FAILED 时不得继续 final-check 或写入 canonical。
- 产物路径：`story/runtime/chapter-XXXX.gatekeeper.md`

## knowledge_index.py

```bash
python scripts/knowledge_index.py build
python scripts/knowledge_index.py query --chapter 12 --agent writer
python scripts/knowledge_index.py query --domain 中医方剂 --keyword 金疮药
```

用途：

- 关键词+元数据项目索引，第一版不依赖向量数据库。
- build 模式扫描项目文件（角色卡、大纲、章节、伏笔池），提取实体和文件元数据。
- query 模式按章节/领域/关键词查询，生成 knowledge_packet。
- 产物路径：`.nw_index/entity_index.json`、`story/runtime/chapter-XXXX.knowledge_packet.md`

## status.py

```bash
python scripts/status.py
python scripts/status.py --verbose
```

用途：

- 项目状态概览：章节进度、活跃/已回收 hook 数、超半衰期 hook 数、角色漂移风险、脚本数量、知识库索引状态。
- 根据检测结果给出建议下一步操作。
- `--verbose` 额外输出 runtime 文件详情。

## style_report.py

```bash
python scripts/style_report.py --chapter 12
python scripts/style_report.py --input chapters/0012_标题.md
```

用途：

- 定量文风报告：句长分布（短/中/长句比例）、对白密度、段落形态、AI 味模式命中次数。
- 输出具体的改进建议。
- 产物路径：`story/runtime/chapter-XXXX.style_report.md`

## character_drift_report.py

```bash
python scripts/character_drift_report.py --chapter 12
python scripts/character_drift_report.py --chapter 12 --character 林半夏
```

用途：

- 读取角色卡的 `cannot_do` 和 `speech_style` 约束，扫描章节文本查找疑似违背。
- 输出预警但不做最终判断——只标可疑点供 Review Agent 评估。
- 产物路径：`story/runtime/chapter-XXXX.character_drift.md`

## decompose_style.py

```bash
python scripts/decompose_style.py --input chapters/drafts/author-sample.md
```

用途：

- 文风拆解器。输入文本 → 输出三个产物：
  1. `style_analysis.md` — 人读的文风拆解报告（叙述视角、句法节奏、情绪表达、对白特点等）
  2. `style_profile.json` — 系统读的结构化配置
  3. `style_skill.md` — Agent 执行的风格规则

## import_inkos_project.py

```bash
python scripts/import_inkos_project.py /path/to/inkos-book
python scripts/import_inkos_project.py /path/to/inkos-book --dry-run
```

用途：

- 将 InkOS 项目文件映射迁移到 Narrative Workbench。不内置 InkOS 源码或 prompt 文本。
- 11 个文件映射规则（直接映射 + 需手动审核）。章节和角色卡批量迁移。
- `--dry-run` 预览模式。

## review_author_chapter.py

```bash
python scripts/review_author_chapter.py --chapter 12
python scripts/review_author_chapter.py --input chapters/drafts/my-chapter.md
```

用途：

- 共创模式：为作者手写章节生成审查简报。
- 脚本生成结构化任务包，不调用 AI 模型、不自动改写正文。真正的审查由 Claude Code/Codex 的 Review Agent 完成。
- 产物路径：`story/runtime/chapter-XXXX.author_review_brief.md`

## polish_author_chapter.py

```bash
python scripts/polish_author_chapter.py --chapter 12 --mode light
python scripts/polish_author_chapter.py --chapter 12 --mode anti-ai
```

用途：

- 共创模式：为作者手写章节生成润色简报。5 种润色模式各有独立指令集。
- 脚本生成结构化任务包，不调用 AI 模型、不自动改写正文。真正的润色由 Claude Code/Codex 的 Polish Agent 完成。
- 产物路径：`story/runtime/chapter-XXXX.author_polish_<mode>.md`

## relevance_resolver.py

```bash
python scripts/relevance_resolver.py --chapter 12 --agent writer
python scripts/relevance_resolver.py --chapter 12 --agent review
```

用途：

- **v0.3 上下文引擎核心。** 根据章节计划的 cast_ids/hook_ids/secret_ids 从结构化账本精确检索相关事实。
- 为 Writer/Polish/Review/Fixer/Librarian 构建不同预算的差异化任务包。
- 每条注入信息标注原因，省略的信息标注省略原因。
- 产物路径：`story/runtime/chapter-XXXX.<agent>.resolved.md`

## ledger_manager.py

```bash
python scripts/ledger_manager.py init
python scripts/ledger_manager.py add hooks '{"id":"HOOK_001",...}'
python scripts/ledger_manager.py query hooks --filter 'status=="open"'
python scripts/ledger_manager.py validate
```

用途：

- 管理 7 类结构化小说账本（facts/hooks/timeline/characters/relationships/secrets/locations）。
- 支持 CRUD、schema 验证、过滤器查询和从章节导演表提取事实。
- 产物路径：`story/ledger/*.jsonl`

## render_views.py

```bash
python scripts/render_views.py all
python scripts/render_views.py hooks
```

用途：

- 将 JSONL 账本渲染为作者可读的 Markdown 视图（伏笔看板、知识边界矩阵、时间线、关系网络）。
- 产物路径：`story/views/*.md`

## director_sheet.py

```bash
python scripts/director_sheet.py --chapter 19 --from-template
python scripts/director_sheet.py --chapter 19 --validate
```

用途：

- 生成章节导演表（全章蓝图：情绪曲线、信息释放计划、语言节奏、场景接力链）。
- 支持从模板生成和从已有 intent/plan 提取。
- `--validate` 检查导演表完整性。
- 产物路径：`story/plans/chapter-NNNN_director_sheet.yaml`

## sync_skills.py

```bash
python scripts/sync_skills.py
python scripts/sync_skills.py --dry-run
python scripts/sync_skills.py --clean
```

用途：

- 将 `skills/`（唯一正式来源）同步到平台原生 Skills 入口包装。
- 生成 `.claude/skills/`（Claude Code）和 `.agents/skills/`（Codex）。
- 同时生成 `.codex/agents/` 和 `.codex/hooks.json`。
- `--dry-run` 预览不写入，`--clean` 清除已废弃的包装文件。

## 边界

这些脚本只做确定性辅助，不做创作判断。不要用脚本自动总结章节、自动回收 hook、自动润色正文或自动调度 Agent。审查和润色脚本生成的是结构化任务包，不调用 AI 模型。
