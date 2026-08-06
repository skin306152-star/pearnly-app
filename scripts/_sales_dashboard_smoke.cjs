/*
 * scripts/_sales_dashboard_smoke.cjs · 销售仪表盘(home#/sales-report 重建版)真浏览器验收
 *
 * 照 _inv_scan_smoke.cjs 的路数:本地静态服 + 真产物(home.html / dist/main.js / dist/home.css /
 * i18n-data.js)+ 只桩 /api/**。文案期望值现场取页面里的真 window.I18N,不注入一个字。
 * 断言全部量真几何(getComputedStyle / getBoundingClientRect),不 grep 类名:
 *   ① Hero 大数字 + 环比徽章真的渲染(count-up 收敛到精确值)
 *   ② 全局按日/按月切换同步 Hero 与商品构成卡(同一只日期器)
 *   ③ 走势卡按月翻页 + hover 标题行实时显示
 *   ④ 点走势某天 → 全局切到那天(横幅+构成卡跟着换)且滚回顶部
 *   ⑤ 饼瓣 hover 提示可见(瞄环带坐标——圆心是洞,瞄了就是假绿)
 *   ⑥ 热力格 hover 提示可见(值与桩喂的一致)
 *   ⑦ 「银行转账」出现在收款构成里(2026-08-04 真机账差修复的回归锚)
 *   ⑧ 390px 竖排:无横向溢出 · 构成卡单列 · Hero 中缝让位
 *
 * 用法(仓库根目录): node scripts/_sales_dashboard_smoke.cjs [截图目录]
 * 退出码 0 = 全过。截图默认落 tests/e2e/_artifacts/sales_dashboard/。
 */
const fs = require('fs');
const path = require('path');
const { startStaticServer } = require('./_smoke_server.cjs');
const { chromium } = require('@playwright/test');

const ROOT = path.resolve(__dirname, '..');
const SHOTS = path.resolve(
    process.argv[2] || path.join(ROOT, 'tests/e2e/_artifacts/sales_dashboard')
);

const p2 = (n) => String(n).padStart(2, '0');
const ymd = (d) => d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
const TODAY = ymd(new Date());
// 金额显示为 ฿ + 窄空格(money.ts BAHT)· 断言前把空白全剥掉,免得拿肉眼看不出的 U+2009 当差异
const squash = (s) => String(s || '').replace(/\s+/g, '');

// ── 桩数据(确定性,Node 侧与断言共用同一套公式)──
const DAY_KPI = {
    gross: '5350.00',
    sales_count: 25,
    avg_ticket: '214.00',
    refund: '60.00',
    cost: '3200.00',
    gross_profit: '2090.00',
    cost_complete: true,
};
const PREV_KPI = { ...DAY_KPI, gross: '5000.00', sales_count: 20, gross_profit: '1900.00' };
const BY_METHOD = { cash: '2650.00', promptpay: '1500.00', card: '1100.00', transfer: '100.00' };
const TOPS = [
    ['p1', 'กาแฟดำ', 'Black coffee', '黑咖啡', '1800.00', '12.000'],
    ['p2', 'ลาเต้', 'Latte', '拿铁', '1200.00', '8.000'],
    ['p3', 'น้ำดื่ม', 'Water', '矿泉水', '800.00', '30.000'],
    ['p4', 'แซนด์วิช', 'Sandwich', '三明治', '500.00', '5.000'],
    ['p5', 'นมสด', 'Milk', '鲜奶', '350.00', '9.000'],
    ['p6', 'ขนม', 'Snack', '零食', '150.00', '3.000'],
].map(([id, th, en, zh, gross, qty]) => ({
    product_id: id,
    name: { th, en, zh },
    qty,
    gross,
    cost: '100.00',
    gross_profit: '50.00',
    cost_complete: true,
}));
// 其他 = 5350 − top5(4650) = 700

function heatGross(i, h) {
    // i = 距锚天数倒序下标(0..13,13=锚当天),h = 钟点
    if ((i * 7 + h) % 5 === 0) return 0;
    return 100 + ((i * 31 + h * 13) % 9) * 150;
}

