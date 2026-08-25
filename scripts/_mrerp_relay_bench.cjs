/*
 * Pearnly · MR.ERP DMS 登录中继时延基准(回归工具 · 2026-08-25)
 *
 * 度量优化后的 about:blank named-popup 登录中继端到端时延:
 *   点按钮 → 弹窗开 → checklogin POST 落 → home.php 加载
 * 并对慢网做鲁棒性验证(延迟 checklogin 响应 → 确认登录不被中断)。
 *
 * 跑法:
 *   PYTHONUTF8=1 node scripts/_mrerp_relay_bench.cjs
 *   DMS_USERNAME / DMS_PASSWORD 可选覆盖(缺省用文档公开测试账号 dmstest)。
 *
 * 只用 Playwright 真浏览器;禁止 HTTP 反向工程。凭据不打印、不写盘。
 */
'use strict';

const { execFileSync } = require('child_process');
const path = require('path');
const { chromium } = require('playwright');

const NORMAL_RUNS = 12;
const SLOW_DELAYS = [3000, 5000];
const HOME_TIMEOUT = 25000;
const USER = process.env.DMS_USERNAME || 'dmstest';
const PASS = process.env.DMS_PASSWORD || 'dmstest';
const ROOT = path.join(__dirname, '..');

function renderRelay() {
    const script = `from services.line_dms.mrerp_portal import render_login_relay; print(render_login_relay("${USER}", "${PASS}")[0])`;
    return execFileSync('python', ['-c', script], {
        cwd: ROOT,
        encoding: 'utf8',
        env: { ...process.env, PYTHONUTF8: '1' },
    });
}

async function measure(browser, relayHtml, delayMs) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    let loginResp = null;
    if (delayMs > 0) {
        await context.route('**/checklogin.php', async (route) => {
            await new Promise((resolve) => setTimeout(resolve, delayMs));
            const response = await route.fetch();
            loginResp = (await response.text()).slice(0, 20);
            await route.fulfill({ response });
        });
    }
    const page = await context.newPage();
    await page.setContent(relayHtml);
    const popupPromise = page.waitForEvent('popup', { timeout: HOME_TIMEOUT });
    const start = Date.now();
    await page.locator('#open-dms').click();
    const popup = await popupPromise;
    let finalUrl = null;
    let reachedHome = false;
    let elapsed = null;
    try {
        await popup.waitForURL(/home\.php/, { timeout: HOME_TIMEOUT });
        reachedHome = true;
        elapsed = Date.now() - start;
        await popup.waitForLoadState('domcontentloaded', { timeout: HOME_TIMEOUT }).catch(() => {});
        await page.waitForTimeout(1200);
        finalUrl = popup.url();
    } catch (_) {
        finalUrl = popup.url();
        elapsed = Date.now() - start;
    }
    await context.close();
    return { elapsed, reachedHome, finalUrl, loginResp };
}

async function main() {
    const relayHtml = renderRelay();
    const browser = await chromium.launch({ headless: true });

    const timings = [];
    for (let i = 0; i < NORMAL_RUNS; i++) {
        const r = await measure(browser, relayHtml, 0);
        timings.push(r.elapsed);
        console.log(`  run ${String(i + 1).padStart(2)}: ${r.elapsed} ms (home=${r.reachedHome})`);
    }

    timings.sort((a, b) => a - b);
    const sum = timings.reduce((acc, v) => acc + v, 0);
    const median = timings[Math.floor(timings.length / 2)];
    const avg = Math.round(sum / timings.length);
    const min = timings[0];
    const max = timings[timings.length - 1];
    const p90 = timings[Math.min(timings.length - 1, Math.floor(timings.length * 0.9))];

    console.log('\n--- Relay timing (normal network) ---');
    console.log(
        `  runs: ${timings.length}  min: ${min}  max: ${max}  avg: ${avg}  median: ${median}  p90: ${p90} ms`
    );
    console.log(`  legacy baseline: ~5800 ms (1800 + 4000)`);
    console.log(
        `  improvement: ~${Math.round(((5800 - median) / 5800) * 100)}% faster (median vs legacy)`
    );

    console.log('\n--- Slow-network robustness (login must not be interrupted) ---');
    for (const delay of SLOW_DELAYS) {
        const r = await measure(browser, relayHtml, delay);
        const ok = r.reachedHome && /home\.php/.test(r.finalUrl || '');
        console.log(
            `  +${delay}ms checklogin: reachedHome=${r.reachedHome} final=${r.finalUrl} elapsed=${r.elapsed}ms => ${ok ? 'OK' : 'FAIL'}`
        );
    }

    await browser.close();
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});
