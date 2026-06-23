// 录入工作台·发票任务 真浏览器验收(stub OCR/endpoints/export/push)· 驱动整条精简流。
// 跑法: node scripts/_intake_invoice_verify.cjs → tests/visual/_shot/inv-*.png
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8797;
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

// 一个 PDF 三张发票(后端 invoice_grouper 拆分)+ needs_review(可能漏票)
const RECOG = {
    ok: true, filename: '3invoices.pdf', document_type: 'tax_invoice', elapsed_ms: 10,
    page_count: 3, history_id: 'h1', history_ids: ['h1', 'h2', 'h3'], invoice_count: 3, confidence: 'low',
    needs_review: true, missed_invoice_warnings: ['maybe missed one'], duplicate_warnings: [],
    pages: [{ fields: {} }],
    invoices: [
        { history_id: 'h1', source_index: 1, source_total: 3, page_indices: [1], fields: { seller_name: 'A Co', seller_tax: '0105', invoice_number: 'INV-001', date: '2026-03-01', subtotal: '100', vat: '7', total_amount: '107', buyer_name: 'Skin', items: [{ name: 'Coffee', qty: '2', price: '60' }, { name: 'Milk', qty: '1', price: '40' }] } },
        { history_id: 'h2', source_index: 2, source_total: 3, page_indices: [2], fields: { seller_name: 'A Co', seller_tax: '0105', invoice_number: 'INV-002', date: '2026-03-02', subtotal: '200', vat: '14', total_amount: '214', buyer_name: 'Skin' } },
        { history_id: 'h3', source_index: 3, source_total: 3, page_indices: [3], fields: { seller_name: 'A Co', seller_tax: '', invoice_number: 'INV-003', date: '2026-03-03', subtotal: '300', vat: '21', total_amount: '321', buyer_name: 'Skin' } },
    ],
};
const EPS_OK = { items: [
    { id: 'e1', adapter: 'mrerp', name: 'MR.ERP 主账套', enabled: true, is_default: true },
    { id: 'e2', adapter: 'xero', name: 'Xero', enabled: false, is_default: false },
    { id: 'edms', adapter: 'mrerp_dms', name: '身份证适配器', enabled: true },
] };
const EPS_EMPTY = { items: [{ id: 'e2', adapter: 'xero', name: 'Xero', enabled: false }] };
// 复核原图查看器:/api/history/{id}/page/1.png → 真 PNG(2×2 红块,看得见即可)
const PNG = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGP8z8Dwn4EBiBkYAA8wAf/h3iEAAAAAAElFTkSuQmCC',
    'base64'
);

async function stub(page, epMode, recMode) {
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (/\/api\/history\/[^/]+\/page\/\d+\.png/.test(u))
            return route.fulfill({ status: 200, contentType: 'image/png', body: PNG });
        if (u.includes('/api/ocr/recognize')) {
            if (recMode === 'fail') return route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'server' }) });
            if (recMode === 'delay') await new Promise((r) => setTimeout(r, 900));
            return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RECOG) });
        }
        if (u.includes('/api/erp/endpoints')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(epMode === 'empty' ? EPS_EMPTY : EPS_OK) });
        if (u.includes('/api/erp/push')) return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, endpoint_name: 'MR.ERP 主账套' }) });
        if (u.includes('/api/ocr/export') || u.includes('/api/reports/history/batch_export') || u.includes('/api/erp/mrerp-xlsx-batch'))
            return route.fulfill({ status: 200, contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers: { 'X-Filename': 'out.xlsx' }, body: Buffer.from('PK') });
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true }) });
    });
}
async function boot(ctx, epMode, recMode) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 1320, height: 980 });
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'tok'));
    await stub(page, epMode, recMode);
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
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('#dx-inv-drop', { timeout: 8000 });
    // 记录 routeTo 调用(查看记录跳转验证)· 覆盖不再导航
    await page.evaluate(() => { window.__routes = []; window.routeTo = (r) => window.__routes.push(r); });
    return { page, errs };
}
const vis = (page, sel) => page.locator(sel).first().isVisible();

