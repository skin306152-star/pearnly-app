# Pearnly · DESIGN_SYSTEM.md

> **来源**:从 `home.css` (v0.3.5 → v118.x)、`home.html`、`home.js` (I18N 字典 4 语言)、`login.html` 提取。
> **品牌名**:Pearnly(英文官名,登录页 `<title>` 与 i18n 字典中 `'ob-finish': '完成 · 进入 Pearnly'` 已确认)。中文内部代号:Mr.Pilot / 票据识别助手。
> **作用范围**:本文档是 Pearnly Web 端(登录页 + 应用主页)的视觉契约。新增页面、新组件必须遵循;偏离需在 PR 描述里说明。

---

## 目录
1. 双主题约定(深色 Marketing 页 vs 浅色 App 页)
2. 色板(完整 HEX + 用途)
3. 字体栈与 4 语言 fallback 链
4. 字号字重梯度
5. 间距系统
6. 圆角规范
7. 阴影规范
8. 按钮样式
9. 卡片样式
10. 抽屉样式
11. 模态弹窗样式
12. 图标规范(SVG / Lucide 风格)
13. 动效与过渡
14. 响应式断点
15. i18n key 命名约定
16. 设计系统反模式(已发现的不一致)

---

## 1. 双主题约定

Pearnly 同时存在 **两套主题**,职责清晰分离,**不可混用**:

| 主题        | 文件               | 主背景色   | 主文本色   | 适用场景                              |
| --------- | ---------------- | ------ | ------ | --------------------------------- |
| Marketing | `login.html`     | `#0a0e27`(深蓝夜空) | `#ffffff` | 落地 / 登录 / 注册 / 营销 hero            |
| App       | `home.css` + `home.html` | `#f7fafc`(浅灰) | `#1a202c` | 登录后所有功能页(OCR / 历史 / 客户 / 设置 / 后台) |

两套主题共用「品牌色」与「字体栈」,但 token 命名不同(见 §2)。

---

## 2. 色板

### 2.1 App 主题(`:root` in `home.css`)

| Token              | HEX        | 用途                                             |
| ------------------ | ---------- | ---------------------------------------------- |
| `--brand`          | `#1a365d`  | 品牌主色 · 主按钮 · sidebar active 文字 · 链接           |
| `--brand-hover`    | `#2a4e7c`  | 主按钮 hover                                      |
| `--accent`         | `#4299e1`  | 强调蓝 · focus ring · 拖拽态 · spinner 主色            |
| `--accent-soft`    | `#ebf4ff`  | 强调浅底 · sidebar active 背景 · info alert 底色      |
| `--bg`             | `#f7fafc`  | 页面背景 · 表头底 · drop-zone 默认底                    |
| `--card`           | `#ffffff`  | 卡片底 / topbar 底 / sidebar 底                     |
| `--line`           | `#e2e8f0`  | 主分隔线 · 边框                                       |
| `--line-soft`      | `#edf2f7`  | 次级分隔线 · 表格行底线                                  |
| `--ink`            | `#1a202c`  | 主文本(L1)                                       |
| `--ink-2`          | `#4a5568`  | 次文本(L2)· 表格 td · 按钮文字                         |
| `--ink-3`          | `#a0aec0`  | 弱文本(L3)· label · placeholder · 元信息            |
| `--ink-4`          | `#cbd5e0`  | 极弱(L4)· 占位 icon · disabled 边框                  |
| `--success`        | `#38a169`  | 成功                                             |
| `--success-bg`     | `#f0fff4`  | 成功底                                            |
| `--warn`           | `#dd6b20`  | 警告 · Pro 套餐标签                                  |
| `--warn-bg`        | `#fffaf0`  | 警告底                                            |
| `--danger`         | `#c53030`  | 危险 · 错误                                        |
| `--danger-bg`      | `#fff5f5`  | 危险底                                            |
| `--line-color`     | `#06c755`  | LINE 品牌色(联系图标 / LINE 按钮)                       |
| `--fb-color`       | `#1877f2`  | Facebook 品牌色                                   |

### 2.2 Marketing 主题(`:root` in `login.html`)

| Token            | HEX        | 用途                       |
| ---------------- | ---------- | ------------------------ |
| `--bg`           | `#0a0e27`  | 落地页主背景(深蓝夜空)         |
| `--primary`      | `#1e3a8a`  | 渐变深端 · 主按钮渐变起点          |
| `--primary-2`    | `#2563eb`  | 渐变浅端 · CTA 主按钮          |
| `--accent`       | `#f59e0b`  | 金色强调 · hero CTA · 标记色   |
| `--accent-2`     | `#fbbf24`  | 金色渐变浅端                   |
| `--green`        | `#22c55e`  | "在线"指示点 · success eyebrow |
| `--text`         | `#0f172a`  | 浅底卡片文字                   |
| `--text-mute`    | `#64748b`  | 浅底次文                     |
| `--text-light`   | `#ffffff`  | 深底主文                     |
| `--text-light-mute` | `rgba(255,255,255,0.65)` | 深底次文                     |
| `--border`       | `#e5e7eb`  | 浅底边框                     |
| `--border-dark`  | `rgba(255,255,255,0.08)` | 深底边框                     |
| `--error`        | `#dc2626`  | 表单错误                     |

### 2.3 表格状态色 / 徽章扩展色(高频出现但未抽 token)

> ⚠️ 这些色值在 `home.css` 里硬编码,建议下版本抽 token 统一。

