// 交付物下载链 · 真栈真浏览器验收(交接单 §3.16)
// ============================================================
// 此前这条链只验到「路由在、鉴权在」:库里 artifact_path 是手工种的、指的文件本机不存在,
// 端点必然 404,于是「点了到底有没有文件落下来」从来没被验过。本 spec 补的就是这一条:
// 界面上真点一次下载 → 真的 download 事件 → 文件真落盘 → 字节与 API 直取的一致 → 内容
// 真能打开(不是 0 字节、不是 200 包着的 HTML 错误页)。
//
// 前置:该工单必须已经真跑过 package(deliverables/vN 下有真文件)。没跑过就先在产品里
// 补销项让引擎推到 review —— 本 spec 不自己造文件,它验的就是「产品自己产的文件下得下来」。
//   本机跑法:
//   1) 起真栈(uvicorn 127.0.0.1:7860)+ docker pearnly-db
//   2) PEARNLY_E2E_LOCAL=1 PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 \
//      npx playwright test tests/e2e/_deliverable_download_real_verify.spec.js
// CI 打的是 pearnly.com,那边不认本机测试号,故文件级 skip。
/* global window */

const { test, expect } = require('@playwright/test');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

test.skip(process.env.PEARNLY_E2E_LOCAL !== '1', '需本机真栈 + 本机开发库测试号');

const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';
// 账号写死本机开发库那一个:PEARNLY_E2E_USER/PASS 在这台机上指的是生产账号,
// 拿它当默认值会静默打到 prod 去(实测 401)。
const USER = 'stw_e2e';
const PASS = 'StwVerify#2026';
const CLIENT_ID = process.env.PEARNLY_LOCAL_CLIENT_ID || '84';
const ORDER_ID = process.env.PEARNLY_LOCAL_ORDER_ID || 'c6c7144a-ebbc-4261-8a4c-977912f5e6a1';
// 另一个租户的工单:同一个 token 去要必须 404(不泄漏存在性)。
const FOREIGN_ORDER_ID =
    process.env.PEARNLY_LOCAL_FOREIGN_ORDER_ID || 'e7b988ba-f921-45f4-bec7-437493787dda';

const ART = path.join(__dirname, '_artifacts', 'deliverable_download');
fs.mkdirSync(ART, { recursive: true });

const sha256 = (buf) => crypto.createHash('sha256').update(buf).digest('hex');

let TOKEN = '';

test.beforeAll(async ({ request }) => {
    const r = await request.post(`${BASE}/api/login`, {
        data: { username: USER, password: PASS, entry: 'ai' },
    });
    expect(r.status()).toBe(200);
    TOKEN = (await r.json()).token;
    expect(TOKEN.length).toBeGreaterThan(20);
});

async function openPkg(page) {
    await page.addInitScript(
        ([t]) => {
            window.localStorage.setItem('mrpilot_token_ai', t);
            window.localStorage.setItem('mrpilot_lang', 'zh');
        },
        [TOKEN]
    );
    await page.goto(`${BASE}/ai#/client/${CLIENT_ID}/pkg?period=2569-06`, {
        waitUntil: 'domcontentloaded',
    });
    await page.waitForSelector('.pkg-files button[data-action="pkg-download"]', { timeout: 20000 });
}

test('界面点下载 → 文件真落盘 · 字节与 API 直取一致 · 内容真能打开', async ({ page, request }) => {
    await openPkg(page);
    await page.screenshot({ path: path.join(ART, '01-pkg-files-list.png'), fullPage: false });

    const btn = page.locator(
        '.pkg-files button[data-action="pkg-download"][data-kind="pp30_draft"]'
    );
    await expect(btn).toBeVisible();

    const [download] = await Promise.all([page.waitForEvent('download'), btn.click()]);
    const saved = path.join(ART, 'downloaded-pp30_draft.md');
    await download.saveAs(saved);

    // 落盘的是真文件:非空、UTF-8 可解、是 ภ.พ.30 底稿而不是一页 HTML 错误。
    const bytes = fs.readFileSync(saved);
    expect(bytes.length).toBeGreaterThan(200);
    const text = bytes.toString('utf8');
    expect(text.startsWith('<!DOCTYPE')).toBe(false);
    expect(text).toContain('ภ.พ.30');
    expect(text).toContain('2569-06');

    // 浏览器那条路拿到的字节 === API 直取的字节(证明 blob 没被截断/转码)。
    const api = await request.get(
        `${BASE}/api/workorder/orders/${ORDER_ID}/deliverables/pp30_draft`,
        { headers: { Authorization: `Bearer ${TOKEN}` } }
    );
    expect(api.status()).toBe(200);
    const apiBytes = Buffer.from(await api.body());
    expect(sha256(bytes)).toBe(sha256(apiBytes));

    // 下载文件名走 filename*(客户名_账期_报表名),不是内部 kind 字面量。
    expect(download.suggestedFilename()).toContain('2569-06');
    expect(api.headers()['content-disposition']).toContain("filename*=UTF-8''");

    // 下完按钮要解禁:防重入的 downloading 态卡住不复位,人就再也点不了第二次。
    await expect(btn).toBeEnabled();
    await page.screenshot({ path: path.join(ART, '02-button-reenabled.png'), fullPage: false });
    fs.writeFileSync(
        path.join(ART, 'evidence.json'),
        JSON.stringify(
            {
                order_id: ORDER_ID,
                saved_bytes: bytes.length,
                sha256: sha256(bytes),
                suggested_filename: download.suggestedFilename(),
                content_disposition: api.headers()['content-disposition'],
                content_type: api.headers()['content-type'],
            },
            null,
            2
        ),
        'utf8'
    );
});

test('鉴权反证:无 token / 坏 token / 别人的工单一律拿不到文件', async ({ request }) => {
    const url = `${BASE}/api/workorder/orders/${ORDER_ID}/deliverables/pp30_draft`;

    const anon = await request.get(url);
    expect(anon.status()).toBe(401);

    const bad = await request.get(url, {
        headers: { Authorization: `Bearer ${TOKEN.slice(0, -4)}beef` },
    });
    expect(bad.status()).toBe(401);

    // 同一个合法 token 去要别的租户的工单:404(不区分「没有」与「不是你的」)。
    const foreign = await request.get(
        `${BASE}/api/workorder/orders/${FOREIGN_ORDER_ID}/deliverables/pp30_draft`,
        { headers: { Authorization: `Bearer ${TOKEN}` } }
    );
    expect(foreign.status()).toBe(404);
    expect(await foreign.text()).not.toContain('ภ.พ.30');
});
