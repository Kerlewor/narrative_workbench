# 启动指令

把下面这段发给 AI，即可启动本框架：

```text
这是一个 AI 小说项目。请先读取项目根目录的 CLAUDE.md，然后按 CLAUDE.md 的"会话启动"顺序读取上下文文件，尤其是 RUN_RULES.md、system_protocol.md、state_contract.md 和 hook_protocol.md。

在读取上下文文件之前，请先询问用户：是否安装了 Python 3 环境，以及是否希望使用 Python 辅助脚本进行确定性检查。如果用户无 Python 或不使用脚本，后续所有脚本运行步骤改为 AI 手动执行等效检查。

如果 Claude Code 可用，请优先调用 `project-librarian` 生成 Context Packet。Context Packet 可以替代 current_state.md、chapter_summaries.md、current_focus.md、RUN_RULES.md 的读取，但不能替代 system_protocol.md、state_contract.md、hook_protocol.md、story_frame.md、volume_map.md。Packet 与原文冲突时以原文为准。

如果当前目录是 `_frameworks/narrative_workbench`，这是模板目录。除非用户明确要求修改模板，不要直接在这里搭建大纲或写正文。应先运行：

```bash
python scripts/create_project.py "项目名"
```

然后进入新项目目录继续。

如果 story/outline/ 和 story/roles/ 还没有实质内容，请先进入"搭建大纲"流程，按五阶段和我对话：故事内核、前台/后台双层结构、分卷设计、角色设计、世界观铁律与禁令。
搭建大纲前，请读取 story/outline/_template.discovery.md，按问卷分批提问；如果 story/style_samples/ 里有样章，请提取 story/style_profile.md。
如果我提供现成大纲，请改用"导入现成大纲"流程：读取 story/outline/_template.import-outline.md，把大纲先拆成 canon / candidate / 缺口 / 冲突 / hook candidate，再追问必要信息。

角色设计（阶段4）不是填表，是四轮深入讨论：Round 1 核心人格 → Round 2 人格压力测试 → Round 3 关系中的性格张力 → Round 4 声音与表达。AI 必须主动追问、挑战矛盾，不能只是记录我给出的标签。

写关键场景、关系转折、身份揭露、高潮或重要 hook 回收时，请使用 story/runtime/_template.scene-beat.md 拆场景，并遵守 story/style_blacklist.md。
如果我点名某个 skill，或章节计划声明需要 skill，请按 skills/skill_protocol.md 和 skills/skill_registry.md 创建 skill request，skill 输出只进入 story/runtime/，由主会话 final-check 后决定是否采纳。
如果该 skill 尚未注册，请先登记到 skills/skill_registry.md，并运行 `python scripts/skill_check.py --skill SKILL_NAME` 验证。

如果大纲已经完成，请先做 drift check，再根据我的命令执行：
- "规划第 N 章"
- "写第 N 章"
- "继续下一章"
- "写接下来 3-5 章"
- "审阅第 N 章"
- "导入现成大纲"
- "审查第 N 章"（共创模式：审查手写稿，不改正文）
- "润色第 N 章 --模式 light"（共创模式：5 种润色模式可选）
- "第 N 章写作简报"（动笔前生成约束简报）
- "深化角色 <角色名>"

写作时使用 Writer -> Polish -> Review -> Fixer 四 Agent 流水线。Agent 是持久会话——首次创建后在同一主会话内持续存活，后续章节无需重复发送项目基线。主会话在写前 SOP 中完成 hook 盘点、角色盘点和弧光分析，将结论写入 intent/plan 驱动 Agent。Agent 持续处理超过 8 章后主会话应主动重置。

Agent 只能写 story/runtime/ 中的 working 文件，canonical 状态由主会话 final-check 后统一提交。写每章前必须读取 hook_protocol.md 做伏笔预算和半衰期检查。每章定稿后，只根据正文真实发生的事件更新 current_state、chapter_summaries、pending_hooks、emotional_arcs 和 state/*.json。Runtime 文件在跨卷后可归档到 story/runtime/volume-N/ 子目录，之后默认跳过不读。
```

## 新书初始化建议

1. 运行 `python scripts/create_project.py "项目名"` 创建新书目录。
2. 进入新书目录启动 Claude Code。
3. 修改 `story/outline/story_frame.md` 的 YAML frontmatter。
4. 填写 `story/book_rules.md` 的类型、视角、节奏硬规则。
5. 对 AI 说"搭建大纲"。
6. 大纲、分卷、角色卡完成后再开始第 1 章。
7. 初始化完成后运行 `python scripts/doctor.py` 做体检。

## Claude Code 使用注意

- 从新书目录根部启动 Claude Code，确保它能读到根目录 `CLAUDE.md` 和 `.claude/agents/`。
- `.claude/agents/project-librarian.md` 是上下文路由 agent 注册文件（一次性会话）。
- `.claude/agents/novel-*.md` 是 Claude Code 写作 subagent 注册文件（持久会话，薄路由层，详细指令在 `agents/*.md`）。
- `agents/*.md` 是各 Agent 的详细职责说明，subagent 和主会话均按需读取。
- 如果 Claude Code 没有自动调用 subagent，可以显式要求："先调用 project-librarian 生成 Context Packet"，或"调用 novel-writer / novel-polish / novel-review / novel-fixer 执行对应阶段"。
- 写作过程中请自动使用 Python 辅助脚本：初始化和批末运行 `doctor.py`，各 Agent 前建议运行 `context_builder.py` + `prompt_compiler.py` 编译上下文和 prompt，final-check 前**必须**运行 `gatekeeper.py` + `text_audit.py`，写后运行 `chapter_index.py --write`，规划/批量前运行 `hook_report.py --current N` 和 `hook_matrix.py --current N`，新卷/批末运行 `structure_report.py`。
- 脚本运行门禁以 `RUN_RULES.md` 为准；脚本报 ERROR 必须先修复，WARN 必须写入对应 runtime 文件并说明处理。
