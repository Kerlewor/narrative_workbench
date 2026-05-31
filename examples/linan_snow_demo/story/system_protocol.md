# System Protocol / 小说工作流系统协议

本框架不是一组松散提示词，而是一个闭环系统。系统目标是：**在长篇创作中持续产出章节，同时保持事实一致、伏笔可回收、角色弧光可追踪、风格可控。**

## 系统组件

| 组件 | 职责 | 主要文件 | 不能做 |
| --- | --- | --- | --- |
| 用户 | 提供创作意图、决策、偏好 | `author_intent.md`、对话 | 不直接维护状态细节 |
| 主会话 | 调度、规划、定稿、状态同步、管理 Agent 生命周期 | `CLAUDE.md`、`runtime/*` | 不跳过审计直接写状态 |
| Project Librarian | 会话入口上下文路由与压缩 | `agents/project-librarian.md`、`runtime/*context.md` | 不写正文、不改状态、不调度 Agent |
| Writer | 生成草稿 | `agents/writer.md` | 不润色、不改状态 |
| Polish | 语言二修 | `agents/polish.md` | 不新增事实、不改情节 |
| Review | 找问题 | `agents/review.md` | 不改正文 |
| Fixer | 按报告修复 | `agents/fixer.md` | 不自由发挥 |
| 正文库 | 最高事实源 | `chapters/` | 不存审阅报告和草稿 |
| 状态层 | 压缩事实和索引 | `story/*.md`、`story/state/*.json` | 不记录正文未发生内容 |
| 规划层 | 候选未来 | `story/runtime/*` | 不冒充事实源 |
| Skill 层 | 可插拔专项能力 | `skills/*`、`story/runtime/*.skill-*.md` | 不直接改 canonical |

## 系统边界

### Canonical 区

以下文件是 canonical，只有主会话在最终检查后可以更新：

- `chapters/*.md`
- `chapters/index.json`
- `story/current_state.md`
- `story/chapter_summaries.md`
- `story/pending_hooks.md`
- `story/emotional_arcs.md`
- `story/current_focus.md`
- `story/state/*.json`

### Working 区

以下文件是 working，允许记录计划、草稿、审阅和中间判断：

- `story/runtime/chapter-*.intent.md`
- `story/runtime/chapter-*.plan.md`
- `story/runtime/chapter-*.writer.md`
- `story/runtime/chapter-*.polish.md`
- `story/runtime/chapter-*.review.md`
- `story/runtime/chapter-*.fixer.md`
- `story/runtime/batch-*.plan.md`
- `story/runtime/batch-*.audit.md`
- `story/runtime/session-*-context.md`
- `story/runtime/chapter-*.context.md`
- `story/runtime/chapter-*.prompt.md`
- `story/runtime/chapter-*.gatekeeper.md`
- `story/runtime/chapter-*.final-check.md`
- `story/runtime/chapter-*.resolved.md`
- `story/runtime/chapter-*.style_report.md`
- `story/runtime/chapter-*.character_drift.md`
- `story/runtime/chapter-*.knowledge_packet.md`
- `story/runtime/chapter-*.session-close.md`
- `story/runtime/chapter-*_scene_handoffs.yaml`
- `story/runtime/chapter-*_coherence_review.md`
- `story/runtime/*.skill-*.md`

Agent 只能输出到 working 区。canonical 区由主会话统一提交。

## 章节状态机

章节状态以 `story/runtime/chapter-000N.intent.md` 的 YAML frontmatter `status` 字段为 canonical 记录。主会话在每个阶段完成后更新此字段。Agent handoff 中的 `status` 是阶段产物，以 intent.md 为准。

| 状态 | 含义 | 允许转移 |
| --- | --- | --- |
| `planned` | intent / plan 完成 | `drafted`、`superseded` |
| `drafted` | Writer 草稿完成 | `polished`、`superseded` |
| `polished` | Polish 润色完成 | `reviewed`、`superseded` |
| `reviewed` | Review 报告完成 | `fixed`、`needs-rewrite` |
| `fixed` | Fixer 修复完成 | `final-check` |
| `final-check` | 主会话终检中 | `final-aligned`、`needs-repair` |
| `final-aligned` | 正文和状态同步完成 | 无 |
| `superseded` | 被正文或新规划取代 | 无 |
| `needs-repair` | 定稿门禁未通过 | `fixed`、`superseded` |
| `needs-rewrite` | 审阅判定结构性失败 | `drafted`、`superseded` |

