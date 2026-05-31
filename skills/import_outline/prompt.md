# import_outline — 搭建或导入大纲

从零搭建新书大纲（五阶段流程）或导入现成大纲。

## 触发条件

- `搭建大纲`
- `导入大纲` / `导入现成大纲`
- `我有现成大纲`

## 工作流（搭建大纲）

**阶段 1：确立故事内核** — 一句话主题、基调、主角核心弧线、全书 Objective
**阶段 2：前台/后台双层结构** — 隐性冲突线 + 暗线阴谋 + 咬合机制
**阶段 3：分卷设计** — 每卷 Objective/KR/情绪曲线/卷尾不可逆改变
**阶段 4：角色设计** — 四轮深度讨论（核心人格 → 人格压力测试 → 关系性格张力 → 声音与表达）
**阶段 5：世界观铁律与禁令** — 不可违反的设定铁律、类型边界、视角规则

详细执行协议见 `CLAUDE.md` 的"搭建大纲"章节。

## 工作流（导入现成大纲）

1. 读取 `story/outline/_template.import-outline.md`
2. 用户大纲默认为 `candidate`，不得直接写入 canonical
3. 拆分：canon / candidate / 缺口 / 冲突 / 逻辑跳跃
4. 主动检测缺口并追问
5. 用户确认后写入 canonical 文件
6. 运行 `structure_report.py` + `doctor.py`
7. 提示用户可深化角色

## 输出

- `story/brief.md`, `story/author_intent.md`
- `story/outline/story_frame.md`, `story/outline/volume_map.md`
- `story/book_rules.md`, `story/roles/*.md`
- `story/character_matrix.md`, `story/current_focus.md`
