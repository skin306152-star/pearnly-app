// /dms 门户「操作员」页的真浏览器验收(跑 static/dist 真构建产物 + stub /api/**):
//   ⓪ 提成归属(销售顾问下拉):列表归属列 · 建号表单默认「自动」· 四语文案 · POST 带 id
//   ① 编辑操作员弹窗(用户名+密码双输入 · 留空=不改 · 空提交被拦 · PATCH body 只带改过的字段
//      · 改/清归属的 PATCH body 精确 · 列表归属列跟着变)
//   ② 删除操作员(红键确认弹窗 · 四语文案切换 · DELETE 后行消失)
//   ③ 操作列表头「操作」与按钮簇对齐(boundingBox 断言列头中心 x 落在按钮簇 bbox 内 ±40px)
//   ④ 顾问名单取数失败:下拉锁住 + 错态提示 + 重试拉回名单(四态里最容易假绿的那两态)
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

// DMS 顾问主档(下拉选项)· 后端已剥掉 tel,桩照后端契约只给 id/code/name。
const ADVISORS = [
    { id: 'A1', code: 'S01', name: 'สมชาย' },
    { id: 'A2', code: 'S02', name: 'อาทิตย์' },
];

// 顾问名单接口的当前应答(④ 四态段会临时换成失败态,验错态 + 重试)。
let advisorsReply = { ok: true, advisors: ADVISORS };

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
        advisor_id: 'A1', // 老板钉死过归属
        advisor_name: 'สมชาย',
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
        advisor_id: '', // 没钉 = 自动匹配
        advisor_name: '',
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
        if (p === '/api/dms/roster/advisors') return json(r, advisorsReply);
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
            if (method === 'PATCH') {
                // 真后端改完归属,列表下一次就带新名字 → 桩同步改,让「列表跟着变」有据可查。
                const body = req.postDataJSON() || {};
                const row = OPERATORS.find((o) => o.user_id === id);
                if (row && Object.prototype.hasOwnProperty.call(body, 'dms_advisor_id')) {
                    const hit = ADVISORS.find((a) => a.id === body.dms_advisor_id);
                    row.advisor_id = hit ? hit.id : '';
                    row.advisor_name = hit ? hit.name : '';
                }
                return json(r, { ok: true });
            }
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

// 提成归属的四语(表单标签 + 列头)· 术语按 Korn 口径:th ที่ปรึกษาการขาย。
const ADV_TEXT = {
    zh: { field: '销售提成归属', col: '提成归属', auto: '自动' },
    th: { field: 'ที่ปรึกษาการขาย', col: 'ที่ปรึกษาการขาย', auto: 'อัตโนมัติ' },
    en: { field: 'Sales advisor', col: 'Advisor', auto: 'Automatic' },
    ja: { field: '販売担当', col: '販売担当', auto: '自動' },
};

