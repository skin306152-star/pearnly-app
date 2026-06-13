// 对账中心重设计 · 组件/交互测试(esbuild 打包真控制器 + Playwright 真 DOM)
// 验:初始渲染 / 开始按钮禁用 / 模板中心抽屉随 tab / 导入说明弹窗 / tab 切换换标题+模板+清残留 /
//     真传文件后启用开始 / 移除后重置 / 无 OCR-AI 字眼。
const fs = require('fs');
const path = require('path');
const os = require('os');
const esbuild = require('esbuild');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
let passed = 0,
    failed = 0;
const ok = (c, m) => (c ? (passed++, console.log('  ✓ ' + m)) : (failed++, console.log('  ✗ ' + m)));

(async () => {
    // 1) 打包真控制器(IIFE · 浏览器可直接 eval)
    const bundle = await esbuild.build({
        entryPoints: [path.join(ROOT, 'src/home/recon-center-x.ts')],
        bundle: true,
        format: 'iife',
        write: false,
        logLevel: 'silent',
    });
    const code = bundle.outputFiles[0].text;

    // 2) RCX_HTML + i18n
    const htmlTs = fs.readFileSync(path.join(ROOT, 'src/home/recon-center-x-html.ts'), 'utf8');
    const RCX = htmlTs.match(/export const RCX_HTML = `([\s\S]*?)`;/)[1];
    global.window = {};
    require(path.join(ROOT, 'static/i18n-data.js'));
    const I18N = global.window.I18N;

    // 3) harness 页(stub t/showToast/_reconPollJob;真 RCX_HTML;真控制器)
    const harness = `<!doctype html><html><head><meta charset="utf-8"></head><body>
<section id="page-reconcile"><div class="wrap">${RCX}</div></section>
<script>
  window.I18N = ${JSON.stringify(I18N)};
  window._currentLang = 'zh';
  window.t = function(k){ var d=window.I18N.zh||{}; return d[k]||k; };
  window.showToast = function(m,t){ (window.__toasts=window.__toasts||[]).push([m,t]); };
  window.subscribeI18n = function(){};
  window.localStorage.setItem('mrpilot_token','test');
  // 初译 data-i18n(镜像 page-reconcile.ts)
  document.querySelectorAll('[data-i18n]').forEach(function(el){var k=el.getAttribute('data-i18n');if(window.I18N.zh[k])el.textContent=window.I18N.zh[k];});
</script>
<script>${code}</script>
<script>window.loadReconcilePage && window.loadReconcilePage();</script>
</body></html>`;

    const tmp = path.join(os.tmpdir(), 'rcx_test_' + Date.now() + '.html');
    fs.writeFileSync(tmp, harness);
    const f1 = path.join(os.tmpdir(), 'stmt_test.xlsx');
    const f2 = path.join(os.tmpdir(), 'gl_test.xlsx');
    fs.writeFileSync(f1, 'x');
    fs.writeFileSync(f2, 'x');

    const browser = await chromium.launch();
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', (e) => errs.push(e.message));
    await page.goto('file://' + tmp.replace(/\\/g, '/'), { waitUntil: 'networkidle' });

    console.log('对账中心重设计 · 交互测试');
    ok(errs.length === 0, '控制器加载无 JS 错误' + (errs.length ? ' → ' + errs[0] : ''));

    // 初始:卡片标题 + 开始按钮禁用
    ok((await page.textContent('#rcx-card-left h3')) === '银行账单', '左卡=银行账单');
    ok((await page.textContent('#rcx-card-right h3')) === '总账（GL）', '右卡=总账（GL）');
    ok(await page.isDisabled('#rcx-start-btn'), '初始开始对账禁用');
    ok((await page.locator('#rcx-results.rcx-show').count()) === 0, '初始不显结果指标');
    ok(await page.isVisible('#rcx-balance'), '银行 tab 显余额预检');

    const hasShow = (sel) => page.evaluate((s) => document.querySelector(s).classList.contains('rcx-show'), sel);
    const hasHidden = (sel) => page.evaluate((s) => document.querySelector(s).classList.contains('rcx-hidden'), sel);

    // 模板中心抽屉(银行:2 模板)· 抽屉用 transform 隐藏 → 判 rcx-show 类
    await page.click('#rcx-template-btn');
    ok(await hasShow('#rcx-tplpanel'), '点模板中心→抽屉打开');
    ok((await page.locator('#rcx-template-list .rcx-template-card').count()) === 2, '银行抽屉=2 个模板');
    ok((await page.locator('[data-rcx-dl-doc="statement"]').count()) === 1, '含 statement 模板');
    ok((await page.locator('[data-rcx-dl-doc="gl"]').count()) === 1, '含 gl 模板');
    await page.keyboard.press('Escape');
    ok(!(await hasShow('#rcx-tplpanel')), 'Esc 关抽屉');

    // 导入说明弹窗
    await page.click('#rcx-guide-btn');
    ok(await hasShow('#rcx-guide-modal'), '点导入说明→弹窗打开');
    await page.keyboard.press('Escape');
    ok(!(await hasShow('#rcx-guide-modal')), 'Esc 关弹窗');

    // 切到收入对账:标题/模板换,余额隐藏
    await page.click('[data-rcx-tab="income"]');
    ok((await page.textContent('#rcx-card-left h3')) === '总账（GL）', '收入对账左卡=总账');
    ok((await page.textContent('#rcx-card-right h3')) === '税表（VAT 报告）', '收入对账右卡=税表VAT');
    ok(await hasHidden('#rcx-balance'), '收入对账隐藏余额预检');
    await page.click('#rcx-template-btn');
    ok((await page.locator('[data-rcx-dl-doc="vat"]').count()) === 1, '收入抽屉含 vat 模板');
    await page.keyboard.press('Escape');

    // 切到销项税核查
    await page.click('[data-rcx-tab="tax"]');
    ok((await page.textContent('#rcx-card-left h3')) === '销项税报告', '销项税左卡=销项税报告');
    ok((await page.textContent('#rcx-card-right h3')) === '销售发票明细', '销项税右卡=销售发票明细');

    // 回银行 tab,真传两份文件 → 启用开始
    await page.click('[data-rcx-tab="bank"]');
    await page.setInputFiles('[data-rcx-input="left"]', f1);
    ok((await page.locator('#rcx-card-left.rcx-loaded').count()) === 1, '左卡传文件→已加载态');
    ok(await page.isDisabled('#rcx-start-btn'), '仅一份→开始仍禁用');
    await page.setInputFiles('[data-rcx-input="right"]', f2);
    ok(!(await page.isDisabled('#rcx-start-btn')), '两份就绪→开始启用');

    // 移除一份 → 立即重新禁用
    await page.click('[data-rcx-remove="left"]');
    ok(await page.isDisabled('#rcx-start-btn'), '移除一份→开始立即禁用');

    // 面向用户无 OCR/AI 字眼(只看渲染文本 · innerText 排除 <script>/隐藏)
    await page.evaluate(() => {
        ['rcx-template-btn', 'rcx-guide-btn'].forEach((id) => document.getElementById(id).click());
    });
    const rendered = await page.innerText('#page-reconcile');
    const drawerTxt = await page.innerText('#rcx-tplpanel');
    const guideTxt = await page.innerText('#rcx-guide-modal');
    const allTxt = rendered + ' ' + drawerTxt + ' ' + guideTxt;
    const banned = ['OCR', 'AI', '人工智能', '大模型'];
    const hit = banned.find((w) => allTxt.includes(w));
    ok(!hit, '面向用户无 OCR/AI/人工智能/大模型 字眼' + (hit ? ' → 命中 ' + hit : ''));

    await browser.close();
    console.log(`\n结果:${passed} 通过 / ${failed} 失败`);
    process.exit(failed ? 1 : 0);
})().catch((e) => {
    console.error(e);
    process.exit(1);
});
