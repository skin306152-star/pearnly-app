// Pearnly E2E · 登录地基 helper · 整顿期 REFACTOR-D1
// ============================================================
// 职责:
//   1) 真站点(pearnly.com)+ 真测试账号 UI 登录(邮箱 + 密码)
//   2) 把登录态(localStorage 里的 mrpilot_token)存成 Playwright storageState
//      让后续 spec 复用 · 不必每个 spec 重登
//
// 铁律(REFACTOR-D1):
//   - 凭据只走环境变量 PEARNLY_E2E_USER / PEARNLY_E2E_PASS · 绝不写文件 / 打印 / commit
//   - 没凭据(CI)→ 调用方用 test.skip 优雅跳过 · 保持 CI 绿
//   - 生成的 .auth/state.json 含 token · 已被 .auth/.gitignore 挡在版本库外
//
// 登录态机制(读 login.html / home.js 实证):
//   - login.html 登录成功 → localStorage.setItem('mrpilot_token', access_token) → 跳 /home
//   - home.js 启动:无 token 直接 window.location.href='/' · 有 token 才进主应用
//   - 普通账号落 /home;超管会被 home.js 弹到 /admin/cost(故测试账号须为普通非超管账号)
//   - token 是 localStorage(非 cookie)· Playwright storageState 会捕获 origin localStorage · 可复用
// ============================================================

const fs = require('fs');
const path = require('path');

const AUTH_DIR = path.join(__dirname, '..', '.auth');
const STORAGE_STATE = path.join(AUTH_DIR, 'state.json');

// storageState 新鲜度 · 超时即重登(token 后端给 30 天有效 · 这里只为防极端陈旧 / 跨天残留)
const STATE_TTL_MS = 30 * 60 * 1000;

function hasCreds() {
    return !!(process.env.PEARNLY_E2E_USER && process.env.PEARNLY_E2E_PASS);
}

// 在给定 page 上走一遍真实 UI 登录(不负责存 state)
// 着陆页登录按钮 [data-open-auth="login"] 打开弹窗 → #form-login 内填邮箱/密码 → #btn-login 提交
async function doUiLogin(page) {
    const user = process.env.PEARNLY_E2E_USER;
    const pass = process.env.PEARNLY_E2E_PASS;
    if (!user || !pass) {
        throw new Error('缺少 PEARNLY_E2E_USER / PEARNLY_E2E_PASS 环境变量');
    }

    await page.goto('/');
    // 打开登录弹窗(着陆页顶栏「登录」)
    await page.locator('[data-open-auth="login"]').first().click();

    // 登录表单(login.html #form-login):邮箱 #li-username · 密码 #li-password · 提交 #btn-login
    const form = page.locator('#form-login');
    await form.locator('#li-username').fill(user);
    await form.locator('#li-password').fill(pass);
    await form.locator('#btn-login').click();

    // 普通账号登录成功 → 跳 /home(超管会跳 /admin/cost · 那种账号不该用于本套测试)
    await page.waitForURL('**/home**', { timeout: 20_000 });
    // 等 token 真正落地 localStorage(storageState 才抓得到)
    await page.waitForFunction(() => !!localStorage.getItem('mrpilot_token'), null, {
        timeout: 10_000,
    });
}

// 确保 storageState 文件存在且新鲜 · 不存在或过期则起一个独立 context 走 UI 登录并保存
// 各 authed spec 在 beforeAll 里调它一次;workers=1 串行,文件落盘后被同一 run 内后续 spec 复用
async function ensureStorageState(browser) {
    if (!hasCreds()) {
        throw new Error('无凭据 · 不应调用 ensureStorageState(调用方应先 test.skip)');
    }
    try {
        const st = fs.statSync(STORAGE_STATE);
        if (Date.now() - st.mtimeMs < STATE_TTL_MS) return STORAGE_STATE;
    } catch {
        /* 文件不存在 · 往下生成 */
    }

    fs.mkdirSync(AUTH_DIR, { recursive: true });
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    try {
        await doUiLogin(page);
        await ctx.storageState({ path: STORAGE_STATE });
    } finally {
        await ctx.close();
    }
    return STORAGE_STATE;
}

module.exports = { STORAGE_STATE, hasCreds, doUiLogin, ensureStorageState };
