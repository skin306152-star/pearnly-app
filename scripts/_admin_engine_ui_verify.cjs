/*
 * 一次性真浏览器验收 · 超管「OCR 引擎」页(/admin/engine)
 *
 * 跑法(先起本机 uvicorn 接 docker pearnly-db,再灌样例数据):
 *   node scripts/_admin_engine_ui_verify.cjs
 * 环境变量:BASE(默认 http://127.0.0.1:7861)· ADMIN_USER / ADMIN_PW
 *
 * 断言一律走 getComputedStyle / isVisible / echarts getOption(),不数类名 ——
 * 类名在就报绿是本仓踩过的假绿。截图落 tests/e2e/_artifacts/admin-engine/。
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { chk, summary } = require('./_verify_shared.cjs');

const BASE = process.env.BASE || 'http://127.0.0.1:7861';
const USER = process.env.ADMIN_USER || 'eng_e2e_admin';
const PW = process.env.ADMIN_PW || 'EngE2E!local-2026';
const SHOTS = path.join('tests', 'e2e', '_artifacts', 'admin-engine');

// 截图前先把目标滚进视口:图表挂在页面第三屏,不滚就截到一张看不见图的「证据」。
async function shot(page, name, sel) {
    if (sel) {
        await page.locator(sel).scrollIntoViewIfNeeded();
        await page.waitForTimeout(250);
    }
    await page.screenshot({ path: path.join(SHOTS, name + '.png'), fullPage: false });
    console.log(`  shot  ${name}.png`);
}

async function login() {
    const r = await fetch(`${BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: USER, password: PW }),
    });
    if (!r.ok) throw new Error(`login failed HTTP ${r.status} ${await r.text()}`);
    const d = await r.json();
    const token = d.access_token || d.token;
    if (!token) throw new Error('login response has no token: ' + JSON.stringify(d));
    const me = await fetch(`${BASE}/api/me`, { headers: { Authorization: 'Bearer ' + token } });
    const meJson = await me.json();
    if (!meJson.is_super_admin) throw new Error('account is not super admin');
    return token;
}

/** echarts 实例的真实 option —— 颜色/参考线是不是真画上去了,只有它说了算。 */
function chartOption(page, sel) {
    return page.evaluate((s) => {
        const el = document.querySelector(s);
        const inst = el && window.echarts && window.echarts.getInstanceByDom(el);
        return inst ? JSON.parse(JSON.stringify(inst.getOption())) : null;
    }, sel);
}

function cssVarRgb(page, name) {
    return page.evaluate((n) => {
        const hex = getComputedStyle(document.documentElement).getPropertyValue(n).trim();
        const probe = document.createElement('span');
        probe.style.color = hex;
        document.body.appendChild(probe);
        const rgb = getComputedStyle(probe).color;
        probe.remove();
        return rgb;
    }, name);
}

async function verifyTiers(page) {
    console.log('\n[1] 档位卡片区');
    const cards = page.locator('.eng-tier[data-eng-tier]:not(.eng-tier-auto)');
    chk('四张档位卡渲染 · ' + `count=${await cards.count()}`, (await cards.count()) === 4);
    for (const mode of ['direct35', 'economy', 'qwen', 'selfhost']) {
        chk(
            `卡片 ${mode} 可见`,
            await page.locator(`.eng-tier[data-eng-tier="${mode}"]`).isVisible()
        );
    }
    chk('auto 行保留', await page.locator('.eng-tier-auto').isVisible());

    // 现役卡的高亮必须是真样式(边框换色 + 外圈),不是只挂了个 class
    const live = page.locator('.eng-tier.is-on').first();
    const on = await live.evaluate((el) => {
        const s = getComputedStyle(el);
        return { border: s.borderTopColor, shadow: s.boxShadow };
    });
    const off = await page
        .locator('.eng-tier:not(.is-on)')
        .first()
        .evaluate((el) => getComputedStyle(el).borderTopColor);
    chk('现役卡边框与未选中不同色 · ' + `${on.border} vs ${off}`, on.border !== off);
    chk('现役卡有外圈 · ' + on.shadow, on.shadow !== 'none');
    chk('现役徽章可见', await page.locator('.eng-tier.is-on .eng-tier-live').isVisible());

    // 模型链等宽字体
    const ff = await page
        .locator('.eng-tier[data-eng-tier="qwen"] .eng-tier-models')
        .evaluate((el) => getComputedStyle(el).fontFamily);
    chk('模型链等宽字体 · ' + ff, /mono/i.test(ff));

    // 自部署没实测过 → 三项必须是占位符,不许借别档数字
    const selfhost = await page
        .locator('.eng-tier[data-eng-tier="selfhost"] .eng-tier-metric-v')
        .allInnerTexts();
    chk(
        '自部署三项诚实占位',
        selfhost.every((t) => t.trim() === '—'),
        JSON.stringify(selfhost)
    );

    // qwen 卡的实测数字真的印在页面上
    const qwenTxt = await page.locator('.eng-tier[data-eng-tier="qwen"]').innerText();
    chk('qwen 每页成本可见 · ' + qwenTxt.split('\n').join(' | '), qwenTxt.includes('0.077'));
    chk('qwen 质量分可见', qwenTxt.includes('98%'));
    chk('金标脚注可见', await page.locator('.eng-tier-foot').isVisible());
    await shot(page, '01-tiers');
}

