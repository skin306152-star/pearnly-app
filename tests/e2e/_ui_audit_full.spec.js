// 全站界面层抓图(安全·只导航+只读打开+渲染型弹窗·绝不点删除/提交/推送)
// 跑: $env:PEARNLY_E2E_USER=...; $env:PEARNLY_E2E_PASS=...; npx playwright test tests/e2e/_ui_audit_full.spec.js --reporter=line
// 产出: scripts/_ui_audit_full/*.png + manifest.json
/* eslint-disable */
/* global window, location, getComputedStyle, document */
const { test } = require('@playwright/test');
const { doUiLogin } = require('./_helpers/auth');
const fs = require('fs');
const OUT = 'scripts/_ui_audit_full';
fs.mkdirSync(OUT, { recursive: true });

const ROUTES = [
    'dashboard',
    'ocr',
    'history',
    'reconcile',
    'automation',
    'sales-invoices',
    'sales-account',
    'sales-products',
    'sales-report',
    'receivables',
    'clients',
    'purchase',
    'purchase-inbox',
    'purchase-suppliers',
    'purchase-settings',
    'vouchers',
    'inventory',
    'pos-onboarding',
    'pos-cashiers',
    'pos-tables',
    'pos-payment',
    'knowledge',
    'exceptions',
    'integrations',
];

async function killWs(page) {
    await page
        .evaluate(() => {
            const m = document.getElementById('ws-modal');
            if (m) m.remove();
            const p = document.querySelector('[data-ws-personal]');
            if (p) p.click();
        })
        .catch(() => {});
}
async function shot(page, name, m) {
    try {
        await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
        m.push({ name, ok: true });
    } catch (e) {
        m.push({ name, ok: false, err: String(e).slice(0, 80) });
    }
}
async function esc(page) {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(250);
    await page
        .evaluate(() => {
            document.querySelectorAll('.modal-mask,.drawer-mask,[class*=mask]').forEach((el) => {
                const s = getComputedStyle(el);
                if (s.position === 'fixed') el.remove();
            });
        })
        .catch(() => {});
}

