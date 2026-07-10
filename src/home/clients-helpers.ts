// ============================================================
// REFACTOR-WB (2026-06-02) · 客户管理 · 纯工具:鉴权/apiClient/颜色/learned 徽章 · 从 clients.js 抽出 · verbatim 0 改逻辑。
// ============================================================

// ---------- 工具 ----------
function authH() {
    return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
}
// 结构化错误(422 detail={code,message:四语字典},见 thai_name_gate.error_payload)附到
// 抛出的 Error 上,不再靠 String(detail) 把整个对象拍扁成 "[object Object]"——调用方
// (如 subject-create.subjectErrorText)按需读 .i18nMessage 直出后端原文,读不到就退化用
// .message(= 业务 code 或 "HTTP {status}")自行映射。detail 是纯字符串时行为不变。
interface ApiError extends Error {
    i18nMessage?: Record<string, string>;
}
async function apiClient(path: string, opts: RequestInit = {}) {
    const r = await fetch(path, {
        ...opts,
        headers: { 'Content-Type': 'application/json', ...authH(), ...(opts.headers || {}) },
    });
    if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        const detail = err.detail;
        const structured = detail && typeof detail === 'object' && typeof detail.code === 'string';
        const code = structured
            ? detail.code
            : typeof detail === 'string'
              ? detail
              : 'HTTP ' + r.status;
        const e = new Error(code) as ApiError;
        if (structured && detail.message && typeof detail.message === 'object') {
            e.i18nMessage = detail.message;
        }
        throw e;
    }
    return r.json();
}

function getActiveColor() {
    const sel = document.querySelector<HTMLElement>('#client-color-picker .color-swatch.active');
    return sel ? sel.dataset.color : '#111111';
}

function _updateLearnedBadge(n: number) {
    const tag = document.getElementById('drawer-cat-learned-tag');
    if (!tag) return;
    // 如果有学过的供应商映射 · badge 显示「已学 N」 · 否则保持「自动建议」默认
    if (n > 0) {
        tag.textContent = (t('drawer-suggest-learned-with-count') || '已学 {n}').replace(
            '{n}',
            String(n)
        );
    }
}

export { authH, apiClient, getActiveColor, _updateLearnedBadge };