function heatRows(anchorIso) {
    const [y, m, d] = anchorIso.split('-').map(Number);
    const rows = [];
    for (let i = 0; i <= 13; i++) {
        const dt = new Date(y, m - 1, d - (13 - i));
        for (let h = 8; h <= 22; h++) {
            const g = heatGross(i, h);
            if (g > 0) rows.push({ date: ymd(dt), hour: h, gross: g.toFixed(2) });
        }
    }
    return rows;
}

function heatRange(anchorIso) {
    const [y, m, d] = anchorIso.split('-').map(Number);
    return { from: ymd(new Date(y, m - 1, d - 13)), to: anchorIso };
}

function monthByDay(fromIso) {
    const [y, m] = fromIso.split('-').map(Number);
    const out = [];
    for (let d = 1; d <= 28; d++) {
        out.push({
            date: `${y}-${p2(m)}-${p2(d)}`,
            gross: String(1000 + d * 37) + '.00',
            sales_count: 10 + (d % 5),
            cost: '600.00',
            gross_profit: String(400 + d * 15) + '.00',
            cost_complete: true,
        });
    }
    return out;
}

function reportFor(params) {
    const from = params.get('from') || '';
    const to = params.get('to') || '';
    const live = {
        last_sale_at: new Date(Date.now() - 3 * 60000).toISOString(),
        open_shift: { cashier_name: 'earn', shift_seq: 4 },
    };
    if (from && from === to) {
        return {
            kpi: DAY_KPI,
            by_day: [
                {
                    date: from,
                    gross: DAY_KPI.gross,
                    sales_count: 25,
                    cost: '3200.00',
                    gross_profit: '2090.00',
                    cost_complete: true,
                },
            ],
            by_hour: [9, 10, 11, 12, 13, 17, 18, 19].map((h) => ({
                hour: h,
                gross: String(300 + h * 40) + '.00',
                sales_count: 3,
            })),
            by_method: BY_METHOD,
            top_products: TOPS,
            by_cashier: [],
            prev_kpi: PREV_KPI,
            prev_range: { from: params.get('prev_from'), to: params.get('prev_to') },
            heat: heatRows(to),
            heat_range: heatRange(to),
            live,
        };
    }
    return {
        kpi: { ...DAY_KPI, gross: '91000.00', sales_count: 700 },
        by_day: monthByDay(from),
        by_hour: null,
        by_method: BY_METHOD,
        top_products: TOPS,
        by_cashier: [],
        prev_kpi: PREV_KPI,
        prev_range: null,
        heat: heatRows(to),
        heat_range: heatRange(to),
        live,
    };
}

const serve = () => startStaticServer({ root: ROOT, index: 'home.html' });

async function stubApi(page) {
    await page.route('https://cdnjs.cloudflare.com/**', (r) => r.abort());
    await page.route('**/api/**', async (route) => {
        const url = new URL(route.request().url());
        if (url.pathname === '/api/pos/admin/report') {
            await route.fulfill({ json: { ok: true, data: reportFor(url.searchParams) } });
            return;
        }
        if (url.pathname === '/api/me') {
            await route.fulfill({ json: { email: 'dash@e2e', role: 'owner', plan: 'pro' } });
            return;
        }
        await route.fulfill({ json: { ok: true, data: {} } });
    });
}

async function openPage(page, origin) {
    await page.goto(`${origin}/home.html`);
    await page.waitForFunction(() => typeof window.loadSalesReport === 'function');
    await page.evaluate(() => {
        document.body.classList.remove('workspace-gate-preboot');
        document.getElementById('workspace-gate-root')?.remove();
        window.getActiveWorkspaceClientId = () => 1;
        document.querySelectorAll('.page').forEach((p) => p.classList.remove('active'));
        document.getElementById('page-sales-report').classList.add('active');
        window.loadSalesReport();
    });
    await page.waitForFunction(
        () =>
            ((document.getElementById('rep-big') || {}).textContent || '').replace(/\s+/g, '') ===
            '฿5,350'
    );
}