async function verifyTierSwitch(page) {
    console.log('\n[2] 档位切换');
    const qwen = page.locator('.eng-tier[data-eng-tier="qwen"]');
    await qwen.click();
    const checked = await page.locator('.eng-tier[data-eng-tier="qwen"] input').isChecked();
    chk('点卡片选中 radio', checked);
    const cls = await qwen.evaluate((el) => el.classList.contains('is-on'));
    chk('高亮跟着走', cls);
    const others = await page.locator('.eng-tier.is-on').count();
    chk('高亮唯一 · ' + `count=${others}`, others === 1);
    await shot(page, '02-tier-switch-qwen');
    // 验收完切回现役档,别把本地库留在别的档上
    await page.locator('.eng-tier[data-eng-tier="economy"]').click();
}

/**
 * 能力未齐的档不可启用(PARTIAL_MODES 绊线):卡片上要有醒目提示,写侧后端 400 挡回。
 * 2026-08-12 qwen 补齐 document_type + 金标复测过门后 PARTIAL_MODES 清空、qwen 解锁为全局档 ——
 * 本段据此改写:不再有 partial 提示,选 qwen 存全局应 200 成功(旧假设已过时)。
 */
async function verifyPartialMode(page) {
    console.log('\n[2b] C 档已解锁为全局档');
    const noteCount = await page.locator('[data-eng-partial]').count();
    chk(
        '无 partial 提示(2026-08-12 qwen 解锁后 PARTIAL_MODES 清空)',
        noteCount === 0,
        `count=${noteCount}`
    );
    await shot(page, '02b-partial-none', '.eng-tier-grid');

    // qwen 作全局档保存 → 后端放行 200(解锁前此处是 400 挡回)
    await page.locator('.eng-tier[data-eng-tier="qwen"]').click();
    const posted = page.waitForResponse(
        (r) => r.url().includes('/api/admin/ocr-engine') && r.request().method() === 'POST'
    );
    await page.click('#adm-eng-save');
    const resp = await posted;
    chk('全局设成 C 档保存成功 · ' + `status=${resp.status()}`, resp.status() === 200);

    // 存回现役档,别把本地库留在别的档上
    await page.locator('.eng-tier[data-eng-tier="economy"]').click();
    const posted2 = page.waitForResponse(
        (r) => r.url().includes('/api/admin/ocr-engine') && r.request().method() === 'POST'
    );
    await page.click('#adm-eng-save');
    const resp2 = await posted2;
    chk('切回经济档保存成功 · ' + `status=${resp2.status()}`, resp2.status() === 200);

    // 重载确认线上档位回到现役
    await page.reload();
    await page.waitForSelector('.eng-tier');
    const live = await page.locator('.eng-tier.is-on').getAttribute('data-eng-tier');
    chk('重载后线上档位是经济档 · ' + `live=${live}`, live === 'economy');
}

/**
 * 账号灰度机制 2026-08-13 整体退役(Zihao 拍板):页面不再有编辑区,保存请求不再携带
 * overrides_by_account(后端见键即 400)。这里验「真的删干净」而不是「碰巧没渲染」。
 */
async function verifyAccountsRetired(page) {
    console.log('\n[3] 账号灰度已退役');
    chk('灰度编辑区不存在', (await page.locator('#adm-eng-accounts').count()) === 0);
    chk('添加账号按钮不存在', (await page.locator('#adm-eng-acct-add').count()) === 0);
    const saved = page.waitForResponse(
        (r) => r.url().includes('/api/admin/ocr-engine') && r.request().method() === 'POST'
    );
    await page.click('#adm-eng-save');
    const resp = await saved;
    chk('保存返回 200 · ' + `status=${resp.status()}`, resp.status() === 200);
    const body = JSON.parse(resp.request().postData() || '{}');
    chk(
        '保存请求不含 overrides_by_account',
        !('overrides_by_account' in body),
        JSON.stringify(Object.keys(body))
    );
    await shot(page, '03-accounts-retired');
}