| 用途                          | HEX                  |
| --------------------------- | -------------------- |
| 缓存命中徽章底 / 文字              | `#ECFDF5` / `#065F46` |
| 中置信度徽章底 / 文字 / 边框       | `#fefcbf` / `#975a16` / `#f6e05e` |
| 高置信度徽章边                    | `#9ae6b4`            |
| 离线 banner(红)                | `#DC2626`            |
| 在线 banner(绿)                | `#059669`            |
| 批量工具栏底 / 文 / 边           | `#eff6ff` / `#1e3a8a` / `#bfdbfe` |
| Plan banner · info(底/文)   | `#eff6ff` / `#1e3a8a` |
| Plan banner · success      | `#ecfdf5` / `#065f46` |
| Plan banner · warn          | `#fef3c7` / `#92400e` |
| Plan banner · danger        | `#fee2e2` / `#991b1b` |
| LINE 按钮(Plan banner 内)      | `#00B900` / hover `#009900` |
| Onboarding · 选中卡片底 / 边    | `#eff6ff` / `#2563eb` |
| Onboarding · 选项 hover 边     | `#93c5fd`            |
| Onboarding · 完成绿 dot       | `#4ade80`            |
| 国旗徽章 · 泰国红 / 蓝             | `#ed1c24` / `#1f3da5` |
| 国旗徽章 · 中国红 / 黄             | `#de2910` / `#ffde00` |
| 国旗徽章 · 日本红                  | `#bc002d`            |

### 2.4 黑/白/透明常用值

| 用途              | 值                           |
| --------------- | --------------------------- |
| 抽屉 mask         | `rgba(0,0,0,0.35)` + `backdrop-filter: blur(2px)` |
| 模态 mask         | `rgba(0,0,0,0.5)`           |
| 升级弹窗 mask       | `rgba(15,23,42,0.55)`       |
| 手机 sidebar 遮罩   | `rgba(0,0,0,0.4)`           |
| Tooltip 底        | `var(--ink)` (`#1a202c`) + 白字 |

---

## 3. 字体栈与 4 语言 fallback 链

### 3.1 主字体栈(2 套并存,**亟待统一**)

```css
/* App 端(home.css line 38)*/
font-family:
  -apple-system, BlinkMacSystemFont, "Segoe UI",
  "Noto Sans Thai",
  Roboto, "PingFang SC", "Microsoft YaHei",
  sans-serif;

/* Marketing 端(login.html line 27)*/
font-family:
  'Inter', -apple-system, 'Sarabun',
  'PingFang SC', 'Helvetica Neue',
  sans-serif;
```

### 3.2 等宽字体栈(发票号 / 金额 / 日期 / 税号)

```css
--font-mono: "SF Mono", "Monaco", Consolas, "Courier New", monospace;
```

> 凡是「不可换行 + 数字对齐」的字段(发票号 `.inv`、日期 `.date`、金额 `.amount`、税号 `.contact-value`)都套这个 token。

### 3.3 4 语言 fallback 链(推荐落地版)

下表是 **整理后的、消除两套不一致** 的统一推荐:

| 语言 | 推荐 fallback 链                                                                                                                                                                                                                            |
| -- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| zh | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Source Han Sans CN', 'Noto Sans SC', sans-serif`                                                                            |
| en | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Roboto, Arial, sans-serif`                                                                                                                                       |
| th | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Sarabun', 'Noto Sans Thai', 'Leelawadee UI', 'Tahoma', sans-serif`                                                                                                              |
| ja | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Noto Sans JP', sans-serif`                                                                                |

**落地建议**:
- 在 `<html>` 上加 `lang="zh|en|th|ja"`,然后用 `:lang(...)` 选择器分别覆盖 `body { font-family }`。
- Inter 作为统一的拉丁字体打头(数字 / 标点视觉一致),CJK / 泰文 fallback 让操作系统接管。
- **不要在主字体栈里直接列 'Sarabun'**(如 `login.html` 现状),它会让英文 / 中文用户也被拖去 Sarabun,字距偏宽。改用 `:lang(th)` 圈定。

### 3.4 字体加载策略

- 当前 **未引入任何外部 webfont**(无 Google Fonts / 自托管 woff2)。Inter 与 Sarabun 在 `font-family` 中声明但实际依赖系统已装。
- 若上线 webfont,优先 `font-display: swap` + `preload`,只对 Inter 400/600/700 三档做。

---

## 4. 字号字重梯度

### 4.1 字号(从源码统计 · 频次倒序)

| Size  | 频次  | 用途                                    |
| ----- | --- | ------------------------------------- |
| 13px  | 103 | **Body 主号** · 按钮 · 表格 td · dropdown 项 |
| 12px  | 103 | **次级 Body** · 标签 · 元信息 · 输入框 hint    |
| 11px  | 69  | 微号 · 表头 · uppercase 元信息 · badge       |
| 14px  | 46  | App 主标题 · section-title              |
| 10px  | 30  | nano · uppercase tag · soon badge      |
| 16px  | 16  | brand-workspace · modal-title         |
| 15px  | 15  | drawer-header-title · onboarding 输入   |
| 18px  | 9   | coming-soon 标题 · nav-item 主标          |
| 20px  | 4   | onboarding step 标题                    |
| 22px  | 6   | login brand-name · 强眼标题              |
| 28~42px | <5 | hero h1(login)                       |

> **规则**:**禁止**新增 9px / 17px / 19px / 21px 这些非梯度上的值。

### 4.2 字重