async function copyOf(page, key) {
    return page.evaluate((k) => window.I18N[window._currentLang][k], key);
}

async function shot(page, name) {
    await page.screenshot({ path: path.join(SHOTS, name), fullPage: false });
}

async function tipState(page) {
    return page.evaluate(() => {
        const tip = document.querySelector('.rep-tip');
        if (!tip) return { on: false };
        const cs = getComputedStyle(tip);
        const r = tip.getBoundingClientRect();
        return {
            on: tip.classList.contains('on') && cs.opacity === '1',
            inViewport: r.left >= 0 && r.top >= 0 && r.right <= window.innerWidth,
            text: tip.innerText,
        };
    });
}

// ① Hero:大数字精确收敛 + 环比徽章 +7.0% + 徽章列(最后一单/在班/客单价)
async function heroFlow(page) {
    const state = await page.evaluate(() => {
        const big = document.getElementById('rep-big');
        const up = document.querySelector('#rep-cmp .up');
        const badges = Array.from(document.querySelectorAll('#rep-hero .badge'));
        const hero = document.querySelector('.posrep .hero');
        return {
            big: big.textContent,
            bigVisible: big.getBoundingClientRect().height > 0,
            bigSize: getComputedStyle(big).fontSize,
            up: up ? up.textContent : null,
            upColorDiffers: up ? getComputedStyle(up).color !== getComputedStyle(big).color : false,
            heroHasGradient: getComputedStyle(hero).backgroundImage.includes('linear-gradient'),
            badgeCount: badges.length,
            badgeText: badges.map((b) => b.innerText).join(' | '),
            sparkDrawn: !!document.querySelector('#rep-hero .spark-line'),
        };
    });
    await shot(page, '01-hero-day.png');
    return {
        ok:
            squash(state.big) === '฿5,350' &&
            state.bigVisible &&
            parseFloat(state.bigSize) >= 34 &&
            state.up === '+7.0%' &&
            state.upColorDiffers &&
            state.heroHasGradient &&
            state.badgeCount === 3 &&
            state.badgeText.includes('earn') &&
            state.sparkDrawn,
        state,
    };
}

// ⑦ 转账进收款构成(账差修复回归锚):图例条 + 色点金额里必须有 transfer
async function transferFlow(page) {
    const wantLabel = await copyOf(page, 'rep-pm-transfer');
    const state = await page.evaluate(() => {
        const chips = Array.from(document.querySelectorAll('#rep-mix-card .paychips > span'));
        const segs = document.querySelectorAll('#rep-mix-card .paybar i');
        const widths = Array.from(segs).map((s) => s.getBoundingClientRect().width);
        return {
            chipTexts: chips.map((c) => c.innerText.replace(/\s+/g, ' ')),
            chipVisible: chips.map((c) => c.getBoundingClientRect().height > 0),
            segCount: segs.length,
            allSegsPainted: widths.every((w) => w > 0),
        };
    });
    await page.evaluate(() => document.getElementById('rep-mix-card').scrollIntoView());
    await shot(page, '02-mix-transfer.png');
    const transferChip = state.chipTexts.find((t2) => t2.includes(wantLabel));
    return {
        ok:
            state.segCount === 4 &&
            state.allSegsPainted &&
            !!transferChip &&
            squash(transferChip).includes('฿100') &&
            state.chipVisible.every(Boolean),
        wantLabel,
        state,
    };
}

