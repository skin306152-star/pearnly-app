// /dms 门户「操作员」页三处真机反馈的真浏览器验收(跑 static/dist 真构建产物 + stub /api/**):
//   ① 换 DMS 账号弹窗(用户名+密码双输入 · 留空=不改 · 空提交被拦 · PATCH body 只带非空字段)
//   ② 删除操作员(红键确认弹窗 · 四语文案切换 · DELETE 后行消失)
//   ③ 操作列表头「操作」与按钮簇对齐(boundingBox 断言列头中心 x 落在按钮簇 bbox 内 ±40px)
// 跑法: node scripts/_dms_roster_verify.cjs → tests/e2e/_artifacts/dms_roster_ux/
/* eslint-disable no-undef */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const PORT = 8921;
const BASE = `http://127.0.0.1:${PORT}`;
const OUT = path.join(ROOT, 'tests', 'e2e', '_artifacts', 'dms_roster_ux');

const TYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.woff2': 'font/woff2',
};

function serve() {
    const srv = http.createServer((req, res) => {
        const p = decodeURIComponent(req.url.split('?')[0]);
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

// ---------- 桩世界 ----------

const OPERATORS = [
    {
        user_id: 'op-0001',
        display_name: 'สมชาย',
        dms_role: 'sales',
        status: 'active',
        username: 'dmsop-abcd1234',
        line_bound: true,
        line_display_name: 'Somchai',
        line_bound_at: '2026-08-01T10:00:00+00:00',
        endpoint_ready: true,
    },
    {
        user_id: 'op-0002',
        display_name: '阿明',
        dms_role: 'admin',
        status: 'inactive',
        username: 'dmsop-efgh5678',
        line_bound: false,
        line_display_name: '',
        line_bound_at: null,
        endpoint_ready: false,
    },
];

async function boot(page) {
    const json = (r, payload) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });

    await page.route('**/api/**', (r) => {
        const req = r.request();
        const p = new URL(req.url()).pathname;
        const method = req.method();

        if (p === '/api/dms/session') return json(r, { ok: true, is_owner: true });
        if (p === '/api/me') return json(r, { username: 'owner', role: 'owner' });

        if (p === '/api/dms/operators' && method === 'GET')
            return json(r, { ok: true, items: OPERATORS });
        if (p === '/api/dms/operators' && method === 'POST')
            return json(r, { ok: true, user_id: 'op-new' });
        if (p.endsWith('/status') && method === 'POST') return json(r, { ok: true });
        if (p.endsWith('/bind-code') && method === 'POST')
            return json(r, {
                ok: true,
                code: '123456',
                expires_at: new Date(Date.now() + 600000).toISOString(),
            });
        const opMatch = p.match(/\/api\/dms\/operators\/([^/]+)$/);
        if (opMatch) {
            const id = decodeURIComponent(opMatch[1]);
            if (method === 'PATCH') return json(r, { ok: true });
            if (method === 'DELETE') {
                // 真后端删完列表不再含该行 → 桩同步移除,让「行消失」断言有据可查。
                const idx = OPERATORS.findIndex((o) => o.user_id === id);
                if (idx >= 0) OPERATORS.splice(idx, 1);
                return json(r, { ok: true });
            }
        }
        // 录入视图挂载时触发的旁路调用:空列表/空绑定态即可,不影响本页验收。
        if (p === '/api/erp/endpoints') return json(r, { items: [] });
        if (p === '/api/dms/line/binding') return json(r, {});
        return json(r, {});
    });

    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token', 'tok-dms-roster-e2e');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/dms.html`);
}

// ---------- 断言小件 ----------

let step = 0;
function ok(label) {
    step += 1;
    console.log(`  ✅ ${String(step).padStart(2, '0')} ${label}`);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(OUT, name), fullPage: false });
}

async function waitForCount(arr, n, ms) {
    const t0 = Date.now();
    while (arr.length < n) {
        if (Date.now() - t0 > ms) throw new Error(`waitForCount 超时:有 ${arr.length} 想要 ${n}`);
        await new Promise((r) => setTimeout(r, 50));
    }
}

async function openRoster(page) {
    await page.waitForSelector('.dms-nav-item[data-view="roster"]', {
        state: 'visible',
        timeout: 15000,
    });
    await page.click('.dms-nav-item[data-view="roster"]');
    await page.waitForSelector('.dms-op-table .dms-op-row:not(.head)', {
        state: 'visible',
        timeout: 15000,
    });
}

async function switchLang(page, lang) {
    await page.click(`.dms-lang-btn[data-dms-lang="${lang}"]`);
    await page.waitForSelector('.dms-op-table .dms-op-row:not(.head)', {
        state: 'visible',
        timeout: 15000,
    });
}

