---
chapter: 000N
status: planned
goal:
threadRefs: []
plannerInputs:
  - story/system_protocol.md
  - story/state_contract.md
  - story/current_focus.md
  - story/current_state.md
  - story/chapter_summaries.md
  - story/pending_hooks.md
  - story/hook_protocol.md
  - story/emotional_arcs.md
  - story/style_blacklist.md
  - skills/skill_protocol.md
  - skills/skill_registry.md
  - story/outline/story_frame.md
  - story/outline/volume_map.md
  - story/book_rules.md
---

# Chapter Plan - 模板

## 场景序列

### 场景1：（名称）

- 地点：
- POV：
- 出场人物：
- 情绪基调：
- 推进什么：
- 欲望：
- 阻力：
- 动作：
- 后果：
- 余波：
- 锚点物件/身体动作：
- 章内位置：开头 / 中段 / 结尾

### 场景2：（名称）

- 地点：
- POV：
- 出场人物：
- 情绪基调：
- 推进什么：
- 欲望：
- 阻力：
- 动作：
- 后果：
- 余波：
- 锚点物件/身体动作：
- 章内位置：

## 钩子操作清单

| hook_id | 操作 | 优先级 | 半衰期 | 具体方式 | 正文证据 | 正文出现后是否进入伏笔池 |
| --- | --- | --- | --- | --- | --- | --- |

## 半衰期处理

| hook_id | 最近推进 | 半衰期 | 是否到期 | 本章处理 |
| --- | --- | --- | --- | --- |

## Agent 输出路径

| 阶段 | 输出文件 | 状态 |
| --- | --- | --- |
| Writer | `story/runtime/chapter-000N.writer.md` | pending |
| Polish | `story/runtime/chapter-000N.polish.md` | pending |
| Review | `story/runtime/chapter-000N.review.md` | pending |
| Fixer | `story/runtime/chapter-000N.fixer.md` | pending |
| Final Check | `story/runtime/chapter-000N.final-check.md` | pending |

## 角色行为一致性核查

> 对照角色卡的 Personality Lock、Behavioral Constraints 和压力测试结论。

| 角色 | 本章行为 | 是否符合 PersonalityLock | 压力测试一致性 | 信息边界检查 |
| --- | --- | --- | --- | --- |

## Scene Beat 需求

| 场景 | 是否需要单独 scene beat | 原因 | 文件 |
| --- | --- | --- | --- |
| 场景1 | yes/no |  | `story/runtime/chapter-000N.scene-1.md` |

复杂场景、关系转折、身份揭露、高潮、亲密张力、关键 hook 回收场景建议使用 `story/runtime/_template.scene-beat.md`。

## 文笔负面清单预检

从 `story/style_blacklist.md` 选择本章最需要避免的 3-5 项：

1.
2.
3.

## Skill 调用计划

| skill | 触发原因 | 使用阶段 | 输入 | 输出 | 采纳方式 |
| --- | --- | --- | --- | --- | --- |

## 段落形态预检

- 日常/过渡章：短段占比目标低于 65%，连续短段不超过 4 段。
- 冲突/高压对话章：允许快切，但每 5-7 段应有环境压力或身体余波。
- 合并候选：只报告一个动作/状态、低于 40 字、且前后没有节奏断裂需求的段落，应并入前后段。
