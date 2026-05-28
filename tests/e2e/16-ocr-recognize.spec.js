// Pearnly E2E · 16 OCR 识别 + 扣费 · REFACTOR-D1
// ============================================================
// 端到端验证 OCR 识别热路径(铁律 #26 高敏 · 自主 loop 安全替身 B):
//   1. 真账号登录 → tokenA
//   2. GET /api/me/credits 记 balance_before / pages_before
//   3. POST /api/ocr/recognize multipart with _test_reports/真实电子发票
//      → 200 + 响应有 history_id / pages
//   4. (异步成本日志写入)→ 短暂等待
//   5. GET /api/me/credits 记 balance_after / pages_after
//   6. 扣费数字对:
//      - 若 response.from_cache === true(同一 PDF 已在用户文件指纹缓存内)→ balance 不变
//        是预期(缓存命中不收费 · 见 app.py:1693-1711),annotate 缓存命中跳过数字断言
//      - 若 is_billing_exempt === true(此账号被免单)→ balance 不变,但 pages 应 +1
//      - 否则:balance_after < balance_before(扣了费)· pages_after > pages_before
//
// 兜底:
//   - 测试账号无 tenant / 余额 0 → annotate skip(Earn 给账号充几张测试额度即可)
//   - 文件指纹缓存导致 from_cache → 不算 fail,annotate 跳过(同一份 PDF 内容字节相同,
//     重跑本 spec 第二次起一律缓存命中,这是产品功能)。本 spec 主要兜底「上传 → 出结果
//     → 余额台账」整条线没失能,缓存路径下也走 log_ocr_cost(engine=cache · cost=0)
//     不算 spec 缺陷。要每次都强制真扣费需要每次构造唯一字节的 PDF · 留后续。
//
// 真烧 Gemini token(铁律 #26.D 计费可自由测 · pennies),Zihao 已授权。
// 端点超时:Gemini 实时 OCR 一张 PDF 平均 10-25s · 这条 spec 用 90s 单测超时。
// ============================================================

const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');
const { request: pwRequest } = require('@playwright/test');
const { hasCreds, doUiLogin } = require('./_helpers/auth');

// 真实电子发票样本(124KB · OCR 能识别为 invoice;真实电子发票 不是发票会被 400 拒)
const FIXTURE_PDF = path.join(
    __dirname,
    '..',
    'fixtures',
    'electronic',
    '8f1e45df',
    '2026-05',
    '83cad7f961bc4afb81910d0e79166c1e.pdf'
);
const BASE_URL = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';

async function getCredits(apiCtx) {
    const r = await apiCtx.get('/api/me/credits');
    const j = await r.json().catch(() => ({}));
    return { status: r.status(), body: j };
}

