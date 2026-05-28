# Changelog

## v0.2.0 — 上下文构建器与门禁系统

### 新增

**`scripts/context_builder.py`** — 按 Agent 类型和章节构建上下文包。

- 支持 `--chapter N --agent <writer|polish|review|fixer|librarian>` 
- 每个 Agent 类型有独立的必读内容、压缩摘要和排除文件配置
- 内置 token 预算（Writer 18K / Polish 12K / Review 15K / Fixer 8K / Librarian 20K）
- 输出包含：必读内容、压缩摘要、禁止泄露提示、输出契约、省略文件清单、预算摘要
- 超出预算时输出 WARNING
- 产物路径：`story/runtime/chapter-XXXX.<agent>.context.md`

**`scripts/gatekeeper.py`** — 确定性门禁检查，在 final-check 之前运行。

- 检查流水线产物完整性（intent / plan / writer / polish / review / fixer 是否全部存在）
- 检查 Review→Fixer 响应覆盖（Review 报告的必修问题是否被 Fixer 处理）
- 检查 hook 半衰期同步（是否有到期未处理的活跃伏笔）
- 检查禁止模式（括号内心独白、非标准引号、AI 味高频词句）
- 检查 intent 状态合法性
- 输出 PASSED / FAILED，阻塞问题和非阻塞警告分开
- 产物路径：`story/runtime/chapter-XXXX.gatekeeper.md`

### 修改

- **CLAUDE.md** — final-check 步骤增加 gatekeeper 前置检查；Agent 恢复步骤增加 context_builder 建议
- **RUN_RULES.md** — 阶段门禁表新增 context_builder 和 gatekeeper 行；脚本职责表新增两个条目；Final-check 前将 gatekeeper 标记为"必须"
- **doctor.py** — 检查范围后续版本将覆盖 context 和 gatekeeper 产物

### 设计决策

- context_builder 是"建议"而非"必须"：主会话仍然可以手动准备 Agent 输入，context_builder 提供自动化和可复现性
- gatekeeper 是 Final-check 前的"必须"步骤：所有检查都是确定性验证，不依赖 AI 判断。gatekeeper 通过不代表章节质量合格——只代表流程完整
- 两个脚本都只做确定性工作，不替代主模型的创作判断

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
