/* REFACTOR-C1-home-batch9c · 员工首次登录强制改密 modal(🔴高敏·铁律#26·Zihao 授权搬)
 * 从 home.js verbatim 抽出(0 逻辑改 · 纯结构搬家):showForceChangePasswordModal。
 *
 * 桥接说明:
 * - window.showForceChangePasswordModal 挂出 —— home.js 用户初始化(loadAll post-await ·
 *   员工 + mustChangePw 时)裸调它(已在 home.js 加 typeof window.X 引导期守卫)。
 * - 自包含 · 单一调用方 · 调用点在 async post-await handler 内 → 无引导期裸调风险。
 * - 改密接口 /api/me/change_password 走原生 fetch(verbatim · 未改任何请求/校验逻辑)。
 */
/* global escapeHtml, token */

// v118.11 · 员工首次登录 · 强制改密 modal · 不可关闭 · 改完才能用产品
function showForceChangePasswordModal() {
    document.querySelectorAll('.force-pw-overlay').forEach((el) => el.remove());
    const overlay = document.createElement('div');
    overlay.className = 'force-pw-overlay';
    overlay.innerHTML = `
        <div class="force-pw-modal">
            <div class="force-pw-head">
                <div class="force-pw-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="force-pw-title">${escapeHtml(t('force-pw-title') || '首次登录 · 请修改初始密码')}</div>
                <div class="force-pw-sub">${escapeHtml(t('force-pw-sub') || '老板设置的临时密码不安全 · 请立即修改')}</div>
            </div>
            <div class="force-pw-body">
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-old') || '临时密码(老板告知您的)')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-old" autocomplete="current-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-new') || '新密码(至少 8 位 · 字母 + 数字)')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new" autocomplete="new-password">
                </div>
                <div class="force-pw-field">
                    <label>${escapeHtml(t('force-pw-new2') || '再次输入新密码')}</label>
                    <input type="password" class="force-pw-input" id="force-pw-new2" autocomplete="new-password">
                </div>
                <div class="force-pw-msg" id="force-pw-msg"></div>
            </div>
            <div class="force-pw-foot">
                <button class="btn btn-primary" type="button" id="force-pw-submit">${escapeHtml(t('force-pw-submit') || '修改并继续')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));
    setTimeout(() => {
        const inp = document.getElementById('force-pw-old');
        if (inp) inp.focus();
    }, 200);

    const submitBtn = overlay.querySelector('#force-pw-submit');
    submitBtn.addEventListener('click', async () => {
        const oldPw = document.getElementById('force-pw-old').value;
        const newPw = document.getElementById('force-pw-new').value;
        const newPw2 = document.getElementById('force-pw-new2').value;
        const msgEl = document.getElementById('force-pw-msg');
        msgEl.textContent = '';
        msgEl.classList.remove('error');

        if (!oldPw || !newPw) {
            msgEl.textContent = t('msg-fill-all') || '请填写所有字段';
            msgEl.classList.add('error');
            return;
        }
        if (newPw !== newPw2) {
            msgEl.textContent = t('force-pw-mismatch') || '两次密码不一致';
            msgEl.classList.add('error');
            return;
        }
        if (newPw.length < 8) {
            msgEl.textContent = t('pwd-too-short') || '密码至少 8 位';
            msgEl.classList.add('error');
            return;
        }
        if (/^\d+$/.test(newPw)) {
            msgEl.textContent = t('pwd-too-weak-numeric') || '不能是纯数字 · 请加入字母';
            msgEl.classList.add('error');
            return;
        }
        if (!(/[a-zA-Z]/.test(newPw) && /\d/.test(newPw))) {
            msgEl.textContent = t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字';
            msgEl.classList.add('error');
            return;
        }
        if (newPw === oldPw) {
            msgEl.textContent = t('pwd-same-as-old') || '新密码不能和临时密码相同';
            msgEl.classList.add('error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = t('msg-saving') || '保存中...';
        try {
            const resp = await fetch('/api/me/change_password', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
            });
            const body = await resp.json().catch(() => ({}));
            if (!resp.ok) {
                const code = (body && body.detail) || 'unknown';
                const map = {
                    wrong_old_password: t('force-pw-wrong-old') || '临时密码不对',
                    password_too_short: t('pwd-too-short') || '密码至少 8 位',
                    password_too_weak: t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字',
                };
                msgEl.textContent = map[code] || t('force-pw-fail') || '修改失败';
                msgEl.classList.add('error');
                submitBtn.disabled = false;
                submitBtn.textContent = t('force-pw-submit') || '修改并继续';
                return;
            }
            // 成功 · 清除标记 · 关闭 modal · 重新加载用户信息
            try {
                sessionStorage.removeItem('pearnly_must_change_pw');
            } catch (e) {}
            showToast(t('force-pw-success') || '密码修改成功', 'success');
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
                // 重新走一遍初始化(让 onboarding 等正常跑)
                location.reload();
            }, 600);
        } catch (e) {
            msgEl.textContent = t('force-pw-fail') || '修改失败';
            msgEl.classList.add('error');
            submitBtn.disabled = false;
            submitBtn.textContent = t('force-pw-submit') || '修改并继续';
        }
    });
    // 阻止 ESC 关闭(强制)
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) e.stopPropagation();
    });
}

// ── window 桥(home.js 用户初始化裸调)──
window.showForceChangePasswordModal = showForceChangePasswordModal;
