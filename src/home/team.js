// ============================================================
// REFACTOR-WB-C1 (2026-05-29) · 团队管理(老板侧:员工增删/启停/重置密码)从 home.js 抽出为 ES module
//
// 来源:home.js 团队 owner 函数群 + 事件委托(loadTeamList / showAddEmployeeModal /
//   toggleEmployeeActive / removeEmployee / resetEmployeePassword + [data-*] 事件代理)。
// 加载顺序:home.js(sync · 先跑 · 暴露公共全局)→ 本 module(Vite bundle · defer · 后跑)。
// 入口 window.loadTeamList 由 home.js switchSettingsTab/applyLang + assign-clients.js 经全局调用 ·
//   抽成 defer module 后仍安全(用户进设置→团队 tab 远晚于模块加载)。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):t / showToast / escapeHtml / apiGet /
//   apiPost / showConfirm / token / window.openAssignClientsModal。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。同 PR 删 home.js 死码 showResetPwdResult(0 调用点)。
// ============================================================
/* global apiGet, apiPost, escapeHtml, showConfirm, token */
/* eslint-disable no-useless-escape -- verbatim 搬迁:用户名校验正则 /^[a-zA-Z0-9_.\-]+$/ 原样保留 · 0 改逻辑 */

// v118.10.2 · 团队管理 · 加载员工列表
async function loadTeamList() {
    const loadingEl = document.getElementById('team-loading');
    const listEl = document.getElementById('team-list');
    const emptyEl = document.getElementById('team-empty');
    const countEl = document.getElementById('team-count');
    if (!listEl) return;
    if (loadingEl) loadingEl.style.display = '';
    listEl.style.display = 'none';
    if (emptyEl) emptyEl.style.display = 'none';
    try {
        const r = await apiGet('/api/team/employees');
        const employees = (r && r.employees) || [];
        if (loadingEl) loadingEl.style.display = 'none';
        if (countEl)
            countEl.textContent = (t('team-count') || '共 {n} 名员工').replace(
                '{n}',
                employees.length
            );
        if (employees.length === 0) {
            if (emptyEl) emptyEl.style.display = '';
            return;
        }
        listEl.style.display = '';
        listEl.innerHTML = employees
            .map((e) => {
                const lastLogin = e.last_login_at
                    ? new Date(e.last_login_at).toLocaleDateString()
                    : t('team-never-login') || '从未登录';
                const statusCls = e.is_active === false ? 'team-status-off' : 'team-status-on';
                const statusText =
                    e.is_active === false
                        ? t('team-status-disabled') || '已禁用'
                        : t('team-status-active') || '正常';
                const emailLine = e.email
                    ? `<span class="team-meta-sep">·</span><span>${escapeHtml(e.email)}</span>`
                    : '';
                return `
            <div class="team-card" data-employee-id="${escapeHtml(e.id)}">
                <div class="team-card-main">
                    <div class="team-avatar">${escapeHtml((e.username || '?')[0].toUpperCase())}</div>
                    <div class="team-info">
                        <div class="team-name">${escapeHtml(e.username || '')}</div>
                        <div class="team-meta">
                            <span class="team-status-dot ${statusCls}"></span>
                            <span>${escapeHtml(statusText)}</span>
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml(t('team-last-login') || '上次登录')}: ${escapeHtml(lastLogin)}</span>
                            ${emailLine}
                            <span class="team-meta-sep">·</span>
                            <span>${escapeHtml((t('team-assigned-clients') || '已分配 {n} 客户').replace('{n}', e.assigned_client_count || 0))}</span>
                        </div>
                    </div>
                </div>
                <div class="team-card-actions">
                    <button class="btn btn-ghost btn-small" data-assign-clients="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}">
                        ${escapeHtml(t('team-assign-clients') || '分配客户')}
                    </button>
                    <button class="btn btn-ghost btn-small" data-reset-pwd-employee="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}" title="${escapeHtml(t('team-reset-pwd') || '重置密码')}">
                        ${escapeHtml(t('team-reset-pwd') || '重置密码')}
                    </button>
                    <button class="btn btn-ghost btn-small" data-toggle-employee="${escapeHtml(e.id)}" data-active="${e.is_active === false ? 'false' : 'true'}">
                        ${escapeHtml(e.is_active === false ? t('team-enable') || '启用' : t('team-disable') || '禁用')}
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger-text" data-remove-employee="${escapeHtml(e.id)}" data-name="${escapeHtml(e.username || '')}">
                        ${escapeHtml(t('team-remove') || '移除')}
                    </button>
                </div>
            </div>`;
            })
            .join('');
    } catch (err) {
        console.error('loadTeamList failed:', err);
        if (loadingEl) loadingEl.textContent = t('team-load-failed') || '加载失败';
    }
}

