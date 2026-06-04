// ============================================================
// REFACTOR-WB-C1 · Session 心跳(v118.32.5.5.13)— 从 home.js 抽出为 ES module
//
// 自包含 IIFE:15 秒 ping /api/me + 切回 tab 立即 check · 401 即踢被挤掉的设备。
//   消费全局 t/showToast/_showSessionRevokedModal(均 home.js 顶层 function · window 可达)。
//   暴露 window._sessionCheck(调试用 · 保留)。自启动(有 token 即开心跳)。
// 加载顺序:home.js(sync)先跑暴露全局 → 本 module(Vite · defer)后跑。
// verbatim 搬迁 · 0 逻辑改。
// ============================================================
/* global _showSessionRevokedModal */
(function () {
    'use strict';
    let _hbTimer: ReturnType<typeof setInterval> | null = null;
    let _hbRunning = false;
    async function _sessionCheck() {
        if (_hbRunning) return;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        _hbRunning = true;
        try {
            const r = await fetch('/api/me', {
                headers: { Authorization: 'Bearer ' + tk },
                cache: 'no-store',
            });
            if (r.status === 401) {
                const body = await r.json().catch(() => ({}));
                const detail = body && body.detail;
                let code = '';
                if (typeof detail === 'string') code = detail;
                else if (detail && typeof detail === 'object') code = detail.code || '';
                console.warn('[heartbeat] session revoked', code);
                localStorage.removeItem('mrpilot_token');
                if (_hbTimer) {
                    clearInterval(_hbTimer);
                    _hbTimer = null;
                }
                if (code === 'auth.session_revoked') {
                    try {
                        _showSessionRevokedModal();
                    } catch (_) {
                        window.location.href = '/';
                    }
                } else {
                    const _msgKey =
                        code === 'auth.password_changed_relogin'
                            ? 'alert-password-changed-relogin'
                            : 'alert-session';
                    try {
                        if (typeof showToast === 'function' && typeof t === 'function') {
                            showToast(t(_msgKey), 'error');
                        } else {
                            alert('Session expired');
                        }
                    } catch (_) {
                        /* silent: 提示展示失败(无 showToast/alert)不阻断下方登出跳转 */
                    }
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1500);
                }
            }
        } catch (e) {
            // 网络错忽略 · 下个 tick 再试
        } finally {
            _hbRunning = false;
        }
    }
    function _startHeartbeat() {
        if (_hbTimer) clearInterval(_hbTimer);
        _hbTimer = setInterval(_sessionCheck, 15000); // 15 秒
    }
    // 启动
    if (localStorage.getItem('mrpilot_token')) {
        _startHeartbeat();
    }
    // 切回 tab 立即 check(关键 · 用户离开后回来第 1 秒就被踢)
    window.addEventListener('focus', _sessionCheck);
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden) _sessionCheck();
    });
    // 暴露调试
    window._sessionCheck = _sessionCheck;
})();
