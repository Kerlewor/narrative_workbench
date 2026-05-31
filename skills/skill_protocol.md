# Skill Protocol / 技能调用协议

## Skill 定义

Skill 是主工作流之外的可插拔能力。它可以提供：

- 特定题材知识。
- 特定文风规则。
- 章节审阅清单。
- 资料整理方法。
- 专项润色方法。
- 世界观、战斗、恋爱、悬疑、推理等专项构造规则。

## 触发条件

满足任一条件时，主会话可以使用 skill：

1. 用户明确点名 skill。
2. `story/runtime/*.intent.md` 或 `*.plan.md` 声明需要 skill。
3. 章节类型明显需要某专项能力，例如推理章、战斗章、亲密场景、论文式设定说明等。
4. Review 报告建议引入某 skill 修复特定问题。

## 调用顺序

1. 在 `skills/skill_registry.md` 中确认 skill 是否已注册。
2. 读取 skill 的入口说明。
3. 在 runtime 中创建或填写 skill request。
4. skill 输出进入 `story/runtime/` working 区。
5. 主会话审查后，必要内容再进入 canonical。

如果用户要求使用未注册 skill：

1. 主会话先按 `skills/_template.skill-entry.md` 在 `skills/` 中创建入口说明，或在 registry 中登记外部说明位置。
2. 更新 `skills/skill_registry.md`，状态设为 `enabled` 或 `disabled`。
3. 运行 `python scripts/skill_check.py --skill SKILL_NAME`。
4. 通过后才能创建 skill request。

## 边界

- skill 不直接改正文和状态。
- skill 不覆盖角色卡、hook 协议、状态契约。
- skill 产生的新设定、新 hook、新规则必须在主会话确认后才能进入 `story/` canonical 文件。
- 如果 skill 与本项目禁令冲突，以本项目禁令为准。

## Runtime 记录

每次使用 skill，应在对应 intent / plan / review / final-check 中记录：

- skill 名称。
- 调用原因。
- 输入文件。
- 输出位置。
- 是否采纳。
- 若未采纳，原因。

## 推荐输出路径

```text
story/runtime/chapter-000N.skill-SKILLNAME.md
story/runtime/batch-000N-000M.skill-SKILLNAME.md
story/runtime/outline.skill-SKILLNAME.md
```
