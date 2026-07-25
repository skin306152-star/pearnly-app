// 使用教程配图批量生成器。
// 图不手截:界面一改重跑本脚本即全部换新,教程里的图永远和线上一致(手截的图三周后就是假的)。
// 产物 static/guide/shots/*.png → build-home-css.mjs 复制进 static/dist/guide-shots/ 随 dist 部署。
// 跑法: node scripts/_guide_shots.cjs [shotId...]  不带参数=全截
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'static', 'guide', 'shots');
const PORT = 8798;
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

const EPS = {
    items: [
        {
            id: 'e1',
            adapter: 'express',
            name: 'Express',
            enabled: true,
            auto_push: true,
            config: { agent_last_seen_at: new Date().toISOString() },
        },
    ],
};

async function boot(ctx, lang) {
    const page = await ctx.newPage();
    await page.addInitScript((lg) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', lg);
    }, lang);
    await page.route('**/api/**', (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(EPS),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true }),
        });
    });
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function');
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('#dx-inv-drop', { timeout: 15000 });
    await page.waitForTimeout(500);
    return page;
}

// 每张图 = 一个选择器 + 可选的前置动作。element 截图而非整页:教程里要的是那一块。
const SHOTS = [
    {
        id: 'upload-01-nav',
        sel: '#sidebar .nav-group, #sidebar',
        prep: async (page) => {
            // 折叠组默认可能是收起的,展开后才拍得到四个入口。
            await page.evaluate(() => {
                document
                    .querySelectorAll('[data-collapsible="firm"] .nav-group-head')
                    .forEach((h) => {
                        const g = h.closest('[data-collapsible]');
                        if (g && !g.classList.contains('open')) h.click();
                    });
            });
            await page.waitForTimeout(400);
        },
    },
    { id: 'upload-02-task', sel: '.dx-task' },
    { id: 'upload-03-dropzone', sel: '#dx-inv-drop' },
    {
        id: 'upload-04-queue',
        sel: '.dx-qlist',
        prep: async (page) => {
            // 文件体积要像真的:1 字节会渲染成「0.0 MB」,会计看图时会以为文件是空的。
            await page.setInputFiles('#dx-inv-file', [
                // 文件名不带语种:中泰两套图共用,也更像会计真实的扫描件命名。
                {
                    name: 'INV-2569-07-01.pdf',
                    mimeType: 'application/pdf',
                    buffer: Buffer.alloc(Math.round(1.2 * 1048576)),
                },
                {
                    name: 'RECEIPT-2569-07-02.jpg',
                    mimeType: 'image/jpeg',
                    buffer: Buffer.alloc(Math.round(0.8 * 1048576)),
                },
            ]);
            await page.waitForTimeout(700);
        },
    },
    { id: 'upload-05-start', sel: '.dx-bar' },
];

// 每种语言各截一套:中文正文配中文界面图,泰文配泰文。混用会让读者对不上号。
const LANGS = ['zh', 'th'];

async function run() {
    const only = process.argv.slice(2);
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        deviceScaleFactor: 2, // 2 倍图经得起放大;页面侧按 naturalWidth/2 还原显示尺寸
    });

    let ok = 0;
    let miss = 0;
    for (const lang of LANGS) {
        const page = await boot(ctx, lang);
        for (const s of SHOTS) {
            if (only.length && !only.includes(s.id)) continue;
            try {
                if (s.prep) await s.prep(page);
                const sels = s.sel.split(',').map((x) => x.trim());
                let target = null;
                for (const sel of sels) {
                    target = await page.$(sel);
                    if (target) break;
                }
                if (!target) {
                    console.log('MISS ', `${s.id}.${lang}`, '· 选择器没命中:', s.sel);
                    miss++;
                    continue;
                }
                await target.screenshot({ path: path.join(OUT, `${s.id}.${lang}.png`) });
                console.log('OK   ', `${s.id}.${lang}`);
                ok++;
            } catch (e) {
                console.log('FAIL ', `${s.id}.${lang}`, String(e).slice(0, 120));
                miss++;
            }
        }
        await page.close();
    }

    await browser.close();
    srv.close();
    console.log(`\n${ok} 张已生成, ${miss} 张未取到 → ${OUT}`);
    process.exit(miss ? 1 : 0);
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
