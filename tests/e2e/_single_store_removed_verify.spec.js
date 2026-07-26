// 「一号一店」撤销 · prod 真站真账号验收(非 CI 用例 · 要真凭据,CI 无凭据自动 skip)
// ============================================================
// 靶子必须是真的:pearnly_e2e_2 的租户 business_type='pos_only' 且已有 1 个套账——
// 正是旧闸会拦下的那个配置(和 Zihao 撞闸的 skin 同构)。不起本地服、不 stub 任何
// 接口,全程打 https://pearnly.com,证明的是线上跑的那份代码。
//
// 两条验收:
//   ① 主体切换器里「新建主体」按钮对 pos_only 老板可见(旧代码按业态藏掉了它)
//   ② 真的建出第二个主体 → 不再回 403 pos.workspace_single_store
// 截图存 tests/e2e/_artifacts/single_store_removed/。
//
// 起法:PEARNLY_E2E_USER=pearnly_e2e_2 PEARNLY_E2E_PASS=<pw> \
//       npx playwright test tests/e2e/_single_store_removed_verify.spec.js
/* global window */

const path = require('path');
const { test, expect } = require('@playwright/test');
const { hasCreds } = require('./_helpers/auth');

// 自带登录:共享 helper 走 /login(main 门),而 pos_only 租户被入口作用域判为未授权,
// 报的是「账号或密码错误」(各是各的 · 故意不泄漏)。老板门在 /pos,真表单真提交。
// 只等 token 落 localStorage(登录成功的唯一事实源),不赌落哪个页面。
async function loginHere(page) {
    await page.goto('/pos');
    await page.locator('#p-email').fill(process.env.PEARNLY_E2E_USER);
    await page.locator('#p-pw').fill(process.env.PEARNLY_E2E_PASS);
    await page.locator('#p-submit').click();
    await page.waitForFunction(() => !!localStorage.getItem('mrpilot_token'), null, {
        timeout: 30000,
    });
}

const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'single_store_removed');
const STAMP = String(process.env.VERIFY_STAMP || 'x');

test.describe('一号一店已撤销 · prod 真账号', () => {
    test.skip(!hasCreds(), '需 PEARNLY_E2E_USER / PEARNLY_E2E_PASS');
    test.describe.configure({ mode: 'serial' });

    test.beforeEach(async ({ page }) => {
        await loginHere(page);
    });

    test('租户确实是 pos_only 且已有套账 · 靶子成立', async ({ page }) => {
        await page.goto('/home');
        await page.waitForFunction(() => typeof window.token === 'string' && window.token, {
            timeout: 30000,
        });

        const me = await page.evaluate(async () => {
            const r = await fetch('/api/me/modules', {
                headers: { Authorization: 'Bearer ' + window.token },
            });
            return r.json();
        });
        expect(
            me.data && me.data.business_type,
            '靶子前提:必须是 pos_only,否则这条验收证明不了任何事'
        ).toBe('pos_only');

        const before = await page.evaluate(async () => {
            const r = await fetch('/api/workspace/clients', {
                headers: { Authorization: 'Bearer ' + window.token },
            });
            return r.json();
        });
        expect(
            before.count,
            '靶子前提:必须已有 ≥1 个套账(旧闸正是从第 2 个开始拦)'
        ).toBeGreaterThanOrEqual(1);
    });

    test('① pos_only 老板看得见「新建主体」入口', async ({ page }) => {
        await page.goto('/home');
        await page.waitForFunction(() => typeof window.token === 'string' && window.token, {
            timeout: 30000,
        });
        await page.waitForTimeout(2500);

        await page.locator('#ws-ctrl-btn').click();
        const createBtn = page.locator('[data-orgcreate="1"]');
        await expect(createBtn).toBeVisible({ timeout: 10000 });

        const box = await createBtn.boundingBox();
        expect(box && box.width, '按钮得真占面积,不是 0×0 的隐形元素').toBeGreaterThan(0);

        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '1-orgcreate-visible.png'),
            fullPage: false,
        });
    });

    test('② 建第 2 个主体不再被 403 拦', async ({ page }) => {
        await page.goto('/home');
        await page.waitForFunction(() => typeof window.token === 'string' && window.token, {
            timeout: 30000,
        });

        const name = `一号一店撤销验收 ${STAMP}`;
        const res = await page.evaluate(async (nm) => {
            const r = await fetch('/api/workspace/clients', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + window.token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: nm, subject_type: 'personal' }),
            });
            return { status: r.status, body: await r.json().catch(() => ({})) };
        }, name);

        expect(
            JSON.stringify(res),
            '若仍出现 pos.workspace_single_store,说明线上跑的还是旧代码'
        ).not.toContain('workspace_single_store');
        expect(res.status, `建档应成功,实际:${JSON.stringify(res)}`).toBe(200);
        expect(res.body.ok).toBe(true);

        const after = await page.evaluate(async () => {
            const r = await fetch('/api/workspace/clients', {
                headers: { Authorization: 'Bearer ' + window.token },
            });
            return r.json();
        });
        expect(after.count, '新主体必须真出现在列表里').toBeGreaterThanOrEqual(2);

        // 证据要看得见:重开切换器,让两个主体同时出现在列表里再截图(截图必须在归档前)
        await page.reload();
        await page.waitForTimeout(2500);
        await page.locator('#ws-ctrl-btn').click();
        await expect(page.locator('#orgsw-pop')).toBeVisible({ timeout: 10000 });
        await expect(page.locator('#orgsw-pop [data-orgpick]')).toHaveCount(2, { timeout: 10000 });
        await page.screenshot({
            path: path.join(ARTIFACT_DIR, '2-second-subject-created.png'),
            fullPage: false,
        });

        // 收尾:归档掉验收造的主体,别把垃圾留在测试租户列表里
        await page.evaluate(async (id) => {
            await fetch('/api/workspace/clients/' + id, {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + window.token },
            });
        }, res.body.id);
    });
});
