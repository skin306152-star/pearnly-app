/*
 * scripts/_wizard_zero_price_verify.cjs · 开票向导「฿0 税票开不出去」的真浏览器验收
 *
 * 为什么不是单测:这条路的判据分散在四个地方 —— 卡片画什么、点下去加不加行、合规清单过不过、
 * 「开出发票」那一下到底有没有 POST 出去。挨个断函数返回值全都能绿,而店员真点下去照样能开出
 * 一张 ฿0 的税票(三轮就是这么过的)。所以这里跑的是真 Chromium + 真 DOM + 真 click:
 * 判据是【点完之后网络上有没有那一发 /issue】,不是某个函数回了什么。
 *
 * 向导是自含模块(window.openSalesWizard),不依赖 SPA 启动,故用 esbuild 现打一份进空白页 ——
 * 装的是 src/home/*.ts 本体,不是 dist 里那份可能过期的产物。
 *
 * 用法(仓库根目录):
 *   node scripts/_wizard_zero_price_verify.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/sales_wizard_zero_price/。
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const esbuild = require('esbuild');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/sales_wizard_zero_price')
);
const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.html': 'text/html' };

// 目录里的两件货:一件挂了 ฿120,一件没设价(扫码就地建品建出来的就长这样)。
const PRODUCTS = [
    { id: 'p-cola', name_th: 'โค้ก 325ml', unit_price: 120, vat_applicable: true },
    { id: 'p-new', name_th: 'นมสด 200ml', unit_price: null, vat_applicable: true },
];

async function bundle() {
    // Vite 约定:TS 之间用 './x.js' 互相 import,落盘的是 x.ts。
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
    const server = http.createServer((req, res) => {
        const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '');
        if (rel === 'wizard.js') {
            res.writeHead(200, { 'content-type': 'text/javascript' });
            res.end(js);
            return;
        }
        const fp = path.join(ROOT, rel);
        if (!fp.startsWith(ROOT) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
            res.writeHead(200, { 'content-type': 'text/html' });
            res.end(
                '<!doctype html><meta charset="utf-8"><title>wizard</title>' +
                    // 令牌层要一起装:向导那层只写 var(--amber),令牌不在时颜色静默回落成黑色,
                    // 「屏上看不看得出这货没设价」就验成了一句空话。
                    '<link rel="stylesheet" href="/static/home-01-base.css">' +
                    '<link rel="stylesheet" href="/static/home-40-sales-wizard.css"><body>'
            );
            return;
        }
        res.writeHead(200, {
            'content-type': MIME[path.extname(fp)] || 'application/octet-stream',
        });
        fs.createReadStream(fp).pipe(res);
    });
    return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

// 页面里的宿主桩:向导要的全局就这几个。网络在 apiGet/apiPost 截断,发出去的每一发都留证。
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
        return {
            ok: true,
            status: 200,
            json: async () => ({ document: { id: 'doc-1' }, product: { id: 'new-1' } }),
        };
    };
}

async function open(browser, origin, products) {
    const page = await browser.newPage({ viewport: { width: 1180, height: 900 } });
    page.on('pageerror', (e) => {
        throw e;
    });
    await page.addInitScript(hostStubs, products);
    await page.goto(`${origin}/`);
    await page.addScriptTag({ url: '/wizard.js' });
    await page.evaluate(() => window.openSalesWizard());
    await page.waitForSelector('.sw-stepper');
    return page;
}

const shot = (page, name) => page.screenshot({ path: path.join(SHOTS, name), fullPage: false });

/**
 * 填一个框然后让它落定。
 *
 * 向导有几个框是 onblur=render:失焦就整屏重画。直接 fill 完点下一个元素,blur 会在
 * mousedown 与 mouseup 之间把按钮换掉 —— 那一下点在了已经脱离文档的节点上,人看起来
 * 像"按钮没反应"。真店员打完字停顿一下再点,所以这里也照真人那样先落定。
 */
async function type(page, sel, value) {
    await page.fill(sel, value);
    await page.evaluate(() => document.activeElement && document.activeElement.blur());
    await page.waitForTimeout(60);
}

