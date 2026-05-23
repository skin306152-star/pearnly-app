// Pearnly E2E · Playwright config
// 阶段 4 Task 4.2 · 第一个 smoke 测试 · 不依赖生产账号
// 默认测 prod 公开登录页(pearnly.com)· PEARNLY_E2E_BASE_URL 可覆盖到 localhost

const { defineConfig, devices } = require('@playwright/test');

const BASE_URL = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';
const IS_CI = !!process.env.CI;

module.exports = defineConfig({
    testDir: './tests/e2e',
    timeout: 30_000,
    expect: { timeout: 5_000 },
    fullyParallel: false,
    workers: 1,
    retries: IS_CI ? 2 : 0,
    forbidOnly: IS_CI,
    reporter: IS_CI ? [['list'], ['github']] : [['list']],
    use: {
        baseURL: BASE_URL,
        headless: true,
        viewport: { width: 1280, height: 800 },
        ignoreHTTPSErrors: true,
        trace: 'on-first-retry',
        video: 'off',
        screenshot: 'only-on-failure',
        actionTimeout: 10_000,
        navigationTimeout: 20_000,
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
});
