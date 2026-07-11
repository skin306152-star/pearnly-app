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
            'ai/ai-review-render.js',
            'ai/ai-review-pool.js',
            'ai/ai-review.js',
            'ai/ai-intake-render.js',
            'ai/ai-intake.js',
            'ai/ai-pkg-render.js',
            'ai/ai-pkg.js',
            // ai-recon-render.js(E2 · 银行对账四清单纯逻辑+HTML,依赖 AI.state/format/
            // viewer/router)排在 ai-recon.js(挂载/折叠/原图模态/推 LINE 待问编排)之前,
            // 两者都在 ai-client.js(renderWo 用 AI.recon.mount)之前——同 ai-pkg 先例。
            'ai/ai-recon-render.js',
            'ai/ai-recon.js',
            'ai/ai-profile-render.js',
            'ai/ai-profile-panels-render.js',
            'ai/ai-supplier-profiles-render.js',
            'ai/ai-profile.js',
            'ai/ai-client-pool-render.js',
            'ai/ai-client-pool.js',
            'ai/ai-client.js',
            'ai/ai.js',
        ],
    },
];

for (const b of BUNDLES) {
    const code = b.files
        .map((f) => transformSync(readSource(`static/${f}`), { loader: 'js', minify: true }).code)
        .join(';\n');
    writeDist(b.out, code);
}