// 第 1 步 → 第 3 步(商品菜单)。买方那步先填齐,免得后面被别的闸挡住看不出是谁拦的。
async function toGoodsStep(page) {
    await page.click('#sw-next');
    await type(page, '#sw-bname', 'บริษัท ทดสอบ จำกัด');
    await type(page, '#sw-baddr', '1 ถนนสุขุมวิท กรุงเทพฯ');
    await type(page, '#sw-btin', '0105500000001');
    await page.click('#sw-next');
    await page.waitForSelector('.sw-pcard');
}

/**
 * 第 3 步 → 第 5 步 → 点「开出发票」。
 *
 * 合规清单要在【点之前】读:拦下来时向导会跳回出问题的那一步,点完再读就读不到第 5 步了。
 * 回的三样正是店员看得见的全部 —— 清单上哪条红了、发出去几发、被送回了第几步。
 */
async function issue(page) {
    await page.click('#sw-next');
    await page.click('#sw-next');
    await page.waitForSelector('.sw-checks');
    const failing = await page.$$eval('.sw-check.fail .sw-ct', (els) =>
        els.map((e) => e.innerText.trim())
    );
    await page.click('#sw-next');
    await page.waitForTimeout(300);
    return page.evaluate(
        (checks) => ({
            posted: window.__posted.map((p) => p.url),
            checks,
            toast: (window.__toasts[window.__toasts.length - 1] || [''])[0],
            // 开成功时向导整屏换成结果页,步骤条就没了 —— 那本身就是「开出去了」的证据
            step: (
                document.querySelector('.sw-step.active .sw-lbl') || { innerText: '' }
            ).innerText.trim(),
        }),
        failing
    );
}

const fail = (msg) => {
    throw new Error(msg);
};

// ── ① 没设价的商品:卡片不画 ฿0.00,点下去也进不了发票行 ──────────────────
async function unpricedCard(browser, origin) {
    const page = await open(browser, origin, PRODUCTS);
    await toGoodsStep(page);

    const cards = await page.$$eval('.sw-pcard', (els) =>
        els.map((el) => {
            const box = el.querySelector('.sw-pp');
            // 量【真在画这行字的那个元素】,不是外层容器:颜色挂在内层 span 上时,量容器
            // 两张卡永远同色,这条断言就成了摆设(判据量错东西的迷你版)。
            const painted = box.querySelector('*') || box;
            return {
                name: el.querySelector('.sw-pn').innerText.trim(),
                price: box.innerText.trim(),
                color: getComputedStyle(painted).color,
                marked: el.classList.contains('noprice'),
            };
        })
    );
    await shot(page, '01-unpriced-card.png');

    const bad = cards.find((c) => c.name.indexOf('นมสด') >= 0);
    if (!bad) fail('没找到那件没设价的货');
    if (/0\.00/.test(bad.price)) fail(`没设价被画成了 ฿0.00:${bad.price}`);
    if (!bad.marked) fail('没设价的卡片没有 noprice 标记');
    const ok = cards.find((c) => c.name.indexOf('โค้ก') >= 0);
    if (!/120/.test(ok.price)) fail(`挂了价的卡片没画出价:${ok.price}`);
    // 「未设价」得在屏上真显出提示色,不能跟正常价一个颜色 —— 类名对了颜色没生效等于没提示
    if (bad.color === ok.color) fail(`未设价与正常价同色(${bad.color}),屏上分不出来`);

    // 点它:不许进购物车,而且要说清为什么 + 指出路
    await page.click('.sw-pcard.noprice');
    await page.waitForTimeout(150);
    const after = await page.evaluate(() => ({
        lines: document.querySelectorAll('.sw-citem').length,
        toasts: window.__toasts.map((t) => t[0]),
    }));
    await shot(page, '02-unpriced-click-refused.png');
    if (after.lines !== 0) fail('没设价的货被加进了发票行');
    if (!after.toasts.length) fail('点下去什么都没说 —— 店员只会以为卡片坏了');
    await page.close();
    return { cardPrice: bad.price, color: bad.color, toast: after.toasts[0] };
}

