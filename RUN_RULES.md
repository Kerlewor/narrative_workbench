# Run Rules / Python 辅助运行规则

本文件集中规定 AI 在小说工作流中必须运行哪些 Python 辅助脚本。脚本只做确定性检查、索引、统计和报告；不做创作判断，不自动总结章节，不自动回收 hook，不自动润色正文，不自动调度 Agent。

## 总原则

1. 运行脚本前，先确认当前工作目录是项目根目录。
2. 脚本报 `ERROR` 时，必须先修复系统问题，再继续写作。
3. 脚本报 `WARN` 时，必须在对应 runtime 文件中记录处理方式。
4. 不得把脚本输出当成语义结论。脚本只指出结构、格式、预算、依赖和同步问题。
5. 若当前目录是 `_frameworks/narrative_workbench`，除非用户明确要求修改模板，否则先用 `create_project.py` 创建新项目。

## 阶段门禁

| 阶段 | 必须运行 | 结果写入 |
| --- | --- | --- |
| 新书初始化后 | `python3 scripts/doctor.py`、`python3 scripts/structure_report.py` | `story/current_focus.md` 或初始化记录 |
| 搭建大纲完成后 | `python3 scripts/structure_report.py`、`python3 scripts/doctor.py` | `story/current_focus.md` |
| 注册或修改 skill 后 | `python3 scripts/skill_check.py`、`python3 scripts/doctor.py` | skill request 或修改说明 |
| 规划第 N 章前 | `python3 scripts/hook_report.py --current N-1`、`python3 scripts/hook_matrix.py --current N-1` | `chapter-000N.intent.md` 的 Hook 预算 |
| 批量规划前 | `python3 scripts/doctor.py`、`python3 scripts/hook_report.py --current N-1`、`python3 scripts/hook_matrix.py --current N-1`、`python3 scripts/structure_report.py` | `batch-000N-000M.plan.md` |
| Writer 前 | 建议 `python3 scripts/context_builder.py --chapter N --agent writer`；必须读取 intent / plan / hook_protocol | `chapter-000N.writer.md` handoff |
| Polish 前 | 建议 `python3 scripts/context_builder.py --chapter N --agent polish`；必须读取 style_profile / style_guide | `chapter-000N.polish.md` handoff |
| Review 前 | 建议 `python3 scripts/context_builder.py --chapter N --agent review`；若已有候选正文文件，运行 `python3 scripts/text_audit.py <候选正文路径>` | `chapter-000N.review.md` |
| Fixer 前 | 建议 `python3 scripts/context_builder.py --chapter N --agent fixer` | `chapter-000N.fixer.md` handoff |
| Final-check 前 | **必须** `python3 scripts/gatekeeper.py --chapter N --stage final`；`python3 scripts/text_audit.py chapters/000N_标题.md` 或候选稿路径；`python3 scripts/hook_report.py --current N`；`python3 scripts/hook_matrix.py --current N` | `chapter-000N.final-check.md` |
| 正文写入后 | `python3 scripts/chapter_index.py --write`、`python3 scripts/doctor.py` | `chapter-000N.final-check.md` |
| 批末审计 | `python3 scripts/doctor.py`、`python3 scripts/chapter_index.py --check`、`python3 scripts/hook_report.py --current M`、`python3 scripts/hook_matrix.py --current M`、`python3 scripts/structure_report.py` | `batch-000N-000M.audit.md` |
| 进入新卷前 | `python3 scripts/structure_report.py`、`python3 scripts/hook_matrix.py --current N`、`python3 scripts/doctor.py` | `story/current_focus.md` 和新卷 plan |
| 手动改状态文件后 | `python3 scripts/doctor.py`、必要时 `python3 scripts/structure_report.py` | 修改说明或 drift check |

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
| `gatekeeper.py` | 检查流水线产物完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式 | 替代主模型做创造性判断 |

## 失败处理

### doctor.py 失败

停止写作，先修：

- 缺失文件。
- JSON 解析错误。
- hook 表头不符合协议。
- runtime 状态非法。
- Claude Code agent frontmatter 错误。

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
