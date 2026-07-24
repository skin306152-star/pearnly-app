# Pearnly 前端全量清单(FRONTEND-INVENTORY)

> 唯一权威地图 · 合并 4 路独立勘察(ROUTES / SCREENS-SHELLS / ENTRY-AUX / COMPONENTS)交叉核对而成。
> 目的:让任何窗口再也不会说「哎呀漏了 X」。证据路径内联。生成日期 2026-07-24。
> 核对方法见文末「勘察方法与局限」。数字为工程量级(class-selector 家族为代理),非逐像素精确。

---

## 0. 顶线总量(硬数字,不是感觉)

| 维度 | 数量 | 说明 |
|---|---:|---|
| **前端 App / SPA** | **8** | 7 生产(home / pos / ai / dms / console / admin / landing)+ 1 实验(pos-next,**未接后端路由**);另有 1 个原生小助手(companion,无 web 面) |
| **用户可达屏幕(生产)** | **93** | home 44 · pos 10 · ai 19 · dms 5 · console 3 · admin 10 · landing 2 |
| ├ 实验屏幕(pos-next) | +6 | 仅 `/static/_posnext/index.html` 直达 |
| └ 占位/隐藏页(不可达或空壳) | +3 | home 的 `cloud`(空)/ `test-center` / `automation`(display:none) |
| **入口 / 辅助面(entry-aux)** | **≈32** | 登录/OAuth/法务/邮件/PDF打印/SW/重定向/LINE卡/小助手/静态挂载/错误处理 |
| **组件类型** | **37** | 见组件矩阵。设计系统「建成」6 个、「桩」5 个、「零实现」26 个 |
| **设计系统组件真实采用率** | **0%** | `.pu-*` 组件类在**全部生产标记里出现 0 次**(只被当 token 用) |

**一句话结论**:表面上「6 站接入 pearnly-ui.css」,但接入的只是 **token**(`var(--pu-*)`/`var(--accent)`);组件层(`.pu-btn`/`.pu-modal`/…)**定义了但零采用**,37 类组件在实操中**站站自写**。这就是设计系统剩余工作的真身。

---

## 1. 按 App 分:每个 App 的屏幕 + 入口 + 组件 + 设计系统状态

### 1.1 home(会计/商户主 SPA · 最大)
- **壳**:`home.html`(根)→ `static/dist/home.html`;`routes/pages_routes.py`(`/home`,`_NO_CACHE`)。前端版本锚点从 home.html 读(`app.py:485`)。
- **设计系统**:链 `static/pearnly-ui.css` ✔(消费 token);组件全 bespoke(`static/home-*.css` 56 个文件)。
- **路由源**:`src/home/route-table.ts`(`VALID_ROUTES` 45 项 + `ROUTE_LOADERS`);侧栏 `src/home/app-shell-sidebar-html.ts`;`page-*` 段在 `home.html`。
- **44 个可达屏幕**(hash-driven SPA 路由,非后端路由):

| 分组 | 屏幕(route id) |
|---|---|
| 总览/记录 | dashboard(首页/订阅)· history(识别记录)· push-logs(推送日志)· exceptions(异常栏)· reconcile(对账中心) |
| 录入/集成 | dms-intake(录入工作台)· integrations(集成)· templates(推送模板)· api-keys(API密钥)· knowledge(客户知识,flag-gated) |
| 客户/公司 | clients(客户管理)· company(公司资料)· settings(设置,内含 general/system/archive/rules/notifications 5 面板) |
| 采购/进项 | purchase · purchase-suppliers · purchase-settings · purchase-form · purchase-detail · purchase-export · purchase-capture |
| 销售/商品 | sales-invoices(发票工作台)· sales-products · expense-data · sales-account(账套/开票资料) |
| 记账 | vouchers(自动凭证)· acct-review(逐笔审)· acct-accounts(科目表)· acct-settings · acct-bank(银行对账)· acct-manual(手工凭证)· acct-books(出账本/报税包) |
| 报税 | tax-center · tax-pp30(PP30复核)· tax-pnd(PND复核)· tax-settings |
| POS(在 home 内) | inventory(库存)· pos-onboarding(开通收银台)· sales-report · pos-sales-log · pos-audit · pos-cashiers · pos-tables · pos-payment · pos-sheets |

