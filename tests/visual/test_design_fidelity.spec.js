/*
 * 视觉照搬机械闸(docs/pos/12-visual-fidelity-gate.md)· 治"施工不照搬设计稿反复返工"。
 *
 * 对每个照搬稿页:把【设计稿 file://】与【生产页本地渲染】的关键元素 getComputedStyle 逐项比对:
 * 主色 #2563EB(rgb(37,99,235))/ 圆角 / box-shadow / font-size / font-family / 无 emoji(线性 svg);
 * 容器另查"左对齐不居中飘"(marginLeft=0,不 auto)。不一致 = 退出码 1 + 打印 哪页/哪选择器/稿X 生产Y。
 *
 * 自洽跑(无需真账号 / 真后端):内置静态服务器伺服 repo + stub 所有 /api/**,渲染本地 dist 真 bundle。
 * 跑法:node tests/visual/test_design_fidelity.spec.js  · 挂 pre-push(改 static/pos 或 src/home/{pos,inventory,purchase}-*)。
 * 加新页怎么补映射:见 README「视觉照搬闸」段 + 本文件 MAPPINGS 数组。
 */
/* eslint-disable no-undef, no-console */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
// 设计稿快照入库(tests/visual/design/)→ 闸自洽:pre-push + CI 都能跑(不依赖桌面)。
// 设计稿改了 → 更新这里的快照副本(README「视觉照搬闸」段)。
const DESIGN_DIR = path.join(__dirname, 'design');
const PORT = 8791;
const BLUE = 'rgb(37, 99, 235)';

// stub:让生产页在无后端下渲染到目标子页。
const API = {
    '/api/me': {
        id: 'u1',
        username: 'designgate',
        role: 'owner',
        is_super_admin: false,
        tenant_id: 't1',
    },
    '/api/ocr/quota': { used: 0, limit: 100 },
    '/api/me/plan': {},
    '/api/contact': {},
    '/api/me/modules': {
        ok: true,
        data: {
            modules: { pos: { enabled: true }, inventory: { enabled: true } },
            business_type: 'restaurant',
            needs_onboarding: false,
        },
    },
    '/api/pos/admin/restaurant/areas': {
        ok: true,
        data: { areas: [{ id: 1, name: '大厅', is_active: true, table_count: 2 }] },
    },
    '/api/pos/admin/restaurant/tables': {
        ok: true,
        data: {
            tables: [
                { id: 1, name: 'A1', area_id: 1, seats: 4, is_active: true },
                { id: 2, name: 'A2', area_id: 1, seats: 2, is_active: false },
            ],
        },
    },
    '/api/pos/admin/payment-settings': {
        ok: true,
        data: {
            promptpay_enabled: true,
            card_enabled: true,
            service_charge_rate: '10',
            price_includes_vat: true,
            promptpay_id: '',
        },
    },
};

