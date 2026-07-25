// 真浏览器验收 · 防重单闸拦下之后,会计到底看见什么(推送日志页真实点击流)。
//   闸的存在理由:改了票号回导重推 → 旧单还在 Express 里 → 不拦就是同一笔记两遍账。
//   拦住只是一半,拦完得让人看懂并知道去删哪一号。此前:前端没接这个码 → 显示小助手那句
//   写死中文 + 方括号里的英文码,泰国会计看不懂,也不知道要删 IV69/00473。
// 断言:① 四语人话可见 ② 句子里带真单据号 ③ 裸码不出现在卡上 ④ 阴性对照(别的失败不长这句)。
// 走真实导航:/home → 点左栏「推送日志」nav-item(禁 routeTo)→ getComputedStyle 判可见。
// 模型抄 scripts/_erp_stock_honesty_ui_verify.cjs。产物:tests/visual/_shot/erp-prior-doc-*.png。
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8831;
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

global.window = global.window || {};
require(path.join(ROOT, 'static/i18n-data.js'));
const I18N = global.window.I18N;
const tr = (lang, key) => I18N[lang][key];

const PRIOR = 'IV69/00473';
const CODE = 'PRIOR_DOC_STILL_IN_ERP';
// 小助手 queue_client.ack_failure 的真实格式 f"[{code}] {error}" · 那句中文原样抄自 companion。
const ACK_ERROR = `[${CODE}] ERP 里上一版单据 ${PRIOR} 还在 · 请先在 Express 删除它再重新导入`;

const BASE = {
    trigger: 'manual',
    push_type: 'invoice',
    endpoint_id: 'e1',
    endpoint_name: 'Express',
    ocr_buyer_name: 'บจก. ตัวอย่าง',
    http_status: 200,
    retry_count: 0,
    max_retries: 3,
};
const ITEMS = [
    {
        ...BASE,
        id: 'log-prior',
        status: 'failed',
        invoice_no: 'IV69/00474', // 会计改过的新号 —— 正是闸要拦的场景
        created_at: new Date().toISOString(),
        error_msg: ACK_ERROR,
        category: 'prior_doc_exists',
        prior_doc_fix: { docnum: PRIOR },
    },
    {
        // 阴性对照:另一种失败不许长出这句
        ...BASE,
        id: 'log-other',
        status: 'failed',
        invoice_no: 'IV69/00475',
        created_at: new Date().toISOString(),
        error_msg: '[CDX_REINDEX_FAILED] index rebuild failed',
        category: 'other',
    },
];
const EPS = {
    items: [{ id: 'e1', adapter: 'express', name: 'Express', enabled: true, config: {} }],
};

const fails = [];
const oks = [];
const check = (c, l) => (c ? oks : fails).push(l);
const visible = (cs) =>
    !!cs &&
    cs.display !== 'none' &&
    cs.visibility !== 'hidden' &&
    parseFloat(cs.opacity) > 0 &&
    cs.h > 0;

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newContext().then((c) => c.newPage());
    await page.setViewportSize({ width: 1320, height: 1000 });

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
                body: JSON.stringify({ total: ITEMS.length, items: ITEMS }),
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
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent =
            '#ws-modal{display:none!important;}#workspace-gate-root{display:none!important;}';
        document.head.appendChild(st);
    });

    await page.waitForSelector('.nav-item[data-route="push-logs"]', { timeout: 15000 });
    await page.click('.nav-item[data-route="push-logs"]');
    await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 15000 });

    for (const lang of LANGS) {
        await page.evaluate((l) => window.applyLang(l), lang);
        await page.click('.nav-item[data-route="push-logs"]');
        await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 8000 });
        const probe = await page.evaluate(() => {
            const cs = (el) => {
                if (!el) return null;
                const s = getComputedStyle(el);
                return {
                    display: s.display,
                    visibility: s.visibility,
                    opacity: s.opacity,
                    h: el.getBoundingClientRect().height,
                    text: (el.textContent || '').trim(),
                };
            };
            const card = (id) => document.querySelector(`.erp-log-card[data-log-detail="${id}"]`);
            return {
                prior: cs(card('log-prior') && card('log-prior').querySelector('.erp-log-reason')),
                priorAll: (card('log-prior')?.textContent || '').trim(),
                other: cs(card('log-other') && card('log-other').querySelector('.erp-log-reason')),
            };
        });
        await page.screenshot({ path: path.join(OUT, `erp-prior-doc-${lang}.png`) });

        // 期望文案由 i18n 单一源生成 —— 脚本里不抄第二份
        const want = tr(lang, 'erp-reason-prior-doc').replace('{doc}', PRIOR);
        check(visible(probe.prior), `[${lang}] 失败摘要可见`);
        check(
            (probe.prior?.text || '').includes(want),
            `[${lang}] 显示的是本语言人话且带单据号(want 尾段=${want.slice(-24)})`
        );
        check(probe.priorAll.includes(PRIOR), `[${lang}] 卡上出现要删的单据号 ${PRIOR}`);
        check(!probe.priorAll.includes(CODE), `[${lang}] 裸英文码 ${CODE} 不出现在卡上`);
        check(
            !probe.priorAll.includes('请先在 Express 删除它'),
            `[${lang}] 小助手那句写死中文不再直接示人`
        );
        check(!(probe.other?.text || '').includes(PRIOR), `[${lang}] 阴性对照:别的失败卡不长这句`);
    }

    await page.emulateMedia({ colorScheme: 'dark' });
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(OUT, 'erp-prior-doc-dark.png') });

    await browser.close();
    srv.close();

    const total = oks.length + fails.length;
    if (fails.length) {
        console.log(`\n🔴 ${fails.length}/${total} FAIL`);
        fails.forEach((f) => console.log('  x ' + f));
        process.exit(1);
    }
    console.log(`\n✅ ${oks.length}/${total} PASS`);
    oks.forEach((o) => console.log('  v ' + o));
})();
