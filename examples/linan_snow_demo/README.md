# 临安雪 — Narrative Workbench 演示项目

一个最小可运行的演示项目。设定是**南宋绍兴年间，女医林半夏伪装身份混入太医院寻找失散的弟弟，却卷入宫廷权力斗争**。

这个项目包含了 Narrative Workbench 在实际写作中会触及的所有核心文件：

- `story/current_state.md` — 第 1 章结束时的角色状态和位置
- `story/pending_hooks.md` — 2 个已开伏笔（弟弟下落线 + 老僧身份线）
- `story/roles/林半夏.md` — 含 Personality Lock、压力测试结论、对白风味、禁止写法
- `story/runtime/chapter-0001.intent.md` — 第 1 章的目标、弧光差值和 hook 操作
- `story/runtime/chapter-0001.plan.md` — 第 1 章的场景序列和钩子操作清单
- `chapters/drafts/chapter-0001.author.md` — 作者手写稿（约 1500 字），供共创模式演示

你可以用它来验证所有 Python 脚本的行为，也可以把它作为新建项目时的参考模板。

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
