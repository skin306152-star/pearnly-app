# 06 · 前端方案(⚠️ 待评审稿,非开工许可)

> **死规则(Zihao 2026-06-04):所有 UI 必须先出设计稿 + 和 Zihao 讨论定稿,才允许实现。**
> 本文件是**待讨论的方案稿**,不是动手依据。落地前必须走一轮设计评审,定稿后才写代码。
> 主仓库前端约定:`src/home/*.ts`(TypeScript strict),build 出 minified bundle 进 `static/dist`,
> 改源码必 `npm run build` + 提交 dist,改前端必 bump `home.html ?v=` 破缓存。

## 落点(导航已留位)

- 填实 `page-sales-invoices`(销售发票)与 `page-receivables`(应收追踪)两个空壳。
- 对应 `src/home/page-placeholders.ts` 现有占位 → 换成真页面模块。

## 页面草图(待评审)

### A. 销售发票 · 开单页(POS 点单式)

```
┌───────────────────────────────────────────────┐
│ 选客户 [▼ 已存档客户 / + 新建]   单据类型 [税票▼] │
├──────────────────┬────────────────────────────┤
│  选品区(4 种入口) │  单据明细(右栏实时算)        │
│  [手输码] [扫条码] │  行1  商品A  x2   100.00     │
│  [扫QR]  [拍照]   │  行2  商品B  x1    50.00     │
│  ───────────────  │  ──────────────────────────  │
│  商品网格(菜单式) │  税前  150.00                │
│  [图][图][图]     │  VAT7%  10.50                │
│  [图][图][图]     │  合计  160.50                │
│                   │  [存草稿]   [正式开出]        │
└──────────────────┴────────────────────────────┘
```
- 4 种入口最终都落到"加一行明细"。扫码/QR 用浏览器 BarcodeDetector(降级 zxing)。
- "正式开出"才取连号(状态诚实:草稿不占号)。开出后单据转只读 + 显示号。

### B. 应收追踪页

- 账龄分组(30/60/90/90+),逾期红标;LINE/邮件催收;银行回款自动核销(复用对账)。

## 四态 UI(铁律,每个列表/异步区都要)

| 态 | 表现 |
|---|---|
| 加载 | 骨架屏 |
| 空 | 引导文案 + 主操作(如"还没有商品,去建档/导入") |
| 错误 | 明确错误 + 重试,不静默吞 |
| 有数据 | 正常 |

## i18n

- 默认 th,全文案走 `data-i18n` key,**4 语补齐(zh/en/th/ja · 等长)**。key 清单见 `docs/07-i18n-keys.md`。
- key 命名遵 `DESIGN_SYSTEM.md §15`:kebab-case · 最多 4 段 · area 前缀(本模块 `sales-` / `ar-`)· 动态内容必 `subscribeI18n` 注册。
- 开工前 `grep -r 'data-i18n="sales-' home.html` 查前缀冲突(§15.6)。

## 设计系统对照(必须遵 `CLAUDE.md/DESIGN_SYSTEM.md` · 新组件偏离要在 PR 说明)

App 主题 token(`home.css :root`),本模块直接用、不另造色值:

| 用途 | token / 值 |
|---|---|
| **主按钮** | ⚠️ 走 `static/home-38-buttons.css` · `.btn-primary` = **品牌蓝 `#2563EB`**(hover `#1D4ED8`)· 见下"色值冲突" |
| 强调/focus/拖拽态/spinner | `--accent #4299e1` · focus ring `0 0 0 2px rgba(66,153,225,0.15)` |
| 页面底/drop-zone 默认底 | `--bg #f7fafc` · 卡片 `--card #fff` · 边框 `--line #e2e8f0` |
| 文本 | `--ink #1a202c` / `--ink-2 #4a5568` / `--ink-3 #a0aec0` |
| 成功/警告/危险 | `--success #38a169` / `--warn #dd6b20` / `--danger #c53030`(+ 各 `-bg`) |
| **发票号/金额/日期/税号** | 套 `--font-mono`(`"SF Mono", Monaco, Consolas, monospace`)· 数字右对齐 tabular-nums |

