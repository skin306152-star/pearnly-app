// ============================================================
// REFACTOR-WB-C1 · LINE 用户补邮箱强制 modal — 从 home.js 抽出为 ES module
//
// 来源:home.js v118.28.4.1 IIFE(自包含 · 自建 DOM · 无 HTML 依赖)。
// LINE 一键登录临时账号(line_xxx@line.local)首次进 /home 必须填真邮箱;填了:
//   已存在→合并老账号;不存在→更新临时账号。普通账号 needs_email=false 不显示。
// 加载顺序:home.html <script src=home.js>(sync)先跑→暴露全局(t/showToast/
//   subscribeI18n)→ 本 module(Vite bundle · defer)后跑,执行时全局已就绪。
// verbatim 搬迁 · 0 逻辑改。
// ============================================================
(function () {
    'use strict';

    let _modalEl = null;
    let _shown = false;

    function _buildModal() {
        if (_modalEl) return _modalEl;
        const el = document.createElement('div');
        el.id = 'line-email-modal';
        el.style.cssText =
            'position:fixed;inset:0;background:rgba(10,14,39,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;';
        el.innerHTML = `
            <div style="background:#fff;border-radius:16px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06C755" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="4" width="20" height="16" rx="2"/>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                    </svg>
                    <h3 id="line-email-title-h" style="font-size:18px;font-weight:600;color:#0f172a;margin:0;"></h3>
                </div>
                <p id="line-email-sub-p" style="font-size:14px;color:#64748b;line-height:1.55;margin:0 0 18px;"></p>
                <input id="line-email-input" type="email" autocomplete="email" style="width:100%;padding:12px 14px;border:1px solid #e5e7eb;border-radius:10px;font-size:15px;outline:none;font-family:inherit;" />
                <div id="line-email-err" style="color:#dc2626;font-size:13px;margin-top:8px;min-height:18px;"></div>
                <button id="line-email-submit-btn" type="button" style="width:100%;margin-top:14px;padding:13px 16px;background:#111111;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;"></button>
            </div>
        `;
        document.body.appendChild(el);
        _modalEl = el;

        const inp = el.querySelector('#line-email-input');
        const btn = el.querySelector('#line-email-submit-btn');
        const err = el.querySelector('#line-email-err');

        async function _submit() {
            err.textContent = '';
            const v = (inp.value || '').trim().toLowerCase();
            if (!v || v.indexOf('@') < 0 || v.split('@')[1].indexOf('.') < 0) {
                err.textContent = t('line-email-err-invalid');
                return;
            }
            btn.disabled = true;
            btn.style.opacity = '0.6';
            try {
                const resp = await fetch('/api/me/line_complete_email', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                    },
                    body: JSON.stringify({ email: v }),
                });
                if (!resp.ok) throw new Error('http_' + resp.status);
                const data = await resp.json();
                if (data.token) {
                    localStorage.setItem('mrpilot_token', data.token);
                }
                // 弹完 toast 后刷新页面 · 让 _userInfo 重拉
                if (typeof showToast === 'function') {
                    showToast(
                        data.merged ? t('line-email-merged-toast') : t('line-email-saved-toast'),
                        'success'
                    );
                }
                setTimeout(function () {
                    window.location.reload();
                }, 600);
            } catch (e) {
                err.textContent = t('line-email-err-failed');
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        }
        btn.addEventListener('click', _submit);
        inp.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') _submit();
        });
        return el;
    }

    function _renderTexts() {
        if (!_modalEl) return;
        const titleEl = _modalEl.querySelector('#line-email-title-h');
        const subEl = _modalEl.querySelector('#line-email-sub-p');
        const inpEl = _modalEl.querySelector('#line-email-input');
        const btnEl = _modalEl.querySelector('#line-email-submit-btn');
        if (titleEl) titleEl.textContent = t('line-email-title');
        if (subEl) subEl.textContent = t('line-email-sub');
        if (inpEl) inpEl.placeholder = t('line-email-placeholder');
        if (btnEl) btnEl.textContent = t('line-email-submit');
    }

    function _show() {
        _buildModal();
        _renderTexts();
        _modalEl.style.display = 'flex';
        _shown = true;
        const inp = _modalEl.querySelector('#line-email-input');
        if (inp)
            setTimeout(function () {
                inp.focus();
            }, 100);
    }

    async function _check() {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const resp = await fetch('/api/me/needs_email', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!resp.ok) return;
            const data = await resp.json();
            if (data && data.needs_email) _show();
        } catch (e) {}
    }

    // 等 i18n + DOM 就绪
    function _init() {
        // 延迟 800ms 让 _userInfo / I18N 都就绪
        setTimeout(_check, 800);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

    // i18n 订阅 · 切语言时重渲 modal 文案(若正在显示)
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('line-email-modal', function () {
            if (_shown) _renderTexts();
        });
    }
})();
