// T8 向导收口验证截图:把【本地新 build】的 wizard/steps + 新 i18n 注入 prod /home,
// 用 mock 端点驱动 3 个状态(open 无 id → 不发 API → 不动 prod 数据)。只读验证。
/* eslint-disable no-undef */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.resolve(__dirname, '..', 'outputs', 't8-verify');
fs.mkdirSync(OUT, { recursive: true });
const BASE = 'https://pearnly.com';
const ACCT = { username: 'pearnly_e2e_3', password: 'Pe@rnly-E2E-3p4' };
const stepsJs = fs.readFileSync(path.join(OUT, 'steps.js'), 'utf8');
const wizardJs = fs.readFileSync(path.join(OUT, 'wizard.js'), 'utf8');
const NEWKEYS = {
    'exp-skip-download': '我已经装过了 · 跳过下载',
    'exp-acct-mirror-hint': '账套在小助手窗口里选择,这里同步显示当前状态。',
    'exp-acct-selected-mirror': '已选账套:{x}(在小助手里选 / 改)',
    'exp-acct-wait-select': '请在小助手窗口里选择你的账套。',
};

(async () => {
    const b = await chromium.launch();
    const ctx = await b.newContext({ viewport: { width: 1340, height: 1000 } });
    const page = await ctx.newPage();
    const resp = await page.request.post(BASE + '/api/login', { data: ACCT });
    const token = (await resp.json()).token;
    if (!token) { console.log('login FAIL'); process.exit(1); }
    await page.addInitScript((t) => localStorage.setItem('mrpilot_token', t), token);
    await page.goto(BASE + '/home', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => typeof window.t === 'function', { timeout: 25000 });
    // 消 workspace 门(preboot 遮罩盖住弹窗)
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        const st = document.createElement('style');
        st.textContent = '#ws-modal{display:none!important}#workspace-gate-root{display:none!important}';
        document.head.appendChild(st);
    });
    await page.waitForTimeout(1500);
    // 注入新 i18n key(prod 旧 bundle 没有这些)+ 覆盖为本地新 build 的组件
    await page.evaluate((nk) => {
        const orig = window.t;
        window.t = (k) => (nk[k] !== undefined ? nk[k] : (orig ? orig(k) : k));
    }, NEWKEYS);
    await page.addScriptTag({ content: stepsJs });
    await page.addScriptTag({ content: wizardJs });
    const has = await page.evaluate(() => !!(window.ExpressWizard && window.ExpressSteps));
    console.log('components injected:', has);

    async function shot(name, opener) {
        await page.evaluate(() => document.getElementById('exp-wiz-overlay')?.remove());
        await page.evaluate(opener);
        await page.waitForSelector('#exp-wiz-overlay', { timeout: 6000 });
        await page.waitForTimeout(600);
        const probe = await page.evaluate(() => ({
            skipBtn: !!document.getElementById('exp-skip-download'),
            acctList: !!document.getElementById('exp-acctlist'),
            mirror: document.getElementById('exp-acct-mirror')?.textContent || null,
            mirrorCls: document.getElementById('exp-acct-mirror')?.className || null,
        }));
        console.log(name, JSON.stringify(probe));
        await page.screenshot({ path: path.join(OUT, name + '.png'), fullPage: true });
    }

    // 1) 下载不强制 + 未选账套镜像(open 无配置)
    await shot('1-download-optional-and-wait-mirror', () => window.ExpressWizard.open({}));
    // 2) 已选账套镜像(小助手已上报 cfg.account_set)
    await shot('2-selected-mirror', () =>
        window.ExpressWizard.open({ config: { account_set: 'DATAT' } }));

    console.log('shots ->', OUT);
    await b.close();
})();