async function verifyCostCharts(page) {
    console.log('\n[4] 成本仪表盘 · 柱图 + 参考线');
    await page.waitForSelector('#adm-eng-chart-bar canvas', { timeout: 15000 });
    const box = await page.locator('#adm-eng-chart-bar').boundingBox();
    chk('柱图有实际尺寸 · ' + JSON.stringify(box), box && box.width > 200 && box.height > 200);

    const opt = await chartOption(page, '#adm-eng-chart-bar');
    chk('echarts 实例存在', !!opt);
    const series = opt.series[0];
    const line = series.markLine.data[0];
    chk('参考线钉在 1.5 铢 · ' + `yAxis=${line.yAxis}`, Number(line.yAxis) === 1.5);
    chk(
        '参考线标了「当前定价」',
        String(series.markLine.label.formatter).includes('1.50'),
        String(series.markLine.label.formatter)
    );

    const over = cssVarToHex(await cssVarRgb(page, '--viz-over'));
    const under = cssVarToHex(await cssVarRgb(page, '--viz-under'));
    const wrong = series.data.filter((d) => {
        const c = (d.itemStyle.color || '').toLowerCase();
        return d.value > 1.5 ? c !== over : c !== under;
    });
    chk(
        '超线红 / 未超绿',
        wrong.length === 0,
        `over=${over} under=${under} bad=${JSON.stringify(wrong.map((w) => [w.value, w.itemStyle.color]))}`
    );
    const overCount = series.data.filter((d) => d.value > 1.5).length;
    chk('样例里确有超线入口 · ' + `overCount=${overCount}`, overCount > 0);

    const donut = await chartOption(page, '#adm-eng-chart-pie');
    chk('环形图渲染', !!donut && donut.series[0].type === 'pie');
    chk(
        '未归因单独成片',
        donut.series[0].data.some((d) => /未归因|ไม่ระบุ/.test(d.name)),
        JSON.stringify(donut.series[0].data.map((d) => d.name))
    );
    await shot(page, '07-cost-charts', '#adm-eng-charts');
}

/** getComputedStyle 回来的是 rgb(),echarts option 里是 hex —— 统一成 hex 再比。 */
function cssVarToHex(rgb) {
    const m = rgb.match(/\d+/g);
    if (!m) return rgb;
    return (
        '#' +
        m
            .slice(0, 3)
            .map((n) => Number(n).toString(16).padStart(2, '0'))
            .join('')
    );
}

async function verifyTable(page) {
    console.log('\n[5] 明细表对齐与占位符');
    const th = await page
        .locator('.eng-table th')
        .first()
        .evaluate((el) => getComputedStyle(el).textAlign);
    chk('表头居中 · ' + th, th === 'center');
    const numTd = await page
        .locator('.eng-table tbody tr:first-child td:nth-child(5)')
        .evaluate((el) => getComputedStyle(el).textAlign);
    chk('每页成本列居中 · ' + numTd, numTd === 'center');
    const textTd = await page
        .locator('.eng-table .eng-cell-text')
        .first()
        .evaluate((el) => getComputedStyle(el).textAlign);
    chk('模型列(长文本)靠左 · ' + textTd, textTd === 'left');

    const rows = await page.locator('.eng-table tbody tr').count();
    chk('明细表有行 · ' + `rows=${rows}`, rows > 0);
    const bodyText = await page.locator('.eng-table tbody').innerText();
    chk('页数未知写占位符 —', bodyText.includes('—'));
    chk('未归因行在表里', /未归因|ไม่ระบุ/.test(bodyText));
    const muted = await page
        .locator('.eng-table .eng-row-muted td')
        .first()
        .evaluate((el) => getComputedStyle(el).color);
    const normal = await page
        .locator('.eng-table tbody tr:first-child td')
        .first()
        .evaluate((el) => getComputedStyle(el).color);
    chk('未归因行灰显 · ' + `${muted} vs ${normal}`, muted !== normal);
    await shot(page, '08-cost-table', '.eng-table');
}

async function verifyDaySwitch(page) {
    console.log('\n[6] 天数切换');
    const req = page.waitForRequest((r) => r.url().includes('/costs?days=30'));
    await page.click('[data-eng-days="30"]');
    await req;
    const bg = await page
        .locator('[data-eng-days="30"]')
        .evaluate((el) => getComputedStyle(el).backgroundColor);
    const bgOff = await page
        .locator('[data-eng-days="7"]')
        .evaluate((el) => getComputedStyle(el).backgroundColor);
    chk('选中档底色变化 · ' + `${bg} vs ${bgOff}`, bg !== bgOff);
    await page.waitForSelector('#adm-eng-chart-bar canvas');
    await shot(page, '09-days-30', '#adm-eng-days');
    await page.click('[data-eng-days="7"]');
    await page.waitForSelector('#adm-eng-chart-bar canvas');
}

