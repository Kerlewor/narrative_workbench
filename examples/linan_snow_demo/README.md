# 临安雪 — Narrative Workbench 演示项目

这是一个最小可运行的演示项目，展示 Narrative Workbench v0.2.0 的核心脚本如何在实际项目中工作。

## 快速验证

```bash
cd examples/linan_snow_demo

# 项目健康检查
python3 ../../scripts/doctor.py

# 项目状态概览
python3 ../../scripts/status.py

# 为 Writer 构建 Ch1 上下文包
python3 ../../scripts/context_builder.py --chapter 1 --agent writer

# 为 Writer 编译 prompt
python3 ../../scripts/prompt_compiler.py --chapter 1 --agent writer

# 运行确定性门禁（预期 FAILED——缺少 Writer/Polish/Review/Fixer 产物）
python3 ../../scripts/gatekeeper.py --chapter 1 --stage final

# 为手写稿生成审查简报
python3 ../../scripts/review_author_chapter.py --chapter 1

# 分析手写稿文风
python3 ../../scripts/decompose_style.py --input chapters/drafts/chapter-0001.author.md

# 构建知识库索引
python3 ../../scripts/knowledge_index.py build
```

## 说明

所有 Python 脚本只做确定性工作——文件检查、格式校验、token 估算、简报生成。
脚本不调用 AI 模型、不自动改写正文、不替代主会话的创作判断。
