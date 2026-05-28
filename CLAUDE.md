# AI 小说写作工作流

本文件是项目启动协议。任何 AI 会话开始后，必须先读取本文件，再读取“会话启动”列出的上下文文件。

## 模板保护规则

如果当前目录路径包含 `_frameworks/narrative_workbench`，说明 AI 正在模板目录中运行。除非用户明确要求修改模板本身，否则不得在该目录中搭建大纲、写正文或更新项目状态。

创建新小说项目时，必须先运行：

```bash
python3 scripts/create_project.py "项目名"
```

然后进入新项目目录继续工作。新项目会自动生成 `PROJECT.md`。

## 目录结构

```text
chapters/              正文章节
story/outline/         故事框架、分卷图、扩写蓝图、题材安全手册
story/runtime/         每章 intent + plan，批量 plan + audit
story/runtime/volume-N/ （可选）已定稿章节的 runtime 归档
story/state/           JSON 状态文件
story/roles/           角色卡
agents/                四 Agent 提示词
.claude/agents/        Claude Code subagent 注册文件，含项目档案员和四个写作 Agent
```

### Runtime 归档规则

- `final-aligned` 超过当前卷的 runtime 文件，Project Librarian 和主会话默认跳过。只在跨卷审计、hook 追溯或用户明确要求时读取。
- 进入新卷时，主会话可将上一卷的 runtime 文件移入 `story/runtime/volume-N/` 子目录（可选但建议）。
- 当前卷内的 runtime 正常读取，不做归档。

## 会话启动

每次新会话必须先读取以下文件。若 Claude Code 可用，应先调用 `project-librarian` 生成 `Context Packet`，用于压缩本轮必读上下文；Context Packet 只是导航图，不能替代原始文件和正文事实源。

1. `story/current_focus.md` - 下一步写什么
2. `story/current_state.md` - 当前章节、地点、人物状态、敌我关系
3. `RUN_RULES.md` - Python 辅助脚本运行门禁
4. `story/system_protocol.md` - 系统边界、状态机、定稿门禁
5. `story/state_contract.md` - 正文 / Markdown / JSON 同步契约
6. `story/chapter_summaries.md` - 已写章节摘要
7. `story/pending_hooks.md` - 正文已成立伏笔
8. `story/hook_protocol.md` - 伏笔生命周期、半衰期、回收审计规则
9. `story/outline/volume_map.md` - 分卷 Objective / KR / 节奏节点
10. `story/outline/story_frame.md` - 主题、冲突、世界观铁律、禁令
11. `story/emotional_arcs.md` - 角色弧光账本

**Context Packet 替代规则：** 当 Project Librarian 生成了 Context Packet 后，主会话按以下规则决定读取策略：

- **可跳过、以 Packet 为准：** `current_state.md`、`chapter_summaries.md`、`current_focus.md`、`RUN_RULES.md`——这些文件的事实摘要、脚本门禁和位置信息在 Packet 中已有覆盖。但如果 Packet 标注了冲突或缺口，必须回头读原文件。
- **必须读原文：** `system_protocol.md`、`state_contract.md`、`hook_protocol.md`、`story_frame.md`、`volume_map.md`——这些是系统规则和结构约束，Packet 只做风险提示不做完整复述。
- **按需决定：** `pending_hooks.md`、`emotional_arcs.md`——如果 Packet 的 hook 表和弧光注意点已足够支撑本轮任务，可跳过；如果本轮核心任务是回收钩子或推进弧光，必须读原文。
- **冲突裁决：** Packet 与原文件不一致时，以原文件为准。Packet 不是 canonical。

按需读取：

- `story/runtime/_template.context-packet.md` - 项目档案员输出模板
- `skills/skill_protocol.md` - 可插拔 skill 调用协议
- `skills/skill_registry.md` - 当前项目可用 skill 注册表
- `story/style_guide.md` - 去 AI 味和写前自检
- `story/style_profile.md` - 本书文风画像，从样章和用户偏好中提取
- `story/style_blacklist.md` - AI 腔、作文腔、万能氛围句、主题金句负面清单
- `story/fiction_style_skill.md` - 本书文风二修规则
- `story/ai_writing_repair_plan.md` - AI 写作修复清单
- `story/roles/*.md` - 本章出场角色卡
- `story/outline/romance_safety_handbook.md` - 亲密/情感张力场景安全写法，如题材适用

