# Scripts

## create_project.py

```bash
python3 scripts/create_project.py "我的新小说"
python3 scripts/create_project.py "我的新小说" --target /path/to/books
```

用途：

- 从 Narrative Workbench 模板创建新书项目目录。
- 保留 `.claude/agents/`、`story/`、`scripts/`、`skills/` 等工作流文件。
- 更新 `story/state/manifest.json` 项目名。
- 生成新项目介绍文件 `PROJECT.md`。
- 避免直接污染 `_frameworks/narrative_workbench` 模板目录。

## doctor.py

运行：

```bash
python3 scripts/doctor.py
```

检查内容：

- 核心文件是否存在。
- JSON 是否可解析。
- `.claude/agents/*.md` frontmatter 是否有效。
- `chapters/index.json` 是否指向真实正文。
- `pending_hooks.md` 字段是否符合 `hook_protocol.md`。
- hook 状态、优先级、半衰期是否合法。
- runtime 状态是否在系统状态机允许范围内。
- `CLAUDE.md` 是否引用关键系统协议。

建议执行时机：

- 新书项目初始化后。
- 每批章节写作完成后。
- 手动改状态文件后。
- 长篇进入新卷前。

## chapter_index.py

```bash
python3 scripts/chapter_index.py --check
python3 scripts/chapter_index.py --write
```

用途：

- 扫描 `chapters/000N_标题.md`。
- 生成或检查 `chapters/index.json`。
- 统计每章字数和更新时间。

## text_audit.py

```bash
python3 scripts/text_audit.py chapters/0001_标题.md
```

用途：

- 统计字数、段落数、短段连续数、对话数量。
- 检查禁用引号 `「」『』`。
- 提示西文对话引号、括号内心独白、连续句末“了”。
- 统计高风险 AI 味词。

## hook_report.py

```bash
python3 scripts/hook_report.py --current 12
```

用途：

- 统计活跃 hook 和 core hook 是否超预算。
- 检查半衰期过期 hook。
- 检查活跃 hook 是否缺正文证据。

## hook_matrix.py

```bash
python3 scripts/hook_matrix.py --current 12
```

用途：

- 输出 hook 优先级和回收节奏分布。
- 检查上游依赖是否存在。
- 检查依赖环。
- 检查活跃 hook 是否缺预期回收或正文证据。
- 检查 resolved hook 是否缺回收证据。
- 列出被活跃依赖阻塞的 hook。

## structure_report.py

```bash
python3 scripts/structure_report.py
```

用途：

- 检查核心结构文件是否存在。
- 检查章节文件、章节摘要、情感弧光是否互相覆盖。
- 检查已定稿章节是否有 intent / plan / final-check。
- 检查 runtime 是否存在明显 dangling 状态。
- 检查 `chapters/index.json` 是否覆盖章节文件。

## skill_check.py

```bash
python3 scripts/skill_check.py
python3 scripts/skill_check.py --skill skill-name
```

用途：

- 检查 `skills/skill_registry.md` 表头。
- 检查 skill 名称是否合法。
- 检查状态是否为 `enabled` / `disabled` / `deprecated`。
- 检查入口文件路径是否存在。
- 在用户要求使用某 skill 时，确认该 skill 已注册。

## 边界

这些脚本只做确定性辅助，不做创作判断。不要用脚本自动总结章节、自动回收 hook、自动润色正文或自动调度 Agent。
