# Skill Registry / 技能注册表

> 新增 skill 时，在本表登记。未登记 skill 不应被自动调用。

| skill | 用途 | 触发条件 | 入口文件/说明 | 输出位置 | 状态 |
| --- | --- | --- | --- | --- | --- |
| plan_chapter | 生成章节写作简报与约束包 | 规划第N章 / 写作简报 | `skills/plan_chapter/prompt.md` | `story/runtime/` | enabled |
| write_chapter | 执行单章完整写作流水线 | 写第N章 / 继续下一章 | `skills/write_chapter/prompt.md` | `story/runtime/` | enabled |
| review_chapter | 审查章节（AI写或作者手写） | 审阅第N章 / 审查第N章 | `skills/review_chapter/prompt.md` | `story/runtime/` | enabled |
| polish_author_draft | 对作者手写章节按模式润色 | 润色第N章 / polish | `skills/polish_author_draft/prompt.md` | `story/runtime/` | enabled |
| import_outline | 搭建或导入现成大纲 | 搭建大纲 / 导入大纲 | `skills/import_outline/prompt.md` | `story/outline/` | enabled |
| deepen_character | 对角色进行四轮深度讨论 | 深化角色 / 角色深度讨论 | `skills/deepen_character/prompt.md` | `story/roles/` | enabled |
| example-style-skill | 示例：专项文风规则 | 用户明确要求或 plan 声明 | `skills/_template.skill-entry.md` | `story/runtime/*.skill-example-style-skill.md` | disabled |

## 状态说明

- `enabled`：可被主会话按触发条件调用。
- `disabled`：示例或暂不启用。
- `deprecated`：已废弃，保留记录。

