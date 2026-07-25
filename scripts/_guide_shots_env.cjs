// 配图生成的运行环境:静态文件服务器 + 假后端 + 三种启动态(scene)。
// 拆分自 _guide_shots.cjs —— 这里只管「把页面弄到可截的状态」,不认识任何一张图。
/* eslint-disable no-undef */
const path = require('path');
const { apiBody, ocrResult, INVOICE_HTML, SUBJECTS } = require('./_guide_shots_data.cjs');
const { serveStatic, dropWorkspaceGate } = require('./_verify_shared.cjs');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'static', 'guide', 'shots');
const PORT = 8798;
const VIEWPORT = { width: 1440, height: 900 };
// 每种语言各截一套:中文正文配中文界面图,泰文配泰文。混用会让读者对不上号。
const LANGS = ['zh', 'th'];

const serve = () => serveStatic(PORT);

// 复核屏右侧的原图查看器要真图,不是 JSON —— 单独渲一张示例税票 PNG 回给 page/N.png。
let invoicePng = null;
async function prepareInvoicePng(ctx) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: 760, height: 1040 });
    await page.setContent(INVOICE_HTML);
    invoicePng = await page.screenshot({ fullPage: true });
    await page.close();
}

async function mockApi(page, lang) {
    await page.route('**/api/**', (route) => {
        const req = route.request();
        const url = req.url();
        if (/\/api\/history\/[^/]+\/page\/\d+\.png/.test(url))
            return route.fulfill({
                status: 200,
                contentType: 'image/png',
                headers: { 'X-Page-Count': '1' },
                body: invoicePng,
            });
        // 一批两张票 · 靠 multipart 头里的文件名分辨是哪一张(并发识别,顺序不可靠)。
        if (url.includes('/api/ocr/recognize') || url.includes('/api/ocr/submit')) {
            const head = String(req.postDataBuffer() || '').slice(0, 4096);
            return route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(ocrResult(head.includes('07-02'))),
            });
        }
        const body = apiBody(url, lang) || { ok: true };
        return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(body),
        });
    });
}

async function boot(ctx, lang) {
    const page = await ctx.newPage();
    await page.addInitScript(
        (a) => {
            localStorage.setItem('mrpilot_token', 'tok');
            localStorage.setItem('mrpilot_lang', a.lang);
            localStorage.setItem('pearnly_active_workspace_client_id', String(a.ws));
        },
        { lang, ws: SUBJECTS[0].id }
    );
    await mockApi(page, lang);
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.routeTo === 'function');
    await dropWorkspaceGate(page);
    await page.evaluate(() => {
        window._userInfo = Object.assign(window._userInfo || {}, {
            can_push_erp: true,
            can_view_history: true,
            plan: 'lifetime',
            role: 'owner', // 顶栏切换器的「新建主体 / 管理全部客户」页脚只对老板出现
        });
        window.routeTo('dms-intake');
    });
    await page.waitForSelector('#dx-inv-drop', { timeout: 15000 });
    await page.waitForTimeout(500);
    return page;
}

// 套账硬门只在「没选过账套」时盖屏。与 boot 的差别只有两处:不注入已选账套、不拆门。
async function bootGate(ctx, lang) {
    const page = await ctx.newPage();
    await page.addInitScript((lg) => {
        localStorage.setItem('mrpilot_token', 'tok');
        localStorage.setItem('mrpilot_lang', lg);
        // 硬门的场景前提就是「一个都还没选」· 同 context 的前几张图留下的选择要清掉。
        localStorage.removeItem('pearnly_active_workspace_client_id');
    }, lang);
    await mockApi(page, lang);
    await page.goto('http://localhost:' + PORT + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.showWorkspaceGate === 'function');
    await page.evaluate(() => {
        window.isOwner = () => true;
        window.showWorkspaceGate();
    });
    await page.waitForSelector('.wsg-card', { timeout: 15000 });
    await page.waitForTimeout(500);
    return page;
}

// 登录页由 landing.js 独立渲染,不在 home 主页面里 —— 不带 token 直接开 /login。
async function bootLogin(ctx, lang) {
    const page = await ctx.newPage();
    await page.addInitScript((lg) => localStorage.setItem('mrpilot_lang', lg), lang);
    await mockApi(page, lang);
    await page.goto('http://localhost:' + PORT + '/login', { waitUntil: 'load' });
    await page.waitForSelector('.auth-card .language-switcher button', { timeout: 15000 });
    await page.waitForTimeout(900);
    return page;
}

// scene → 启动器。main 是原有的「已进系统 · 停在录入工作台」。
const BOOTS = { main: boot, wb: boot, review: boot, pages: boot, login: bootLogin, gate: bootGate };

module.exports = { OUT, VIEWPORT, LANGS, BOOTS, serve, prepareInvoicePng };
