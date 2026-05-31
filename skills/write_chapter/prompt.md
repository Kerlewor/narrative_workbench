# write_chapter — 单章写作流水线

执行单章完整流水线：规划确认 → 上下文编译 → Writer → Polish → Review → Fixer → Gatekeeper → Final-check → 写入 canonical。

## 触发条件

- `写第N章`
- `继续下一章`
- `write chapter N`

## 前置条件

1. 大纲已完成（`story/outline/story_frame.md` 已填充）
2. 角色卡已创建（`story/roles/` 非空）
3. 当前卷已确定（`story/outline/volume_map.md`）

## 工作流

1. **确认章节号** — 以 `chapters/index.json` 最大章节号 + 1 为准；与 `current_state.md` 冲突时优先 `index.json`
2. **规划前检查** — 运行 `hook_report.py --current N-1` + `hook_matrix.py --current N-1`（N=1 时跳过）
3. **创建/复核 intent 与 plan** — `story/runtime/chapter-000N.intent.md` + `.plan.md`
4. **编译上下文包** — 运行 `relevance_resolver.py --chapter N --agent writer`
5. **Writer** → `chapter-000N.writer.md`
6. **Polish** → `chapter-000N.polish.md`
7. **Review** → `chapter-000N.review.md`（若 `needs-rewrite`，返回步骤 5）
8. **Fixer** → `chapter-000N.fixer.md`
9. **Gatekeeper** — `gatekeeper.py --chapter N --stage final`（必须通过）
10. **Final-check** — 主会话定稿门禁 → 写入 `chapters/000N_标题.md`
11. **状态同步** — 按 `state_contract.md` 顺序同步状态 + 标记 `final-aligned`

## 输出

- `chapters/000N_标题.md`（正式章节）
- `story/runtime/chapter-000N.*.md`（各阶段产物）
- 更新后的状态文件和 JSON 镜像

## 门禁

- gatekeeper 未通过不得写入 canonical
- 单章未完成不得开始下一章状态同步