## 事实源规则

1. 正文章节 `chapters/` 是最高事实源。
2. `story/runtime/*.intent.md` 和 `*.plan.md` 只代表规划，除非标记为 `status: final-aligned`，否则不得作为已发生事实。
3. `pending_hooks.md` 只记录正文已经成立的伏笔。规划中的候选伏笔留在 runtime 文件里。
4. 所有 hook 操作遵守 `story/hook_protocol.md`：candidate 不进伏笔池，open / advance / resolve 必须有正文证据。
5. 写下一章前必须做 drift check：对比最近正文、摘要、伏笔、当前状态、JSON 状态与最近 runtime。发现冲突先修状态，再写正文。
6. 写下一章前必须做 hook 半衰期检查：过期钩子必须 advance / defer / resolve / dormant / dropped。
7. Agent 只能输出到 working 区 `story/runtime/`，不得直接改 canonical 文件。canonical 文件只能由主会话通过 final-check 后更新。
8. Markdown 状态先于 JSON 状态更新。JSON 只镜像 Markdown，不独立创造事实。

## 用户命令

### 搭建大纲

用于从零开始搭建新书大纲，分五阶段推进。

搭建前先读取 `story/outline/_template.discovery.md`，按问卷分批向用户确认关键信息。不要一次性问完所有问题；优先确认类型、主角、前台冲突、后台真相、结局方向和禁区。

**阶段1：确立故事内核**

- 与用户确认：一句话主题、基调、主角核心弧线、全书 Objective。
- 输出到 `story/outline/story_frame.md` 的主题、基调、终局方向。
- 同步更新 `story/brief.md` 和 `story/author_intent.md`。

**阶段2：构建前台/后台双层结构**

- 前台故事：显性冲突线，谁和谁在什么舞台上对抗。
- 后台故事：暗线阴谋、历史真相、人物秘密。
- 咬合机制：每个前台事件如何被后台齿轮驱动。
- 输出到 `story/outline/story_frame.md` 的核心冲突部分。

**阶段3：分卷设计**

- 每卷定义：主题、情绪曲线、Objective、3 个 KR、卷尾不可逆改变。
- 设计卷间钩子：前卷埋什么，后卷回收什么。
- 输出到 `story/outline/volume_map.md`。

**阶段4：角色设计**

角色设计不是填表，而是与用户进行多轮深入讨论。AI 必须主动追问、挑战矛盾、提出替代视角。每个角色完成后，用户应该感觉"我比之前更了解这个角色了"。

进入阶段 4 前，先确认阶段 1-3 已完成，因为角色设计依赖故事内核、前台/后台结构和分卷框架。

**角色设计通用规则：**

- 每个角色必须有至少一个内在矛盾（想要 A 但害怕 B、声称 C 实则渴望 D、擅长 E 却在 F 面前无能为力）。
- 每个性格标签必须有至少一种可见的行为外化方式——不写"她性格倔强"而是"她在什么情境下会做什么"。
- 角色之间的关系必须由性格驱动，不能只是"他是她的朋友"——要追问"为什么是这个人而不是别人？这段关系里谁在忍受谁？"
- AI 发现以下情况时必须主动指出：角色之间性格雷同、某个角色只在功能上存在（只为主角服务而无独立诉求）、性格与成长弧光矛盾、标签堆砌但无行为支撑。

**Round 1：核心人格**

从 `_template.discovery.md` 的 Section 2 出发，但不止于回答问题。对每个主角，AI 必须执行：

