/* REFACTOR-C1-home-batch9d · LINE Bot 绑定面板(🔴高敏·铁律#26·Zihao 授权搬)
 * 从 home.js verbatim 抽出(0 逻辑改 · 纯结构搬家):v0.19 · T1 · LINE Bot 面板 IIFE。
 *
 * 桥接说明:
 * - IIFE 自执行(import 时·defer)→ 暴露 window._loadLineBotPanel = load + 绑 document
 *   级 click 委托(刷新码/解绑按钮)。跟已模块化的 folder-watcher/email-ingest 同款 ·
 *   集成抽屉打开时(home.js loaders map · handler)+ automation.js(guarded)读 window._loadLineBotPanel。
 * - 内部状态/函数全 IIFE 局部(_codeTimer/_pollTimer/load/refreshStatus/...)· 局部 token
 *   走 localStorage。外部仅 t(config 全局)+ showConfirm(home.js · window 桥)。
 * - 不 eval 自调 load()(load 只在 panel 打开时经 window._loadLineBotPanel 触发)· 无引导期风险。
 * - LINE 绑定接口 /api/line/binding* 全 verbatim · 未改任何请求逻辑。
 */
/* global showConfirm */

(function () {
    let _codeTimer = null; // 过期倒计时
    let _pollTimer = null; // 绑定状态轮询
    let _currentCode = null;
    let _currentExpiresAt = null;

    function $(id) {
        return document.getElementById(id);
    }

    async function load() {
        clearTimers();
        hideError();
        await refreshStatus();
    }

    async function refreshStatus() {
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) {
                showError(t('linebot-err-status'));
                return;
            }
            const data = await resp.json();
            if (data.bound) {
                renderBound(data);
            } else {
                await renderUnbound();
            }
        } catch (e) {
            showError(t('linebot-err-status'));
        }
    }

    function renderBound(data) {
        stopPolling();
        $('linebot-unbound').style.display = 'none';
        $('linebot-bound').style.display = 'block';

        const pill = $('linebot-status-summary');
        if (pill) {
            pill.textContent = t('linebot-status-bound');
            pill.style.background = '#D1FAE5';
            pill.style.color = '#065F46';
        }

        const nameEl = $('linebot-bound-name');
        if (nameEl) nameEl.textContent = data.line_display_name || '(LINE User)';

        const avatarEl = $('linebot-avatar');
        if (avatarEl) {
            if (data.line_picture_url) {
                avatarEl.src = data.line_picture_url;
                avatarEl.style.display = '';
            } else {
                avatarEl.style.display = 'none';
            }
        }

        const sinceEl = $('linebot-bound-since');
        if (sinceEl && data.bound_at) {
            sinceEl.textContent = new Date(data.bound_at).toLocaleString();
        }
    }

    async function renderUnbound() {
        $('linebot-bound').style.display = 'none';
        $('linebot-unbound').style.display = 'block';

        const pill = $('linebot-status-summary');
        if (pill) {
            pill.textContent = t('linebot-status-unbound');
            pill.style.background = '#FEE2E2';
            pill.style.color = '#B91C1C';
        }

        await fetchNewCode();
        startPolling();
    }

    async function fetchNewCode() {
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding-code', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) {
                showError(t('linebot-err-code'));
                return;
            }
            const data = await resp.json();
            _currentCode = data.code;
            _currentExpiresAt = new Date(data.expires_at).getTime();
            renderCode(data);
        } catch (e) {
            showError(t('linebot-err-code'));
        }
    }

    function renderCode(data) {
        const codeEl = $('linebot-code');
        if (codeEl) codeEl.textContent = data.code;

        // Bot ID
        const idEl = $('linebot-bot-id');
        if (idEl) {
            idEl.textContent = data.bot_basic_id || t('linebot-bot-id-missing');
        }

        // QR 码:如果后端配了 LINE_BOT_FRIEND_URL · 用 Google Chart API 生成 QR
        const qrBox = $('linebot-qr');
        if (qrBox) {
            if (data.bot_friend_url) {
                const qrUrl =
                    'https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data=' +
                    encodeURIComponent(data.bot_friend_url);
                qrBox.classList.remove('empty');
                qrBox.innerHTML = '<img src="' + qrUrl + '" alt="LINE Bot QR">';
            } else {
                qrBox.classList.add('empty');
                qrBox.innerHTML = '';
            }
        }

        // 倒计时
        startCountdown();
    }

    function startCountdown() {
        if (_codeTimer) clearInterval(_codeTimer);
        const expEl = $('linebot-code-expires');

        function tick() {
            if (!_currentExpiresAt) return;
            const ms = _currentExpiresAt - Date.now();
            if (ms <= 0) {
                if (expEl) {
                    expEl.textContent = t('linebot-code-expired');
                    expEl.classList.add('expiring');
                }
                const codeEl = $('linebot-code');
                if (codeEl) codeEl.style.opacity = '0.4';
                clearInterval(_codeTimer);
                _codeTimer = null;
                return;
            }
            const total = Math.floor(ms / 1000);
            const m = Math.floor(total / 60);
            const s = total % 60;
            if (expEl) {
                expEl.textContent = t('linebot-code-expires-in')
                    .replace('{m}', m)
                    .replace('{s}', String(s).padStart(2, '0'));
                if (ms < 60000) expEl.classList.add('expiring');
                else expEl.classList.remove('expiring');
            }
        }
        tick();
        _codeTimer = setInterval(tick, 1000);
    }

    function startPolling() {
        stopPolling();
        // 每 4 秒轮询一次绑定状态
        _pollTimer = setInterval(async () => {
            try {
                const token = localStorage.getItem('mrpilot_token');
                const resp = await fetch('/api/line/binding', {
                    headers: { Authorization: 'Bearer ' + token },
                });
                if (!resp.ok) return;
                const data = await resp.json();
                if (data.bound) {
                    renderBound(data);
                }
            } catch (e) {
                // 静默 · 下一轮再试
            }
        }, 4000);
    }

    function stopPolling() {
        if (_pollTimer) {
            clearInterval(_pollTimer);
            _pollTimer = null;
        }
    }

    function clearTimers() {
        if (_codeTimer) {
            clearInterval(_codeTimer);
            _codeTimer = null;
        }
        stopPolling();
    }

    function showError(msg) {
        const box = $('linebot-error');
        if (box) {
            box.textContent = msg;
            box.style.display = 'block';
        }
    }

    function hideError() {
        const box = $('linebot-error');
        if (box) box.style.display = 'none';
    }

    async function unbind() {
        const ok = await showConfirm(t('linebot-unbind-confirm'), { danger: true });
        if (!ok) return;
        try {
            const token = localStorage.getItem('mrpilot_token');
            const resp = await fetch('/api/line/binding', {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) {
                showError(t('linebot-err-unbind'));
                return;
            }
            await load();
        } catch (e) {
            showError(t('linebot-err-unbind'));
        }
    }

    // 事件绑定
    document.addEventListener('click', (e) => {
        const refreshBtn = e.target.closest('#linebot-code-refresh');
        if (refreshBtn) {
            e.preventDefault();
            hideError();
            fetchNewCode();
            return;
        }
        const unbindBtn = e.target.closest('#linebot-unbind');
        if (unbindBtn) {
            e.preventDefault();
            unbind();
            return;
        }
    });

    // 暴露给 switchAutomationTab
    window._loadLineBotPanel = load;
})();
