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
    function strength(pw) {
        let s = 0;
        if (pw.length >= 8) s++;
        if (pw.length >= 12) s++;
        if (/[a-zA-Z]/.test(pw) && /\d/.test(pw)) s++;
        if (/[^a-zA-Z0-9]/.test(pw)) s++;
        return Math.min(3, s);
    }

    // 显示消息(成功 / 失败)
    function showMsg(text, type) {
        const el = document.getElementById('cpw-msg');
        if (!el) return;
        el.textContent = text;
        el.className = 'cpw-msg ' + (type || '');
    }

    // 翻译 · 走全局 t()
    function tt(key) {
        return typeof t === 'function' ? t(key) : key;
    }

    function bindEvents() {
        // v109.4 · 防 Chrome/Edge autofill 关键技巧:页面加载时字段是 readonly · 用户点击/聚焦时才移除 readonly
        // 这样浏览器不会触发 autofill(autofill 只对非 readonly 字段生效)
        const cpwInputs = ['cpw-old', 'cpw-new', 'cpw-confirm'];
        cpwInputs.forEach((id) => {
            const inp = document.getElementById(id);
            if (!inp) return;
            // 页面加载强制清空 + 设 readonly 避免 autofill
            inp.value = '';
            inp.setAttribute('readonly', 'readonly');
            // focus 时移除 readonly · 让用户能输入
            inp.addEventListener('focus', function () {
                this.removeAttribute('readonly');
            });
            // blur 时清空(防键盘 manager 残留)— 不做这个 · 用户可能想编辑后再回来确认 newpw
        });

        // 设置页打开时再次清空(用户可能已经填了之后切走又回来)
        // 通过监听 settings tab 切换实现
        document
            .querySelectorAll('.settings-nav-item[data-settings-tab="account"]')
            .forEach((tab) => {
                tab.addEventListener('click', () => {
                    setTimeout(() => {
                        cpwInputs.forEach((id) => {
                            const inp = document.getElementById(id);
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
                    }, 100);
                });
            });

        // 眼睛图标 · 切换密码可见
        document.querySelectorAll('.cpw-eye').forEach((btn) => {
            btn.addEventListener('click', () => {
                const target = btn.dataset.target;
                const inp = document.getElementById(target);
                if (!inp) return;
                inp.type = inp.type === 'password' ? 'text' : 'password';
            });
        });

        // 新密码强度条
        const newInp = document.getElementById('cpw-new');
        const bar = document.getElementById('cpw-strength-bar');
        if (newInp && bar) {
            newInp.addEventListener('input', () => {
                const s = strength(newInp.value);
                const widths = ['0%', '33%', '66%', '100%'];
                const cls = ['', 'weak', 'medium', 'strong'];
                bar.style.width = widths[s];
                bar.className = 'cpw-strength-bar ' + cls[s];
            });
        }

        // v109.4 · 「忘记当前密码?」链接 → 弹窗确认发送重置邮件
        const forgotLink = document.getElementById('cpw-forgot-link');
        if (forgotLink) {
            forgotLink.addEventListener('click', () => openForgotCurrentPwModal());
        }

        // 提交
        const btn = document.getElementById('btn-change-pw');
        if (!btn) return;
        btn.addEventListener('click', async () => {
            const oldEl = document.getElementById('cpw-old');
            const newEl = document.getElementById('cpw-new');
            const cfmEl = document.getElementById('cpw-confirm');
            if (!oldEl || !newEl || !cfmEl) return;

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
                    else if (detail === 'password_too_short')
                        msg = tt('settings-change-pw-too-short');
                    else if (detail === 'password_too_weak')
                        msg = tt('settings-change-pw-too-weak');
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
        });
    }

    // v109.4 · 「忘记当前密码?」弹窗
    function openForgotCurrentPwModal() {
        const u = window._userInfo || (typeof _userInfo !== 'undefined' ? _userInfo : null);
        const email = u && u.username ? u.username : '';
        const maskedEmail = maskEmail(email);

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
        overlay.querySelector('#cpw-forgot-close').addEventListener('click', close);
        overlay.querySelector('#cpw-forgot-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });

        // 发送
        overlay.querySelector('#cpw-forgot-send').addEventListener('click', async () => {
            const sendBtn = overlay.querySelector('#cpw-forgot-send');
            const msgEl = overlay.querySelector('#cpw-forgot-msg');
            sendBtn.disabled = true;
            const oldText = sendBtn.textContent;
            sendBtn.textContent = tt('cpw-forgot-sending');
            try {
                const r = await fetch('/api/auth/forgot_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email }),
                });
                const data = await r.json().catch(() => ({}));
                if (r.ok) {
                    msgEl.textContent = tt('cpw-forgot-success');
                    msgEl.className = 'cpw-forgot-msg success';
                    sendBtn.style.display = 'none';
                    overlay.querySelector('#cpw-forgot-cancel').textContent =
                        tt('cpw-forgot-close-btn');
                } else {
                    msgEl.textContent = data.detail || tt('cpw-forgot-fail');
                    msgEl.className = 'cpw-forgot-msg error';
                    sendBtn.disabled = false;
                    sendBtn.textContent = oldText;
                }
            } catch (e) {
                msgEl.textContent = tt('cpw-forgot-fail');
                msgEl.className = 'cpw-forgot-msg error';
                sendBtn.disabled = false;
                sendBtn.textContent = oldText;
            }
        });
    }

    // 邮箱半遮罩 · ab****@gmail.com
    function maskEmail(email) {
        if (!email || !email.includes('@')) return email || '';
        const [local, domain] = email.split('@');
        if (local.length <= 2) return local + '****@' + domain;
        return local.slice(0, 2) + '****@' + domain;
    }

    // 安全转义
    function esc(s) {
        if (s == null) return '';
        return String(s).replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
        );
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        bindEvents();
    } else {
        document.addEventListener('DOMContentLoaded', bindEvents);
    }
})();