1. 核心标签与反差：用户提出的每个标签，追问"这个标签在什么情境下最明显？什么情境下它会失效？"找出至少一个反差细节——一个让标签变复杂的小习惯、小破绽或例外。
2. 内在驱动拆解：从"想要什么"追问到"为什么想要这个而不是别的？"再追问"如果真的得到了，然后呢？"确保驱动力不是情节需要而是人格产物。
3. 错误信念溯源：主角的错误信念不是凭空来的。追问"她在什么时候第一次相信了这件事？那个场景具体发生了什么？"如果用户没想好，这可以是后台故事的一部分。
4. 情绪表达风格：这个角色在愤怒/悲伤/恐惧/喜悦时，分别用什么方式表达？是外放还是内收？是话多还是话少？会找谁？会躲谁？会摔东西还是捏杯子？
5. 盲点：角色最大的自我欺骗是什么？她对自己哪一点判断完全错误？读者什么时候能看出来，她自己什么时候能发现？

输出：将讨论结果填入 `story/roles/<角色名>.md` 的基础信息、核心标签、Personality Lock、人物小传和当前诉求部分。

**Round 2：人格压力测试**

此轮不新增信息，而是验证已有设定的一致性。AI 必须为每个主角和重要配角构造 3-5 个虚拟情境，测试角色反应是否自洽：

1. 从故事中选取一个关键决策点（如"发现最好的朋友背叛了自己"），追问"按她现在的性格，她的第一反应是什么？她会先做什么再做什么？她会不会后悔第一步？"
2. 构造一个与角色核心恐惧直接冲突的情境（如"她最害怕被抛弃，但现在必须主动离开一个人"），追问"她会怎么处理？"
3. 构造一个道德/情感两难（如"救 A 就要牺牲 B，A 和 B 都是她在乎的人"），追问"她会怎么选？选完会怎么想？"
4. 找出至少一个"这个角色绝对做不出的事"和一个"这个角色自己都没想到自己会做的事"。

AI 如果发现矛盾（如"她平时很谨慎但压力测试中不断冲动决策"），必须指出来并追问用户：这是刻意设计的成长空间，还是设定需要调整？

输出：将压力测试的关键结论写入角色卡的 Behavioral Constraints 和禁止写法部分。"绝对做不出的事"和"自己都没想到会做的事"写入 Personality Lock。

**Round 3：关系网络中的性格张力**

角色关系的本质是性格碰撞。此轮针对每条核心关系线展开：

1. 对每组重要关系，追问：两个人性格中哪个点最容易摩擦？哪个点是互补的？如果一方改变了，另一方会不安还是松了一口气？
2. 追问信息边界：谁在谁面前戴着面具？谁看穿了谁？谁以为看穿了但其实完全搞错了？
3. 追问权力关系：这段关系里谁更需要谁？什么时候权力会翻转？
4. 群像检查：把所有主要角色的核心标签排在一起，检查是否有性格重复。如果有两个"表面冷漠内心温柔"的角色，追问用户：她们的区别在哪里？读者凭什么能分清？

输出：将关系讨论写入角色卡的关系网络表，并将群像层面的性格互补/冲突关系写入 `story/character_matrix.md` 的群像规则区。

**Round 4：声音与表达**

性格最终落在对白和行动上。此轮为每个重要角色校准对白风味：

1. 对白试写：让用户或 AI 为角色写 2-3 句代表性对白（同一情境下的不同反应），确认角色的说话方式与性格一致。
2. 情绪外化风格：确认角色在关键情绪下如何外化——通过物件、动作、对白破绽还是身体反应？参考 `story/runtime/_template.scene-beat.md` 的情绪外化表。
3. 动作锚点：为角色选定 1-2 个可用于情绪外化的具体动作或物件。

输出：将对话风味、动作锚点填入角色卡的对应部分。

**角色设计完成标准：**

