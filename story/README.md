# Story 工作区

`story/` 存放小说事实源之外的全部控制文件。正文事实以 `chapters/` 为最高准则，`story/` 负责让 AI 维持连续性。

## 文件分工

**状态账本（每章更新）：**
- `current_focus.md`：下一步写什么，接下来 1-3 章方向。
- `current_state.md`：当前章节、地点、人物状态、敌我关系、最近事实（≤5 条）。
- `chapter_summaries.md`：每章摘要，按卷分段。
- `pending_hooks.md`：正文已经成立的伏笔。已回收/放弃超一卷的钩子归档。
- `emotional_arcs.md`：谁在每章发生了变化，按卷分段。

**系统协议（不改或很少改）：**
- `system_protocol.md`：系统边界、状态机、反馈回路、定稿门禁。
- `state_contract.md`：正文、Markdown 状态和 JSON 镜像之间的同步契约。
- `hook_protocol.md`：伏笔生命周期、半衰期、升级、回收审计规则。

**项目设定（大纲阶段填写）：**
- `brief.md`：项目一句话简介和核心卖点。
- `author_intent.md`：作者最核心的创作意图。
- `book_rules.md`：类型规则、世界观铁律、视角规则、节奏规则。
- `character_matrix.md`：角色矩阵、群像规则、性格分布检查、关系张力地图。

**风格控制：**
- `style_guide.md`：写前自检、六步人物心理分析、代入感支柱、格式规则。
- `style_profile.md`：从用户偏好和样章中提取的文风画像。
- `style_blacklist.md`：文笔负面清单，禁止 AI 腔、主题金句、万能氛围句。
- `fiction_style_skill.md`：本书专属文风规则和意象库。
- `ai_writing_repair_plan.md`：AI 写作常见问题与修复顺序。
- `style_samples/`：用户提供的风格样本。

**诊断与审计：**
- `audit_drift.md`：Drift check 记录模板，写下一章前用于对比正文与状态文件。

**子目录：**
- `outline/`：故事框架、分卷地图、扩写蓝图、题材安全手册、发现问卷。
- `runtime/`：每章 intent/plan + Agent 产出 + final-check + 批量 plan/audit。已定稿跨卷 runtime 可归档到 `volume-N/` 子目录。
- `roles/`：角色卡（含 Personality Lock、Behavioral Constraints、压力测试结论）。
- `state/`：机器可读 JSON 镜像（current_state.json、chapter_summaries.json、hooks.json、manifest.json）。

## 使用原则

1. 正文已经写出的事实才能进入状态文件。
2. 规划中的想法留在 `runtime/`，不能提前写进伏笔池。
3. 每章完成后立刻同步状态，提交顺序以 `state_contract.md` 为准。
4. 发现状态与正文冲突时，以正文为准修状态。
