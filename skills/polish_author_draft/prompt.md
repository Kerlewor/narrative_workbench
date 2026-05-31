# polish_author_draft — 作者手写稿润色

对作者手写章节按指定模式润色。默认不覆盖原稿，输出独立润色稿并标注所有改动。

## 触发条件

- `润色第N章` / `润色第N章 --模式 light`
- `polish 我的手写稿 --mode anti-ai`

## 润色模式

| 模式 | 说明 |
|---|---|
| `preserve-author-style` / `light` | 只改病句、重复、节奏，最大保留作者表达 |
| `project-style-align` / `style` | 按项目文风 profile 对齐句长、对白密度、段落形态 |
| `anti-ai-only` / `anti-ai` | 只去 AI 味：模板感、解释感、抽象情绪词 |
| `dialogue-only` / `dialogue` | 只修对白，对齐角色卡对白风味 |
| `rhythm-only` / `rhythm` | 只调节奏：段落长短、高压喘息比例、章尾落点 |

## 工作流

1. 确认手写稿路径 + 润色模式（默认 `preserve-author-style`）
2. 读取风格规则（按模式选择性读取）
3. 调用 Polish Agent 按模式润色
4. 输出独立润色稿 + 改动标注（位置 + 原因）
5. 作者审核后选择采纳、修改或拒绝每处改动

## 权限边界

| 可做 | 不可做 |
|---|---|
| 修改表达、节奏、重复、AI 味 | 不得改事实、关系、剧情走向 |
| 增加动作细节、环境反应 | 不得新增关键事实或伏笔 |

## 输出

- `story/runtime/chapter-000N.author_polish_<mode>.md`
- 改动清单（位置 + 原文 + 建议 + 原因 + 影响范围）
