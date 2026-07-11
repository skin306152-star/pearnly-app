// Pearnly AI · 批次 G1b · 月度报表包(BS/PL/TB + 账龄/折旧四态)· 本地全栈真机验收(非 CI 用例 · 用完即删)
// ============================================================
// 真后端 uvicorn(本地 docker postgres pearnly-db)+ 金标工单 d3267d34 真库读投影,零
// page.route——order_detail().financials 是真库读投影,/ai wo 视图真渲染。验收:报表包区
// isVisible + getComputedStyle(不是 grep 类名)、BS/PL/TB 数字与后端逐一吻合、权益节含
// 本期损益行(视觉配平)、账龄/折旧「未接入」占位、四语切换 + 手机 390 无横溢。
//
// 起法:
//   1) npm run build(产出含本次改动的 static/dist/ai.js/ai.css)
//   2) 本地全栈 harness 起服务(scratchpad/gbatch_run_server.py,端口 8793)
//   3) PEARNLY_E2E_BASE_URL=http://127.0.0.1:8793 GBATCH_E2E_SEED='<GBATCH_SEED_JSON 的值>' \
//      npx playwright test tests/e2e/_gbatch_financials_local.spec.js
/* global document, window, getComputedStyle */

const { test, expect } = require('@playwright/test');
const path = require('path');

const SEED_RAW = process.env.GBATCH_E2E_SEED || '';
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'gbatch');

test.skip(!SEED_RAW, 'GBATCH_E2E_SEED 未设置 · 本地全栈用例跳过(非 CI 用例)');

const SEED = SEED_RAW ? JSON.parse(SEED_RAW) : {};

async function primeAuth(page, lang) {
    await page.addInitScript(
        ({ token, lang }) => {
            window.localStorage.setItem('mrpilot_token', token);
            window.localStorage.setItem('mrpilot_lang', lang);
        },
        { token: SEED.token, lang: lang || 'zh' }
    );
}

async function gotoWo(page) {
    await page.goto('/ai');
    await page.waitForFunction(() => !!window.AI && !!window.AI.router);
    await page.evaluate((cid) => {
        window.location.hash = '#/client/' + cid + '/wo';
    }, SEED.workspace_client_id);
    // 报表包区真出现(不是 loading / 空态壳)。
    await page.waitForSelector('#cv-wo .fin-section', { timeout: 20000 });
}

async function backendFinancials(page) {
    return page.evaluate(
        async ({ token, wo }) => {
            const r = await fetch('/api/workorder/orders/' + wo, {
                headers: { Authorization: 'Bearer ' + token },
            });
            return (await r.json()).financials;
        },
        { token: SEED.token, wo: SEED.work_order_id }
    );
}

