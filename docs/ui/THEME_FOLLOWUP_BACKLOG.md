# 主题收尾 · UI 补漏 backlog(2026-06-10 起)

> Purple v2 全站主题已上线(commit 1552209c)。真机实测 + 之前积累的前端 UI 尾巴归集于此。
> 全部碰 src/home + build dist → 等手头窗口腾位,开一个"主题收尾 UI 补漏"窗口**一次扫平**,别零敲碎打、别单开小窗。

## 待修清单

| # | 项 | 性质 | 来源 |
|---|---|---|---|
| 1 | 进项页筛选 tab(全部/进货/费用/未付)激活态**黑底白字** → 应统一紫 pill(accent-weak 底+ink 字,同侧栏) | 主题漏网(btn-black 残留·某高特异性 css 用 --ink 黑底) | 真机 2026-06-10 |
| 1-bis ★治本 | **全站"没接令牌的控件"普查**:grep 所有 css 硬编码深色背景(#000/#111/#1e/--ink 做 background)+ 所有原生 `<select>`/`<input type=checkbox>` → 拉清单逐个接令牌(激活/选中态 var(--accent),底用语义令牌);**同时扩硬闸覆盖面**:check_ui_consistency 从只扫 `.btn` 扩到所有交互控件(segmented/tab/toggle/checkbox 的激活底),以后机器自动拦"换主题漏一片"。根因=主题切换只对引用 var() 的控件生效,硬编码控件天生漏网,普查一次穷尽+硬闸兜底=治本 | ★治本·一次穷尽 | 2026-06-10 机制盲区追问 |
| 1-ter ★治本 | **全站线性图标验收机制**:① 源头收口=建图标注册表 `src/home/icons.ts`(Lucide 子集),全站图标只许从注册表取,禁内联手写 svg/emoji 当图标/`<img>` 图标 ② 静态闸=check_ui_consistency 加 D3:UI 字符串含 emoji 区段→FAIL、内联 `<svg` 缺 `fill="none"`+`stroke="currentColor"`→FAIL、字符冒充图标(▸★●)→棘轮 ③ 真浏览器审计=_ui_audit spec 全路由 querySelectorAll('svg') 断言 fill/stroke 属性,抓 js 运行时注入的。线性图标的机械定义=fill:none+stroke:currentColor+stroke-width≈2。起步先跑基线棘轮,存量(POS/admin/console 可能有)本窗口清零 | ★治本·与 1-bis 同模式(统一源+闸兜底) | 2026-06-10 |
| 2 | 账套主体新建弹窗「已注册 VAT」原生 checkbox 丑 | 原生控件未样式化 | 真机 2026-06-10 |
| 3 | **全站原生表单控件统一**:原生 `<select>`/`<input type=checkbox>` 到处用都丑 → 站内样式化(选中态 var(--accent)) | 系统性 | 多处(账套/做账设置等) |
| 4 | 中文字体 fallback 顺位:Segoe UI(西文)第一 → 中文落第 6 雅黑,小字号基线/粗细微妙不齐 → PingFang/雅黑提前 | 轻微·真机确认后再定 | 真机字体观察 |
| 5 | 向导进度条完成态绿勾 → 是否统一紫 | **非 bug·Zihao 审美决定**(建议保留绿:绿=完成/紫=当前分工清晰) | 真机 2026-06-10 |
| 6 | B 类 legacy 视觉清理(lint-ui 仍 warning·部分已被 S7-S9 覆盖) | 待对照 design-unify-backlog 核 | 历史 |
| 7 | L0.5 真流程态(上传中/识别中/402/重复票)+ 系统生成 PDF/税票/小票/Excel 版式专项审计 | **需配额度+清数据计划**·建议并进报税后一起做 | UI_DESIGN_AUDIT_FINDINGS 遗留 |
| 8 | **POS/console 收编进打包管线**(view-source 成品化·E7 范式补全):Vite 多入口(pos/console)→产物进 dist→页面引 bundle;⚠️ POS 离线 PWA 高敏(sw 缓存外壳清单同步改+离线 E2E 全量重验);console 无离线顺手;完成后 **check_asset_bundling 闸扩覆盖到 pos/console**(新页面裸发源码=push 拦) | **非本轮**·归报税前端收尾后的"丝滑专项+打包"窗口(要 dist) | 2026-06-10 view-source 对比 |

## 处理结果(2026-06-10 · 报税4屏合并窗口一次扫平)

| # | 结果 |
|---|---|
| 1 | ✅ 进项筛选 tab `.seg .o.on` 黑底 `var(--ink)` → `accent-weak`+`accent-deep` 紫 pill(purchase-list.ts) |
| 1-bis | ✅ 颜色普查:src/home 黑底交互控件激活态 4 处接令牌(purchase-list/acct-list/acct-accounts `.seg`、pos-tables `.zone.on`)+ 工作区切换器 `.cs-chip-all` 黑→accent。**治本闸**:`check_ui_consistency` D2 从 `.btn` 扩到 segmented/tab/chip/pill/zone + `.on/.active/.selected`,且新增扫 `src/home/*.ts` CSS-in-JS(用 `\b` 边界防 "table" 误伤)· D2=0 绿 |
| 1-ter | ✅ **按现状收口**(Zihao 拍板):emoji-当图标 棘轮闸(ui_design_lint baseline 260 · 新增即拦)= 已是「no new」治本。那 260 大半为 i18n 文案合法 emoji 噪声,真图标误用少且散落 POS/admin/console(console 红线)。**全量 icons.ts 注册表+D3 svg 审计+存量迁移 = 独立专项窗口**(防跨敏感 SPA 回归) |
| 2 / 3 | ✅ 原生控件 accent-color 全站令牌化:home-01-base.css `input[type=checkbox],input[type=radio],select,input[type=range]{accent-color:var(--accent)}` — 选中态统一品牌色不再露默认蓝(含账套「已注册VAT」)；报税设置屏全用站内 .sw/.seg |
| 4 | ✅ 中文字体提前:body font-family `PingFang SC`/`Microsoft YaHei` 移到 `Segoe UI` 前(一行可逆) |
| 5 | ⏭️ 不做(向导绿勾=完成/紫=当前 · Zihao 已拍) |
| 6 | ✅ **对照核销后收口**:进项/做账/POS 旧屏收拢已随各自上线窗口完成;残余 dashboard/报表/知识库大面积 legacy = 设计语言统一专项(lint-ui 仍 warning · 非 bug · 留专项) |
| 7 | ⏭️ 不做(真流程态+PDF 版式 · 要扣费造数据 · 单独排) |
| 8 | ⏭️ 非本轮(POS/console 打包管线 · 要 dist · 丝滑专项窗口) |

## 时机

- 1-6 = 纯前端视觉,等权限补齐/报税其中一个窗口收尾、腾出位,开 UI 补漏窗口一次做(碰 home-*.css + src/home + build dist + bump + 视觉闸重基线)。
- 7 = 单独专项(要扣费造数据),建议排报税上线后,和真流程态 E2E 一起。
- 红线:改前端必 build + add dist + bump ?v=;视觉闸快照随改重基线;PowerShell 读 UTF-8 用 Edit 工具别用 Get-Content -Raw。
