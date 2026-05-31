# State Contract / 状态同步契约

本文件定义正文、Markdown 状态和 JSON 状态之间的同步关系。

## 权威顺序

1. `chapters/*.md`：最高事实源。
2. `story/chapter_summaries.md`：正文事实的人工摘要。
3. `story/current_state.md`、`story/pending_hooks.md`、`story/emotional_arcs.md`：当前状态账本。
4. `story/state/*.json`：机器可读镜像。
5. `story/runtime/*`：规划和流水线产物，不是事实源。

当冲突发生时，按上述顺序裁决。

## 同步规则

- 每章定稿后，先更新 Markdown 状态，再更新 JSON 镜像。
- JSON 只能镜像 Markdown 已确认内容，不能独立新增事实。
- 如果 JSON 与 Markdown 冲突，以 Markdown 为准修 JSON。
- 如果 Markdown 与正文冲突，以正文为准修 Markdown 和 JSON。
- runtime 中未标记 `final-aligned` 的内容不得进入 JSON。

## Markdown 到 JSON 映射

| Markdown | JSON | 说明 |
| --- | --- | --- |
| `current_state.md` | `state/current_state.json` | 当前章节、地点、目标、敌我、活跃/已回收 hook |
| `chapter_summaries.md` | `state/chapter_summaries.json` | 章节摘要索引 |
| `pending_hooks.md` | `state/hooks.json` | 伏笔池 |
| `chapters/index.json` | 无 | 正文章节索引，独立维护 |

## 提交顺序

1. 写入最终正文 `chapters/000N_标题.md`。
2. 更新 `chapters/index.json`。
3. 更新 `chapter_summaries.md`。
4. 更新 `emotional_arcs.md`。
5. 更新 `pending_hooks.md`。
6. 更新 `current_state.md`。
7. 更新 `current_focus.md`。
8. 更新 `story/state/*.json`。
9. 将 runtime 标记为 `final-aligned`。

## 禁止

- 禁止 Agent 直接改 canonical 状态。
- 禁止把 Review Report 或 Fixer 修复清单写入正文。
- 禁止 JSON 与 Markdown 记录不同版本的事实。
- 禁止为了保持计划而改写正文事实。