// ── ② 唯一一行没设价 → 「开出发票」一发都不许出去 ────────────────────────
async function zeroInvoiceBlocked(browser, origin) {
    const page = await open(browser, origin, PRODUCTS);
    await toGoodsStep(page);
    // 自定义行:只填名字不填价(店员抱着货只输个名字,就是这条最常走的路)
    await page.click('#sw-addcustom');
    await type(page, '.sw-citem input[data-f="desc"]', 'ของทดลอง');

    const cart = await page.$eval('.sw-citem', (el) => ({
        priceBox: el.querySelector('input[data-f="price"]').value,
        amount: el.querySelector('.sw-amt').innerText.trim(),
    }));
    if (cart.priceBox !== '') fail(`新行预填了价:${cart.priceBox}`);
    if (/0\.00/.test(cart.amount)) fail(`没设价的行金额画成了 ฿0.00:${cart.amount}`);

    const r = await issue(page);
    await shot(page, '03-zero-invoice-blocked.png');
    if (r.posted.some((u) => /\/issue$/.test(u))) fail(`฿0 的税票被开出去了:${r.posted.join(' ')}`);
    if (r.posted.length) fail(`拦住了却还发了请求:${r.posted.join(' ')}`);
    if (!r.checks.length) fail('合规清单一条红的都没有 —— 人不知道差在哪');
    if (!r.toast) fail('拦住了却一声不吭 —— 店员只会以为「开出」这个按钮坏了');
    // 送回商品那一步:光说"差点什么"不指路,人得自己找是哪一行
    if (r.step.indexOf('รายการสินค้า') < 0) fail(`没送回商品明细那一步:${r.step}`);
    await page.close();
    return r;
}

// ── ③ 真的赠品(人手打的 ฿0)照旧开得出去 ───────────────────────────────
async function explicitGiftIssues(browser, origin) {
    const page = await open(browser, origin, PRODUCTS);
    await toGoodsStep(page);
    await page.click('.sw-pcard:not(.noprice)'); // ฿120 那件
    await page.click('#sw-addcustom');
    const gift = '.sw-citem:last-child ';
    await type(page, gift + 'input[data-f="desc"]', 'ของแถม');
    // 人自己打的 0 = 老板拍过板的价,票面上看得见 —— 与"没设价"必须是两件事
    await type(page, gift + 'input[data-f="price"]', '0');

    const r = await issue(page);
    await shot(page, '04-explicit-gift-issued.png');
    if (!r.posted.some((u) => /\/issue$/.test(u)))
        fail(`人手打的 ฿0 赠品被当成"没设价"拦掉了:${r.posted.join(' ') || '(一发都没发)'}`);
    if (r.checks.length) fail(`赠品单在合规清单上被标红了:${r.checks.join(' · ')}`);
    // 发出去的那一单里,赠品行的价必须是 0(不是被悄悄改成别的,也不是整行丢掉)
    const body = await page.evaluate(() =>
        window.__posted.map((p) => p.body).find((b) => b && b.lines)
    );
    const lines = (body && body.lines) || [];
    if (lines.length !== 2) fail(`发票行数不对:${JSON.stringify(lines)}`);
    if (lines.filter((l) => Number(l.unit_price) === 0).length !== 1)
        fail(`赠品那一行的 ฿0 没原样发出去:${JSON.stringify(lines)}`);
    await page.close();
    return { posted: r.posted, lines };
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve(await bundle());
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const out = {};
    try {
        out.unpricedCard = await unpricedCard(browser, origin);
        out.zeroInvoiceBlocked = await zeroInvoiceBlocked(browser, origin);
        out.explicitGiftIssues = await explicitGiftIssues(browser, origin);
    } finally {
        await browser.close();
        server.close();
    }
    fs.writeFileSync(path.join(SHOTS, 'report.json'), JSON.stringify(out, null, 2));
    console.log(JSON.stringify(out, null, 2));
    console.log('PASS · 截图 ' + SHOTS);
})().catch((e) => {
    console.error('FAIL ·', e.message);
    process.exit(1);
});
