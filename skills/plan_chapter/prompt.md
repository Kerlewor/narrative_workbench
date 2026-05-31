# plan_chapter — 章节规划与写作简报

为指定章节生成意图文件（intent）、施工计划（plan）和写作约束简报。

## 触发条件

- `规划第N章`
- `第N章写作简报`
- `writing brief 第N章`

## 工作流

1. **确认位置** — 读取 `volume_map.md` 确认本章在整卷中的功能和位置
2. **Hook 审计** — 运行 `hook_report.py --current N-1` + `hook_matrix.py --current N-1`（N=1 时跳过）
3. **角色盘点** — 读取角色卡，确认出场角色 + 行为边界（Personality Lock / Behavioral Constraints）
4. **弧光差值** — 确认章初状态 → 章末状态 → 变化证据
5. **禁止清单** — 列出本章不得提前泄露的信息
6. **生成 intent** — `story/runtime/chapter-000N.intent.md`（本章在整卷中的位置和功能）
7. **生成 plan** — `story/runtime/chapter-000N.plan.md`（场景级施工计划）
8. **生成简报** — 简洁格式输出：本章类型、必须处理、禁止事项、推荐写法

## 输出

- `story/runtime/chapter-000N.intent.md`
- `story/runtime/chapter-000N.plan.md`
- 写作简报（一屏内读完）

## 门禁

- hook_report / hook_matrix 出现 WARN 时必须在 intent 中写明处理方式
- 禁止提前泄露的信息必须列入 intent 的 forbidden_reveals
