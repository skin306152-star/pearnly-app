// 真浏览器验收 · F1 错误码四语友好文案(推送日志页真实点击流)。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo 捷径)→ 桩两条失败日志
// (DBF_WRITE_FAILED / STOCK_ITEM_NOT_FOUND · error_friendly 用后端 friendly_any 真实输出)→
// 抓 getComputedStyle 断言失败摘要条可见、显泰文友好文案、不含裸原始码。四语截图。
// 模型抄 scripts/_stock_guard_ui_verify.cjs。产物:tests/visual/_shot/erp-errfriendly-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8824;
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

// error_friendly = 后端 friendly_any(...) 真实输出(逐字·非手打)。
const DBF_FRIENDLY = {
    zh: '写入 Express 账套失败 · 常见于该账套还没有库存商品主档 · 请先在 Express 建好库存商品,或本批改用「销售·服务」模式推送',
    en: 'Failed to write into the Express account set — commonly because the set has no stock-item master yet. Please create a stock item in Express first, or push this batch in the “Sales · Service” mode.',
    th: 'เขียนข้อมูลลงชุดบัญชี Express ไม่สำเร็จ มักเป็นเพราะชุดบัญชียังไม่มีสินค้าคงคลังตั้งต้น กรุณาสร้างสินค้าคงคลังใน Express ก่อน หรือส่งชุดนี้ด้วยโหมด «ขาย•บริการ»',
    ja: 'Express の帳簿セットへの書き込みに失敗しました。多くは在庫品マスタが未作成のためです。先に Express で在庫品を作成するか、本バッチを「販売・サービス」モードで送信してください。',
};
const STOCK_FRIENDLY = {
    zh: '该商品在 Express 里库存为零或不足 · 请先在 Express 录入进货或期初库存,再推送',
    en: 'This item has zero or insufficient stock in Express. Please record a purchase or opening balance in Express first, then push again.',
    th: 'สินค้านี้มีสต๊อกใน Express เป็นศูนย์หรือไม่เพียงพอ กรุณาบันทึกการซื้อหรือยอดยกมาใน Express ก่อน แล้วจึงส่งอีกครั้ง',
    ja: 'この商品は Express の在庫がゼロまたは不足しています。先に Express で仕入または期首在庫を登録してから再送信してください。',
};
const RAW = { dbf: 'DBF_WRITE_FAILED', stock: 'STOCK_ITEM_NOT_FOUND' };

const LOGS = {
    total: 2,
    items: [
        {
            id: 'log-dbf',
            status: 'failed',
            trigger: 'manual',
            push_type: 'invoice',
            invoice_no: 'IV69/00473',
            endpoint_name: 'Express',
            ocr_buyer_name: 'บจก. ตัวอย่าง',
            created_at: new Date().toISOString(),
            error_msg: 'DBF_WRITE_FAILED 账套无真库存品模板(STKTYP=0)',
            error_friendly: DBF_FRIENDLY,
            http_status: 200,
            retry_count: 3,
            max_retries: 3,
        },
        {
            id: 'log-stock',
            status: 'failed',
            trigger: 'manual',
            push_type: 'invoice',
            invoice_no: 'IV69/00475',
            endpoint_name: 'Express',
            ocr_buyer_name: 'บจก. ตัวอย่าง',
            created_at: new Date().toISOString(),
            error_msg: 'STOCK_ITEM_NOT_FOUND 零/负库存',
            error_friendly: STOCK_FRIENDLY,
            http_status: 200,
            retry_count: 3,
            max_retries: 3,
        },
    ],
};
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }],
};

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

    // 真实点击流:点左栏「推送日志」nav-item(不用 routeTo)。
    await page.waitForSelector('.nav-item[data-route="push-logs"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('#erp-logs-list .erp-log-card.fail .erp-log-reason', {
        timeout: 15000,
    });

    const results = [];
    async function checkAndShot(lang) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]'); // 重渲染当前语言
        await page.waitForSelector('#erp-logs-list .erp-log-card.fail .erp-log-reason', {
            timeout: 8000,
        });
        const probe = await page.evaluate(() => {
            const out = [];
            document
                .querySelectorAll('#erp-logs-list .erp-log-card.fail')
                .forEach((card) => {
                    const strip = card.querySelector('.erp-log-reason');
                    const span = strip && strip.querySelector('span');
                    const cs = strip ? getComputedStyle(strip) : null;
                    out.push({
                        id: card.getAttribute('data-log-detail'),
                        text: span ? span.textContent : null,
                        display: cs ? cs.display : null,
                        visibility: cs ? cs.visibility : null,
                        opacity: cs ? cs.opacity : null,
                        h: strip ? strip.getBoundingClientRect().height : 0,
                    });
                });
            return out;
        });
        await page.screenshot({ path: path.join(OUT, `erp-errfriendly-${lang}.png`) });
        results.push({ lang, probe });
    }

    for (const lang of ['th', 'zh', 'en', 'ja']) await checkAndShot(lang);

    await browser.close();
    srv.close();

    let fail = 0;
    for (const r of results) {
        for (const c of r.probe) {
            const visible =
                c.display !== 'none' &&
                c.visibility !== 'hidden' &&
                parseFloat(c.opacity) > 0 &&
                c.h > 0;
            const friendly = c.id === 'log-dbf' ? DBF_FRIENDLY[r.lang] : STOCK_FRIENDLY[r.lang];
            const rawCode = c.id === 'log-dbf' ? RAW.dbf : RAW.stock;
            const showsFriendly = !!(c.text && c.text.includes(friendly));
            const leaksRaw = !!(c.text && c.text.includes(rawCode));
            const ok = visible && showsFriendly && !leaksRaw;
            if (!ok) fail++;
            console.log(
                `[${ok ? 'PASS' : 'FAIL'}] ${r.lang}/${c.id} visible=${visible} ` +
                    `friendly=${showsFriendly} leaksRawCode=${leaksRaw} :: "${(c.text || '').trim()}"`
            );
        }
    }
    console.log(fail === 0 ? '\n✅ ALL PASS (8/8)' : `\n🔴 ${fail} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
