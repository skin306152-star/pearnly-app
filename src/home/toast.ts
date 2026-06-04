/* REFACTOR-C1-home-batch6 · Toast / 提示条 / 错误人话化
 * 从 home.js verbatim 抽出(0 逻辑改):showAlert / hideAlerts /
 * _humanizeBackendError / humanizeError / showToast。
 * 这些被 ~38 个 src/home 模块 + home.js 自身(showToast 11 处)裸调,
 * 故每个都 window.X=X 挂出供运行期全局作用域解析。
 * showToast 仍是 eslint 配置里的只读全局(38 模块依赖该声明过 no-undef),
 * 本模块是其唯一定义处;所有调用点都在事件 / 异步 handler 内 →
 * defer 模块就绪后才执行 → 无引导期裸调风险。
 */
/* global escapeHtml */

// ============================================================
// 提示
// ============================================================
function showAlert(type: string, msg: string) {
    const box = document.getElementById('alert-' + type);
    if (!box) return;
    document.getElementById('alert-' + type + '-text')!.textContent = msg;
    box.classList.add('show');
}
function hideAlerts() {
    ['info', 'warn', 'error'].forEach((t) => {
        document.getElementById('alert-' + t)!.classList.remove('show');
    });
}

// [TECH_DEBT §2 P0] 2026-05-15 · 删除 showToast 重复定义(line 13461 旧版)
//   旧版签名 (msg, type) 被 line 14894 新版 (msg, kind, duration) 完全覆盖
//   276 处调用点全部兼容新版(已用脚本核 type 参数:'' / error / info / success 全在新版 kind 白名单)

// v118.35.0.23 · 把后端 HTTPException detail 转成人话(防 [object Object])
// detail 可能是: string / {code, ...其它字段} / pydantic errors[] / 其它对象
type BackendErr = {
    msg?: string;
    code?: string;
    message?: string;
    error?: string;
    detail?: unknown;
};

function _humanizeBackendError(detail: unknown, fallback?: string) {
    if (detail == null) return fallback || '操作失败';
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        // pydantic ValidationError
        const first = (detail[0] as BackendErr) || {};
        if (first.msg) return first.msg;
        return fallback || '请求格式错误';
    }
    if (typeof detail === 'object') {
        // 优先按 code 走 i18n: 'err.<code>'
        if ((detail as BackendErr).code) {
            const k = 'err.' + (detail as BackendErr).code;
            try {
                const tr = t(k, detail);
                if (tr && tr !== k) return tr;
            } catch (e) {
                console.warn('[i18n] t() failed for key:', k, e);
            }
            return (detail as BackendErr).code;
        }
        if ((detail as BackendErr).message) return (detail as BackendErr).message;
        if ((detail as BackendErr).error) return (detail as BackendErr).error;
        if ((detail as BackendErr).detail && typeof (detail as BackendErr).detail === 'string')
            return (detail as BackendErr).detail as string;
        try {
            return JSON.stringify(detail).slice(0, 160);
        } catch (_) {
            /* silent: detail 含循环引用时 stringify 抛错 · 下方 fallback/String(detail) 兜底 */
        }
    }
    return fallback || String(detail);
}

function humanizeError(raw: unknown) {
    if (!raw) return '';
    const r = String(raw);
    if (/ECONNREFUSED|Connection refused/i.test(r))
        return '连接被拒绝 · ERP 地址可能错了,或服务没启动';
    // 问题 A (Zihao 2026-05-19 拍板 · v118.34.25) · 去掉 ">10s" 过时数字
    // (实际 wait_for_selector 30s · retry 3 次 · 累计 ~90s)
    if (/listing fetch failed|wait_for_selector/i.test(r))
        return '拉取 MR.ERP 客户/商品列表超时 · 已重试 3 次仍不通 · 可能 MR.ERP 响应慢 · 稍后再试';
    if (/ETIMEDOUT|timeout/i.test(r)) return '连接超时 · MR.ERP 响应慢 · 稍后再试';
    if (/ENOTFOUND|getaddrinfo/i.test(r)) return '域名解析失败 · ERP 地址拼错了';
    if (/certificate|SSL/i.test(r)) return 'SSL 证书问题 · ERP 站点证书异常';
    if (/401|Unauthorized/i.test(r)) return 'HTTP 401 · 认证失败,检查 Token 是否正确';
    if (/403|Forbidden/i.test(r)) return 'HTTP 403 · 权限不足,ERP 拒绝访问';
    if (/404|Not Found/i.test(r)) return 'HTTP 404 · URL 路径不存在';
    if (/^5\d\d/.test(r) || /500|502|503|504/.test(r))
        return 'ERP 服务器错误 · 不是你的问题,等会儿再试';
    return r;
}

// 简易 toast(右下角冒泡 · 2.5 秒自动消失 · 不阻塞交互)
function showToast(msg: string, kind?: string, duration?: number) {
    let wrap = document.getElementById('mp-toast-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.id = 'mp-toast-wrap';
        document.body.appendChild(wrap);
    }
    kind = kind || 'success';
    // 兼容别名:ok/success/info/warn/warning/error/danger
    if (kind === 'ok') kind = 'success';
    if (kind === 'warning') kind = 'warn';
    if (kind === 'danger') kind = 'error';

    const ICONS = {
        success: '<path d="M3 8l3 3 7-7"/>',
        error: '<circle cx="8" cy="8" r="6"/><path d="M5.5 5.5l5 5M10.5 5.5l-5 5"/>',
        warn: '<path d="M8 2L1.5 13h13L8 2z"/><path d="M8 7v3M8 12v.01"/>',
        info: '<circle cx="8" cy="8" r="6"/><path d="M8 5.5v.01M8 8v3"/>',
        loading: '<path d="M8 1a7 7 0 017 7" stroke-linecap="round" class="mp-toast-spin"/>',
    };

    const toast = document.createElement('div');
    toast.className = 'mp-toast ' + kind;
    toast.innerHTML = `
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            ${ICONS[kind as keyof typeof ICONS] || ICONS.success}
        </svg>
        <span>${escapeHtml(msg)}</span>
    `;
    wrap.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    // v115 · duration 默认 2500ms · 传 0 表示不自动关 · 调用方需手动关
    const dur = typeof duration === 'number' ? duration : 2500;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const dismiss = () => {
        if (timer) {
            clearTimeout(timer);
            timer = null;
        }
        toast.classList.remove('show');
        setTimeout(() => {
            try {
                toast.remove();
            } catch (e) {}
        }, 300);
    };
    if (dur > 0) {
        timer = setTimeout(dismiss, dur);
    }
    return dismiss; // 返回手动关闭函数
}

// ── window 桥(供 home.js + 其它 src/home 模块裸调时全局作用域解析)──
window.showAlert = showAlert;
window.hideAlerts = hideAlerts;
window._humanizeBackendError = _humanizeBackendError;
window.humanizeError = humanizeError;
window.showToast = showToast;
