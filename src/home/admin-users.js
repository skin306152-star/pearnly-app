/* admin-users.js · REFACTOR-C1 · 抽自 home.js v109.3 IIFE 后半
 * (loadAdminUsersPage + window.__adm_* 全套 + 风控 + 员工 tab)。
 * 0 业务逻辑改动。仅三处适配:
 *   ① 自带 tt/esc + const I18N=window.I18N(原在同 IIFE 前半 · 前半留 home.js)
 *   ② tt 改读 window._currentLang(ES 模块拿不到 home.js 闭包 currentLang)
 *   ③ init 去掉 loadPlan/setInterval(套餐轮询留 home.js 前半)
 * 调用点(routeTo/启动/抽屉)早已 window.* 桥接 · /admin SPA 独立不受影响。 */
/* global showConfirm */
(function () {
    'use strict';
    const I18N = window.I18N;
    function tt(key, params) {
        const lang = window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
        let s = (I18N[lang] && I18N[lang][key]) || key;
        if (params)
            Object.keys(params).forEach((p) => {
                s = s.replace(new RegExp('\\{' + p + '\\}', 'g'), params[p]);
            });
        return s;
    }
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(
            /[&<>"']/g,
            (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]
        );
    }

    // ============================================================
    // 后台 · 用户管理页(仅 super_admin · 由路由切换触发渲染)
    // ============================================================
    // v118.3 · 全页数据缓存 · 切语言时立即重渲(不等 fetch)
    const _admPageState = {
        funnel: null,
        pay: null,
        users: [],
        risk: null,
    };

    function loadAdminUsersPage() {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        const _h = { headers: { Authorization: 'Bearer ' + tok } };
        const _errHtml = (id) => `<div class="adm-empty" style="color:#ef4444">
            加载失败 · <a href="#" style="color:#ef4444;text-decoration:underline" onclick="loadAdminUsersPage();return false">重试</a>
        </div>`;

        // v4.10.16 · 4 路同时发出 · 各自独立渲染 · 互不阻塞(原串行 ~8s → 并行 ~2-3s)
        const funnelP = fetch('/api/admin/users/funnel', _h);
        const payP = fetch('/api/admin/payments/pending', _h);
        const usersP = fetch('/api/admin/users?plan=all&search=&limit=100', _h);
        const riskP = fetch('/api/admin/risk/suspicious', _h);

        funnelP
            .then(async (r) => {
                if (r.status === 403) return null;
                return r.json();
            })
            .then((d) => {
                if (!d) return;
                _admPageState.funnel = d;
                renderAdmKpi(d);
                renderAdmExpiring(d.trial_expiring_soon || []);
            })
            .catch(() => {
                const w = document.getElementById('adm-kpi-grid');
                if (w) w.innerHTML = _errHtml();
            });

        payP.then((r) => r.json())
            .then((d) => {
                _admPageState.pay = d;
                renderAdmPending(d.payments || []);
            })
            .catch(() => {
                const w = document.getElementById('adm-pending-list');
                if (w) w.innerHTML = _errHtml();
            });

        usersP
            .then((r) => r.json())
            .then((d) => {
                _admPageState.users = d.users || [];
                renderAdmUserList(d.users || []);
            })
            .catch(() => {
                const w = document.getElementById('adm-users-table');
                if (w) w.innerHTML = _errHtml();
            });

        riskP
            .then((r) => r.json())
            .then((d) => {
                _admPageState.risk = d;
                renderAdmRisk(d);
            })
            .catch(() => {
                const w = document.getElementById('adm-risk-content');
                if (w) w.innerHTML = _errHtml();
            });
    }

    // v118.3 · 立即用缓存数据 + 当前 i18n 重渲整页(切语言用 · 不等 fetch · 视觉零延迟)
    window.__rerenderAdmPage = function () {
        if (_admPageState.funnel) {
            renderAdmKpi(_admPageState.funnel);
            renderAdmExpiring(_admPageState.funnel.trial_expiring_soon || []);
        }
        if (_admPageState.pay) renderAdmPending(_admPageState.pay.payments || []);
        if (_admPageState.users && _admPageState.users.length)
            renderAdmUserList(_admPageState.users);
        if (_admPageState.risk) renderAdmRisk(_admPageState.risk);
        // v118.29.0 · 日志切语言重渲
        if (_admLogsState && _admLogsState.rows && _admLogsState.rows.length) {
            renderAdmLogs();
            renderAdmLogsPager();
        }
    };

    function renderAdmKpi(f) {
        const wrap = document.getElementById('adm-kpi-grid');
        if (!wrap) return;
        const bp = f.by_plan || {};
        const cards = [
            { lbl: tt('adm-kpi-today'), val: f.new_today || 0, color: '#111111' },
            { lbl: tt('adm-kpi-week'), val: f.new_week || 0, color: '#111111' },
            { lbl: tt('adm-kpi-month'), val: f.new_month || 0, color: '#111111' },
            { lbl: tt('plan-trial'), val: bp.trial || 0, color: '#f59e0b' },
            { lbl: tt('plan-free'), val: bp.free || 0, color: '#64748b' },
            { lbl: tt('plan-pro'), val: bp.pro || 0, color: '#10b981' },
            { lbl: tt('plan-firm'), val: bp.firm || 0, color: '#8b5cf6' },
            { lbl: tt('adm-kpi-conv'), val: (f.conversion_pct || 0) + '%', color: '#dc2626' },
        ];
        wrap.innerHTML = cards
            .map(
                (c) => `
            <div class="adm-kpi-card" style="border-top: 3px solid ${c.color}">
                <div class="adm-kpi-val" style="color: ${c.color}">${esc(c.val)}</div>
                <div class="adm-kpi-lbl">${esc(c.lbl)}</div>
            </div>
        `
            )
            .join('');
    }

    function renderAdmPending(rows) {
        const wrap = document.getElementById('adm-pending-list');
        if (!wrap) return;
        if (!rows.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-pending-empty'))}</div>`;
            return;
        }
        wrap.innerHTML =
            rows
                .filter((r) => r.status === 'pending')
                .map(
                    (r) => `
            <div class="adm-pending-item">
                <div class="adm-pending-info">
                    <div class="adm-pending-line1">
                        <strong>${esc(r.user_email || '?')}</strong> · ${esc(r.company_name || '')}
                        <span class="adm-tag">${esc(r.target_plan.toUpperCase())}</span>
                    </div>
                    <div class="adm-pending-line2">฿${esc(r.amount_thb)} · ${esc(r.payer_name || '—')} · ${esc(r.payer_note || '')}</div>
                    <div class="adm-pending-line3">${esc(new Date(r.created_at).toLocaleString())} · LINE: ${esc(r.line_id || '—')}</div>
                </div>
                <div class="adm-pending-actions">
                    ${r.screenshot_path ? `<button class="btn btn-ghost btn-sm" onclick="window.__adm_view_slip(${r.id})">${esc(tt('adm-view-slip'))}</button>` : ''}
                    <button class="btn btn-primary btn-sm" onclick="window.__adm_approve(${r.id})">${esc(tt('adm-approve'))}</button>
                    <button class="btn btn-danger btn-sm" onclick="window.__adm_reject(${r.id})">${esc(tt('adm-reject'))}</button>
                </div>
            </div>
        `
                )
                .join('') || `<div class="adm-empty">${esc(tt('adm-pending-empty'))}</div>`;
    }

    // v111.3 · 看付款截图 · 带 token 鉴权 · 用 blob URL 打开
    window.__adm_view_slip = async function (payment_id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${payment_id}/screenshot`, {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (!r.ok) {
                showToast(tt('adm-slip-not-found'), 'error');
                return;
            }
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            // 弹个简单 lightbox
            const overlay = document.createElement('div');
            overlay.className = 'slip-overlay';
            overlay.innerHTML = `
                <div class="slip-modal">
                    <button class="slip-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                    <img src="${url}" alt="payment slip">
                </div>`;
            const close = () => {
                URL.revokeObjectURL(url);
                overlay.remove();
            };
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close();
            });
            overlay.querySelector('.slip-close').addEventListener('click', close);
            document.body.appendChild(overlay);
        } catch (e) {
            console.error(e);
            showToast(tt('adm-slip-not-found'), 'error');
        }
    };

    window.__adm_approve = async function (id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${id}/review?action=approve`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-approved'), 'success');
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };
    window.__adm_reject = async function (id) {
        const ok = await showConfirm(tt('adm-confirm-reject'), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/payments/${id}/review?action=reject`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-rejected'), 'success');
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };

    function renderAdmExpiring(rows) {
        const wrap = document.getElementById('adm-expiring-list');
        if (!wrap) return;
        if (!rows.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-expiring-empty'))}</div>`;
            return;
        }
        wrap.innerHTML = rows
            .map(
                (r) => `
            <div class="adm-expiring-item">
                <div>
                    <strong>${esc(r.email)}</strong> · ${esc(r.company_name || '')}
                    <span class="adm-tag adm-tag-warn">${r.hours_left}h</span>
                </div>
                <div class="adm-expiring-actions">
                    ${r.line_id ? `<span class="adm-line-id">LINE: ${esc(r.line_id)}</span>` : ''}
                    <button class="btn btn-primary btn-sm" onclick="window.__adm_quick_upgrade('${esc(r.id)}', '${esc(r.email)}')">${esc(tt('adm-quick-upgrade'))}</button>
                </div>
            </div>
        `
            )
            .join('');
    }

    window.__adm_quick_upgrade = async function (uid, email) {
        // v109.4 · 用 modal 代替原生 prompt · 跟产品 UI 一致
        // 套餐对齐新方案:trial/solo/team/firm/enterprise
        let overlay = document.getElementById('adm-upgrade-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-upgrade-overlay';
        const plans = [
            { id: 'trial', label: tt('upg-plan-trial'), desc: tt('upg-plan-trial-desc') },
            { id: 'monthly', label: tt('upg-plan-monthly'), desc: tt('upg-plan-monthly-desc') },
            { id: 'yearly', label: tt('upg-plan-yearly'), desc: tt('upg-plan-yearly-desc') },
            { id: 'lifetime', label: tt('upg-plan-lifetime'), desc: tt('upg-plan-lifetime-desc') },
        ];
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:480px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('adm-upgrade-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-upg-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(email)}</p>
                    <div class="adm-plan-options">
                        ${plans
                            .map(
                                (p) => `
                            <label class="adm-plan-option">
                                <input type="radio" name="adm-target-plan" value="${p.id}">
                                <div class="adm-plan-option-body">
                                    <div class="adm-plan-option-label">${esc(p.label)}</div>
                                    <div class="adm-plan-option-desc">${esc(p.desc)}</div>
                                </div>
                            </label>
                        `
                            )
                            .join('')}
                    </div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="adm-upg-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-primary" id="adm-upg-confirm">${esc(tt('adm-upg-confirm'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        overlay.querySelector('#adm-upg-close').addEventListener('click', close);
        overlay.querySelector('#adm-upg-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        overlay.querySelector('#adm-upg-confirm').addEventListener('click', async () => {
            const sel = overlay.querySelector('input[name="adm-target-plan"]:checked');
            if (!sel) {
                showToast(tt('adm-pick-plan'), 'warn');
                return;
            }
            const targetPlan = sel.value;
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch('/api/admin/users/upgrade', {
                    method: 'POST',
                    headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: uid,
                        target_plan: targetPlan,
                        note: 'manual_admin',
                    }),
                });
                if (r.ok) {
                    showToast(tt('adm-upgrade-ok'), 'success');
                    close();
                    loadAdminUsersPage();
                } else {
                    const data = await r.json().catch(() => ({}));
                    showToast(data.detail || tt('adm-upgrade-fail'), 'error');
                }
            } catch (e) {
                showToast(tt('adm-upgrade-fail'), 'error');
            }
        });
    };

    async function loadAdmUserList() {
        const tok = localStorage.getItem('mrpilot_token');
        const planF = document.getElementById('adm-plan-filter').value;
        const search = document.getElementById('adm-user-search').value;
        try {
            const qs = `?plan=${encodeURIComponent(planF)}&search=${encodeURIComponent(search)}&limit=100`;
            const r = await fetch('/api/admin/users' + qs, {
                headers: { Authorization: 'Bearer ' + tok },
            });
            const data = await r.json();
            _admPageState.users = data.users || []; // v118.3 · 缓存
            renderAdmUserList(data.users || []);
        } catch (e) {
            console.error(e);
        }
    }

    function renderAdmUserList(users) {
        const wrap = document.getElementById('adm-users-table');
        if (!wrap) return;
        if (!users.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-users-empty'))}</div>`;
            return;
        }
        // v109.4 · 当前登录的 super_admin 自己 · 不能对自己操作
        const meId = window._userInfo && window._userInfo.id ? String(window._userInfo.id) : null;
        const planLabelMap = {
            trial: 'Trial',
            free: 'Trial',
            solo: 'Pearnly Solo',
            team: 'Pearnly Team',
            firm: 'Pearnly Firm',
            enterprise: 'Enterprise',
            pro: 'Pearnly Solo', // v109.4 · 老 pro 视为 solo · 兼容老数据
            plus: 'Pearnly Solo', // v109.4 · 老 plus 也视为 solo
            monthly: 'Monthly',
            lifetime: 'Lifetime',
        };
        wrap.innerHTML = `
            <div class="adm-table-head">
                <div>${esc(tt('adm-col-email'))}</div>
                <div>${esc(tt('adm-col-company'))}</div>
                <div>${esc(tt('adm-col-plan'))}</div>
                <div>${esc(tt('adm-col-usage'))}</div>
                <div>${esc(tt('adm-col-country'))}</div>
                <div>${esc(tt('adm-col-actions'))}</div>
            </div>
            ${users
                .map((u) => {
                    const isSelf = meId && String(u.id) === meId;
                    const isAdmin = u.is_super_admin || u.tenant_type === 'admin';
                    const planLabel =
                        planLabelMap[u.plan] ||
                        (u.plan ? u.plan.charAt(0).toUpperCase() + u.plan.slice(1) : '—');
                    const adminBadge = isAdmin
                        ? `<span class="adm-admin-tag">${esc(tt('admin-type-super'))}</span>`
                        : '';
                    const lineBadge = u.line_id ? '· LINE' : '';
                    // 自己那行 / 其他超管 · 操作按钮 disabled + 加 tooltip
                    const actions =
                        isSelf || isAdmin
                            ? `<div class="adm-row-actions" title="${esc(tt('admin-self-disabled-tip'))}">
                            <button class="btn btn-ghost btn-sm" disabled>${esc(tt('adm-upgrade'))}</button>
                            <button class="btn btn-ghost btn-sm" disabled>${esc(tt('adm-ban'))}</button>
                       </div>`
                            : `<div class="adm-row-actions">
                            <button class="btn btn-ghost btn-sm" onclick="window.__adm_quick_upgrade('${esc(u.id)}', '${esc(u.email)}')">${esc(tt('adm-upgrade'))}</button>
                            <button class="btn btn-ghost btn-sm" onclick="window.__adm_ban_user('${esc(u.id)}', '${esc(u.email)}')">${esc(tt('adm-ban'))}</button>
                            <button class="btn btn-ghost btn-sm adm-emp-btn-danger" onclick="window.__adm_cascade_delete('${esc(u.id)}', '${esc(u.username || u.email || '')}')" title="${esc(tt('adm-cascade-del-tip'))}">${esc(tt('adm-cascade-del'))}</button>
                       </div>`;
                    return `
                    <div class="adm-table-row${isSelf ? ' adm-self-row' : ''}">
                        <div>
                            <div class="adm-cell-strong adm-cell-clickable" onclick="window.__adm_open_user_drawer('${esc(u.id)}')">${esc(u.email || u.username)}</div>
                            <div class="adm-cell-mute">${esc(new Date(u.created_at).toLocaleDateString())} ${adminBadge}</div>
                        </div>
                        <div>${esc(u.company_name || '—')}</div>
                        <div>
                            <span class="adm-plan-badge adm-plan-${esc(u.plan)}">${esc(planLabel)}</span>
                            ${u.days_left !== null && u.days_left !== undefined ? `<div class="adm-cell-mute">${u.days_left}d</div>` : ''}
                        </div>
                        <div>${u.ocr_used_month || 0}</div>
                        <div>${esc(u.country || '—')} ${lineBadge}</div>
                        ${actions}
                    </div>
                `;
                })
                .join('')}
        `;
    }

    window.__adm_ban_user = async function (uid, email) {
        // v109.4 · 用 modal 代替原生 prompt
        let overlay = document.getElementById('adm-ban-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-ban-overlay';
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:420px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title">${esc(tt('adm-ban-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-ban-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-desc">${esc(email)}</p>
                    <p class="cpw-forgot-tip">${esc(tt('adm-ban-warn'))}</p>
                    <div style="margin-top:12px;">
                        <label style="display:block;font-size:13px;color:#475569;margin-bottom:6px;">${esc(tt('adm-ban-reason'))}</label>
                        <input type="text" id="adm-ban-reason-input" class="cpw-input" autocomplete="off" placeholder="${esc(tt('adm-ban-reason-ph'))}" value="abuse">
                    </div>
                </div>
                <div class="cpw-forgot-foot">
                    <button class="btn btn-ghost" id="adm-ban-cancel">${esc(tt('cpw-forgot-cancel'))}</button>
                    <button class="btn btn-danger" id="adm-ban-confirm">${esc(tt('adm-ban-confirm'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        overlay.querySelector('#adm-ban-close').addEventListener('click', close);
        overlay.querySelector('#adm-ban-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });
        overlay.querySelector('#adm-ban-confirm').addEventListener('click', async () => {
            const reason =
                (overlay.querySelector('#adm-ban-reason-input').value || '').trim() || 'abuse';
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch(
                    `/api/admin/users/${uid}/ban?reason=${encodeURIComponent(reason)}`,
                    {
                        method: 'POST',
                        headers: { Authorization: 'Bearer ' + tok },
                    }
                );
                if (r.ok) {
                    showToast(tt('adm-ban-ok'), 'success');
                    close();
                    loadAdmUserList();
                } else {
                    const data = await r.json().catch(() => ({}));
                    showToast(data.detail || tt('adm-ban-fail'), 'error');
                }
            } catch (e) {
                showToast(tt('adm-ban-fail'), 'error');
            }
        });
    };

    // v118.16 · 级联删除老板账号(高风险 · 双重确认)
    window.__adm_cascade_delete = async function (uid, username) {
        const tok = localStorage.getItem('mrpilot_token');
        // 1) 先取影响范围
        let preview;
        try {
            const r = await fetch(`/api/admin/users/${encodeURIComponent(uid)}/cascade-preview`, {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (!r.ok) {
                const data = await r.json().catch(() => ({}));
                showToast(data.detail || tt('adm-cd-preview-fail'), 'error');
                return;
            }
            preview = await r.json();
        } catch (e) {
            showToast(tt('adm-cd-preview-fail'), 'error');
            return;
        }

        // 2) 渲染 modal
        let overlay = document.getElementById('adm-cd-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'cpw-forgot-overlay';
        overlay.id = 'adm-cd-overlay';
        const c = preview.counts || {};
        const t_owner = preview.owner || {};
        const t_tenant = preview.tenant || {};
        overlay.innerHTML = `
            <div class="cpw-forgot-modal" style="max-width:520px;">
                <div class="cpw-forgot-head">
                    <div class="cpw-forgot-title" style="color:#dc2626;">⚠ ${esc(tt('adm-cd-title'))}</div>
                    <button class="cpw-forgot-close" id="adm-cd-close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="cpw-forgot-body">
                    <p class="cpw-forgot-tip" style="background:#fef2f2;border-color:#fecaca;color:#991b1b;">${esc(tt('adm-cd-warn'))}</p>
                    <div style="background:#f4f4f0;border-radius:8px;padding:12px 14px;margin:12px 0;font-size:13px;">
                        <div style="font-weight:600;margin-bottom:8px;color:#0f172a;">${esc(t_owner.username || t_owner.email || username)}</div>
                        <div style="color:#64748b;margin-bottom:10px;">${esc(t_tenant.name || '—')}${t_tenant.tenant_type ? ' · ' + esc(t_tenant.tenant_type) : ''}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;color:#475569;">
                            <div>${esc(tt('adm-cd-c-employees'))}: <b>${c.employees || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-ocr'))}: <b>${c.ocr_records || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-clients'))}: <b>${c.clients || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-erp'))}: <b>${c.erp_endpoints || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-pushlog'))}: <b>${c.erp_push_logs || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-email'))}: <b>${c.email_accounts || 0}</b></div>
                            <div>${esc(tt('adm-cd-c-bank'))}: <b>${c.bank_recon_sessions || 0}</b></div>
                        </div>
                    </div>
                    <label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569;">${esc(tt('adm-cd-type-username').replace('{n}', t_owner.username || username))}</label>
                    <input type="text" id="adm-cd-username" autocomplete="off" placeholder="${esc(t_owner.username || username)}"
                        style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
                    <label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569;">${esc(tt('adm-cd-type-password'))}</label>
                    <input type="password" id="adm-cd-password" autocomplete="current-password"
                        style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
                </div>
                <div class="cpw-forgot-footer">
                    <button class="btn btn-ghost" id="adm-cd-cancel">${esc(tt('confirm-cancel') || '取消')}</button>
                    <button class="btn btn-danger" id="adm-cd-submit">${esc(tt('adm-cd-submit'))}</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        const close = () => overlay.remove();
        document.getElementById('adm-cd-close').addEventListener('click', close);
        document.getElementById('adm-cd-cancel').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });

        document.getElementById('adm-cd-submit').addEventListener('click', async () => {
            const u = (document.getElementById('adm-cd-username').value || '').trim();
            const p = document.getElementById('adm-cd-password').value || '';
            const expected = (t_owner.username || username || '').trim();
            if (u !== expected) {
                showToast(tt('adm-cd-username-mismatch'), 'error');
                return;
            }
            if (!p) {
                showToast(tt('adm-cd-password-required'), 'error');
                return;
            }
            try {
                const r = await fetch(
                    `/api/admin/users/${encodeURIComponent(uid)}/cascade-delete`,
                    {
                        method: 'POST',
                        headers: {
                            Authorization: 'Bearer ' + tok,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ confirm_username: u, confirm_password: p }),
                    }
                );
                const data = await r.json().catch(() => ({}));
                if (r.ok) {
                    showToast(tt('adm-cd-ok'), 'success');
                    close();
                    loadAdmUserList();
                } else {
                    // 把后端 detail 转成友好文案
                    const code = data.detail;
                    const map = {
                        'admin.password_invalid': tt('adm-cd-password-invalid'),
                        'admin.username_mismatch': tt('adm-cd-username-mismatch'),
                        'admin.cannot_delete_self': tt('adm-cd-cannot-self'),
                        'admin.not_an_owner': tt('adm-cd-not-owner'),
                        'admin.cascade_delete_failed': tt('adm-cd-fail'),
                    };
                    showToast(
                        map[code] || (typeof code === 'string' ? code : tt('adm-cd-fail')),
                        'error'
                    );
                }
            } catch (e) {
                showToast(tt('adm-cd-fail'), 'error');
            }
        });
    };

    // v109.4 · 用户详情抽屉(右侧滑出)· 展示完整字段
    window.__adm_open_user_drawer = async function (uid) {
        const tok = localStorage.getItem('mrpilot_token');
        let overlay = document.getElementById('adm-drawer-overlay');
        if (overlay) overlay.remove();
        overlay = document.createElement('div');
        overlay.className = 'adm-drawer-overlay';
        overlay.id = 'adm-drawer-overlay';
        overlay.dataset.uid = uid; // v111.3 · setLang 重渲用
        overlay.innerHTML = `
            <div class="adm-drawer">
                <div class="adm-drawer-head">
                    <div class="adm-drawer-title">${esc(tt('adm-drawer-title'))}</div>
                    <button class="adm-drawer-close" id="adm-drawer-close" aria-label="close">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>
                    </button>
                </div>
                <div class="adm-drawer-body" id="adm-drawer-body">
                    <div class="adm-drawer-loading">${esc(tt('adm-drawer-loading'))}</div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 等下一帧再加 .show class · 让 transition 生效
        requestAnimationFrame(() => overlay.classList.add('show'));

        const close = () => {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 250);
        };
        overlay.querySelector('#adm-drawer-close').addEventListener('click', close);
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) close();
        });

        // 拉详情
        try {
            const r = await fetch(`/api/admin/users/${uid}`, {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (!r.ok) {
                document.getElementById('adm-drawer-body').innerHTML =
                    `<div class="adm-drawer-error">${esc(tt('adm-drawer-error'))}</div>`;
                return;
            }
            const u = await r.json();
            renderAdmUserDrawer(u);
        } catch (e) {
            document.getElementById('adm-drawer-body').innerHTML =
                `<div class="adm-drawer-error">${esc(tt('adm-drawer-error'))}</div>`;
        }
    };

    // 抽屉内部渲染
    function renderAdmUserDrawer(u) {
        const body = document.getElementById('adm-drawer-body');
        if (!body) return;

        const fmtTime = (s) => {
            if (!s) return '—';
            try {
                const d = new Date(s);
                const now = new Date();
                const diff = Math.floor((now - d) / 1000);
                let rel;
                if (diff < 60) rel = tt('time-just-now');
                else if (diff < 3600) rel = tt('time-mins-ago', { n: Math.floor(diff / 60) });
                else if (diff < 86400) rel = tt('time-hours-ago', { n: Math.floor(diff / 3600) });
                else if (diff < 86400 * 30)
                    rel = tt('time-days-ago', { n: Math.floor(diff / 86400) });
                else rel = '';
                return d.toLocaleString() + (rel ? ' · ' + rel : '');
            } catch (e) {
                return s;
            }
        };

        const planLabelMap = {
            trial: 'Trial',
            free: 'Trial',
            solo: 'Pearnly Solo',
            pro: 'Pearnly Solo',
            plus: 'Pearnly Solo',
            team: 'Pearnly Team',
            firm: 'Pearnly Firm',
            enterprise: 'Enterprise',
            monthly: 'Monthly',
            lifetime: 'Lifetime',
        };
        const planLabel = planLabelMap[u.plan] || u.plan || '—';

        const lineStatus = u.line_user_id
            ? `<span class="adm-drawer-pill adm-pill-success">✓ ${esc(tt('adm-drawer-line-linked'))}</span>`
            : `<span class="adm-drawer-pill adm-pill-warn">○ ${esc(tt('adm-drawer-line-not-linked'))}</span>`;

        const riskBadge = u.has_risk_signal
            ? `<span class="adm-drawer-pill adm-pill-danger">⚠ ${esc(tt('adm-drawer-risky'))}</span>`
            : '';

        body.innerHTML = `
            <div class="adm-drawer-header-row">
                <div class="adm-drawer-avatar">${esc((u.email || u.username || '?').charAt(0).toUpperCase())}</div>
                <div class="adm-drawer-header-text">
                    <div class="adm-drawer-name">${esc(u.email || u.username || '')}</div>
                    <div class="adm-drawer-sub">${esc(u.company_name || tt('adm-drawer-no-company'))}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-account'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-plan'))}</div>
                    <div class="adm-drawer-value">
                        <span class="adm-plan-badge adm-plan-${esc(u.plan)}">${esc(planLabel)}</span>
                        ${u.days_left != null ? ` · ${u.days_left}d` : ''}
                    </div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-status'))}</div>
                    <div class="adm-drawer-value">${u.is_active === false ? esc(tt('adm-drawer-banned')) : esc(tt('adm-drawer-active'))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-line'))}</div>
                    <div class="adm-drawer-value">${lineStatus}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-role'))}</div>
                    <div class="adm-drawer-value">${u.is_super_admin ? '⭐ Super Admin' : esc(u.role || 'owner')}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-contact'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-email'))}</div>
                    <div class="adm-drawer-value">${esc(u.email || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-phone'))}</div>
                    <div class="adm-drawer-value">${esc(u.phone || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-line-id'))}</div>
                    <div class="adm-drawer-value">${esc(u.line_id || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-country'))}</div>
                    <div class="adm-drawer-value">${esc(u.country || '—')}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-signup'))} ${riskBadge}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-signed-up'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.created_at))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-source'))}</div>
                    <div class="adm-drawer-value">${esc(u.signup_source || tt('adm-drawer-source-direct'))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-ip'))}</div>
                    <div class="adm-drawer-value adm-drawer-mono">${esc(u.signup_ip || '—')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-fingerprint'))}</div>
                    <div class="adm-drawer-value adm-drawer-mono">${esc((u.signup_fingerprint || '—').slice(0, 16))}${u.signup_fingerprint ? '...' : ''}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-usage'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-month-ocr'))}</div>
                    <div class="adm-drawer-value">${u.ocr_used_month || 0} / ${u.ocr_quota || tt('adm-drawer-unlimited')}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-total-ocr'))}</div>
                    <div class="adm-drawer-value">${u.ocr_total || 0}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-ocr'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_ocr_at))}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-login'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_login_at))}</div>
                </div>
            </div>

            <div class="adm-drawer-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-payment'))}</div>
                <div class="adm-drawer-grid">
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-payments'))}</div>
                    <div class="adm-drawer-value">${u.payment_count || 0}</div>
                    <div class="adm-drawer-label">${esc(tt('adm-drawer-last-payment'))}</div>
                    <div class="adm-drawer-value">${esc(fmtTime(u.last_payment_at))}</div>
                </div>
            </div>

            ${
                !u.is_super_admin
                    ? `
            <div class="adm-drawer-section adm-drawer-actions-section">
                <div class="adm-drawer-section-title">${esc(tt('adm-drawer-sec-actions'))}</div>
                <div class="adm-drawer-actions-grid">
                    <button class="btn btn-primary" onclick="window.__adm_upgrade_from_drawer('${esc(u.id)}', '${esc(u.email || '')}')">
                        ${esc(tt('adm-drawer-btn-upgrade'))}
                    </button>
                    ${
                        u.is_active === false
                            ? `<button class="btn btn-ghost" onclick="window.__adm_unban_user('${esc(u.id)}')">${esc(tt('adm-drawer-btn-unban'))}</button>`
                            : `<button class="btn btn-danger" onclick="window.__adm_ban_user('${esc(u.id)}', '${esc(u.email || '')}')">${esc(tt('adm-drawer-btn-ban'))}</button>`
                    }
                </div>
            </div>
            `
                    : ''
            }
        `;
    }

    // v111.3 · 抽屉里点升级 → 复用现有快速升级对话框
    window.__adm_upgrade_from_drawer = function (uid, email) {
        if (typeof window.__adm_quick_upgrade === 'function') {
            window.__adm_quick_upgrade(uid, email);
        } else {
            showToast('upgrade dialog not loaded', 'error');
        }
    };
    // v111.3 · 封禁/解封用户(用现有 admin/users/ban API)
    window.__adm_ban_user = async function (uid, email) {
        const ok = await showConfirm(tt('adm-confirm-ban', { e: email }), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/ban`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'admin_action' }),
            });
            if (r.ok) {
                showToast(tt('adm-banned'), 'success');
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };
    window.__adm_unban_user = async function (uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/unban`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-unbanned'), 'success');
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };

    // v116 · 风控状态(模块内闭包)
    const _admRiskState = {
        collapsed: true, // 默认收起
        page: { ip: 1, fp: 1, heavy: 1 }, // 各分类当前页
        pageSize: 5,
        data: null, // 缓存上一次接口数据
    };

    function renderAdmRisk(r) {
        const wrap = document.getElementById('adm-risk-content');
        if (!wrap) return;
        if (r) _admRiskState.data = r;
        const data = _admRiskState.data || {};
        const sip = data.same_ip_signups || [];
        const sfp = data.same_fingerprint_signups || [];
        const heavy = data.heavy_ocr_users || [];
        const ev = data.risk_events_24h || [];
        const totalSignals = sip.length + sfp.length + heavy.length;
        const totalEvents = ev.reduce((a, e) => a + (e.count || 0), 0);

        // 全部干净:简单一行
        if (!totalSignals && !totalEvents) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-risk-clean'))}</div>`;
            return;
        }

        // 顶部 summary + 展开/收起
        const collapsed = _admRiskState.collapsed;
        const summary = `
            <div class="adm-risk-summary">
                <div class="adm-risk-summary-stats">
                    ${totalSignals > 0 ? `<span class="adm-risk-stat-pill warn">${totalSignals} ${esc(tt('adm-risk-stat-groups'))}</span>` : ''}
                    ${totalEvents > 0 ? `<span class="adm-risk-stat-pill info">${totalEvents} ${esc(tt('adm-risk-stat-events'))}</span>` : ''}
                </div>
                <button class="adm-risk-toggle-btn" onclick="window.__adm_risk_toggle()">
                    ${esc(collapsed ? tt('adm-risk-expand') : tt('adm-risk-collapse'))}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate(${collapsed ? '0' : '180'}deg); transition: transform 0.2s">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
            </div>`;

        if (collapsed) {
            wrap.innerHTML = summary;
            return;
        }

        // 展开 · 渲染 4 分组
        const renderGroup = (title, items, kind, renderRow) => {
            if (!items.length) return '';
            const ps = _admRiskState.pageSize;
            const cur = _admRiskState.page[kind] || 1;
            const totalPages = Math.max(1, Math.ceil(items.length / ps));
            const safeCur = Math.min(cur, totalPages);
            const slice = items.slice((safeCur - 1) * ps, safeCur * ps);
            const pager =
                totalPages > 1
                    ? `
                <div class="adm-risk-pager">
                    <button class="adm-risk-pager-btn" ${safeCur <= 1 ? 'disabled' : ''} onclick="window.__adm_risk_page('${kind}', ${safeCur - 1})">‹</button>
                    <span class="adm-risk-pager-info">${safeCur} / ${totalPages}</span>
                    <button class="adm-risk-pager-btn" ${safeCur >= totalPages ? 'disabled' : ''} onclick="window.__adm_risk_page('${kind}', ${safeCur + 1})">›</button>
                </div>`
                    : '';
            return `
                <div class="adm-risk-block">
                    <div class="adm-risk-title">${esc(title)} <span class="adm-risk-count">(${items.length})</span></div>
                    <div class="adm-risk-rows">${slice.map(renderRow).join('')}</div>
                    ${pager}
                </div>`;
        };

        const ipRows = renderGroup(
            tt('adm-risk-same-ip'),
            sip,
            'ip',
            (x) => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>IP</strong> <code>${esc(x.ip)}</code> · ${x.count} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-row-sub">${(x.accounts || [])
                        .slice(0, 3)
                        .map((a) => esc(a.email))
                        .join(' · ')}${(x.accounts || []).length > 3 ? ` …` : ''}</div>
                </div>
                <button class="adm-risk-detail-btn" onclick='window.__adm_risk_detail("ip", ${JSON.stringify(JSON.stringify(x))})'>${esc(tt('adm-risk-view-detail'))}</button>
            </div>`
        );

        const fpRows = renderGroup(
            tt('adm-risk-same-fp'),
            sfp,
            'fp',
            (x) => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>FP</strong> <code>${esc(x.fingerprint_short || '')}</code> · ${x.count} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-row-sub">${(x.accounts || [])
                        .slice(0, 3)
                        .map((a) => esc(a.email))
                        .join(' · ')}${(x.accounts || []).length > 3 ? ` …` : ''}</div>
                </div>
                <button class="adm-risk-detail-btn" onclick='window.__adm_risk_detail("fp", ${JSON.stringify(JSON.stringify(x))})'>${esc(tt('adm-risk-view-detail'))}</button>
            </div>`
        );

        const heavyRows = renderGroup(
            tt('adm-risk-heavy-ocr'),
            heavy,
            'heavy',
            (x) => `
            <div class="adm-risk-row">
                <div class="adm-risk-row-main">
                    <div><strong>${esc(x.email)}</strong> ${x.is_banned ? `<span class="adm-pill-banned">${esc(tt('adm-risk-banned-tag'))}</span>` : ''}</div>
                    <div class="adm-risk-row-sub">${esc(x.plan || '')} · ${x.ocr_today} ${esc(tt('adm-risk-ocr-24h'))}</div>
                </div>
                ${
                    x.is_banned
                        ? `<button class="adm-risk-detail-btn" onclick="window.__adm_unban_user('${x.user_id}')">${esc(tt('adm-drawer-btn-unban'))}</button>`
                        : `<button class="adm-risk-detail-btn danger" onclick="window.__adm_ban_user('${x.user_id}', '${esc(x.email)}')">${esc(tt('adm-drawer-btn-ban'))}</button>`
                }
            </div>`
        );

        const evBlock = ev.length
            ? `
            <div class="adm-risk-block">
                <div class="adm-risk-title">${esc(tt('adm-risk-events-24h'))}</div>
                <div class="adm-risk-tags">
                    ${ev.map((e) => `<span class="adm-tag ${e.event === 'disposable_email' || e.event === 'rate_limited_try_later' ? 'adm-tag-warn' : ''}">${esc(e.event)}: ${e.count}</span>`).join('')}
                </div>
            </div>`
            : '';

        wrap.innerHTML = summary + ipRows + fpRows + heavyRows + evBlock;
    }

    // v118 · export 给 applyLang · 切语言时立即用缓存数据重渲(不等 fetch)
    window.__rerenderAdmRisk = function () {
        renderAdmRisk();
    };

    // v116 · 折叠/展开
    window.__adm_risk_toggle = function () {
        _admRiskState.collapsed = !_admRiskState.collapsed;
        renderAdmRisk();
    };
    // v116 · 分页
    window.__adm_risk_page = function (kind, page) {
        _admRiskState.page[kind] = page;
        renderAdmRisk();
    };

    // v116 · 查看详情 modal · 显示 group 内所有 accounts + 操作按钮
    window.__adm_risk_detail = function (kind, groupJson) {
        let group;
        try {
            group = JSON.parse(groupJson);
        } catch (e) {
            return;
        }
        const accounts = group.accounts || [];
        const headerKey =
            kind === 'ip' ? `IP: ${group.ip}` : `Fingerprint: ${group.fingerprint_short || ''}`;

        // 关掉旧的(如果有)
        const old = document.getElementById('adm-risk-detail-modal');
        if (old) old.remove();

        const modal = document.createElement('div');
        modal.id = 'adm-risk-detail-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal modal-md">
                <div class="modal-head">
                    <div class="modal-title">${esc(tt('adm-risk-detail-title'))}</div>
                    <button class="modal-close" onclick="document.getElementById('adm-risk-detail-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="adm-risk-detail-meta">${esc(headerKey)} · ${accounts.length} ${esc(tt('adm-risk-accounts'))}</div>
                    <div class="adm-risk-detail-list" id="adm-risk-detail-list">
                        ${accounts
                            .map(
                                (a) => `
                            <div class="adm-risk-detail-row" data-uid="${esc(a.user_id)}">
                                <div class="adm-risk-detail-main">
                                    <div><strong>${esc(a.email)}</strong>
                                        ${a.is_banned ? `<span class="adm-pill-banned">${esc(tt('adm-risk-banned-tag'))}</span>` : ''}
                                    </div>
                                    <div class="adm-risk-detail-sub">${esc(a.plan || '')} · ${esc((a.created_at || '').slice(0, 10))}</div>
                                </div>
                                <div class="adm-risk-detail-actions">
                                    ${
                                        a.is_banned
                                            ? `<button class="adm-risk-detail-btn" onclick="window.__adm_risk_modal_unban('${esc(a.user_id)}')">${esc(tt('adm-drawer-btn-unban'))}</button>`
                                            : `<button class="adm-risk-detail-btn danger" onclick="window.__adm_risk_modal_ban('${esc(a.user_id)}', '${esc(a.email)}')">${esc(tt('adm-drawer-btn-ban'))}</button>`
                                    }
                                </div>
                            </div>
                        `
                            )
                            .join('')}
                    </div>
                </div>
                <div class="modal-foot">
                    <button class="btn-ghost" onclick="document.getElementById('adm-risk-detail-modal').remove()">${esc(tt('common-close'))}</button>
                    <button class="btn-danger" onclick='window.__adm_risk_batch_ban(${JSON.stringify(JSON.stringify(accounts))})'>
                        ${esc(tt('adm-risk-batch-ban'))} (${accounts.filter((a) => !a.is_banned).length})
                    </button>
                </div>
            </div>`;
        document.body.appendChild(modal);
    };

    // v116 · modal 内单个 ban/unban(操作完后刷新整个风控)
    window.__adm_risk_modal_ban = async function (uid, email) {
        const ok = await showConfirm(tt('adm-confirm-ban', { e: email }), { danger: true });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/ban`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'risk_review' }),
            });
            if (r.ok) {
                showToast(tt('adm-banned'), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };
    window.__adm_risk_modal_unban = async function (uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/users/${uid}/unban`, {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-unbanned'), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };

    // v116 · 批量封禁(modal 底部按钮)
    window.__adm_risk_batch_ban = async function (accountsJson) {
        let accounts;
        try {
            accounts = JSON.parse(accountsJson);
        } catch (e) {
            return;
        }
        const targets = accounts.filter((a) => !a.is_banned).map((a) => a.user_id);
        if (!targets.length) {
            showToast(tt('adm-risk-no-targets'), 'info');
            return;
        }
        const ok = await showConfirm(tt('adm-risk-confirm-batch', { n: targets.length }), {
            danger: true,
        });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/risk/batch-ban', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_ids: targets, reason: 'risk_batch_ban' }),
            });
            const j = await r.json().catch(() => ({}));
            if (r.ok && j.ok) {
                showToast(tt('adm-risk-batch-done', { n: j.banned || 0 }), 'success');
                document.getElementById('adm-risk-detail-modal')?.remove();
                loadAdminUsersPage();
            } else showToast(tt('adm-action-fail'), 'error');
        } catch (e) {
            showToast(tt('adm-action-fail'), 'error');
        }
    };

    // 路由切换触发(hash 变化时)
    function bindAdminUsersRoute() {
        const fire = () => {
            if (location.hash === '#admin-users') {
                loadAdminUsersPage();
            }
        };
        window.addEventListener('hashchange', fire);
        fire();
    }

    // 把额外 i18n 加进来
    Object.assign(I18N.zh, {
        'nav-admin-users': '用户管理',
        'admin-users-title': '用户管理',
        'admin-users-sub': '注册用户 · 套餐分布 · 待审核付款 · 风控',
        'adm-kpi-today': '今日新增',
        'adm-kpi-week': '本周新增',
        'adm-kpi-month': '本月新增',
        'adm-kpi-conv': '付费转化',
        'adm-pending-title': '待审核付款',
        'adm-pending-empty': '没有待审核的付款',
        'adm-refresh': '刷新',
        'adm-view-slip': '查看截图',
        'adm-approve': '批准',
        'adm-reject': '拒绝',
        'adm-approved': '已批准 · 用户已升级',
        'adm-rejected': '已拒绝',
        'adm-confirm-reject': '确认拒绝此付款?',
        'adm-action-fail': '操作失败',
        'adm-expiring-title': 'Trial 即将到期(≤ 3 天)',
        'adm-expiring-empty': '无',
        'adm-quick-upgrade': '一键升级',
        'adm-users-title': '所有用户',
        'adm-users-empty': '没有用户',
        // v118.12 · 客户/员工分 tab
        'adm-tab-customers': '客户',
        'adm-cascade-del': '删除账号',
        'adm-cascade-del-tip': '永久删除该账号 + 整个事务所数据 · 不可恢复',
        'adm-cd-title': '永久删除客户账号',
        'adm-cd-warn':
            '此操作将永久删除该老板 + 旗下所有员工 + 全部识别记录 / 客户档案 / ERP 配置 / 邮箱配置 / 对账数据。删除后不可恢复 · 请确认无误。',
        'adm-cd-c-employees': '员工',
        'adm-cd-c-ocr': '发票识别',
        'adm-cd-c-clients': '客户档案',
        'adm-cd-c-erp': 'ERP 端点',
        'adm-cd-c-pushlog': '推送日志',
        'adm-cd-c-email': '邮箱配置',
        'adm-cd-c-bank': '对账会话',
        'adm-cd-type-username': '请输入要删除的账号「{n}」以确认:',
        'adm-cd-type-password': '输入您(超管)自己的登录密码:',
        'adm-cd-submit': '永久删除',
        'adm-cd-username-mismatch': '账号名不匹配 · 已取消',
        'adm-cd-password-required': '请输入您的密码',
        'adm-cd-password-invalid': '密码错误',
        'adm-cd-cannot-self': '不能删除自己',
        'adm-cd-not-owner': '该用户不是老板账号',
        'adm-cd-ok': '已永久删除',
        'adm-cd-fail': '删除失败',
        'adm-cd-preview-fail': '获取影响范围失败',

        'adm-tab-employees': '员工',
        'adm-employees-empty': '暂无员工',
        'adm-employee-search-ph': '员工名 / 邮箱 / 老板 / 公司',
        'adm-emp-col-name': '员工',
        'adm-emp-col-owner': '所属老板',
        'adm-emp-col-tenant': '事务所',
        // v118.28.6 · 超管员工 tab 只读提示
        'adm-emp-readonly-tip':
            '本视图为只读 · 员工管理(启用/禁用/重置密码/移除)由所属老板自行操作 · 如需协助请打开老板抽屉',
        'adm-emp-col-actions': '操作',
        'adm-emp-enable': '启用',
        'adm-emp-disable': '禁用',
        'adm-emp-reset-pw': '重置密码',
        'adm-emp-remove': '移除',
        'adm-emp-confirm-enable': '启用',
        'adm-emp-confirm-disable': '禁用',
        'adm-emp-confirm-reset-pw': '为 {n} 重置密码?',
        'adm-emp-confirm-remove': '⚠ 永久移除员工 {n}?\n该员工的账号将被删除 · 此操作不可恢复。',
        'adm-emp-confirm-type-name': '请输入员工名 "{n}" 以确认删除:',
        'adm-emp-name-mismatch': '员工名不匹配 · 已取消',
        'adm-emp-toggle-ok': '操作成功',
        'adm-emp-toggle-fail': '操作失败',
        'adm-emp-new-pw': '新临时密码(请复制并告诉员工):\n\n{n}\n\n下次登录会强制员工改密。',
        'adm-emp-reset-fail': '重置失败',
        'adm-emp-remove-ok': '已移除',
        'adm-emp-copy-and-close': '我已复制',
        'adm-emp-remove-fail': '移除失败',
        'adm-emp-col-status': '状态',
        'adm-emp-col-last-login': '最后登录',
        'adm-emp-col-created': '创建时间',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': '全部套餐',
        'adm-col-email': '邮箱',
        'adm-col-company': '公司',
        'adm-col-plan': '套餐',
        'adm-search-ph': '邮箱 / 公司名',
        'adm-col-usage': '本月用量',
        'adm-col-country': '国家',
        'adm-col-actions': '操作',
        'adm-upgrade': '升级',
        'adm-ban': '封停',
        // v109.4 · admin modal
        'adm-upgrade-title': '修改套餐',
        'adm-upg-confirm': '确认升级',
        'adm-pick-plan': '请选择套餐',
        'adm-upgrade-ok': '套餐已修改',
        'adm-upgrade-fail': '修改失败',
        'adm-ban-title': '封停账号',
        'adm-ban-warn': '⚠ 封停后该账号将无法登录 · 操作可撤销',
        'adm-ban-reason': '原因',
        'adm-ban-reason-ph': '如:abuse / 欠费 / 测试',
        'adm-ban-confirm': '确认封停',
        'adm-ban-ok': '已封停',
        'adm-ban-fail': '操作失败',
        // v109.4 · 用户详情抽屉
        'adm-drawer-title': '用户详情',
        'adm-drawer-loading': '加载中...',
        'adm-drawer-error': '加载失败 · 请稍后重试',
        'adm-drawer-no-company': '未填写公司',
        'adm-drawer-sec-account': '账户',
        'adm-drawer-sec-contact': '联系方式',
        'adm-drawer-sec-signup': '注册信息',
        'adm-drawer-sec-usage': '使用情况',
        'adm-drawer-sec-payment': '付款记录',
        'adm-drawer-plan': '套餐',
        'adm-drawer-status': '状态',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': '角色',
        'adm-drawer-email': '邮箱',
        'adm-drawer-phone': '手机',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': '国家',
        'adm-drawer-signed-up': '注册时间',
        'adm-drawer-source': '注册来源',
        'adm-drawer-source-direct': '直接访问',
        'adm-drawer-ip': '注册 IP',
        'adm-drawer-fingerprint': '设备指纹',
        'adm-drawer-month-ocr': '本月用量',
        'adm-drawer-total-ocr': '累计 OCR',
        'adm-drawer-last-ocr': '最近识别',
        'adm-drawer-last-login': '最后登录',
        'adm-drawer-payments': '付款次数',
        'adm-drawer-last-payment': '最近付款',
        'adm-drawer-banned': '🚫 已封停',
        'adm-drawer-active': '✓ 正常',
        'adm-drawer-line-linked': '已绑定',
        'adm-drawer-line-not-linked': '未绑定',
        'adm-drawer-risky': '风险用户',
        'adm-drawer-unlimited': '无限',
        'time-just-now': '刚刚',
        'time-mins-ago': '{n} 分钟前',
        'time-hours-ago': '{n} 小时前',
        'time-days-ago': '{n} 天前',
        'adm-risk-title': '⚠ 风控 · 可疑活动',
        'adm-risk-events-24h': '24h 风控事件',
        'adm-risk-same-ip': '同 IP 注册多个账号',
        'adm-risk-same-fp': '同设备指纹注册多个',
        'adm-risk-heavy-ocr': 'OCR 异常用量(24h > 30 张)',
        'adm-risk-stat-groups': '可疑分组',
        'adm-risk-stat-events': '风控事件',
        'adm-risk-expand': '展开查看',
        'adm-risk-collapse': '收起',
        'adm-risk-accounts': '个账号',
        'adm-risk-view-detail': '查看详情',
        'adm-risk-detail-title': '可疑分组详情',
        'adm-risk-batch-ban': '批量封禁',
        'adm-risk-confirm-batch': '确认封禁这 {n} 个账号?此操作可在用户管理中解除',
        'adm-risk-batch-done': '已封禁 {n} 个账号',
        'adm-risk-no-targets': '没有可封禁的账号(均已封禁或为超管)',
        'adm-risk-banned-tag': '已封禁',
        'adm-risk-ocr-24h': '张 / 24h',
        'common-close': '关闭',
        'adm-risk-clean': '✓ 当前无异常',
        'adm-engine-ocr': '单据识别',
        'adm-engine-ocr-backup': '单据识别(备用)',
        'adm-engine-epdf': '电子PDF',
        'adm-engine-vex': '销项税对账',
    });
    Object.assign(I18N.en, {
        'nav-admin-users': 'Users',
        'admin-users-title': 'User Management',
        'admin-users-sub': 'Signups · plan distribution · pending payments · risk control',
        'adm-kpi-today': 'Today',
        'adm-kpi-week': 'Week',
        'adm-kpi-month': 'Month',
        'adm-kpi-conv': 'Conversion',
        'adm-pending-title': 'Pending Payments',
        'adm-pending-empty': 'No pending payments',
        'adm-refresh': 'Refresh',
        'adm-view-slip': 'View slip',
        'adm-approve': 'Approve',
        'adm-reject': 'Reject',
        'adm-approved': 'Approved · user upgraded',
        'adm-rejected': 'Rejected',
        'adm-confirm-reject': 'Confirm reject?',
        'adm-action-fail': 'Action failed',
        'adm-expiring-title': 'Trial expiring soon (≤ 3 days)',
        'adm-expiring-empty': 'None',
        'adm-quick-upgrade': 'Quick upgrade',
        'adm-users-title': 'All Users',
        'adm-users-empty': 'No users',
        // v118.12 · customers / employees tabs
        'adm-tab-customers': 'Customers',
        'adm-cascade-del': 'Delete account',
        'adm-cascade-del-tip': 'Permanently delete this account + entire firm data · cannot undo',
        'adm-cd-title': 'Permanently delete customer',
        'adm-cd-warn':
            'This will permanently delete the owner + all employees + all OCR records / clients / ERP configs / email configs / reconciliation data. Cannot be undone — please confirm.',
        'adm-cd-c-employees': 'Employees',
        'adm-cd-c-ocr': 'OCR records',
        'adm-cd-c-clients': 'Clients',
        'adm-cd-c-erp': 'ERP endpoints',
        'adm-cd-c-pushlog': 'Push logs',
        'adm-cd-c-email': 'Email accounts',
        'adm-cd-c-bank': 'Bank recon',
        'adm-cd-type-username': 'Type username "{n}" to confirm:',
        'adm-cd-type-password': 'Enter YOUR (super-admin) login password:',
        'adm-cd-submit': 'Permanently delete',
        'adm-cd-username-mismatch': 'Username mismatch · cancelled',
        'adm-cd-password-required': 'Enter your password',
        'adm-cd-password-invalid': 'Wrong password',
        'adm-cd-cannot-self': 'Cannot delete yourself',
        'adm-cd-not-owner': 'Not an owner account',
        'adm-cd-ok': 'Deleted',
        'adm-cd-fail': 'Delete failed',
        'adm-cd-preview-fail': 'Failed to fetch impact',

        'adm-tab-employees': 'Employees',
        'adm-employees-empty': 'No employees yet',
        'adm-employee-search-ph': 'Username / email / owner / firm',
        'adm-emp-col-name': 'Employee',
        'adm-emp-col-owner': 'Owner',
        'adm-emp-col-tenant': 'Firm',
        // v118.28.6
        'adm-emp-readonly-tip':
            "Read-only view · Employee management (enable/disable/reset password/remove) is the firm owner's responsibility · Open the owner drawer if assistance is needed",
        'adm-emp-col-actions': 'Actions',
        'adm-emp-enable': 'Enable',
        'adm-emp-disable': 'Disable',
        'adm-emp-reset-pw': 'Reset password',
        'adm-emp-remove': 'Remove',
        'adm-emp-confirm-enable': 'Enable',
        'adm-emp-confirm-disable': 'Disable',
        'adm-emp-confirm-reset-pw': 'Reset password for {n}?',
        'adm-emp-confirm-remove':
            '⚠ Permanently remove employee {n}?\nAccount will be deleted · this action cannot be undone.',
        'adm-emp-confirm-type-name': 'Type employee name "{n}" to confirm:',
        'adm-emp-name-mismatch': 'Name mismatch · cancelled',
        'adm-emp-toggle-ok': 'OK',
        'adm-emp-toggle-fail': 'Failed',
        'adm-emp-new-pw':
            'New temp password (copy and tell employee):\n\n{n}\n\nEmployee will be forced to change on next login.',
        'adm-emp-reset-fail': 'Reset failed',
        'adm-emp-remove-ok': 'Removed',
        'adm-emp-copy-and-close': 'Copied',
        'adm-emp-remove-fail': 'Remove failed',
        'adm-emp-col-status': 'Status',
        'adm-emp-col-last-login': 'Last login',
        'adm-emp-col-created': 'Created',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': 'All plans',
        'adm-col-email': 'Email',
        'adm-col-company': 'Company',
        'adm-col-plan': 'Plan',
        'adm-search-ph': 'Email / Company',
        'adm-col-usage': 'Usage',
        'adm-col-country': 'Country',
        'adm-col-actions': 'Actions',
        'adm-upgrade': 'Upgrade',
        'adm-ban': 'Ban',
        // v109.4 · admin modal
        'adm-upgrade-title': 'Change Plan',
        'adm-upg-confirm': 'Confirm Upgrade',
        'adm-pick-plan': 'Please select a plan',
        'adm-upgrade-ok': 'Plan updated',
        'adm-upgrade-fail': 'Update failed',
        'adm-ban-title': 'Ban Account',
        'adm-ban-warn': '⚠ Banned account cannot login · action is reversible',
        'adm-ban-reason': 'Reason',
        'adm-ban-reason-ph': 'e.g. abuse / unpaid / test',
        'adm-ban-confirm': 'Confirm Ban',
        'adm-ban-ok': 'Banned',
        'adm-ban-fail': 'Failed',
        // v109.4 · user detail drawer
        'adm-drawer-title': 'User Details',
        'adm-drawer-loading': 'Loading...',
        'adm-drawer-error': 'Failed to load · please retry',
        'adm-drawer-no-company': 'No company',
        'adm-drawer-sec-account': 'Account',
        'adm-drawer-sec-contact': 'Contact',
        'adm-drawer-sec-signup': 'Sign-up Info',
        'adm-drawer-sec-usage': 'Usage',
        'adm-drawer-sec-payment': 'Payments',
        'adm-drawer-plan': 'Plan',
        'adm-drawer-status': 'Status',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': 'Role',
        'adm-drawer-email': 'Email',
        'adm-drawer-phone': 'Phone',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': 'Country',
        'adm-drawer-signed-up': 'Signed up',
        'adm-drawer-source': 'Source',
        'adm-drawer-source-direct': 'Direct',
        'adm-drawer-ip': 'Sign-up IP',
        'adm-drawer-fingerprint': 'Device fingerprint',
        'adm-drawer-month-ocr': 'OCR this month',
        'adm-drawer-total-ocr': 'OCR total',
        'adm-drawer-last-ocr': 'Last OCR',
        'adm-drawer-last-login': 'Last login',
        'adm-drawer-payments': 'Payment count',
        'adm-drawer-last-payment': 'Last payment',
        'adm-drawer-banned': '🚫 Banned',
        'adm-drawer-active': '✓ Active',
        'adm-drawer-line-linked': 'Linked',
        'adm-drawer-line-not-linked': 'Not linked',
        'adm-drawer-risky': 'Risk user',
        'adm-drawer-unlimited': 'Unlimited',
        'time-just-now': 'just now',
        'time-mins-ago': '{n} min ago',
        'time-hours-ago': '{n} hr ago',
        'time-days-ago': '{n} days ago',
        'adm-risk-title': '⚠ Risk · Suspicious Activity',
        'adm-risk-events-24h': '24h risk events',
        'adm-risk-same-ip': 'Same IP multi-signups',
        'adm-risk-same-fp': 'Same fingerprint multi-signups',
        'adm-risk-heavy-ocr': 'Heavy OCR (>30 in 24h)',
        'adm-risk-stat-groups': 'suspicious groups',
        'adm-risk-stat-events': 'risk events',
        'adm-risk-expand': 'Expand',
        'adm-risk-collapse': 'Collapse',
        'adm-risk-accounts': 'accounts',
        'adm-risk-view-detail': 'View detail',
        'adm-risk-detail-title': 'Suspicious group detail',
        'adm-risk-batch-ban': 'Batch ban',
        'adm-risk-confirm-batch':
            'Ban these {n} accounts? You can unban them later in user management.',
        'adm-risk-batch-done': '{n} accounts banned',
        'adm-risk-no-targets': 'No accounts to ban (all banned or super-admin)',
        'adm-risk-banned-tag': 'Banned',
        'adm-risk-ocr-24h': 'OCRs / 24h',
        'common-close': 'Close',
        'adm-risk-clean': '✓ All clear',
        'adm-engine-ocr': 'Invoice OCR',
        'adm-engine-ocr-backup': 'Invoice OCR (backup)',
        'adm-engine-epdf': 'Electronic PDF',
        'adm-engine-vex': 'Output VAT Reconciliation',
    });
    Object.assign(I18N.th, {
        'nav-admin-users': 'จัดการผู้ใช้',
        'admin-users-title': 'จัดการผู้ใช้',
        'admin-users-sub': 'ผู้สมัคร · แพ็กเกจ · รอตรวจสอบ · ควบคุมความเสี่ยง',
        'adm-kpi-today': 'วันนี้',
        'adm-kpi-week': 'สัปดาห์นี้',
        'adm-kpi-month': 'เดือนนี้',
        'adm-kpi-conv': 'อัตราชำระ',
        'adm-pending-title': 'รอตรวจสอบการชำระ',
        'adm-pending-empty': 'ไม่มี',
        'adm-refresh': 'รีเฟรช',
        'adm-view-slip': 'ดูสลิป',
        'adm-approve': 'อนุมัติ',
        'adm-reject': 'ปฏิเสธ',
        'adm-approved': 'อนุมัติแล้ว · ผู้ใช้ได้รับการอัปเกรด',
        'adm-rejected': 'ปฏิเสธแล้ว',
        'adm-confirm-reject': 'ยืนยันปฏิเสธ?',
        'adm-action-fail': 'ไม่สำเร็จ',
        'adm-expiring-title': 'ทดลองใกล้หมดอายุ (≤ 3 วัน)',
        'adm-expiring-empty': 'ไม่มี',
        'adm-quick-upgrade': 'อัปเกรดทันที',
        'adm-users-title': 'ผู้ใช้ทั้งหมด',
        'adm-users-empty': 'ไม่มี',
        // v118.12 · ลูกค้า / พนักงาน
        'adm-tab-customers': 'ลูกค้า',
        'adm-cascade-del': 'ลบบัญชี',
        'adm-cascade-del-tip': 'ลบบัญชีและข้อมูลสำนักงานทั้งหมดอย่างถาวร · ไม่สามารถกู้คืนได้',
        'adm-cd-title': 'ลบลูกค้าอย่างถาวร',
        'adm-cd-warn':
            'การดำเนินการนี้จะลบเจ้าของ + พนักงานทั้งหมด + ประวัติ OCR / ลูกค้า / ERP / อีเมล / กระทบยอดทั้งหมดอย่างถาวร · ไม่สามารถกู้คืนได้',
        'adm-cd-c-employees': 'พนักงาน',
        'adm-cd-c-ocr': 'OCR',
        'adm-cd-c-clients': 'ลูกค้า',
        'adm-cd-c-erp': 'ERP',
        'adm-cd-c-pushlog': 'Push logs',
        'adm-cd-c-email': 'อีเมล',
        'adm-cd-c-bank': 'กระทบยอด',
        'adm-cd-type-username': 'พิมพ์ชื่อผู้ใช้ "{n}" เพื่อยืนยัน:',
        'adm-cd-type-password': 'พิมพ์รหัสผ่าน(ผู้ดูแลระบบ)ของคุณ:',
        'adm-cd-submit': 'ลบถาวร',
        'adm-cd-username-mismatch': 'ชื่อไม่ตรงกัน · ยกเลิก',
        'adm-cd-password-required': 'กรอกรหัสผ่าน',
        'adm-cd-password-invalid': 'รหัสผ่านไม่ถูกต้อง',
        'adm-cd-cannot-self': 'ลบตัวเองไม่ได้',
        'adm-cd-not-owner': 'ไม่ใช่บัญชีเจ้าของ',
        'adm-cd-ok': 'ลบแล้ว',
        'adm-cd-fail': 'ลบล้มเหลว',
        'adm-cd-preview-fail': 'ดึงข้อมูลผลกระทบล้มเหลว',

        'adm-tab-employees': 'พนักงาน',
        'adm-employees-empty': 'ยังไม่มีพนักงาน',
        'adm-employee-search-ph': 'ชื่อผู้ใช้ / อีเมล / เจ้าของ / สำนักงาน',
        'adm-emp-col-name': 'พนักงาน',
        'adm-emp-col-owner': 'เจ้าของ',
        'adm-emp-col-tenant': 'สำนักงาน',
        // v118.28.6
        'adm-emp-readonly-tip':
            'มุมมองแบบอ่านอย่างเดียว · การจัดการพนักงาน (เปิด/ปิด/รีเซ็ตรหัสผ่าน/ลบ) เป็นหน้าที่ของเจ้าของสำนักงาน · เปิดลิ้นชักเจ้าของหากต้องการช่วยเหลือ',
        'adm-emp-col-actions': 'การดำเนินการ',
        'adm-emp-enable': 'เปิดใช้',
        'adm-emp-disable': 'ปิดใช้',
        'adm-emp-reset-pw': 'รีเซ็ตรหัสผ่าน',
        'adm-emp-remove': 'ลบ',
        'adm-emp-confirm-enable': 'เปิดใช้',
        'adm-emp-confirm-disable': 'ปิดใช้',
        'adm-emp-confirm-reset-pw': 'รีเซ็ตรหัสผ่านให้ {n}?',
        'adm-emp-confirm-remove': '⚠ ลบพนักงาน {n} อย่างถาวร?\nบัญชีจะถูกลบ · ไม่สามารถกู้คืนได้',
        'adm-emp-confirm-type-name': 'พิมพ์ชื่อพนักงาน "{n}" เพื่อยืนยัน:',
        'adm-emp-name-mismatch': 'ชื่อไม่ตรงกัน · ยกเลิก',
        'adm-emp-toggle-ok': 'สำเร็จ',
        'adm-emp-toggle-fail': 'ล้มเหลว',
        'adm-emp-new-pw':
            'รหัสผ่านชั่วคราวใหม่(คัดลอกและบอกพนักงาน):\n\n{n}\n\nพนักงานจะถูกบังคับให้เปลี่ยนรหัสในการเข้าสู่ระบบครั้งถัดไป',
        'adm-emp-reset-fail': 'รีเซ็ตล้มเหลว',
        'adm-emp-remove-ok': 'ลบแล้ว',
        'adm-emp-copy-and-close': 'คัดลอกแล้ว',
        'adm-emp-remove-fail': 'ลบล้มเหลว',
        'adm-emp-col-status': 'สถานะ',
        'adm-emp-col-last-login': 'เข้าใช้ล่าสุด',
        'adm-emp-col-created': 'สร้างเมื่อ',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': 'แพ็กเกจทั้งหมด',
        'adm-col-email': 'อีเมล',
        'adm-col-company': 'บริษัท',
        'adm-col-plan': 'แพ็กเกจ',
        'adm-search-ph': 'อีเมล / บริษัท',
        'adm-col-usage': 'ใช้แล้ว',
        'adm-col-country': 'ประเทศ',
        'adm-col-actions': 'จัดการ',
        'adm-upgrade': 'อัปเกรด',
        'adm-ban': 'ระงับ',
        // v109.4 · admin modal
        'adm-upgrade-title': 'เปลี่ยนแพ็กเกจ',
        'adm-upg-confirm': 'ยืนยันอัปเกรด',
        'adm-pick-plan': 'กรุณาเลือกแพ็กเกจ',
        'adm-upgrade-ok': 'อัปเดตแพ็กเกจแล้ว',
        'adm-upgrade-fail': 'อัปเดตไม่สำเร็จ',
        'adm-ban-title': 'ระงับบัญชี',
        'adm-ban-warn': '⚠ บัญชีที่ถูกระงับจะเข้าสู่ระบบไม่ได้ · สามารถยกเลิกได้',
        'adm-ban-reason': 'เหตุผล',
        'adm-ban-reason-ph': 'เช่น abuse / ค้างชำระ / ทดสอบ',
        'adm-ban-confirm': 'ยืนยันระงับ',
        'adm-ban-ok': 'ระงับแล้ว',
        'adm-ban-fail': 'ล้มเหลว',
        // v109.4 · ลิ้นชักรายละเอียดผู้ใช้
        'adm-drawer-title': 'รายละเอียดผู้ใช้',
        'adm-drawer-loading': 'กำลังโหลด...',
        'adm-drawer-error': 'โหลดไม่สำเร็จ · ลองใหม่',
        'adm-drawer-no-company': 'ไม่ได้กรอกบริษัท',
        'adm-drawer-sec-account': 'บัญชี',
        'adm-drawer-sec-contact': 'การติดต่อ',
        'adm-drawer-sec-signup': 'ข้อมูลสมัคร',
        'adm-drawer-sec-usage': 'การใช้งาน',
        'adm-drawer-sec-payment': 'การชำระ',
        'adm-drawer-plan': 'แพ็กเกจ',
        'adm-drawer-status': 'สถานะ',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': 'บทบาท',
        'adm-drawer-email': 'อีเมล',
        'adm-drawer-phone': 'โทรศัพท์',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': 'ประเทศ',
        'adm-drawer-signed-up': 'สมัครเมื่อ',
        'adm-drawer-source': 'ช่องทาง',
        'adm-drawer-source-direct': 'เข้าตรง',
        'adm-drawer-ip': 'IP ที่สมัคร',
        'adm-drawer-fingerprint': 'ลายนิ้วมืออุปกรณ์',
        'adm-drawer-month-ocr': 'OCR เดือนนี้',
        'adm-drawer-total-ocr': 'OCR รวม',
        'adm-drawer-last-ocr': 'OCR ล่าสุด',
        'adm-drawer-last-login': 'เข้าสู่ระบบล่าสุด',
        'adm-drawer-payments': 'จำนวนชำระ',
        'adm-drawer-last-payment': 'ชำระล่าสุด',
        'adm-drawer-banned': '🚫 ระงับแล้ว',
        'adm-drawer-active': '✓ ปกติ',
        'adm-drawer-line-linked': 'เชื่อมแล้ว',
        'adm-drawer-line-not-linked': 'ยังไม่เชื่อม',
        'adm-drawer-risky': 'ผู้ใช้เสี่ยง',
        'adm-drawer-unlimited': 'ไม่จำกัด',
        'time-just-now': 'เพิ่งจะ',
        'time-mins-ago': '{n} นาทีที่แล้ว',
        'time-hours-ago': '{n} ชั่วโมงที่แล้ว',
        'time-days-ago': '{n} วันที่แล้ว',
        'adm-risk-title': '⚠ ควบคุมความเสี่ยง',
        'adm-risk-events-24h': 'เหตุการณ์ 24h',
        'adm-risk-same-ip': 'IP เดียวกันสมัครหลายบัญชี',
        'adm-risk-same-fp': 'อุปกรณ์เดียวกันสมัครหลายบัญชี',
        'adm-risk-heavy-ocr': 'OCR ผิดปกติ (>30 ใน 24h)',
        'adm-risk-stat-groups': 'กลุ่มน่าสงสัย',
        'adm-risk-stat-events': 'เหตุการณ์ความเสี่ยง',
        'adm-risk-expand': 'ขยาย',
        'adm-risk-collapse': 'ย่อ',
        'adm-risk-accounts': 'บัญชี',
        'adm-risk-view-detail': 'ดูรายละเอียด',
        'adm-risk-detail-title': 'รายละเอียดกลุ่มน่าสงสัย',
        'adm-risk-batch-ban': 'แบนหลายบัญชี',
        'adm-risk-confirm-batch': 'แบน {n} บัญชีนี้? สามารถปลดแบนภายหลังได้',
        'adm-risk-batch-done': 'แบน {n} บัญชีเรียบร้อย',
        'adm-risk-no-targets': 'ไม่มีบัญชีให้แบน (แบนหมดแล้วหรือเป็นแอดมิน)',
        'adm-risk-banned-tag': 'ถูกแบน',
        'adm-risk-ocr-24h': 'OCR / 24 ชม.',
        'common-close': 'ปิด',
        'adm-risk-clean': '✓ ไม่มีความผิดปกติ',
        'adm-engine-ocr': 'OCR หลัก',
        'adm-engine-ocr-backup': 'OCR สำรอง',
        'adm-engine-epdf': 'PDF อิเล็กทรอนิกส์',
        'adm-engine-vex': 'กระทบยอดภาษีขาย',
    });
    Object.assign(I18N.ja, {
        'nav-admin-users': 'ユーザー管理',
        'admin-users-title': 'ユーザー管理',
        'admin-users-sub': '登録 · プラン分布 · 審査待ち · リスク管理',
        'adm-kpi-today': '今日',
        'adm-kpi-week': '今週',
        'adm-kpi-month': '今月',
        'adm-kpi-conv': '有料転換',
        'adm-pending-title': '審査待ちの支払',
        'adm-pending-empty': 'なし',
        'adm-refresh': '更新',
        'adm-view-slip': 'スリップ',
        'adm-approve': '承認',
        'adm-reject': '拒否',
        'adm-approved': '承認 · ユーザー昇格',
        'adm-rejected': '拒否済',
        'adm-confirm-reject': '拒否しますか?',
        'adm-action-fail': '失敗',
        'adm-expiring-title': '試用期限間近(≤ 3 日)',
        'adm-expiring-empty': 'なし',
        'adm-quick-upgrade': '即昇格',
        'adm-users-title': '全ユーザー',
        'adm-users-empty': 'なし',
        // v118.12 · 顧客 / 社員
        'adm-tab-customers': '顧客',
        'adm-cascade-del': 'アカウント削除',
        'adm-cascade-del-tip': 'アカウントと事務所データを完全削除 · 復元不可',
        'adm-cd-title': '顧客を完全削除',
        'adm-cd-warn':
            'オーナー + 全社員 + OCR履歴 / 顧客 / ERP / メール / 銀行照合データを完全削除します · 復元不可 · 確認してください',
        'adm-cd-c-employees': '社員',
        'adm-cd-c-ocr': 'OCR',
        'adm-cd-c-clients': '顧客',
        'adm-cd-c-erp': 'ERP',
        'adm-cd-c-pushlog': 'プッシュログ',
        'adm-cd-c-email': 'メール',
        'adm-cd-c-bank': '銀行照合',
        'adm-cd-type-username': 'ユーザー名 "{n}" を入力して確認:',
        'adm-cd-type-password': 'あなた(管理者)のログインパスワードを入力:',
        'adm-cd-submit': '完全削除',
        'adm-cd-username-mismatch': '名前が一致しません · キャンセル',
        'adm-cd-password-required': 'パスワードを入力',
        'adm-cd-password-invalid': 'パスワード違い',
        'adm-cd-cannot-self': '自分を削除できません',
        'adm-cd-not-owner': 'オーナーアカウントではない',
        'adm-cd-ok': '削除済み',
        'adm-cd-fail': '削除失敗',
        'adm-cd-preview-fail': '影響範囲取得失敗',

        'adm-tab-employees': '社員',
        'adm-employees-empty': '社員なし',
        'adm-employee-search-ph': 'ユーザー名 / メール / オーナー / 事務所',
        'adm-emp-col-name': '社員',
        'adm-emp-col-owner': 'オーナー',
        'adm-emp-col-tenant': '事務所',
        // v118.28.6
        'adm-emp-readonly-tip':
            '読み取り専用ビュー · 社員管理(有効化/無効化/パスワードリセット/削除)は事務所オーナーの担当 · サポートが必要な場合はオーナードロワーを開いてください',
        'adm-emp-col-actions': '操作',
        'adm-emp-enable': '有効化',
        'adm-emp-disable': '無効化',
        'adm-emp-reset-pw': 'パスワードリセット',
        'adm-emp-remove': '削除',
        'adm-emp-confirm-enable': '有効化',
        'adm-emp-confirm-disable': '無効化',
        'adm-emp-confirm-reset-pw': '{n} のパスワードをリセットしますか?',
        'adm-emp-confirm-remove':
            '⚠ 社員 {n} を完全に削除しますか?\nアカウントは削除されます · この操作は元に戻せません',
        'adm-emp-confirm-type-name': '社員名 "{n}" を入力して確認:',
        'adm-emp-name-mismatch': '名前が一致しません · キャンセル',
        'adm-emp-toggle-ok': '成功',
        'adm-emp-toggle-fail': '失敗',
        'adm-emp-new-pw':
            '新しい一時パスワード(コピーして社員に伝える):\n\n{n}\n\n次回ログイン時に強制的にパスワード変更されます',
        'adm-emp-reset-fail': 'リセット失敗',
        'adm-emp-remove-ok': '削除済み',
        'adm-emp-copy-and-close': 'コピー済み',
        'adm-emp-remove-fail': '削除失敗',
        'adm-emp-col-status': '状態',
        'adm-emp-col-last-login': '最終ログイン',
        'adm-emp-col-created': '作成日',
        'adm-plan-solo': 'Solo',
        'adm-plan-team': 'Team',
        'adm-filter-all': '全プラン',
        'adm-col-email': 'メール',
        'adm-col-company': '会社',
        'adm-col-plan': 'プラン',
        'adm-search-ph': 'メール / 会社',
        'adm-col-usage': '使用量',
        'adm-col-country': '国',
        'adm-col-actions': '操作',
        'adm-upgrade': '昇格',
        'adm-ban': '停止',
        // v109.4 · admin modal
        'adm-upgrade-title': 'プラン変更',
        'adm-upg-confirm': 'アップグレード確認',
        'adm-pick-plan': 'プランを選択してください',
        'adm-upgrade-ok': 'プランを変更しました',
        'adm-upgrade-fail': '変更に失敗しました',
        'adm-ban-title': 'アカウント停止',
        'adm-ban-warn': '⚠ 停止されたアカウントはログインできません · 操作は取り消し可能',
        'adm-ban-reason': '理由',
        'adm-ban-reason-ph': '例:abuse / 未払い / テスト',
        'adm-ban-confirm': '停止確認',
        'adm-ban-ok': '停止しました',
        'adm-ban-fail': '失敗',
        // v109.4 · ユーザー詳細ドロワー
        'adm-drawer-title': 'ユーザー詳細',
        'adm-drawer-loading': '読み込み中...',
        'adm-drawer-error': '読み込み失敗 · 再試行してください',
        'adm-drawer-no-company': '会社未入力',
        'adm-drawer-sec-account': 'アカウント',
        'adm-drawer-sec-contact': '連絡先',
        'adm-drawer-sec-signup': '登録情報',
        'adm-drawer-sec-usage': '利用状況',
        'adm-drawer-sec-payment': '支払い',
        'adm-drawer-plan': 'プラン',
        'adm-drawer-status': '状態',
        'adm-drawer-line': 'LINE',
        'adm-drawer-role': '役割',
        'adm-drawer-email': 'メール',
        'adm-drawer-phone': '電話',
        'adm-drawer-line-id': 'LINE ID',
        'adm-drawer-country': '国',
        'adm-drawer-signed-up': '登録日時',
        'adm-drawer-source': '登録元',
        'adm-drawer-source-direct': '直接アクセス',
        'adm-drawer-ip': '登録 IP',
        'adm-drawer-fingerprint': 'デバイス指紋',
        'adm-drawer-month-ocr': '今月の OCR',
        'adm-drawer-total-ocr': '累計 OCR',
        'adm-drawer-last-ocr': '最終 OCR',
        'adm-drawer-last-login': '最終ログイン',
        'adm-drawer-payments': '支払い回数',
        'adm-drawer-last-payment': '最終支払い',
        'adm-drawer-banned': '🚫 停止中',
        'adm-drawer-active': '✓ 正常',
        'adm-drawer-line-linked': '連携済',
        'adm-drawer-line-not-linked': '未連携',
        'adm-drawer-risky': 'リスクユーザー',
        'adm-drawer-unlimited': '無制限',
        'time-just-now': 'たった今',
        'time-mins-ago': '{n} 分前',
        'time-hours-ago': '{n} 時間前',
        'time-days-ago': '{n} 日前',
        'adm-risk-title': '⚠ リスク · 不審な活動',
        'adm-risk-events-24h': '24h リスクイベント',
        'adm-risk-same-ip': '同 IP 複数登録',
        'adm-risk-same-fp': '同指紋複数登録',
        'adm-risk-heavy-ocr': '異常 OCR(24h で 30 超)',
        'adm-risk-stat-groups': '不審グループ',
        'adm-risk-stat-events': 'リスクイベント',
        'adm-risk-expand': '展開',
        'adm-risk-collapse': '折りたたむ',
        'adm-risk-accounts': 'アカウント',
        'adm-risk-view-detail': '詳細を見る',
        'adm-risk-detail-title': '不審グループ詳細',
        'adm-risk-batch-ban': '一括停止',
        'adm-risk-confirm-batch': '{n} アカウントを停止しますか?後で解除可能。',
        'adm-risk-batch-done': '{n} アカウント停止完了',
        'adm-risk-no-targets': '停止できるアカウントがありません',
        'adm-risk-banned-tag': '停止中',
        'adm-risk-ocr-24h': 'OCR / 24h',
        'common-close': '閉じる',
        'adm-risk-clean': '✓ 異常なし',
        'adm-engine-ocr': '請求書認識',
        'adm-engine-ocr-backup': '請求書認識（予備）',
        'adm-engine-epdf': '電子PDF',
        'adm-engine-vex': '売上税報告チェック',
    });

    document.addEventListener('DOMContentLoaded', () => {
        // 显示 admin 侧栏项(super_admin 才能看见)· 复用现有 nav-admin-only 类
        // home.js 里已经有逻辑根据 user.is_super_admin 显示这些
        bindAdminUsersRoute();
        // 绑定后台筛选事件
        const planFilter = document.getElementById('adm-plan-filter');
        if (planFilter) planFilter.addEventListener('change', loadAdmUserList);
        const search = document.getElementById('adm-user-search');
        if (search) {
            let timer;
            search.addEventListener('input', () => {
                clearTimeout(timer);
                timer = setTimeout(loadAdmUserList, 300);
            });
        }
        const refr = document.getElementById('adm-refresh-pending');
        if (refr) refr.addEventListener('click', loadAdminUsersPage);
    });
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        bindAdminUsersRoute();
    }

    // v109.4 · 暴露给 routeTo 调用 · 让侧栏点击能直接触发表格加载
    window.loadAdminUsersPage = loadAdminUsersPage;

    // ============================================================
    // v118.12 · 员工 tab(新)· 仅超管查看 · 显示所有 role=member 用户
    // ============================================================
    let _admEmployeesCache = [];

    async function loadAdmEmployees() {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        try {
            const r = await fetch('/api/admin/employees', {
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.status === 403) return;
            const data = await r.json();
            _admEmployeesCache = data.employees || [];
            renderAdmEmployees(_admEmployeesCache);
        } catch (e) {
            console.error('loadAdmEmployees', e);
        }
    }

    function renderAdmEmployees(employees) {
        const wrap = document.getElementById('adm-employees-table');
        if (!wrap) return;
        // 应用搜索过滤
        const q = (document.getElementById('adm-employee-search')?.value || '')
            .toLowerCase()
            .trim();
        const filtered = q
            ? employees.filter(
                  (e) =>
                      (e.username || '').toLowerCase().includes(q) ||
                      (e.email || '').toLowerCase().includes(q) ||
                      (e.tenant_name || '').toLowerCase().includes(q) ||
                      (e.owner_username || '').toLowerCase().includes(q)
              )
            : employees;
        if (!filtered.length) {
            wrap.innerHTML = `<div class="adm-empty">${esc(tt('adm-employees-empty'))}</div>`;
            return;
        }
        // v118.28.6 · 只读化 · 砍「禁用/启用 / 重置密码 / 移除」3 个写按钮
        // 行业惯例:Xero/QuickBooks/Stripe 超管对客户内部员工 = 只读 + 跳老板抽屉
        wrap.innerHTML = `
            <div class="adm-emp-readonly-tip">${esc(tt('adm-emp-readonly-tip'))}</div>
            <div class="adm-emp-row adm-emp-row-head">
                <div>${esc(tt('adm-emp-col-name'))}</div>
                <div>${esc(tt('adm-emp-col-owner'))}</div>
                <div>${esc(tt('adm-emp-col-tenant'))}</div>
                <div>${esc(tt('adm-emp-col-status'))}</div>
                <div>${esc(tt('adm-emp-col-last-login'))}</div>
            </div>
            ${filtered
                .map((e) => {
                    const statusCls =
                        e.is_active === false ? 'adm-emp-status-disabled' : 'adm-emp-status-active';
                    const statusTxt =
                        e.is_active === false
                            ? tt('team-status-disabled')
                            : tt('team-status-active');
                    const lastLogin = e.last_login_at
                        ? new Date(e.last_login_at).toLocaleDateString()
                        : tt('team-never-login');
                    return `
                    <div class="adm-emp-row">
                        <div>
                            <div class="adm-emp-cell-strong">${esc(e.username || '?')}</div>
                            <div class="adm-emp-cell-mute">${esc(e.email || '—')}</div>
                        </div>
                        <div>
                            ${e.owner_id ? `<a class="adm-emp-owner-link" onclick="window.__adm_open_user_drawer('${esc(e.owner_id)}')">${esc(e.owner_username || e.owner_email || '—')}</a>` : '—'}
                        </div>
                        <div class="adm-emp-cell-mute">${esc(e.tenant_name || '—')}</div>
                        <div class="${statusCls}">${esc(statusTxt)}</div>
                        <div class="adm-emp-cell-mute">${esc(lastLogin)}</div>
                    </div>
                `;
                })
                .join('')}
        `;
    }

    // v118.13 · 员工 tab 操作处理 · v118.14 改用统一 modal
    window.__adm_emp_toggle = async function (employeeId, username, makeActive) {
        if (!employeeId) return;
        const verb = makeActive
            ? tt('adm-emp-confirm-enable') || '启用'
            : tt('adm-emp-confirm-disable') || '禁用';
        const ok = await showConfirm(`${verb} ${username}?`, {
            title: tt('adm-emp-col-actions') || '操作',
            danger: !makeActive,
        });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/employees/${encodeURIComponent(employeeId)}/active`, {
                method: 'PATCH',
                headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !!makeActive }),
            });
            if (r.ok) {
                showToast(tt('adm-emp-toggle-ok') || '操作成功', 'success');
                loadAdmEmployees();
            } else {
                showToast(tt('adm-emp-toggle-fail') || '操作失败', 'error');
            }
        } catch (e) {
            showToast(tt('adm-emp-toggle-fail') || '操作失败', 'error');
        }
    };

    window.__adm_emp_reset_pw = async function (employeeId, username) {
        if (!employeeId) return;
        const ok = await showConfirm(
            (tt('adm-emp-confirm-reset-pw') || '为 {n} 重置密码?').replace('{n}', username),
            { title: tt('adm-emp-reset-pw') || '重置密码' }
        );
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(
                `/api/admin/employees/${encodeURIComponent(employeeId)}/reset-password`,
                {
                    method: 'POST',
                    headers: { Authorization: 'Bearer ' + tok, 'Content-Type': 'application/json' },
                }
            );
            const data = await r.json();
            if (r.ok && data.new_password) {
                // 用统一 modal · 单按钮信息提示(替代 alert)
                await showConfirm(
                    (
                        tt('adm-emp-new-pw') ||
                        '新临时密码(请复制并告诉员工):\n\n{n}\n\n下次登录会强制员工改密。'
                    ).replace('{n}', data.new_password),
                    {
                        title: tt('adm-emp-reset-pw') || '重置密码',
                        okText: tt('adm-emp-copy-and-close') || '我已复制',
                        hideCancel: true,
                    }
                );
            } else {
                showToast(tt('adm-emp-reset-fail') || '重置失败', 'error');
            }
        } catch (e) {
            showToast(tt('adm-emp-reset-fail') || '重置失败', 'error');
        }
    };

    window.__adm_emp_remove = async function (employeeId, username) {
        if (!employeeId) return;
        // 第 1 步:danger confirm
        const ok1 = await showConfirm(
            (
                tt('adm-emp-confirm-remove') ||
                '⚠ 永久移除员工 {n}?\n该员工的账号将被删除 · 此操作不可恢复。'
            ).replace('{n}', username),
            { title: tt('adm-emp-remove') || '移除', danger: true }
        );
        if (!ok1) return;
        // 第 2 步:输入员工名再次确认 · 用 promptInput 模式
        const typed = await showConfirm(
            (tt('adm-emp-confirm-type-name') || '请输入员工名 "{n}" 以确认删除:').replace(
                '{n}',
                username
            ),
            {
                title: tt('adm-emp-remove') || '移除',
                danger: true,
                promptInput: true,
                placeholder: username,
                okText: tt('adm-emp-remove') || '移除',
            }
        );
        if (typed === null) return; // 取消
        if (typed !== username) {
            showToast(tt('adm-emp-name-mismatch') || '员工名不匹配 · 已取消', 'info');
            return;
        }
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(`/api/admin/employees/${encodeURIComponent(employeeId)}`, {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + tok },
            });
            if (r.ok) {
                showToast(tt('adm-emp-remove-ok') || '已移除', 'success');
                loadAdmEmployees();
            } else {
                showToast(tt('adm-emp-remove-fail') || '移除失败', 'error');
            }
        } catch (e) {
            showToast(tt('adm-emp-remove-fail') || '移除失败', 'error');
        }
    };

    // tab 切换
    document.addEventListener('click', (ev) => {
        const tabBtn = ev.target.closest('.adm-tab[data-adm-tab]');
        if (!tabBtn) return;
        const targetTab = tabBtn.dataset.admTab;
        document
            .querySelectorAll('.adm-tab[data-adm-tab]')
            .forEach((b) => b.classList.toggle('active', b.dataset.admTab === targetTab));
        document.querySelectorAll('[data-adm-tab-pane]').forEach((p) => {
            p.style.display = p.dataset.admTabPane === targetTab ? '' : 'none';
        });
        document.querySelectorAll('[data-adm-tab-filter]').forEach((f) => {
            f.style.display = f.dataset.admTabFilter === targetTab ? '' : 'none';
        });
        if (targetTab === 'employees') loadAdmEmployees();
        if (targetTab === 'logs') loadAdmLogs(1);
    });

    // 员工搜索 · 实时过滤
    document.addEventListener('input', (ev) => {
        if (ev.target && ev.target.id === 'adm-employee-search') {
            renderAdmEmployees(_admEmployeesCache);
        }
        if (ev.target && ev.target.id === 'adm-logs-search') {
            clearTimeout(window.__admLogsSearchTimer);
            window.__admLogsSearchTimer = setTimeout(function () {
                _admLogsState.q = (ev.target.value || '').trim();
                loadAdmLogs(1);
            }, 350);
        }
    });

    // v118.29.0 · CSV 导出 · 用 fetch 拿 token + blob 下载(避免 GET URL 暴露 token)
    async function _csvDownload(url, filename) {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        try {
            const resp = await fetch(url, { headers: { Authorization: 'Bearer ' + tok } });
            if (!resp.ok) {
                showToast(tt('adm-csv-failed') || 'Export failed', 'error');
                return;
            }
            const blob = await resp.blob();
            const a = document.createElement('a');
            const objUrl = URL.createObjectURL(blob);
            a.href = objUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(function () {
                URL.revokeObjectURL(objUrl);
                a.remove();
            }, 100);
            showToast(tt('adm-csv-ok') || 'Exported', 'success');
        } catch (e) {
            showToast(tt('adm-csv-failed') || 'Export failed', 'error');
        }
    }

    document.addEventListener('click', function (ev) {
        const btnUsers = ev.target.closest('#adm-users-csv-btn');
        if (btnUsers) {
            ev.preventDefault();
            _csvDownload('/api/admin/users.csv', 'pearnly_users.csv');
            return;
        }
        const btnLogs = ev.target.closest('#adm-logs-csv-btn');
        if (btnLogs) {
            ev.preventDefault();
            const q = encodeURIComponent(_admLogsState.q || '');
            _csvDownload('/api/admin/logs.csv?q=' + q, 'pearnly_logs.csv');
            return;
        }
        // 分页器按钮
        const pgBtn = ev.target.closest('.adm-pager-btn[data-adm-page]');
        if (pgBtn && !pgBtn.disabled) {
            const targetPage = parseInt(pgBtn.dataset.admPage, 10);
            const scope = pgBtn.dataset.admPagerScope;
            if (scope === 'logs') loadAdmLogs(targetPage);
        }
    });

    // ============================================================
    // v118.29.0 · 操作日志加载 + 渲染 + 分页
    // ============================================================
    const _admLogsState = { page: 1, per_page: 50, q: '', total: 0, rows: [] };

    async function loadAdmLogs(page) {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        const tbl = document.getElementById('adm-logs-table');
        if (tbl)
            tbl.innerHTML =
                '<div class="adm-log-empty">' +
                esc(tt('adm-logs-loading') || 'Loading...') +
                '</div>';
        _admLogsState.page = page || 1;
        try {
            const url =
                '/api/admin/logs?page=' +
                _admLogsState.page +
                '&per_page=' +
                _admLogsState.per_page +
                '&q=' +
                encodeURIComponent(_admLogsState.q || '');
            const r = await fetch(url, { headers: { Authorization: 'Bearer ' + tok } });
            if (!r.ok) throw new Error('http_' + r.status);
            const data = await r.json();
            _admLogsState.rows = data.logs || [];
            _admLogsState.total = data.total || 0;
            renderAdmLogs();
            renderAdmLogsPager();
        } catch (e) {
            if (tbl)
                tbl.innerHTML =
                    '<div class="adm-log-empty">' +
                    esc(tt('adm-logs-fail') || 'Failed to load') +
                    '</div>';
        }
    }

    function renderAdmLogs() {
        const tbl = document.getElementById('adm-logs-table');
        if (!tbl) return;
        const rows = _admLogsState.rows || [];
        if (!rows.length) {
            tbl.innerHTML =
                '<div class="adm-log-empty">' + esc(tt('adm-logs-empty') || 'No logs') + '</div>';
            return;
        }
        const head = `
            <div class="adm-log-row adm-log-head">
                <div>${esc(tt('adm-log-time') || 'Time')}</div>
                <div>${esc(tt('adm-log-actor') || 'Actor')}</div>
                <div>${esc(tt('adm-log-action') || 'Action')}</div>
                <div>${esc(tt('adm-log-target') || 'Target')}</div>
                <div>${esc(tt('adm-log-ip') || 'IP')}</div>
            </div>`;
        const body = rows
            .map(function (l) {
                let timeStr = '';
                if (l.created_at) {
                    try {
                        const d = new Date(l.created_at);
                        timeStr = d.toLocaleString();
                    } catch (e) {
                        timeStr = l.created_at;
                    }
                }
                const actor = (l.actor_username || '-') + (l.actor_is_super ? ' ⭐' : '');
                return `
                <div class="adm-log-row">
                    <div class="adm-log-time" data-label="${esc(tt('adm-log-time') || 'Time')}">${esc(timeStr)}</div>
                    <div class="adm-log-actor" data-label="${esc(tt('adm-log-actor') || 'Actor')}">${esc(actor)}</div>
                    <div data-label="${esc(tt('adm-log-action') || 'Action')}"><span class="adm-log-action">${esc(l.action || '-')}</span></div>
                    <div class="adm-log-target" data-label="${esc(tt('adm-log-target') || 'Target')}">${esc(l.target_name || l.target_type || '-')}</div>
                    <div class="adm-log-ip" data-label="${esc(tt('adm-log-ip') || 'IP')}">${esc(l.ip || '-')}</div>
                </div>`;
            })
            .join('');
        tbl.innerHTML = head + body;
    }

    function renderAdmLogsPager() {
        const wrap = document.getElementById('adm-pager-logs');
        if (!wrap) return;
        const total = _admLogsState.total || 0;
        const page = _admLogsState.page || 1;
        const per = _admLogsState.per_page || 50;
        const totalPages = Math.max(1, Math.ceil(total / per));
        const info = (tt('adm-pager-total') || 'Total {n}').replace('{n}', total);
        const pageStr = (tt('adm-pager-page') || 'Page {p} / {t}')
            .replace('{p}', page)
            .replace('{t}', totalPages);
        wrap.style.display = '';
        wrap.innerHTML = `
            <div class="adm-pager-info">${esc(info)}</div>
            <div class="adm-pager-ctrl">
                <button class="adm-pager-btn" type="button" data-adm-page="${page - 1}" data-adm-pager-scope="logs" ${page <= 1 ? 'disabled' : ''}>← ${esc(tt('adm-pager-prev') || 'Prev')}</button>
                <span class="adm-pager-page">${esc(pageStr)}</span>
                <button class="adm-pager-btn" type="button" data-adm-page="${page + 1}" data-adm-pager-scope="logs" ${page >= totalPages ? 'disabled' : ''}>${esc(tt('adm-pager-next') || 'Next')} →</button>
            </div>`;
    }

    window.loadAdmEmployees = loadAdmEmployees;
})();