- [ ] 每个主角都经过了 4 轮讨论。
- [ ] 每个重要配角至少经过了 Round 1 和 Round 3。
- [ ] 群像性格无重复（或差异已被明确标注）。
- [ ] 每个角色的 Personality Lock 至少有 3 条具体可验证的条目。
- [ ] 每个角色的 Behavioral Constraints 至少有 3 条。
- [ ] 压力测试中发现的矛盾已被处理（修正设定或标记为成长空间）。
- [ ] 角色卡已写入 `story/roles/`。
- [ ] `story/character_matrix.md` 已更新。
- [ ] 如适用题材，亲密/情感场景的写法边界在角色卡中已标注。

**阶段5：世界观铁律与禁令**

- 更新 `story/outline/story_frame.md` 的 YAML frontmatter：主角锁定、行为约束、类型锁、禁令。
- 在 `story/outline/story_frame.md` 写入 2-3 条不可违反的世界观铁律。
- 在 `story/book_rules.md` 写入类型规则、视角规则、节奏原则（高潮间距、喘息频率、钩子密度、信息释放、情感节点）。
- 如果用户提供样章，读取 `story/style_samples/` 中最相关的 1-3 个样本，提取 `story/style_profile.md`。

### 导入现成大纲

触发语包括：

- `我有现成大纲`
- `导入大纲`
- `拆解这个大纲`
- `根据这个大纲搭建项目`
- `把这个大纲变成工作流文件`

执行流程：

1. 读取 `story/outline/_template.import-outline.md`。
2. 将用户大纲默认视为 `candidate`，不得直接写入 canonical。
3. 拆分大纲中的 canon / candidate / 缺口 / 冲突 / 逻辑跳跃。
4. **主动检测缺口：** 对照"最低完备性检查"逐项判断用户大纲是否覆盖。未覆盖的项列入追问清单，向用户提问。优先问会影响后续步骤的问题（如主角弧线不清晰会导致角色设计无法进行）。
5. **必须追问的类别（无论大纲是否提及）：**
   - 主角的错误信念是什么？什么经历让她相信了它？
   - 主角的核心内在矛盾是什么？
   - 前台冲突与后台真相如何咬合？
   - 终局方向是什么？全书 Objective 是什么？
   - 每个重要配角的独立诉求是什么？
   即使用户大纲部分涉及，AI 也应追问以确认和深化。
6. 用户确认 canon 内容后，写入 `story/brief.md`、`story/author_intent.md`、`story/outline/story_frame.md`、`story/outline/volume_map.md`、`story/book_rules.md`、`story/roles/*.md`、`story/character_matrix.md`、`story/current_focus.md`。
7. 导入阶段的伏笔通常是 hook candidate，不直接进入 `pending_hooks.md`。
8. 导入完成后运行：

```bash
python3 scripts/structure_report.py
python3 scripts/doctor.py
```

9. **导入后角色深化（必须提示用户）：** 导入完成后，AI 必须主动告知用户：当前角色卡仅包含大纲中的基本信息，尚未经过人格深度讨论。用户可随时对任意角色说"深化角色 <角色名>"，AI 将按阶段 4 的四轮协议（核心人格 → 压力测试 → 关系张力 → 声音表达）逐轮讨论并补全 Personality Lock、Behavioral Constraints、压力测试结论、对白风味和动作锚点。

### 规划第 N 章

创建本章规划文件，不启动四 Agent：

1. 运行 `python3 scripts/hook_report.py --current N-1` 和 `python3 scripts/hook_matrix.py --current N-1`（N 为本章号）。若 N=1（第 1 章），尚无已定稿章节，跳过此步。
2. 创建 `story/runtime/chapter-000N.intent.md` 和 `story/runtime/chapter-000N.plan.md`，填入 hook 预算和半衰期检查结果。

### 写第 N 章 / 继续下一章

执行单章完整流水线。"继续下一章"时，N = `current_state.md` 当前章节 + 1。若不确定，以 `chapters/index.json` 中最大章节号 + 1 为准；两者冲突时优先 `index.json`。

