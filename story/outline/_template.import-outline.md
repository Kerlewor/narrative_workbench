# Import Outline - 现成大纲导入模板

> 用于用户已有大纲、设定集、旧稿梗概、分卷草案时。导入目标不是照搬，而是把用户材料拆成可维护的工作流文件。

## 0. 输入信息

- 用户大纲来源：
- 输入形式：粘贴文本 / Markdown / PDF / 旧章节 / 口述 / 其他
- 用户要求：完整保留 / 可重构 / 只保留核心设定 / 扩写成长篇
- 目标篇幅：
- 目标类型：

## 1. 导入原则

- 用户提供的大纲默认是 `candidate`，不是项目 canon。
- 只有用户明确确认的内容，才能写入 canonical 文件。
- 不确定、矛盾、缺失的信息必须进入“追问清单”。
- 大纲中的“伏笔候选”不能直接进入 `pending_hooks.md`，除非用户确认且它属于正文已发生事实；新项目未写正文时，伏笔应先进入 `story/outline/volume_map.md` 或 runtime candidate。
- 旧稿不是最高事实源；新项目开始后，`chapters/` 中定稿正文才是最高事实源。

## 2. 大纲摘要

用 300-800 字压缩用户大纲：

-

## 3. Canon / Candidate 拆分

### 已确认 Canon

| 项目 | 内容 | 用户证据 |
| --- | --- | --- |

### Candidate 候选

| 项目 | 内容 | 需要确认的问题 |
| --- | --- | --- |

## 4. 缺口与冲突

### 缺失信息

| 编号 | 缺口 | 为什么必须问 | 影响文件 |
| --- | --- | --- | --- |

### 冲突点

| 编号 | 冲突内容 | 可能解释 | 需要用户决定 |
| --- | --- | --- | --- |

### 逻辑跳跃

| 编号 | 跳跃位置 | 缺少的因果 | 建议补法 |
| --- | --- | --- | --- |

## 5. 最低完备性检查

> AI 在拆分完成后、向用户提问前，必须逐项检查以下内容。标记为"缺失"的项必须列入追问清单。"不确定"的项需要向用户确认。

| 检查项 | 状态（已覆盖/不确定/缺失） | 追问优先级 |
|---|---|---|
| 一句话主题清晰可陈述 |  | 立即 |
| 主角身份、核心诉求、错误信念可识别 |  | 立即 |
| 主角有内在矛盾（即使大纲未明确写出） |  | 立即 |
| 前台冲突与后台真相的关系可描述 |  | 立即 |
| 终局方向有大致轮廓 |  | 立即 |
| 主要配角和对手有独立诉求 |  | 本批 |
| 分卷/分阶段有大致边界 |  | 本批 |
| 世界观铁律或类型边界可识别（至少 2 条） |  | 本批 |
| 主角的情感表达风格有线索 |  | 可稍后 |
| 核心关系线的起点和终点可描述 |  | 可稍后 |
| 主要角色的对白或行为风格有线索 |  | 可稍后 |

检查完成后，AI 应向用户汇报：哪些已覆盖、哪些需要补充、哪些可以稍后。只就"立即"和"本批"优先级的项向用户提问。

## 6. 故事框架拆解

| 模块 | 从大纲提取的内容 | 是否确认 | 写入目标 |
| --- | --- | --- | --- |
| 一句话主题 |  |  | `story/brief.md` |
| 主角核心弧线 |  |  | `story/outline/story_frame.md` |
| 前台冲突 |  |  | `story/outline/story_frame.md` |
| 后台真相 |  |  | `story/outline/story_frame.md` |
| 终局方向 |  |  | `story/outline/story_frame.md` |
| 世界观铁律 |  |  | `story/book_rules.md` |
| 类型禁令 |  |  | `story/book_rules.md` |

## 7. 分卷 / 阶段拆解

| 卷/阶段 | 起止范围 | Objective | KR1 | KR2 | KR3 | 卷尾不可逆改变 | 缺口 |
| --- | --- | --- | --- | --- | --- | --- | --- |

写入目标：

- `story/outline/volume_map.md`
- 必要时写入 `story/outline/expansion_blueprint.md`

## 8. 角色拆解

| 角色 | 大纲定位 | 核心诉求 | 弧线起点 | 弧线终点 | 反差细节 | 信息边界 | 是否需追问 |
| --- | --- | --- | --- | --- | --- | --- | --- |

写入目标：

- `story/roles/*.md`（注意：导入阶段仅填写基础信息和可提取的标签。Personality Lock、Behavioral Constraints、压力测试结论、对白风味、动作锚点等深度内容需通过"深化角色"命令补全——AI 必须在导入完成后主动提示用户。）
- `story/character_matrix.md`

## 9. Hook 候选拆解

> 注意：导入阶段通常只形成 hook candidate，不直接进入 `pending_hooks.md`。

| candidate_id | 类型 | 来源位置 | 内容 | 预计开钩位置 | 预计回收位置 | 上游依赖 | 是否核心 |
| --- | --- | --- | --- | --- | --- | --- | --- |

写入目标：

- `story/outline/volume_map.md`
- `story/outline/expansion_blueprint.md`
- 后续章节 runtime 的 hook candidate

## 10. 必问问题

> 基于 Section 5（最低完备性检查）的结果，将标记为"缺失"和"不确定"的项转为具体问题。只问会影响结构的问题。避免重复询问大纲已经明确的内容。

### 必须立即问（来自最低完备性检查中优先级为"立即"的缺失项）

1.
2.
3.

### 本批问（来自优先级为"本批"的缺失项）

1.
2.
3.

### 可以稍后问（来自优先级为"可稍后"的缺失项——可在导入完成后通过"深化角色"命令处理）

1.
2.
3.

## 11. 写入计划

| 文件 | 写入内容 | 是否需要用户确认 |
| --- | --- | --- |
| `story/brief.md` |  | yes/no |
| `story/author_intent.md` |  | yes/no |
| `story/outline/story_frame.md` |  | yes/no |
| `story/outline/volume_map.md` |  | yes/no |
| `story/outline/expansion_blueprint.md` |  | yes/no |
| `story/book_rules.md` |  | yes/no |
| `story/roles/*.md` |  | yes/no |
| `story/character_matrix.md` |  | yes/no |
| `story/current_focus.md` |  | yes/no |

## 12. 导入后检查

导入完成后运行：

```bash
python scripts/structure_report.py
python scripts/doctor.py
```

如果已生成 hook candidate 表，但尚未写正文，不运行 `hook_report.py` 作为正式伏笔审计；正式 hook 审计从正文定稿后开始。

