# Changelog

## v0.2.0 — 全面运行时升级

### 新增脚本（共 11 个，v0.1.0 原有 8 个 → 现共 19 个）

**上下文工程：**
- `context_builder.py` — 按 Agent 类型和章节构建上下文包，内置 token 预算。产物：`chapter-XXXX.<agent>.context.md`
- `prompt_compiler.py` — 三层 prompt 编译（Base + 项目规则 + 本章任务）。产物：`chapter-XXXX.<agent>.prompt.md`

**流程确定性：**
- `gatekeeper.py` — 确定性门禁检查（final-check 前必须运行）。检查流水线完整性、Review→Fixer 响应覆盖、hook 同步、禁止模式。产物：`chapter-XXXX.gatekeeper.md`

**知识库与状态：**
- `knowledge_index.py` — 关键词+元数据项目索引，支持 build/query 两种模式。产物：`.nw_index/entity_index.json`、知识包
- `status.py` — 项目状态概览：章节进度、hook 统计、角色漂移风险、建议下一步

**文风与角色：**
- `style_report.py` — 定量文风报告（句长分布、对白密度、AI 味模式命中）。产物：`chapter-XXXX.style_report.md`
- `character_drift_report.py` — 对照角色约束扫描章节文本，输出疑似漂移预警。产物：`chapter-XXXX.character_drift.md`
- `decompose_style.py` — 文风拆解器。输入文本 → 输出 `style_analysis.md` + `style_profile.json` + `style_skill.md`

**共创与兼容：**
- `review_author_chapter.py` — 为手写章节生成 Review 审查简报
- `polish_author_chapter.py` — 为手写章节生成 Polish 润色简报（5 种模式）
- `import_inkos_project.py` — InkOS 项目文件映射迁移

### 共创模式

- **审查第 N 章** — 对手写章节进行一致性审查，不改正文，只出问题清单
- **润色第 N 章 --模式** — 5 种润色模式（preserve-author-style / project-style-align / anti-ai-only / dialogue-only / rhythm-only），默认不覆盖原稿
- **第 N 章写作简报** — 作者动笔前生成约束简报

### Skill 模板更新

- `_template.skill-entry.md` — 新增"知识库依赖"和"内置知识声明"字段
- `_template.skill-request.md` — 新增"知识库查询"字段

### 文档更新

- **CLAUDE.md** — 恢复 Agent 职责标题；final-check 增加 gatekeeper；新增 3 个共创命令 + 深化角色命令
- **RUN_RULES.md** — 脚本职责表新增 10 行；阶段门禁表新增 4 行；gatekeeper 失败处理规则
- **START_HERE.md** — 命令列表和脚本列表同步更新
- **system_protocol.md** — Working 区新增 3 种 runtime 文件类型
- **README.md** — 新增共创模式章节；用户命令表新增 3 个命令
- **doctor.py** — 检查范围覆盖全部 18 个脚本和 6 种新 runtime 文件类型

### 设计决策

- context_builder 和 prompt_compiler 是"建议"——主会话仍可手动准备 Agent 输入
- gatekeeper 是 Final-check 前的**必须**步骤——所有检查都是确定性验证
- 共创模式保护作者原稿——Review 不改文、Polish 默认不覆盖、所有改动标注位置和原因
- Skill 零事实原则——Skill 是纯方法论，领域事实来自知识库

---

## v0.1.0 — 首次公开发布

- 四 Agent 持久会话写作流水线（Writer / Polish / Review / Fixer）
- Project Librarian 上下文路由
- 角色设计四轮协议（核心人格 → 压力测试 → 关系张力 → 声音表达）
- Hook 伏笔生命周期管理与半衰期系统
- 章节状态机（10 状态，含 needs-rewrite / needs-repair 失败回路）
- Skill 可插拔扩展机制
- 8 个 Python 确定性检查脚本
- 导入现成大纲流程（含最低完备性检查和主动缺口检测）
- 深化角色命令
- Context Packet 替代规则
- Runtime 跨卷归档策略
- AGPL-3.0 许可证
- 受 InkOS 启发，独立 Markdown-native 实现
