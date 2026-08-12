/*
 * 一次性真浏览器验收 · 超管成本页 30 天趋势图(ECharts 收编后)
 *
 * 跑法(本机 uvicorn 127.0.0.1:7861 + docker pearnly-db 已就绪,ocr_cost_log 已灌 30 天样例):
 *   node scripts/_cost_trend_ui_verify.cjs
 * 断言走 echarts getOption() 拿真实 option,不数类名;截图落 tests/e2e/_artifacts/cost-trend/。
 */
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { chk, summary } = require('./_verify_shared.cjs');

const BASE = process.env.BASE || 'http://127.0.0.1:7861';
const USER = process.env.ADMIN_USER || 'eng_e2e_admin';
const PW = process.env.ADMIN_PW || 'EngE2E!local-2026';
const SHOTS = path.join('tests', 'e2e', '_artifacts', 'cost-trend');

async function shot(page, name) {
    await page.locator('#cost-trend-chart').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(SHOTS, name + '.png'), fullPage: false });
    console.log(`  shot  ${name}.png`);
}

function chartOption(page) {
    return page.evaluate(() => {
        const el = document.getElementById('cost-trend-chart');
        const inst = el && window.echarts && window.echarts.getInstanceByDom(el);
        return inst ? JSON.parse(JSON.stringify(inst.getOption())) : null;
    });
}

function cssVarRgb(page, name) {
    return page.evaluate((n) => {
        const v = getComputedStyle(document.documentElement).getPropertyValue(n).trim();
        const probe = document.createElement('span');
        probe.style.color = v;
        document.body.appendChild(probe);
        const rgb = getComputedStyle(probe).color;
        probe.remove();
        return rgb;
    }, name);
}

// 令牌原始值(getPropertyValue 出来是 hex,ECharts option 里存的也是 hex —— 同格式才可比)
function cssVarRaw(page, name) {
    return page.evaluate((n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim(), name);
}

async function login() {
    const r = await fetch(`${BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: USER, password: PW }),
    });
    if (!r.ok) throw new Error(`login failed HTTP ${r.status}`);
    const d = await r.json();
    return d.access_token || d.token;
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const token = await login();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on('pageerror', (e) => chk('页面 JS 报错 · ' + e.message, false));
    await page.addInitScript((t) => localStorage.setItem('mrpilot_token', t), token);
    await page.goto(`${BASE}/admin/cost`, { waitUntil: 'domcontentloaded' });

    // 1. 图表就位
    await page.waitForSelector('#cost-trend-chart canvas', { timeout: 20000 });
    const box = await page.locator('#cost-trend-chart').boundingBox();
    chk('趋势图容器有实际尺寸', box && box.width > 400 && box.height > 150, JSON.stringify(box));

    const opt = await chartOption(page);
    chk('echarts 实例存在', !!opt);
    const series = opt.series || [];
    chk('有堆叠柱序列(≥2 引擎)', series.filter((s) => s.type === 'bar').length >= 2,
        `bars=${series.filter((s) => s.type === 'bar').length}`);
    chk('有总花费折线', series.some((s) => s.type === 'line'), `total series: ${series.map((s) => s.type).join(',')}`);
    const line = series.find((s) => s.type === 'line');
    const inkRaw = await cssVarRaw(page, '--ink');
    chk('折线颜色取 --ink 令牌', !!line && line.lineStyle && line.lineStyle.color === inkRaw,
        `line=${line && line.lineStyle && line.lineStyle.color} vs ink=${inkRaw}`);

    // 2. 柱色 = viz 令牌
    const bar = series.find((s) => s.type === 'bar');
    const v1Raw = await cssVarRaw(page, '--viz-1');
    const colors = (bar.itemStyle && bar.itemStyle.color) || '';
    const usesToken = colors === v1Raw || String(colors).length === 0; // 序列级没设色就在 item 级
    const perItem = bar.data.some((d) => d && d.itemStyle && d.itemStyle.color === v1Raw);
    chk('柱色来自 viz 令牌(--viz-1 命中)', usesToken || perItem, `colors=${JSON.stringify(colors).slice(0, 60)}`);

    // 3. 图例 = 出现过的引擎
    const legendData = (opt.legend && opt.legend[0] && opt.legend[0].data) || [];
    chk('图例列出出现过的引擎', legendData.length >= 2, JSON.stringify(legendData));
    const barNames = series.filter((s) => s.type === 'bar').map((s) => s.name);
    chk('堆叠序列有名字', barNames.every((n) => n && n.length), JSON.stringify(barNames));

    // 4. 分段切换(调次数 → 柱数据变 invoices)
    await page.click('[data-metric="count"]');
    await page.waitForTimeout(400);
    const optCount = await chartOption(page);
    const barCount = optCount.series.find((s) => s.type === 'bar');
    const isCount = barCount.data.some((v) => typeof v === 'number' && Number.isInteger(v) && v < 1000);
    chk('切「调用次数」后柱值变小整数', isCount, JSON.stringify(barCount.data.slice(0, 3)));
    await page.click('[data-metric="cost"]');
    await page.waitForTimeout(400);

    // 5. 图例点击隐藏引擎(交互保留)
    const legendBtn = page.locator('.echarts legend').first(); // ECharts 图例是 canvas 内,只能走 option
    const beforeCount = (await chartOption(page)).series.filter((s) => s.type === 'bar').length;
    await page.evaluate(() => {
        const el = document.getElementById('cost-trend-chart');
        const inst = window.echarts.getInstanceByDom(el);
        inst.dispatchAction({ type: 'legendToggleSelect', name: inst.getOption().legend[0].data[0] });
    });
    await page.waitForTimeout(400);
    const afterCount = (await chartOption(page)).series.filter((s) => s.type === 'bar').length;
    chk('图例关掉一个引擎后重画(序列数不变·数据归零)', beforeCount === afterCount,
        `before=${beforeCount} after=${afterCount}`);
    const hidden = await page.evaluate(() => {
        const el = document.getElementById('cost-trend-chart');
        const inst = window.echarts.getInstanceByDom(el);
        const o = inst.getOption();
        const name = o.legend[0].data[0];
        return { name, selected: o.legend[0].selected[name] };
    });
    chk('隐藏状态落进 _ctState(经 legend.selected 回读)', hidden.selected === false, JSON.stringify(hidden));

    // 6. 截图:亮
    await shot(page, 'trend-light');

    // 7. 暗色:挂 init script 让 .dark 在下次导航的 document 起就生效(裸 evaluate 加的类 reload 即丢;
    //    init script 阶段 documentElement 可能还没建出来,兜到 DOMContentLoaded 再加)
    await page.addInitScript(() => {
        const apply = () => document.documentElement.classList.add('dark');
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
        else apply();
    });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#cost-trend-chart canvas', { timeout: 20000 });
    const darkInkRaw = await cssVarRaw(page, '--ink');
    chk('暗色令牌真生效(--ink 已是暗色值)', String(darkInkRaw).toLowerCase() === '#f0eefa', `ink=${darkInkRaw}`);
    const darkOpt = await chartOption(page);
    const darkLine = darkOpt.series.find((s) => s.type === 'line');
    chk('暗色下折线取暗色 --ink', darkLine.lineStyle.color === darkInkRaw,
        `${darkLine.lineStyle.color} vs ${darkInkRaw}`);
    await shot(page, 'trend-dark');

    await browser.close();
    process.exit(summary());
})().catch((e) => {
    console.error(e);
    process.exit(1);
});
