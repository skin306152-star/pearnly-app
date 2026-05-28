// Pearnly · Visual regression Playwright config · REFACTOR-WC-D5(2026-05-28 窗口 C)
//
// 跟主 playwright.config.js 分离:
//   - 主 config testDir = tests/e2e(真账号 17 spec · 流程测试)
//   - 本 config testDir = tests/visual(10 页 screenshot baseline · 视觉回归)
//
// 跑法:npx playwright test --config tests/visual/playwright.visual.config.js
// 出基线:加 --update-snapshots
//
// CI 不跑(2026-05-28 窗口 C 决策 · 见 tests/visual/README.md §3)。
//
// 窗口 C 硬约束:不动 eslint.config.mjs(不在允许清单)· 自洽 disable(同 baseline.spec.js)。
/* eslint-disable no-undef */

const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

const BASE_URL =
    process.env.PEARNLY_VISUAL_BASE_URL ||
    process.env.PEARNLY_E2E_BASE_URL ||
    'https://pearnly.com';
const IS_CI = !!process.env.CI;

module.exports = defineConfig({
    testDir: path.join(__dirname),
    timeout: 60_000,
    expect: {
        timeout: 10_000,
        // 跨平台容忍策略(README §4)
        toHaveScreenshot: {
            // 5% 像素允许不一样(字体抗锯齿 / 微小 layout 抖动)· 大改就 fail
            maxDiffPixelRatio: 0.05,
            // 每个像素的色彩差异 0-1 · 0.2 = 抗锯齿差异内合理放过
            threshold: 0.2,
            // 不在动画里截图 · 等动画稳定
            animations: 'disabled',
            caret: 'hide',
        },
    },
    fullyParallel: false, // 视觉测试 serial 跑 · 避免 login 互相干扰
    workers: 1,
    retries: IS_CI ? 1 : 0,
    forbidOnly: IS_CI,
    reporter: IS_CI ? [['list'], ['github']] : [['list'], ['html', { open: 'never' }]],
    outputDir: path.join(__dirname, 'playwright-output'),

    use: {
        baseURL: BASE_URL,
        headless: true,
        viewport: { width: 1280, height: 800 }, // 桌面端 baseline · 不抖
        ignoreHTTPSErrors: true,
        trace: 'on-first-retry',
        video: 'off',
        screenshot: 'only-on-failure',
        actionTimeout: 10_000,
        navigationTimeout: 30_000,
        // 隐藏滚动条 · 防出现/消失抖动
        launchOptions: {
            args: ['--hide-scrollbars'],
        },
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
});
