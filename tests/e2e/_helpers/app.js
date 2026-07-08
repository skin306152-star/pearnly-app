// Pearnly E2E · 主应用导航小工具 · REFACTOR-D1
// ============================================================
// 复用 storageState 进 /home 后,走真实点击切路由(home.js: .nav-item[data-route] → routeTo)。
// ============================================================

const { expect } = require('@playwright/test');

// 登录后「账套软弹」(workspace-switcher.js 的 #ws-modal · 2026-05-27 上线)是全屏 overlay,
// 会拦截一切点击。它在 /api/me 回来后自动弹,时机略晚于侧栏渲染。进应用后探测并用 ✕ 关掉
// (不选账套 / 不新建 · 纯关闭 · 不造数据)· 否则后续点击全被它挡(intercepts pointer events)。
async function dismissWorkspaceModal(page) {
    const modal = page.locator('#ws-modal');
    const appeared = await modal
        .waitFor({ state: 'visible', timeout: 6_000 })
        .then(() => true)
        .catch(() => false);
    if (!appeared) return;
    await page.locator('#ws-modal [data-ws-close="1"]').click();
    await modal.waitFor({ state: 'detached', timeout: 5_000 }).catch(() => {});
}

// 多账套用户登录后有一道硬启动闸 workspace-gate-root(#workspace-gate-root · onboarding 选公司),
// 在 sidebar 之前 preboot 且把 sidebar 置 visibility:hidden——必须先选一个账套才能进主应用。
// 单账套用户此闸自动跳过。E2E 里选第一个账套进场(不新建 · 只做启动必需的选择)。
async function dismissWorkspaceGate(page) {
    const pick = page.locator('#workspace-gate-root [data-wsg-pick]').first();
    const appeared = await pick
        .waitFor({ state: 'visible', timeout: 6_000 })
        .then(() => true)
        .catch(() => false);
    if (!appeared) return;
    await pick.click();
    await page
        .locator('#workspace-gate-root')
        .waitFor({ state: 'detached', timeout: 8_000 })
        .catch(() => {});
}

// 进主应用 · storageState 已注入 mrpilot_token → home.js 不该把我们踢回着陆页
async function enterApp(page) {
    await page.goto('/home');
    // 多账套启动闸先过(否则 sidebar 一直 visibility:hidden)
    await dismissWorkspaceGate(page);
    // 侧栏在 = token 有效、进了主应用(无 token 时 home.js 会 window.location.href='/')
    await expect(page.locator('#sidebar'), '进主应用(token 有效)').toBeVisible({
        timeout: 15_000,
    });
    // 关掉登录账套软弹(若弹)· 让后续点击不被 overlay 拦截
    await dismissWorkspaceModal(page);
}

// 点侧栏入口切到某路由 · 断言对应 page 容器激活
async function openRoute(page, route) {
    await page.locator(`.nav-item[data-route="${route}"]`).first().click();
    await expect(page.locator(`#page-${route}`), `路由 ${route} 页面激活`).toHaveClass(/active/);
}

module.exports = { enterApp, openRoute };
