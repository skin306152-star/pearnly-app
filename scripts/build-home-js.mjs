// 把 home.html 里零散的浏览器全局脚本合并压缩成两个 bundle,按原加载位置分组:
//   pre.js  = main.js 之前(defer): recon-mapping + recon-review
//   post.js = main.js 之后(defer): erp-mrerp-connect + erp-log-enhance
// 分组 = 原 DOM 顺序,保住相对 main.js 的执行时序(脚本依赖 main.js 设的全局 +
// erp-log-enhance 依赖 erp-mrerp-connect 的 window._mrerpConnectShared)。
// 每个文件独立 minify 后用 `;` 拼接 = 等价于原来各自一个 <script>(同享全局作用域)。
// i18n-data.js 是 715KB 纯数据(window.I18N),保留独立 <script>,不并入。
// landing.js = 着陆页(landing -> scale -> i18n -> mascot,保 DOM 时序)。
//
// 用法: node scripts/build-home-js.mjs

import { transformSync } from 'esbuild';
import { readSource, writeDist } from './build-lib.mjs';

const BUNDLES = [
    { out: 'static/dist/pre.js', files: ['recon-mapping.js', 'recon-review.js'] },
    {
        out: 'static/dist/post.js',
        files: ['erp-mrerp-connect.js', 'erp-log-enhance.js'],
    },
    {
        out: 'static/dist/landing.js',
        files: [
            'landing/landing.js',
            'landing/landing-scale.js',
            'landing/landing-i18n.js',
            'landing/mascot-scene.js',
            'landing/landing-tour-i18n.js',
            'landing/landing-tour-scenes.js',
            'landing/landing-tour.js',
        ],
    },
    // 管理控制台 SPA · 邀请接受公开页:plain-script 逻辑 minify 进 dist(view-source 只见外壳)。
    // console-i18n.js 是纯翻译数据(window.CI18N · 同 home 的 i18n-data.js),保留独立 raw 在 HTML 先加载。
    { out: 'static/dist/console.js', files: ['console/console.js'] },
    { out: 'static/dist/invite.js', files: ['console/invite.js'] },
    // POS 收银 SPA(零售/药房/餐厅三业态):8 个 plain-script 逻辑文件按 DOM 顺序拼成一个
    // bundle(pos.js 原是 defer · 整 bundle 在 pos.html 以 defer 加载,执行时序不变)。
    // pos-i18n.js 是纯翻译数据(window.POSI18N · 同 console-i18n),保留独立 raw 先加载。
    // 离线链路(pos-offline outbox / pos-totals 本地算价)只是被打包,逻辑零改;pos-sw
    // cache-first 缓存此 bundle,bump CACHE 名即让旧的按文件缓存失效。
    {
        out: 'static/dist/pos.js',
        files: [
            'pos/pos-totals.js',
            'pos/pos-data.js',
            'pos/pos-offline.js',
            'pos/pos-approve.js',
            'pos/pos-ops.js',
            'pos/pos-shift.js',
            'pos/pos-cashier.js',
            'pos/pos-restaurant.js',
            'pos/pos-restaurant-ops.js',
            'pos/pos.js',
        ],
    },
    // Pearnly AI SPA(M1-W3)· 纯函数模块在前,DOM 编排模块在后,boot(ai.js)收尾。
    // ai-i18n.js 是纯翻译数据(window.AII18N · 同 console-i18n/pos-i18n),独立 <script> 先加载。
    // ai-board.js(分列/摘要纯函数)必须排在 ai-kanban-render.js(用它渲染)之前;
    // ai-kanban-render.js 必须排在 ai-dashboard.js(用它渲染看板)之前。
    // ai-viewer.js(原件查看器框架,零依赖)必须排在 ai-review-render.js(拼查看器骨架 HTML)
    // 和 ai-review.js(mount/remount 交互 + 共享 LRU 缓存)之前。ai-matrix-render.js(矩阵表格
    // 纯 HTML 拼装 + 事件委托,依赖 AI.state/format/board)必须排在 ai-matrix.js(数据编排,
    // C4 · 工作台新默认视图)之前,两者都排在 ai-dashboard.js 之后即可(矩阵/看板互不依赖,
    // 谁先谁后对彼此零影响,紧邻放置只是语义上的"同属工作台"分组)。ai-review-queue.js(队列
    // 过滤/分级/裁决 payload 纯函数)必须排在 ai-review-render.js(拼 HTML)之前,两者都要
    // 排在 ai-review.js(编排)之前;ai-client.js 挂 renderReview 时才用到 AI.review,
    // 故 ai-review.js 仍需排在 ai-client.js 之前。ai-intake-render.js(纯校验+HTML)排在
    // ai-intake.js(上传/填数/续跑编排)之前,两者都在 ai-client.js(renderIntake 用 AI.intake)之前。
    // ai-pkg-render.js(交付包纯函数+HTML,依赖 AI.format/AI.state/AI.viewer)排在
    // ai-pkg.js(挂载/下载/证据模态框编排)之前,两者都在 ai-client.js(renderPkg 用
    // AI.pkg)和 ai.js(离开客户页时调 AI.pkg.onLeave)之前。ai-profile-render.js(画像
    // 表单纯函数+HTML,buildProfilePayload 借道 AI.format.parseAmount)、
    // ai-profile-panels-render.js(别名+义务清单纯函数+HTML,拆自前者,单文件<500 铁律)、
    // ai-supplier-profiles-render.js(供应商过账档案纯函数+HTML,Z3-b·骨架同构别名面板)
    // 三者都必须排在 ai-profile.js(挂载/保存/别名与供应商档案增删编排)之前,四者都在
    // ai-client.js(renderProfile 用 AI.profile)之前(B2-e · 2026-07-10;Z3-b · 2026-07-11)。
    {
        out: 'static/dist/ai.js',
        files: [
            'ai/ai-format.js',
            'ai/ai-router.js',
            'ai/ai-state.js',
            // ai-poll.js(J-B · 共享轮询器:5s 间隔 + 终态即停 + 页面隐藏时暂停,零依赖)
            // 只需排在四个消费者(ai-intake.js/ai-review.js/ai-dashboard.js/ai-client.js)
            // 之前,紧邻 ai-state.js 是"同属零依赖基础设施"的语义分组。
            'ai/ai-poll.js',
            // ai-api-payroll.js(工资表 H1b 五端点,拆自 ai-api.js·单文件<500 铁律)只需
            // 排在 ai-api.js 之前(apiFactory() 到调用时才读 AI.apiPayroll,不是加载时),
            // 紧邻放置是"同属后端调用薄层"的语义分组。
            'ai/ai-api-payroll.js',
            // ai-api-client-import.js(IN-0d · 客户名录导入 parse/commit 两端点,拆自
            // ai-api.js·单文件<500 铁律)同 ai-api-payroll.js 先例,只需排在 ai-api.js 之前。
            'ai/ai-api-client-import.js',
            // ai-api-desk.js(FD-0d · 前门四端点:建草稿/解析/确认/消息流,拆自 ai-api.js·
            // 单文件<500 铁律)同 ai-api-payroll.js 先例,只需排在 ai-api.js 之前。
            'ai/ai-api-desk.js',
            // ai-api-review.js(MC1-b2 · 审核收件箱 + 签批闭环七端点,拆自 ai-api.js·单文件
            // <500 铁律)同 ai-api-payroll.js 先例,只需排在 ai-api.js 之前。
            'ai/ai-api-review.js',
            // ai-api-upload.js(S1 · 收料上传 XHR 进度薄层,拆自 ai-api.js·单文件<500
            // 铁律)同 ai-api-payroll.js 先例,只需排在 ai-api.js 之前。
            'ai/ai-api-upload.js',
            // 银行倒推四端点(run/progress/单行/批量裁决)，拆出避免 ai-api.js 顶格。
            'ai/ai-api-bank-sales.js',
            'ai/ai-api.js',
            // ai-gate.js(Z1-a 登录卡/邀请制门面)只依赖 AI.state.esc(可选)与全局 at()/
            // atSetLang,排在 ai-state.js/ai-api.js 之后、ai.js(boot 调 AI.gate.mountLogin/
            // mountInvited)之前即可,不依赖看板/客户页那批渲染模块。
            'ai/ai-gate.js',
            'ai/ai-viewer.js',
            'ai/ai-board.js',
            'ai/ai-kanban-render.js',
            'ai/ai-dashboard.js',
            'ai/ai-matrix-render.js',
            'ai/ai-matrix.js',
            'ai/ai-review-queue.js',
            // ai-review-verdict.js(MC1-b2 · 判据人话渲染 + 批量建议裁决纯函数,零依赖)
            // 排在 ai-review-queue.js 之后即可(同属人审判据的纯函数分组),
            // ai-review-inbox-render.js(用它拼裁决卡三件套)之前。
            'ai/ai-review-verdict.js',
            // ai-review-suggest-render.js(J-C · J-A 建议值三字段改数表单纯 HTML,依赖
            // AI.state)排在 ai-review-render.js 之前——cardHtml 的 editHtml 分支调用
            // AI.reviewSuggest.editFormHtml。ai-review-fold-render.js(J-C · 已判折叠分组 +
            // 批量确认横幅纯 HTML,依赖 AI.state/format/reviewQueue)与前者互不依赖,同属
            // "卡片之外的队列 chrome"分组,紧邻放置即可,都在 ai-review.js(注入两者)之前。
            'ai/ai-review-suggest-render.js',
            'ai/ai-review-fold-render.js',
            'ai/ai-review-render.js',
            'ai/ai-review-pool.js',
            // ai-review-bulk.js(J-C ·「全部按建议处理」批量确认状态机,依赖 AI.reviewQueue/
            // reviewVerdict/api,均已在上面)只需排在 ai-review.js(挂 S.bulkHandle)之前,
            // 同 ai-review-pool.js 先例。
            'ai/ai-review-bulk.js',
            'ai/ai-review.js',
            'ai/ai-intake-render.js',
            // ai-intake-manifest.js(IN-0b · 文件夹展平/队列态/盘点条+密码卡+续传横幅
            // 纯逻辑+HTML,依赖 AI.state)排在 ai-intake-render.js 之后即可——intakeHtml()
            // 只在渲染调用时才引用 AI.intakeManifest.*,不在加载期解析,顺序要求同其余
            // render 模块一样宽松;紧邻放置是"同属收料视图"的语义分组。
            'ai/ai-intake-manifest.js',
            // ai-bank-sales-render.js(SA-3b · 银行流水倒推销项建议卡纯逻辑+HTML,依赖
            // AI.state/format)排在 ai-intake.js 之前——收料 tab 缺 sales_summary 时,
            // needsCardHtml() 直接内嵌调用 AI.bankSalesRender.cardHtml(),不另开 mount。
            // ai-intake-bank-sales.js(拆自 ai-intake.js 的网络编排,单文件<500 行铁律)
            // 只需排在 ai-intake.js(mount() 里用 AI.intakeBankSales.create())之前。
            'ai/ai-bank-sales-groups.js',
            'ai/ai-bank-sales-render.js',
            'ai/ai-intake-bank-sales.js',
            // ai-intake-queue.js(IN-0b · 文件夹递归展开+批级隔离重试+密码串行+队列态
            // 持久化的联网编排,拆自 ai-intake.js·单文件<500 行铁律,同 ai-intake-bank-sales.js
            // 先例)依赖 AI.api/AI.intakeRender.splitBatches/AI.intakeManifest(均已在上面),
            // 只需排在 ai-intake.js(mount() 里用 AI.intakeQueue.create())之前。
            'ai/ai-intake-queue.js',
            // 排除件改判的联网态与 payload 纯函数；ai-intake.js mount 时装配。
            'ai/ai-intake-excluded.js',
            'ai/ai-intake.js',
            'ai/ai-pkg-render.js',
            // ai-mact-render.js(SA-1 · 机器自动改动清单)被 ai-pkg-render.pageHtml 在运行时
            // 调用,排在其后即可;拆成独立文件是因为 ai-pkg-render.js 已顶到 500 行铁律线。
            'ai/ai-mact-render.js',
            'ai/ai-pkg.js',
            // ai-recon-render.js(E2 · 银行对账四清单纯逻辑+HTML,依赖 AI.state/format/
            // viewer/router)排在 ai-recon.js(挂载/折叠/原图模态/推 LINE 待问编排)之前,
            // 两者都在 ai-client.js(renderWo 用 AI.recon.mount)之前——同 ai-pkg 先例。
            'ai/ai-recon-render.js',
            'ai/ai-recon.js',
            // ai-corrob.js(MC1-c.1 · 销项佐证卡:已开票逐票聚合的只读四态呈现,依赖 AI.state/
            // format)必须在 ai-client.js(renderWo 用 AI.corrob.mount)之前——同 ai-recon 先例;
            // 与银行对账区互不依赖,同属工单详情只读区块的语义分组。
            'ai/ai-corrob.js',
            // ai-shadow-render.js(F3 · 影子底稿三件套+GL对平纯逻辑+HTML,依赖 AI.state/
            // format)排在 ai-shadow.js(挂载/折叠编排)之前,两者都在 ai-client.js(renderWo
            // 用 AI.shadow.mount)之前——同 ai-recon 先例;与银行对账区互不依赖,紧邻放置
            // 只是"同属工单详情只读区块"的语义分组。
            'ai/ai-shadow-render.js',
            'ai/ai-shadow.js',
            // ai-financials-render.js(G1b · 月度报表包 BS/PL/TB + 账龄/折旧四态降级纯逻辑+
            // HTML,依赖 AI.state/format)排在 ai-financials.js(挂载/折叠编排)之前,两者都在
            // ai-client.js(renderWo 用 AI.financials.mount)之前——同 ai-shadow 先例;与影子
            // 底稿区互不依赖,紧邻放置只是"同属工单详情只读区块"的语义分组。
            'ai/ai-financials-render.js',
            'ai/ai-financials.js',
            'ai/ai-profile-render.js',
            'ai/ai-profile-panels-render.js',
            'ai/ai-supplier-profiles-render.js',
            'ai/ai-profile.js',
            'ai/ai-client-pool-render.js',
            // ai-client-pool.js 现更名导出 AI.clientPool(MC1-b2·「客户待答」降级为审核
            // 收件箱聚合页的第三分区,不再独占 #/pool——见该文件顶注)。
            'ai/ai-client-pool.js',
            // ai-review-progress.js(MC2-A3 · 裁决后进度轮询状态机纯函数,零依赖)排在
            // ai-review-inbox.js(用它排期轮询)之前即可。
            'ai/ai-review-progress.js',
            // ai-review-inbox-item-render.js(J-C · 单张裁决卡拼装,拆自 -inbox-render.js·
            // 单文件<500 铁律,依赖 AI.state/format/reviewQueue/reviewVerdict/reviewRender
            // 均已在上面)排在 -inbox-render.js(groupHtml 用它拼组内卡片)之前。
            // 审核收件箱聚合页(MC1-b2 · 接管 #/pool,方案见 ai-review-inbox.js 顶注)四文件:
            // -render.js(纯 HTML,依赖 AI.state/format/reviewQueue/reviewVerdict 均已在上面)、
            // -signoff.js(工单卡签批闭环状态机,依赖 AI.api)、-flagged.js(异常票据分组+
            // 批量/逐张裁决状态机,依赖 AI.reviewQueue/reviewVerdict/api)三者互不依赖,
            // 只需都排在 -inbox.js(编排,依赖前三者 + AI.clientPool,后者已在上面)之前。
            'ai/ai-review-inbox-item-render.js',
            'ai/ai-review-inbox-render.js',
            'ai/ai-review-inbox-signoff.js',
            'ai/ai-review-inbox-flagged.js',
            'ai/ai-review-inbox.js',
            // ai-vatcheck-render.js(N1 · 销项税报告三查纯逻辑+HTML,依赖 AI.state/format)
            // 排在 ai-vatcheck.js(上传/运行/挂载编排)之前,两者都在 ai.js(onRoute 用
            // AI.vatcheck.mount)之前——同 ai-client-pool 先例(顶层独立视图,不挂客户页下)。
            'ai/ai-vatcheck-render.js',
            'ai/ai-vatcheck.js',
            // ai-fileconv-render.js(K1b · 财务文件转换纯逻辑+HTML,依赖 AI.state/format)
            // 排在 ai-fileconv.js(上传/转换/下载编排)之前,两者都在 ai.js(onRoute 用
            // AI.fileconv.mount)之前——同 ai-vatcheck 先例(顶层独立工具视图)。
            'ai/ai-fileconv-render.js',
            'ai/ai-fileconv.js',
            // ai-payroll-render.js(H1b · 工资表 ภ.ง.ด.1 工具卡纯逻辑+HTML,依赖 AI.state/
            // format)排在 ai-payroll.js(选客户/期间/上传/映射确认/提交/手工加行/下载
            // 编排)之前,两者都在 ai.js(onRoute 用 AI.payroll.mount)之前——同 ai-fileconv
            // 先例(顶层独立工具视图)。ai-payroll-annual-render.js(批次 H 收尾件 · ภ.ง.ด.1ก
            // 年度聚合面板纯逻辑+HTML,依赖 AI.state/format/AI.payrollRender.issueRowHtml)
            // 拆自 ai-payroll-render.js(单文件<500 行铁律已在预算线上),排它之后即可
            // (只用它导出的 issueRowHtml,不依赖装配顺序),ai-payroll.js 之前(render() 里
            // 拼 AI.payrollAnnualRender.panelHtml)。
            'ai/ai-payroll-render.js',
            'ai/ai-payroll-annual-render.js',
            'ai/ai-payroll.js',
            // ai-desk-render.js(FD-0d · 总台 #/desk 消息卡纯逻辑+HTML,依赖 AI.state/format/
            // board)排在 ai-desk-compose-render.js(输入区/手动开单面板拼装,拆自前者·单
            // 文件<500 铁律,依赖 AI.deskRender 的 clientOptionsHtml/periodOptionsHtml/
            // intentOptionsHtml/confirmReady/feedHtml)之前,两者都在 ai-desk.js(编排:
            // 上传/送出/确认/手动兜底,依赖 AI.intakeRender.validateFiles/mergeFiles + 上面
            // 两个 render 模块)与 ai.js(onRoute 用 AI.desk.mount + 闸探针控制侧栏项显隐)
            // 之前——同 ai-vatcheck/ai-payroll 先例(顶层独立视图)。
            'ai/ai-desk-render.js',
            'ai/ai-desk-compose-render.js',
            'ai/ai-desk.js',
            // ai-client-wo-render.js(S2 · 工单页状态头纯拼装,拆自 ai-client.js·单文件<500
            // 铁律,依赖 AI.state/format/router/reviewQueue 均已在上面)只需排在 ai-client.js
            // (woSummaryPanel 重画用 AI.clientWoRender)之前。
            'ai/ai-client-wo-render.js',
            'ai/ai-client.js',
            // EN-clients(2026-07-13)· 客户目录/单客户档案页/报表中心/设置——三个侧栏占位
            // 收口转正。ai-clients-render.js(目录纯拼装,依赖 AI.matrixRender.BADGE_CHIP)
            // 排在 ai-matrix-render.js 之后即可(已在上面);ai-clients.js(目录编排)排它
            // 之后。ai-client-archive-render.js/ai-client-archive.js(档案页,复用
            // ai-profile.js 的 container/sections 改造,复用 ai-client.js 的 .chead/.ctabs
            // 结构)排在 ai-profile.js 与 ai-client.js 之后。ai-reports-render.js 依赖
            // AI.pkgRender.KIND_ORDER(已在上面 ai-pkg-render.js)与 AI.payrollRender.
            // defaultPeriod(已在上面 ai-payroll-render.js);ai-reports.js(报表中心编排)
            // 直接复用 AI.financials.mount()/AI.shadow.mount()(已在上面),排它们之后即可。
            // ai-settings.js 编排+拼装未拆(体量小,同 ai-financials.js 先例),零跨模块依赖
            // 之外的顺序要求,排最后、ai.js 之前。
            'ai/ai-clients-render.js',
            // ai-client-new.js(N1-P0-1 ·「+新建客户」模态,依赖 AI.state/api/router)只需
            // 排在 ai-clients.js(load() 里调 AI.clientNew.wireButton)之前。
            'ai/ai-client-new.js',
            // ai-client-import-render.js(IN-0d · 客户名录批量导入纯逻辑+HTML,依赖
            // AI.state)排在 ai-client-import.js(挂载/上传/预览/确认编排,依赖
            // AI.clientImportRender)之前,两者都在 ai-clients.js(load() 里调
            // AI.clientImport.wireButton)之前——同 ai-client-new.js 先例。
            'ai/ai-client-import-render.js',
            'ai/ai-client-import.js',
            'ai/ai-clients.js',
            'ai/ai-client-archive-render.js',
            'ai/ai-client-archive.js',
            'ai/ai-reports-render.js',
            'ai/ai-reports.js',
            'ai/ai-settings.js',
            'ai/ai.js',
        ],
    },
    // Pearnly DMS SPA(身份证 → DMS 客户)· 独立入口壳。装配顺序按依赖:全局工具 → 后端薄层 →
    // 登录门面 → 向导模板(DXHTML,被 core/confirm/controller 引用)→ 取值模型(DXST)→ 上下文
    // ERP 卡(读 DXST)→ 确认页(读 DXST/DXHTML)→ 控制器(读 DXST/DXHTML/DXCONFIRM/DXERP)→
    // 连接向导(读 DXAPI)→ LINE 绑定卡(DL-4b · 读 DXAPI,同 dms-connect 挂载范式,连接卡下方)
    // → 套餐与余额(波1 · 模板 dms-billing-html 先于逻辑 dms-billing · 读 DXAPI)→ 记录页 →
    // boot(读全部,收尾)。i18n 数据+装配层是独立 <script> 先加载(同 /ai 的
    // ai-i18n.js),不并入本 bundle。
    {
        out: 'static/dist/dms.js',
        files: [
            'dms/dms-util.js',
            'dms/dms-api.js',
            'dms/dms-gate.js',
            'dms/dms-intake-html.js',
            'dms/dms-intake-core.js',
            'dms/dms-intake-erp-cards.js',
            'dms/dms-intake-form.js',
            'dms/dms-intake-confirm.js',
            'dms/dms-intake.js',
            'dms/dms-connect.js',
            'dms/dms-line.js',
            'dms/dms-billing-html.js',
            'dms/dms-billing-topup.js',
            'dms/dms-billing-records.js',
            'dms/dms-billing.js',
            'dms/dms-roster-html.js',
            'dms/dms-roster.js',
            'dms/dms-records.js',
            'dms/dms-boot.js',
        ],
    },
];

for (const b of BUNDLES) {
    const code = b.files
        .map((f) => transformSync(readSource(`static/${f}`), { loader: 'js', minify: true }).code)
        .join(';\n');
    writeDist(b.out, code);
}
