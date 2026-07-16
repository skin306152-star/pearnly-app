// Pearnly AI · FD-0d · 总台(#/desk)工作台 · 本地 stub 真浏览器验收(非 CI 用例 · 照
// _h1b_payroll_local.spec.js 范式)
// ============================================================
// python http.server 静态服 static/dist/ai.html + page.route stub /api/**:闸探针 200 →
// 进工作台;GET /api/ai/front-desk/feed 双作总台闸探针(limit=1)与消息流拉取(limit=50)。
// 验收:两批拖拽合批盘点计数对 → 说目标出合同卡 → 人点下拉改客户(不是 AI 建议的那个)→
// 确认开工真建工单 → 进度卡;大脑降级 → 降级卡 + 手动开单真开工单;四语切换无缺词;
// 手机 390 单列/sticky 输入区/无横溢;闸关 → 侧栏项不显示 + #/desk 静默落回工作台。
// 截图存 tests/e2e/_artifacts/fd0d/。
//
// 起法:npx playwright test tests/e2e/_fd0d_desk_local.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8983;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'fd0d');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
});

test.afterAll(() => {
    localServer.stop(server);
});

const CLIENTS = {
    clients: [
        { id: 7, name: 'Sister Makeup' },
        { id: 9, name: 'AsiaSports Co' },
    ],
};

function contractResponse(id, fileCount) {
    return {
        contract: {
            id: id,
            workspace_client_id: null,
            period: null,
            intent: null,
            status: 'draft',
            deliverables: [],
            work_order_id: null,
            brain_suggestion: {},
        },
        inventory: {
            groups: [{ group: 'image', count: fileCount, names: [] }],
            total: fileCount,
            recognized: fileCount,
            unrecognized: 0,
        },
    };
}

// deskFeedStatus: 200(闸开,feed 拉取返回空流)| 404(闸关,探针即失败)。
// interpretSuggestion: interpret 端点固定回这份建议(测试按场景各自定制)。
async function bootDesk(page, { lang = 'zh', deskFeedStatus = 200, interpretSuggestion = null } = {}) {
    await page.route('**/api/workorder/orders**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{"orders":[]}' })
    );
    await page.route('**/api/workspace/clients**', (r) =>
        r.fulfill({ contentType: 'application/json', body: JSON.stringify(CLIENTS) })
    );
    await page.route('**/api/ai/front-desk/feed**', (r) => {
        if (deskFeedStatus !== 200) {
            return r.fulfill({
                status: deskFeedStatus,
                contentType: 'application/json',
                body: '{"detail":"front_desk.not_found"}',
            });
        }
        return r.fulfill({ contentType: 'application/json', body: '{"contracts":[]}' });
    });
    let contractSeq = 0;
    await page.route('**/api/ai/front-desk/contracts', async (r) => {
        const req = r.request();
        let fileCount = 0;
        try {
            const body = req.postData() || '';
            fileCount = (body.match(/name="files"/g) || []).length;
        } catch (e) {
            fileCount = 0;
        }
        contractSeq += 1;
        return r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify(contractResponse('c-' + contractSeq, fileCount)),
        });
    });
    await page.route('**/api/ai/front-desk/interpret', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
                contract_id: 'c-1',
                suggestion: interpretSuggestion || {
                    degraded: false,
                    intent: 'monthly_vat',
                    client_suggestion: 7,
                    period: null,
                    reason: null,
                },
            }),
        })
    );
    await page.route('**/api/ai/front-desk/confirm', async (r) => {
        const body = JSON.parse(r.request().postData() || '{}');
        return r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({
                ok: true,
                work_order_id: 'wo-' + body.workspace_client_id,
                registered: [],
                count: 0,
            }),
        });
    });
    await page.route('**/api/**', (r) => {
        const url = r.request().url();
        if (
            url.includes('/api/workorder/orders') ||
            url.includes('/api/workspace/clients') ||
            url.includes('/api/ai/front-desk/')
        ) {
            return r.fallback();
        }
        return r.fulfill({ contentType: 'application/json', body: '{}' });
    });
    await page.addInitScript(
        ([l]) => {
            window.localStorage.setItem('mrpilot_token', 'tok-fd0d');
            window.localStorage.setItem('mrpilot_lang', l);
        },
        [lang]
    );
    await page.goto(`${BASE}/static/dist/ai.html#/desk`);
}

function fileList(prefix, count) {
    return Array.from({ length: count }, (_, i) => ({
        name: `${prefix}-${i + 1}.jpg`,
        mimeType: 'image/jpeg',
        buffer: Buffer.from('stub-image-bytes'),
    }));
}

