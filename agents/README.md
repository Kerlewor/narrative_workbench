# Agent 提示词目录

主会话负责调度，不直接替代各 agent 的职责。

## 会话模型

Writer、Polish、Review、Fixer 在同一主会话内持续存活，首次创建时读取项目基线，后续章节不重建——主会话每次只发送本章驱动文件（intent、plan、上一章正文、出场角色卡）。跨主会话重启后 Agent 销毁，新会话从头创建。

Project Librarian 每次调用独立执行，不保留跨次记忆。

详见 `CLAUDE.md` 的"Agent 职责"章节。

## 上下文入口

会话开始或上下文过载时，可先调用：

1. `project-librarian.md`

它只生成 Context Packet，用于告诉主会话本轮必须读哪些文件、哪些文件可暂缓、有哪些状态和 hook 风险。它不写正文、不改状态、不调度四 Agent。

## 写作流水线

建议调用顺序：

1. `writer.md`
2. `polish.md`
3. `review.md`
4. `fixer.md`

批量写作时，同一章节内仍然串行，不同章节之间可以流水线重叠。

## 系统边界

- Agent 只写 `story/runtime/` working 文件。
- Agent 不直接修改 `chapters/`、`story/current_state.md`、`story/pending_hooks.md`、`story/state/*.json` 等 canonical 文件。
- 主会话通过 final-check 后，按 `state_contract.md` 提交 canonical。