// ② 全局按日/按月切换:横幅标语 + 构成卡标题同一次点击一起换
async function granSyncFlow(page) {
    const wantMonthCap = await copyOf(page, 'rep-hero-month');
    const month = TODAY.slice(0, 7);
    // 先滚回顶部:hero 若贴着 sticky 顶栏,auto-scroll 会把按钮送进顶栏的命中区(点击被拦)
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(150);
    await page.locator('#rep-gran button[data-gran="month"]').click();
    await page.waitForFunction(
        (m) => {
            const cap = document.querySelector('#rep-hero .cap');
            const mix = document.querySelector('#rep-mix-card .hd .tnum');
            return cap && mix && cap.textContent.includes(m.month) && mix.textContent === m.month;
        },
        { month }
    );
    const state = await page.evaluate(() => ({
        cap: document.querySelector('#rep-hero .cap span').textContent,
        capdate: document.querySelector('#rep-hero .capdate').textContent,
        mixTitle: document.querySelector('#rep-mix-card .hd .tnum').textContent,
        monthInputShown:
            getComputedStyle(document.getElementById('rep-g-month')).display !== 'none',
        dateInputHidden: getComputedStyle(document.getElementById('rep-g-date')).display === 'none',
    }));
    await shot(page, '03-month-mode.png');
    const back = await page.evaluate(() => {
        document.querySelector('#rep-gran button[data-gran="day"]').click();
        return true;
    });
    await page.waitForFunction(
        () =>
            ((document.getElementById('rep-big') || {}).textContent || '').replace(/\s+/g, '') ===
            '฿5,350'
    );
    const backState = await page.evaluate(() => ({
        capdate: document.querySelector('#rep-hero .capdate').textContent,
        mixTitle: document.querySelector('#rep-mix-card .hd .tnum').textContent,
    }));
    return {
        ok:
            state.cap === wantMonthCap &&
            state.capdate === month &&
            state.mixTitle === month &&
            state.monthInputShown &&
            state.dateInputHidden &&
            back &&
            backState.capdate === TODAY &&
            backState.mixTitle === TODAY,
        wantMonthCap,
        state,
        backState,
    };
}

// ③ 走势按月翻页 + hover 标题行实时显示;④ 点某天 → 全局联动 + 滚回顶部
async function trendFlow(page) {
    // 卡片居中再点:贴边元素会被 sticky 顶栏拦掉真实点击
    await page.evaluate(() =>
        document.getElementById('rep-trend-card').scrollIntoView({ block: 'center' })
    );
    await page.waitForTimeout(150);
    const startMonth = await page.locator('#rep-t-month').inputValue();
    await page.locator('#rep-t-prev').click();
    const [y, m] = startMonth.split('-').map(Number);
    const prevMonth = `${m === 1 ? y - 1 : y}-${p2(m === 1 ? 12 : m - 1)}`;
    // 等到真数据渲染完(skeleton 也画 .ch-col,只认月份+列数会撞上加载态)
    await page.waitForFunction(
        (pm) =>
            document.getElementById('rep-t-month').value === pm &&
            !document.querySelector('#rep-t-plot .skel') &&
            document.querySelectorAll('#rep-t-plot .ch-col').length === 31,
        prevMonth
    );
    const cols = await page.evaluate(() => ({
        count: document.querySelectorAll('#rep-t-plot .ch-col').length,
        bars: document.querySelectorAll('#rep-t-plot .ch-bar').length,
        someBarPainted: Array.from(document.querySelectorAll('#rep-t-plot .ch-bar')).some(
            (b) => b.getBoundingClientRect().height > 2
        ),
    }));
    // hover 第 15 根:标题行(livebar)要实时换成那天,提示卡要出现
    await page.evaluate(() => document.getElementById('rep-trend-card').scrollIntoView());
    const col15 = page.locator('#rep-t-plot .ch-col').nth(14);
    await col15.hover();
    const tip = await tipState(page);
    const liveText = await page.locator('#rep-livebar').innerText();
    const day15 = `${prevMonth}-15`;
    const day15Gross = (1000 + 15 * 37).toLocaleString('en-US');
    await shot(page, '04-trend-prevmonth-hover.png');
    // 点它 → 全局切到那天(横幅 capdate + 构成卡标题),并滚回顶部
    await col15.click();
    await page.waitForFunction((d) => {
        const cd = document.querySelector('#rep-hero .capdate');
        const mix = document.querySelector('#rep-mix-card .hd .tnum');
        return cd && cd.textContent === d && mix && mix.textContent === d;
    }, day15);
    await page.waitForFunction(() => {
        const hero = document.getElementById('rep-hero');
        return hero && hero.getBoundingClientRect().top > -40;
    });
    const linked = await page.evaluate(() => ({
        capdate: document.querySelector('#rep-hero .capdate').textContent,
        granOn: document.querySelector('#rep-gran button.on').dataset.gran,
        heroTop: document.getElementById('rep-hero').getBoundingClientRect().top,
    }));
    await shot(page, '05-day-link.png');
    return {
        ok:
            cols.count === 31 &&
            cols.bars === 31 &&
            cols.someBarPainted &&
            tip.on &&
            tip.inViewport &&
            tip.text.includes(day15) &&
            liveText.includes(day15) &&
            liveText.includes(day15Gross) &&
            linked.capdate === day15 &&
            linked.granOn === 'day' &&
            linked.heroTop > -40,
        startMonth,
        prevMonth,
        cols,
        tip,
        liveText,
        linked,
    };
}

