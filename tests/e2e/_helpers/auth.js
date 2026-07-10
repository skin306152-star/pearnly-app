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
//   - home.js 启动:无 token 直接跳 /login(脸0 前 = '/';/ 现为品牌门户)· 有 token 才进主应用
//   - 普通账号落 /home;超管会被 home.js 弹到 /admin/cost(故测试账号须为普通非超管账号)
//   - token 是 localStorage(非 cookie)· Playwright storageState 会捕获 origin localStorage · 可复用
// ============================================================

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const AUTH_DIR = path.join(__dirname, '..', '.auth');

// storageState 按账号隔离(解 3 窗口并行「session 互踢」文件层根因)
//   - 每个窗口在自己 shell 里设 PEARNLY_E2E_USER → 落到 state-<email短哈希>.json
//   - 不同账号 = 不同文件 · 互不覆盖 token · 各窗口 E2E 可靠并行
//   - 无凭据(CI)→ 'default' 占位(调用方会 test.skip · 文件不会真生成)
function stateFileFor(user) {
    if (!user) return path.join(AUTH_DIR, 'state-default.json');
    const slug = crypto.createHash('sha1').update(user).digest('hex').slice(0, 10);
    return path.join(AUTH_DIR, `state-${slug}.json`);
}

// 模块加载时按当前环境的测试账号定 state 文件(各窗口环境不同 → 文件不同)
const STORAGE_STATE = stateFileFor(process.env.PEARNLY_E2E_USER);

// storageState 新鲜度 · 超时即重登(token 后端给 30 天有效 · 这里只为防极端陈旧 / 跨天残留)
const STATE_TTL_MS = 30 * 60 * 1000;

function hasCreds() {
    return !!(process.env.PEARNLY_E2E_USER && process.env.PEARNLY_E2E_PASS);
}

// 在给定 page 上走一遍真实 UI 登录(不负责存 state)
// 新分层着陆页:登录表单 #form-login 默认即在页面上(登录 tab 默认 active · 无弹窗)
async function doUiLogin(page) {
    const user = process.env.PEARNLY_E2E_USER;
    const pass = process.env.PEARNLY_E2E_PASS;
    if (!user || !pass) {
        throw new Error('缺少 PEARNLY_E2E_USER / PEARNLY_E2E_PASS 环境变量');
    }

    // 脸0(2026-07-10):`/` 改为品牌门户,登录表单挪到 `/login`(门户四卡「登录」按钮亦指此)。
    await page.goto('/login');

    // 登录表单(#form-login):用户名 #li-username · 密码 #li-password · 提交 #btn-login
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
    // 自举鸡生蛋:调用方 spec 的 test.use({ storageState: STORAGE_STATE }) 会把文件路径继承给
    // browser.newContext(),文件还没生成时直接 ENOENT。显式传空 storageState 内存对象覆盖掉继承的
    // 路径(Playwright 原生收 {cookies,origins} 对象),不落占位文件——既免了占位期间同账号并行进程
    // TTL 误判已登录,也免了登录失败时 unlink 掉盘上仍有效的旧 token(仅登录成功才写盘)。
    const ctx = await browser.newContext({ storageState: { cookies: [], origins: [] } });
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
