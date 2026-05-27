# Skills Interface / 技能接口

本目录用于为小说工作流接入额外 skill。skill 可以是写作技法、题材知识、审校规则、文风转换、资料检索、图表/设定整理等能力。

## 使用原则

- skill 是可选增强层，不替代主工作流。
- skill 只能在明确触发时使用：用户点名、章节计划声明、题材/任务明显需要。
- skill 输出不能直接写入 canonical，必须经过主会话 final-check。
- skill 若与 `CLAUDE.md`、`system_protocol.md`、`state_contract.md` 冲突，优先遵守项目工作流。

## 文件

- `skill_protocol.md`：skill 调用规则和生命周期。
- `skill_registry.md`：当前项目可用 skill 注册表。
- `_template.skill-entry.md`：新增 skill 的注册模板。
- `_template.skill-request.md`：在 runtime 中声明 skill 调用请求的模板。