test.describe('批次 G1b · 月度报表包(真库 · 真 reconcile 步落库)', () => {
    test('报表包区真渲染 + BS/PL/TB isVisible/getComputedStyle + 数字与后端逐一吻合', async ({
        page,
    }) => {
        await primeAuth(page, 'zh');
        await gotoWo(page);

        const fin = await backendFinancials(page);
        expect(fin, 'order_detail.financials 应非空').toBeTruthy();
        expect(fin.balance_sheet.asset_total).toBe('918894.77');
        expect(fin.balance_sheet.liability_total).toBe('478080.53');
        expect(fin.balance_sheet.equity_total).toBe('440814.24');
        expect(fin.balance_sheet.balanced).toBe(true);
        expect(fin.profit_loss.net_profit).toBe('440814.24');
        expect(fin.trial_balance.balanced).toBe(true);
        expect(fin.ar_ap_aging.source).toBe('not_wired');
        expect(fin.depreciation.source).toBe('not_wired');

        // 报表包外壳真可见(getComputedStyle 亲验,非 grep 类名)。
        const wrap = page.locator('#cv-wo .fin-body-wrap');
        await expect(wrap).toBeVisible();
        const wrapStyle = await wrap.evaluate((el) => {
            const s = getComputedStyle(el);
            return { display: s.display, visibility: s.visibility };
        });
        expect(wrapStyle.display).not.toBe('none');
        expect(wrapStyle.visibility).toBe('visible');

        // 五分区各就位(bs/pl/tb/aging/depreciation),默认展开。
        await expect(page.locator('#cv-wo .fin-section')).toHaveCount(5);
        for (const kind of ['bs', 'pl', 'tb', 'aging', 'depreciation']) {
            const sec = page.locator(`.fin-section[data-fin-kind="${kind}"]`);
            await expect(sec, `${kind} 区应存在`).toHaveCount(1);
            await expect(sec, `${kind} 区应默认展开`).toHaveClass(/\bon\b/);
            const secStyle = await sec.evaluate((el) => {
                const s = getComputedStyle(el);
                return { display: s.display, visibility: s.visibility };
            });
            expect(secStyle.display, `${kind} 区不该 display:none`).not.toBe('none');
            expect(secStyle.visibility).toBe('visible');
        }

        // BS 区:配平胶囊 + 资产/负债/权益三数 + 本期损益行(视觉配平硬约束)。
        const bsSection = page.locator('.fin-section[data-fin-kind="bs"]');
        await expect(bsSection.locator('.chip.g')).toHaveText('已配平');
        await expect(bsSection).toContainText('918,894.77');
        await expect(bsSection).toContainText('478,080.53');
        await expect(bsSection).toContainText('440,814.24');
        await expect(bsSection).toContainText('本期损益');
        const earningsRow = bsSection.locator('.fin-earnings-row');
        await expect(earningsRow).toBeVisible();
        await expect(earningsRow).toContainText('440,814.24');

        // PL 区:净利润数字真显。
        const plSection = page.locator('.fin-section[data-fin-kind="pl"]');
        await expect(plSection).toContainText('440,814.24');

        // TB 区:配平胶囊 + 借贷合计一致。
        const tbSection = page.locator('.fin-section[data-fin-kind="tb"]');
        await expect(tbSection.locator('.chip.g')).toHaveText('已配平');
        await expect(tbSection).toContainText(
            fin.trial_balance.debit.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
        );

        // 账龄/折旧:诚实「未接入」占位,禁止假 0 表。
        const agingSection = page.locator('.fin-section[data-fin-kind="aging"]');
        await expect(agingSection.locator('.chip.n')).toHaveText('未接入');
        await expect(agingSection).toContainText('未接入');
        const depSection = page.locator('.fin-section[data-fin-kind="depreciation"]');
        await expect(depSection.locator('.chip.n')).toHaveText('未接入');

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '01-financials-zh-desktop.png'),
            fullPage: true,
        });
    });

    for (const lang of ['zh', 'th', 'en', 'ja']) {
        test(`四语切换(${lang}):报表包区可见 + 标题非原始 key`, async ({ page }) => {
            await primeAuth(page, lang);
            await gotoWo(page);
            const bsSection = page.locator('.fin-section[data-fin-kind="bs"]');
            await expect(bsSection).toBeVisible();
            // 标题不该原样显示未翻译的 i18n key(at() 找不到 key 时会原样回退成 key 本身)。
            const titleText = await page
                .locator('#cv-wo .panel:has(.fin-body-wrap) .hd h3')
                .first()
                .innerText();
            expect(titleText).not.toContain('fin_title');
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `02-financials-${lang}.png`),
                fullPage: true,
            });
        });
    }

    test('手机 390 视口:报表包五分区可见 + 无横向溢出', async ({ page }) => {
        await page.setViewportSize({ width: 390, height: 844 });
        await primeAuth(page, 'zh');
        await gotoWo(page);

        await expect(page.locator('#cv-wo .fin-section')).toHaveCount(5);
        await expect(page.locator('.fin-section[data-fin-kind="depreciation"]')).toBeVisible();

        const overflow = await page.evaluate(() => document.body.scrollWidth - window.innerWidth);
        expect(overflow, '手机视口不该出横向滚动').toBeLessThanOrEqual(1);

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '03-financials-mobile-390.png'),
            fullPage: true,
        });
    });
});
