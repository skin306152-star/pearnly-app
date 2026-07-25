// 真浏览器验收 · 录入工作台 step① 侧栏 + step③ 复核屏(真实点击流)。
//   ① 侧栏:「当前流程」「设计原则」两个纯文案框已删;进项/销项 与 服务/库存 两级声明在位、可选可取消。
//   ② 声明真的随请求走:抓 /api/ocr/recognize 的 multipart 体,断言 direction / posting_kind 在里面。
//   ③ 复核卡按方向取对手方:销项票「名称/税号」必须是买方的值(此前写死 seller_* → 销项显示空 + 需确认)。
//   ④ 明细四列:数量/单价/金额各归各位(此前「金额」列显示的是单价),且可编辑、改了进 IV.results。
//   ⑤ 走库存路时明细默认摊开(它是要建 STMAS 主档的主数据,不是附加信息)。
//   ⑥ 查看器:sticky 钉住 + 聚焦第 N 张字段 → 翻到该张 page_indices[0] + 左侧该组高亮。
// 走真实导航:/home → 点左栏「录入工作台」nav-item(禁 routeTo)→ 真 setInputFiles → 真点开始。
// 断言一律 getComputedStyle / 真值,禁 grep 类名。四语截图 → tests/visual/_shot/dms-intake-review-*.png。
// 模型抄 scripts/_erp_stock_honesty_ui_verify.cjs。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8829;
const LANGS = ['th', 'zh', 'en', 'ja'];
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

// 期望文案读 static/i18n-data.js(单一源)· 抄第二份进脚本必漂。
global.window = global.window || {};
require(path.join(ROOT, 'static/i18n-data.js'));
const I18N = global.window.I18N;
const tr = (lang, key) => I18N[lang][key];

const BUYER = 'บริษัท กันยารัตน์ คอร์ปอเรชั่น จำกัด';
const BUYER_TAX = '0735563002423';
const SELLER = 'บริษัท ซินเซียร์ ไอซ์ จำกัด';
const SELLER_TAX = '0105546015062';
// 3 张票散在 2 个物理页 —— 这正是用户报的场景(查看器停在第 1 页,三张共用一个画面)。
const PAGES_OF = [[1], [1], [2]];
const inv = (i) => ({
    history_id: 'h' + i,
    source_index: i + 1,
    source_total: 3,
    page_indices: PAGES_OF[i],
    fields: {
        direction: 'sales', // 走库存/销项声明 → 后端把它落进 fields(本次新链路)
        invoice_number: ['IV69/00179', 'IV69/00189', 'IV69/00199'][i],
        date_raw: '28/2/2569',
        seller_name: SELLER,
        seller_tax: SELLER_TAX,
        buyer_name: BUYER,
        buyer_tax: BUYER_TAX,
        subtotal: '2700.00',
        vat: '189.00',
        total_amount: '2889.00',
        items: [{ name: 'น้ำแข็งหลอดเล็ก', qty: '16', price: '55', subtotal: '880.00' }],
    },
});
const OCR_OK = {
    filename: 'SINCERE.pdf',
    invoices: [inv(0), inv(1), inv(2)],
    history_ids: ['h0', 'h1', 'h2'],
    invoice_count: 3,
    page_count: 2,
};
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }],
};