// 映射表:稿 ↔ 生产路由 ↔ 关键选择器比对项。
// token: 设计选择器 vs 生产选择器,getComputedStyle props 必须相等。
// layout: 仅查生产容器左对齐(marginLeft=0)。
const MAPPINGS = [
    {
        name: '桌台管理(05 v2)',
        design: '05-tables.html',
        route: 'pos-tables',
        ready: '.ptbl .btn.primary',
        layout: { sel: '.ptbl', maxWidth: '960px' },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.ptbl .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.btn', prod: '.ptbl .btn', props: ['backgroundColor', 'borderRadius'] },
            { design: '.card', prod: '.ptbl .card', props: ['borderRadius', 'boxShadow'] },
            { design: '.zone', prod: '.ptbl .zone', props: ['borderRadius'] },
            { design: '.t', prod: '.ptbl .t', props: ['borderRadius'] },
        ],
        bluemust: '.ptbl .btn.primary',
        nosvgemoji: '.ptbl .btn.primary svg',
    },
    {
        name: '收款设置(13)',
        design: '13-payment.html',
        route: 'pos-payment',
        ready: '.rpay .save',
        layout: { sel: '.rpay', maxWidth: '760px' },
        tokens: [
            { design: '.save', prod: '.rpay .save', props: ['backgroundColor', 'borderRadius'] },
            { design: '.card', prod: '.rpay .card', props: ['borderRadius'] },
        ],
        bluemust: '.rpay .save',
        primary: 'rgb(14, 124, 102)', // 已令牌化迁到 emerald(风格 B)· 其余 B 组屏待 Window B 迁移仍蓝
        nosvgemoji: '.rpay .pm .ic svg',
    },
    {
        name: '采购/进项主屏(01 收拢版)',
        design: 'pur-list.html',
        route: 'purchase',
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: '1020px' },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
            { design: '.seg .o', prod: '.pur .seg .o', props: ['borderRadius'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .btn.primary svg',
    },
    {
        name: '费用/进项录入(10)',
        design: 'pur-form.html',
        route: 'purchase-form',
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: '1080px' },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.card', prod: '.pur .card', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .img svg',
    },
    {
        name: '单据详情(06)',
        design: 'pur-detail.html',
        route: 'purchase-detail',
        pre: () => window.openPurchaseDetail && window.openPurchaseDetail('doc-1'),
        ready: '.pur .btn.primary',
        layout: { sel: '.pur .wrap', maxWidth: '1000px' },
        tokens: [
            {
                design: '.btn.primary',
                prod: '.pur .btn.primary',
                props: ['backgroundColor', 'borderRadius'],
            },
            { design: '.card', prod: '.pur .card', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .btn.primary',
        nosvgemoji: '.pur .img svg',
    },
    {
        name: '供应商管理(04 收拢版)',
        design: 'pur-suppliers.html',
        route: 'purchase-suppliers',
        ready: '.pur .add',
        layout: { sel: '.pur .wrap', maxWidth: '920px' },
        tokens: [
            {
                design: '.btn',
                prod: '.pur .add',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .add',
        nosvgemoji: '.pur .add svg',
    },
    {
        name: '采购设置(05 收拢版)',
        design: 'pur-settings.html',
        route: 'purchase-settings',
        ready: '.pur .save',
        layout: { sel: '.pur .wrap', maxWidth: '820px' },
        tokens: [
            {
                design: '.btn',
                prod: '.pur .save',
                props: ['backgroundColor', 'borderRadius', 'fontSize'],
            },
            { design: '.panel', prod: '.pur .panel', props: ['borderRadius', 'boxShadow'] },
        ],
        bluemust: '.pur .save',
        nosvgemoji: '.pur .addcat svg',
    },
];

const fails = [];
const ok = (c, m) => {
    if (!c) {
        fails.push(m);
        console.log('  ❌ ' + m);
    } else console.log('  ✅ ' + m);
};

function serveStatic() {
    const types = {
        '.js': 'application/javascript',
        '.css': 'text/css',
        '.html': 'text/html',
        '.map': 'application/json',
        '.webmanifest': 'application/json',
        '.png': 'image/png',
        '.svg': 'image/svg+xml',
    };
    const srv = http.createServer((req, res) => {
        let p = decodeURIComponent(req.url.split('?')[0]);
        if (p === '/home') p = '/home.html';
        const file = path.join(ROOT, p);
        if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
            res.writeHead(404);
            return res.end('nf');
        }
        res.writeHead(200, {
            'content-type': types[path.extname(file)] || 'text/plain',
            'cache-control': 'no-store',
        });
        fs.createReadStream(file).pipe(res);
    });
    return new Promise((r) => srv.listen(PORT, () => r(srv)));
}

async function styleOf(page, sel, props) {
    return await page.evaluate(
        ([s, ps]) => {
            const el = document.querySelector(s);
            if (!el) return null;
            const cs = getComputedStyle(el);
            const out = {};
            ps.forEach((p) => (out[p] = cs[p]));
            out.fontFamily = cs.fontFamily;
            return out;
        },
        [sel, props]
    );
}

(async () => {
    const srv = await serveStatic();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    await page.route('**/api/**', (route) => {
        const u = new URL(route.request().url());
        // 采购模块:后端未上线时 papi 走前端 mock 兜底(purchase-mock)· 这里回 404 触发兜底,让页渲染真 mock 数据。
        if (u.pathname.startsWith('/api/purchase/')) {
            return route.fulfill({ status: 404, contentType: 'application/json', body: '{}' });
        }
        const body = API[u.pathname] !== undefined ? API[u.pathname] : { ok: true, data: {} };
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    });
    await ctx.addInitScript(() => {
        localStorage.setItem('mrpilot_token', 'designgate.fake.token');
        localStorage.setItem('mrpilot_lang', 'zh');
        localStorage.setItem('pearnly_work_mode', 'personal');
    });

    for (const m of MAPPINGS) {
        console.log('\n[' + m.name + ']');
        // 1) 设计稿基线
        const designFile = 'file://' + path.join(DESIGN_DIR, m.design).replace(/\\/g, '/');
        await page.goto(designFile, { waitUntil: 'domcontentloaded' });
        const expected = {};
        for (const tk of m.tokens) expected[tk.design] = await styleOf(page, tk.design, tk.props);

        // 2) 生产页本地渲染
        await page
            .goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' })
            .catch(() => {});
        // bundle 就绪 = routeTo 在(各页 loader 由 routeTo 经 ROUTE_LOADERS 表调度,无需逐个探)。
        // 数据驱动:加新页只往 MAPPINGS 加一项即可,这里不必改(曾写死 loadPosTables/loadPosPayment → 加页必踩)。
        const fnReady = await page
            .waitForFunction(() => typeof window.routeTo === 'function', { timeout: 20000 })
            .then(() => true)
            .catch(() => false);
        ok(fnReady, '生产 bundle 就绪');
        if (!fnReady) continue;
        await page.evaluate(() => {
            window.isOwner = () => true;
            window.getActiveWorkspaceClientId = () => 1;
            const st = document.createElement('style');
            st.textContent = '#ws-modal{display:none!important;}';
            document.head.appendChild(st);
        });
        // 进路由前可选预置(如详情屏需先 openPurchaseDetail 置当前单据 id)。
        if (m.pre) await page.evaluate(m.pre);
        await page.evaluate((r) => window.routeTo(r), m.route);
        const rendered = await page
            .waitForSelector(m.ready, { timeout: 15000 })
            .then(() => true)
            .catch(() => false);
        ok(rendered, '生产页渲染 ' + m.ready);
        if (!rendered) continue;

        // 3) 容器左对齐(不居中飘)+ max-width
        const lay = await page.evaluate((s) => {
            const el = document.querySelector(s);
            if (!el) return null;
            const cs = getComputedStyle(el);
            return {
                maxWidth: cs.maxWidth,
                marginLeft: cs.marginLeft,
                marginRight: cs.marginRight,
            };
        }, m.layout.sel);
        ok(
            lay && lay.maxWidth === m.layout.maxWidth,
            `容器 ${m.layout.sel} max-width=${m.layout.maxWidth}(got ${lay && lay.maxWidth})`
        );
        ok(
            lay && lay.marginLeft === '0px',
            `容器左对齐 marginLeft=0(got ${lay && lay.marginLeft})`
        );

        // 4) token 逐项比对(稿 vs 生产)
        for (const tk of m.tokens) {
            const exp = expected[tk.design];
            const act = await styleOf(page, tk.prod, tk.props);
            if (!exp || !act) {
                ok(false, `选择器缺失 ${tk.design}/${tk.prod}`);
                continue;
            }
            for (const p of tk.props) {
                ok(exp[p] === act[p], `${tk.prod} ${p}: 稿 ${exp[p]} == 生产 ${act[p]}`);
            }
        }

        // 5) 主色 #2563EB + 图标是线性 svg(无 emoji)
        const blue = await page.evaluate((s) => {
            const el = document.querySelector(s);
            return el ? getComputedStyle(el).backgroundColor : null;
        }, m.bluemust);
        const wantPrimary = m.primary || BLUE; // 默认蓝 · 已迁 emerald 的屏在 mapping 里覆写
        ok(blue === wantPrimary, `主按钮主色 ${wantPrimary}(got ${blue})`);
        const hasSvg = await page.$(m.nosvgemoji);
        ok(!!hasSvg, `图标为线性 svg(无 emoji)· ${m.nosvgemoji}`);
    }

    await browser.close();
    srv.close();
    console.log(
        '\n' +
            (fails.length
                ? `❌ 视觉照搬闸 FAIL · ${fails.length} 项不一致(回去对齐设计稿)`
                : '✅ 视觉照搬闸 PASS · 关键令牌全等设计稿')
    );
    process.exit(fails.length ? 1 : 0);
})().catch((e) => {
    console.error('design-fidelity gate error:', e);
    process.exit(2);
});
