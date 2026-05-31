# 《临安雪》— Narrative Workbench 演示项目

> 这是一个 Narrative Workbench v0.3.0 的演示项目。完整协议见模板目录的 `CLAUDE.md`。
> 
> 核心协议引用: `RUN_RULES.md`, `story/system_protocol.md`, `story/state_contract.md`, `story/hook_protocol.md` — 详见模板目录。

## 快速开始

对 AI 说：
- `写第3章` — 启动第3章的完整写作流水线
- `审查第1章` — 审查第1章手写稿
- `润色第2章 --模式 light` — 润色第2章
- `深化角色 林半夏` — 对林半夏进行人格深度讨论
- `第3章写作简报` — 生成第3章写作约束简报

## 确定性门禁

所有 Python 脚本位于模板的 `scripts/` 目录，通过相对路径调用：
```bash
python ../../scripts/doctor.py
python ../../scripts/status.py
python ../../scripts/gatekeeper.py --chapter N --stage final
```
