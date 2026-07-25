// 教程深链真浏览器验收:会计盯着一张推不进去的失败卡时,那条「这是怎么回事」在不在、点了去哪。
// 三个面都验:推送日志失败卡的原因条、详情抽屉的失败框、Express 体检卡住的那一行。
//
// 落点一律拿仓库里的真内容验。此前这里注入过一篇自造的 stuck-no-revenue-account —— 验收对象
// 是脚本自己造的、产品里根本不存在的章,于是 16 项全绿,而映射表整表指向占位 id 一条不命中。
// 教训:桩可以造输入(日志行),不能造被验对象。
//
// dist 不重建(统一由人做 build),本脚本自己把 src 编到临时目录,再在服务端顶掉
// /static/dist/main.js;CSS 同理把新写的 home-57-guide.css 追加在 bundle 末尾 ——
// 与 build-home-css.mjs 的拼接顺序一致(它就是清单最后一项),层叠结果等价。
//
// 跑法: node scripts/_guide_deeplink_verify.cjs
/* eslint-disable no-undef */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execSync } = require('child_process');
const { chromium } = require('playwright');
const { serveStatic, chk, summary, crumbs, bootHome } = require('./_verify_shared.cjs');

const ROOT = path.resolve(__dirname, '..');
const TMP = path.join(os.tmpdir(), 'pearnly-guide-deeplink-build');
const OUT = path.join(ROOT, 'tests', 'visual', '_shot');
const PORT = 8801;

// 页面 fetch 的是 dist 那一份,所以校验也对 dist —— 顺带把「改了正文忘了 build」也拦下。
const CONTENT = path.join(ROOT, 'static', 'dist', 'guide-content');
const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));

// guide-links.ts 的 REASON_CHAPTER(原因码 → 篇/章)· 正则读源码,与 check_guide.py 同一张表。
function reasonChapters() {
    const src = fs
        .readFileSync(path.join(ROOT, 'src', 'home', 'guide-links.ts'), 'utf8')
        .replace(/\/\/[^\n]*/g, '');
    const table = /inSection\(\s*'([\w-]+)'\s*,\s*\{([\s\S]*?)^\}\)/gm;
    const out = [];
    for (let m; (m = table.exec(src)); ) {
        const entry = /^\s*(\w+)\s*:\s*'([^']+)'/gm;
        for (let e; (e = entry.exec(m[2])); ) out.push({ code: e[1], sec: m[1], ch: e[2] });
    }
    return out;
}

const LINKS = reasonChapters();

function chapterOf(sec, ch) {
    const file = path.join(CONTENT, sec + '.json');
    if (!fs.existsSync(file)) return null;
    return (readJson(file).chapters || []).find((c) => c.id === ch) || null;
}

// 某原因码该落到哪一章(拿真内容里的那一章对象,标题用来断言面包屑)。
function targetOf(code) {
    const ref = LINKS.find((l) => l.code === code);
    return ref && chapterOf(ref.sec, ref.ch);
}

function buildBundle() {
    execSync(`npx vite build --outDir "${TMP}" --emptyOutDir`, { cwd: ROOT, stdio: 'pipe' });
}

function serve() {
    const css =
        fs.readFileSync(path.join(ROOT, 'static/dist/home.css'), 'utf8') +
        '\n' +
        fs.readFileSync(path.join(ROOT, 'static/home-57-guide.css'), 'utf8');
    return serveStatic(PORT, {
        intercept: (p, res) => {
            if (p !== '/static/dist/home.css') return false;
            res.writeHead(200, { 'content-type': 'text/css', 'cache-control': 'no-store' });
            res.end(css);
            return true;
        },
        resolveFile: (p) => (p === '/static/dist/main.js' ? path.join(TMP, 'main.js') : null),
    });
}

