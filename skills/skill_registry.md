# Skill Registry / 技能注册表

> 新增 skill 时，在本表登记。未登记 skill 不应被自动调用。

| skill | 用途 | 触发条件 | 入口文件/说明 | 输出位置 | 状态 |
| --- | --- | --- | --- | --- | --- |
| example-style-skill | 示例：专项文风规则 | 用户明确要求或 plan 声明 | `skills/_template.skill-entry.md` | `story/runtime/*.skill-example-style-skill.md` | disabled |

## 状态说明

- `enabled`：可被主会话按触发条件调用。
- `disabled`：示例或暂不启用。
- `deprecated`：已废弃，保留记录。

