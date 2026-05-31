# Narrative Workbench — 章节生命周期

## 状态机

```
planned → drafted → polished → reviewed → fixed → final-check → final-aligned
                 ↘ ↓          ↓
               needs-rewrite  needs-repair → superseded
```

| 状态 | 含义 | 触发条件 |
|---|---|---|
| `planned` | 已规划，未起草 | intent/plan 创建后 |
| `drafted` | Writer 完成草稿 | Writer 写出草稿 |
| `polished` | Polish 完成润色 | Polish 写出润色稿 |
| `reviewed` | Review 完成审阅 | Review 写出审阅报告 |
| `fixed` | Fixer 完成修复 | Fixer 写出修复稿 |
| `final-aligned` | 通过门禁，已写入正文 | gatekeeper + final-check 通过 |
| `needs-rewrite` | Review 判定结构性失败 | Review 报告标注 |
| `needs-repair` | final-check 未通过 | gatekeeper/final-check 阻塞 |
| `superseded` | 本章被废弃 | 用户或主会话标记 |

## 单章完整流水线

1. **规划** → `story/runtime/chapter-000N.intent.md` + `.plan.md`
2. **上下文编译** → `relevance_resolver.py` 生成任务包
3. **Writer** → `story/runtime/chapter-000N.writer.md`
4. **Polish** → `story/runtime/chapter-000N.polish.md`
5. **Review** → `story/runtime/chapter-000N.review.md`
6. **Fixer** → `story/runtime/chapter-000N.fixer.md`
7. **Gatekeeper** → 确定性门禁检查（必须通过）
8. **Final-check** → 主会话执行定稿门禁
9. **写入 canonical** → `chapters/000N_标题.md`
10. **同步状态** → Markdown + JSON 状态更新

## 章节双循环（v0.3+）

适用于分场景写作模式：

**内循环（场景完成）：**
```
导演表 → 写当前场景 → 轻量检查 → 生成接力卡 → 下一场景
```

**外循环（整章完成）：**
```
合并全部场景 → 全章连续性审查 → 局部修订 → 节奏复核 → 定稿
```

## 不同长度策略

| 字数 | 写作方式 | 审查方式 |
|---|---|---|
| ≤3000 | 可整章生成 | 直接全文审查 |
| 3000–6000 | 建议分场景 | 全文审查 + 局部润色 |
| 6000–10000 | 分场景 + 接力卡 | 全文连续性 + 分场景语言审查 |
| >10000 | 强制导演表与接力卡 | 全文审查，禁止只做局部审查 |

## 批量写作

- 单批最多 5 章
- 每章写定后立刻同步状态（禁止先写完多章再统一补状态）
- 批前 drift check + hook 报告
- 批末 audit 审计
