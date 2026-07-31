// 启动探针失败 → 落哪个门面 · 本地真浏览器验收(跑 static/dist 真构建产物)
// ============================================================
// python http.server 静态服仓库根 + page.route 逐个状态码 stub 探针(同
// _fail_ways_out_local.spec.js 先例)。断言的每句话都来自真词典分片,stub 只兜响应。
//
// 出身(2026-07-30 两轮走查 · 缺陷4):/ai 与 /dms 的 boot().catch 都只分 401 与「无
// status」,其余一律走 resolveGateClosed —— 服务器返 500 时,已受邀的用户看到的是
// 「为邀请制 · 请联系 Pearnly 团队开通访问权限」,唯一出路是退出登录。临时故障被说成
// 永久的权限判定。
//
// 本 spec 钉的就是这张分档表(两个壳同一份,不许有两个说法):
//   500 / 503 → 服务不可用卡(说清不是权限问题)+ 重试
//   404 / 403 → 邀请制卡(这两个是真的闸关/非本入口,语义不动)
//   401       → 登录卡 + 令牌已清
//   断网      → 服务不可用卡(连不上口径)+ 重试,令牌不动
// 反证:把 classifyBootFailure 的 unavailable 那一行去掉,500/503 两语四条当场红。
//
// 起法:npx playwright test tests/e2e/_gate_probe_honesty_local.spec.js
/* global window, document, getComputedStyle */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const localServer = require('./_local_static_server');

const PORT = 8987;
const BASE = `http://127.0.0.1:${PORT}`;
const ARTIFACT_DIR = path.join(__dirname, '_artifacts', 'gate_probe_honesty');

let server;

test.beforeAll(async () => {
    server = await localServer.start(PORT);
    fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
});
test.afterAll(() => localServer.stop(server));

// 被断言的句子(词典里的原文,不是测试自己造的字)。
const COPY = {
    zh: {
        down: '服务器暂时出错了',
        downClause: '不是你的权限有问题',
        offline: '连不上服务器',
        retry: '重试',
        invite: '邀请制',
    },
    th: {
        down: 'เซิร์ฟเวอร์ขัดข้องชั่วคราว',
        downClause: 'ไม่ใช่ปัญหาเรื่องสิทธิ์',
        offline: 'เชื่อมต่อเซิร์ฟเวอร์ไม่ได้',
        retry: 'ลองใหม่',
        invite: 'เฉพาะผู้ได้รับเชิญ',
    },
};

// 两个壳的差异全收在这里:进哪个页、令牌存哪把钥匙、闸探针是哪条 URL。
const SHELLS = {
    ai: {
        page: '/static/dist/ai.html',
        tokenKey: 'mrpilot_token_ai',
        probes: ['**/api/ai/session', '**/api/workorder/orders?**'],
        // 总台/管家两项侧栏入口是探针控显隐的,不能当「进壳了」的判据;看板永远在。
        shellReady: '#navDash',
    },
    dms: {
        page: '/static/dist/dms.html',
        tokenKey: 'mrpilot_token',
        probes: ['**/api/dms/session'],
        shellReady: '#dmsShell.on',
    },
};

function respond(mode) {
    return (route) => {
        if (mode === 'offline') return route.abort('failed');
        return route.fulfill({
            status: mode,
            contentType: 'application/json',
            body: '{"detail":"boom"}',
        });
    };
}

// mode = HTTP 码 | 'offline' | 200(探针照常通过)。/api/me 恒 200:邀请制卡要靠它
// 分辨「未受邀」与「令牌失效」,它挂了就分不出来,那是另一条路。
async function boot(page, shellName, lang, mode) {
    const shell = SHELLS[shellName];
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/me', (r) =>
        r.fulfill({
            contentType: 'application/json',
            body: JSON.stringify({ username: 'stw', tenant_name: 'stw' }),
        })
    );
    if (mode !== 200) {
        // 后注册者优先:探针必须排在上面两条通配之后才拦得住。
        for (const p of shell.probes) await page.route(p, respond(mode));
    }
    await page.addInitScript(
        (cfg) => {
            window.localStorage.setItem(cfg.tokenKey, 'tok-gate-probe');
            window.localStorage.setItem('mrpilot_lang', cfg.lang);
        },
        { tokenKey: shell.tokenKey, lang: lang }
    );
    await page.goto(`${BASE}${shell.page}`);
}

const gateRoot = (page) => page.locator('#gateRoot');

