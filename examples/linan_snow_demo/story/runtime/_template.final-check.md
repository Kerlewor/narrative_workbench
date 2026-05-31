# Final Check - 模板

---
chapter: 000N
status: final-check
---

## 输入文件

- Writer：
- Polish：
- Review：
- Fixer：
- 最终正文：

## 门禁检查

| 项目 | 结果 | 证据 | 修正 |
| --- | --- | --- | --- |
| 连续性 |  |  |  |
| Hook 账 |  |  |  |
| 半衰期 |  |  |  |
| 人物弧光 |  |  |  |
| 人格一致性 |  |  |  |
| 信息边界 |  |  |  |
| 格式规则 |  |  |  |
| style_blacklist |  |  |  |
| scene beat 落点 |  |  |  |
| 审阅残留 |  |  |  |
| 状态同步 |  |  |  |
| text_audit.py |  |  |  |
| chapter_index.py |  |  |  |
| hook_report.py |  |  |  |
| hook_matrix.py |  |  |  |
| skill 输出采纳 |  |  |  |

## Canonical 更新清单

- [ ] `chapters/000N_标题.md`
- [ ] `chapters/index.json`
- [ ] `story/chapter_summaries.md`
- [ ] `story/emotional_arcs.md`
- [ ] `story/pending_hooks.md`
- [ ] `story/current_state.md`
- [ ] `story/current_focus.md`
- [ ] `story/state/*.json`
- [ ] runtime 状态改为 `final-aligned`
- [ ] 已运行 `python scripts/text_audit.py chapters/000N_标题.md`
- [ ] 已运行 `python scripts/chapter_index.py --write`
- [ ] 必要时已运行 `python scripts/hook_report.py --current N`
- [ ] 必要时已运行 `python scripts/hook_matrix.py --current N`
- [ ] 已审查本章 skill request，明确 adopted / rejected

## 结论

- 是否可定稿：
- 若不可定稿，返回阶段：
