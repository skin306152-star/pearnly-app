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
            'pos/pos-ops.js',
            'pos/pos-cashier.js',
            'pos/pos-restaurant.js',
            'pos/pos-restaurant-ops.js',
            'pos/pos.js',
        ],
    },
];

for (const b of BUNDLES) {
    const code = b.files
        .map((f) => transformSync(readSource(`static/${f}`), { loader: 'js', minify: true }).code)
        .join(';\n');
    writeDist(b.out, code);
}
