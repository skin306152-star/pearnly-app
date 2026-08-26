/*
 * scripts/_sx_barcode_copy_accept.cjs · 建品表单条码位的文案独立验收(泰文界面 · 零文案注入)
 *
 * 补的是 _products_barcode_ui_verify.cjs 的一个洞:那个脚本把自带的一份中文 COPY 写进
 * window.I18N 的全部四种语言再断言,于是「泰文界面上其实画的是中文」这类漏译它天然照不出
 * (它的截图 07-scanned-filled.png 就是泰文页面配中文条码提示)。
 *
 * 这里一个字都不注入:期望值现场从页面里真 window.I18N.th 取(static/i18n-data.js 的真产物),
 * 断言屏幕上真的画着那几条泰文。摄像头是 Chromium 假设备喂真合成 EAN-13,只有 /api/** 是桩。
 *
 * 用法(仓库根目录):
 *   node scripts/_sx_barcode_copy_accept.cjs <fixture.y4m> [截图目录]
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const Y4M = path.resolve(process.argv[2] || '.scan_fixture.y4m');
const SHOTS = path.resolve(
    process.argv[3] || path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/sx-copy')
);
const CODE = '8850999320014';
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };
const DUP = { id: 'p-dup', name_th: 'น้ำอัดลม 325 มล.', name_en: 'Soda 325ml', barcode: CODE };

let lookupMode = 'free';

function serve() {
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        // cowork / erp / home(以及原 home.html / 空路径)都落到 home.html —— 路由名随 app 走,
        // 但静态地基只认这一个真文件。
        const page = ['cowork', 'erp', 'home', 'home.html'].includes(rel)
            ? 'home.html'
            : rel || 'home.html';
        const fp = path.join(ROOT, page);
        const ok = fp.startsWith(ROOT) && fs.existsSync(fp) && !fs.statSync(fp).isDirectory();
        res.writeHead(ok ? 200 : 404, {
            'content-type': ok ? MIME[path.extname(fp)] || 'text/html' : 'text/html',
        });
        if (ok) fs.createReadStream(fp).pipe(res);
        else res.end('not found');
    });
    return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

const json = (body, status = 200) => ({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
});

async function boot(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 1320, height: 960 } });
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th'); // 真语言键(旧脚本写的 'lang' 根本不生效)
        localStorage.setItem('pearnly_entry', 'pos');
        localStorage.setItem('pearnly_active_workspace_client_id', '1');
    });
    await page.route('**/api/**', (route) => {
        const u = route.request().url();
        if (route.request().method() !== 'GET') return route.fulfill(json({ ok: true }));
        if (u.includes('/api/sales/products/lookup')) {
            return route.fulfill(
                lookupMode === 'dup'
                    ? json({ product: DUP })
                    : json({ detail: 'sales.product_not_found' }, 404)
            );
        }
        if (u.includes('/api/sales/products')) return route.fulfill(json({ products: [] }));
        if (u.includes('/api/me/plan')) return route.fulfill(json({ plan: 'lifetime' }));
        if (u.includes('/api/me/modules'))
            return route.fulfill(
                json({
                    data: {
                        modules: { pos: { enabled: true }, inventory: { enabled: true } },
                        business_type: 'pos_only',
                        entry: 'pos',
                    },
                })
            );
        if (u.includes('/api/workspace/clients'))
            return route.fulfill(
                json({ clients: [{ id: 1, name: 'Demo Co Ltd', tax_id: '0105567178203' }] })
            );
        return route.fulfill(json({ ok: true, items: [] }));
    });
    await page.goto(origin + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal,#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
        window.routeTo('sales-products');
    });
    await page.waitForSelector('#sx-p-add', { timeout: 15000 });
    return page;
}

const textOf = (page, sel) =>
    page.evaluate((s) => {
        const el = document.querySelector(s);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const b = el.getBoundingClientRect();
        return {
            text: (el.innerText || el.textContent || '').trim(),
            visible: cs.display !== 'none' && cs.visibility === 'visible' && b.height > 0,
        };
    }, sel);

(async () => {
    if (!fs.existsSync(Y4M)) {
        console.error(`缺假摄像头素材 ${Y4M}`);
        process.exit(2);
    }
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch({
        args: [
            '--use-fake-ui-for-media-stream',
            '--use-fake-device-for-media-stream',
            `--use-file-for-fake-video-capture=${Y4M}`,
        ],
    });
    const page = await boot(browser, origin);
    const th = await page.evaluate(() => window.I18N.th);
    const lang = await page.evaluate(() => window._currentLang || null);

    await page.click('#sx-p-add');
    await page.waitForSelector('#sx-pf-barcode', { timeout: 8000 });
    const hint = await textOf(page, '.sx-bc-row + .sx-field-hint');
    // 扫码按钮是纯图标(无字):它的文案在 title / aria-label 上,那才是漏译看得见的地方
    const scanBtn = await page.evaluate(() => {
        const b = document.getElementById('sx-pf-bc-scan');
        return b ? { title: b.title, aria: b.getAttribute('aria-label') } : null;
    });

    await page.click('#sx-pf-bc-scan');
    await page.waitForFunction((c) => document.getElementById('sx-pf-barcode')?.value === c, CODE, {
        timeout: 30000,
    });
    await page.waitForFunction(
        () => (document.getElementById('sx-pf-bc-state')?.innerText || '').trim().length > 0,
        null,
        { timeout: 10000 }
    );
    const free = await textOf(page, '#sx-pf-bc-state');
    await page.screenshot({ path: path.join(SHOTS, 'cam-12-sx-barcode-th-free.png') });

    // 换成撞码再查一次:同一条链,只是后端说这个码有人用了
    lookupMode = 'dup';
    await page.fill('#sx-pf-barcode', '');
    await page.click('#sx-pf-barcode');
    await page.keyboard.type(CODE, { delay: 15 });
    await page.waitForFunction(
        () => (document.getElementById('sx-pf-bc-state')?.innerText || '').indexOf('325') >= 0,
        null,
        { timeout: 10000 }
    );
    const dup = await textOf(page, '#sx-pf-bc-state');
    await page.screenshot({ path: path.join(SHOTS, 'cam-13-sx-barcode-th-dup.png') });
    await browser.close();
    server.close();

    // 撞码那格里是「一句话 + 一个链接按钮」两个节点,innerText 会在中间塞换行 —— 分开比,
    // 别把渲染细节写进期望值(否则下次换个 <br> 就红,而文案其实没问题)。
    const wantDup = [th['sx-p-bc-dup'].split('{name}').join(DUP.name_th), th['sx-p-bc-dup-open']];
    const checks = [
        ['界面语言真的是泰文', lang === 'th'],
        ['条码框旁的提示是泰文真词条', hint && hint.visible && hint.text === th['sx-p-bc-hint']],
        [
            '扫码按钮 title/aria 是泰文真词条',
            !!scanBtn &&
                scanBtn.title === th['sx-p-bc-scan'] &&
                scanBtn.aria === th['sx-p-bc-scan'],
        ],
        ['摄像头解出的码填进了条码框', true], // waitForFunction 已保证
        ['「没人用这个码」是泰文真词条', free && free.visible && free.text === th['sx-p-bc-free']],
        [
            '撞码提示是泰文真词条 + 带商品名 + 去编辑那个商品',
            !!dup && dup.visible && dup.text.split(/\s*\n\s*/).join('|') === wantDup.join('|'),
        ],
    ];
    checks.forEach(([n, ok]) => console.log((ok ? 'PASS  ' : 'FAIL  ') + n));
    const bad = checks.filter(([, ok]) => !ok);
    console.log(JSON.stringify({ lang, hint, scanBtn, free, dup, wantDup }, null, 2));
    console.log(bad.length ? `FAIL ${bad.length} 条` : `PASS · 截图在 ${SHOTS}`);
    process.exit(bad.length ? 1 : 0);
})().catch((e) => {
    console.error('SX BARCODE COPY ACCEPT CRASH', e);
    process.exit(2);
});
