// 使用教程页真浏览器验收:入口可达、目录成型、样章可读、配图真的加载出来、中泰跟随全站语言。
// 图用 naturalWidth 判,不看 src 是否写对 —— 路径写对但 404 的坑就是这么漏过去的。
// 跑法: node scripts/_guide_page_verify.cjs → tests/visual/_shot/guide-*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8799;
const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.map': 'application/json',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

function serve() {
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': TYPES[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

let pass = 0;
let fail = 0;
function chk(name, ok) {
    ok ? pass++ : fail++;
    console.log((ok ? 'PASS' : 'FAIL').padEnd(5), name);
    return ok;
}

async function boot(ctx, lang, viewport) {
    const page = await ctx.newPage();
    await page.setViewportSize(viewport);
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
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function');
    await page.evaluate(() => {
        window.isOwner = () => true;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
    });
    return { page, errs };
}

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ deviceScaleFactor: 2 });

    // ---- 泰文 · 桌面 ----
    const { page, errs } = await boot(ctx, 'th', { width: 1440, height: 980 });

    // 入口必须是「点得到」的,不是「DOM 里有」:会计版侧栏白名单漏加就会被 display:none。
    const navVisible = await page.evaluate(() => {
        const el = document.getElementById('nav-guide');
        if (!el) return false;
        let n = el;
        while (n && n !== document.body) {
            if (getComputedStyle(n).display === 'none') return false;
            n = n.parentElement;
        }
        return true;
    });
    chk('侧栏「使用教程」入口可见(未被业态白名单隐掉)', navVisible);

    await page.click('#nav-guide');
    await page.waitForSelector('#page-guide .gd', { timeout: 8000 });
    chk('点侧栏能进教程页', await page.isVisible('#page-guide .gd'));

    const secs = await page.locator('.gd-sec').count();
    chk(`目录列出全部 7 篇(实得 ${secs})`, secs === 7);

    const h1 = (await page.locator('.gd-h1').innerText()).trim();
    console.log('  泰文标题:', h1);
    chk('样章标题是泰文', /อัปโหลด/.test(h1));

    const steps = await page.locator('.gd-step').count();
    chk(`步骤全渲染(实得 ${steps} 步)`, steps === 6);

    const notes = await page.locator('.gd-note').count();
    chk(`提示块全渲染(实得 ${notes} 条)`, notes === 3);
    chk('有一条是警示级(计费那条)', (await page.locator('.gd-note.is-warn').count()) === 1);

    // 配图:naturalWidth>0 才算真加载出来,src 写对但 404 一样是白板。
    await page.waitForTimeout(1200);
    const imgs = await page.evaluate(() =>
        [...document.querySelectorAll('.gd-fig img')].map((i) => ({
            src: i.getAttribute('src'),
            w: i.naturalWidth,
        }))
    );
    console.log('  配图:', imgs.map((i) => `${i.src.split('/').pop()}=${i.w}px`).join(' '));
    chk(`配图数量正确(实得 ${imgs.length})`, imgs.length === 5);
    chk('每张配图都真的加载出来(naturalWidth>0)', imgs.length > 0 && imgs.every((i) => i.w > 0));
    chk(
        '没有降级成占位(说明图路径与部署链通了)',
        (await page.locator('.gd-fig.is-missing').count()) === 0
    );

    await page.screenshot({ path: path.join(OUT, 'guide-th-desktop.png'), fullPage: true });

    // ---- 切中文:正文跟随全站语言,页内没有独立语言键 ----
    await page.evaluate(() => window.applyLang && window.applyLang('zh'));
    await page.waitForTimeout(600);
    const h1zh = (await page.locator('.gd-h1').innerText()).trim();
    console.log('  中文标题:', h1zh);
    chk('切中文后正文变中文', h1zh === '上传本批票据');
    chk('页内没有单独的语言切换键', (await page.locator('.gd-lang-b').count()) === 0);
    await page.screenshot({ path: path.join(OUT, 'guide-zh-desktop.png'), fullPage: true });

    chk('无页面 JS 错误', errs.length === 0);
    if (errs.length) console.log('  pageerror:', errs.slice(0, 3));
    await page.close();

    // ---- 手机端:目录必须收到正文上方,不能并排挤成两栏 ----
    const { page: m } = await boot(ctx, 'th', { width: 390, height: 844 });
    await m.evaluate(() => window.routeTo('guide'));
    await m.waitForSelector('#page-guide .gd', { timeout: 8000 });
    const cols = await m.evaluate(
        () => getComputedStyle(document.querySelector('.gd')).gridTemplateColumns
    );
    console.log('  手机端栅格:', cols);
    chk('手机端目录改为单栏堆叠', !/\s/.test(cols.trim()));
    const noHScroll = await m.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth + 1
    );
    chk('手机端不横向滚动', noHScroll);
    await m.screenshot({ path: path.join(OUT, 'guide-th-mobile.png'), fullPage: true });

    await browser.close();
    srv.close();
    console.log(`\n${pass} passed, ${fail} failed`);
    process.exit(fail ? 1 : 0);
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