1. 主会话读取启动上下文，做 drift check。
2. 检查 `story/runtime/chapter-000N.intent.md` 是否已存在：
   - 已存在且 `status: planned`：复核 intent/plan 是否仍然有效，必要时更新。无需重建。
   - 已存在但非 `planned`（如 `drafted`、`needs-rewrite` 等）：说明之前已启动过。检查现有进度，从适当的阶段继续（例如 `needs-rewrite` 应返回 Writer）。
   - 不存在：运行 `hook_report.py --current N-1` 和 `hook_matrix.py --current N-1`（N=1 时跳过），然后创建本章 intent 与 plan，填入 hook 预算和半衰期检查结果。
3. Writer 根据 intent + plan + 角色卡 + 上一章正文写草稿，输出到 `story/runtime/chapter-000N.writer.md`。
4. Polish 根据风格规则润色草稿，输出到 `story/runtime/chapter-000N.polish.md`。
5. Review 对润色稿出具审阅报告，输出到 `story/runtime/chapter-000N.review.md`。若 Review 判定结构性失败（`needs-rewrite`），将 Review Report 一并发送给 Writer，回到步骤 3 重写。
6. Fixer 只按审阅报告修正，输出到 `story/runtime/chapter-000N.fixer.md`。
7. 运行 `python3 scripts/gatekeeper.py --chapter N --stage final` 做确定性门禁检查。gatekeeper 通过后，主会话创建 `story/runtime/chapter-000N.final-check.md`，执行定稿门禁检查。
   - 通过：继续步骤 8。
   - gatekeeper 阻塞：修复阻塞问题后重新运行 gatekeeper。
   - 未通过 final-check（`needs-repair`）：将本章 intent.md 状态设为 `needs-repair`，将 final-check 报告发送给 Fixer，返回步骤 6 重新修复；或标记为 `superseded`（放弃本章）。
8. 主会话写入 `chapters/000N_标题.md`。
9. 主会话按 `state_contract.md` 顺序同步 `current_state.md`、`chapter_summaries.md`、`pending_hooks.md`、`emotional_arcs.md`、`story/state/*.json`。
10. 将本章 runtime 标记为 `status: final-aligned`。

### 写接下来 3-5 章

执行批量流水线：

1. 批前 drift check。运行 `hook_report.py --current N-1`、`hook_matrix.py --current N-1`、`structure_report.py`、`doctor.py`（N 为本批首章号；N=1 时跳过 hook 脚本）。
2. 创建 `story/runtime/batch-000N-000M.plan.md`，填入 hook 预算和半衰期检查结果。
3. 对每章按单章流水线执行。
4. 不同章节的 working 文件可流水线重叠产出，但不得并行写 canonical 状态。
5. 每章写定后由主会话按章节顺序立刻同步状态，下一章以最新正文事实为准。
6. 批末创建 `story/runtime/batch-000N-000M.audit.md`。

硬约束：单批最多 5 章；禁止先写完多章再统一补状态。

### 审阅第 N 章

对已存在章节启动返修流水线。先读取该章的 `intent.md` 确认当前状态：

- `final-aligned`：已定稿章节。先问用户要修什么，再决定从哪个阶段切入。
- `drafted`：从 Polish 开始（Polish → Review → Fixer）。
- `polished`：从 Review 开始（Review → Fixer）。
- `reviewed`：从 Fixer 开始。
- `fixed`：直接进入 final-check。
- `needs-rewrite`：返回 Writer 重写（Writer → Polish → Review → Fixer）。
- `needs-repair`：返回 Fixer 重新修复，然后 final-check。
- 仅有 `planned`：尚未写过，应使用"写第 N 章"而非审阅。
- 状态不明：先检查 runtime 文件和正文是否存在，判断实际进度后再决定流程。

主会话最后写定并同步必要状态。

### 深化角色

对已导入或已创建的角色，按阶段 4 的四轮协议进行人格深度讨论。触发语包括：

- `深化角色 <角色名>`
- `深化 <角色名>`
- `角色深度讨论 <角色名>`
- `补全角色 <角色名>`

执行流程：

