# Run Rules / Python 辅助运行规则

本文件集中规定 AI 在小说工作流中必须运行哪些 Python 辅助脚本。脚本只做确定性检查、索引、统计和报告；不做创作判断，不自动总结章节，不自动回收 hook，不自动润色正文，不自动调度 Agent。

## 总原则

1. 运行脚本前，先确认当前工作目录是项目根目录。
2. 脚本报 `ERROR` 时，必须先修复系统问题，再继续写作。
3. 脚本报 `WARN` 时，必须在对应 runtime 文件中记录处理方式。
4. 不得把脚本输出当成语义结论。脚本只指出结构、格式、预算、依赖和同步问题。
5. 若当前目录是 `_frameworks/narrative_workbench`，除非用户明确要求修改模板，否则先用 `create_project.py` 创建新项目。

### Python 不可用时的降级规则

当用户无 Python 环境或选择不使用脚本时，AI 必须手动执行以下等效检查：

| 脚本 | 降级方案 |
|---|---|
| `doctor.py` | AI 逐项检查：核心文件存在性（对照 REQUIRED_FILES 列表）、JSON 可解析性、agent frontmatter 格式、hook 表头合法性、runtime 状态枚举 |
| `chapter_index.py` | AI 扫描 `chapters/` 目录，手动更新 `chapters/index.json` |
| `text_audit.py` | AI 扫描候选稿全文，对照 `style_blacklist.md` 逐项检查 |
| `hook_report.py` | AI 读取 `pending_hooks.md`，人工计算活跃 hook 数、core 数、半衰期到期项 |
| `hook_matrix.py` | AI 检查 hook 依赖环、阻塞关系、回收元数据完整性 |
| `structure_report.py` | AI 对比章节文件、摘要、弧光、runtime、索引的覆盖关系 |
| `gatekeeper.py` | AI 逐项执行 gatekeeper 检查清单：流水线产物完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式、intent 状态 |
| `skill_check.py` | AI 检查 skill 注册表表头、名称合法性和入口文件存在性 |
| `context_builder.py` | AI 按 Agent 类型手动收集必读文件、压缩摘要、排除文件，构建上下文包 |
| `prompt_compiler.py` | AI 按三层结构手动拼接 Agent prompt |
| `dashboard.py` | AI 手动汇总当前进度、到期伏笔、知识边界、时间线风险和下一步建议，写入 `story/DASHBOARD.md` |
| `diff_workflow.py` / `nw diff` | AI 手动维护修改候选编号、索引、单条详情、接受/拒绝决策和新版本输出 |
| `scene_card.py` / `nw scene` | AI 手动创建或列出场景卡，并把自然语言修改落实到 Markdown 场景卡 |
| `voice_lab.py` / `nw voice-lab` | AI 手动生成角色声线测试任务包，输出会说/不会说的候选检查要求 |
| `export_book.py` / `nw export` | AI 手动收集正式章节并导出 Markdown、DOCX 或 EPUB |
| 其余新脚本 | AI 执行等效的手动检查或分析 |

降级模式下的产物应写入与脚本相同的 runtime 路径，并标注 `(manual)` 以区分。

## 阶段门禁

