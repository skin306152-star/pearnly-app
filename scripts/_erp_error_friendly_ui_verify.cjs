// 真浏览器验收 · F1 错误码四语友好文案(推送日志页真实点击流)。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo 捷径)→ 桩三条失败日志
// (DBF_WRITE_FAILED / STOCK_IN_FAILED / STOCK_ITEM_NOT_FOUND · error_friendly 用后端 friendly_any 真实输出)→
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
    zh: '写入 Express 账套失败 · 常见于该账套还没有库存商品主档 · 请先在 Express 建好库存商品,或本批改用「服务·非库存」模式推送',
    en: 'Failed to write into the Express account set — commonly because the set has no stock-item master yet. Please create a stock item in Express first, or push this batch in the “Service · Non-stock” mode.',
    th: 'เขียนข้อมูลลงชุดบัญชี Express ไม่สำเร็จ มักเป็นเพราะชุดบัญชียังไม่มีสินค้าคงคลังตั้งต้น กรุณาสร้างสินค้าคงคลังใน Express ก่อน หรือส่งชุดนี้ด้วยโหมด «บริการ · ไม่ใช่สินค้าคงคลัง»',
    ja: 'Express の帳簿セットへの書き込みに失敗しました。多くは在庫品マスタが未作成のためです。先に Express で在庫品を作成するか、本バッチを「サービス・非在庫」モードで送信してください。',
};
const STOCKIN_FRIENDLY = {
    zh: '这张进货票没能入库 · 请依次检查:票里库存品和非库存品是否混在一起(混了就拆成两张分别推)· 明细行的数量/金额是否与票面一致 · 账套是否已配存货和销售成本科目',
    en: 'This purchase invoice could not be booked into stock. Check in order: stock and non-stock lines mixed on one invoice (split them and push separately), line quantities/amounts not matching the invoice, and whether the account set has inventory and COGS accounts configured.',
    th: 'ใบซื้อนี้ลงสต๊อกไม่สำเร็จ กรุณาตรวจตามลำดับ: มีสินค้าคงคลังปนกับสินค้าที่ไม่ใช่คงคลังในใบเดียวกันหรือไม่ (ถ้าปนให้แยกเป็นสองใบแล้วส่งแยกกัน) · จำนวนและมูลค่าในรายการตรงกับหน้าใบหรือไม่ · ชุดบัญชีตั้งบัญชีสินค้าคงเหลือและต้นทุนขายแล้วหรือยัง',
    ja: 'この仕入請求書は在庫計上できませんでした。順に確認してください:1 枚に在庫品と非在庫品が混在していないか(混在なら 2 枚に分けて送信)· 明細の数量/金額が請求書と一致しているか · 会計セットに棚卸資産と売上原価の勘定が設定されているか。',
};
const STOCK_FRIENDLY = {
    zh: '这件商品在 Express 里还没有库存档案,或库存为零/不足 · 请先把它的进货票用「库存」模式推一次(或补录期初库存),再推这张销售票',
    en: 'This item has no stock record in Express yet, or its stock is zero/insufficient. Push its purchase invoice in Inventory mode first (or fill in the opening balance), then push this sales invoice again.',
    th: 'สินค้านี้ยังไม่มีทะเบียนสต๊อกใน Express หรือสต๊อกเป็นศูนย์/ไม่เพียงพอ กรุณาส่งใบซื้อของสินค้านี้ด้วยโหมดสินค้า (คงคลัง) ก่อน หรือกรอกยอดยกมา แล้วจึงส่งใบขายนี้อีกครั้ง',
    ja: 'この商品は Express に在庫マスタが未登録、または在庫がゼロ/不足です。先にこの商品の仕入請求書を在庫モードで送信するか期首在庫を登録してから、この売上請求書を再送信してください。',
};
const ACCGRP_FRAGMENTS = {
    zh: '选存货科目组',
    en: 'inventory account group',
    th: 'เลือกกลุ่มบัญชีสินค้า',
    ja: '在庫勘定グループを選択',
};
// 卡片 id → {期望文案, 不得裸露的原始码}
const EXPECT = {
    'log-dbf': { friendly: DBF_FRIENDLY, raw: 'DBF_WRITE_FAILED' },
    'log-stockin': { friendly: STOCKIN_FRIENDLY, raw: 'STOCK_IN_FAILED' },
    'log-stock': { friendly: STOCK_FRIENDLY, raw: 'STOCK_ITEM_NOT_FOUND' },
    // 只钉各语种的判别片段(全文单一源在 static/i18n-data.js,别在这儿抄第二份)。
    'log-accgrp': { friendly: ACCGRP_FRAGMENTS, raw: 'stock_acc_group_required' },
};

const LOGS = {
    total: 3,
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
            id: 'log-stockin',
            status: 'failed',
            trigger: 'manual',
            push_type: 'invoice',
            invoice_no: 'PU69/00120',
            endpoint_name: 'Express',
            ocr_buyer_name: 'บจก. ตัวอย่าง',
            created_at: new Date().toISOString(),
            error_msg: 'STOCK_IN_FAILED 采购入库失败',
            error_friendly: STOCKIN_FRIENDLY,
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
        {
            id: 'log-accgrp',
            status: 'failed',
            trigger: 'manual',
            push_type: 'invoice',
            invoice_no: 'IV69/00473',
            endpoint_name: 'Express',
            ocr_buyer_name: 'บจก. ตัวอย่าง',
            created_at: new Date().toISOString(),
            // preflight 的 EXPRESS_MANUAL 原因码:后端不产 error_friendly,靠前端码→i18n 映射。
            // 生产日志 47a281c8 就是漏了映射,裸码直接怼到会计脸上。
            error_msg: 'EXPRESS_MANUAL: stock_acc_group_required',
            http_status: 0,
            retry_count: 0,
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
        st.textContent =
            '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
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
            document.querySelectorAll('#erp-logs-list .erp-log-card.fail').forEach((card) => {
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
    let total = 0;
    for (const r of results) {
        for (const c of r.probe) {
            total++;
            const visible =
                c.display !== 'none' &&
                c.visibility !== 'hidden' &&
                parseFloat(c.opacity) > 0 &&
                c.h > 0;
            const exp = EXPECT[c.id] || {};
            const friendly = (exp.friendly || {})[r.lang];
            const showsFriendly = !!(friendly && c.text && c.text.includes(friendly));
            const leaksRaw = !!(exp.raw && c.text && c.text.includes(exp.raw));
            const ok = visible && showsFriendly && !leaksRaw;
            if (!ok) fail++;
            console.log(
                `[${ok ? 'PASS' : 'FAIL'}] ${r.lang}/${c.id} visible=${visible} ` +
                    `friendly=${showsFriendly} leaksRawCode=${leaksRaw} :: "${(c.text || '').trim()}"`
            );
        }
    }
    console.log(fail === 0 ? `\n✅ ALL PASS (${total}/${total})` : `\n🔴 ${fail} FAIL`);
    process.exit(fail === 0 ? 0 : 1);
})().catch((e) => {
    console.error(e);
    process.exit(2);
});
