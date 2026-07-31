/*
 * scripts/_r4_wizard_zero_total_verify.cjs · 第四轮对抗:每一行都有价,合计还是 ฿0
 *
 * 本轮那份验收(_wizard_zero_price_verify.cjs)打的是「某一行【没设价】」。前端合规清单里
 * 对应的那条叫 ckPrice,判据是 billableLines(st).every(l => priced(l.price)) —— 每一行有没有
 * 价。而后端那道闸(services/sales/issue_gates.amount_gate)判的是【合计 > 0】。两条不是同一
 * 件事,中间夹着一整类真实单据:
 *   z1 giftOnly    整单只有一行,店员自己打的 ฿0(试用装/整单赠送)
 *   z2 fullDiscount 一行 ฿120,整单折扣打到 120(谈成免单)
 * 两种在前端都「每一行都有价」,ckPrice 全绿 —— 于是「开出发票」按下去,草稿真的建出来了,
 * 然后才被后端顶回来。本脚本量的就是这一段:发出去了几发、店员屏上看到的是什么。
 *
 * 后端桩照 amount_gate 的真口径回:grand_total <= 0 → 400 zero_amount。桩只在网络这一层,
 * 页面里跑的是 src/home/sales-wizard*.ts 本体(esbuild 现打,不吃 dist 里可能过期的产物)。
 *
 * 跑法(仓库根目录):node scripts/_r4_wizard_zero_total_verify.cjs
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const esbuild = require('esbuild');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.join(ROOT, 'tests/e2e/_artifacts/pos_barcode_scan/fix3');
const PRODUCTS = [{ id: 'p-cola', name_th: 'โค้ก 325ml', unit_price: 120, vat_applicable: true }];

async function bundle() {
    const tsExt = {
        name: 'ts-ext',
        setup(build) {
            build.onResolve({ filter: /^\.\/.*\.js$/ }, (args) => {
                const p = path.resolve(args.resolveDir, args.path.replace(/\.js$/, '.ts'));
                return fs.existsSync(p) ? { path: p } : undefined;
            });
        },
    };
    const built = await esbuild.build({
        entryPoints: [path.join(ROOT, 'src/home/sales-wizard.ts')],
        bundle: true,
        format: 'iife',
        write: false,
        plugins: [tsExt],
    });
    return built.outputFiles[0].text;
}

function serve(js) {
    const MIME = { '.js': 'text/javascript', '.css': 'text/css' };
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        if (rel === 'wizard.js') {
            res.writeHead(200, { 'content-type': 'text/javascript' });
            return res.end(js);
        }
        const fp = path.join(ROOT, rel);
        if (!fp.startsWith(ROOT) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
            res.writeHead(200, { 'content-type': 'text/html' });
            return res.end(
                '<!doctype html><meta charset="utf-8"><title>wizard</title>' +
                    '<link rel="stylesheet" href="/static/home-01-base.css">' +
                    '<link rel="stylesheet" href="/static/home-40-sales-wizard.css"><body>'
            );
        }
        res.writeHead(200, {
            'content-type': MIME[path.extname(fp)] || 'application/octet-stream',
        });
        fs.createReadStream(fp).pipe(res);
    });
    return new Promise((r) => server.listen(0, '127.0.0.1', () => r(server)));
}

// 后端桩照 issue_gates.amount_gate 的真口径:合计 ≤ 0 的税票不给号。
function hostStubs(products) {
    window.__posted = [];
    window.__toasts = [];
    window.escapeHtml = (s) =>
        String(s == null ? '' : s).replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
        );
    window.showToast = (msg, kind) => window.__toasts.push([String(msg), kind || '']);
    window.apiGet = async (url) => {
        if (url.indexOf('/sellers') >= 0)
            return { sellers: [{ id: 1, name: 'ร้านทดสอบ', tax_id: '0105500000001', branch: '' }] };
        return { products };
    };
    window.apiPost = async (url, body) => {
        window.__posted.push({ url: String(url), body });
        if (/\/issue$/.test(String(url))) {
            const g = Number((window.__lastDoc && window.__lastDoc.grand_total) || 0);
            if (!(g > 0))
                return {
                    ok: false,
                    status: 400,
                    json: async () => ({ detail: 'zero_amount' }),
                };
        }
        if (/\/documents$/.test(String(url))) window.__lastDoc = body;
        return {
            ok: true,
            status: 200,
            json: async () => ({ document: { id: 'doc-1' }, product: { id: 'new-1' } }),
        };
    };
}

async function open(browser, origin) {
    const page = await browser.newPage({ viewport: { width: 1180, height: 900 } });
    page.on('pageerror', (e) => {
        throw e;
    });
    await page.addInitScript(hostStubs, PRODUCTS);
    await page.goto(`${origin}/`);
    await page.addScriptTag({ url: '/wizard.js' });
    await page.evaluate(() => window.openSalesWizard());
    await page.waitForSelector('.sw-stepper');
    return page;
}

async function type(page, sel, value) {
    await page.fill(sel, value);
    await page.evaluate(() => document.activeElement && document.activeElement.blur());
    await page.waitForTimeout(60);
}

async function toGoodsStep(page) {
    await page.click('#sw-next');
    await type(page, '#sw-bname', 'บริษัท ทดสอบ จำกัด');
    await type(page, '#sw-baddr', '1 ถนนสุขุมวิท กรุงเทพฯ');
    await type(page, '#sw-btin', '0105500000001');
    await page.click('#sw-next');
    await page.waitForSelector('.sw-pcard');
}

async function issue(page, name) {
    await page.click('#sw-next');
    await page.click('#sw-next');
    await page.waitForSelector('.sw-checks');
    const failing = await page.$$eval('.sw-check.fail .sw-ct', (els) =>
        els.map((e) => e.innerText.trim())
    );
    const grandOnScreen = await page.evaluate(() =>
        (document.querySelector('.sw-tr.grand .v') || { innerText: '' }).innerText.trim()
    );
    await page.click('#sw-next');
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
    return page.evaluate(
        ([checks, grand]) => ({
            posted: window.__posted.map((p) => p.url),
            failingChecks: checks,
            grandOnScreen: grand,
            grandSent: (window.__lastDoc || {}).grand_total,
            toast: (window.__toasts[window.__toasts.length - 1] || [''])[0],
            step: (
                document.querySelector('.sw-step.active .sw-lbl') || { innerText: '' }
            ).innerText.trim(),
        }),
        [failing, grandOnScreen]
    );
}

// ── z1 · 整单只有一行赠品(店员自己打的 ฿0)────────────────────────────────
async function giftOnly(browser, origin) {
    const page = await open(browser, origin);
    await toGoodsStep(page);
    await page.click('#sw-addcustom');
    await type(page, '.sw-citem input[data-f="desc"]', 'ของแถม');
    await type(page, '.sw-citem input[data-f="price"]', '0');
    const r = await issue(page, 'z1-gift-only-zero-total.png');
    await page.close();
    return r;
}

// ── z2 · 一行 ฿120,整单折扣打到 120 ───────────────────────────────────────
async function fullDiscount(browser, origin) {
    const page = await open(browser, origin);
    await toGoodsStep(page);
    await page.click('.sw-pcard');
    const discSel = '#sw-hdisc';
    const hasDisc = (await page.$(discSel)) !== null;
    if (hasDisc) await type(page, discSel, '120');
    const r = await issue(page, 'z2-full-discount-zero-total.png');
    await page.close();
    return Object.assign({ hasDiscountBox: hasDisc }, r);
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve(await bundle());
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const out = {};
    try {
        out.z1_giftOnly = await giftOnly(browser, origin);
        out.z2_fullDiscount = await fullDiscount(browser, origin);
    } finally {
        await browser.close();
        server.close();
    }
    // 判据只认「钱」那一层:฿0 的单有没有拿到票号、店员知不知道差在哪、被送回的是不是能改
    // 的那一步。「走没走到 /issue」不当判据 —— 前端 ckPrice 只管每行有没有价,合计那条按设计
    // 就在后端(sales-wizard.ts 的 SERVER_ERR 里写着「前端 ckPrice 漏掉的走这条兜底」),
    // 而后端那道闸跑在 numbering.allocate 之前,不占号。把它记成事实,不记成失败。
    for (const [k, v] of Object.entries(out)) {
        v.reachedIssue = v.posted.some((u) => /\/issue$/.test(u));
        v.gotNumber = /result|success/i.test(v.step) || v.step === '';
        v.ok = !!v.toast && v.step.indexOf('รายการสินค้า') >= 0;
        console.log(
            `${v.ok ? 'PASS' : 'FAIL'} ${k} · 走到 /issue=${v.reachedIssue} · ` +
                `送回「${v.step}」· 说了「${v.toast.slice(0, 40)}」`
        );
    }
    fs.writeFileSync(
        path.join(SHOTS, 'report-r4-wizard-zero-total.json'),
        JSON.stringify(out, null, 2)
    );
    console.log(JSON.stringify(out, null, 2));
    process.exit(Object.values(out).every((v) => v.ok) ? 0 : 1);
})().catch((e) => {
    console.error('R4 WIZARD ZERO TOTAL CRASH', e);
    process.exit(2);
});