1. 读取 `story/roles/<角色名>.md` 当前内容，判断已有信息和缺口。
2. 按阶段 4 的四轮协议逐轮与用户讨论（Round 1 核心人格 → Round 2 压力测试 → Round 3 关系张力 → Round 4 声音表达）。每轮结束后将结论写入角色卡对应部分。
3. 如果角色卡已有部分信息（如对白风味已填写），跳过已充分的轮次，重点讨论缺失的轮次。
4. 四轮完成后，更新 `story/character_matrix.md` 中的性格分布检查和关系张力地图。
5. 如果该角色已出现在已写章节中，提示用户是否需要回头看已写章节中该角色的行为是否符合新补全的人格设定（建议但不强制）。

适用场景：
- 导入现成大纲后，导入的角色卡只有框架信息。
- 搭建大纲阶段 4 中只快速填写了角色卡，想回头深化。
- 写作过程中发现角色行为不够鲜明，需要补全人格设定。

### 会话模型

Writer、Polish、Review、Fixer 四个写作 Agent 在同一主会话内**持续存活**，不因单章完成而重建。其价值在于：Agent 首次创建时读取项目基线（规则、风格、角色卡、大纲），后续章节无需主会话重复发送这些文件。主会话每次只发送本章驱动文件（intent、plan、上一章正文、出场角色卡）即可。

**信息流向原则：** 主会话在写前 SOP 中完成 hook 盘点、角色盘点、弧光差值分析和 drift check，将结论写入 intent 和 plan。Agent 只读本章驱动文件，不自行重复读取基线文件做分析。这确保了分析工作集中在一处，Agent 专注于执行。

跨主会话重启后，Agent 随之销毁。新会话从头创建，重新读取项目文件。handoff 摘要仅用于本章流水线内接力（Writer→Polish→Review→Fixer），传递偏离和未解决问题，不承载跨章知识迁移。

`project-librarian` 采用一次性模型：每次调用独立执行，不保留跨次记忆。

### Agent 职责表

| Agent | 输入 | 任务 | 输出 |
| --- | --- | --- | --- |
| Project Librarian | 规则 + 状态文件 | 上下文路由，生成 Context Packet | `story/runtime/session-YYYYMMDD-context.md` |
| Writer | intent + plan + 角色卡 + 上一章正文 | 写 3000 字左右草稿，只管情节、角色、节奏 | 原始草稿 |
| Polish | Writer 草稿 + 风格规则 | 去 AI 味、校准文风、保持情节不变 | 润色稿 |
| Review | 润色稿 + 检查清单 | 找 bug、漂移、设定越界、文风问题 | 审阅报告 |
| Fixer | 润色稿 + 审阅报告 | 只修报告指出的问题 | 修正稿 |

同一章内严格串行：Writer -> Polish -> Review -> Fixer。

多章批量时，不同章节可流水线重叠：Writer 完成 ChN 后立即收到 ChN+1 任务，同时 Polish 正在处理 ChN。同一 Agent 一次只处理一个章节。

每个 Agent 完成后必须生成 handoff 摘要，使用 `story/runtime/_template.agent-handoff.md` 的字段说明偏离、未处理问题和事实变更声明。

### 会话管理

- **创建：** 首次写第 1 章时，主会话创建四个 Agent，各发送一份项目基线。Agent 首次响应确认已理解。
- **恢复：** 后续章节，主会话向已有 Agent 发送本章驱动文件即可。不重建 Agent。建议先运行 `python3 scripts/context_builder.py --chapter N --agent <agent>` 生成上下文包，避免手动拼接输入。
- **重置触发条件：** 满足以下任一条件时，主会话结束当前 Agent 会话并创建替代：
  - Agent 已连续处理 **8 章以上**（上下文积累导致质量下降风险）。
  - Agent 输出出现角色漂移、事实矛盾或风格偏离，且纠正无效。
  - 用户要求。
- **重置流程：** 用 `story/runtime/_template.session-close.md` 记录关闭原因和已处理章节范围。新 Agent 重新读取项目基线，从当前章节继续。
- **跨会话重启：** 主会话退出后 Agent 全部销毁。下次启动时重新创建，重新读取项目文件。

### Project Librarian

