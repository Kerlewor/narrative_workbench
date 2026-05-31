# Narrative Workbench — 系统原则

本文档包含 Narrative Workbench 的完整系统原则，供维护者与脚本验证器使用。
具体操作路由见 `CLAUDE.md`（精简入口）和 `skills/` 目录。

## 核心原则

1. **Canonical 文件永远优先于工作草稿。** 正文 `chapters/` 是最高事实源。Agent 输出和 runtime 文件只代表规划或建议，不能取代 canonical。
2. **当前任务必须先调用 packet compiler。** Relevance Resolver 或 Context Builder 生成的任务包是 Agent 工作的起点，不可绕过。
3. **不得绕过门禁直接写入正式章节。** gatekeeper 通过 + final-check 完成后，才能由主会话写入 `chapters/`。
4. **主模型只负责当前创作决策与高层协调。** 状态筛选、上下文拼接、重复消除、事实追溯、预算限制，由程序层完成。
5. **Agent 记忆可以提高效率，但永远不能成为事实唯一来源。** 正式章节与结构化账本才是 canonical truth。

## Agent 职责边界

| Agent | 职责 | 不可做 |
|---|---|---|
| Writer | 写原始草稿 | 修改状态文件、替换正式章节 |
| Polish | 语言润色、去 AI 味 | 改变事实、关系、剧情走向 |
| Review | 审阅、找问题 | 直接改文 |
| Fixer | 按 Review 报告修复 | 超出报告范围的改动 |
| Project Librarian | 上下文路由 | 写正文、修改 canonical |

## 事实源规则

1. `chapters/` 正文是最高事实源。
2. `story/runtime/` 文件只是规划，除非标记 `final-aligned`。
3. `pending_hooks.md` 只记录正文已成立的伏笔。候选伏笔留在 runtime 文件。
4. Hook 操作必须有正文证据。candidate 不进伏笔池。
5. Agent 只能输出到 working 区，不得直接改 canonical 文件。
6. Markdown 状态先于 JSON 状态更新。JSON 只镜像 Markdown。

## 上下文工程原则

1. 不同 Agent 接收不同任务包——Writer 不需要完整伏笔库，Polish 不需要全量角色卡。
2. 每条注入信息写明注入原因；省略的信息写明清原因。
3. 预算超出时主动裁剪、降级、说明。
4. 稳定规则使用版本哈希，仅变化时重新发送。
5. 上下文精准比上下文大更重要。长上下文带来噪音淹没和注意力分散。

## 不应做的事

1. 不要继续把新功能说明追加进 CLAUDE.md — 新流程进 Skill，新规则进验证器，新事实进账本
2. 不要以为更长上下文窗口就能解决问题
3. 不要过早增加更多 Agent — Writer/Polish/Review/Fixer/Librarian 已足够
4. 不要把 Agent 会话记忆当成事实库
5. 不要先做花哨界面再补底层检索
6. 不要做 TUI 或独立界面 — Claude Code 和 Codex 已是交互界面
