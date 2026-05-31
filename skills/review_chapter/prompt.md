# review_chapter — 章节审查

对已存在章节（AI 写或作者手写）启动审查/返修流水线。

## 触发条件

- `审阅第N章`（AI 写章节）
- `审查第N章`（作者手写章节）
- `review 我的手写稿`

## 工作流（AI 写章节）

1. 读取 `chapter-000N.intent.md` 确认当前状态
2. 按状态进入对应阶段：
   - `final-aligned` → 先问用户要修什么
   - `drafted` → Polish → Review → Fixer
   - `polished` → Review → Fixer
   - `reviewed` → Fixer
   - `fixed` → final-check
   - `needs-rewrite` → Writer 重写
   - `needs-repair` → Fixer 重新修复
   - `planned` → 使用"写第N章"
3. 主会话最后写定 + 同步状态

## 工作流（作者手写章节）

1. 确认手写稿位置：`chapters/drafts/chapter-000N.author.md`
2. 读取手写稿 + 角色卡 + 伏笔池 + 当前状态
3. 调用 Review Agent 进行一致性审查（**不改文**）
4. 输出问题清单（按严重度排列）：角色违背、伏笔遗漏、秘密泄露、状态冲突、节奏失衡、AI 味

## 输入

- 待审章节正文（`chapters/000N_标题.md` 或 `chapters/drafts/chapter-000N.author.md`）
- 角色卡、伏笔池、当前状态

## 输出

- `story/runtime/chapter-000N.review.md`（审阅报告）
- 问题清单（阻塞 / 高 / 中 / 低）