// 确认弹窗四语预期(文案随当前语言变 = i18n 装配层在动,不是桩定死)。
const DEL_TEXT = {
    zh: { title: '删除操作员', bodyPart: '解绑其 LINE' },
    th: { title: 'ลบผู้ปฏิบัติงาน', bodyPart: 'ยกเลิกการเชื่อม LINE' },
    en: { title: 'Delete operator', bodyPart: 'push history is kept' },
    ja: { title: '担当者を削除', bodyPart: 'LINE連携を解除' },
};
const NEXT_LANG = { zh: 'th', th: 'en', en: 'ja', ja: 'zh' };

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await boot(page);
    await openRoster(page);
    await shot(page, '01-roster-list.png');

    // ── ① 换 DMS 账号弹窗 ──
    const patchBodies = [];
    page.on('request', (req) => {
        if (req.method() === 'PATCH' && req.url().includes('/api/dms/operators/'))
            patchBodies.push(req.postDataJSON());
    });

    await page.locator('[data-op-act="pw"][data-op-id="op-0001"]').click();
    await page.waitForSelector('#dms-op-acc-user-input', { state: 'visible', timeout: 10000 });
    if (!(await page.locator('#dms-op-pw-input').isVisible()))
        throw new Error('换账号弹窗缺密码输入框');
    await shot(page, '02-account-modal-two-inputs.png');
    ok('换 DMS 账号弹窗:用户名 + 密码两个输入框在场');

    // 两个输入框都留空 → 保存被拦(错误提示出现 · 不发 PATCH)。
    await page.click('#dms-op-pw-save');
    await page.waitForSelector('#dms-op-pw-err', { state: 'visible', timeout: 10000 });
    await page.waitForTimeout(400);
    if (patchBodies.length !== 0) throw new Error('空提交不该发 PATCH');
    await shot(page, '03-account-modal-empty-blocked.png');
    ok('留空提交被拦:错误提示在场且未发 PATCH');

    // 只填用户名 → PATCH body 只带 dms_username。
    await page.fill('#dms-op-acc-user-input', 'sales01');
    await page.click('#dms-op-pw-save');
    await waitForCount(patchBodies, 1, 5000);
    if (JSON.stringify(patchBodies[0]) !== JSON.stringify({ dms_username: 'sales01' }))
        throw new Error(`PATCH body 应只含 dms_username: ${JSON.stringify(patchBodies[0])}`);
    await page.waitForSelector('#dms-toast.show', { state: 'visible', timeout: 10000 });
    await shot(page, '04-account-saved-toast.png');
    ok('只填用户名保存:toast 出现 · PATCH body 仅 {dms_username}');

    // 只填密码 → PATCH body 只带 dms_password。
    await page.locator('[data-op-act="pw"][data-op-id="op-0001"]').click();
    await page.waitForSelector('#dms-op-acc-user-input', { state: 'visible', timeout: 10000 });
    await page.fill('#dms-op-pw-input', 'newpass-9');
    await page.click('#dms-op-pw-save');
    await waitForCount(patchBodies, 2, 5000);
    if (JSON.stringify(patchBodies[1]) !== JSON.stringify({ dms_password: 'newpass-9' }))
        throw new Error(`PATCH body 应只含 dms_password: ${JSON.stringify(patchBodies[1])}`);
    ok('只填密码保存:PATCH body 仅 {dms_password}');

    // ── ② 删除操作员:红键确认弹窗 + 四语 + DELETE 后行消失 ──
    // 桩世界第一行是 op-0001(启用 · 已绑 LINE),数据带 data-op-id,定位无需按位置。
    const delBtn = page.locator('.dms-op-btn-danger[data-op-id="op-0001"]');
    if (!(await delBtn.isVisible())) throw new Error('删除按钮不在场');
    const delColor = await delBtn.evaluate((el) => getComputedStyle(el).color);
    await shot(page, '05-delete-button-present.png');
    ok(`行尾删除按钮在场且 danger 红(${delColor})`);

    for (const lang of ['zh', 'th', 'en', 'ja']) {
        await delBtn.click();
        await page.waitForSelector('#dms-op-del-confirm', { state: 'visible', timeout: 10000 });
        const title = await page.locator('.dms-op-modal-h').innerText();
        const body = await page.locator('#dms-op-del-body').innerText();
        if (!title.includes(DEL_TEXT[lang].title))
            throw new Error(`${lang} 弹窗标题不对: ${title}`);
        if (!body.includes(DEL_TEXT[lang].bodyPart))
            throw new Error(`${lang} 弹窗正文不对: ${body}`);
        await shot(page, `06-delete-confirm-${lang}.png`);
        ok(`${lang} 确认弹窗文案正确(标题+后果说明)`);
        await page.click('#dms-op-del-cancel');
        await switchLang(page, NEXT_LANG[lang]); // 循环尾 ja→zh,收尾时语言已回中文
    }

    await page.locator('.dms-op-btn-danger[data-op-id="op-0001"]').click();
    await page.waitForSelector('#dms-op-del-confirm', { state: 'visible', timeout: 10000 });
    await page.click('#dms-op-del-confirm');
    await page.waitForSelector('#dms-toast.show', { state: 'visible', timeout: 10000 });
    await page.waitForTimeout(500);
    const rowsAfter = await page.locator('.dms-op-row:not(.head)').count();
    if (rowsAfter !== 1) throw new Error(`删除后应剩 1 行,实际 ${rowsAfter}`);
    await shot(page, '07-delete-done-row-gone.png');
    ok('确认删除:DELETE 成功 toast · 该行从列表消失(剩 1 行)');

    // ── ③ 操作列表头与按钮簇对齐 ──
    const hb = await page.locator('.dms-op-row.head .dms-op-c.acts').boundingBox();
    const ab = await page.locator('.dms-op-row:not(.head) .dms-op-actions').first().boundingBox();
    if (!hb || !ab) throw new Error('拿不到对齐 boundingBox');
    const headCenter = hb.x + hb.width / 2;
    const inRange = headCenter >= ab.x - 40 && headCenter <= ab.x + ab.width + 40;
    console.log(
        `    列头中心 x=${headCenter.toFixed(1)} · 按钮簇 bbox [${ab.x.toFixed(1)}, ${(ab.x + ab.width).toFixed(1)}] · 容差 ±40px`
    );
    if (!inRange) throw new Error('操作列头中心 x 落在按钮簇 bbox 外(±40px)');
    await shot(page, '08-actions-column-aligned.png');
    ok('操作列表头中心 x 落在按钮簇 bbox 范围内(±40px)');

    await browser.close();
    srv.close();
    console.log(`\n全部通过 · 截图在 ${path.relative(ROOT, OUT)}`);
})().catch((err) => {
    console.error('❌ 验收失败:', err);
    process.exit(1);
});