// 卡上量到的真值(可见性 + 计算样式 + 盒子),写进 evidence.json 备查。
async function measure(page) {
    return page.evaluate(() => {
        const title = document.querySelector('#gateDownTitle');
        const retry = document.querySelector('#gateRetryBtn');
        const ic = document.querySelector('.gate-ic-warn');
        const box = (el) => {
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top) };
        };
        return {
            titleText: title ? title.textContent : null,
            titleVisible: title ? getComputedStyle(title).visibility : null,
            retryBox: box(retry),
            retryDisabled: retry ? retry.disabled : null,
            warnIconStroke: ic ? getComputedStyle(ic.querySelector('svg')).stroke : null,
            codeLine: document.querySelector('.gate-code')
                ? document.querySelector('.gate-code').textContent
                : null,
        };
    });
}

const evidence = {};

test.afterAll(() => {
    fs.writeFileSync(
        path.join(ARTIFACT_DIR, 'evidence.json'),
        JSON.stringify(evidence, null, 2) + '\n'
    );
});

for (const shellName of ['ai', 'dms']) {
    test.describe(`/${shellName} 启动探针分档(本地 stub · 真构建产物)`, () => {
        for (const lang of ['zh', 'th']) {
            const c = COPY[lang];

            for (const status of [500, 503]) {
                test(`${status} → 说服务器出错并给重试,不说未受邀(${lang})`, async ({ page }) => {
                    await boot(page, shellName, lang, status);
                    const root = gateRoot(page);
                    await expect(root).toContainText(c.down, { timeout: 15000 });
                    await expect(root).toContainText(c.downClause);
                    await expect(root).toContainText(`HTTP ${status}`);
                    await expect(root).not.toContainText(c.invite);
                    const retry = page.locator('#gateRetryBtn');
                    await expect(retry).toBeVisible();
                    await expect(retry).toHaveText(c.retry);
                    // 令牌不能被故障态顺手清掉(清了 = 用户下次冷启动还得重登)。
                    expect(
                        await page.evaluate(
                            (k) => localStorage.getItem(k),
                            SHELLS[shellName].tokenKey
                        )
                    ).toBe('tok-gate-probe');
                    evidence[`${shellName}-${status}-${lang}`] = await measure(page);
                    await page.screenshot({
                        path: path.join(ARTIFACT_DIR, `${shellName}-${status}-${lang}.png`),
                        fullPage: true,
                    });
                });
            }

            // 404/403 的语义没变:这两个真的是「闸关 / 非本入口」,改坏它同样是缺陷。
            for (const status of [404, 403]) {
                test(`${status} → 仍是邀请制卡(权限判定这一档不许被改掉)(${lang})`, async ({
                    page,
                }) => {
                    await boot(page, shellName, lang, status);
                    const root = gateRoot(page);
                    await expect(root).toContainText(c.invite, { timeout: 15000 });
                    await expect(root).not.toContainText(c.down);
                    await expect(page.locator('#gateRetryBtn')).toHaveCount(0);
                    await page.screenshot({
                        path: path.join(ARTIFACT_DIR, `${shellName}-${status}-${lang}.png`),
                        fullPage: true,
                    });
                });
            }

            test(`401 → 登录卡 + 令牌已清(${lang})`, async ({ page }) => {
                await boot(page, shellName, lang, 401);
                await expect(page.locator('#gateLoginForm')).toBeVisible({ timeout: 15000 });
                await expect(gateRoot(page)).not.toContainText(c.down);
                expect(
                    await page.evaluate((k) => localStorage.getItem(k), SHELLS[shellName].tokenKey)
                ).toBeNull();
                await page.screenshot({
                    path: path.join(ARTIFACT_DIR, `${shellName}-401-${lang}.png`),
                    fullPage: true,
                });
            });

            test(`断网 → 说连不上服务器,不说未受邀(${lang})`, async ({ page }) => {
                await boot(page, shellName, lang, 'offline');
                const root = gateRoot(page);
                await expect(root).toContainText(c.offline, { timeout: 15000 });
                await expect(root).not.toContainText(c.invite);
                await expect(page.locator('#gateRetryBtn')).toBeVisible();
                // 没有状态码就不摆 HTTP 行(摆了就是编一个出来)。
                await expect(page.locator('.gate-code')).toHaveCount(0);
                expect(
                    await page.evaluate((k) => localStorage.getItem(k), SHELLS[shellName].tokenKey)
                ).toBe('tok-gate-probe');
                evidence[`${shellName}-offline-${lang}`] = await measure(page);
                await page.screenshot({
                    path: path.join(ARTIFACT_DIR, `${shellName}-offline-${lang}.png`),
                    fullPage: true,
                });
            });
        }

        // 出路真的通:500 那一屏点重试,后端恢复后就进得去工作台(不用退出登录)。
        test('500 后点「重试」→ 服务恢复即进工作台', async ({ page }) => {
            await boot(page, shellName, 'zh', 500);
            await expect(gateRoot(page)).toContainText(COPY.zh.down, { timeout: 15000 });
            for (const p of SHELLS[shellName].probes) await page.unroute(p);
            await page.locator('#gateRetryBtn').click();
            await expect(page.locator(SHELLS[shellName].shellReady)).toBeVisible({
                timeout: 15000,
            });
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `${shellName}-retry-recovered.png`),
                fullPage: true,
            });
        });

        // 服务器还没好就再点一次:卡还在、按钮回到可点。按下即禁用的那一下若不随重画
        // 复位,用户就被钉在一屏灰按钮上——那还是死胡同,只是换了句话说。
        test('重试时服务器仍 500 → 卡还在,按钮回可点', async ({ page }) => {
            await boot(page, shellName, 'zh', 500);
            const retry = page.locator('#gateRetryBtn');
            await expect(retry).toBeVisible({ timeout: 15000 });
            await retry.click();
            await expect(gateRoot(page)).toContainText(COPY.zh.down);
            await expect(page.locator('#gateRetryBtn')).toBeEnabled();
        });

        // 手机是这一屏的主场景(会计在路上打开发现进不去)。两颗按钮整颗在视口内、
        // 页面不横滚 —— .gate-acts 是新加的一行 flex,窄屏会不会挤出去要量。
        test('390×844 两颗按钮整颗可点 + 页面不横滚', async ({ page }) => {
            await page.setViewportSize({ width: 390, height: 844 });
            await boot(page, shellName, 'zh', 503);
            await expect(gateRoot(page)).toContainText(COPY.zh.down, { timeout: 15000 });
            const geo = await page.evaluate(() => {
                const rect = (sel) => {
                    const r = document.querySelector(sel).getBoundingClientRect();
                    return { left: r.left, right: r.right, w: r.width, h: r.height };
                };
                return {
                    retry: rect('#gateRetryBtn'),
                    logout: rect('#gateLogoutBtn'),
                    vw: window.innerWidth,
                    docW: document.documentElement.scrollWidth,
                };
            });
            expect(geo.docW).toBeLessThanOrEqual(geo.vw);
            for (const b of [geo.retry, geo.logout]) {
                expect(b.left).toBeGreaterThanOrEqual(0);
                expect(b.right).toBeLessThanOrEqual(geo.vw);
                expect(b.h).toBeGreaterThanOrEqual(32); // 触控目标
            }
            evidence[`${shellName}-mobile390`] = geo;
            await page.screenshot({
                path: path.join(ARTIFACT_DIR, `${shellName}-mobile390-zh.png`),
                fullPage: true,
            });
        });

        // 前提自检:探针 200 时本就进工作台 —— 否则上面那条「重试后进得去」不算数。
        test('探针 200 → 直接进工作台(前提自检)', async ({ page }) => {
            await boot(page, shellName, 'zh', 200);
            await expect(page.locator(SHELLS[shellName].shellReady)).toBeVisible({
                timeout: 15000,
            });
            await expect(page.locator('#gateRetryBtn')).toHaveCount(0);
        });
    });
}

// 原报告的场景:/ai 的会话探针 200,是随后那次列表查询 500。同一条 catch,分档必须一样。
test('/ai 只有 listOrders 500(原报告场景)→ 仍落服务不可用卡', async ({ page }) => {
    await page.route('**/api/**', (r) =>
        r.fulfill({ contentType: 'application/json', body: '{}' })
    );
    await page.route('**/api/workorder/orders?**', (r) =>
        r.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"boom"}' })
    );
    await page.addInitScript(() => {
        window.localStorage.setItem('mrpilot_token_ai', 'tok-gate-probe');
        window.localStorage.setItem('mrpilot_lang', 'zh');
    });
    await page.goto(`${BASE}/static/dist/ai.html`);
    await expect(gateRoot(page)).toContainText(COPY.zh.down, { timeout: 15000 });
    await expect(gateRoot(page)).not.toContainText(COPY.zh.invite);
    await page.screenshot({
        path: path.join(ARTIFACT_DIR, 'ai-500-listorders-zh.png'),
        fullPage: true,
    });
});
