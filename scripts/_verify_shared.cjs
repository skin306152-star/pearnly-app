// 教程相关真浏览器脚本的公共零件:静态服务器 / PASS-FAIL 计数 / 越过套账硬门 / 面包屑取值。
// 三个消费方(_guide_page_verify · _guide_deeplink_verify · _guide_shots_env)原先各抄一份,
// MIME 少一种、硬门注入漏一句都只会在自己那份里修好 —— 收拢到这里,端口和特例路由由调用方传。
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

const MIME = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.json': 'application/json',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

// 应用是单页壳,这两条路由路径没有同名文件,得落到真实文件上。
function rewrite(urlPath) {
    if (urlPath === '/home') return '/home.html';
    if (urlPath === '/login') return '/static/dist/login.html';
    return urlPath;
}

/**
 * 仓库根静态服务器。
 * @param {number} port
 * @param {object} [opts]
 * @param {(p: string, res: http.ServerResponse) => boolean} [opts.intercept]
 *        自行响应并返回 true 即短路(用于把某个路径换成内存里拼好的内容)
 * @param {(p: string) => string | null} [opts.resolveFile]
 *        把某条路径指到仓库外的绝对路径(如临时构建产物);返回 null 走默认解析
 * @returns {Promise<http.Server>}
 */
function serveStatic(port, { intercept, resolveFile } = {}) {
    const srv = http.createServer((req, res) => {
        const p = rewrite(decodeURIComponent(req.url.split('?')[0]));
        if (intercept && intercept(p, res)) return;
        // 仓库外的落点必须由调用方显式给出才放行;默认解析的路径一律不许越出 ROOT。
        const outside = resolveFile ? resolveFile(p) : null;
        const file = outside || path.join(ROOT, p);
        const inFence = outside || file.startsWith(ROOT);
        if (!inFence || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': MIME[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(port, () => r(srv)));
}

const tally = { pass: 0, fail: 0 };

function chk(name, ok) {
    ok ? tally.pass++ : tally.fail++;
    console.log((ok ? 'PASS' : 'FAIL').padEnd(5), name);
    return ok;
}

// 打印合计并给出退出码,调用方写 process.exit(summary())。
function summary() {
    console.log(`\n${tally.pass} passed, ${tally.fail} failed`);
    return tally.fail ? 1 : 0;
}

// 没选账套时套账硬门盖满全屏。验的是门后面的东西 → 进来先拆门,再压住它重开。
const dropWorkspaceGate = (page) =>
    page.evaluate(() => {
        window.isOwner = () => true;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
    });

// 面包屑当前文案(中间层按钮 + 末级当前项)。
const crumbs = (page) =>
    page.evaluate(() =>
        [...document.querySelectorAll('.gd-crumb-b, .gd-crumb-cur')].map((e) =>
            e.textContent.trim()
        )
    );

/**
 * 起一个已登录、已越过套账硬门、停在 home 的页面,并回收页面 JS 错误。
 * beforeGoto 里注册的 route 晚于通配兜底 —— Playwright 后注册者先匹配,更具体的规则才生效。
 */
async function bootHome(ctx, { port, lang = 'th', viewport, beforeGoto } = {}) {
    const page = await ctx.newPage();
    if (viewport) await page.setViewportSize(viewport);
    await page.addInitScript((lg) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', lg);
    }, lang);
    await page.route('**/api/**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, items: [] }),
        })
    );
    if (beforeGoto) await beforeGoto(page);
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + port + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function');
    await dropWorkspaceGate(page);
    return { page, errs };
}

module.exports = { MIME, serveStatic, chk, summary, dropWorkspaceGate, crumbs, bootHome };