任何状态倒退都必须写明原因。

## 反馈回路

### 快回路：单章质量

Writer -> Polish -> Review -> Fixer -> 主会话 final-check。

目标：修正文风、连续性、人物逻辑、信息边界和格式问题。

### 入口回路：上下文压缩

Project Librarian -> Context Packet -> 主会话读取关键源文件。

目标：在不替代事实源的前提下，降低每次启动的上下文负担，明确本轮必读文件、可暂缓文件、hook 风险、状态冲突和脚本门禁。

### 中回路：批量连续性

batch-plan -> 单章流水线 x 3-5 -> batch-audit。

目标：检查连续高压、hook 预算、角色弧光、状态漂移。

### 慢回路：全书结构

volume_map -> chapter_summaries -> emotional_arcs -> pending_hooks -> volume_map。

目标：确认每卷 Objective / KR 真的被章节推进，必要时调整后续卷纲。

## 系统不变量

1. 正文是最高事实源。
2. planning 不能污染 canonical。
3. Agent 不直接改 canonical。
4. 每章至少产生一个可观察状态变化。
5. hook 的 open / advance / resolve 必须有正文证据。
6. 状态文件必须能被最近正文解释。
7. 角色只能基于其信息边界行动。
8. 批量流水线中不得同时写同一个 canonical 文件。
9. Context Packet 不是 canonical；它只能指路，不能覆盖原始规则、状态文件或正文。

## 常见系统故障与修复

| 故障 | 症状 | 修复 |
| --- | --- | --- |
| 状态漂移 | 摘要、伏笔、JSON 与正文冲突 | 以正文为准修状态，runtime 标记 superseded |
| 候选污染 | plan 中想写的 hook 进入 pending_hooks | 从伏笔池移除，回到 runtime |
| Agent 越权 | Polish/Fixer 新增剧情或改状态 | 回滚该段，重新按职责处理 |
| 并行竞争 | 多章流水线同时改状态 | Agent 只写 runtime，主会话按章节顺序提交 canonical |
| 上下文过载 | 每次会话读取大量规则后仍抓不住本轮重点 | 先调用 Project Librarian 输出 Context Packet，再由主会话读取关键源文件 |
| 压缩误导 | Context Packet 与原文件不一致 | 以原文件和正文为准，重建 Context Packet |
| 弧光空转 | 角色出场很多但章末无变化 | 降低戏份或补可见选择与后果 |
| 性格漂移 | 角色行为偏离 Personality Lock 和 Behavioral Constraints，且无情节理由 | 对照角色卡压力测试结论判断是成长还是漂移；若为漂移则修正行为或更新角色卡 |
| 伪回收 | 只解释设定，没有情绪或局面变化 | 追加状态改变、意象回环或不可逆后果 |
| 上帝视角 | 角色知道未获知信息 | 改为误判、推理、旁观证据或删除 |
| 会话断裂 | 持久 Agent 上下文过载，输出质量下降或行为漂移 | 记录 session-close 文件，创建新 Agent 会话并重新读取项目基线 |

## Python 辅助边界

具体运行门禁见根目录 `RUN_RULES.md`。

Python 脚本属于“确定性辅助层”，只允许做：

- 文件存在性检查。
- JSON 合法性检查。
- 章节索引生成或校验。
- 字数、段落、引号、风险词统计。
- hook 预算和半衰期报告。
- hook 依赖、缺证据、回收元数据完整性报告。
- 分卷、章节、摘要、runtime 覆盖关系检查。

Python 脚本不允许做：

- 自动总结章节。
- 自动判定人物弧光。
- 自动判定 hook 已回收。
- 自动润色正文。
- 自动调度 Claude Code subagent。
- 绕过 final-check 直接提交 canonical 状态。

## 定稿门禁

主会话写入 `chapters/` 前必须通过以下检查。执行时使用 `story/runtime/_template.final-check.md` 作为操作清单。

1. 最近正文连续性通过。
2. Hook 账通过（含半衰期）。
3. 角色弧光账通过。
4. 人格一致性通过（对照角色卡 Personality Lock 和压力测试结论）。
5. 信息边界通过。
6. 格式规则通过（含 style_blacklist、scene beat 落点）。
7. Agent 输出没有审阅报告残留。
8. canonical 状态更新清单明确。
9. gatekeeper.py 已通过（确定性门禁——流水线完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式）。
10. Python 辅助脚本已运行（text_audit.py、chapter_index.py、必要时 hook_report.py / hook_matrix.py）。