`project-librarian` 是上下文路由 agent，不属于写作流水线。每次调用独立执行，读取当前最新规则和状态，输出 Context Packet。不得写正文、规划新剧情、修改 canonical 或调度四 Agent。

## 写前 SOP

1. 确定位置：以 `chapters/index.json` 最大章节号为准确认当前章节；以 `volume_map.md` 确认当前卷；读取上一章正文确认章尾状态。
2. 盘点钩子：读取 `hook_protocol.md` 和 `pending_hooks.md`，检查活跃钩子预算、core 钩子、半衰期到期项，本章执行 open / advance / escalate / resolve / defer。
3. 盘点角色：出场角色、信息边界；对照角色卡的 Personality Lock、Behavioral Constraints 和压力测试结论，确认本章角色的行为边界和禁止写法。
4. 确认节点：本章推进哪条线，章尾必须发生什么改变。
5. 确认人物弧光差值：对照角色卡的成长弧光表，确认章初状态、本章想要、阻力、选择、章末状态、可见证据。
6. 复习禁令：类型禁令、世界观铁律、视角边界。
7. 复杂场景或文笔要求高的章节，按 `story/runtime/_template.scene-beat.md` 为关键场景补 scene beat，明确对白策略、动作锚点、情绪外化和段尾落点。
8. 若用户点名 skill、plan 声明 skill，或章节明显需要专项能力，按 `skills/skill_protocol.md` 创建 skill request，并将 skill 输出保留在 runtime working 区等待主会话采纳。

## 写后 SOP

每章完成后，按 `story/state_contract.md` 的提交顺序更新以下文件。只允许根据正文中真实出现的事件更新状态文件。Markdown 状态先于 JSON 镜像。

- `chapters/000N_标题.md` 及 `chapters/index.json`
- `story/chapter_summaries.md`
- `story/emotional_arcs.md`
- `story/pending_hooks.md`
- `story/current_state.md`
- `story/current_focus.md`
- `story/state/*.json`
- 将本章 runtime 标记为 `status: final-aligned`

## 自动体检

Python 脚本只用于确定性检查、索引、统计和报告；不得用脚本自动总结章节、自动判定 hook 回收、自动润色正文或自动调度 Agent。

具体运行时机以根目录 `RUN_RULES.md` 为准。若本文件和 `RUN_RULES.md` 冲突，优先执行 `RUN_RULES.md`。

### 必须运行

```bash
python3 scripts/doctor.py
```

运行时机：

- 新书项目初始化后。
- 每批章节完成后。
- 手动修改状态文件后。
- 进入新卷前。

若 doctor 报错，先修系统问题，再继续写作。

### 写后索引

每章正文写入 `chapters/` 后运行：

```bash
python3 scripts/chapter_index.py --write
```

如果只想检查：

```bash
python3 scripts/chapter_index.py --check
```

### 单章文本审计

每章 final-check 前，对最终候选稿运行：

```bash
python3 scripts/text_audit.py chapters/000N_标题.md
```

如果正文尚未写入 `chapters/`，主会话可先对 runtime 中的候选稿进行同类检查，或在写入后立刻审计并返修。

### Hook 报告

规划下一章或进入批量写作前运行：

```bash
python3 scripts/hook_report.py --current N
python3 scripts/hook_matrix.py --current N
```

其中 `N` 是当前最新已定稿章节号。报告出现 warnings 时，必须在 intent 的 Hook 预算与半衰期检查中处理。

### 结构报告

以下时机运行：

```bash
python3 scripts/structure_report.py
```

- 新书大纲搭建完成后。
- 每批章节完成后。
- 进入新卷前。
- 手动移动、删除或补写章节后。

结构报告只检查结构闭环，不评价文学质量。

## 硬性格式规则

- 对话统一使用中文双引号。
- 禁止把内心独白放进括号里。
- 章尾至少留下一个钩子。
- 每场冲突必须推进情节、关系、后台碎片或人物后效之一。
- 日常场景必须承担埋伏笔、推关系、建立反差中的至少一项。