// 三张失败卡:两个原因码各自命中一章(且是不同章)/ 一个压根没进映射表。
const LOG_MAPPED_LIVE = {
    id: 'L1',
    status: 'failed',
    push_type: 'invoice',
    trigger: 'manual',
    invoice_no: 'INV-0001',
    endpoint_name: 'Express',
    endpoint_adapter: 'express',
    endpoint_id: 9,
    history_id: 11,
    created_at: '2026-07-25T03:00:00Z',
    http_status: 200,
    elapsed_ms: 120,
    error_msg: 'EXPRESS_MANUAL: no_revenue_account',
    response_body: {
        preflight: [{ key: 'mapping', status: 'blocked', reason: 'no_revenue_account' }],
    },
};
const LOG_MAPPED_TODO = {
    ...LOG_MAPPED_LIVE,
    id: 'L2',
    invoice_no: 'INV-0002',
    error_msg: 'EXPRESS_MANUAL: credit_note',
    response_body: {},
};
const LOG_UNMAPPED = {
    ...LOG_MAPPED_LIVE,
    id: 'L3',
    invoice_no: 'INV-0003',
    error_msg: 'EXPRESS_MANUAL: enqueue_error:KeyError',
    response_body: {},
};
const LOGS = [LOG_MAPPED_LIVE, LOG_MAPPED_TODO, LOG_UNMAPPED];

// bootHome 已铺好通配兜底;这里补更具体的规则(Playwright 后注册者先匹配)。
async function stubLogs(page) {
    await page.route('**/api/erp/logs?**', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ ok: true, items: LOGS, total: LOGS.length }),
        })
    );
    await page.route('**/api/erp/logs/*', (route) => {
        const id = route.request().url().split('/').pop().split('?')[0];
        const hit = LOGS.find((l) => l.id === id) || LOGS[0];
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(hit),
        });
    });
    // 教程正文不拦:落点必须是仓库里真发出去的那份内容,不是这里编一篇给自己看。
}

const boot = (ctx) =>
    bootHome(ctx, {
        port: PORT,
        viewport: { width: 1440, height: 980 },
        beforeGoto: stubLogs,
    });

async function openPushLogs(page) {
    await page.evaluate(() => window.routeTo('push-logs'));
    await page.waitForSelector('#erp-logs-list .erp-log-card', { timeout: 8000 });
}

const linkIn = (page, logId) =>
    page.locator(`.erp-log-card[data-log-detail="${logId}"] .erp-log-reason .gd-why`);