// v118.10.2 · 团队管理 · 添加员工 modal + 提交
// v118.10.3 · 升级为真正的 modal(替代浏览器 prompt 丑陋弹窗)
async function showAddEmployeeModal() {
    // 移除旧 modal(避免重复)
    document.querySelectorAll('.add-emp-overlay').forEach((el) => el.remove());
    const overlay = document.createElement('div');
    overlay.className = 'add-emp-overlay';
    overlay.innerHTML = `
        <div class="add-emp-modal">
            <div class="add-emp-head">
                <div class="add-emp-title">${escapeHtml(t('team-add') || '添加员工')}</div>
                <button class="add-emp-close" type="button" aria-label="close">
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                </button>
            </div>
            <div class="add-emp-body">
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-username') || '员工用户名')}</label>
                    <input type="text" class="add-emp-input" id="add-emp-username" placeholder="${escapeHtml(t('team-modal-username-ph') || 'employee01')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-username-hint') || '3-50 位 · 字母 / 数字 / 下划线 / 点 / 横线 · 唯一')}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-email') || '邮箱(选填)')}</label>
                    <input type="email" class="add-emp-input" id="add-emp-email" placeholder="${escapeHtml(t('team-modal-email-ph') || 'employee@example.com')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-email-hint') || '选填 · 用于忘记密码时邮件重置 · 留空则只能由老板重置')}</div>
                </div>
                <div class="add-emp-field">
                    <label>${escapeHtml(t('team-modal-password') || '初始密码')}</label>
                    <input type="text" class="add-emp-input" id="add-emp-password" placeholder="${escapeHtml(t('team-modal-password-ph') || '至少 8 位 · 字母 + 数字')}" autocomplete="off">
                    <div class="add-emp-hint">${escapeHtml(t('team-modal-password-hint') || '员工首次登录后会被强制修改密码')}</div>
                </div>
                <div class="add-emp-msg" id="add-emp-msg"></div>
            </div>
            <div class="add-emp-foot">
                <button class="btn btn-ghost" type="button" id="add-emp-cancel">${escapeHtml(t('btn-cancel') || '取消')}</button>
                <button class="btn btn-primary" type="button" id="add-emp-submit">${escapeHtml(t('team-add') || '添加员工')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('show'));
    setTimeout(() => {
        const inp = document.getElementById('add-emp-username');
        if (inp) inp.focus();
    }, 200);

    function close() {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 220);
    }
    overlay.querySelector('.add-emp-close').addEventListener('click', close);
    overlay.querySelector('#add-emp-cancel').addEventListener('click', close);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });

    overlay.querySelector('#add-emp-submit').addEventListener('click', async () => {
        const usernameEl = document.getElementById('add-emp-username');
        const emailEl = document.getElementById('add-emp-email');
        const passwordEl = document.getElementById('add-emp-password');
        const msgEl = document.getElementById('add-emp-msg');
        const submitBtn = document.getElementById('add-emp-submit');
        const username = (usernameEl.value || '').trim();
        const email = (emailEl.value || '').trim();
        const password = passwordEl.value || '';
        msgEl.textContent = '';
        msgEl.classList.remove('error');

        if (!username || username.length < 3) {
            msgEl.textContent = t('team-modal-err-username') || '用户名至少 3 位';
            msgEl.classList.add('error');
            return;
        }
        if (!/^[a-zA-Z0-9_.\-]+$/.test(username)) {
            msgEl.textContent =
                t('team-modal-err-username-fmt') || '只能用字母 / 数字 / 下划线 / 点 / 横线';
            msgEl.classList.add('error');
            return;
        }
        // v118.11 · 邮箱选填 · 但填了就要格式正确
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            msgEl.textContent = t('msg-email-invalid') || '邮箱格式不对';
            msgEl.classList.add('error');
            return;
        }
        // v118.11 · 密码强度本地预检(后端再校验一次,这里给即时反馈)
        if (password.length < 8) {
            msgEl.textContent = t('pwd-too-short') || '密码至少 8 位';
            msgEl.classList.add('error');
            return;
        }
        if (/^\d+$/.test(password)) {
            msgEl.textContent = t('pwd-too-weak-numeric') || '不能是纯数字 · 请加入字母';
            msgEl.classList.add('error');
            return;
        }
        if (!(/[a-zA-Z]/.test(password) && /\d/.test(password))) {
            msgEl.textContent = t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字';
            msgEl.classList.add('error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = t('msg-saving') || '保存中...';
        try {
            const payload = { username, password };
            if (email) payload.email = email;
            const resp = await apiPost('/api/team/employees', payload);
            const body = resp ? await resp.json().catch(() => ({})) : {};
            if (resp && resp.ok && body && body.ok) {
                showToast(t('team-added') || '员工已添加', 'success');
                close();
                loadTeamList();
                return;
            }
            const code = (body && body.detail) || 'unknown';
            const msgMap = {
                'team.username_exists': t('team-username-exists') || '用户名已被占用',
                'team.email_exists': t('team-email-exists') || '邮箱已被占用',
                'team.create_failed': t('team-create-failed') || '创建失败',
                'team.only_owner_or_super': t('team-no-permission') || '无权限',
                'team.no_tenant': t('team-no-tenant') || '请先升级账号',
                'pwd.too_short': t('pwd-too-short') || '密码至少 8 位',
                'pwd.too_weak_numeric': t('pwd-too-weak-numeric') || '不能是纯数字',
                'pwd.too_weak_common': t('pwd-too-weak-common') || '这个密码太常见 · 请换一个',
                'pwd.too_weak': t('pwd-too-weak') || '密码至少 8 位 · 字母 + 数字',
            };
            msgEl.textContent =
                msgMap[code] || (t('team-create-failed') || '创建失败') + ' (' + code + ')';
            msgEl.classList.add('error');
        } catch (e) {
            msgEl.textContent = t('team-create-failed') || '创建失败';
            msgEl.classList.add('error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = t('team-add') || '添加员工';
        }
    });

    // ESC 关闭
    function onKey(e) {
        if (e.key === 'Escape') {
            close();
            document.removeEventListener('keydown', onKey);
        }
    }
    document.addEventListener('keydown', onKey);
}

// v118.10.2 · 团队管理 · 启用/禁用 + 移除
async function toggleEmployeeActive(employeeId, makeActive) {
    try {
        const resp = await fetch(`/api/team/employees/${encodeURIComponent(employeeId)}/active`, {
            method: 'PATCH',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !!makeActive }),
        });
        if (resp.ok) {
            loadTeamList();
            return;
        }
        showToast(t('team-toggle-failed') || '操作失败', 'error');
    } catch (e) {
        showToast(t('team-toggle-failed') || '操作失败', 'error');
    }
}
async function removeEmployee(employeeId, username) {
    // v118.11 · 用系统 modal 替代浏览器原生 confirm() · 兼容 {name}/{n} 占位符
    const tpl =
        t('team-confirm-remove') ||
        '确认移除员工「{name}」?他的所有识别记录会保留 · 但他将无法登录';
    const msg = tpl.replace('{name}', username).replace('{n}', username);
    const ok = await showConfirm(msg, { danger: true, okText: t('team-remove') });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/team/employees/${encodeURIComponent(employeeId)}`, {
            method: 'DELETE',
            headers: { Authorization: 'Bearer ' + token },
        });
        if (resp.ok) {
            showToast(t('team-removed') || '已移除', 'success');
            loadTeamList();
            return;
        }
        showToast(t('team-remove-failed') || '移除失败', 'error');
    } catch (e) {
        showToast(t('team-remove-failed') || '移除失败', 'error');
    }
}

