# 临安雪 — Narrative Workbench 演示项目

南宋绍兴年间，女医林半夏伪装身份混入太医院寻找失散的弟弟，却卷入宫廷权力斗争。

本演示项目展示了 Narrative Workbench v0.3.0 的全部核心功能。

---

## 项目结构

```
linan_snow_demo/
├── chapters/
│   └── drafts/
│       ├── chapter-0001.author.md   ← 第1章手写稿（约1500字）
│       └── chapter-0002.author.md   ← 第2章手写稿（约1500字）
├── story/
│   ├── outline/
│   │   ├── story_frame.md           ← 故事框架：五卷结构、世界观铁律、禁令
│   │   └── volume_map.md            ← 分卷地图：每卷 Objective/KR/情绪曲线
│   ├── roles/
│   │   ├── 林半夏.md                ← 主角卡：Personality Lock、压力测试、对白风味
│   │   └── 老僧.md                  ← 配角卡：核心标签、行为约束
│   ├── ledger/                      ← [v0.3 新增] 结构化账本（7类JSONL）
│   │   ├── hooks.jsonl              ←   2条伏笔记录
│   │   ├── facts.jsonl              ←   3条核心事实
│   │   ├── timeline.jsonl           ←   2条时间线事件
│   │   ├── characters.jsonl         ←   2个角色摘要
│   │   ├── relationships.jsonl      ←   1条关系记录
│   │   ├── secrets.jsonl            ←   2条秘密边界
│   │   └── locations.jsonl          ←   2个关键地点
│   ├── views/                       ← [v0.3 新增] 自动生成的Markdown视图
│   │   ├── hook_dashboard.md        ←   伏笔看板
│   │   ├── knowledge_matrix.md      ←   角色知识边界矩阵
│   │   ├── timeline.md              ←   时间线
│   │   └── relationships.md         ←   关系网络
│   ├── plans/
│   │   └── chapter-0001_director_sheet.yaml  ← [v0.3 新增] 章节导演表
│   ├── runtime/
│   │   ├── chapter-0001.intent.md
│   │   ├── chapter-0001.plan.md
│   │   └── chapter-0001_scene_handoffs.yaml  ← [v0.3 新增] 场景接力卡
│   ├── state/                       ← JSON 状态镜像
│   └── style_samples/
│       └── sample_chapter_01.md     ← 文风样章（供 decompose_style.py 分析）
└── skills/                          ← 项目级 Skill 注册
```

---

## 快速验证：v0.2 功能

```bash
cd examples/linan_snow_demo

# 项目健康检查
python ../../scripts/doctor.py

# 项目状态概览
python ../../scripts/status.py

# 为 Writer 构建 Ch1 上下文包
python ../../scripts/context_builder.py --chapter 1 --agent writer

# 运行确定性门禁
python ../../scripts/gatekeeper.py --chapter 1 --stage final

# 为手写稿生成审查简报
python ../../scripts/review_author_chapter.py --chapter 1

# 分析手写稿文风
python ../../scripts/decompose_style.py --input chapters/drafts/chapter-0001.author.md

# 构建知识库索引
python ../../scripts/knowledge_index.py build
```

## 快速验证：v0.3 新增功能

```bash
cd examples/linan_snow_demo

# === 上下文引擎 ===
# 精确上下文注入（替代 context_builder 核心逻辑）
python ../../scripts/relevance_resolver.py --chapter 1 --agent writer

# === 结构化账本 ===
# 查看账本状态
python ../../scripts/ledger_manager.py validate

# 查询活跃伏笔
python ../../scripts/ledger_manager.py query hooks --filter 'status=="open"'

# 查询所有事实
python ../../scripts/ledger_manager.py list facts

# === 视图渲染 ===
# 生成全部作者可读 Markdown 视图
python ../../scripts/render_views.py all
# 查看: cat story/views/hook_dashboard.md

# === 章节统筹 ===
# 为 Ch1 生成导演表
python ../../scripts/director_sheet.py --chapter 3 --from-template --title "入局"

# 验证已有导演表
python ../../scripts/director_sheet.py --chapter 1 --validate

# === 平台同步（仅演示，需在模板目录运行） ===
# python ../../scripts/sync_skills.py --dry-run
```

## 演示要点

| 功能 | 演示文件 | 说明 |
|---|---|---|
| 手写稿审查 | `review_author_chapter.py --chapter 1` | 全文分块审查（非截断），段落 ID 锚定 |
| 手写稿润色 | `polish_author_chapter.py --chapter 1 --mode light` | 5 种润色模式，默认不覆盖原稿 |
| 上下文注入 | `relevance_resolver.py --chapter 1 --agent writer` | 根据 plan 的 cast_ids/hook_ids 精确检索 |
| 结构化账本 | `ledger_manager.py query hooks` | 7 类 JSONL，支持过滤查询 |
| 视图渲染 | `render_views.py all` | 账本 → Markdown 看板 |
| 导演表 | `director_sheet.py --chapter 1 --validate` | YAML 全章蓝图 |
| 场景接力 | `chapter-0001_scene_handoffs.yaml` | 物理/情绪/信息状态传递 |
| 文风分析 | `decompose_style.py --input ...` | 输出 style_analysis.md + profile + skill |

## 说明

所有 Python 脚本只做确定性工作——不调用 AI 模型、不自动改写正文。
真正的语义审查和润色由 Claude Code/Codex 的 Agent 完成。