| 值   | 频次  | 用途                            |
| --- | --- | ----------------------------- |
| 600 | 99  | **默认强调**(标题、按钮、active 项)     |
| 500 | 81  | 中度强调(label、徽章、hover 提示)       |
| 700 | 29  | 强标题、stat-value、conf-badge    |
| 800 | 4   | hero h1 · brand-name(仅 login) |
| 400 | 3   | 极少用 · 仅段落正文                   |

> 不用 100/200/300/900。

### 4.3 字间距(letter-spacing)

| 用途             | 值                   |
| -------------- | ------------------- |
| 一般正文           | 默认(0)               |
| 大标题(brand-workspace) | `-0.3px`            |
| Hero h1        | `-1.2px`            |
| UPPERCASE 元信息  | `0.05em` ~ `0.08em` |
| Eyebrow / tag  | `0.4px` ~ `0.6px`   |

---

## 5. 间距系统

### 5.1 间距尺度(基于 4px / 实际频次驱动)

| Token(建议)        | 值     | 实测频次(gap+padding+margin) | 推荐用途                     |
| ----------------- | ----- | ----------------------- | ------------------------ |
| `--space-1`       | 2px   | 多                       | 微贴(SVG 内、点中心)            |
| `--space-2`       | 4px   | 多                       | label/value 上下           |
| `--space-3`       | 6px   | 高频                      | 元素间紧凑                    |
| `--space-4`       | 8px   | **最高频(58 次 gap)**        | **栅格基本单元**               |
| `--space-5`       | 10px  | 高频                      | 卡片内列表 row gap            |
| `--space-6`       | 12px  | 高频                      | 按钮 row、stats grid gap    |
| `--space-7`       | 14px  | 高频                      | drawer-body 内 section 间  |
| `--space-8`       | 16px  | 高频                      | 卡片 padding 横、margin-bottom |
| `--space-9`       | 20px  | 中频                      | 卡片 padding · drawer 横    |
| `--space-10`      | 24px  | 低频                      | 大间距 / hero               |
| `--space-12`      | 28px ~ 32px | 极少                      | hero / 落地页              |

### 5.2 高频 padding 组合

| 组合           | 用途                                    |
| ------------ | ------------------------------------- |
| `10px 12px`  | dropdown item · 输入框默认                 |
| `10px 14px`  | alert · stat-card                     |
| `8px 12px`   | nav-item · file-item                  |
| `6px 12px`   | dropdown 按钮                            |
| `12px 14px`  | drop-zone · drawer-field input        |
| `2px 8px` / `2px 6px` | tag / badge / chip(超扁)         |
| `10px 18px`  | `.btn` 主按钮(配合 `min-height: 40px`)    |
| `20px`       | `.card` padding                        |
| `16px 20px`  | drawer-header / modal-header          |

### 5.3 强制规则

- 所有按钮 `min-height: 40px`(`home.css` line 423,v113.1 手机点击区域不误触)。
- 卡片 `margin-bottom: 16px`,**禁止**写 24px/30px 拉开。
- `.section-head` 与正文之间固定 `margin-bottom: 14px`。

---

## 6. 圆角规范

| Token(建议)         | 值     | 频次 | 用途                                |
| ------------------ | ----- | -- | --------------------------------- |
| `--radius-xs`      | 3px   | 9  | tag · badge · mini-bar 内核         |
| `--radius-sm`      | 4px   | 23 | 文件 retry-btn · 微 chip · 提示气泡       |
| `--radius`         | 6px   | 57 | **默认输入 / 输入框 / 小按钮 / chip / alert** |
| `--radius-md`      | 7px   | 5  | sidebar-toggle 等内嵌按钮              |
| `--radius-lg`      | 8px   | **61(最高)** | **主按钮 / dropdown menu / 表格容器**    |
| `--radius-xl`      | 10px  | 32 | **卡片(`.card`)** · file-list-body |
| `--radius-2xl`     | 12px  | 19 | modal · coming-soon · marketing CTA |
| `--radius-3xl`     | 14px  | 7  | login mcard / 大卡片                |
| 圆点 / 全圆           | 50%   | 17 | 头像 · onboarding step dot · pulse  |
| 胶囊                 | 999px / 99px | 16 | conf-badge · engine-badge · plan-banner-btn |

### 规则
- **input / button / chip → 6~8px**
- **card → 10~12px**
- **modal → 12px**
- **avatar / dot / pulse → 50%**
- **pill(状态徽章)→ 999px**
- 禁止使用 5px / 11px / 13px 等非梯度值。

---

## 7. 阴影规范

### 7.1 已有 token

```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.05);   /* 卡片 */
--shadow:    0 4px 20px rgba(0,0,0,0.06);  /* dropdown · tooltip */
--shadow-lg: 0 10px 40px rgba(0,0,0,0.12); /* modal · toast */
```

### 7.2 高频专用阴影(建议升 token)

| 场景             | 值                                       | 建议 token              |
| -------------- | --------------------------------------- | --------------------- |
| Drawer(右抽屉)    | `-8px 0 32px rgba(0,0,0,0.12)`          | `--shadow-drawer`     |
| Hero CTA(login) | `0 4px 14px rgba(37,99,235,0.35)` (hover `0 6px 20px rgba(37,99,235,0.5)`) | `--shadow-cta`        |
| Hero CTA · 金色  | `0 8px 24px rgba(245,158,11,0.4)`       | `--shadow-cta-accent` |
| Focus ring · 蓝 | `0 0 0 3px rgba(37,99,235,0.12)`        | `--shadow-focus`      |
| Focus ring · 输入框 | `0 0 0 2px rgba(66,153,225,0.15)`       | `--shadow-focus-soft` |
| 浮起卡片 hover     | `0 8px 24px rgba(0,0,0,0.08)`           | `--shadow-hover`      |
| Brand logo 反白底 | `0 4px 20px rgba(255,255,255,0.15)`     | (login 专用)            |

