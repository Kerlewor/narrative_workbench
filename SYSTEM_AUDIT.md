# 系统论审计报告

> 本文件是历史审计记录。当前系统不变量以 `story/system_protocol.md` 为准。

## 审计视角

本框架被视为一个由“输入、处理、状态、反馈、输出”组成的闭环系统：

- 输入：用户意图、故事框架、状态账本、上一章正文。
- 处理：主会话调度 + Writer / Polish / Review / Fixer。
- 状态：正文、Markdown 账本、JSON 镜像、runtime working 文件。
- 反馈：Review、drift check、batch audit、hook 半衰期、final-check。
- 输出：定稿章节和同步后的状态。

## 发现的问题与修复

| 问题 | 系统风险 | 已修复 |
| --- | --- | --- |
| Agent 与主会话边界不够硬 | 批量并行时 Agent 可能直接写 canonical 状态，造成竞争和漂移 | 新增 `system_protocol.md`，规定 Agent 只写 `story/runtime/`，canonical 由主会话 final-check 后提交 |
| 缺少章节状态机 | runtime 文件可能被误当事实源，或旧规划继续污染后文 | 新增章节状态机：planned / drafted / polished / reviewed / fixed / final-check / final-aligned / superseded 等 |
| Markdown 与 JSON 双状态无契约 | 两套状态可能记录不同事实 | 新增 `state_contract.md`，规定权威顺序、同步顺序和 Markdown -> JSON 映射 |
| 四 Agent 交接无固定产物 | 草稿、润色稿、审阅报告、修复稿可能混在一起 | 新增 `_template.agent-handoff.md`，并规定 `chapter-000N.writer/polish/review/fixer.md` 输出路径 |
| 缺少定稿门禁 | Fixer 后可能直接写正文，残留审阅报告或未同步状态 | 新增 `_template.final-check.md`，要求通过连续性、hook、弧光、信息边界、格式和状态同步检查 |
| Polish / Fixer 可能引入新事实 | 语言修复阶段可能改变情节或新开 hook | 更新 Polish / Fixer 提示词，禁止新增事实、hook、角色章末状态 |
| Hook 协议只在伏笔池存在 | 写作、审阅、批量审计可能不执行半衰期机制 | 已将 `hook_protocol.md` 接入启动协议、runtime 模板、Review 检查和 drift check |
| JSON schema 过空 | 无法承载 hook 优先级、半衰期、runtime 状态 | 扩展 `state/*.json` 与 `chapters/index.json` schema |
| 批量模式有状态竞争 | 不同章节并行时可能同时更新状态 | 更新批量规则：Agent 可并行 working，canonical 只能由主会话按章节顺序提交 |

## 当前系统不变量

1. 正文是最高事实源。
2. 规划不进入事实层。
3. Agent 不写 canonical。
4. Hook 必须有正文证据。
5. Markdown 状态先于 JSON 镜像。
6. 每章 final-check 通过后才写入正文。
7. 批量写作只并行 working 阶段，不并行 canonical 提交。

## 剩余人工决策点

- 新书初始化时，仍需用户确认类型、主题、主角弧线和禁令。
- 如果 Review 判定结构性失败，主会话需要决定返 Writer 重写，不能让 Fixer 强修。
- 如果正文推翻大纲，需要用户或主会话决定修大纲还是修后续章节。

