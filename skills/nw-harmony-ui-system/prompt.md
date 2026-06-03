# nw-harmony-ui-system

## Skill 名称

HarmonyOS 统一视觉系统 — 维护小说写作 App 的完整视觉语言规范。

## 用途

避免 AI 每写一页就换一套风格。提前规定页面边距、字体层级、卡片圆角、按钮类型、颜色系统、编辑器布局、AI 功能入口样式、空状态与加载状态、深色模式规则。所有前端 Agent 必须引用本 Skill 作为视觉实现的单一权威来源。

## 适用场景

- 任何 HarmonyOS App 页面的 UI 实现
- 新增页面或组件时，需要对齐现有视觉风格
- 代码审查阶段，检查 UI 一致性
- 设计师/产品经理对齐视觉方向

## 触发条件

- 编写或修改任何 `.ets` 页面文件
- 涉及组件样式、布局、颜色的代码变更
- 用户明确要求"统一视觉风格"或"调整 UI"
- Review 阶段发现 UI 不一致问题

## 必读输入

- `nw-product-flow-architect` 产出的页面清单
- `hmos-design-visual-mobile` 的参考输出（如已安装）

## 设计原则

### 定位

**它首先是写作软件，其次才是 AI 工作台。** 视觉设计必须服务于"安静写作"这个核心体验，而非炫耀 AI 能力。

### 关键词

安静、低干扰、大块留白、纸张质感、墨色为主、类似写作软件/电子书阅读器、AI 功能隐藏在需要时才展开。

## 颜色系统

### 浅色模式

| Token | 色值 | 用途 |
|---|---|---|
| `color_bg_primary` | `#FAF9F6`（暖白/纸张色） | 主背景（编辑器、阅读区） |
| `color_bg_secondary` | `#F5F2ED`（浅米色） | 次级背景（卡片、面板、设置页） |
| `color_bg_tertiary` | `#EDE8E0` | 分隔区域背景 |
| `color_surface` | `#FFFFFF` | 浮层、弹窗、底部面板背景 |
| `color_text_primary` | `#1C1C1C`（近黑） | 正文文字 |
| `color_text_secondary` | `#6B6B6B`（中灰） | 辅助说明、时间戳、章节编号 |
| `color_text_tertiary` | `#9E9E9E`（浅灰） | 占位符、禁用状态文字 |
| `color_accent` | `#4A6FA5`（蓝灰） | 主操作按钮、链接、选中态 |
| `color_accent_subtle` | `#E8EDF3`（浅蓝灰） | AI 功能区域背景、选中卡片 |
| `color_divider` | `#E0DCD5` | 分割线 |
| `color_error` | `#C44E4E`（暗红） | 错误、危险操作、删除按钮 |
| `color_warning` | `#C4914E`（暗琥珀） | 未保存标记、警告 |
| `color_success` | `#4E8C5E`（暗绿） | 已保存、生成完成 |

### 深色模式

| Token | 色值 | 用途 |
|---|---|---|
| `color_bg_primary_dark` | `#1A1A1A` | 主背景 |
| `color_bg_secondary_dark` | `#252525` | 次级背景 |
| `color_surface_dark` | `#2E2E2E` | 浮层背景 |
| `color_text_primary_dark` | `#E0DCD0`（暖白） | 正文文字 |
| `color_text_secondary_dark` | `#999999` | 辅助文字 |
| `color_accent_dark` | `#7B9DC7`（浅蓝灰） | 主操作（降低亮度避免刺眼） |

## 字体层级

使用 HarmonyOS 系统默认字体（HarmonyOS Sans）：

| Token | 字号 | 字重 | 用途 |
|---|---|---|---|
| `font_display` | 24fp | Bold | 页面标题（作品库、项目首页） |
| `font_heading_1` | 20fp | Medium | 章节标题 |
| `font_heading_2` | 17fp | Medium | 区块标题、角色名 |
| `font_body` | 16fp | Regular | 正文、编辑器默认字号 |
| `font_body_small` | 14fp | Regular | 辅助说明、列表副标题 |
| `font_caption` | 12fp | Regular | 时间戳、字数统计、脚注 |
| `font_button` | 15fp | Medium | 按钮文字 |

行高：`font_body` 使用 1.6 倍行高（`lineHeight: 25.6fp`），保证长文阅读舒适度。

## 间距系统

基础单位：4fp

| Token | 值 | 用途 |
|---|---|---|
| `space_xs` | 4fp | 图标与文字间距 |
| `space_sm` | 8fp | 列表项内间距、标签间距 |
| `space_md` | 16fp | 标准页面水平边距、卡片内边距 |
| `space_lg` | 24fp | 区块间距、卡片间距 |
| `space_xl` | 32fp | 页面顶部/底部留白 |
| `space_2xl` | 48fp | 大区块分隔（如编辑器与工具栏之间） |