- **占位/隐藏(不计入 44)**:`cloud`(在 VALID_ROUTES:30,**但无 loader → 可路由但渲染空 `page-cloud`**)· `test-center`(不在 VALID_ROUTES,空段)· `automation`(`home.html:87` display:none,历史 email-ingest 页)。
- **入口/aux 归属 home**:`/liff/purchase/{doc_id}` → 302 进 `/home?liff=purchase`(LINE webview);报表导出 modal(`src/home/report-templates.ts`,4 语,复用 4 处);销售热敏打印(`src/home/sales-common.ts` window.print)。
- **组件重灾区**:card/panel ~177 · badge/chip ~155 · button 133 · empty 82 · drawer 82 · stat/KPI 65 · tabs 63 · file-upload 38。

### 1.2 pos(收银台 SPA)
- **壳**:`static/pos/pos.html` → `static/dist/pos.html`;`/cashier` + `/cashier/{rest}`(`_CASHIER_HEADERS` 严格 CSP);PWA `cashier-sw.js`(scope /cashier)+ 遗留 `pos-sw.js`(scope /pos)。
- **入口**:`/pos`(老板后台登录 `pos-login.html`,bespoke)+ `/pos/{rest}` 兜底。
- **设计系统**:链 pearnly-ui.css ✔;`pos.css`/`pos-restaurant.css` bespoke。
- **10 个屏幕**(`static/pos/pos.html` `#view-*`):bind(设备绑定 :21)· login(收银登录 :74)· main(收银/卖 :132)· hold(挂单 :860)· refund(退货 :902)· shift(开/关班 :1012)· rtables(餐桌 floor :1035)· rorder(餐桌点单 :1084)· rkitchen(KDS 厨显 :1165)· fatal(错误屏 :1190)。
- **组件**:pin pad/numpad(bespoke)· modal 6 · button 7。