test('full surface audit', async ({ page }) => {
    test.setTimeout(600000);
    const m = [];
    await page.setViewportSize({ width: 1440, height: 900 });
    await doUiLogin(page);
    await page.waitForTimeout(2500);

    // L1: 账套选择弹窗(首次自动弹)先抓
    await shot(page, 'L1-ws-modal-账套选择', m);
    await killWs(page);

    // L0 顶层屏 · 浅色
    for (const r of ROUTES) {
        try {
            await page.evaluate((x) => {
                window.navigateTo ? window.navigateTo(x) : (location.hash = '#/' + x);
            }, r);
            await page.waitForTimeout(1300);
            await killWs(page);
            await page.waitForTimeout(300);
            await shot(page, `L0-${r}`, m);
        } catch (e) {
            m.push({ name: 'L0-' + r, ok: false, err: String(e).slice(0, 80) });
        }
    }

    // L0 暗夜(强制 .dark 类)· 抓几个代表 + 全部
    await page.evaluate(() => document.documentElement.classList.add('dark'));
    for (const r of ROUTES) {
        try {
            await page.evaluate((x) => {
                window.navigateTo ? window.navigateTo(x) : (location.hash = '#/' + x);
            }, r);
            await page.waitForTimeout(1100);
            await killWs(page);
            await page.waitForTimeout(250);
            await shot(page, `DARK-${r}`, m);
        } catch (e) {}
    }
    await page.evaluate(() => document.documentElement.classList.remove('dark'));
    await page.waitForTimeout(300);

    // L1 安全打开:渲染型全局函数(无副作用)
    const openers = [
        ['L1-settings-设置弹窗', 'openSettingsModal'],
        ['L1-cmdk-命令面板', 'openCmdk'],
        ['L1-rules-归档规则', 'openRulesSettings'],
        ['L1-camera-tips-拍照贴士', 'showCameraTips'],
        ['L1-help-帮助', 'openHelpModal'],
    ];
    for (const [name, fn] of openers) {
        try {
            const ok = await page.evaluate((f) => {
                if (typeof window[f] === 'function') {
                    try {
                        window[f]();
                        return true;
                    } catch (e) {
                        return false;
                    }
                }
                return false;
            }, fn);
            if (ok) {
                await page.waitForTimeout(900);
                await shot(page, name, m);
                await esc(page);
            } else m.push({ name, ok: false, err: 'no global fn' });
        } catch (e) {
            m.push({ name, ok: false, err: String(e).slice(0, 60) });
        }
    }

    // L1 抽屉/详情:点列表首行打开(只读)· 选择器按各屏真实渲染类名(2026-06-10 修)
    const rowOpens = [
        ['history', 'L1-drawer-识别结果抽屉', '.history-row[data-hid]'],
        ['purchase', 'L1-进项单据详情', '#pur-body .row[data-id]'],
        ['sales-invoices', 'L1-销项单据详情', '#page-sales-invoices table.sx-tbl tr.click'],
        ['clients', 'L1-客户抽屉', '#buyer-tbody .cust-row[data-cid] .cust-cell-name'],
        ['exceptions', 'L1-异常抽屉', '.exc-row[data-exc-id] .exc-row-main, .exc-row[data-exc-id]'],
    ];
    for (const [route, name, sel] of rowOpens) {
        try {
            await page.evaluate((x) => {
                window.navigateTo ? window.navigateTo(x) : (location.hash = '#/' + x);
            }, route);
            await page.waitForTimeout(1500);
            await killWs(page);
            // killWs 点「个人事务」会触发套账切换遮罩(กำลังเปลี่ยน…)盖住页面吃掉行点击 · 等它消失
            await page.waitForTimeout(2200);
            const el = page.locator(sel).first();
            if (await el.isVisible().catch(() => false)) {
                await el.click({ timeout: 2500 }).catch(() => {});
                await page.waitForTimeout(1600);
                await shot(page, name, m);
                await esc(page);
            } else m.push({ name, ok: false, err: 'no row' });
        } catch (e) {
            m.push({ name, ok: false, err: String(e).slice(0, 60) });
        }
    }

    // L0.5 开票向导 5 步(只走步不开出:第 5 步绝不再点 sw-next)· 顺带抓步间校验错误态
    try {
        await page.evaluate(() => {
            window.navigateTo
                ? window.navigateTo('sales-invoices')
                : (location.hash = '#/sales-invoices');
        });
        await page.waitForTimeout(1200);
        await killWs(page);
        const okWiz = await page.evaluate(() => {
            if (typeof window.openSalesWizard === 'function') {
                window.openSalesWizard();
                return true;
            }
            return false;
        });
        if (okWiz) {
            await page.waitForTimeout(1200);
            for (let step = 1; step <= 5; step++) {
                await shot(page, `L05-wizard-step${step}`, m);
                if (step === 5) break; // 第 5 步「开出」按钮绝不点
                const next = page.locator('#sw-next');
                if (!(await next.isVisible().catch(() => false))) break;
                await next.click({ timeout: 2000 }).catch(() => {});
                await page.waitForTimeout(900);
            }
            await esc(page);
            await esc(page);
        } else m.push({ name: 'L05-wizard', ok: false, err: 'no openSalesWizard' });
    } catch (e) {
        m.push({ name: 'L05-wizard', ok: false, err: String(e).slice(0, 60) });
    }

    // L2 抽屉里的嵌套面(只读):识别抽屉里滚到底部细节区
    try {
        await page.evaluate(() => {
            window.navigateTo ? window.navigateTo('history') : (location.hash = '#/history');
        });
        await page.waitForTimeout(1500);
        await killWs(page);
        const row = page.locator('.history-row[data-hid]').first();
        if (await row.isVisible().catch(() => false)) {
            await row.click({ timeout: 2500 }).catch(() => {});
            await page.waitForTimeout(1100);
            await page
                .evaluate(() => {
                    const d = document.querySelector(
                        '.drawer-body,.drawer-content,[class*=drawer]'
                    );
                    if (d) d.scrollTop = d.scrollHeight;
                })
                .catch(() => {});
            await page.waitForTimeout(400);
            await shot(page, 'L2-识别抽屉-底部', m);
            await esc(page);
        }
    } catch (e) {}

    // L1 集成配置抽屉:点第一个"设置"
    try {
        await page.evaluate(() => {
            window.navigateTo
                ? window.navigateTo('integrations')
                : (location.hash = '#/integrations');
        });
        await page.waitForTimeout(1200);
        await killWs(page);
        const b = page.getByText('ตั้งค่า', { exact: false }).first();
        if (await b.isVisible().catch(() => false)) {
            await b.click({ timeout: 2500 }).catch(() => {});
            await page.waitForTimeout(900);
            await shot(page, 'L1-集成配置抽屉', m);
            await esc(page);
        }
    } catch (e) {}

    fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(m, null, 2));
});