### 7.3 规则
- **不要在新增组件里写第三套 RGBA 阴影**,优先用现有 `--shadow-sm/--shadow/--shadow-lg`。
- Focus 状态统一用 `0 0 0 3px rgba(37,99,235,0.12)`(蓝 12% 外发光),输入框可降到 2px / 0.15。

---

## 8. 按钮样式

### 8.1 基础 `.btn`(App 内通用)

```css
.btn {
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 120ms;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: inherit;
  min-height: 40px;     /* 强约束 · 移动端不误触 */
}
.btn svg { width: 14px; height: 14px; }
```

### 8.2 变体

| 变体              | 默认                                                | hover                                       | disabled                            |
| --------------- | ------------------------------------------------- | ------------------------------------------- | ----------------------------------- |
| `.btn-primary`  | bg `--brand` / 白字                                  | bg `--brand-hover`                          | bg `--ink-3` · cursor not-allowed |
| `.btn-secondary`| bg `#fff` / `--ink-2` / 1px `--line` 边             | bg `--bg` / 边 `--ink-4`                     | opacity 0.5                         |
| `.btn-success`  | bg `--success` / 白字                                | bg `#2f855a`                                | bg `--ink-3`                        |
| `.btn-locked`   | bg `#fff` / `--ink-3` / 1px **dashed** `--line` 边 | bg `--bg`                                   | -                                   |
| `.dd-btn`       | 32px 高 · 6/10 padding · 1px `--line` 边 · 7px 圆角 | bg `--bg` / 边 `--ink-4`                     | -                                   |
| `.logout-btn`   | 同 `.dd-btn` 但内嵌 SVG 14px                          | 同上                                          | -                                   |

### 8.3 Marketing 专用按钮

| 类                       | 特征                                                                     |
| ----------------------- | ---------------------------------------------------------------------- |
| `.hero-cta-primary`     | linear-gradient `--accent → --accent-2` · 14px 28px · 12px 圆角 · 大金色阴影 |
| `.hero-cta-secondary`   | 半透白底 6% · 1px 14% 白边                                                  |
| `.topbar-btn-primary`   | linear-gradient `--primary-2 → --primary` · 蓝渐变 · 蓝阴影                  |
| `.topbar-btn-ghost`     | 透明底 + 白字 65% · 1px 8% 白边                                              |
| `.ob-btn-next`          | linear-gradient `#2563eb → #1e3a8a` · hover 上移 1px · 蓝阴影              |

### 8.4 Lock / Plus 标签(嵌按钮内的角标)

```css
.btn-lock-tag {
  font-size: 10px;
  background: var(--accent-soft);
  color: var(--brand);
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: 4px;
  font-weight: 500;
}
```

---

## 9. 卡片样式

### 9.1 主卡片 `.card`

```css
.card {
  background: var(--card);   /* #fff */
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid var(--line);
}
```

### 9.2 卡片内组件三件套

```css
.section-head     { margin-bottom: 14px; }
.section-title    { font-size: 14px; font-weight: 600; color: var(--ink);   margin-bottom: 3px; }
.section-sub      { font-size: 12px; color: var(--ink-3); }
```

### 9.3 信息卡片变体

| 类                | 用途                                                    |
| ---------------- | ----------------------------------------------------- |
| `.stat-card`     | 4 格统计 · `--bg` 底 / 8px 圆角 / 12-14 padding             |
| `.info-chip`     | 顶部状态条单元 · `#fff` + 1px `--line` / 6px 圆角 / 5×10 padding |
| `.coming-soon`   | 占位页 · `--card` + **dashed** `--line` 边 / 12px 圆角 / 60×30 padding · 中央居 |
| `.contact-item`  | 联系方式卡片 · `--bg` 底 / 6px 圆角 / 10×12                    |
| `.mcard` (login) | 半透白 3% / 12px 圆角 / 1px 8% 白边 / hover 浮起 2px           |
| `.ob-option`     | 选项卡片 · `#f8fafc` 底 / 1.5px `#e2e8f0` 边 / 10px 圆角 · 选中蓝边 + 12% 蓝外发光 |

### 9.4 落地态 / hover 规则

- 卡片 hover **不变背景**(避免视觉抖动),只在「可点」语义下浮 `translateY(-2px)` + 加一档阴影。
- 选中态:用 1.5~2px 边框色变化(`--accent` / `#2563eb`),**禁止** 加粗 border-width 改变盒模型尺寸。

---

## 10. 抽屉样式

### 10.1 容器

```css
.drawer {
  position: fixed; top: 0; right: 0; height: 100vh;
  width: 480px; max-width: 92vw;
  background: #fff;
  box-shadow: -8px 0 32px rgba(0,0,0,0.12);
  z-index: 999;
  transform: translateX(100%);
  transition: transform 250ms cubic-bezier(.22,.61,.36,1);
  display: flex; flex-direction: column;
}
.drawer.show { transform: translateX(0); }

.drawer-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(2px);
  z-index: 998;
  opacity: 0;
  transition: opacity 200ms;
}
```

### 10.2 三段式结构