async function run() {
    fs.mkdirSync(OUT, { recursive: true });
    const browser = await chromium.launch();
    const ctx = await browser.newContext();
    let pass = 0, fail = 0;
    const chk = async (k, cond) => { cond = await cond; cond ? pass++ : fail++; console.log((cond ? 'PASS' : 'FAIL').padEnd(5), k); return cond; };

    // ── 全流程(有可用端点)──
    const { page, errs } = await boot(ctx, 'ok');
    // ★ 问题一:toast 必须高于所有弹窗(switcher 100000 / express 13000)· 否则弹窗内 toast 被遮
    await chk('★toast z-index 高于所有弹窗(>100000)', page.evaluate(() => {
        window.showToast('z-check', 'info');
        const w = document.getElementById('mp-toast-wrap');
        return !!w && parseInt(getComputedStyle(w).zIndex, 10) > 100000;
    }));
    await chk('默认任务=发票(卡片active)', vis(page, '.dx-opt[data-task="invoice"].active'));
    await chk('发票上传屏(拖拽区)', vis(page, '#dx-inv-drop'));
    await chk('桌面端无「拍照」按钮(仅触屏显示)', page.locator('#dx-inv-camera').count().then((n) => n === 0));
    await page.setInputFiles('#dx-inv-file', { name: '3invoices.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await page.waitForSelector('#dx-inv-start', { timeout: 5000 });
    await chk('上传后队列出现', vis(page, '.dx-qlist'));
    await chk('开始按钮无「DMS」字样', page.locator('#dx-inv-start').innerText().then((s) => !/DMS/.test(s)));
    // 去重:同文件再选一次 → 仍 1 行
    await page.setInputFiles('#dx-inv-file', { name: '3invoices.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await chk('文件去重(同文件不重复入队)', page.locator('.dx-qrow').count().then((n) => n === 1));
    await page.click('#dx-inv-start');
    await page.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });
    await chk('复核屏可见', vis(page, '#dx-s-inv-review.active'));
    await chk('复核列表1文件', page.locator('.dx-acc-item').count().then((n) => n === 1));
    await chk('★第一张自动就地展开(手风琴)', vis(page, '.dx-acc-item.open .dx-acc-panel'));
    await chk('★多发票:行显示「3 张发票」', page.locator('.dx-acc-row').first().innerText().then((s) => /3/.test(s)));
    await chk('★多发票:面板3个分组(逐张)', page.locator('.dx-inv-head').count().then((n) => n === 3));
    await chk('★needs_review 漏票 banner', vis(page, '.dx-recheck-banner'));
    await chk('第3张空税号标黄(warn)', vis(page, '.dx-rv.warn'));
    // ★ 原图查看器:图片卡 + 原图加载(page.png stub)+ 缩放
    await chk('★原图查看器可见', vis(page, '.dx-acc-item.open .dx-viewport'));
    await page.waitForFunction(() => { const i = document.querySelector('.dx-acc-item.open .dx-rimg'); return i && i.src && i.src.startsWith('blob:'); }, { timeout: 5000 }).catch(() => {});
    await chk('★原图加载成功(blob 非 noimg)', page.evaluate(() => { const c = document.querySelector('.dx-acc-item.open .dx-imgcard'); const i = document.querySelector('.dx-acc-item.open .dx-rimg'); return !!i && i.src.startsWith('blob:') && !c.classList.contains('noimg'); }));
    await page.click('.dx-acc-item.open .dx-zoom-in');
    await chk('★放大按钮改变缩放标签', page.locator('.dx-acc-item.open .dx-zoom').innerText().then((s) => s !== '100%'));
    await page.click('.dx-acc-item.open .dx-reset');
    await chk('★重置回 100%', page.locator('.dx-acc-item.open .dx-zoom').innerText().then((s) => s === '100%'));
    await page.screenshot({ path: path.join(OUT, 'inv-1review.png') });
    // ★ 展开全部字段 → 更多字段 + 明细行表
    await page.click('.dx-acc-item.open .dx-extra-toggle');
    await chk('★展开全部字段(更多字段显示)', page.locator('.dx-acc-item.open .dx-rv').count().then((n) => n >= 18));
    await chk('★展开后明细行表出现', vis(page, '.dx-acc-item.open .dx-item-tbl'));
    await page.screenshot({ path: path.join(OUT, 'inv-1review-expanded.png') });
    // ★ 原图左右切换
    await page.click('.dx-imgside-btn[data-iv-side="left"]');
    await chk('★原图切到左侧(image-left)', vis(page, '.dx-acc-item.open .dx-rgrid.image-left'));
    // ★ 确认并继续 → 视觉 ✓
    await page.click('.dx-acc-item.open .dx-confirm-one');
    await chk('★确认并继续→出现已确认✓徽标', page.locator('.dx-pill.ok').filter({ hasText: '✓' }).count().then((n) => n >= 1));
    await page.click('#dx-inv-rev-next');
    await page.waitForSelector('#dx-s-inv-submit.active', { timeout: 8000 });
    await chk('导出屏可见', vis(page, '#dx-s-inv-submit.active'));
    await chk('输出方式两卡', page.locator('.dx-choice').count().then((n) => n === 2));
    // 勾上推送 ERP
    await page.click('.dx-choice[data-iv-out="erp"]');
    await page.waitForSelector('.dx-erp', { timeout: 5000 });
    await chk('ERP端点卡(mrerp亮起)', vis(page, '.dx-erp.active'));
    await chk('mrerp_dms 被排除', page.locator('.dx-erp').filter({ hasText: '身份证' }).count().then((n) => n === 0));
    await page.screenshot({ path: path.join(OUT, 'inv-2submit.png') });
    await page.click('#dx-inv-finish');
    await page.waitForSelector('.dx-success', { timeout: 8000 });
    await chk('结果屏(成功)', vis(page, '.dx-success'));
    await page.screenshot({ path: path.join(OUT, 'inv-3success.png') });
    await chk('结果·查看记录跳 history', page.locator('#dx-inv-view-rec').click().then(() => page.evaluate(() => window.__routes.includes('history'))));
    await chk('结果·查看推送跳 integrations', page.locator('#dx-inv-view-push').click().then(() => page.evaluate(() => window.__routes.includes('integrations'))));
    await chk('无 JS 报错', Promise.resolve(errs.length === 0));
    if (errs.length) console.log('  errs:', errs.slice(0, 3));

    // ── 查看记录按钮(发票→history / 身份证→集成推送日志+筛mrerp_dms)──
    const { page: p2 } = await boot(ctx, 'ok');
    await p2.evaluate(() => {
        window.__routes = []; window.__adapter = null; window.__logsTab = false;
        window.routeTo = (r) => window.__routes.push(r);
        window.activateIntegrationsLogsTab = () => { window.__logsTab = true; };
        window.setErpLogAdapter = (a) => { window.__adapter = a; };
    });
    await p2.click('#dx-records');
    await chk('发票·查看记录→history', p2.evaluate(() => window.__routes.includes('history')));
    await p2.click('.dx-opt[data-task="identity"]');
    await p2.waitForSelector('#dx-drop', { timeout: 5000 });
    await p2.click('#dx-records');
    await p2.waitForTimeout(150);
    await chk('身份证·查看记录→集成推送日志tab', p2.evaluate(() => window.__logsTab === true));
    await chk('身份证·推送日志筛 mrerp_dms', p2.evaluate(() => window.__adapter === 'mrerp_dms'));
    await p2.close();

    // ── ERP 未配置 → 黑底指引 ──
    const { page: p3 } = await boot(ctx, 'empty');
    await p3.setInputFiles('#dx-inv-file', { name: 'a.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await p3.click('#dx-inv-start');
    await p3.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });
    await p3.click('#dx-inv-rev-next');
    await p3.waitForSelector('#dx-s-inv-submit.active', { timeout: 8000 });
    await p3.click('.dx-choice[data-iv-out="erp"]');
    await p3.waitForSelector('.dx-erp-empty', { timeout: 5000 });
    await chk('未配置→黑底指引', vis(p3, '.dx-erp-empty'));
    await chk('指引含去集成按钮', vis(p3, '#dx-inv-go-int'));
    await p3.evaluate(() => { window.__routes = []; window.routeTo = (r) => window.__routes.push(r); });
    await p3.click('#dx-inv-go-int');
    await chk('点指引→integrationss', p3.evaluate(() => window.__routes.includes('integrations')));
    await p3.screenshot({ path: path.join(OUT, 'inv-4erp-empty.png') });
    await p3.close();
    await page.close();

    // ── Pass2:停止按钮(延迟 stub)──
    const { page: pStop } = await boot(ctx, 'ok', 'delay');
    await pStop.setInputFiles('#dx-inv-file', { name: 's.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await pStop.click('#dx-inv-start');
    await pStop.waitForSelector('#dx-s-searching.active', { timeout: 5000 });
    await chk('Pass2·识别中显示停止按钮', vis(pStop, '#dx-inv-stop'));
    await pStop.click('#dx-inv-stop');
    await pStop.close();

    // ── Pass2:失败→重试按钮(500 stub)──
    const { page: pFail } = await boot(ctx, 'ok', 'fail');
    await pFail.setInputFiles('#dx-inv-file', { name: 'f.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await pFail.click('#dx-inv-start');
    await pFail.waitForSelector('.dx-qrow', { timeout: 8000 });
    await chk('Pass2·失败留在上传屏', vis(pFail, '#dx-s-upload.active'));
    await chk('Pass2·失败文件有重试按钮', vis(pFail, '[data-iv-retry]'));
    await pFail.close();

    // ── Pass2:图片→PDF(上传 png 不报错、入队)──
    const { page: pImg, errs: ie } = await boot(ctx, 'ok');
    // 1×1 png
    const pngB64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
    await pImg.setInputFiles('#dx-inv-file', { name: 'photo.png', mimeType: 'image/png', buffer: Buffer.from(pngB64, 'base64') });
    await pImg.waitForTimeout(800); // 等 imagesToPdf 转换
    await chk('Pass2·图片入队(转PDF或原图)', pImg.locator('.dx-qrow').count().then((n) => n === 1));
    await chk('Pass2·图片处理无JS报错', Promise.resolve(ie.length === 0));
    if (ie.length) console.log('  img errs:', ie.slice(0, 2));
    await pImg.close();

    // ── 手机视口截图 ──
    const m = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
    const { page: mp } = await (async () => { const r = await boot(m, 'ok'); return r; })();
    await mp.setInputFiles('#dx-inv-file', { name: 'a.pdf', mimeType: 'application/pdf', buffer: Buffer.from('x') });
    await mp.click('#dx-inv-start');
    await mp.waitForSelector('#dx-s-inv-review.active', { timeout: 8000 });
    await mp.screenshot({ path: path.join(OUT, 'inv-m-review.png'), fullPage: true });
    await mp.close();

    await browser.close();
    console.log(`\n结果: ${pass} PASS / ${fail} FAIL`);
    process.exit(fail ? 1 : 0);
}
serve().then(run).catch((e) => { console.error(e); process.exit(1); });