规范硬约束:
- 字号走梯度(body **13px** · 次级 12px · 表头 11px · 标题 14px)· 禁 9/17/19px。
- 按钮 `.btn` `min-height: 40px` · padding `10px 18px` · 圆角 8px · 字重 600。
- 卡片 `.card`:圆角 10px · padding 20px · `margin-bottom: 16px`(禁 24/30)· `--shadow-sm`。
- 圆角:input/button 6–8px · card 10–12px · modal 12px · pill 999px。
- 图标:**Lucide 风 inline SVG** · viewBox 16/20/24 · stroke-width 1.8 · `currentColor` · round caps · **禁 emoji 当图标**。
- 动效:hover 120ms · 中交互 200–250ms · 永不 >500ms · 只动 transform/opacity。
- 断点:应用内只用 **768px / 600px** 两档。

## 复用现成组件(铁律 47/48:不许重新发明 · 详见 DESIGN_SYSTEM §11/§17)

> **Zihao 拍板(2026-06-04):单据编辑/详情一律用弹窗(modal),不用抽屉(drawer)。**

| 需求 | 复用 | 不要 |
|---|---|---|
| 确认弹窗(作废/删除) | `await window.pearnlyConfirm(msg, title)` | ❌ 原生 `confirm()`/`alert()` |
| **单据编辑/详情面板** | **`.modal`(§11·`--shadow-lg`·12px 圆角·`modalIn 200ms` 进场)·宽度按表单需要(`.modal-md` 620px 起·明细多可加宽)** | ❌ 抽屉 `.drawer`(Zihao 不要) |
| 销项单的"三 Tab"(对标 Paypers 单据/信息/明细) | `.erp-subtab` 二级切换范式(§17.2)·嵌在 modal 内 | 自造 tab |
| 表单字段 | modal body 内沿用字段样式(input 8×10 padding·6px 圆角·focus `--accent` 边) | — |
| KPI 统计卡(应收账龄/对账汇总) | `.stat-card`(4 格·`--bg` 底·8px 圆角) | — |
| 当前占位页 | `.coming-soon`(dashed 边·`cs-*` i18n key) | 改成真页面时替换 |

> modal mask `rgba(0,0,0,0.5)` · Header/Body/Footer padding `16×22 / 22 / 12×22` · Footer 底 `--bg`。
> 手机端(≤600px)modal 仍居中可滚(`.modal-mask` `overflow-y:auto`),不退化成全屏抽屉。

## ⚠️ 给 Zihao 的一处色值冲突(需你定)

`DESIGN_SYSTEM.md §2.1` 写主按钮 = `--brand #1a365d`(深蓝);但 `CLAUDE.md §30` 更新(2026-05-29 · REFACTOR-WB-C)拍板"全站 `.btn-primary` 一律品牌蓝 `#2563EB`",走中央 `static/home-38-buttons.css`。
→ **按更新的来:主按钮用 `#2563EB`(home-38-buttons.css 为准)**,DESIGN_SYSTEM 那行是旧值待同步。本模块按钮一律复用 `.btn-primary`,不写死色值。

## 客户已答锁定(2026-06-05 · 见 docs/09)

- **选品 = 菜单式图卡网格点选 + 手输码**(Q2:从商品图库点选,像点菜单)· 商品**必带图**。
  扫条码/扫 QR → **POS 下一个独立项目**,本模块 Phase 1 不做。
- **发送 = 邮件 / LINE / 打印纸 三通道全做**(开出后单据弹窗里给三个发送动作)。
- 单据编辑/详情 = **弹窗(modal)**,不用抽屉(Zihao 拍板)。

## 待评审要点(设计评审时和 Zihao 定 · UI 先讨论后做)

1. 菜单图卡网格的布局(每行几卡 · 卡片含图/名/价/加号)+ 手输码搜索条放哪。
2. 开单是独立全页,还是列表页 + "开新单"弹窗?(倾向:列表页 + 弹窗,和 modal 决定一致)
3. 三发送通道在弹窗里的呈现(打印走浏览器 print CSS · LINE/邮件走后端发送)。
4. 与现有 home 设计语言(home-01..38 token)如何统一,避免再出 admin 那种 CSS 崩。