test.describe('OCR 识别 + 扣费台账闭环(铁律 #26 高敏)', () => {
    test.skip(!hasCreds(), '需测试账号·CI 无凭据时跳过');

    test('上传 真实电子发票 → 200 + history_id + balance/pages 台账动了', async ({
        browser,
    }, testInfo) => {
        test.setTimeout(120_000); // Gemini OCR 一张 PDF + 网络往返 + 等异步成本日志

        // ────── 1) 登录 · 拿 token
        const ctx = await browser.newContext();
        const page = await ctx.newPage();
        await doUiLogin(page);
        const token = await page.evaluate(() => localStorage.getItem('mrpilot_token'));
        expect((token || '').length, '登录后应有 token').toBeGreaterThan(0);

        // ────── 2) 用 APIRequestContext 携带 Bearer · 拿 credits 基线
        const apiCtx = await pwRequest.newContext({
            baseURL: BASE_URL,
            extraHTTPHeaders: { Authorization: 'Bearer ' + token },
            timeout: 60_000,
        });

        const before = await getCredits(apiCtx);
        expect(before.status, `/api/me/credits 基线应 200 (got ${before.status})`).toBe(200);
        const hasTenant = before.body.has_tenant !== false;
        if (!hasTenant) {
            testInfo.annotations.push({
                type: 'skip',
                description: '测试账号无 tenant · Earn 给账号建一个测试公司即可',
            });
            test.skip(true, 'no tenant');
            return;
        }
        const isOwner = before.body.is_owner === true;
        const isExempt = before.body.is_exempt === true;
        const balanceBefore = Number(before.body.balance_thb || 0);
        const pagesBefore = Number(before.body.pages_used || before.body.pages_this_month || 0);

        if (!isExempt && balanceBefore <= 0) {
            testInfo.annotations.push({
                type: 'skip',
                description: `测试账号余额 0(THB ${balanceBefore})· 用 Earn 后台给账号充几张测试额度`,
            });
            test.skip(true, 'no balance');
            return;
        }

        // ────── 3) 真上传 PDF · POST /api/ocr/recognize multipart
        expect(fs.existsSync(FIXTURE_PDF), `测试 PDF 应存在: ${FIXTURE_PDF}`).toBe(true);
        const pdfBuffer = fs.readFileSync(FIXTURE_PDF);

        const upRes = await apiCtx.post('/api/ocr/recognize', {
            multipart: {
                file: {
                    name: 'invoice_83cad7f9.pdf',
                    mimeType: 'application/pdf',
                    buffer: pdfBuffer,
                },
            },
            timeout: 90_000,
        });

        const upStatus = upRes.status();
        const upBody = await upRes.json().catch(() => ({}));
        expect(
            upStatus,
            `/api/ocr/recognize 应 200 (got ${upStatus} body=${JSON.stringify(upBody).slice(0, 300)})`
        ).toBe(200);
        expect(upBody, 'response 应是 object').toBeTruthy();
        expect(upBody.history_id, 'response 应含 history_id').toBeTruthy();
        // pages 可能是数组(真识别)或 cached.pages(缓存命中 · 也是数组)
        expect(Array.isArray(upBody.pages), 'response.pages 应是数组').toBe(true);
        expect(upBody.pages.length, 'pages 数组非空').toBeGreaterThan(0);

        const fromCache = upBody.from_cache === true;
        testInfo.annotations.push({
            type: 'info',
            description: `engine=${upBody.engine} from_cache=${fromCache} page_count=${upBody.page_count} is_exempt=${isExempt} is_owner=${isOwner}`,
        });

        // ────── 4) 等异步成本日志写入(create_task 入队 → 通常 < 2s 完成)
        await page.waitForTimeout(3000);

        // ────── 5) 拿 credits 终态
        const after = await getCredits(apiCtx);
        expect(after.status, '/api/me/credits 终态应 200').toBe(200);
        const balanceAfter = Number(after.body.balance_thb || 0);
        const pagesAfter = Number(after.body.pages_used || after.body.pages_this_month || 0);

        // ────── 6) 扣费数字对
        if (fromCache) {
            // 缓存命中 · 不收费是正常(app.py:1693-1711 · engine=cache · cost=0)
            // pages_used 仍会 +page_count(同上 db.log_ocr_cost engine=cache)
            testInfo.annotations.push({
                type: 'note',
                description: `缓存命中 · 跳过 balance 扣费数字断言(同一 PDF 字节内容已识别过)`,
            });
            // 仍验:pages_used 至少没倒退
            expect(pagesAfter, 'pages_used 不应回退').toBeGreaterThanOrEqual(pagesBefore);
        } else if (isExempt) {
            testInfo.annotations.push({
                type: 'note',
                description: 'is_billing_exempt=true · balance 不变 · pages 应 +1',
            });
            expect(balanceAfter, '免单账号 balance 不变').toBeCloseTo(balanceBefore, 5);
            expect(pagesAfter, '免单账号 pages 应增加').toBeGreaterThan(pagesBefore);
        } else {
            // 真扣费路径
            expect(
                balanceAfter,
                `balance_thb 应减少 (before=${balanceBefore} after=${balanceAfter})`
            ).toBeLessThan(balanceBefore);
            const delta = balanceBefore - balanceAfter;
            expect(delta, `扣费应 > 0 (delta=${delta})`).toBeGreaterThan(0);
            expect(delta, `单张 PDF 扣费应 < 100 THB · 防错位 (delta=${delta})`).toBeLessThan(100);
            expect(
                pagesAfter,
                `pages_used 应增加 (before=${pagesBefore} after=${pagesAfter})`
            ).toBeGreaterThan(pagesBefore);
        }

        await apiCtx.dispose();
        await ctx.close();
    });
});