// v118.11 · 重置员工密码 · 系统生成 12 位强随机密码 · 一次性弹窗给老板
async function resetEmployeePassword(employeeId, username) {
    const confirmTpl =
        t('team-reset-pwd-confirm') ||
        '给员工「{name}」发送改密链接?系统将通过员工的邮箱或 LINE 发送一个 15 分钟内有效的链接 · 员工自己点链接改密码 · 您看不到密码';
    const msg = confirmTpl.replace('{name}', username).replace('{n}', username);
    const ok = await showConfirm(msg, { okText: t('team-reset-link-send-btn') || '发送链接' });
    if (!ok) return;
    try {
        const resp = await fetch(
            `/api/team/employees/${encodeURIComponent(employeeId)}/reset-password`,
            {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
            }
        );
        const body = await resp.json().catch(() => ({}));
        // 没渠道:员工既无邮箱也无 LINE
        if (resp.status === 400 && body.detail === 'team.reset_no_channel') {
            showToast(
                t('team-reset-no-channel') || '员工尚未绑定邮箱或 LINE · 请先帮员工补充邮箱再重置',
                'error'
            );
            return;
        }
        if (!resp.ok) {
            showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
            return;
        }
        if (body.channel === 'line' || body.channel === 'email') {
            const tpl =
                t('team-reset-link-sent') || '改密链接已通过 {ch} 发送给员工 · 链接 15 分钟内有效';
            const chName = body.channel === 'line' ? 'LINE' : t('team-reset-via-email') || '邮箱';
            showToast(tpl.replace('{ch}', chName), 'success');
            return;
        }
        showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
    } catch (e) {
        showToast(t('team-reset-pwd-fail') || '发送失败', 'error');
    }
}