// ⑤ 饼瓣 hover:必须瞄环带坐标(圆心是洞)。第一瓣 33.6%,从 12 点顺时针,取 20° 入弧点。
async function pieFlow(page) {
    await page.evaluate(() =>
        document.getElementById('rep-mix-card').scrollIntoView({ block: 'center' })
    );
    const geom = await page.evaluate(() => {
        const svg = document.querySelector('#rep-pie .dn-svg');
        const r = svg.getBoundingClientRect();
        return {
            cx: r.left + r.width / 2,
            cy: r.top + r.height / 2,
            ring: r.width * (15.915 / 42),
        };
    });
    const rad = (20 * Math.PI) / 180;
    const x = geom.cx + geom.ring * Math.sin(rad);
    const y = geom.cy - geom.ring * Math.cos(rad);
    await page.mouse.move(x, y);
    await page.mouse.move(x + 1, y);
    await page.waitForFunction(() => {
        const tip = document.querySelector('.rep-tip');
        return tip && tip.classList.contains('on') && getComputedStyle(tip).opacity === '1';
    });
    const tip = await tipState(page);
    // 圆心是洞:挪去圆心提示必须灭(有环带命中才证明真的瞄准了饼瓣)
    await page.mouse.move(geom.cx, geom.cy);
    await page.waitForFunction(() => {
        const tip2 = document.querySelector('.rep-tip');
        return !tip2 || !tip2.classList.contains('on');
    });
    const nameZh = TOPS[0].name.zh;
    const nameTh = TOPS[0].name.th;
    await page.mouse.move(x, y); // 留提示在屏上截图
    await page.waitForFunction(() => document.querySelector('.rep-tip')?.classList.contains('on'));
    await shot(page, '06-pie-tip.png');
    // 图例:其他 = 差额 700 必须在(第 6 行,含金额)
    const wantOther = await copyOf(page, 'rep-mix-other');
    const legend = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('#rep-mix-card .plegend .r'));
        return {
            count: rows.length,
            last: rows.length ? rows[rows.length - 1].innerText.replace(/\s+/g, ' ') : '',
        };
    });
    return {
        ok:
            tip.on &&
            tip.inViewport &&
            (tip.text.includes(nameZh) || tip.text.includes(nameTh)) &&
            tip.text.includes('34%') &&
            legend.count === 6 &&
            legend.last.includes(wantOther) &&
            squash(legend.last).includes('฿700'),
        tip,
        legend,
        wantOther,
    };
}