| 阶段 | 必须运行 | 结果写入 |
| --- | --- | --- |
| 新书初始化后 | `python scripts/doctor.py`、`python scripts/structure_report.py` | `story/current_focus.md` 或初始化记录 |
| 搭建大纲完成后 | `python scripts/structure_report.py`、`python scripts/doctor.py` | `story/current_focus.md` |
| 注册或修改 skill 后 | `python scripts/skill_check.py`、`python scripts/doctor.py` | skill request 或修改说明 |
| 规划第 N 章前 | `python scripts/hook_report.py --current N-1`、`python scripts/hook_matrix.py --current N-1` | `chapter-000N.intent.md` 的 Hook 预算 |
| 批量规划前 | `python scripts/doctor.py`、`python scripts/hook_report.py --current N-1`、`python scripts/hook_matrix.py --current N-1`、`python scripts/structure_report.py` | `batch-000N-000M.plan.md` |
| Writer 前 | 建议 `python scripts/relevance_resolver.py --chapter N --agent writer`（优先）或 `python scripts/context_builder.py --chapter N --agent writer` + `python scripts/prompt_compiler.py --chapter N --agent writer`；必须读取 intent / plan / hook_protocol | `chapter-000N.writer.md` handoff |
| Polish 前 | 建议 `python scripts/context_builder.py --chapter N --agent polish` + `python scripts/prompt_compiler.py --chapter N --agent polish`；必须读取 style_profile / style_guide | `chapter-000N.polish.md` handoff |
| Review 前 | 建议 `python scripts/context_builder.py --chapter N --agent review` + `python scripts/prompt_compiler.py --chapter N --agent review`；若已有候选正文文件，运行 `python scripts/text_audit.py <候选正文路径>` | `chapter-000N.review.md` |
| Fixer 前 | 建议 `python scripts/context_builder.py --chapter N --agent fixer` + `python scripts/prompt_compiler.py --chapter N --agent fixer` | `chapter-000N.fixer.md` handoff |
| Final-check 前 | **必须** `python scripts/gatekeeper.py --chapter N --stage final`；`python scripts/text_audit.py chapters/000N_标题.md` 或候选稿路径；`python scripts/hook_report.py --current N`；`python scripts/hook_matrix.py --current N` | `chapter-000N.final-check.md` |
| 正文写入后 | `python scripts/chapter_index.py --write`、`python scripts/doctor.py` | `chapter-000N.final-check.md` |
| 批末审计 | `python scripts/doctor.py`、`python scripts/chapter_index.py --check`、`python scripts/hook_report.py --current M`、`python scripts/hook_matrix.py --current M`、`python scripts/structure_report.py` | `batch-000N-000M.audit.md` |
| 进入新卷前 | `python scripts/structure_report.py`、`python scripts/hook_matrix.py --current N`、`python scripts/doctor.py` | `story/current_focus.md` 和新卷 plan |
| 手动改状态文件后 | `python scripts/doctor.py`、必要时 `python scripts/structure_report.py` | 修改说明或 drift check |
| 初始化账本 | `python scripts/ledger_manager.py init` + `python scripts/ledger_manager.py validate` | `story/ledger/*.jsonl` |
| 更新视图 | `python scripts/render_views.py all` | `story/views/*.md` |
| 同步 Skills | `python scripts/sync_skills.py` | `.claude/skills/` + `.agents/skills/` |
| 章节导演表 | `python scripts/director_sheet.py --chapter N --from-template` | `story/plans/chapter_NNNN_director_sheet.yaml` |
| 更新写作控制台 | `python scripts/dashboard.py` 或 `python scripts/nw dashboard` | `story/DASHBOARD.md` |
| 生成共创 diff | `python scripts/nw diff generate --chapter N --original <作者稿> --revised <候选润色稿>` | `chapter-000N.diff_index.md` + `patch_candidates.jsonl` |
| 应用共创 diff | `python scripts/nw diff apply --chapter N --accept 01,03 --reject 02` | `chapters/drafts/chapter-000N.author.v2.md` + `decision_log.md` |
| 创建场景卡 | `python scripts/nw scene create --chapter N --id scene_01 --title 标题` | `story/plans/scenes/chapter-000N/scene_01.md` |
| 角色声音实验 | `python scripts/nw voice-lab --character 角色名 --line 台词` | `story/runtime/voice_lab.角色名.md` |
| 导出成书 | `python scripts/nw export --format docx --output exports/book.docx` | `exports/` 或指定路径 |

## 脚本职责

