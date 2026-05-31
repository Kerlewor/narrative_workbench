# Narrative Workbench (Codex)

> 与 `CLAUDE.md` 同源。本文件为 Codex CLI/IDE Extension 的入口协议。

## 核心原则（不可违反）

1. **canonical 文件永远优先于工作草稿。** `chapters/` 正文是最高事实源。Agent 输出和 runtime 文件只代表规划或建议。
2. **先编译上下文包，再执行任务。** 每次写作/审阅/润色前必须先运行 Relevance Resolver（`relevance_resolver.py`）或 Context Builder 生成任务包。
3. **不得绕过门禁。** gatekeeper 通过 + final-check 完成后，才能写入 `chapters/`。
4. **写前 drift check，写后状态同步。** 写前检查伏笔/角色/状态冲突；写后按 `story/state_contract.md` 顺序同步。
5. 脚本运行门禁见 `RUN_RULES.md`。完整系统原则见 `workflow/constitution.md`，章节生命周期见 `workflow/lifecycle.md`。

## 模板保护

若当前目录路径包含 `_frameworks/narrative_workbench`，先运行:
```bash
python scripts/create_project.py "项目名"
```

## 目录结构

```text
chapters/         正文章节（canonical）
story/outline/    大纲、分卷（canonical）
story/roles/      角色卡（canonical）
story/ledger/     结构化事实账本（JSONL）
story/views/      作者可读视图（Markdown）
story/plans/      章节导演表（YAML）
story/runtime/    临时任务包、审阅结果（working 区）
workflow/         系统原则与协议文档
scripts/          确定性 Python 脚本
skills/           可插拔 Skill（正式来源）
.agents/skills/   Codex 原生 Skills 入口（同步脚本生成）
```

## 会话启动

每次新会话:
1. **检查 Python 环境** — 有 Python 则使用脚本，无 Python 则手动等效执行
2. **调用 `project-librarian`** 或运行 `relevance_resolver.py`（优先）/ `context_builder.py`（备选）生成上下文导航
3. **读取以下原文（Context Packet 可替代部分）:**
   - 必须读原文: `workflow/constitution.md`, `story/system_protocol.md`, `story/state_contract.md`, `story/hook_protocol.md`, `story/outline/story_frame.md`, `story/outline/volume_map.md`
   - 可按需: `story/pending_hooks.md`, `story/emotional_arcs.md`, `story/current_focus.md`, `story/current_state.md`, `story/chapter_summaries.md`
4. Context Packet 与原文件冲突时以原文件为准

## Agent 调度

| Agent | 职责 | 会话 |
|---|---|---|
| project-librarian | 上下文路由 | 一次性，每次独立 |
| novel-writer | 写原始草稿 | 持久，8 章后重置 |
| novel-polish | 语言润色、去 AI 味 | 持久，8 章后重置 |
| novel-review | 审阅，找漂移和 bug | 持久，8 章后重置 |
| novel-fixer | 按 Review 报告修复 | 持久，8 章后重置 |

Agent 在同一主会话内持续存活。首次创建时发送项目基线，后续章节只发送本章任务包。Agent 只能输出到 `story/runtime/`，不得直接改 canonical。

## 用户命令路由

| 命令 | 路由 |
|---|---|
| `搭建大纲` | `skills/import_outline/` — 五阶段流程 |
| `导入大纲` | `skills/import_outline/` — 导入 + 缺口检测 |
| `写第N章` | `skills/write_chapter/` — 完整流水线 |
| `审阅第N章` | `skills/review_chapter/` — 返修流水线 |
| `审查第N章` (共创) | `skills/review_chapter/` — 一致性审查 |
| `润色第N章 --模式 X` (共创) | `skills/polish_author_draft/` — 5 种润色模式 |
| `第N章写作简报` | `skills/plan_chapter/` — 约束简报 |
| `深化角色 <角色名>` | `skills/deepen_character/` — 四轮讨论 |

## 写前 SOP（摘要）

1. 确认位置: `chapters/index.json` + `volume_map.md` + 上一章正文
2. 盘点钩子: `hook_report.py` + `hook_matrix.py`
3. 盘点角色: 出场角色 + Personality Lock + Behavioral Constraints
4. 确认节点: 本章推进目标
5. 弧光差值: 章初状态 → 章末状态
6. 复习禁令: 世界观铁律 + 视角边界

## 写后 SOP（摘要）

每章完成后按 `story/state_contract.md` 顺序同步: chapters → chapter_summaries → emotional_arcs → pending_hooks → current_state → current_focus → JSON 镜像。将 runtime 标记为 `final-aligned`。

## 确定性门禁

```bash
# 新书/批量/进入新卷后
python scripts/doctor.py && python scripts/structure_report.py

# 规划前
python scripts/hook_report.py --current N-1 && python scripts/hook_matrix.py --current N-1

# Final-check 前 (必须)
python scripts/gatekeeper.py --chapter N --stage final
python scripts/text_audit.py chapters/000N_标题.md

# 正文写入后
python scripts/chapter_index.py --write && python scripts/doctor.py
```

## 硬性格式规则

- 对话使用中文双引号
- 禁止内心独白放括号里
- 章尾至少留一个钩子
- 每场冲突必须推进情节/关系/后台碎片/人物后效之一
- 日常场景必须承担埋伏笔/推关系/建立反差中的至少一项