// 下拉要等名单拉回来才可选(加载中是锁住的)—— 抓瞬态的断言等于没断言。
async function waitAdvisorReady(page, id) {
    await page.waitForFunction(
        (sel) => {
            const el = document.getElementById(sel);
            return !!el && !el.disabled;
        },
        id,
        { timeout: 10000 }
    );
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    const srv = await serve();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await boot(page);
    await openRoster(page);
    await shot(page, '01-roster-list.png');

    // ── ⓪ 提成归属:列表列 + 建号表单下拉 ──
    const advCells = page.locator('.dms-op-row:not(.head) .dms-op-c.advisor');
    if ((await advCells.count()) !== 2) throw new Error('归属列没有逐行渲染');
    const pinnedCell = await advCells.first().innerText();
    if (!pinnedCell.includes('สมชาย')) throw new Error(`钉死的行应显示顾问名: ${pinnedCell}`);
    const autoCell = await advCells.nth(1).innerText();
    if (!autoCell.includes('自动')) throw new Error(`没钉死的行应显示「自动」: ${autoCell}`);
    ok('列表归属列:钉死行显示顾问名 · 未钉行显示「自动」');

    await waitAdvisorReady(page, 'dms-op-advisor');
    const createSel = page.locator('#dms-op-advisor');
    if ((await createSel.inputValue()) !== '')
        throw new Error('建号表单的归属下拉默认应是空值(自动匹配)');
    const optCount = await createSel.locator('option').count();
    if (optCount !== ADVISORS.length + 1)
        throw new Error(`下拉应为 1 个「自动」+ ${ADVISORS.length} 位顾问,实际 ${optCount}`);
    await shot(page, '01a-create-form-advisor-default-auto.png');
    ok('建号表单归属下拉在场:默认「自动」· 选项 = 自动 + 顾问名单');

    for (const lang of ['zh', 'th', 'en', 'ja']) {
        const label = await page.locator('[data-adv-field] > span').first().innerText();
        const col = await page.locator('.dms-op-row.head .dms-op-c.advisor').innerText();
        if (!label.includes(ADV_TEXT[lang].field))
            throw new Error(`${lang} 归属下拉标签不对: ${label}`);
        // 列头 CSS 是 text-transform: uppercase,innerText 拿到的是转换后的字形 → 比大小写不敏感。
        if (!col.toLowerCase().includes(ADV_TEXT[lang].col.toLowerCase()))
            throw new Error(`${lang} 归属列头不对: ${col}`);
        const autoOpt = await page.locator('#dms-op-advisor option').first().innerText();
        if (!autoOpt.includes(ADV_TEXT[lang].auto))
            throw new Error(`${lang} 「自动」选项文案不对: ${autoOpt}`);
        await shot(page, `01b-advisor-${lang}.png`);
        ok(`${lang} 归属文案在场(表单标签 + 列头 + 自动选项)`);
        await switchLang(page, NEXT_LANG[lang]); // 循环尾 ja→zh,收尾时语言已回中文
        await waitAdvisorReady(page, 'dms-op-advisor');
    }

    const postBodies = [];
    page.on('request', (req) => {
        if (req.method() === 'POST' && new URL(req.url()).pathname === '/api/dms/operators')
            postBodies.push(req.postDataJSON());
    });
    await page.fill('#dms-op-name', 'อาทิตย์');
    await page.fill('#dms-op-user', 'sales09');
    await page.fill('#dms-op-pass', 'pw-123456');
    await page.selectOption('#dms-op-advisor', 'A2');
    await shot(page, '01c-create-form-advisor-picked.png');
    await page.click('#dms-op-create');
    await waitForCount(postBodies, 1, 5000);
    if (postBodies[0].dms_advisor_id !== 'A2')
        throw new Error(`建号 POST 应带 dms_advisor_id=A2: ${JSON.stringify(postBodies[0])}`);
    ok('选中顾问后新增:POST body 带 dms_advisor_id');

    // ── ① 编辑操作员弹窗 ──
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

    // 改归属 → PATCH 只带 dms_advisor_id;列表归属列跟着变。
    await page.locator('[data-op-act="pw"][data-op-id="op-0001"]').click();
    await waitAdvisorReady(page, 'dms-op-acc-advisor');
    if ((await page.locator('#dms-op-acc-advisor').inputValue()) !== 'A1')
        throw new Error('编辑弹窗应回显该操作员当前钉死的顾问');
    await shot(page, '09-edit-modal-advisor-preselected.png');
    ok('编辑弹窗:归属下拉回显当前钉死的顾问(A1)');

    await page.selectOption('#dms-op-acc-advisor', 'A2');
    await page.click('#dms-op-pw-save');
    await waitForCount(patchBodies, 3, 5000);
    if (JSON.stringify(patchBodies[2]) !== JSON.stringify({ dms_advisor_id: 'A2' }))
        throw new Error(
            `改归属的 PATCH body 应只含 dms_advisor_id: ${JSON.stringify(patchBodies[2])}`
        );
    await page.waitForSelector('.dms-op-row:not(.head) .dms-op-c.advisor', { timeout: 10000 });
    await page.waitForFunction(
        () => {
            const c = document.querySelector('.dms-op-row:not(.head) .dms-op-c.advisor');
            return !!c && c.innerText.includes('อาทิตย์');
        },
        null,
        { timeout: 10000 }
    );
    await shot(page, '10-advisor-repinned-in-list.png');
    ok('改归属:PATCH body 仅 {dms_advisor_id} · 列表归属列换成新顾问');

    // 选回「自动」→ 空串(清除钉死),不是「不带该字段」。
    await page.locator('[data-op-act="pw"][data-op-id="op-0001"]').click();
    await waitAdvisorReady(page, 'dms-op-acc-advisor');
    await page.selectOption('#dms-op-acc-advisor', '');
    await page.click('#dms-op-pw-save');
    await waitForCount(patchBodies, 4, 5000);
    if (JSON.stringify(patchBodies[3]) !== JSON.stringify({ dms_advisor_id: '' }))
        throw new Error(`清归属的 PATCH body 应是空串: ${JSON.stringify(patchBodies[3])}`);
    await page.waitForFunction(
        () => {
            const c = document.querySelector('.dms-op-row:not(.head) .dms-op-c.advisor');
            return !!c && c.innerText.includes('自动');
        },
        null,
        { timeout: 10000 }
    );
    await shot(page, '11-advisor-cleared-back-to-auto.png');
    ok('选回「自动」:PATCH body 带空串清钉 · 列表回到「自动」');

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

    // ── ④ 顾问名单取数失败:锁住下拉 + 指路 + 重试(错态不许冒充「名册是空的」)──
    advisorsReply = { ok: false, code: 'fetch_failed', advisors: [] };
    const page2 = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await boot(page2);
    await openRoster(page2);
    await page2.waitForSelector('#dms-op-advisor', { state: 'visible', timeout: 15000 });
    await page2.waitForSelector('[data-adv-retry]', { state: 'visible', timeout: 15000 });
    if (!(await page2.locator('#dms-op-advisor').isDisabled()))
        throw new Error('名单取不回来时下拉必须锁住(照发等于把归属清成自动)');
    // 建号表单那一份归属字段(编辑弹窗里还有一份同构的)——按字段容器锚定,不按位置取,
    // 否则选择器打偏时点到的是另一份、断言照样"成立"。
    const createField = page2.locator('[data-adv-field]:has(#dms-op-advisor)');
    const hintText = await createField.locator('[data-adv-hint]').innerText();
    if (!hintText.includes('顾问名单读取失败')) throw new Error(`错态提示文案不对: ${hintText}`);
    await shot(page2, '12-advisor-fetch-failed-locked.png');
    ok('取数失败:下拉锁住 + 错态提示 + 重试按钮在场');

    advisorsReply = { ok: true, advisors: ADVISORS };
    await createField.locator('[data-adv-retry]').click();
    await waitAdvisorReady(page2, 'dms-op-advisor');
    if ((await page2.locator('#dms-op-advisor option').count()) !== ADVISORS.length + 1)
        throw new Error('重试成功后下拉应填回完整名单');
    await shot(page2, '13-advisor-retry-recovered.png');
    ok('点重试:名单拉回来 · 下拉解锁并填满选项');

    // 手机端:多一列不许把表格撑出横滚(列头在 ≤640px 已隐藏,单元格改两列排)。
    await page2.setViewportSize({ width: 390, height: 844 });
    await page2.waitForTimeout(200);
    const overflow = await page2.evaluate(
        () => document.documentElement.scrollWidth - window.innerWidth
    );
    if (overflow > 1) throw new Error(`手机端出现横向溢出 ${overflow}px`);
    await shot(page2, '14-mobile-390.png');
    ok(`手机端 390px 无横向溢出(${overflow}px)`);

    await browser.close();
    srv.close();
    console.log(`\n全部通过 · 截图在 ${path.relative(ROOT, OUT)}`);
})().catch((err) => {
    console.error('❌ 验收失败:', err);
    process.exit(1);
});
