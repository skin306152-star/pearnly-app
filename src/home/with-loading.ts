// 给任何触发服务端往返的按钮即时反馈:点击 → 禁用 + 转圈 → 完成/失败必恢复。
// 应用与 DB 同区后单请求已快,但跨境网络仍有几十~上百 ms 空窗;没反馈用户会重复点。
// window 桥:沿用 toast/confirm 同款全局暴露,被各事件 handler 裸调。

type BusyTarget = HTMLElement | null | undefined;

// 已在 busy 的元素(重入/双击)直接复用其进行中的 promise 周期:不重复切换状态、不抢先恢复。
async function withLoading<T>(btn: BusyTarget, fn: () => Promise<T>): Promise<T> {
    const el = btn instanceof HTMLElement ? btn : null;
    const owns = !!el && !el.classList.contains('is-busy');
    const prevDisabled = el instanceof HTMLButtonElement ? el.disabled : false;
    if (owns && el) {
        el.classList.add('is-busy');
        el.setAttribute('aria-busy', 'true');
        if (el instanceof HTMLButtonElement) el.disabled = true;
    }
    try {
        return await fn();
    } finally {
        if (owns && el) {
            el.classList.remove('is-busy');
            el.removeAttribute('aria-busy');
            if (el instanceof HTMLButtonElement) el.disabled = prevDisabled;
        }
    }
}

window.withLoading = withLoading;