| 区        | 类                  | 关键样式                                                                                  |
| -------- | ------------------ | ------------------------------------------------------------------------------------- |
| Header   | `.drawer-header`   | 16×20 padding · 底 `--bg` · 底分隔 1px `--line`                                            |
| Body     | `.drawer-body`     | flex:1 · overflow-y:auto · padding `14px 20px 80px`(底部 80 留给悬浮 save bar)               |
| Footer   | `.drawer-history-save-bar` | 浮于底部                                                                                  |

### 10.3 字段

```css
.drawer-field input,
.drawer-field textarea {
  width: 100%;
  padding: 8px 10px;
  font-size: 13px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  font-family: inherit;
  outline: none;
  transition: all 120ms;
}
.drawer-field input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(66,153,225,0.15);
}
```

- 字段 label 12px `--ink-2` 500 字重
- 已编辑标记 `.drawer-field-edited-dot`:6px 圆点 · `--accent` · 显示在 label 旁
- 只读态:bg `--bg` + cursor not-allowed

### 10.4 抽屉宽度断点

| 屏幕         | 宽度                |
| ---------- | ----------------- |
| 桌面 ≥ 769px | 480px(固定)         |
| 平板 / 手机    | `max-width: 92vw` |

---

## 11. 模态弹窗样式

```css
.modal-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 30px 20px;
  overflow-y: auto;
}
.modal {
  background: #fff;
  border-radius: 12px;        /* 注意:比卡片大 2px */
  box-shadow: var(--shadow-lg);
  width: 100%;
  overflow: hidden;
  animation: modalIn 200ms ease;
}
.modal-md { max-width: 620px; }
```

- Header / Body / Footer:`16×22` / `22` / `12×22` padding
- Footer 底色 `--bg`(浅灰区分主区)
- 入场动画:`scale(0.96) → scale(1)` + opacity

### 升级弹窗(`.upg-overlay`)
- mask 用更深的 `rgba(15,23,42,0.55)`,因为 z-index 9999、视觉上要"盖住一切"
- 内嵌套餐对比表(见 §13 高频组件)

---

## 12. 图标规范

### 12.1 来源 · 风格
- **Lucide 风格**(stroke-based,`fill="none"` + `stroke="currentColor"`),全部 inline SVG,**不引入图标库**。
- 颜色用 `currentColor`,跟随父级 `color` 自动着色。

### 12.2 标准 viewBox

| viewBox        | 频次 | 用途                            |
| -------------- | -- | ----------------------------- |
| `0 0 16 16`    | 45 | **默认 UI 图标**(按钮 / 字段 / 列表)    |
| `0 0 20 20`    | 39 | 中等图标(close / dropdown caret) |
| `0 0 24 24`    | 25 | 大图标(navigation 主项 · 标题)      |
| `0 0 48 48`    | 18 | 占位页 / coming-soon / 装饰         |
| `0 0 14 14` / `0 0 32 32` | 极少 | 兼容个别历史尺寸                      |

> 新增图标 **优先使用 16 / 20 / 24 三档之一**,禁止 18 / 22 这种非梯度值。

### 12.3 标准 stroke-width

| stroke-width | 频次 | 用途                              |
| ------------ | -- | ------------------------------- |
| `1.8`        | 55 | **默认**(纤细但清晰)                  |
| `1.6`        | 32 | 轻量 16px UI 图标                   |
| `1.5`        | 17 | 大装饰图标(48px)                     |
| `2`          | 13 | 强调状态图标(success check / banner) |
| `2.2`        | 5  | 极特殊 · 不推荐新增                     |

### 12.4 渲染尺寸(由父类 `svg` 选择器控制)

| 父容器                   | width × height |
| --------------------- | -------------- |
| `.btn svg`            | 14 × 14        |
| `.alert svg`          | 16 × 16        |
| `.modal-close svg`    | 14~16 px       |
| `.nav-item .nav-icon` | 18 × 18        |
| `.sidebar-toggle svg` | 18 × 18        |
| `.topbar-hamburger svg` | 20 × 20      |
| `.dd-btn svg.caret`   | 11 × 11        |
| `.coming-soon svg.cs-icon` | 48 × 48   |

### 12.5 用法约束

```html
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor"
     stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <!-- path -->
</svg>
```

- `stroke-linecap` 与 `stroke-linejoin` 一律 `round`。
- **不要给 SVG 写硬编码颜色**,全部 `currentColor`。
- 装饰性图标加 `aria-hidden="true"`,语义图标加 `<title>`。

---

## 13. 动效与过渡

| 场景                  | 时长 + 曲线                                  |
| ------------------- | ---------------------------------------- |
| **默认 hover / focus** | `120ms`(无 timing-function = linear)     |
| 通用 ui 变化            | `0.15s` / `.15s`(home.css 21+8 次最高频)    |
| 输入框边框               | `0.15s ease`                             |
| Sidebar 折叠          | `width 180ms ease`                       |
| 抽屉滑入 / 滑出           | `transform 250ms cubic-bezier(.22,.61,.36,1)` |
| Modal 缩放进场          | `200ms ease` (`scale 0.96 → 1`)         |
| Toast 进场            | `200ms ease`(translateY 10 → 0)         |
| Page 切换             | `200ms ease`(opacity + translateY 4)    |
| Onboarding 卡片 hover | `0.15s`                                  |
| Hero CTA 悬浮         | `0.2s` (translateY -2)                   |
| Plan banner 切换      | `transition: left 180ms ease`            |
| Sticky CTA 滑入       | `0.45s cubic-bezier(0.4, 0, 0.2, 1)` 主, `0.35s ease 0.05s` opacity |