### 1.3 ai(Pearnly AI SPA)
- **壳**:`static/ai/ai.html` → `static/dist/ai.html`;`/ai` + `/ai/{rest}`。`ai-theme.css` `@import` pearnly-ui.css;另 25 个 `ai-*.css` bespoke 模块。gate off/未登录 → 跳 `/home`。
- **路由源**:`static/ai/ai-router.js`(`parseHash`)。
- **19 个屏幕**:gate(登录/邀请门)· dashboard-matrix(工作台/矩阵 #/)· dashboard-board(五列看板 #/board)· pool(待我处理 #/pool)· desk(总台 #/desk,flag `pearnly_ai_front_desk`)· vatcheck(销项税三查 #/vatcheck)· fileconv(文件转换 #/fileconv)· payroll(工资表 #/payroll)· clients(客户目录 #/clients)· reports(报表中心 #/reports)· settings(#/settings)· **客户工作区** 5 视图(intake/wo/review/pkg/profile,`#/client/<id>/*`)· **单客户档案** 3 页签(profile/supplier/history,`#/clients/<id>/*`)。
- **组件**:empty 10(最重)· breadcrumb(全站仅此 1 处)· progress bar(fc/pr/vc-done-bar)· 图表多为 JS/SVG 绘制(无 CSS 类)。

### 1.4 dms(Pearnly DMS SPA)
- **壳**:`static/dms/dms.html` → `static/dist/dms.html`;`/dms` + `/dms/{rest}`。**邀请制,token gate,`dms_portal` flag 默认 off**。注意 `/dms-` 前缀(如 `/dms-pick`)**故意避开** `/dms/{rest}` 兜底。
- **设计系统**:链 pearnly-ui.css ✔(归主站紫);`dms-shell.css`/`dms-intake.css` bespoke token。
- **5 个屏幕**(`dms.html` `data-view`):gate(:13 #gateRoot)· intake(录入向导 :38,多步 confirm+erp-cards)· records(:44)· roster(花名册 :50)· billing(充值/top-up :56)。
- **companion**:car-select/paint pick(见 entry-aux `/dms-pick`)。
- **组件**:card ~16 · modal 12(全站最多)· stepper `.dx-stepper`/`.dx-step`(录入向导)。

### 1.5 console(权限/团队管理 SPA)
- **壳**:`static/console/console.html` → `static/dist/console.html`;`/console` + `/console/{rest}`。紫主题;前端 `can(team.member.view)` gate。
- **设计系统**:链 pearnly-ui.css ✔ + `console-theme.css`/`console.css` bespoke。
- **3 个屏幕**(`data-view`):members(团队 :29)· roles(:46)· security(:63)。
- **入口**:`/invite/{token}`(公开邀请接受页 `invite.html`,**bespoke,不在 pearnly-ui**)——归属 console 但壳独立。
- **组件**:唯一带 `.pu-skeleton` 级 skeleton bespoke 的站(1 处);check-card。

### 1.6 admin(Earn 超管 SPA)
- **壳**:`static/admin/admin.html` → `static/dist/admin.html`;`/admin` → **301** `/admin/cost`;`/admin/{rest}` 兜底。`admin.js` 经 `/api/me` `is_super_admin` 门控,非超管 → `/`。
- **入口**:`/earn`(超管后台登录 `earn-login.html`,bespoke);`admin.js` 失败 auth 弹回这里。
- **设计系统**:链 pearnly-ui.css ✔ + `admin.css` bespoke。**注意**:`dist/admin.css`(416KB)与 `dist/home.css` 共享 2345/2579 类——admin 是建在 home CSS 基座上的子应用,源 `admin.css` 仅 22KB。
- **10 个屏幕**(`admin.html` `#page-admin-*`):cost(成本/用量 :308,默认)· users(:606)· topup(:734)· monitor(:781)· settings(:890)· engine(识别/引擎 :981)· agent(:1067)· pos(:1114)· pearnly-ai(:1214)· dms(:1312)。

### 1.7 landing(品牌门户 / 营销)
- **壳**:`static/landing/portal.dc.html`(129KB)→ `static/dist/portal.html`;`/`(公开,无 auth,`_NO_CACHE`)。**`<!-- ui-lint: standalone -->` 完全 bespoke**:自托管字体 + WebGL runtime + 自有 `landing.css`/mascot/auth-modal——**不在 pearnly-ui.css**。
- **2 个屏幕/面**:hero + 产品 tour(`landing-tour*.js` + `landing-tour-cards/phone.css` + `mascot-scene.js`)· 内嵌 auth modal/SSO(`auth-modal.css`/`auth-sso.css`/`landing-auth.css`,登录/注册/SSO)。
- **是 4 产品分流门户**:把用户导向 home/pos/ai/dms 各入口。

### 1.8 pos-next(实验 SPA · ⚠ 未接后端路由)
- **壳**:`src/pos-next/index.html`(标题「POS-Next · 批1 收银主屏」)→ 构建产物 `static/_posnext/index.html`(`vite.pos-next.config.mjs`)。
- **⚠ 可达性**:`grep posnext routes/ = 0 命中`——**没有任何 FastAPI 路由**,仅经 `/static` 挂载直达 `/static/_posnext/index.html`。是 vendored Odoo OWL POS 的批-0 实验,大概率非面向用户的生产面。
- **设计系统**:链 pearnly-ui.css ✔(唯一链它但非生产路由的壳)。
- **6 个屏幕**(`src/pos-next/main.js` `state.screen`):product(:36)· payment(:37)· receipt(:38)· refund(:39)· refundDetail(:40)· refundDone(:41)。
- **组件**:67 个 `.posnext-*` inline 类(btn-pri/sec · modal · pinpad/pin-dot/pin-err · chip · tabs · empty · panel/cart · modebar/methods)+ vendored Odoo Owl numpad(`vendor/point_of_sale/...`,编译 bundle `index-Vig9GXUx.js` 未反编译)。

---

## 2. 入口 / 辅助面(Entry / Aux)总表 —— ≈32 个「最易被忘」的面

> 这些是设计系统的盲区:除了 6 个生产 SPA 壳 + pos-next 链 pearnly-ui.css,**下面几乎全 bespoke / 无设计系统**。

| # | 面 | 类型 | 位置(证据) | 归属 | 设计系统 |
|---:|---|---|---|---|---|
| 1 | `/` 品牌门户 | route+entry | pages_routes → dist/portal.html(源 portal.dc.html) | landing | BESPOKE |
| 2 | `/login` 主登录 | login-gate | pages_routes → dist/login.html(源 根 login.html) | landing/home | BESPOKE |
| 3 | `/pos` 老板登录 | login-gate | pages_routes → dist/pos-login.html | pos | BESPOKE |
| 4 | `/earn` 超管登录 | login-gate | pages_routes → dist/earn-login.html | admin | BESPOKE |
| 5 | `/reset` 改密页 | login-gate | pages_routes → dist/reset.html(`test_reset_page_static.py` 覆盖) | home | BESPOKE |
| 6 | `/invite/{token}` 邀请接受 | entrance | pages_routes → dist/invite.html(源 console/invite.html) | console | BESPOKE |
| 7 | `/dms-pick` 选车/配色 webview | embedded-webview | `dms_pick_routes.py:72-78` → dist/dms-pick.html;LINE 一次性 `?t=` token,`/api/dms/pick/*` 校验,`no-store` | dms | BESPOKE(本地 rgb token 镜像 dms-shell) |
| 8 | `/terms` 服务条款 | legal | pages_routes → dist/terms.html | landing | BESPOKE |
| 9 | `/privacy` 隐私政策 | legal | pages_routes → dist/privacy.html | landing | BESPOKE |
| 10 | `/admin` → 301 `/admin/cost` | redirect | pages_routes | admin | n/a |
| 11 | `/liff/purchase/{doc_id}` → 302 `/home` | webview redirect | `line_liff_routes.py:88-96`;auth `/api/line/liff/auth` id_token | home | 复用 home 壳 ✔ |
| 12 | OAuth「Signing you in…」(LINE)插页 | interstitial | `oauth_line_routes.py:314`(inline HTML,写 localStorage token 后跳转) | — | inline bespoke |
| 13 | OAuth「Signing in…」(通用)插页 | interstitial | `oauth_routes.py:205`(inline HTML) | — | inline bespoke(深色 #0a0e27 splash) |
| 14 | OAuth 内嵌浏览器 breakout 页 | interstitial | `oauth_routes.py:65-80` `_BREAKOUT_HTML`(lang=th,逃 LINE webview) | — | inline bespoke |
| 15 | Google 集成 OAuth(connect/callback/status/disconnect) | integration-oauth | `google_oauth_routes.py:89,131`(前缀 `/api/integrations/google`) | home | inline bespoke(泰文错误串) |
| 16 | Google OAuth 错误页(授权失败/过期/换令牌) | error | `google_oauth_routes.py:137,141,145`(400/502 inline 片段) | — | 裸 `<p>` 无样式 |
| 17 | `/pos-sw.js` 遗留收银 PWA SW | PWA asset | `pages_routes.py:157-163`(scope /pos) | pos | n/a(JS) |
| 18 | `/cashier-sw.js` 新收银 PWA SW | PWA asset | `pages_routes.py:166-172`(scope /cashier) | pos | n/a(JS) |
| 19 | `/static/*` 原生挂载 | raw static | `app.py:493` StaticFiles | 全部 | 混合——**直达未压缩源壳**(admin/ai/pos/dms/console/portal/earn-login)+ 全 dist + `_posnext/index.html` |
| 20 | 小助手安装包下载 | companion | `companion_installer_routes.py:20-30`(auth-gated exe;目录未在 = 未发布) | companion | N/A(原生 Windows,无 web 面) |
| 21 | LINE bot 图/Flex 卡 + onboarding 卡 | companion-cards | `static/line-cards/*.jpg`(A1-welcome/A2..A11 状态/A12-onboard-1..6/B-banner-*);经 `line_card_image_routes.py:31` | companion | 预渲染 JPG,非 HTML |
| 22 | 邮件:验证码(注册) | email | `auth_email_code_routes.py:123-150`(4 语 inline HTML,紫渐变) | — | BESPOKE inline-style |
| 23 | 邮件:团队邀请 | email | `services/team/invitations.py:243-247` | — | BESPOKE inline-style |
| 24 | 邮件+LINE:密码重置 | email | `auth_password_routes.py:64-72`(email)+ `:36`(LINE 文本) | — | BESPOKE inline-style |
| 25 | 邮件:销售单据带 PDF 附件 | email | `services/sales/send.py:36-72`;路由 `sales_send_routes.py` | — | BESPOKE inline-style |
| 26 | POS 热敏小票 PDF(58/80mm) | print-receipt | `services/pos/receipt_pdf.py:16` → `services/sales/pdf_thermal.py`;`pos_sales_routes.py:139` | pos | N/A(热敏 PDF) |
| 27 | 充值/泰式标准税票 PDF | pdf-receipt | `services/billing/topup_receipt.py`(ใบเสร็จ/ใบกำกับภาษี,Sarabun 字体,VAT7% split) | — | N/A(打印 PDF) |
| 28 | 银行/GL 对账 PDF(mrerp) | pdf-report | `services/recon/bank_gl_pdf_mrerp.py` | home | N/A(打印 PDF) |
| 29 | 应用内报表导出 modal + 模板 | print-export | `src/home/report-templates.ts`(4 语,复用 4 处) | home | in-SPA modal(home 在设计系统 ✔) |
| 30 | 销售单据热敏打印视图 | print | `src/home/sales-common.ts`(window.print) | home | in-SPA print CSS |
| 31 | 未捕获 500 错误处理 | error | `app.py:469-472` → `services/error_handlers.py`;`_record_500` 快照。**无自定义 404/维护页** | — | JSON/handler,无样式页 |
| 32 | 设计系统预览页 | design-preview | `design-preview/pearnly-ui.html` + `buttons.html` + `check_ui_consistency.py`;另 `pearnly_nav_prototype_final.html`(141KB nav 原型) | — | **是** 设计系统本身的展示页(`--pu-*` token 源) |

---

## 3. 组件矩阵(37 类)× 设计系统状态 × 分布

> 图例:**建成-未采用** = pearnly-ui.css 里有 `.pu-*` 类但生产标记 0 引用;**桩** = 只有注释占位(B4/B5),未实现;**零** = 设计系统里完全没有。
> `bespoke~N` = 各 SPA 自写的 distinct class 家族数(工程量级代理,非精确)。

| 组件 | 设计系统状态 | pearnly-ui.css 锚点 | 分布(SPA 数/重灾) | bespoke~ |
|---|---|---|---|---:|
| Button | 建成-未采用 | `.pu-btn` :119(B2 全变体/尺寸/loading) | 全 8 站(home 133) | ~170 |
| Modal/Dialog | 建成-未采用 | `.pu-modal` :449 / mask :431(B3.2) | 7/8(dms 12 最多) | ~110 |
| Toast | 建成-未采用 | `.pu-toast` :325 / stack :297(B3.1) | 6/8(DMS `toast()` 复制 ~7 文件) | ~35 |
| Empty state | 建成-未采用 | `.pu-empty` :547(B3.3) | 6/8(home 82 · ai 10) | ~90 |
| Error/retry | 建成-未采用 | `.pu-error` :585(B3.4) | 5/8(home 35) | ~35 |
| Skeleton | 建成-未采用(近乎 net-new) | `.pu-skeleton` :626(B3.5) | 1/8 bespoke(仅 console) | ~1 |
| **Table/data-table** | **桩**(B4,未建) | `:629` 注释 `.pu-table` | 4/8(home 44) | ~49 |
| **Pagination/pager** | **桩**(B4,未建) | `:629` 注释 `.pu-pager` | 4/8(admin/console/dms/home) | ~33 |
| **Text input/field** | **桩**(B5,未建;`--ctrl-*` :65-67 已留) | `:630` 注释 `.pu-field/.pu-input` | 5/8(home 48) | ~66 |
| **Select/combobox** | **桩**(B5) | `:630` `.pu-select` | 3/8 + 大量 native | ~29 |
| **Checkbox** | **桩**(B5) | `:630` `.pu-check` | 5/8 | ~37 |
| Textarea | 桩(并入 B5)/多为 native | — | 1/8 显式 | ~1 |
| Loading spinner(非 skeleton) | 零(仅 `.pu-btn.is-loading`) | — | 3/8(home 28) | ~33 |
| Radio | 零(B5 只列 check,无 radio) | — | 3/8 | ~6 |
| Switch/toggle | 零 | — | 5/8(home 33) | ~42 |
| Date picker/calendar | 零(**连 bespoke 都没有**,全 native input) | — | 0/8 | 0 |
| File upload/dropzone | 零 | — | 2/8(home 38,OCR 录入重) | ~41 |
| Drawer/sheet | 零 | — | 3/8(home 82 极重) | ~84 |
| Popover/flyout | 零 | — | 2/8 | ~10 |
| Dropdown/context menu | 零 | — | 2/8 | ~13 |
| Tabs/notebook | 零 | — | 6/8(dms 7 · home 63) | ~79 |
| **Badge/chip/tag/pill** | 零 | — | 全 8 站(home 155) | **~185**(第二大) |
| Avatar | 零 | — | 4/8(admin 7) | ~26 |
| Tooltip | 零 | — | 3/8(home 15) | ~17 |
| **Card/panel** | 零 | — | 全 8 站(home 177 · dms 16) | **~222**(最大结构族) |
| Banner/alert/callout | 零(区别于 toast:内联常驻) | — | 4/8(home 46) | ~56 |
| Breadcrumb | 零(近乎缺失) | — | 1/8(ai) | ~1 |
| Stepper/wizard | 零 | — | 5/8(dms 录入 + home 销售向导) | ~44 |
| Accordion/collapsible | 零 | — | 3/8(home 19) | ~23 |
| Search/omnibox/cmdk | 零 | — | 6/8(home 42,含 cmdk 命令面板) | ~47 |
| Segmented control | 零 | — | 4/8 | ~6 |
| Progress bar/meter | 零 | — | 2/8(home 19) | ~21 |
| Status bar | 零 | — | 1/8(home) | ~1 |
| Chart/data-viz | 零(多为 JS/canvas/SVG 绘制,无 CSS 类) | — | 2/8 CSS(landing spark) | ~7(+JS 未计) |
| Nav/sidebar/topbar 壳 chrome | 零(pearnly-ui「B1 只留 headers」;壳从未中心化) | — | 6/8(home 56 · admin 8) | ~72 |
| Stat/KPI tile | 零 | — | 3/8(home 65,dashboard 重) | ~70 |
| PIN pad/numpad(POS) | 零(域组件,pos-next 用 vendored Odoo Owl) | — | 2/8(pos/posnext) | ~6 |

**汇总**:37 类中——建成但零采用 **6**;桩(计划未建 B4/B5)**5**(table/pager/text-input/select/checkbox);**26 类设计系统里完全没有**。**最大的 bespoke 债务**:Card/panel ~222 · Badge/chip ~185 · Button ~170 · Drawer ~84 · Tabs ~79 · Nav ~72 · Stat/KPI ~70。

---

## 4. ⚠ 交叉核对发现的缺口/存疑(最重要一节)

> 这些是 4 路勘察互相对不上、或与真代码对不上的地方。已逐条回代码核实。

| # | 存疑/缺口 | 谁说什么 | 核实结论(真代码) | 影响 |
|---:|---|---|---|---|
| **G1** | `.pu-*` 组件类**零生产采用** | COMPONENTS 声称「0 production markup」 | ✅**证实**:`grep pu-btn` 只命中 `pearnly-ui.css`(定义本身)+ `tests/e2e/_artifacts/ds_layout`(测试产物)。生产 html/js/ts **0 引用**。 | **设计系统组件层 0% 落地**——这才是「剩余设计系统工作」的真相,不是「还差 B4/B5」而是「已建的 B2/B3 也是货架货」 |
| **G2** | home `cloud` 页可达性 | SCREENS 说「`cloud` **不在** VALID_ROUTES → latent/unreachable」 | ❌**说反了**:`cloud` **在** VALID_ROUTES(`route-table.ts:30`),但**无 ROUTE_LOADER** → URL `#cloud` 会被接受、路由通过,只是渲染空的 `page-cloud`。是「**可路由但空**」,非「不可达」。 | 归类订正:cloud = 可达空壳;真正不可达的是 `test-center`(不在 VALID_ROUTES)与 `automation`(display:none) |
| **G3** | pos-next 是不是生产 SPA | SCREENS 当它是完整 SPA(壳+6 屏);ENTRY/ROUTES 说「无后端路由」 | ✅**证实无路由**:`grep posnext routes/ app.py = 0`。仅 `/static/_posnext/index.html` 直达。 | pos-next = **影子 SPA**:真代码在、链 pearnly-ui.css、但没接路由,用户正常路径**到不了**。别把它算进生产屏幕(本清单单列实验) |
| **G4** | 「6 站 vs 7 站接入设计系统」 | ROUTES 说「6 壳链 pearnly-ui.css」;SCREENS 说 pos-next 也链 | 两者都对但表述冲突:**7 个源壳** `grep` 到 pearnly-ui/ai-theme(home/pos/ai/dms/console/admin/**pos-next**),但只 **6 个是生产路由**。 | 口径统一:6 生产 + 1 实验(pos-next)= 7 文件链它;landing/login/reset/pos-login/earn-login/invite/terms/privacy/dms-pick **全不链** |
| **G5** | home 44 屏在 ROUTES 里「消失」 | ROUTES 只列 `/home` 一个壳 | 非缺口,是**粒度差**:44 屏是 `route-table.ts` 的 hash 路由,不是后端路由。 | 提醒:别把 `/home` 当「一个屏幕」——它下面 44 个可达页 + 3 占位 |
| **G6** | SCREENS 里 route-table.ts 行号自相撞 | 多条引 `:29`/`:33`(reconcile 与 sales-account 都标 :29;inventory 与 pos-onboarding 都标 :33) | 行号是近似/串号。**权威源 = 本清单 §1.1 的 VALID_ROUTES 全表**(已读真文件)。 | 引用 home 路由行号时以 `route-table.ts` 实文件为准,别信勘察里的行号 |
| **G7** | 原始 `/static` 挂载暴露**未压缩源壳** | ROUTES 与 SCREENS 都提到 | ✅ `app.py:493` StaticFiles(directory=static)→ `static/admin/admin.html` 等源壳、`_posnext/index.html` 均可直接 GET。 | 既是一致性面(源壳 ≠ dist),也是可达性/安全提醒:view-source 压外壳的前提被 `/static` 直达绕过 |
| **G8** | AI `desk` / home `knowledge` / dms 全站 = flag-gated | SCREENS 有标,ROUTES 未强调 | 证实:`pearnly_ai_front_desk`(desk)、knowledge flag、`dms_portal` 默认 off。 | 这些屏「默认看不到」——盘点 UI/验收时零配置账号根本走不到,易漏 |
| **G9** | settings 是 1 路由含 5 内部面板 | SCREENS 单列 settings | general/system/archive/rules/notifications 是 `settings-panels.ts` 内 tab,不是独立路由。 | 若要逐面盘点,settings 要拆 5 子面(本清单按 1 屏计) |
| **G10** | 无自定义 404/维护页 | ENTRY 提到 | ✅ 只有 `app.py:469` 的 500 exception handler(JSON/快照),**没有任何 404/维护 HTML**。 | 错误态是设计系统真空区——想统一错误页得从零起 |
| **G11** | `/dms-` 前缀故意避开 `/dms/{rest}` 兜底 | ROUTES 提到 | 证实:`/dms-pick` 走 `dms_pick_routes.py` 独立路由,不落 `/dms/{rest}` catch-all。 | 新增 `/dms-xxx` 面时别以为被 DMS SPA 兜住 |

---

## 5. 还可能漏的地方(completeness critic — 诚实的边界)

本次 4 路勘察扫的是「**后端页路由 + 壳 HTML + 路由表 + CSS 类家族**」。以下模态**没被逐一枚举**,是下一个「哎呀漏了」的高发区:

1. **SPA 内的 modal/drawer/wizard 子态**:`src/home/*-html.ts` 有约十几个注入式 HTML 模块(`app-shell-html` / `confirm-modals-html` / `cmdk-mask-html` / `bank-cand-drawer-html` 等),AI 的 sales-wizard 步、dms-intake confirm 步、POS numpad/桌台对话框、welcome/onboarding 向导、knowledge FAB——都是**屏内状态**,未作独立屏枚举。**闭合法**:对每个 SPA 跑一次「打开所有 modal/drawer/向导步」的真浏览器遍历,截图存档。
2. **LINE Flex-card / bot 会话 UI**:`services/line_binding/*.py`、`services/line_dms/cards.py` 的 Flex JSON 消息布局是聊天里的 UI,非 HTML,本次没解析。**闭合法**:单列一份 LINE 卡片清单(消息模板级)。
3. **flag/角色门控屏**:超管专属、`dms_portal`/`pearnly_ai_front_desk`/knowledge 等默认 off 的屏,零配置账号走不到。**闭合法**:用开全 flag 的 fixture 账号 + 超管账号各跑一遍旅程。
4. **打印/PDF 输出**(热敏小票、泰式税票、对账 PDF、报表导出):服务端渲染,非 DOM 屏,设计系统管不到。**闭合法**:单列打印物清单 + 各出一张样张。
5. **邮件模板(4 个)**:邮件客户端渲染,inline-style,与 web 设计系统天然隔离。**闭合法**:邮件模板单独立项统一。
6. **JS/canvas/SVG 绘制的图表**:AI dashboard 的数据可视化没有 CSS 类家族,组件矩阵里被低计。**闭合法**:按 JS 渲染器(非 CSS)另盘。
7. **动态/模板字面量注入的 HTML**:`src/**/*.ts` 里 template-literal 拼的 DOM 没被 class-count。**闭合法**:AST 扫 `` `<...>` `` 字面量。
8. **native HTML 控件**(date/textarea/部分 select/checkbox/radio):CSS 类=0 **不等于**控件不存在——它们是未加样式的原生元素。组件矩阵里这几类 bespoke~ 偏低是这个原因。
9. **pos-next 编译 bundle**:`static/_posnext/assets/index-*.js`(vendored Odoo Owl)未反编译,只扫了 inline 样式。
10. **原生小助手(companion)**:Windows 桌面 exe,无 web 面,本清单只记它的下载入口。UI 若要盘点需另开桌面端勘察。
11. **数字量级而非精确**:组件 bespoke~N 是 class-selector 家族的 grep 代理,会**过计**(关键词误命中工具类,如 `empty`/`-bar`)或**欠计**(native 控件、JS inline 样式)。当作数量级看,别当账。

---

*核对方法*:本清单在 4 路勘察基础上回代码复核了 11 处关键断言——读全 `routes/pages_routes.py` 与 `src/home/route-table.ts`;`grep` 验证 `.pu-*` 零采用、pos-next 零路由、7 源壳链 pearnly-ui.css、`cloud` 在 VALID_ROUTES 但无 loader。凡与勘察原文冲突处,以真代码为准并在 §4 标注。
