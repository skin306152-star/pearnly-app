// 批次一 UI 验收(真浏览器 · 泰语):① 库存前置闸的转人工原因在推送日志卡上显示成人话,
// 不裸露英文码;② 删推送日志的确认弹窗必须写明「删了这票可以再推一次」。
// 跑法: node scripts/_stock_guard_ui_verify.cjs → tests/visual/_shot/stockguard-*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8801;
const TYPES = { '.js': 'application/javascript', '.css': 'text/css', '.html': 'text/html', '.map': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.ico': 'image/x-icon' };

function serve() {
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'text/plain', 'cache-control': 'no-store' });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

// 一条被库存前置闸拦下的销项推送(status=manual · 后端 fail 的规范 reason 走 EXPRESS_MANUAL 哨兵)
const LOGS = {
    total: 1,
    items: [{
        id: 'log-1', endpoint_id: 'e1', history_id: 'h1', invoice_no: 'IV69/00473',
        seller_name: 'บริษัท ซินเซียร์ไอซ์ จำกัด', total_amount: 941.6,
        status: 'manual', http_status: 0,
        error_msg: 'EXPRESS_MANUAL: stock_no_master_in_account_set',
        attempt: 1, elapsed_ms: 12, trigger: 'manual',
        created_at: '2026-07-23T13:30:00+00:00',
        retry_count: 0, max_retries: 3, next_retry_at: null,
        endpoint_name: 'Express', endpoint_adapter: 'express',
        push_type: 'invoice', category: '', error_code: '',
    }],
};
const EPS = { items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, is_default: true }] };

async function boot(ctx) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 1320, height: 980 });
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/erp/logs?'))
            return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(LOGS) });
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EPS) });
        if (u.includes('/api/erp/stats/today'))
            return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ total: 1, success: 0, failed: 0, auto_cnt: 0 }) });
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, items: [] }) });
    });
    const errs = [];
    page.on('pageerror', (e) => errs.push(String(e)));
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 });
    await page.evaluate(() => {
        window.isOwner = () => true;
        window._userInfo = Object.assign(window._userInfo || {}, { can_push_erp: true, plan: 'lifetime' });
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
        window.routeTo('push-logs');
    });
    await page.waitForSelector('[data-log-detail="log-1"]', { timeout: 15000 });
    return { page, errs };
}

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext();
    let pass = 0, fail = 0;
    const chk = async (k, cond) => { cond = await cond; cond ? pass++ : fail++; console.log((cond ? 'PASS' : 'FAIL').padEnd(5), k); };

    const { page, errs } = await boot(ctx);

    // ① 卡片显示泰语人话,不裸露英文码
    const card = page.locator('[data-log-detail="log-1"]').first();
    const cardText = await card.innerText();
    await chk('显示泰语原因(สินค้าคงคลัง)', cardText.includes('สินค้าคงคลัง'));
    await chk('提到要先建库存商品 / 录进货或期初', cardText.includes('ใบซื้อ') || cardText.includes('ยอดยกมา'));
    await chk('不裸露英文码 stock_no_master_in_account_set', !cardText.includes('stock_no_master_in_account_set'));
    await chk('原因文字真的画出来了(非零高度)', page.evaluate(() => {
        const el = document.querySelector('[data-log-detail="log-1"]');
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.height > 40 && getComputedStyle(el).visibility === 'visible';
    }));
    await page.screenshot({ path: path.join(OUT, 'stockguard-1-card.png') });

    // ② 删除确认弹窗必须写明「删了可以再推一次」
    await page.locator('[data-log-cb="log-1"]').first().check();
    await page.waitForSelector('#erp-logs-batch-bar:not([style*="display: none"])', { timeout: 5000 });
    await page.locator('#btn-erp-batch-delete').first().click();
    // 面板有淡入动画:不等它停就截图会拍到半透明面板(底下内容透出来 · 像渲染坏了)。
    // 等到 opacity=1 同时蕴含「弹窗已出现且有尺寸」,故只需这一段等待。
    await page.waitForFunction(
        () => {
            const box = document.querySelector('#confirm-modal .modal');
            return !!box && box.getBoundingClientRect().height > 0 && getComputedStyle(box).opacity === '1';
        },
        { timeout: 5000 }
    );
    const dlg = await page.evaluate(() => {
        const body = document.getElementById('confirm-modal-body');
        return {
            text: body.innerText,
            boxBg: getComputedStyle(document.querySelector('#confirm-modal .modal')).backgroundColor,
            // 文案变长后面板会不会撑破/裁掉:body 内容高度须完全落在面板内
            bodyOverflow: body.scrollHeight - body.clientHeight,
        };
    });
    await chk('确认弹窗有文案', dlg.text.trim().length > 10);
    await chk('弹窗写明「可以再送一次 ERP」(ซ้ำ/ERP)', dlg.text.includes('ERP') && dlg.text.includes('ซ้ำ'));
    await chk('面板不透明(底下内容不透出)', dlg.boxBg === 'rgb(255, 255, 255)');
    await chk('加长文案没撑破面板(body 无裁切)', dlg.bodyOverflow <= 0);
    await page.screenshot({ path: path.join(OUT, 'stockguard-2-delete-confirm.png') });

    await chk('零 console pageerror', errs.length === 0);
    if (errs.length) console.log('pageerror:', errs.slice(0, 3));

    await browser.close();
    srv.close();
    console.log(`\n${pass} pass / ${fail} fail · 截图 ${OUT}`);
    process.exit(fail ? 1 : 0);
}
run();
