// 真浏览器验收 · B1 补期初卡(推送日志失败卡真实点击流)。
// 真实导航:/home → 点左栏「推送日志」→ 桩一条 stock_opening_needed 失败卡 →
// 点"补期初"展开面板 → 填 数量/单位成本/日期 → getComputedStyle 断言面板可见+逐行有三输入
// + 填得进。四语截图。产物:tests/visual/_shot/erp-stockopen-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8825;
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

const LOGS = {
    total: 1,
    items: [
        {
            id: 'log-stockopen',
            status: 'failed',
            trigger: 'manual',
            push_type: 'invoice',
            invoice_no: 'IV69/00520',
            endpoint_name: 'Express',
            ocr_buyer_name: 'บจก. ตัวอย่าง จำกัด',
            created_at: new Date().toISOString(),
            error_msg: 'stock_no_master_in_account_set',
            error_friendly: {
                th: 'ชุดบัญชีนี้ยังไม่มีสินค้าคงคลัง กรุณาตั้งยอดยกมาก่อน',
                zh: '该账套还没有这些库存商品 · 请先补期初',
                en: 'Account has no stock for these items. Set opening stock first.',
                ja: 'この帳簿に在庫がありません。先に期首在庫を登録してください。',
            },
            category: 'stock_opening_needed',
            stock_fix: {
                items: [
                    { name: 'น้ำแข็งหลอดเล็ก', stkcod: '' },
                    { name: 'น้ำแข็งบด', stkcod: '' },
                ],
            },
            http_status: 200,
            retry_count: 3,
            max_retries: 3,
        },
    ],
};
const EPS = { items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }] };

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newContext().then((c) => c.newPage());
    await page.setViewportSize({ width: 1320, height: 980 });

    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/logs'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(LOGS),
            });
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(EPS),
            });
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, items: [] }),
        });
    });

    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            plan: 'lifetime',
        });
        document.body.classList.remove('workspace-gate-preboot');
        const g = document.getElementById('workspace-gate-root');
        if (g) g.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
    });

    // 真实点击流:左栏「推送日志」→ 失败卡「补期初」按钮 → 面板展开 → 填三格。
    await page.waitForSelector('.nav-item[data-route="push-logs"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('.erp-log-card.fail [data-erpexc-acctfix]', { timeout: 15000 });
    await page.click('.erp-log-card.fail [data-erpexc-acctfix]');
    await page.waitForSelector('.erp-exc-stockopen[data-acctfix-panel]:not([hidden])', {
        timeout: 8000,
    });

    async function fillAndProbe() {
        // 逐行填 数量/单位成本/期初日期(证明填得进)。
        await page.evaluate(() => {
            document.querySelectorAll('.erp-exc-stockopen-row').forEach((row, i) => {
                const q = row.querySelector('[data-stockopen-qty]');
                const c = row.querySelector('[data-stockopen-cost]');
                const d = row.querySelector('[data-stockopen-date]');
                if (q) q.value = String(50 + i * 30);
                if (c) c.value = String(4.5 + i);
                if (d) d.value = '2026-06-01';
                [q, c, d].forEach((el) => el && el.dispatchEvent(new Event('input', { bubbles: true })));
            });
        });
        return page.evaluate(() => {
            const panel = document.querySelector('.erp-exc-stockopen[data-acctfix-panel]');
            if (!panel) return null;
            const cs = getComputedStyle(panel);
            const rows = [...panel.querySelectorAll('.erp-exc-stockopen-row')].map((r) => ({
                name: (r.querySelector('.erp-exc-stockopen-name') || {}).textContent || '',
                qty: (r.querySelector('[data-stockopen-qty]') || {}).value,
                cost: (r.querySelector('[data-stockopen-cost]') || {}).value,
                date: (r.querySelector('[data-stockopen-date]') || {}).value,
            }));
            const submit = panel.querySelector('[data-stockopen-submit]');
            return {
                display: cs.display,
                visibility: cs.visibility,
                opacity: cs.opacity,
                h: panel.getBoundingClientRect().height,
                rows,
                hasSubmit: !!submit,
            };
        });
    }

    const results = [];
    for (const lang of ['th', 'zh', 'en', 'ja']) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]');
        await page.waitForSelector('.erp-log-card.fail [data-erpexc-acctfix]', { timeout: 8000 });
        await page.click('.erp-log-card.fail [data-erpexc-acctfix]');
        await page.waitForSelector('.erp-exc-stockopen[data-acctfix-panel]:not([hidden])', {
            timeout: 8000,
        });
        const probe = await fillAndProbe();
        await page.screenshot({ path: path.join(OUT, `erp-stockopen-${lang}.png`) });
        results.push({ lang, probe });
    }

    await browser.close();
    srv.close();

    let fail = 0;
    for (const r of results) {
        const p = r.probe || {};
        const visible =
            p.display !== 'none' &&
            p.visibility !== 'hidden' &&
            parseFloat(p.opacity) > 0 &&
            p.h > 0;
        const twoRows = (p.rows || []).length === 2;
        const filled = (p.rows || []).every((x) => x.qty && x.cost && x.date && x.name);
        const ok = visible && twoRows && filled && p.hasSubmit;
        if (!ok) fail++;
        console.log(
            `[${ok ? 'PASS' : 'FAIL'}] ${r.lang} visible=${visible} rows=${(p.rows || []).length} ` +
                `filled=${filled} submit=${p.hasSubmit} :: ${JSON.stringify(p.rows)}`
        );
    }
    console.log(fail === 0 ? '\n✅ ALL PASS (4/4)' : `\n🔴 ${fail} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