const fails = [];
const oks = [];
function check(cond, label) {
    (cond ? oks : fails).push(label);
}
function visible(cs) {
    return (
        !!cs &&
        cs.display !== 'none' &&
        cs.visibility !== 'hidden' &&
        parseFloat(cs.opacity) > 0 &&
        cs.h > 0
    );
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newContext().then((c) => c.newPage());
    await page.setViewportSize({ width: 1320, height: 1000 });

    let sentBody = null;
    await page.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', 'th');
    });
    await page.route('**/api/**', async (route) => {
        const u = route.request().url();
        if (u.includes('/api/ocr/recognize')) {
            // multipart + 文件时 postData() 返回 null(踩过一次,断言会假绿)→ 用 buffer。
            const buf = route.request().postDataBuffer();
            sentBody = buf ? buf.toString('utf8') : null;
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(OCR_OK),
            });
        }
        if (u.includes('/api/erp/endpoints'))
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(EPS),
            });
        if (/\/api\/history\/[^/]+\/page\/\d+\.png/.test(u))
            return route.fulfill({
                status: 200,
                contentType: 'image/png',
                headers: { 'X-Page-Count': '2' },
                // 1x1 PNG · 只为让查看器进入"有图"态,像素内容与断言无关
                body: Buffer.from(
                    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
                    'base64'
                ),
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
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
    });

    // ── 真实点击流:左栏「录入工作台」→ 发票录入 ────────────────────────────
    await page.waitForSelector('.nav-item[data-route="dms-intake"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="dms-intake"]');
    await page.waitForSelector('.dmsx .dx-side', { timeout: 15000 });

    // ① 两个纯文案框已删 + 两级声明在位
    const rail = await page.evaluate(() => {
        const boxes = Array.from(document.querySelectorAll('.dmsx .dx-side .dx-side-box'));
        return {
            heads: boxes.map((b) => (b.querySelector('b')?.textContent || '').trim()),
            nDir: document.querySelectorAll('.dmsx [data-iv-dir]').length,
            nPost: document.querySelectorAll('.dmsx [data-iv-posting]').length,
        };
    });
    check(rail.heads.length === 2, `侧栏只剩两个框(实=${rail.heads.length}:${rail.heads})`);
    check(rail.nDir === 2, `进项/销项两个选项在位(实=${rail.nDir})`);
    check(rail.nPost === 2, `服务/库存两个选项在位(实=${rail.nPost})`);
    for (const lang of LANGS) {
        check(
            rail.heads.every((h) => h !== tr(lang, 'dx-side-cur') && h !== tr(lang, 'dx-side-rule')),
            `[${lang}] 「当前流程」「设计原则」已不在侧栏`
        );
    }

    // 选中/取消:再点一次要能退回「不声明」
    await page.click('[data-iv-dir="sales"]');
    let st = await page.evaluate(() => window.__IVDBG?.() || null);
    await page.click('[data-iv-dir="sales"]');
    const afterUnset = await page.evaluate(
        () => document.querySelectorAll('.dmsx [data-iv-dir].active').length
    );
    check(afterUnset === 0, `再点一次可取消方向声明(实 active=${afterUnset})`);
    await page.click('[data-iv-dir="sales"]');
    await page.click('[data-iv-posting="stock"]');
    const picked = await page.evaluate(() => ({
        dir: document.querySelector('.dmsx [data-iv-dir].active')?.dataset.ivDir || '',
        post: document.querySelector('.dmsx [data-iv-posting].active')?.dataset.ivPosting || '',
    }));
    check(picked.dir === 'sales', `销项已选中(实=${picked.dir})`);
    check(picked.post === 'stock', `库存已选中(实=${picked.post})`);

    // ── 真上传 + 真点开始 ───────────────────────────────────────────────
    const tmp = path.join(OUT, '_intake_probe.pdf');
    fs.writeFileSync(tmp, '%PDF-1.4\n%probe\n');
    await page.setInputFiles('.dmsx input[type=file]', tmp);
    await page.waitForSelector('#dx-inv-start', { timeout: 8000 });
    await page.click('#dx-inv-start');
    await page.waitForSelector('.dmsx .dx-acc-item.open .dx-acc-panel', { timeout: 20000 });

    // ② 声明真的随请求走
    check(!!sentBody && sentBody.length > 0, '抓到 recognize 的 multipart 体(非空)');
    check(/name="direction"[\s\S]{0,40}sales/.test(sentBody || ''), '请求体带 direction=sales');
    check(
        /name="posting_kind"[\s\S]{0,40}stock/.test(sentBody || ''),
        '请求体带 posting_kind=stock'
    );

    const results = [];
    for (const lang of LANGS) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.waitForTimeout(120);
        const probe = await page.evaluate(() => {
            const cs = (el) => {
                if (!el) return null;
                const s = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    position: s.position,
                    top: s.top,
                    h: r.height,
                    text: (el.textContent || '').trim(),
                };
            };
            const panel = document.querySelector('.dmsx .dx-acc-item.open .dx-acc-panel');
            const grps = Array.from(panel.querySelectorAll('[data-inv-grp]'));
            const g0 = grps[0];
            const labels = Array.from(g0.querySelectorAll('.dx-review-grid .dx-rv')).map((d) => ({
                label: (d.querySelector('label')?.textContent || '').trim(),
                key: d.querySelector('input')?.dataset.ivField || '',
                val: d.querySelector('input')?.value || '',
            }));
            const th = Array.from(g0.querySelectorAll('.dx-item-tbl th')).map((x) =>
                (x.textContent || '').trim()
            );
            const td = Array.from(g0.querySelectorAll('.dx-item-tbl tbody tr td input')).map(
                (x) => x.value
            );
            return {
                labels,
                th,
                td,
                extra: cs(g0.querySelector('.dx-extra')),
                imgcard: cs(panel.querySelector('.dx-imgcard')),
                warnPill: cs(
                    document.querySelector('.dmsx .dx-acc-item.open .dx-acc-row .dx-pill.warn')
                ),
                nGrp: grps.length,
            };
        });
        await page.screenshot({ path: path.join(OUT, `dms-intake-review-${lang}.png`) });
        results.push({ lang, probe });
    }

    for (const { lang, probe } of results) {
        // ③ 销项票的对手方 = 买方
        const nameCell = probe.labels[0] || {};
        const taxCell = probe.labels[1] || {};
        check(
            nameCell.key.endsWith(':buyer_name') && nameCell.val === BUYER,
            `[${lang}] 名称取买方(实 key=${nameCell.key} val=${(nameCell.val || '').slice(0, 12)})`
        );
        check(
            taxCell.key.endsWith(':buyer_tax') && taxCell.val === BUYER_TAX,
            `[${lang}] 税号取买方(实 key=${taxCell.key} val=${taxCell.val})`
        );
        check(!visible(probe.warnPill), `[${lang}] 销项票不再被误判「需确认」`);

        // ④ 明细四列 + 值各归各位
        const want = [
            tr(lang, 'dxi-rev-item-name'),
            tr(lang, 'dxi-rev-item-qty'),
            tr(lang, 'dxi-rev-item-price'),
            tr(lang, 'dxi-rev-item-amt'),
        ];
        check(
            JSON.stringify(probe.th) === JSON.stringify(want),
            `[${lang}] 明细四列表头四语正确(实=${JSON.stringify(probe.th)})`
        );
        check(
            JSON.stringify(probe.td) === JSON.stringify(['น้ำแข็งหลอดเล็ก', '16', '55', '880.00']),
            `[${lang}] 金额列是 880.00 不是单价 55(实=${JSON.stringify(probe.td)})`
        );

        // ⑤⑥ 库存路默认摊开 + 查看器钉住
        check(visible(probe.extra), `[${lang}] 走库存路时明细默认可见`);
        check(probe.imgcard?.position === 'sticky', `[${lang}] 查看器 sticky(实=${probe.imgcard?.position})`);
        check(probe.nGrp === 3, `[${lang}] 三张发票各成一组(实=${probe.nGrp})`);
    }

    // ⑥ 跟随:聚焦第 3 张的字段 → 查看器翻到第 2 页 + 该组高亮
    await page.evaluate((l) => window.applyLang(l), 'th');
    const before = await page.evaluate(
        () => document.querySelector('.dx-acc-item.open .pv-pgnum')?.textContent || ''
    );
    await page.focus('[data-inv-grp="2"] .dx-rv-in');
    await page.waitForTimeout(400);
    const follow = await page.evaluate(() => ({
        pg: document.querySelector('.dx-acc-item.open .pv-pgnum')?.textContent || '',
        active: document.querySelector('[data-inv-grp].active')?.dataset.invGrp ?? '',
    }));
    check(before.startsWith('1/'), `初始停在第 1 页(实=${before})`);
    check(follow.pg.startsWith('2/'), `聚焦第 3 张 → 查看器翻到第 2 页(实=${follow.pg})`);
    check(follow.active === '2', `第 3 张被高亮(实=${follow.active})`);

    // 反向:聚焦第 1 张 → 翻回第 1 页
    await page.focus('[data-inv-grp="0"] .dx-rv-in');
    await page.waitForTimeout(400);
    const back = await page.evaluate(() => ({
        pg: document.querySelector('.dx-acc-item.open .pv-pgnum')?.textContent || '',
        active: document.querySelector('[data-inv-grp].active')?.dataset.invGrp ?? '',
    }));
    check(back.pg.startsWith('1/'), `聚焦第 1 张 → 翻回第 1 页(实=${back.pg})`);
    check(back.active === '0', `第 1 张被高亮(实=${back.active})`);

    // ④ 明细可编辑:真键盘输入 → 进 IV.results(fill() 绕过真实按键,不算数)
    const cell = await page.$('[data-inv-grp="0"] .dx-item-tbl tbody tr td input');
    await cell.click({ clickCount: 3 });
    await page.keyboard.type('น้ำแข็งหลอดใหญ่');
    await page.waitForTimeout(80);
    const edited = await page.evaluate(
        () =>
            document.querySelector('[data-inv-grp="0"] .dx-item-tbl tbody tr td input')?.value || ''
    );
    check(edited === 'น้ำแข็งหลอดใหญ่', `明细可真键盘编辑(实=${edited})`);

    // 暗夜
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUT, 'dms-intake-review-dark.png') });

    fs.unlinkSync(tmp);
    await browser.close();
    srv.close();

    const total = oks.length + fails.length;
    if (fails.length) {
        console.log(`\n🔴 ${fails.length}/${total} FAIL`);
        fails.forEach((f) => console.log('  ✗ ' + f));
        process.exit(1);
    }
    console.log(`\n✅ ${oks.length}/${total} PASS`);
    oks.forEach((o) => console.log('  ✓ ' + o));
})();
