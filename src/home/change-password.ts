// ============================================================
// REFACTOR-WB-C1 · 修改密码模块(v109.4)— 从 home.js 抽出为 ES module
//
// 自包含 IIFE:绑定设置→账户 tab 的改密表单(cpw-*)+「忘记当前密码」弹窗。
//   消费全局 t/showToast/window._userInfo;不暴露任何符号,自启动(DOMContentLoaded)。
// 加载顺序:home.js(sync)先跑暴露全局 → 本 module(Vite · defer)后跑,DOM/全局已就绪。
// verbatim 搬迁 · 0 逻辑改。
// ============================================================
(function () {
    'use strict';

    // 密码强度评估(0-3)
    function strength(pw: string) {
        let s = 0;
        if (pw.length >= 8) s++;
        if (pw.length >= 12) s++;
        if (/[a-zA-Z]/.test(pw) && /\d/.test(pw)) s++;
        if (/[^a-zA-Z0-9]/.test(pw)) s++;
        return Math.min(3, s);
    }

    // 显示消息(成功 / 失败)
    function showMsg(text: string, type: string) {
        const el = document.getElementById('cpw-msg');
        if (!el) return;
        el.textContent = text;
        el.className = 'cpw-msg ' + (type || '');
    }

    // 翻译 · 走全局 t()
    function tt(key: string) {
        return typeof t === 'function' ? t(key) : key;
    }

    // Bug A 修复(2026-05-30)· 改密表单元素由 page-settings.js 运行期注入 + recon-subtab DOM-move →
    // DOMContentLoaded 直绑必 race(忘记密码/提交/眼睛全曾失效)· 改 document 事件委托(对注入/move 免疫)。
    // 钩子 id/class 全保留 · 0 逻辑改(仅绑定机制)。
    let _cpwDelegated = false;

    function armCpwInputs() {
        ['cpw-old', 'cpw-new', 'cpw-confirm'].forEach((id) => {
            const inp = document.getElementById(id) as HTMLInputElement | null;
            if (inp) {
                inp.value = '';
                inp.setAttribute('readonly', 'readonly');
            }
        });
        const bar = document.getElementById('cpw-strength-bar');
        if (bar) {
            bar.style.width = '0%';
            bar.className = 'cpw-strength-bar';
        }
        showMsg('', '');
    }

    async function submitChangePw() {
        const btn = document.getElementById('btn-change-pw') as HTMLButtonElement | null;
        const oldEl = document.getElementById('cpw-old') as HTMLInputElement | null;
        const newEl = document.getElementById('cpw-new') as HTMLInputElement | null;
        const cfmEl = document.getElementById('cpw-confirm') as HTMLInputElement | null;
        const bar = document.getElementById('cpw-strength-bar') as HTMLElement | null;
        if (!btn || !oldEl || !newEl || !cfmEl) return;

        const oldPw = oldEl.value;
        const newPw = newEl.value;
        const cfm = cfmEl.value;

        // 前端校验
        if (!oldPw || !newPw || !cfm) {
            showMsg(tt('settings-change-pw-empty'), 'error');
            return;
        }
        if (newPw.length < 8) {
            showMsg(tt('settings-change-pw-too-short'), 'error');
            return;
        }
        if (!(/[a-zA-Z]/.test(newPw) && /\d/.test(newPw))) {
            showMsg(tt('settings-change-pw-too-weak'), 'error');
            return;
        }
        if (newPw !== cfm) {
            showMsg(tt('settings-change-pw-mismatch'), 'error');
            return;
        }

        // 提交
        btn.disabled = true;
        const oldText = btn.textContent;
        btn.textContent = tt('settings-change-pw-submitting');
        showMsg('', '');

        try {
            const tok = localStorage.getItem('mrpilot_token');
            const r = await fetch('/api/me/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: 'Bearer ' + tok,
                },
                body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
            });
            const data = await r.json().catch(() => ({}));
            if (r.ok && data.ok) {
                showMsg(tt('settings-change-pw-success'), 'success');
                if (typeof showToast === 'function')
                    showToast(tt('settings-change-pw-success'), 'success');
                oldEl.value = '';
                newEl.value = '';
                cfmEl.value = '';
                if (bar) {
                    bar.style.width = '0%';
                    bar.className = 'cpw-strength-bar';
                }
            } else {
                const detail = data.detail || '';
                let msg = tt('settings-change-pw-success'); // 占位
                if (detail === 'wrong_old_password') msg = tt('settings-change-pw-wrong-old');
                else if (detail === 'password_too_short') msg = tt('settings-change-pw-too-short');
                else if (detail === 'password_too_weak') msg = tt('settings-change-pw-too-weak');
                else msg = detail || 'Error';
                showMsg(msg, 'error');
            }
        } catch (e) {
            console.error('change_password', e);
            showMsg('Network error', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = oldText;
        }
    }

    function bindEvents() {
        if (_cpwDelegated) return;
        _cpwDelegated = true;

        // 点击委托:眼睛切换 / 忘记密码 / 提交 / 切账户安全 tab 清空
        document.addEventListener('click', (e) => {
            if (!e.target || !(e.target as HTMLElement).closest) return;
            const eye = (e.target as HTMLElement).closest('.cpw-eye') as HTMLElement | null;
            if (eye) {
                const inp = document.getElementById(eye.dataset.target!) as HTMLInputElement | null;
                if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
                return;
            }
            if ((e.target as HTMLElement).closest('#cpw-forgot-link')) {
                e.preventDefault();
                openForgotCurrentPwModal();
                return;
            }
            if ((e.target as HTMLElement).closest('#btn-change-pw')) {
                submitChangePw();
                return;
            }
            if (
                (e.target as HTMLElement).closest(
                    '.settings-nav-item[data-settings-tab="account"], .settings-nav-item[data-tab="account"], .settings-nav-item[data-tab="security"]'
                )
            ) {
                setTimeout(armCpwInputs, 100);
            }
        });

        // 输入委托:新密码强度条
        document.addEventListener('input', (e) => {
            if (e.target && (e.target as HTMLElement).id === 'cpw-new') {
                const bar = document.getElementById('cpw-strength-bar');
                if (!bar) return;
                const s = strength((e.target as HTMLInputElement).value);
                const widths = ['0%', '33%', '66%', '100%'];
                const cls = ['', 'weak', 'medium', 'strong'];
                bar.style.width = widths[s];
                bar.className = 'cpw-strength-bar ' + cls[s];
            }
        });

        // 焦点委托:防 autofill · 聚焦改密字段时移除 readonly
        document.addEventListener('focusin', (e) => {
            if (
                e.target &&
                ['cpw-old', 'cpw-new', 'cpw-confirm'].includes((e.target as HTMLElement).id)
            ) {
                (e.target as HTMLElement).removeAttribute('readonly');
            }
        });

        // 若改密表单此刻已在场 · 立即武装一次(清空 + readonly 防 autofill)
        if (document.getElementById('cpw-old')) armCpwInputs();
    }

    // v109.4 · 「忘记当前密码?」弹窗
    function openForgotCurrentPwModal() {
        const u = window._userInfo || (typeof _userInfo !== 'undefined' ? _userInfo : null);
        const email = u && u.username ? u.username : '';
        const maskedEmail = maskEmail(email as string);

        // 创建 overlay
        let overlay = document.getElementById('cpw-forgot-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.id = 'cpw-forgot-overlay';
        overlay.className = 'cpw-forgot-overlay';
        overlay.innerHTML = `
            <div class="cpw-forgot-modal">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('cpw-forgot-title'))}</div>
                    <button class="cpw-forgot-close" id="cpw-forgot-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(tt('cpw-forgot-desc'))}</p>
                    <div class="cpw-forgot-email">${esc(maskedEmail)}</div>
                    <p class="cpw-forgot-tip">${esc(tt('cpw-forgot-tip'))}</p>
                    <div class="cpw-forgot-msg" id="cpw-forgot-msg"></div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="cpw-forgot-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-primary" id="cpw-forgot-send">${esc(tt('cpw-forgot-send'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 关闭
        const close = () => overlay.remove();
        overlay.querySelector('#cpw-forgot-close')!.addEventListener('click', close);
        overlay.querySelector('#cpw-forgot-cancel')!.addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });

        // 发送
        overlay.querySelector('#cpw-forgot-send')!.addEventListener('click', async () => {
            const sendBtn = overlay.querySelector('#cpw-forgot-send') as HTMLButtonElement | null;
            const msgEl = overlay.querySelector('#cpw-forgot-msg') as HTMLElement | null;
            sendBtn!.disabled = true;
            const oldText = sendBtn!.textContent;
            sendBtn!.textContent = tt('cpw-forgot-sending');
            try {
                const r = await fetch('/api/auth/forgot_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email }),
                });
                const data = await r.json().catch(() => ({}));
                if (r.ok) {
                    msgEl!.textContent = tt('cpw-forgot-success');
                    msgEl!.className = 'cpw-forgot-msg success';
                    sendBtn!.style.display = 'none';
                    overlay.querySelector('#cpw-forgot-cancel')!.textContent =
                        tt('cpw-forgot-close-btn');
                } else {
                    msgEl!.textContent = data.detail || tt('cpw-forgot-fail');
                    msgEl!.className = 'cpw-forgot-msg error';
                    sendBtn!.disabled = false;
                    sendBtn!.textContent = oldText;
                }
            } catch (e) {
                msgEl!.textContent = tt('cpw-forgot-fail');
                msgEl!.className = 'cpw-forgot-msg error';
                sendBtn!.disabled = false;
                sendBtn!.textContent = oldText;
            }
        });
    }

    // 邮箱半遮罩 · ab****@gmail.com
    function maskEmail(email: string) {
        if (!email || !email.includes('@')) return email || '';
        const [local, domain] = email.split('@');
        if (local.length <= 2) return local + '****@' + domain;
        return local.slice(0, 2) + '****@' + domain;
    }

    // 安全转义
    function esc(s: unknown) {
        if (s == null) return '';
        return String(s).replace(
            /[&<>"']/g,
            (c: string) =>
                ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[
                    c
                ] as string
        );
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        bindEvents();
    } else {
        document.addEventListener('DOMContentLoaded', bindEvents);
    }
})();
