# Changelog

## v0.2.0 — 上下文工程与共创模式

### 新增脚本

**`scripts/context_builder.py`** — 按 Agent 类型和章节构建上下文包。

- 5 种 Agent 各有独立的必读内容、压缩摘要和排除文件配置
- 内置 token 预算（Writer 18K / Polish 12K / Review 15K / Fixer 8K / Librarian 20K）
- 输出：必读内容 + 压缩摘要 + 禁止泄露提示 + 输出契约 + 省略文件清单 + 预算摘要
- 产物路径：`story/runtime/chapter-XXXX.<agent>.context.md`

**`scripts/prompt_compiler.py`** — 三层 prompt 编译（Base Prompt + 项目规则 + 本章任务）。

- Layer 1：从 `agents/<agent>.md` 读取 Agent 角色定义（永不变更）
- Layer 2：从 `story/book_rules.md` / `style_blacklist.md` / `style_profile.md` 编译项目规则
- Layer 3：从 intent / plan / context 编译本章任务注入，含半衰期到期 hook 风险提示
- 产物路径：`story/runtime/chapter-XXXX.<agent>.prompt.md`

**`scripts/gatekeeper.py`** — 确定性门禁检查，final-check 之前必须运行。

- 检查流水线产物完整性、Review→Fixer 响应覆盖、hook 半衰期同步、禁止模式、intent 状态合法性
- 输出 PASSED / FAILED + 阻塞问题（BLOCKING）+ 非阻塞警告（WARN）
- 产物路径：`story/runtime/chapter-XXXX.gatekeeper.md`

### 共创模式（新增命令）

- **审查第 N 章** — 对作者手写章节进行一致性审查，不改正文，只出问题清单
- **润色第 N 章 --模式** — 5 种润色模式（preserve-author-style / project-style-align / anti-ai-only / dialogue-only / rhythm-only），默认不覆盖原稿，标注所有改动位置
- **第 N 章写作简报** — 作者动笔前生成约束简报（本章类型 + 必须处理 + 禁止事项 + 推荐写法）

### Skill 模板更新

- `_template.skill-entry.md` — 新增"知识库依赖"和"内置知识声明"字段
- `_template.skill-request.md` — 新增"知识库查询"字段

### 修改

- **CLAUDE.md** — final-check 增加 gatekeeper；Agent 恢复增加 context_builder 建议；新增 3 个共创模式命令
- **RUN_RULES.md** — 阶段门禁表新增 context_builder / prompt_compiler / gatekeeper 行；脚本职责表新增 3 个条目
- **doctor.py** — 检查范围覆盖新脚本和新 runtime 文件类型
- **README.md** — 用户命令表新增 3 个共创模式命令

### 设计决策

- context_builder 和 prompt_compiler 是"建议"——主会话仍可手动准备 Agent 输入
- gatekeeper 是 Final-check 前的**必须**步骤——所有检查都是确定性验证，不依赖 AI 判断
- 共创模式保护作者原稿——Review 不改文、Polish 默认不覆盖、所有改动标注位置和原因

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
