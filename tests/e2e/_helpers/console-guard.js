// Pearnly E2E · console.error / pageerror 守门 · REFACTOR-D1
// ============================================================
// 照 smoke.spec.js 的做法:全程收集 console.error + pageerror · 收尾断言为空 ·
// 用来抓 subscribeI18n 类「页面看着没事、控制台在尖叫」的隐患。
//
// 与 smoke 的差异:登录后真实业务页会打到真后端,偶发少量与被测功能无关的浏览器/
// 三方噪声(favicon 404、ResizeObserver loop、analytics beacon 失败)。这些不是
// 应用 bug,放进 IGNORE 白名单避免假红。白名单刻意保持最小 · 任何应用自身的报错
// 都不在内 · 仍会让 spec 变红。
// ============================================================

// 已知良性噪声(与被测功能无关)· 命中即忽略 · 保持最小
const IGNORE = [
    /favicon/i, // favicon 404
    /ResizeObserver loop/i, // 浏览器布局回调噪声 · 非错误
    /Failed to load resource.*\b(analytics|gtag|googletagmanager|sentry|clarity|hotjar|facebook|fbevents)\b/i,
    /net::ERR_.*\b(analytics|gtag|googletagmanager|sentry|clarity|hotjar|facebook)\b/i,
];

function isIgnorable(text) {
    return IGNORE.some((re) => re.test(text || ''));
}

// 在 page 上挂收集器 · 返回 { consoleErrors, pageErrors }
function attachConsoleGuard(page) {
    const consoleErrors = [];
    const pageErrors = [];
    page.on('console', (msg) => {
        if (msg.type() === 'error' && !isIgnorable(msg.text())) consoleErrors.push(msg.text());
    });
    page.on('pageerror', (err) => {
        if (!isIgnorable(err.message)) pageErrors.push(err.message);
    });
    return { consoleErrors, pageErrors };
}

// 收尾断言:无未过滤的 pageerror / console.error。
// opts.allow:spec 声明式豁免额外的 console.error 噪声(如切业态过渡期的 403 资源载入)——
// 走共用接口而非各 spec 直改 guard.consoleErrors 数组。pageerror 永不豁免(未捕获 JS 异常)。
function assertNoConsoleErrors(expect, guard, { allow = [] } = {}) {
    const consoleErrors = guard.consoleErrors.filter((e) => !allow.some((re) => re.test(e || '')));
    expect(
        guard.pageErrors,
        `pageerror(uncaught JS 异常): ${guard.pageErrors.join(' | ')}`
    ).toEqual([]);
    expect(consoleErrors, `console.error: ${consoleErrors.join(' | ')}`).toEqual([]);
}

module.exports = { attachConsoleGuard, assertNoConsoleErrors, isIgnorable };