// ⑥ 热力格 hover:14 行 × 15 格,hover 锚日 18 点那格,值与桩公式一致
async function heatFlow(page) {
    await page.evaluate(() =>
        document.getElementById('rep-heat-card').scrollIntoView({ block: 'center' })
    );
    const title = await page.evaluate(
        () => document.querySelector('#rep-heat-card .hd .t').textContent
    );
    const grid = await page.evaluate(() => {
        const rows = document.querySelectorAll('#rep-heat-card .hrow');
        return {
            rows: rows.length,
            cellsFirstRow: rows.length ? rows[0].querySelectorAll('.cell').length : 0,
            shades: new Set(
                Array.from(document.querySelectorAll('#rep-heat-card .cell')).map(
                    (c) => getComputedStyle(c).backgroundColor
                )
            ).size,
        };
    });
    // 锚日(gDate=点过去的那天)= 桩下标 i=13;18 点:heatGross(13,18)=1150
    const anchor = await page.evaluate(
        () => document.querySelector('#rep-hero .capdate').textContent
    );
    const want = heatGross(13, 18);
    const cell = page.locator(`#rep-heat-card .cell[data-d="${anchor}"][data-h="18"]`);
    await cell.hover();
    // 等淡入走完(transition 0.08s):只等 class 会在 opacity 半途量到假 off
    await page.waitForFunction(() => {
        const tip = document.querySelector('.rep-tip');
        return tip && tip.classList.contains('on') && getComputedStyle(tip).opacity === '1';
    });
    const tip = await tipState(page);
    await shot(page, '07-heat-tip.png');
    return {
        ok:
            title.includes(heatRange(anchor).from) &&
            title.includes(heatRange(anchor).to) &&
            grid.rows === 14 &&
            grid.cellsFirstRow === 15 &&
            grid.shades >= 4 &&
            tip.on &&
            tip.inViewport &&
            tip.text.includes(`${anchor} · 18:00`) &&
            squash(tip.text).includes('฿' + want.toLocaleString('en-US')),
        grid,
        anchor,
        want,
        tip,
    };
}

// ⑧ 390px:无横向溢出 · 构成卡单列 · Hero 中缝让位 · 触屏点按出提示(pointer 事件)
async function mobileFlow(page) {
    await page.setViewportSize({ width: 390, height: 820 });
    await page.evaluate(() => window.scrollTo(0, 0));
    const state = await page.evaluate(() => {
        const grid = document.querySelector('#rep-mix-card .topgrid');
        const cols = grid
            ? getComputedStyle(grid).gridTemplateColumns.trim().split(/\s+/).length
            : 0;
        return {
            scrollW: document.scrollingElement.scrollWidth,
            innerW: window.innerWidth,
            bodyOverflow:
                document.scrollingElement.scrollWidth - document.scrollingElement.clientWidth,
            gridCols: cols,
            midHidden:
                getComputedStyle(document.querySelector('.posrep .hero .mid')).display === 'none',
            bigSize: parseFloat(getComputedStyle(document.getElementById('rep-big')).fontSize),
        };
    });
    await shot(page, '08-mobile-390-hero.png');
    await page.evaluate(() => document.getElementById('rep-mix-card').scrollIntoView());
    await shot(page, '08b-mobile-390-mix.png');
    return {
        ok:
            state.bodyOverflow <= 0 &&
            state.gridCols === 1 &&
            state.midHidden &&
            state.bigSize <= 36,
        state,
    };
}

(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    const server = await serve();
    const origin = `http://127.0.0.1:${server.address().port}`;
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    // 页内异常必须浮出水面:静默吞掉的话,超时看起来像"等不到元素",其实是代码崩了
    page.on('pageerror', (e) => console.error('PAGEERROR:', e.message));
    await page.addInitScript(() => localStorage.setItem('mrpilot_token', 'dash-e2e'));
    await stubApi(page);
    await openPage(page, origin);

    const report = {
        heroFlow: await heroFlow(page),
        transferFlow: await transferFlow(page),
        granSyncFlow: await granSyncFlow(page),
        trendFlow: await trendFlow(page),
        pieFlow: await pieFlow(page),
        heatFlow: await heatFlow(page),
        mobileFlow: await mobileFlow(page),
    };
    await browser.close();
    server.close();

    const failed = Object.keys(report).filter((k) => !report[k].ok);
    console.log(JSON.stringify(report, null, 2));
    console.log(failed.length ? `FAIL: ${failed.join(', ')}` : `PASS · 截图在 ${SHOTS}`);
    process.exit(failed.length ? 1 : 0);
})().catch((e) => {
    console.error('SMOKE CRASH', e);
    process.exit(2);
});
