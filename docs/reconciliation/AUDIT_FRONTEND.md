# 对账中心 UI 落地 · 项目审计(§二 · 2026-06-13)

> 配合 `00_CURRENT_STATE_AND_CORRECTIONS.md`(权威现状)与 `UI_IMPLEMENTATION.md`(任务书)读。
> 本文是开工前的现状地图 + 原型映射表 + 风险。结论:**后端 + 三条业务逻辑链全就绪,本次只重排表现层外壳并把动作接到现有逻辑。**

---

## 一、现有实现位置

| 关注点 | 现有位置 | 说明 |
|---|---|---|
| 路由/页面入口 | route 名 `reconcile`;`src/home/recon-center.ts`(首页统计) + `src/home/page-reconcile.ts`(运行期注入 `#page-reconcile` innerHTML) | 外壳 HTML 来自 `page-reconcile-panes-1.ts`(`RECON_HTML_1`)+ `page-reconcile-panes-2.ts`(`RECON_HTML_2`) |
| 三 tab 切换 | `src/home/recon-subtab-settings.ts` `_initSubTabs()` | `[data-recon-tab]`:`bank` / `sale-vat` / `gl-vat` |
| 银行对账逻辑 | `bank-recon-v2.ts`(主)+ store/helpers/anchor/results/history/upload 六子模块 | submit→轮询→needs_mapping/review→结果→导出 **全通** |
| 收入对账逻辑 | `gl-vat-recon.ts` + `glv-*.ts` | submit `/api/recon/gl-vat/submit`,轮询同源 |
| 销项税逻辑 | `excel-formula-recon.ts` + `excel-recon-*.ts` | submit `/api/vat_excel/submit`,结果 `/api/vat_excel/tasks/{id}` + `/download` |
| 异步轮询(三对账共用) | `recon-job-poll.ts` → `window._reconPollJob` / `window._reconProgressText` | 轮询 `GET /api/recon/jobs/{id}` 到 done/failed/needs_mapping/needs_review |
| 字段对应弹窗 | `static/recon-mapping.js` → `window.ReconMapping.show(payload,{token,lang,onConfirmed})` | **真存学习层**(`services/importer/template_store`),即设计稿「确认字段对应关系」 |
| 内容确认弹窗 | `static/recon-review.js` → `window.ReconReview.show(payload,{token,lang,jobId,onConfirmed})` | 走 `confirm-rows` 真重对账,即设计稿「确认需要关注的内容」 |
| 模板下载端点 | `GET /api/recon/template/{doc_type}?lang=`(`routes/recon_jobs_routes.py:377`) | 真 xlsx,sheet 名 `Pearnly-<TYPE>` 签名,列头随 lang |
| toast / 确认框 | `window.showToast(msg,type)` / `window.showConfirm(...)` | |
| i18n | `static/i18n-data.js`(`window.I18N`)+ `window.t(key)` + `window.subscribeI18n` / `window.__i18nSubs` | |
| 构建 | `npm run build`(vite + build-home-css + build-home-js + html-minify);产物 `static/dist/{main.js,home.css}`;`src/main.js` 是入口 | home css/js 都打包,改完必 build + add static/dist + bump `?v=` |
| CSS | `home-21-recon-center` / `home-29-vat-recon-clients` / `home-32-recon-folding` / `home-35-bankrecon-v2` | 前缀 `.reconcile- / .recon- / .vex- / .glv- / .brv2-` |
| 权限 | 后端 `require_perm(recon.view/create/approve)`;前端无专门门控(owner 全开) | |

---

## 二、原型 → 项目映射表

| 原型元素 | 现有对应 | 处理方式 | 复用现有逻辑 |
|---|---|---|---|
| 页面标题区 | 新建(页头区) | 新外壳 | 否(纯展示) |
| 三个对账标签 | `[data-recon-tab]` 已有三 tab | 重排为 segmented,切换换 doc_type/端点/模板/数据 | 复用切换思路,新控制器 |
| 标准模板引导横幅 | 无 | 新建;暂不提示=会话隐藏可恢复 | 否 |
| 四步流程 | 无 | 新建(纯展示) | 否 |
| 左右上传卡片 | brv2/glv/vex 各有上传区 | 统一双卡;选择/拖拽走同一处理 | 复用 submit 入参组装 |
| 余额预检 | brv2 anchor 四输入(`brv2-anchor-*`) | 映射为余额预检面板,值入 `*_override` | 复用 anchor override 入参 |
| 对账中状态 | brv2 `#brv2-progress` + `_reconProgressText` | 诚实进行中态,无假百分比 | 复用 `_reconPollJob` |
| 结果指标(4KPI) | brv2 filter tabs / KPI strip | 新四指标卡,点击真筛选 | 复用 result 载荷 |
| 优先处理区 | 无(brv2 只有 filter) | 新建,按真实差异分类计数 | 复用 result 载荷 |
| 结果明细 | brv2 detail 表 | 新明细表,随 KPI 筛选 | 复用 result `detail` 行 |
| 模板中心抽屉 | 无(原型 mock) | 新建,下载走真端点 | 复用 template 端点 |
| 普通表格字段确认弹窗 | `window.ReconMapping` | **直接复用** | 是 |
| 文件内容确认弹窗 | `window.ReconReview` | **直接复用** | 是 |
| 导入说明弹窗 | 无 | 新建(纯说明) | 否 |
| 底部 4 个演示按钮 | 无 | **删除**(原型演示用) | — |

---

## 三、风险与冲突

1. **模板标签**:原型 JS 的 `config.income = 收款流水/销售收入` 是错的,作废。收入对账=GL+税表VAT;模板用 `00` 号文 §1.3 的 statement/gl/vat/invoice。
2. **收入对账端点**:实际 `/api/recon/gl-vat/submit`(非 Explore 误报的 `/api/glv/submit`)。
3. **进度**:后端只给 stage(parse/reconcile/...)无精确百分比 → 诚实进行中态,**禁原型的 setInterval 假 67% / 假「已处理 864 条」**。
4. **余额预检数据**:原型是写死 mock。真实只有银行对账有 GL/Statement 期初期末概念(接 anchor override);收入/销项税无同义余额 → 这两 tab 该区按真实情况隐藏/改文案,不造假。
5. **销项税结果**:vex 走自有 `/api/vat_excel/tasks/{id}` + `/download`,与 bank/gl-vat 的 `/api/recon/jobs/{id}` 不同源;统一控制器需按 tab 分派结果读取。
6. **后端依赖(00 号 §四)**:VAT 解析器 zh/ja 列头、销项发票 Excel 结构化路 —— 若未补,中/日界面税表/发票模板的「标准模板读取」或发票侧会静默失败,须在交付报告标注。
7. **演示数据**:原型固定 1,286 行 / 97% / TXN-* 一律不照搬,只接真实 result。
8. **共用工作树**:别窗口在改无关任务 → 已建分支 `feat/recon-center-redesign`,只动对账相关文件,不全局重置、不动别人文件。

---

## 四、施工取向(结论)

- **新建统一控制器 + 新外壳 HTML + 作用域 CSS(`.rcx-`)**,把动作接到上面「复用」列的现成端点/面板。
- 后端契约一字不改;`ReconMapping`/`ReconReview`/`_reconPollJob`/template/submit/export 全部复用。
- 旧 brv2/glv/vex 模块文件保留(其 init 见不到对应 DOM 即 no-op),逐步由新控制器接管页面。
</content>
</invoke>