async function verifyStates(page) {
    console.log('\n[7] 四态');
    // 加载中:把 /costs 压住 2.5 秒,截到真实的 loading 态
    await page.route('**/api/admin/ocr-engine/costs*', async (route) => {
        await new Promise((r) => setTimeout(r, 2500));
        route.continue();
    });
    await page.click('[data-eng-days="90"]');
    await page.waitForSelector('#adm-eng-cost-body [data-eng-state="loading"]');
    chk(
        '加载态可见',
        await page.locator('#adm-eng-cost-body [data-eng-state="loading"]').isVisible()
    );
    await shot(page, '10-state-loading', '#adm-eng-cost-body');
    await page.waitForSelector('#adm-eng-chart-bar canvas', { timeout: 20000 });
    await page.unroute('**/api/admin/ocr-engine/costs*');

    // 空态
    await page.route('**/api/admin/ocr-engine/costs*', (route) =>
        route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ days: 7, rows: [], unattributed: { calls: 0, cost_thb: 0 } }),
        })
    );
    await page.click('[data-eng-days="30"]');
    await page.waitForSelector('#adm-eng-cost-body [data-eng-state="empty"]');
    chk('空态可见', await page.locator('#adm-eng-cost-body [data-eng-state="empty"]').isVisible());
    await shot(page, '11-state-empty', '#adm-eng-cost-body');
    await page.unroute('**/api/admin/ocr-engine/costs*');

    // 错误态 + 重试
    await page.route('**/api/admin/ocr-engine/costs*', (route) =>
        route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"boom"}' })
    );
    await page.click('[data-eng-days="7"]');
    const err = page.locator('#adm-eng-cost-body [data-eng-state="error"]');
    await err.waitFor();
    chk('错误态可见', await err.isVisible());
    const errColor = await err.evaluate((el) => getComputedStyle(el).color);
    const danger = await cssVarRgb(page, '--danger');
    chk('错误态用告警色 · ' + `${errColor} vs ${danger}`, errColor === danger);
    chk('错误态给重试按钮', await page.locator('[data-eng-retry="costs"]').isVisible());
    await shot(page, '12-state-error', '#adm-eng-cost-body');

    await page.unroute('**/api/admin/ocr-engine/costs*');
    await page.click('[data-eng-retry="costs"]');
    await page.waitForSelector('#adm-eng-chart-bar canvas', { timeout: 20000 });
    chk('重试后回到有数据态', await page.locator('.eng-table').isVisible());
    await shot(page, '13-state-data', '#adm-eng-charts');

    // 策略区的加载/错误态
    await page.route('**/api/admin/ocr-engine', (route) =>
        route.request().method() === 'GET'
            ? route.fulfill({ status: 500, contentType: 'application/json', body: '{}' })
            : route.continue()
    );
    await page.reload();
    const perr = page.locator('#adm-eng-policy-body [data-eng-state="error"]');
    await perr.waitFor();
    chk('策略区错误态可见', await perr.isVisible());
    await shot(page, '14-state-policy-error');
    await page.unroute('**/api/admin/ocr-engine');
}

async function verifyFullPage(page) {
    await page.reload();
    await page.waitForSelector('#adm-eng-chart-bar canvas', { timeout: 20000 });
    await page.screenshot({ path: path.join(SHOTS, '15-full-page.png'), fullPage: true });
    console.log('  shot  15-full-page.png');
    console.log('\n[8] 泰语');
    await page.click('#admin-lang-btn');
    await page.click('button[data-admin-lang="th"]');
    await page.waitForSelector('#adm-eng-chart-bar canvas', { timeout: 20000 });
    const title = await page.locator('#page-admin-engine .page-title').innerText();
    chk('标题切泰语 · ' + title, /[฀-๿]/.test(title));
    const tier = await page.locator('.eng-tier[data-eng-tier="economy"]').innerText();
    chk('档位卡切泰语', /[฀-๿]/.test(tier));
    await page.screenshot({ path: path.join(SHOTS, '16-thai.png'), fullPage: true });
    console.log('  shot  16-thai.png');
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const token = await login();
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1440, height: 960 } });
    page.on('pageerror', (e) => {
        chk('页面 JS 报错 · ' + e.message, false);
    });
    await page.addInitScript((t) => localStorage.setItem('mrpilot_token', t), token);
    await page.goto(`${BASE}/admin/engine`, { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('.eng-tier', { timeout: 20000 });

    await verifyTiers(page);
    await verifyTierSwitch(page);
    await verifyPartialMode(page);
    await verifyCostCharts(page);
    await verifyTable(page);
    await verifyDaySwitch(page);
    await verifyAccountsRetired(page);
    await verifyStates(page);
    await verifyFullPage(page);

    await browser.close();
    process.exit(summary());
})().catch((e) => {
    console.error(e);
    process.exit(1);
});