// v118.10.2 · 团队管理 · 事件代理(点击 add / toggle / remove 按钮)
document.addEventListener('click', (e) => {
    if (e.target.closest('#btn-add-employee')) {
        e.preventDefault();
        showAddEmployeeModal();
        return;
    }
    const tg = e.target.closest('[data-toggle-employee]');
    if (tg) {
        e.preventDefault();
        toggleEmployeeActive(tg.dataset.toggleEmployee, tg.dataset.active === 'false');
        return;
    }
    const rm = e.target.closest('[data-remove-employee]');
    if (rm) {
        e.preventDefault();
        removeEmployee(rm.dataset.removeEmployee, rm.dataset.name || '');
        return;
    }
    // v118.11 · 重置密码按钮
    const rs = e.target.closest('[data-reset-pwd-employee]');
    if (rs) {
        e.preventDefault();
        resetEmployeePassword(rs.dataset.resetPwdEmployee, rs.dataset.name || '');
        return;
    }
    // v118.28.1 · 分配客户按钮
    const ac = e.target.closest('[data-assign-clients]');
    if (ac) {
        e.preventDefault();
        if (typeof window.openAssignClientsModal === 'function')
            window.openAssignClientsModal(ac.dataset.assignClients, ac.dataset.name || '');
        return;
    }
});

// home.js(switchSettingsTab / applyLang)+ assign-clients.js 经全局 bare 调 loadTeamList · 暴露之
window.loadTeamList = loadTeamList;