| 脚本 | 职责 | 不负责 |
| --- | --- | --- |
| `doctor.py` | 全局文件、JSON、runtime 状态、hook 表头、agent frontmatter 体检 | 判断剧情好坏 |
| `create_project.py` | 从模板创建新书项目目录并生成 `PROJECT.md` | 在模板目录内直接写作 |
| `chapter_index.py` | 扫描章节文件，检查或重写 `chapters/index.json` | 总结章节 |
| `text_audit.py` | 检查引号、短段、风险词、括号内心独白等格式/词句风险 | 润色正文 |
| `hook_report.py` | 活跃 hook 数、core hook 数、半衰期、正文证据缺失 | 判断 hook 是否该回收 |
| `hook_matrix.py` | hook 依赖、依赖环、阻塞关系、回收元数据完整性 | 设计伏笔 |
| `structure_report.py` | 章节、摘要、弧光、runtime、索引覆盖关系 | 判断故事结构是否精彩 |
| `skill_check.py` | skill 注册表、状态、入口文件检查 | 判断 skill 输出质量 |
| `context_builder.py` | 按 Agent 类型和章节构建上下文包，控制 token 预算 | 替代主模型判断哪些文件该读 |
| `prompt_compiler.py` | 按三层结构编译 Agent prompt（Base + 项目规则 + 本章任务） | 替代主模型手动拼接 prompt |
| `gatekeeper.py` | 检查流水线产物完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式 | 替代主模型做创造性判断 |
| `knowledge_index.py` | 扫描项目文件构建实体索引，支持关键词查询和知识包生成 | 替代全文语义理解 |
| `status.py` | 项目状态概览：章节进度、hook 统计、角色漂移风险、建议下一步 | 替代主模型手动盘点 |
| `style_report.py` | 分析章节句长分布、对白密度、AI 味模式命中 | 润色正文 |
| `character_drift_report.py` | 对照角色约束扫描章节文本，输出疑似漂移预警 | 做最终漂移判断 |
| `decompose_style.py` | 输入文本 → 输出 style_analysis.md + style_profile.json + style_skill.md | 替代人工文风分析 |
| `import_inkos_project.py` | 将 InkOS 项目文件映射迁移到 Narrative Workbench | 处理语义不兼容内容 |
| `review_author_chapter.py` | 为手写章节生成 Review 审查简报（共创模式） | 替代 Review Agent |
| `polish_author_chapter.py` | 为手写章节生成 Polish 润色简报（共创模式，5 种模式） | 替代 Polish Agent |
| `relevance_resolver.py` | 精确相关性上下文注入 — 根据章节 plan 的 cast_ids/hook_ids/secret_ids 从账本检索，为不同 Agent 构建差异化任务包 | 替代 context_builder 核心逻辑 |
| `ledger_manager.py` | 管理结构化小说账本（JSONL CRUD + 验证 + 抽取） | 替代手动维护 Markdown 状态 |
| `render_views.py` | 从 JSONL 账本渲染作者可读 Markdown 视图 | 不做语义分析 |
| `director_sheet.py` | 生成和验证章节导演表 | 不做创作决策 |
| `sync_skills.py` | 将 skills/ 同步到 .claude/skills/ 和 .agents/skills/ 平台入口 | 不维护重复内容 |
| `dashboard.py` | 生成 Markdown-native 写作控制台与 JSON 协议摘要 | 不替代作者判断故事下一步 |
| `diff_workflow.py` | 生成分层 diff 索引、单条详情、JSONL 修改候选，并按编号应用作者决策 | 不替代作者判断是否采纳修改 |
| `nw` | 统一本地入口，封装 doctor/dashboard/gatekeeper/diff 等常用命令 | 不替代 Claude Code/Codex 的创作调度 |
| `scene_card.py` | 创建和列出 Markdown 场景卡 | 不替代作者/主会话设计场景内容 |
| `voice_lab.py` | 生成角色声线实验任务包 | 不替代作者确认角色声音 |
| `export_book.py` | 将正式章节导出为 Markdown、DOCX 或 EPUB | 不替代专业排版软件 |

## 失败处理

### doctor.py 失败

停止写作，先修：

- 缺失文件。
- JSON 解析错误。
- hook 表头不符合协议。
- runtime 状态非法。
- Claude Code agent frontmatter 错误。

### gatekeeper.py 阻塞

gatekeeper 报 FAILED 时，**不得继续 final-check 或写入 canonical**。必须：

- 逐条修复 BLOCKING 问题（缺少的产物补上，未响应的 Review 项交给 Fixer 处理，到期的 hook 在正文中推进或正式 defer/dormant）。
- 修复后重新运行 gatekeeper，直到 PASSED。
- WARN 项不阻塞，但必须记录到 final-check 中。

### hook_report.py / hook_matrix.py 警告

不要自动改 hook。必须在 intent 或 batch plan 中写明：

- 本章推进哪个过期 hook。
- 哪个 hook 明确 defer，理由是什么。
- 哪个依赖阻塞了回收。
- 是否需要减少新开 hook。

### text_audit.py 警告

交给 Polish / Fixer 处理格式和词句风险。不得因此擅自改剧情。

### structure_report.py 警告

主会话判断是否需要：

- 补 chapter summary。
- 补 emotional arcs。
- 补 final-check。
- 修 chapters/index。
- 标记 runtime 为 `superseded`。