**规则**:
- 微交互(120-150ms)≤ 中交互(200-250ms) ≤ 进场动画(<450ms)
- 永远不要 `> 500ms`(感知会卡顿)。
- 用 `transform` / `opacity`,**避免** `top` / `left` / `width` 触发布局抖动(Sticky CTA 例外因为 max-width 是收纳动画必需)。

---

## 14. 响应式断点

源码扫到的真实断点(频次倒序):

| 断点         | 含义              | 主要触发                                    |
| ---------- | --------------- | --------------------------------------- |
| `≤ 980px`  | 平板宽屏            | login 左侧 padding 收窄                     |
| `≤ 768px`  | **平板 / 切换主断点**  | sidebar 隐藏 · table 横滚 · plan-banner 全宽 |
| `≤ 760px`  | stats 4→2 列     | (建议未来归并到 768)                         |
| `≤ 720px`  | login 顶栏按钮缩    |                                         |
| `≤ 600px`  | **手机主断点**       | brand-name 缩小 · stats 2 列 · onboarding 单列 |
| `≤ 500px`  | 联系方式 grid 改单列   |                                         |
| `≤ 460px`  | login 极窄屏       | 顶栏按钮再缩                                  |
| `≤ 380px`  | login 超极窄屏      | 字号再降 1px                                |

**规范**:
- 应用内组件统一只用 **768px / 600px** 两档,其它仅 marketing 落地页用。
- 移动端 sidebar 用 `transform: translateX(-100%)` 抽屉式;**不要**用 `display: none`(失去动画)。

---

## 15. i18n key 命名约定

### 15.1 字典结构

`home.js` 中:
```js
const I18N = {
  zh: { 'lang-name': '中文', /* 14000+ keys */ },
  en: { 'lang-name': 'English', ... },
  th: { 'lang-name': 'ไทย',     ... },
  ja: { 'lang-name': '日本語',  ... },
};
```

**4 个版本必须等长** —— 当前已达约 451 个独立 key(home.html 中 data-i18n 标注计数)。

### 15.2 key 模式 · 总规则

```
<area>-<element>-<modifier?>
```

- 全 **小写 + kebab-case**
- 段数:**最多 4 段**(超过则压缩 area)
- **不允许** `_`、空格、大写、CJK 字符
- **不允许** 在 key 里编进序号(用 `-1` `-2` 等仅限 onboarding 选项编号)

### 15.3 已固化的 area 前缀

| 前缀          | 范围                  | 例                                          |
| ----------- | ------------------- | ------------------------------------------ |
| `lang-`     | 语言系统(`lang-name`)   | `lang-name`、`lang-switching-text`         |
| `brand-`    | 品牌字段                | `brand-sub`、`brand-workspace-fallback`    |
| `nav-`      | sidebar 导航          | `nav-dashboard`、`nav-group-core`          |
| `nav-group-`| sidebar 分组标签         | `nav-group-data`、`nav-group-system`       |
| `btn-`      | 通用按钮文本              | `btn-save`、`btn-cancel`、`btn-export`     |
| `badge-`    | 通用角标                | `badge-soon`、`badge-admin`               |
| `confirm-`  | 通用确认弹窗              | `confirm-ok`、`confirm-cancel`             |
| `col-`      | 表格表头                | `col-no`、`col-filename`、`col-total`      |
| `ocr-`      | OCR 中心页             | `ocr-title`、`ocr-sub`                     |
| `upload-`   | 上传组件                | `upload-title`                             |
| `drop-`     | drop-zone           | `drop-text`、`drop-hint`                   |
| `results-`  | OCR 结果区             | `results-title`、`results-sub`             |
| `history-`  | 单据记录页              | `history-client-all`                       |
| `client(s)-`| 客户管理页(plural=列表)   | `clients-title`、`client-field-name`      |
| `bank-`     | 银行对账页              | `bank-stat-matched`                        |
| `auto-`     | 自动化页               | `auto-title`、`auto-erp-add`              |
| `set-` / `settings-` | 设置页(混用,**应统一为 `set-`**) | `set-tab-archive`                          |
| `pref-`     | 设置 · 首选项 sub-tab   | `pref-toggle-...`                          |
| `cost-`     | 后台 · 成本追踪          | `cost-today`、`cost-th-month`              |
| `admin-cost-` / `admin-users-` | 后台页标题/副 | `admin-cost-title`、`admin-users-sub`     |
| `adm-`      | 后台共享组件 · ⚠️ 与上面重复 | `adm-tab-employees`、`adm-refresh`        |
| `billing-`  | Google AI Studio 余额追踪 | `billing-title`、`billing-google-link`    |
| `ob-`       | 登录后 onboarding 向导   | `ob-eyebrow`、`ob-s1-title`、`ob-fb-done` |
| `archive-`  | 归档命名编辑器            | `archive-token-title`                       |
| `ep-`       | endpoint(自动化对接)    | `ep-...`                                    |
| `erp-` / `linebot-` / `bank-` / `email-` / `folder-` | 自动化各 pillar | `erp-add`                                   |
| `country-`  | 国家选项                | `country-th`                               |
| `role-` / `vol-` / `team-` | onboarding 字典 | `role-owner`、`vol-1-tip`                  |
| `camera-`   | 拍照引导                | `camera-tip-light`                         |
| `cs-`       | coming-soon 占位页    | `cs-title`、`cs-desc`                      |
| `tag-`      | tag 文本(plus / pro)| `tag-plus`、`tag-pro`                      |