页面水平边距：统一 `16fp`（`space_md`）。

## 组件规范

### 按钮

| 类型 | 样式 | 用途 |
|---|---|---|
| Primary | 实心，`color_accent` 背景，白色文字，圆角 8fp | 主操作：保存、新建、生成 |
| Secondary | 描边，`color_accent` 描边，透明背景 | 次要操作：查看详情、更多选项 |
| Text | 无背景无描边，`color_accent` 文字 | 轻量操作：取消、跳过、了解更多 |
| Danger | 实心，`color_error` 背景 | 删除、丢弃、不可逆操作 |
| AI Action | 实心，`color_accent_subtle` 背景，`color_accent` 文字，左侧 AI 小图标 | AI 润色、AI 续写、AI 审查 |

按钮最小点击区域：48fp × 48fp。

### 卡片

- 圆角：12fp
- 背景：`color_bg_secondary`（浅色）/ `color_bg_secondary_dark`（深色）
- 内边距：`space_md`（16fp）
- 卡片间距：`space_lg`（24fp）
- 阴影：不使用或极轻微（`elevation: 1fp`），保持平面感

### 编辑器

- 章节标题：`font_heading_1`，顶部居中或左对齐，与正文之间有清晰分隔
- 正文区：`font_body`，`1.6` 行高，占满可用宽度
- 底部工具栏：固定 56fp 高度，左侧章节信息（字数/保存状态），右侧 AI 操作入口
- 工具栏背景：`color_bg_secondary`，与正文区用 `color_divider` 分隔
- 键盘弹起时工具栏上移，不遮挡正文

### AI 操作面板

- 不占据编辑器主区域，以底部弹出面板（BottomSheet）或侧边抽屉形式呈现
- 面板内包含：操作类型选择（润色/续写/审查）、模式选择、发起按钮、状态指示器
- 生成中显示进度动画 + 可取消按钮
- 生成完成后面板自动收起，编辑器顶部出现"查看候选稿"入口条

### 空状态

每个列表页都定义空状态插画 + 引导文案：

- 作品库为空："还没有作品，点击下方创建一个" + 新建按钮
- 角色列表为空："尚未创建角色。你可以在写作过程中随时添加"
- 章节列表为空："点击下方开始第一章"

### 加载状态

- 页面级加载：居中 spinner（`color_accent`），不显示具体百分比
- 局部加载（卡片/列表项）：骨架屏（shimmer），宽高与目标内容一致
- AI 生成中：底部面板内显示进度动画 + "正在生成..." 文案 + 取消按钮

## 深色模式规则

- 所有页面必须支持深色模式。
- 颜色使用 Token 引用，不要写死色值。
- 深色模式下正文背景使用 `color_bg_primary_dark`，模拟深色纸张感（非纯黑）。
- 深色模式下 AI 功能区域色板同步降暗，避免对比度过高刺眼。

## 输出格式

### 组件样式检查清单

```markdown
- [ ] 颜色全部使用 Token，无硬编码色值
- [ ] 按钮最小点击区域 >= 48fp × 48fp
- [ ] 正文行高 >= 1.5 倍
- [ ] 卡片圆角统一 12fp
- [ ] 页面水平边距统一 16fp
- [ ] 所有列表页有空状态定义
- [ ] 所有异步操作有加载状态
- [ ] 深色模式下可读性正常
- [ ] AI 功能入口不喧宾夺主
- [ ] 编辑器正文区是视觉重心
```

## 禁止事项

- 禁止在 ArkUI 代码中硬编码色值（必须使用 Token 或资源引用）。
- 禁止将 AI 功能放在比正文更显眼的位置。
- 禁止编辑器内同时堆满角色、设定、审查、润色按钮。
- 禁止使用系统默认蓝色作为主色调（那是工具型 App 的视觉语言，不适合写作软件）。
- 禁止忽略空状态和加载状态。

## 与主工作流的关系

- 是否可用于 Writer：否
- 是否可用于 Polish：否
- 是否可用于 Review：是 — Review Agent 审查前端 UI 代码时应逐项对照本 Skill
- 是否可用于 Fixer：是 — 修复 UI 不一致问题时参照本 Skill
- 是否可用于大纲搭建：是 — 用于鸿蒙 App 的视觉设计阶段

## 知识库依赖

> 本 Skill 不依赖 narrative_workbench 项目知识库。

- 是否需要 knowledge_index.py 查询：否

## 内置知识声明

- 是否包含领域事实数据：否 — 本 Skill 是视觉设计方法论文档。颜色、字体、间距等规范是独立制定的设计决策，不依赖外部数据源。实际实现时需参考 HarmonyOS 官方设计指南和 ArkUI 组件 API。
