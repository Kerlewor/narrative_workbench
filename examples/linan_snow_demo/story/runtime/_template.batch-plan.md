# Batch Plan - 模板

---
batch: 000N-000M
status: planned
maxChapters: 5
---

## 批次目标

（这 3-5 章共同推进第几卷的哪个 Objective / KR）

## 批前状态摘要

- 当前章节：
- 当前地点：
- 主角状态：
- 当前敌我：
- 活跃主钩：
- 本批禁止提前揭示：
- canonical 提交顺序：
- 允许流水线重叠的 working 阶段：（如"Writer ChN+1 可与 Polish ChN 同时进行"）

## 章节节奏表

| 章节 | 暂定标题 | 类型 | POV | 主推进线 | 必须发生的改变 | 章尾钩子 |
| --- | --- | --- | --- | --- | --- | --- |

## 钩子预算

| hook_id | 当前状态 | 优先级 | 最近推进 | 半衰期 | 本批操作 | 涉及章节 | 具体方式 | 是否进入正式伏笔 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 半衰期到期清单

| hook_id | 到期原因 | 必须处理章节 | 处理方式 |
| --- | --- | --- | --- |

## Python 辅助报告

- `python3 scripts/hook_report.py --current N-1` 输出摘要（N 是本批首章号，N-1 是最新已定稿章）：
- `python3 scripts/hook_matrix.py --current N-1` 输出摘要：
- `python3 scripts/structure_report.py` 输出摘要：
- `python3 scripts/doctor.py` 是否通过：

## 情绪曲线

- 第1章：
- 第2章：
- 第3章：
- 第4章：
- 第5章：

## 连续性约束

- N 章章尾如何接 N+1 章开头：
- N+1 章章尾如何接 N+2 章开头：
- N+2 章章尾如何接 N+3 章开头：
- N+3 章章尾如何接 N+4 章开头：

## 不要做

1.
2.
3.

## 批末审计重点

- 连续性：
- 钩子账：
- 节奏：
- 文笔：
- 信息边界：
- canonical 状态是否只由主会话按章节顺序提交：