test.describe('FD-0d · 总台(#/desk)本地 stub 真浏览器', () => {
    test('闸开:两批拖拽合批 → 盘点卡计数对(25 张)', async ({ page }) => {
        await bootDesk(page);
        await expect(page.locator('#navDesk')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('#deskDrop')).toBeVisible();

        // 两次分批选择(A10「跨两批」验收场景):mergeFiles 累积,不互相顶替。
        await page.setInputFiles('#fdFileInput', fileList('batch1', 13));
        await expect(page.locator('.dz-count b')).toHaveText('13');
        await page.setInputFiles('#fdFileInput', fileList('batch2', 12));
        await expect(page.locator('.dz-count b')).toHaveText('25');

        await page.click('[data-action="desk-send"]');
        await expect(page.locator('.fd-inventory')).toBeVisible();
        await expect(page.locator('.fd-inv-total')).toContainText('25');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '01-inventory.png'), fullPage: true });
    });

    test('说目标 → 合同卡 → 人点下拉改客户(非 AI 建议)→ 确认开工 → 进度卡 + 真建工单', async ({
        page,
    }) => {
        await bootDesk(page);
        await page.setInputFiles('#fdFileInput', fileList('vat', 3));
        await page.locator('#fdUtteranceInput').fill('ทำภาษีมูลค่าเพิ่มเดือนนี้');
        await page.click('[data-action="desk-send"]');

        const card = page.locator('.fd-contract');
        await expect(card).toBeVisible();
        // 建议客户 7 已预填,但必须是可交互的真 <select>——不是纯文字展示。
        await expect(page.locator('.fd-client-sel')).toHaveValue('7');

        // 人点下拉改成另一个客户(9),证明「必须人点」不是形式主义:confirm 提交的
        // 是用户选的 9,不是 AI 建议的 7。
        const [confirmReq] = await Promise.all([
            page.waitForRequest((r) => r.url().includes('/api/ai/front-desk/confirm')),
            (async () => {
                await page.selectOption('.fd-client-sel', '9');
                await page.selectOption('.fd-period-sel', { index: 0 });
                await page.click('[data-action="desk-confirm"]');
            })(),
        ]);
        const sentBody = JSON.parse(confirmReq.postData() || '{}');
        expect(sentBody.workspace_client_id).toBe(9);

        await expect(page.locator('.fd-progress')).toBeVisible();
        await expect(page.locator('a.btn.sm[href*="/client/9/wo"]')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '02-contract-progress.png'), fullPage: true });
    });

    test('大脑降级 → 降级卡 + 手动开单可用(不经大脑真开工单)', async ({ page }) => {
        await bootDesk(page, {
            interpretSuggestion: { degraded: true, intent: null, client_suggestion: null, period: null, reason: 'brain_timeout' },
        });
        await page.setInputFiles('#fdFileInput', fileList('deg', 2));
        await page.locator('#fdUtteranceInput').fill('this month vat');
        await page.click('[data-action="desk-send"]');
        await expect(page.locator('.fd-degraded')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '03-degraded.png'), fullPage: true });

        // 降级卡里的「手动开单」按钮打开兜底表单,复用同一批已选文件,不经 interpret。
        await page.click('[data-action="desk-open-manual"]');
        await expect(page.locator('.fd-manual')).toBeVisible();
        await page.selectOption('#fdManualClientSel', '7');
        await page.selectOption('#fdManualPeriodSel', { index: 0 });
        await page.selectOption('#fdManualIntentSel', 'monthly_vat');
        const [confirmReq] = await Promise.all([
            page.waitForRequest((r) => r.url().includes('/api/ai/front-desk/confirm')),
            page.click('[data-action="desk-manual-submit"]'),
        ]);
        expect(JSON.parse(confirmReq.postData() || '{}').intent).toBe('monthly_vat');
        await expect(page.locator('.fd-progress')).toBeVisible();
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '04-manual-open-worked.png'), fullPage: true });
    });

    for (const lang of ['th', 'en', 'ja']) {
        test(`四语(${lang}):欢迎卡/上传区文案非原始 key`, async ({ page }) => {
            await bootDesk(page, { lang });
            await expect(page.locator('.fd-welcome')).toBeVisible();
            const lead = await page.locator('.fd-welcome .fd-lead').innerText();
            expect(lead).not.toContain('fd_welcome_lead');
            const dropText = await page.locator('#deskDrop .dz-t').innerText();
            expect(dropText).not.toContain('fd_drop_t');
            const navText = await page.locator('#navDesk span').innerText();
            expect(navText).not.toContain('nav_desk');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `05-lang-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390:单列 / composer sticky bottom / 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await bootDesk(page);
        await expect(page.locator('#v-desk')).toHaveClass(/\bon\b/);
        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '#/desk 手机视口不该出横向滚动').toBeLessThanOrEqual(1);
        const sticky = await page.locator('.fd-composer').evaluate((el) => getComputedStyle(el).position);
        expect(sticky).toBe('sticky');
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '06-mobile-390.png'), fullPage: true });
    });

    test('闸关:侧栏项不显示,直接深链 #/desk 静默落回工作台', async ({ page }) => {
        await bootDesk(page, { deskFeedStatus: 404 });
        await expect(page.locator('#navDesk')).toBeHidden({ timeout: 10000 });
        await expect(page.locator('#v-desk')).not.toHaveClass(/\bon\b/);
        await expect(page.locator('#v-dashboard')).toHaveClass(/\bon\b/);
        await expect(page).toHaveURL(/#\/$|#$/);
        await page.screenshot({ path: path.join(ARTIFACT_DIR, '07-gate-closed.png'), fullPage: true });
    });

    test('闸关:工作台其余功能逐字节不受影响(矩阵仍是默认首页)', async ({ page }) => {
        await bootDesk(page, { deskFeedStatus: 404 });
        await page.goto(`${BASE}/static/dist/ai.html#/`);
        await expect(page.locator('#navDesk')).toBeHidden({ timeout: 10000 });
        await expect(page.locator('#v-dashboard')).toHaveClass(/\bon\b/);
        await expect(page.locator('#matrixSection')).toBeVisible();
    });
});
