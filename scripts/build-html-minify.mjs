// 把可读的 home.html / login.html 源压缩成 minified 产物到 static/dist/,
// 路由层改读这俩(见 routes/pages_routes.py)。源保持可读,产品 view-source 精简成一行。
//
// 用法: node scripts/build-html-minify.mjs

import { minify } from 'html-minifier-terser';
import { transform } from 'esbuild';
import CleanCSS from 'clean-css';
import { readSource, writeDist } from './build-lib.mjs';

// 门户 dc-runtime 用 style="{{ 绑定 }}" 承载按状态变化的内联样式(导航语言按钮等),由
// support.js 水合时把 {{…}} 换成 renderVals() 的样式对象。但 minifyCSS:true 走 CleanCSS,
// 它视 {{…}} 为非法 CSS 整条丢弃 → served 产物退化成 style=""(占位没了,水合无从下手,
// 元素裸奔无样式)。故自定义 minifyCSS:含 {{ 的内联样式原样放行交运行时,其余照
// html-minifier 默认路径(wrap→CleanCSS→unwrap)压。
const wrapCSS = (text, type) =>
    type === 'inline'
        ? '*{' + text + '}'
        : type === 'media'
          ? '@media ' + text + '{a{top:0}}'
          : text;
const unwrapCSS = (text, type) => {
    const m =
        type === 'inline'
            ? text.match(/^\*\{([\s\S]*)\}$/)
            : type === 'media'
              ? text.match(/^@media ([\s\S]*?)\s*{[\s\S]*}$/)
              : null;
    return m ? m[1] : text;
};
async function minifyCSSKeepBindings(text, type) {
    if (text.includes('{{')) return text; // dc-runtime 绑定占位:放行,交给运行时水合
    const out = new CleanCSS({}).minify(wrapCSS(text, type));
    return out.errors.length ? text : unwrapCSS(out.styles, type);
}

// 保守但有效:折叠标签间空白 + 压内联 JS(鉴权 bootstrap),保留 data-i18n / 属性引号 / 自闭合斜杠
const OPTS = {
    collapseWhitespace: true,
    conservativeCollapse: true, // 至少留一个空格,防 inline 元素(span/a)粘连
    removeComments: true,
    minifyJS: true,
    minifyCSS: minifyCSSKeepBindings,
    keepClosingSlash: true,
    caseSensitive: true,
};

// 门户 dc-runtime 的组件逻辑挂在 <script type="text/x-dc">(support.js 经 Babel 转译执行)。
// html-minifier 的 minifyJS 只认 text/javascript,不碰自定义 type → 那 ~580 行可读逻辑(含中文
// 注释)会原样吐进产物,view-source 退化。而 processScripts 会把内容当 HTML 重新解析(报错)。
// 故先用 esbuild 单独把 x-dc 脚本体压成一行(纯 JS 逻辑,非 JSX),再交给 html-minifier 压外壳。
async function preminifyDcScript(html) {
    const re = /(<script\b[^>]*\btype="text\/x-dc"[^>]*>)([\s\S]*?)(<\/script>)/gi;
    const parts = [];
    let last = 0;
    for (let m; (m = re.exec(html)); ) {
        const { code } = await transform(m[2], { loader: 'js', minify: true });
        // esbuild 已压掉结构性换行;残留换行只在反引号模板串里(门户全是 GLSL 着色器串,
        // 无 # 预处理指令 / // 注释,语句以 ; 分隔)→ 换行折成空格语义等价,外壳收成一行。
        parts.push(html.slice(last, m.index), m[1], code.replace(/\n/g, ' ').trimEnd(), m[3]);
        last = m.index + m[0].length;
    }
    parts.push(html.slice(last));
    return parts.join('');
}

// 源(可读) → 产物(dist·minified)。所有对外路由的 HTML 外壳都经 FileResponse 读产物。
// dist/ 子目录 webhook 部署可靠拾取(门户 vendor 全套已实证),故新页面一律走"可读源→dist 产物",
// 不再内联进 .py 常量(2026-07-10 脸0 门户 + reset/pos-login 全部并入本管线)。
const TARGETS = [
    { src: 'home.html', out: 'static/dist/home.html' },
    { src: 'login.html', out: 'static/dist/login.html' },
    // 脸0 品牌门户(dc-runtime 营销页 · 路由 /)· 源逐字保真在 static/landing/,产物压成外壳。
    { src: 'static/landing/portal.dc.html', out: 'static/dist/portal.html' },
    // 管理控制台 / 邀请接受页:壳成品化(JS/CSS 早已进 dist · 此处收口 HTML 外壳)。
    { src: 'static/console/console.html', out: 'static/dist/console.html' },
    { src: 'static/console/invite.html', out: 'static/dist/invite.html' },
    // POS 收银 SPA:壳成品化(8 逻辑 JS 已合 dist/pos.js · 2 CSS 已合 dist/pos.css)。
    { src: 'static/pos/pos.html', out: 'static/dist/pos.html' },
    // POS 老板后台登录页(路由 /pos)· 原内联 routes/pos_login_page.py 常量 → 挪成可读源 + dist 产物。
    { src: 'static/pos/pos-login.html', out: 'static/dist/pos-login.html' },
    // Pearnly AI SPA(M1-W1):壳成品化(7 逻辑 JS 已合 dist/ai.js · 4 CSS 已合 dist/ai.css)。
    { src: 'static/ai/ai.html', out: 'static/dist/ai.html' },
    // Pearnly DMS SPA(身份证 → DMS 客户 · 邀请制独立入口):逻辑 JS 合 dist/dms.js · CSS 合 dist/dms.css。
    { src: 'static/dms/dms.html', out: 'static/dist/dms.html' },
    // Earn 平台超管后台(路由 /admin/*)· SPA 外壳收口(admin JS/CSS 仍独立 · 超管页防抄需求低)。
    { src: 'static/admin/admin.html', out: 'static/dist/admin.html' },
    // Earn 超管登录页(路由 /earn)· 原内联 routes/earn_login_page.py 常量 → 挪成可读源 + dist 产物。
    { src: 'static/earn/earn-login.html', out: 'static/dist/earn-login.html' },
    // 重置密码落地页(路由 /reset)· 原内联 routes/reset_page.py 常量 → 挪成可读源 + dist 产物。
    { src: 'reset.html', out: 'static/dist/reset.html' },
    // 法务公开页(路由 /terms /privacy)· 纯静态内容 · 外壳收口。
    { src: 'static/terms.html', out: 'static/dist/terms.html' },
    { src: 'static/privacy.html', out: 'static/dist/privacy.html' },
];

for (const t of TARGETS) {
    const src = await preminifyDcScript(readSource(t.src));
    const html = await minify(src, OPTS);
    writeDist(t.out, html.trimEnd());
}