### 15.4 element 后缀

| 后缀                  | 用途                |
| ------------------- | ----------------- |
| `-title`            | 区域大标题             |
| `-sub`              | 副标题 / 描述         |
| `-eyebrow`          | 眉标(小号 uppercase) |
| `-tip` / `-hint`    | 提示文 · placeholder |
| `-label`            | 表单字段名             |
| `-ph`               | placeholder 文本(`client-field-name-ph`) |
| `-field-<name>`     | 字段 label          |
| `-modal-<action>`   | 弹窗(`-modal-new`、`-modal-edit`) |
| `-msg-<event>`      | 操作反馈(`-msg-created`、`-msg-save-fail`) |
| `-fb-<scene>`       | onboarding 反馈 toast(`-fb-role`、`-fb-done`) |
| `-empty` / `-empty-hint` | 空态文案           |
| `-loading`          | 加载态                |
| `-th-<key>`         | 表头(`cost-th-month`) |
| `-stat-<key>`       | 统计卡(`bank-stat-matched`) |
| `-filter-<value>`   | 筛选项(`bank-filter-all`) |
| `-cancel` / `-save` / `-delete` | 弹窗动作          |

### 15.5 反例(不要这么写)

```text
# 不要
SaveBtn                  ← 大写驼峰
btn_save                 ← 下划线
btn-保存                  ← CJK
btn.save                 ← 点号
client-field-客户名称   ← CJK 嵌入
nav-1                   ← 无意义序号
```

### 15.6 落地建议

1. **统一 `set-` 与 `settings-`、`adm-` 与 `admin-`** —— 已发现混用,新 key 一律用更短形式(`set-`、`adm-`)。旧 key 渐进迁移。
2. **value 中的占位符**用 `{name}` 风格(已在 `client-delete-confirm` 中使用),**不要**混用 `%s` 或 `${name}`。
3. **保留键** 全 4 语言必须存在:`lang-name`、`brand-sub`、`btn-logout`、`btn-save`、`btn-cancel`、`confirm-ok`、`confirm-cancel`、`badge-soon`、`badge-admin` —— 这些是其它模块兜底引用的"基底键"。
4. **新增模块前 检查 area 前缀冲突**:用 `grep -r "data-i18n=\"<area>-" home.html` 扫一遍,撞了就换。

---

## 16. 设计系统反模式(已发现的不一致 / 待清)

下面是从源码里扫到的 **已经存在但不规范** 的点,新代码不要复制,**也欢迎安排专门 PR 修复**:

| #  | 问题                                                          | 位置                      | 建议修复                            |
| -- | ----------------------------------------------------------- | ----------------------- | ------------------------------- |
| 1  | App 主字体栈写了 `"Noto Sans Thai"` 给所有用户,英 / 中用户也会被拖           | `home.css` line 38      | 改用 `:lang(th)` 圈定               |
| 2  | Marketing 字体栈直接写 `'Sarabun'`                                | `login.html` line 27    | 同上                              |
| 3  | mono 字体栈两套并存:`var(--font-mono)` vs `'SF Mono', Menlo, ...`(home.html / home.css) | 多处                      | 全部走 `--font-mono` token        |
| 4  | 设置页前缀 `set-` 与 `settings-` 混用                                | i18n keys              | 统一 `set-`                      |
| 5  | 后台前缀 `adm-` 与 `admin-` 混用                                    | i18n keys              | 统一 `adm-`                      |
| 6  | 颜色硬编码 `#ECFDF5 / #fefcbf / #DC2626 / #00B900` 等             | home.css 多处             | 抽 `--success-bg-2 / --warn-bg-2 / --line-green` 等 token |
| 7  | 圆角混用 5px / 11px / 13px(非梯度)                                 | 个别 history / cost 区     | 改 4 / 12px                     |
| 8  | 字号偶现 `12.5px`、`9px`                                          | plan-row / log-tag      | 移到 12 / 10                     |
| 9  | 阴影第三套 RGBA 没抽 token(drawer / hero / focus)                  | 多处                      | 见 §7.2 升 5 个新 token            |
| 10 | 部分按钮 `transition: all 0.15s` 与 `120ms` 并存                    | home.css                | 统一 120ms 微交互 + 0.15s 通用       |
| 11 | `data-i18n-placeholder=` 与 `data-i18n=` 两套属性 · 已默契但需要在 README 强调约定 | home.html               | 文档化约定即可                         |

---

> **最后**:这份文档对应当前主仓的 v109+ ~ v118+。每次大版本(v120 / v200)发布前,跑一次:
> ```bash
> grep -E "padding:|gap:|border-radius:|font-size:" home.css | sort | uniq -c | sort -rn | head -50
> ```
> 校对反模式表是否减少。设计系统的健康度 = **token 命中率** + **反模式条数(越少越好)**。

---

## 17. v118.27.x 新组件 · ERP 适配器主线引入(2026-05-10)

> **来源**:v118.27.0 / 27.0.1 / 27.4 三版引入的全局可复用组件。
> **铁律 47-48**:见 STATE_PEARNLY.md · 跨适配器必须复用,不许重新发明。

### 17.1 全局确认弹窗 · `pearnlyConfirm(msg, title?)`(铁律 47)

**用途**:替代浏览器原生 `confirm()` · 4 语支持 · 与品牌色 / 模态弹窗规范统一。