async function run() {
    console.log('building src -> ' + TMP);
    fs.mkdirSync(OUT, { recursive: true });

    // ── 面〇:整张映射表都得落在真章上(不进浏览器 · 这条是上次假绿的根因)──
    const dead = LINKS.filter((l) => !chapterOf(l.sec, l.ch));
    console.log(`  映射表 ${LINKS.length} 条 · 落空 ${dead.length} 条`);
    if (dead.length)
        console.log('  落空:', dead.map((d) => `${d.code}→${d.sec}/${d.ch}`).join(', '));
    chk('映射表抠得出内容(表空/写法变了要报红,不是默认全绿)', LINKS.length >= 30);
    chk('表里每个 ch 都在真实教程内容里', dead.length === 0);

    const live = targetOf('no_revenue_account');
    const other = targetOf('credit_note');
    chk('两个样本原因码各有真章可落', !!live && !!other && live.id !== other.id);
    console.log('  L1 落点:', live && live.id, '· L2 落点:', other && other.id);
    if (dead.length || LINKS.length < 30 || !live || !other) {
        console.log('\n表本身就不成立,后面几十项浏览器断言绿不绿都没有意义 —— 先修表。');
        return process.exit(summary());
    }

    buildBundle();
    const srv = await serve();
    const browser = await chromium.launch();
    const ctx = await browser.newContext({ deviceScaleFactor: 1 });
    const { page, errs } = await boot(ctx);

    await openPushLogs(page);

    // ── 面一:失败卡原因条 ──
    chk('命中映射的失败卡出现「这是怎么回事」', (await linkIn(page, 'L1').count()) === 1);
    chk('另一个原因码同样给入口', (await linkIn(page, 'L2').count()) === 1);
    chk('没进映射表的原因码不显示链接', (await linkIn(page, 'L3').count()) === 0);
    chk('链接真的可见(不是 DOM 里有)', await linkIn(page, 'L1').isVisible());
    const label = (await linkIn(page, 'L1').innerText()).trim();
    console.log('  链接文案(th):', label);
    chk('文案走 i18n 泰文,不是键名', label.startsWith('เกิดจากอะไร'));
    await page.locator('#erp-logs-list').screenshot({ path: path.join(OUT, 'gd-why-cards.png') });

    // ── 面二:点了真的落到对应章(标题取自真内容,不写死正则)──
    await linkIn(page, 'L1').click();
    await page.waitForSelector('#page-guide .gd-steps', { timeout: 8000 });
    const c = await crumbs(page);
    console.log('  面包屑:', c.join(' / '));
    chk('落到教程页且面包屑三级', c.length === 3);
    chk('末级正是该原因对应的那一章', (c[2] || '').includes(live.title.th));

    // 两个原因码落两章 —— 只验一条时,整表塌成同一章也照样绿。
    await openPushLogs(page);
    await linkIn(page, 'L2').click();
    await page.waitForSelector('#page-guide .gd-steps', { timeout: 8000 });
    const c2 = await crumbs(page);
    console.log('  面包屑(L2):', c2.join(' / '));
    chk('第二个原因码落到它自己的那一章', (c2[2] || '').includes(other.title.th));
    chk('点链接不连带弹出详情抽屉', (await page.locator('.erp-detail-drawer').count()) === 0);

    // ── 面三:内容里没有的章 id → 退手册首页(openGuide 的兜底,不是产品里的映射)──
    await page.evaluate(() => window.openGuide('exc-no-such-chapter', 'stuck'));
    await page.waitForSelector('#page-guide .gd-grid', { timeout: 8000 });
    chk('未知章 id 降级到手册首页', (await page.locator('.gd-card').count()) > 0);
    chk('降级后不留面包屑(确实回到了首页)', (await page.locator('.gd-crumb').count()) === 0);
    chk(
        '降级后正文非空',
        ((await page.locator('#page-guide .gd-body').innerText()) || '').length > 0
    );

    // ── 面四:详情抽屉(失败框 + Express 体检行)──
    await openPushLogs(page);
    await page.click('.erp-log-card[data-log-detail="L1"] .btn-ghost[data-log-detail]');
    await page.waitForSelector('.erp-detail-drawer .erp-receipt-fail-box', { timeout: 8000 });
    chk(
        '抽屉失败框有深链',
        (await page.locator('.erp-detail-drawer .erp-receipt-fail-box .gd-why').count()) === 1
    );
    chk(
        'Express 体检卡住那一行有深链',
        (await page.locator('.erp-detail-drawer .erp-tl-row.fail .gd-why').count()) === 1
    );
    await page
        .locator('.erp-detail-drawer')
        .screenshot({ path: path.join(OUT, 'gd-why-drawer.png') });
    await page.click('.erp-detail-drawer .erp-receipt-fail-box .gd-why');
    await page.waitForSelector('#page-guide .gd-steps', { timeout: 8000 });
    const c3 = await crumbs(page);
    chk('抽屉里点深链同样直达该章', c3.length === 3 && (c3[2] || '').includes(live.title.th));
    chk('跳走时抽屉被收掉,不盖在教程上', (await page.locator('.erp-detail-drawer').count()) === 0);

    chk('无页面 JS 错误', errs.length === 0);
    if (errs.length) console.log('  pageerror:', errs.slice(0, 3));

    await browser.close();
    srv.close();
    process.exit(summary());
}

run().catch((e) => {
    console.error(e);
    process.exit(1);
});