**API**:
```js
const ok = await window.pearnlyConfirm('确定删除?', '删除映射');
if (ok) doDelete();
```

**返回**:`Promise<boolean>` · 用户点确定 → `true` · 取消或关闭 → `false`

**实现要求**:
- 复用 §11 模态弹窗样式(`.modal` + `.modal-md`)· mask `rgba(0,0,0,0.5)`
- 标题默认走 i18n key `confirm-default-title`("请确认")· 可传 `title` 参数覆盖
- 两个按钮:`confirm-cancel`(.btn-ghost)· `confirm-ok`(.btn-primary)· 4 语词条已固化
- 入场动画用 §11 的 `modalIn 200ms` · 不要换

**反模式**:任何调用 `confirm()` / `alert()` 原生 API 的代码都必须重构。本窗口已发现 v118.27.0 的 1 处违反并修(见反模式表 #12)。

### 17.2 二级 sub-tab · `.erp-subtab`

**用途**:在主 tab 内部的二级横向切换 · 当前用于「自动化 → ERP 对接」内部分:
- 「连接 & 推送日志」 · `data-erp-subtab="connect"`
- 「字段映射」 · `data-erp-subtab="mappings"`

**结构**:
```html
<div class="erp-subtabs">
  <button class="erp-subtab active" data-erp-subtab="connect">连接 & 推送日志</button>
  <button class="erp-subtab" data-erp-subtab="mappings">字段映射</button>
</div>
<div class="erp-subpanel active" data-erp-subpanel="connect">...</div>
<div class="erp-subpanel" data-erp-subpanel="mappings">...</div>
```

**视觉**:
- 高度 36px · padding `8px 16px` · 字号 13px / 500 字重
- 默认色 `--ink-3` · active 色 `--brand` + 底部 2px `--brand` 横线
- hover 色 `--ink-2`
- 切换 transition 120ms

**断点**:`≤ 600px` 时横滚(`overflow-x: auto`)· 不换行

### 17.3 ERP 连接卡片 · `.erp-connect-card`(铁律 48)

**用途**:统一展示每家 ERP 的连接状态 · 当前 Xero 用 · 后续 FlowAccount / PEAK / QuickBooks / Express 必须复用。

**结构**:
```html
<div class="erp-connect-cards">  <!-- grid 容器 · 每行 ≥1 张 · 自适应 -->
  <div class="erp-connect-card erp-connect-xero">
    <div class="erp-cc-head">
      <div class="erp-cc-title">Xero</div>
      <span class="erp-cc-badge green">已连接 Xero</span>
    </div>
    <div class="erp-cc-body">
      <!-- organisation 列表 / 连接按钮 / 断开按钮 -->
    </div>
  </div>
</div>
```

**视觉**:
- 容器:CSS Grid · `repeat(auto-fit, minmax(280px, 1fr))` · gap 12px
- 卡片:背景 `#fff` · border `1px var(--line)` · 圆角 10px · padding 16px
- Title:16px / 600 字重 · 色 `--ink`
- Badge:padding `3px 10px` · 圆角 12px · 字号 12px / 500
  - `green`:底 `#dcfce7` · 文 `#166534`(已连接)
  - `gray`:底 `#f1f5f9` · 文 `--ink-3`(未连接 / 未配置)
- Body:font-size 13px · 色 `--ink-2` · 行高 1.6
- 内嵌 organisation radio 行:padding `6px 8px` · 圆角 6px · hover 底 `#f8fafc`
- Actions 区:`border-top 1px #f1f5f9` + `padding-top 10px` 分隔操作按钮

**变体类**(每家 ERP 1 个):
- `.erp-connect-xero`(已用)
- `.erp-connect-flowaccount`(v27.2 加)
- `.erp-connect-peak`(v27.3 加)
- `.erp-connect-quickbooks`(v27.4.x 加)
- 等等 · 默认共享基础样式 · 变体类只在需要品牌色徽章时差异化

### 17.4 i18n key 命名约定补充

承接 §15.3 area 前缀表 · 新增:

| 前缀 | 范围 | 例 |
|---|---|---|
| `confirm-` | 全局确认弹窗 | `confirm-default-title` `confirm-ok` `confirm-cancel` |
| `mrerp-` | MR.ERP 适配器 | `mrerp-btn` `mrerp-toast-ok` `mrerp-err-no_client_mapping` |
| `xero-` | Xero 适配器 | `xero-card-title` `xero-connect-btn` `xero-err-contact_not_found` |
| `erp-map-` | ERP 字段映射页 | `erp-map-tab-clients` `erp-map-add` |

新增 ERP 适配器(FlowAccount / PEAK / QuickBooks / Express)前缀:`flowaccount-` / `peak-` / `quickbooks-` / `express-` · 严禁简写为 `flow-` / `qb-` / 等。

### 17.5 反模式更新

| #  | 问题 | 位置 | 建议修复 |
|----|------|------|----------|
| 12 | **原生 `confirm()` 用法** · 与 4 语 i18n 不兼容 / 视觉与品牌脱节 | v118.27.0.1 已发现 1 处 · 已修 | 全部用 `pearnlyConfirm()` · 检查命令:`grep -rn "confirm(" static/home.js` |
| 13 | ERP 卡片视觉重复定义 | 后续 FlowAccount / PEAK 适配器若复制 .erp-connect-card 样式重写 | 必须复用 `.erp-connect-card` 基类 + 加 `.erp-connect-<name>` 变体类 |