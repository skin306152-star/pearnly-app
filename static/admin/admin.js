/*
 * Pearnly · admin.js · v118.44.0.7 NAV-IA Phase 8 救援版
 * Earn 超管 admin layout SPA · 完全独立 · 不引 home.js
 * 鉴权 + 路由 + UI + 业务 API 全部自己处理
 */
(function () {
    'use strict';

    // ============ 工具函数 ============
    function _esc(s) {
        if (s == null) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function _fmt(n, d) {
        if (n == null || isNaN(n)) return '—';
        d = d == null ? 2 : d;
        return Number(n).toFixed(d).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }
    function _fmtBaht(n) {
        if (!n || n === 0) return '฿ 0';
        return '฿ ' + _fmt(n, 4);
    }
    function _setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }
    function _setHtml(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    }
    function _on(id, ev, fn) {
        const el = document.getElementById(id);
        if (el) el.addEventListener(ev, fn);
    }
    async function _adminFetch(path, opts) {
        opts = opts || {};
        const tok = localStorage.getItem('mrpilot_token');
        const headers = Object.assign({ 'Authorization': 'Bearer ' + tok }, opts.headers || {});
        if (opts.body && typeof opts.body !== 'string') {
            headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(opts.body);
        }
        const r = await fetch(path, Object.assign({}, opts, { headers: headers }));
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
    }
    function _toast(msg, kind) {
        let host = document.getElementById('admin-toast-host');
        if (!host) {
            host = document.createElement('div');
            host.id = 'admin-toast-host';
            host.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px';
            document.body.appendChild(host);
        }
        const el = document.createElement('div');
        el.style.cssText = 'background:' + (kind === 'error' ? '#dc2626' : kind === 'success' ? '#16a34a' : '#111') + ';color:#fff;padding:10px 16px;border-radius:6px;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.2);animation:fade 0.2s ease';
        el.textContent = msg;
        host.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    }

    // ============ v118.44.1 用户管理 state ============
    const _admPageState = { funnel: null, pay: null, users: [], risk: null };
    const _admEmployeesCache = { rows: [] };
    const _admLogsState = { page: 1, per_page: 50, q: '', total: 0, rows: [] };
    const _admRiskState = { collapsed: true, page: { ip: 1, fp: 1, heavy: 1 }, pageSize: 5, data: null };
    let _admCurTab = 'customers';

    // ============ i18n(读 window.ADMIN_I18N · 不依赖 home.js)============
    let _curLang = 'zh';
    function _t(key) {
        const dict = (window.ADMIN_I18N && window.ADMIN_I18N[_curLang]) || (window.ADMIN_I18N && window.ADMIN_I18N.zh) || {};
        return dict[key] || key;
    }
    function _applyI18n(lang) {
        _curLang = lang || _curLang;
        const dict = (window.ADMIN_I18N && window.ADMIN_I18N[_curLang]) || {};
        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) el.textContent = dict[key];
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
            const key = el.getAttribute('data-i18n-placeholder');
            if (dict[key]) el.setAttribute('placeholder', dict[key]);
        });
        document.documentElement.lang = _curLang;
        try { localStorage.setItem('mrpilot_lang', _curLang); } catch (_) {}
    }

    // ============ 鉴权 ============
    async function _verifySuperAdmin() {
        const token = localStorage.getItem('mrpilot_token');
        if (!token) { window.location.replace('/'); return null; }
        try {
            const r = await fetch('/api/me', { headers: { 'Authorization': 'Bearer ' + token } });
            if (!r.ok) { window.location.replace('/'); return null; }
            const u = await r.json();
            if (!u || !u.is_super_admin) { window.location.replace('/'); return null; }
            return u;
        } catch (e) {
            console.warn('[admin] auth failed', e);
            window.location.replace('/');
            return null;
        }
    }

    // ============ 路由 ============
    function _resolveRoute() {
        const p = location.pathname;
        if (p === '/admin/users' || p === '/admin/users/') return 'users';
        return 'cost';
    }

    function _switchView(route) {
        const costPage = document.getElementById('page-admin-cost');
        const usersPage = document.getElementById('page-admin-users');
        if (costPage) costPage.classList.toggle('active', route === 'cost');
        if (usersPage) usersPage.classList.toggle('active', route === 'users');
        document.querySelectorAll('.admin-layout-nav-item[data-admin-route]').forEach(function (el) {
            el.classList.toggle('active', el.dataset.adminRoute === route);
        });
        if (route === 'cost') _renderCostPage();
        if (route === 'users') _renderUsersPage();
    }

    function _bindSidebar() {
        document.querySelectorAll('.admin-layout-nav-item[data-admin-route]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                e.preventDefault();
                const route = el.dataset.adminRoute;
                const targetPath = '/admin/' + route;
                if (location.pathname !== targetPath) history.pushState({ route: route }, '', targetPath);
                _switchView(route);
            });
        });
        window.addEventListener('popstate', function () { _switchView(_resolveRoute()); });
    }

    // ============ 头像菜单 ============
    function _bindAvatar(user) {
        const btn = document.getElementById('admin-avatar-btn');
        const popup = document.getElementById('admin-avatar-popup');
        if (!btn || !popup) return;
        const name = user.display_name || user.full_name || user.name || user.username || user.email || 'Earn';
        const email = user.email || user.login || user.username || '';
        const initial = String(name).trim().charAt(0).toUpperCase() || 'E';
        _setText('admin-avatar-name', name);
        _setText('admin-avatar-email', email);
        btn.textContent = initial;
        btn.addEventListener('click', function (e) { e.stopPropagation(); popup.classList.toggle('show'); });
        document.addEventListener('click', function (e) {
            if (!popup.contains(e.target) && !btn.contains(e.target)) popup.classList.remove('show');
        });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') popup.classList.remove('show'); });
    }

    // ============ 语言切换 ============
    function _bindLang() {
        const btn = document.getElementById('admin-lang-btn');
        const popup = document.getElementById('admin-lang-popup');
        const label = document.getElementById('admin-lang-label');
        if (!btn || !popup) return;
        const labelMap = { zh: '中', th: 'ไทย' };
        function _setLabel(lang) {
            popup.querySelectorAll('button[data-admin-lang]').forEach(function (b) {
                b.classList.toggle('active', b.dataset.adminLang === lang);
            });
            if (label) label.textContent = labelMap[lang] || '中';
        }
        let cur = 'zh';
        try { cur = localStorage.getItem('mrpilot_lang') || 'zh'; } catch (_) {}
        if (!['zh', 'th'].includes(cur)) cur = 'zh'; // en/ja 暂未翻译 · 回落 zh
        _curLang = cur;
        _setLabel(cur);

        btn.addEventListener('click', function (e) { e.stopPropagation(); popup.classList.toggle('show'); });
        document.addEventListener('click', function (e) {
            if (!popup.contains(e.target) && !btn.contains(e.target)) popup.classList.remove('show');
        });
        popup.querySelectorAll('button[data-admin-lang]').forEach(function (b) {
            b.addEventListener('click', function () {
                const lang = b.dataset.adminLang;
                _applyI18n(lang);
                _setLabel(lang);
                popup.classList.remove('show');
                if (location.pathname === '/admin/users') _renderUsersPage();
                else _renderCostPage();
            });
        });
    }

    // ============ 退出登录 ============
    function _bindLogout() {
        document.querySelectorAll('[data-action="logout"]').forEach(function (el) {
            el.addEventListener('click', function (e) {
                e.preventDefault();
                try { localStorage.removeItem('mrpilot_token'); } catch (_) {}
                try { localStorage.removeItem('mrpilot_user'); } catch (_) {}
                window.location.href = '/';
            });
        });
    }

    // ============ 顶栏右侧 SLA 文字 ============
    function _renderUptime() {
        _setText('admin-uptime', 'SLA · 平台运维视图');
    }

    // ============ 成本追踪页业务 ============
    async function _renderCostPage() {
        // Google 余额 · 正确 endpoint 是 /api/admin/billing/balance
        try {
            const d = await _adminFetch('/api/admin/billing/balance');
            const bal = d && (d.real_balance_thb != null ? d.real_balance_thb : d.balance_thb);
            const upd = d && (d.updated_at || d.last_updated || d.created_at);
            _setHtml('billing-card-body',
                '<div style="font-size:28px;font-weight:700;color:#fff">฿ ' + _fmt(bal || 0, 2) + '</div>' +
                (upd ? '<div style="font-size:11px;color:rgba(255,255,255,0.7);margin-top:6px">' + _esc(String(upd).slice(0, 16).replace('T', ' ')) + '</div>' : ''));
        } catch (e) {
            _setHtml('billing-card-body', '<div style="color:rgba(255,255,255,0.85);font-size:13px">— ' + _esc(e.message) + '</div>');
        }
        // overview KPI
        try {
            const d = await _adminFetch('/api/admin/cost/overview');
            const today = d.today || {}, month = d.month || {}, total = d.total || {};
            const pageSuffix = _curLang === 'th' ? ' หน้า' : ' 页';
            const invSuffix = _curLang === 'th' ? ' ใบ' : ' 张';
            _setText('kpi-today-cost', '฿ ' + _fmt(today.cost_thb || 0, 2));
            _setText('kpi-today-sub', (today.invoices || 0) + invSuffix + ' · ' + (today.pages || 0) + pageSuffix);
            _setText('kpi-month-cost', '฿ ' + _fmt(month.cost_thb || 0, 2));
            _setText('kpi-month-sub', (month.invoices || 0) + invSuffix + ' · ' + (month.pages || 0) + pageSuffix);
            _setText('kpi-total-cost', '฿ ' + _fmt(total.cost_thb || 0, 2));
            _setText('kpi-total-sub', (total.invoices || 0) + invSuffix + ' · ' + (total.pages || 0) + pageSuffix);
            const engines = d.engines || [];
            if (!engines.length) {
                _setHtml('kpi-engines', '<span style="font-size:12px;color:#a0aec0">' + _t('adm-empty') + '</span>');
            } else {
                const sorted = engines.slice().sort((a, b) => (b.cost_thb || 0) - (a.cost_thb || 0));
                _setHtml('kpi-engines', sorted.slice(0, 3).map(e =>
                    '<div style="font-size:11px;line-height:1.5"><strong>' + _esc(e.engine || '') + '</strong> ฿' + _fmt(e.cost_thb || 0, 4) + ' · ' + (e.count || 0) + '</div>'
                ).join(''));
            }
        } catch (e) {
            console.error('cost overview', e);
        }
        // by user
        try {
            const d = await _adminFetch('/api/admin/cost/by_user');
            const users = (d && d.users) || [];
            const tbody = document.getElementById('cost-by-user-tbody');
            if (!tbody) return;
            if (!users.length) {
                tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#a0aec0">' + _t('adm-empty') + '</td></tr>';
            } else {
                tbody.innerHTML = users.map(u => {
                    const avg = u.total_invoices ? (u.total_cost_thb / u.total_invoices) : 0;
                    return '<tr>' +
                        '<td><strong>' + _esc(u.username || '—') + '</strong></td>' +
                        '<td>' + _esc(u.plan || '—') + '</td>' +
                        '<td>' + _fmtBaht(u.today_cost_thb) + '</td>' +
                        '<td>' + _fmtBaht(u.month_cost_thb) + '</td>' +
                        '<td>' + _fmtBaht(u.total_cost_thb) + '</td>' +
                        '<td>' + (u.total_pages || 0) + '</td>' +
                        '<td>' + (u.total_invoices || 0) + '</td>' +
                        '<td>' + (avg ? '฿ ' + _fmt(avg, 4) : '—') + '</td>' +
                        '<td>' + (u.last_used_at ? String(u.last_used_at).slice(0, 10) : '—') + '</td>' +
                    '</tr>';
                }).join('');
            }
        } catch (e) {
            const tbody = document.getElementById('cost-by-user-tbody');
            if (tbody) tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#dc2626">' + _t('adm-load-fail') + '</td></tr>';
        }
        // trend
        try {
            const d = await _adminFetch('/api/admin/cost/daily_trend?days=30');
            const wrap = document.getElementById('cost-trend-chart');
            if (!wrap) return;
            const points = (d && d.points) || (d && d.data) || [];
            if (!points.length) {
                wrap.innerHTML = '<div style="text-align:center;padding:30px;color:#a0aec0;font-size:13px">' + _t('adm-empty') + '</div>';
            } else {
                const max = points.reduce((m, p) => Math.max(m, p.cost_thb || 0), 0) || 1;
                wrap.innerHTML = '<div style="display:flex;align-items:flex-end;gap:3px;height:140px;padding:14px 10px">' +
                    points.map(p => {
                        const h = Math.max(2, ((p.cost_thb || 0) / max) * 100);
                        return '<div style="flex:1;background:#111;height:' + h + '%;border-radius:2px;min-width:6px" title="' + _esc(p.date || '') + ': ฿' + _fmt(p.cost_thb || 0, 2) + '"></div>';
                    }).join('') + '</div>';
            }
        } catch (e) { /* trend 失败不致命 */ }

        // v118.35.0.22 · Credits 收入 KPI + 公司清单(并行拉)
        _renderCreditsRevenue();
        _renderCreditsTenants();
    }

    // v118.35.0.22 · Credits 收入端 KPI 渲染(从 credit_transactions 拉真实扣费)
    async function _renderCreditsRevenue() {
        try {
            const d = await _adminFetch('/api/admin/credits/overview');
            const today = d.today || {}, month = d.month || {};
            const pageSuffix = _curLang === 'th' ? ' หน้า' : ' 页';
            const ocrSuffix  = _curLang === 'th' ? ' ครั้ง' : ' 次';
            _setText('kpi-rev-today', '฿ ' + _fmt(today.usage_thb || 0, 2));
            _setText('kpi-rev-today-sub', (today.ocr_count || 0) + ocrSuffix + ' · ' + (today.pages || 0) + pageSuffix);
            _setText('kpi-rev-month', '฿ ' + _fmt(month.usage_thb || 0, 2));
            _setText('kpi-rev-month-sub', (month.ocr_count || 0) + ocrSuffix + ' · ' + (month.pages || 0) + pageSuffix);
            _setText('kpi-rev-pool', '฿ ' + _fmt(d.pool_balance_thb || 0, 2));
            const overdraft = d.overdraft_tenants || 0;
            const odEl = document.getElementById('kpi-rev-overdraft');
            if (odEl) {
                odEl.textContent = String(overdraft);
                odEl.style.color = overdraft > 0 ? '#dc2626' : '';
            }
        } catch (e) {
            console.error('credits revenue', e);
        }
    }

    // v118.35.0.22 · 全公司余额清单渲染
    async function _renderCreditsTenants() {
        const tbody = document.getElementById('credits-tenants-tbody');
        if (!tbody) return;
        try {
            const d = await _adminFetch('/api/admin/credits/tenants?limit=200');
            const tenants = (d && d.tenants) || [];
            if (!tenants.length) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#a0aec0">' + _t('adm-empty') + '</td></tr>';
                return;
            }
            tbody.innerHTML = tenants.map(t => {
                const balColor = t.is_overdraft ? '#dc2626' : (t.is_low_balance ? '#d97706' : '#059669');
                const statusLabel = t.is_overdraft
                    ? '<span style="color:#dc2626;font-weight:600">' + _t('tn-status-overdraft') + '</span>'
                    : (t.is_low_balance
                        ? '<span style="color:#d97706">' + _t('tn-status-low') + '</span>'
                        : '<span style="color:#059669">' + _t('tn-status-ok') + '</span>');
                return '<tr>' +
                    '<td><strong>' + _esc(t.tenant_name || '—') + '</strong></td>' +
                    '<td style="color:' + balColor + ';font-weight:600">฿ ' + _fmt(t.balance_thb || 0, 2) + '</td>' +
                    '<td>฿ ' + _fmt(t.month_usage_thb || 0, 2) + '</td>' +
                    '<td>' + (t.pages_this_month || 0) + '</td>' +
                    '<td>฿ ' + _fmt(t.lifetime_topup_thb || 0, 2) + '</td>' +
                    '<td>' + (t.last_usage_at ? String(t.last_usage_at).slice(0, 16).replace('T', ' ') : '—') + '</td>' +
                    '<td>' + statusLabel + '</td>' +
                '</tr>';
            }).join('');
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#dc2626">' + _t('adm-load-fail') + '</td></tr>';
        }
    }

    // ============ 用户管理页业务(v118.44.1 完整版)============
    async function _renderUsersPage() {
        const tok = localStorage.getItem('mrpilot_token');
        if (!tok) return;
        const _hd = { headers: { 'Authorization': 'Bearer ' + tok } };
        fetch('/api/admin/users/funnel', _hd).then(r => r.json()).then(d => {
            _admPageState.funnel = d;
            _renderAdmKpi(d);
            _renderAdmExpiring(d.trial_expiring_soon || []);
        }).catch(_ => {});
        fetch('/api/admin/payments/pending', _hd).then(r => r.json()).then(d => {
            _admPageState.pay = d;
            _renderAdmPending((d && d.payments) || []);
        }).catch(_ => {});
        fetch('/api/admin/users?plan=all&search=&limit=100', _hd).then(r => r.json()).then(d => {
            _admPageState.users = (d && d.users) || [];
            _renderAdmUserList(_admPageState.users);
        }).catch(_ => {
            const el = document.getElementById('adm-users-table');
            if (el) el.innerHTML = '<div class="adm-empty" style="color:#ef4444">' + _t('adm-load-fail') + '</div>';
        });
        fetch('/api/admin/risk/suspicious', _hd).then(r => r.json()).then(d => {
            _admPageState.risk = d;
            _renderAdmRisk(d);
        }).catch(_ => {});
    }

    function _renderAdmKpi(f) {
        const wrap = document.getElementById('adm-kpi-grid');
        if (!wrap) return;
        const bp = (f && f.by_plan) || {};
        const cards = [
            { lbl: _t('adm-kpi-today'), val: (f && f.new_today) || 0, color: '#111111' },
            { lbl: _t('adm-kpi-week'), val: (f && f.new_week) || 0, color: '#111111' },
            { lbl: _t('adm-kpi-month'), val: (f && f.new_month) || 0, color: '#111111' },
            { lbl: _t('plan-trial'), val: bp.trial || 0, color: '#f59e0b' },
            { lbl: _t('plan-free'), val: bp.free || 0, color: '#64748b' },
            { lbl: _t('plan-pro'), val: bp.pro || 0, color: '#10b981' },
            { lbl: _t('plan-firm'), val: bp.firm || 0, color: '#8b5cf6' },
            { lbl: _t('adm-kpi-conv'), val: ((f && f.conversion_pct) || 0) + '%', color: '#dc2626' },
        ];
        wrap.style.cssText = 'display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0';
        wrap.innerHTML = cards.map(c =>
            '<div style="background:#fff;border:1px solid #e8e8e3;border-top:3px solid ' + c.color + ';border-radius:10px;padding:14px 16px">' +
                '<div style="font-size:22px;font-weight:700;color:' + c.color + '">' + _esc(c.val) + '</div>' +
                '<div style="font-size:11px;color:#6b7280;margin-top:3px">' + _esc(c.lbl) + '</div>' +
            '</div>'
        ).join('');
    }

    function _renderAdmPending(rows) {
        const wrap = document.getElementById('adm-pending-list');
        if (!wrap) return;
        const pending = rows.filter(r => r.status === 'pending');
        if (!pending.length) {
            wrap.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-pending-empty')) + '</div>';
            return;
        }
        wrap.innerHTML = pending.map(r =>
            '<div style="background:#fff;border:1px solid #e8e8e3;border-radius:6px;padding:10px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;gap:12px">' +
                '<div style="flex:1;min-width:0"><strong>' + _esc(r.user_email || '?') + '</strong> · ' + _esc(r.company_name || '') +
                ' <span style="background:#fef3c7;color:#92400e;padding:1px 7px;border-radius:4px;font-size:11px;margin-left:4px">' + _esc((r.target_plan || '').toUpperCase()) + '</span>' +
                '<div style="color:#6b7280;font-size:12px;margin-top:3px">฿' + _esc(r.amount_thb) + ' · ' + _esc(r.payer_name || '—') + ' · ' + _esc(r.payer_note || '') + '</div></div>' +
                '<div style="display:flex;gap:6px;flex-shrink:0">' +
                    (r.screenshot_path ? '<button class="btn btn-ghost btn-sm" onclick="window.__admViewSlip(' + r.id + ')">' + _esc(_t('adm-view-slip')) + '</button>' : '') +
                    '<button class="btn btn-primary btn-sm" onclick="window.__admApprovePay(' + r.id + ')">' + _esc(_t('adm-approve')) + '</button>' +
                    '<button class="btn btn-danger btn-sm" onclick="window.__admRejectPay(' + r.id + ')">' + _esc(_t('adm-reject')) + '</button>' +
                '</div>' +
            '</div>'
        ).join('');
    }

    function _renderAdmExpiring(rows) {
        const wrap = document.getElementById('adm-expiring-list');
        if (!wrap) return;
        if (!rows.length) {
            wrap.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-expiring-empty')) + '</div>';
            return;
        }
        wrap.innerHTML = rows.map(r =>
            '<div style="background:#fff;border:1px solid #e8e8e3;border-radius:6px;padding:8px 12px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">' +
                '<div><strong>' + _esc(r.email) + '</strong> · ' + _esc(r.company_name || '') +
                ' <span style="background:#fef3c7;color:#92400e;padding:1px 7px;border-radius:4px;font-size:11px;margin-left:4px">' + r.hours_left + 'h</span></div>' +
                '<button class="btn btn-primary btn-sm" onclick="window.__admQuickUpgrade(\'' + _esc(r.id) + '\',\'' + _esc(r.email) + '\')">' + _esc(_t('adm-quick-upgrade')) + '</button>' +
            '</div>'
        ).join('');
    }

    function _planLabel(plan) {
        const map = {
            'trial': 'Trial', 'free': 'Trial',
            'solo': 'Pearnly Solo', 'pro': 'Pearnly Solo', 'plus': 'Pearnly Solo',
            'team': 'Pearnly Team', 'firm': 'Pearnly Firm', 'enterprise': 'Enterprise',
            'monthly': 'Monthly', 'yearly': 'Yearly', 'lifetime': 'Lifetime',
        };
        return map[plan] || (plan ? plan.charAt(0).toUpperCase() + plan.slice(1) : '—');
    }

    function _renderAdmUserList(users) {
        const wrap = document.getElementById('adm-users-table');
        if (!wrap) return;
        const sq = (document.getElementById('adm-user-search')?.value || '').toLowerCase().trim();
        const pf = document.getElementById('adm-plan-filter')?.value || 'all';
        let filtered = users || [];
        if (pf !== 'all') filtered = filtered.filter(u => u.plan === pf);
        if (sq) filtered = filtered.filter(u =>
            (u.email || '').toLowerCase().includes(sq) ||
            (u.username || '').toLowerCase().includes(sq) ||
            (u.company_name || '').toLowerCase().includes(sq)
        );
        if (!filtered.length) {
            wrap.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-users-empty')) + '</div>';
            return;
        }
        wrap.innerHTML =
            '<div class="adm-table-head">' +
                '<div>' + _esc(_t('adm-col-email')) + '</div>' +
                '<div>' + _esc(_t('adm-col-company')) + '</div>' +
                '<div>' + _esc(_t('adm-col-plan')) + '</div>' +
                '<div>' + _esc(_t('adm-col-usage')) + '</div>' +
                '<div>' + _esc(_t('adm-col-country')) + '</div>' +
                '<div>' + _esc(_t('adm-col-actions')) + '</div>' +
            '</div>' +
            filtered.map(u => {
                const isAdmin = u.is_super_admin || u.tenant_type === 'admin';
                const adminBadge = isAdmin ? ' <span style="background:#fef3c7;color:#92400e;padding:1px 6px;border-radius:3px;font-size:10px">' + _esc(_t('admin-type-super')) + '</span>' : '';
                const lineBadge = u.line_id ? ' · LINE' : '';
                const actions = isAdmin
                    ? '<div class="adm-row-actions" title="' + _esc(_t('admin-self-disabled-tip')) + '">' +
                        '<button class="btn btn-ghost btn-sm" disabled>' + _esc(_t('adm-upgrade')) + '</button>' +
                        '<button class="btn btn-ghost btn-sm" disabled>' + _esc(_t('adm-ban')) + '</button>' +
                    '</div>'
                    : '<div class="adm-row-actions">' +
                        '<button class="btn btn-ghost btn-sm" onclick="window.__admQuickUpgrade(\'' + _esc(u.id) + '\',\'' + _esc(u.email || '') + '\')">' + _esc(_t('adm-upgrade')) + '</button>' +
                        (u.is_active === false
                            ? '<button class="btn btn-ghost btn-sm" onclick="window.__admUnbanUser(\'' + _esc(u.id) + '\')">' + _esc(_t('adm-drawer-btn-unban')) + '</button>'
                            : '<button class="btn btn-ghost btn-sm" onclick="window.__admBanUser(\'' + _esc(u.id) + '\',\'' + _esc(u.email || '') + '\')">' + _esc(_t('adm-ban')) + '</button>'
                        ) +
                        '<button class="btn btn-ghost btn-sm adm-emp-btn-danger" onclick="window.__admCascadeDelete(\'' + _esc(u.id) + '\',\'' + _esc(u.username || u.email || '') + '\')">' + _esc(_t('adm-cascade-del')) + '</button>' +
                    '</div>';
                return '<div class="adm-table-row">' +
                    '<div>' +
                        '<div class="adm-cell-strong adm-cell-clickable" onclick="window.__admOpenUserDrawer(\'' + _esc(u.id) + '\')">' + _esc(u.email || u.username) + '</div>' +
                        '<div class="adm-cell-mute">' + (u.created_at ? new Date(u.created_at).toLocaleDateString() : '—') + adminBadge + '</div>' +
                    '</div>' +
                    '<div>' + _esc(u.company_name || '—') + '</div>' +
                    '<div>' +
                        '<span class="adm-plan-badge adm-plan-' + _esc(u.plan || 'trial') + '">' + _esc(_planLabel(u.plan)) + '</span>' +
                        (u.days_left != null ? '<div class="adm-cell-mute">' + u.days_left + 'd</div>' : '') +
                    '</div>' +
                    '<div>' + (u.ocr_used_month || 0) + '</div>' +
                    '<div>' + _esc(u.country || '—') + lineBadge + '</div>' +
                    actions +
                '</div>';
            }).join('');
    }

    function _renderAdmRisk(r) {
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
        if (!totalSignals && !totalEvents) {
            wrap.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-risk-clean')) + '</div>';
            return;
        }
        const collapsed = _admRiskState.collapsed;
        const summary =
            '<div class="adm-risk-summary">' +
                '<div class="adm-risk-summary-stats">' +
                    (totalSignals > 0 ? '<span class="adm-risk-stat-pill warn">' + totalSignals + ' ' + _esc(_t('adm-risk-stat-groups')) + '</span>' : '') +
                    (totalEvents > 0 ? '<span class="adm-risk-stat-pill info">' + totalEvents + ' ' + _esc(_t('adm-risk-stat-events')) + '</span>' : '') +
                '</div>' +
                '<button class="adm-risk-toggle-btn" onclick="window.__admRiskToggle()">' +
                    _esc(collapsed ? _t('adm-risk-expand') : _t('adm-risk-collapse')) +
                    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate(' + (collapsed ? '0' : '180') + 'deg); transition: transform 0.2s">' +
                        '<polyline points="6 9 12 15 18 9"></polyline>' +
                    '</svg>' +
                '</button>' +
            '</div>';
        if (collapsed) { wrap.innerHTML = summary; return; }
        const renderGroup = (title, items, kind, renderRow) => {
            if (!items.length) return '';
            const ps = _admRiskState.pageSize;
            const cur = _admRiskState.page[kind] || 1;
            const totalPages = Math.max(1, Math.ceil(items.length / ps));
            const safe = Math.min(cur, totalPages);
            const slice = items.slice((safe - 1) * ps, safe * ps);
            const pager = totalPages > 1 ?
                '<div class="adm-risk-pager">' +
                    '<button class="adm-risk-pager-btn" ' + (safe <= 1 ? 'disabled' : '') + ' onclick="window.__admRiskPage(\'' + kind + '\',' + (safe - 1) + ')">‹</button>' +
                    '<span class="adm-risk-pager-info">' + safe + ' / ' + totalPages + '</span>' +
                    '<button class="adm-risk-pager-btn" ' + (safe >= totalPages ? 'disabled' : '') + ' onclick="window.__admRiskPage(\'' + kind + '\',' + (safe + 1) + ')">›</button>' +
                '</div>' : '';
            return '<div class="adm-risk-block">' +
                '<div class="adm-risk-title">' + _esc(title) + ' <span class="adm-risk-count">(' + items.length + ')</span></div>' +
                '<div class="adm-risk-rows">' + slice.map(renderRow).join('') + '</div>' +
                pager +
            '</div>';
        };
        const ipRows = renderGroup(_t('adm-risk-same-ip'), sip, 'ip', x =>
            '<div class="adm-risk-row">' +
                '<div class="adm-risk-row-main">' +
                    '<div><strong>IP</strong> <code>' + _esc(x.ip) + '</code> · ' + x.count + ' ' + _esc(_t('adm-risk-accounts')) + '</div>' +
                    '<div class="adm-risk-row-sub">' + (x.accounts || []).slice(0, 3).map(a => _esc(a.email)).join(' · ') + ((x.accounts || []).length > 3 ? ' …' : '') + '</div>' +
                '</div>' +
                '<button class="adm-risk-detail-btn" onclick=\'window.__admRiskDetail("ip", ' + JSON.stringify(JSON.stringify(x)) + ')\'>' + _esc(_t('adm-risk-view-detail')) + '</button>' +
            '</div>');
        const fpRows = renderGroup(_t('adm-risk-same-fp'), sfp, 'fp', x =>
            '<div class="adm-risk-row">' +
                '<div class="adm-risk-row-main">' +
                    '<div><strong>FP</strong> <code>' + _esc(x.fingerprint_short || '') + '</code> · ' + x.count + ' ' + _esc(_t('adm-risk-accounts')) + '</div>' +
                    '<div class="adm-risk-row-sub">' + (x.accounts || []).slice(0, 3).map(a => _esc(a.email)).join(' · ') + ((x.accounts || []).length > 3 ? ' …' : '') + '</div>' +
                '</div>' +
                '<button class="adm-risk-detail-btn" onclick=\'window.__admRiskDetail("fp", ' + JSON.stringify(JSON.stringify(x)) + ')\'>' + _esc(_t('adm-risk-view-detail')) + '</button>' +
            '</div>');
        const heavyRows = renderGroup(_t('adm-risk-heavy-ocr'), heavy, 'heavy', x =>
            '<div class="adm-risk-row">' +
                '<div class="adm-risk-row-main">' +
                    '<div><strong>' + _esc(x.email) + '</strong> ' + (x.is_banned ? '<span class="adm-pill-banned">' + _esc(_t('adm-risk-banned-tag')) + '</span>' : '') + '</div>' +
                    '<div class="adm-risk-row-sub">' + _esc(x.plan || '') + ' · ' + x.ocr_today + ' ' + _esc(_t('adm-risk-ocr-24h')) + '</div>' +
                '</div>' +
                (x.is_banned
                    ? '<button class="adm-risk-detail-btn" onclick="window.__admUnbanUser(\'' + _esc(x.user_id) + '\')">' + _esc(_t('adm-drawer-btn-unban')) + '</button>'
                    : '<button class="adm-risk-detail-btn danger" onclick="window.__admBanUser(\'' + _esc(x.user_id) + '\',\'' + _esc(x.email) + '\')">' + _esc(_t('adm-drawer-btn-ban')) + '</button>') +
            '</div>');
        const evBlock = ev.length ?
            '<div class="adm-risk-block">' +
                '<div class="adm-risk-title">' + _esc(_t('adm-risk-events-24h')) + '</div>' +
                '<div class="adm-risk-tags">' +
                    ev.map(e => '<span class="adm-tag ' + (e.event === 'disposable_email' || e.event === 'rate_limited_try_later' ? 'adm-tag-warn' : '') + '">' + _esc(e.event) + ': ' + e.count + '</span>').join('') +
                '</div>' +
            '</div>' : '';
        wrap.innerHTML = summary + ipRows + fpRows + heavyRows + evBlock;
    }

    window.__admRiskToggle = function() {
        _admRiskState.collapsed = !_admRiskState.collapsed;
        _renderAdmRisk();
    };
    window.__admRiskPage = function(kind, page) {
        _admRiskState.page[kind] = page;
        _renderAdmRisk();
    };

    window.__admRiskDetail = function(kind, groupJson) {
        let group;
        try { group = JSON.parse(groupJson); } catch (e) { return; }
        const accounts = group.accounts || [];
        const headerKey = kind === 'ip' ? ('IP: ' + group.ip) : ('Fingerprint: ' + (group.fingerprint_short || ''));
        const old = document.getElementById('adm-risk-detail-modal');
        if (old) old.remove();
        const modal = document.createElement('div');
        modal.id = 'adm-risk-detail-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML =
            '<div class="modal modal-md">' +
                '<div class="modal-head">' +
                    '<div class="modal-title">' + _esc(_t('adm-risk-detail-title')) + '</div>' +
                    '<button class="modal-close" onclick="document.getElementById(\'adm-risk-detail-modal\').remove()">×</button>' +
                '</div>' +
                '<div class="modal-body">' +
                    '<div class="adm-risk-detail-meta">' + _esc(headerKey) + ' · ' + accounts.length + ' ' + _esc(_t('adm-risk-accounts')) + '</div>' +
                    '<div class="adm-risk-detail-list" id="adm-risk-detail-list">' +
                        accounts.map(a =>
                            '<div class="adm-risk-detail-row" data-uid="' + _esc(a.user_id) + '">' +
                                '<div class="adm-risk-detail-main">' +
                                    '<div><strong>' + _esc(a.email) + '</strong>' +
                                        (a.is_banned ? ' <span class="adm-pill-banned">' + _esc(_t('adm-risk-banned-tag')) + '</span>' : '') +
                                    '</div>' +
                                    '<div class="adm-risk-detail-sub">' + _esc(a.plan || '') + ' · ' + _esc((a.created_at || '').slice(0, 10)) + '</div>' +
                                '</div>' +
                                '<div class="adm-risk-detail-actions">' +
                                    (a.is_banned
                                        ? '<button class="adm-risk-detail-btn" onclick="window.__admRiskModalUnban(\'' + _esc(a.user_id) + '\')">' + _esc(_t('adm-drawer-btn-unban')) + '</button>'
                                        : '<button class="adm-risk-detail-btn danger" onclick="window.__admRiskModalBan(\'' + _esc(a.user_id) + '\',\'' + _esc(a.email) + '\')">' + _esc(_t('adm-drawer-btn-ban')) + '</button>') +
                                '</div>' +
                            '</div>'
                        ).join('') +
                    '</div>' +
                '</div>' +
                '<div class="modal-foot">' +
                    '<button class="btn-ghost" onclick="document.getElementById(\'adm-risk-detail-modal\').remove()">' + _esc(_t('common-close')) + '</button>' +
                    '<button class="btn-danger" onclick=\'window.__admRiskBatchBan(' + JSON.stringify(JSON.stringify(accounts)) + ')\'>' +
                        _esc(_t('adm-risk-batch-ban')) + ' (' + accounts.filter(a => !a.is_banned).length + ')' +
                    '</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(modal);
    };

    window.__admRiskModalBan = async function(uid, email) {
        const ok = await _admConfirm(_t('adm-confirm-ban').replace('{e}', email), { danger: true, title: _t('adm-ban-title') });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/users/' + uid + '/ban', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'risk_review' }),
            });
            if (r.ok) {
                _toast(_t('adm-banned'), 'success');
                const m = document.getElementById('adm-risk-detail-modal');
                if (m) m.remove();
                _renderUsersPage();
            } else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };
    window.__admRiskModalUnban = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/users/' + uid + '/unban', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) {
                _toast(_t('adm-unbanned'), 'success');
                const m = document.getElementById('adm-risk-detail-modal');
                if (m) m.remove();
                _renderUsersPage();
            } else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };

    window.__admRiskBatchBan = async function(accountsJson) {
        let accounts;
        try { accounts = JSON.parse(accountsJson); } catch (e) { return; }
        const targets = accounts.filter(a => !a.is_banned).map(a => a.user_id);
        if (!targets.length) { _toast(_t('adm-risk-no-targets'), 'info'); return; }
        const ok = await _admConfirm(_t('adm-risk-confirm-batch').replace('{n}', targets.length), { danger: true, title: _t('adm-risk-batch-ban') });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/risk/batch-ban', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_ids: targets, reason: 'risk_batch_ban' }),
            });
            const j = await r.json().catch(() => ({}));
            if (r.ok && j.ok) {
                _toast(_t('adm-risk-batch-done').replace('{n}', j.banned || 0), 'success');
                const m = document.getElementById('adm-risk-detail-modal');
                if (m) m.remove();
                _renderUsersPage();
            } else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };

    // ============ v118.35.0.17 通用输入 modal · 替代 window.prompt ============
    function _admPrompt(message, opts) {
        opts = opts || {};
        return new Promise(resolve => {
            const old = document.getElementById('adm-prompt-modal');
            if (old) old.remove();
            const ov = document.createElement('div');
            ov.id = 'adm-prompt-modal';
            ov.className = 'cpw-forgot-overlay';
            ov.innerHTML =
                '<div class="cpw-forgot-modal" style="max-width:420px">' +
                    '<div class="cpw-forgot-head"><div class="cpw-forgot-title">' + _esc(opts.title || message) + '</div></div>' +
                    '<div class="cpw-forgot-body">' +
                        '<input type="' + (opts.type || 'text') + '" id="adm-pr-input" ' +
                            'placeholder="' + _esc(opts.placeholder || '') + '" ' +
                            'value="' + _esc(opts.defaultValue || '') + '" ' +
                            'style="width:100%;padding:8px;border-radius:4px;border:1px solid #ddd;box-sizing:border-box">' +
                    '</div>' +
                    '<div class="cpw-forgot-foot">' +
                        '<button class="btn btn-ghost" id="adm-pr-cancel">' + _esc(_t('confirm-cancel')) + '</button>' +
                        '<button class="btn btn-primary" id="adm-pr-ok">' + _esc(opts.okText || _t('adm-upg-confirm')) + '</button>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(ov);
            const inp = ov.querySelector('#adm-pr-input');
            setTimeout(() => { if (inp) inp.focus(); }, 50);
            const cleanup = () => ov.remove();
            const finish = (val) => { cleanup(); resolve(val); };
            ov.querySelector('#adm-pr-ok').addEventListener('click', () => finish(inp ? inp.value : null));
            ov.querySelector('#adm-pr-cancel').addEventListener('click', () => finish(null));
            ov.addEventListener('click', e => { if (e.target === ov) finish(null); });
            if (inp) {
                inp.addEventListener('keydown', e => {
                    if (e.key === 'Enter') { e.preventDefault(); finish(inp.value); }
                    else if (e.key === 'Escape') { e.preventDefault(); finish(null); }
                });
            }
        });
    }

    // ============ v118.44.1 通用确认 modal ============
    function _admConfirm(message, opts) {
        opts = opts || {};
        return new Promise(resolve => {
            const old = document.getElementById('adm-confirm-modal');
            if (old) old.remove();
            const ov = document.createElement('div');
            ov.id = 'adm-confirm-modal';
            ov.className = 'cpw-forgot-overlay';
            ov.innerHTML =
                '<div class="cpw-forgot-modal" style="max-width:420px">' +
                    '<div class="cpw-forgot-head"><div class="cpw-forgot-title">' + _esc(opts.title || _t('common-close')) + '</div></div>' +
                    '<div class="cpw-forgot-body"><div style="white-space:pre-line">' + _esc(message) + '</div></div>' +
                    '<div class="cpw-forgot-foot">' +
                        (opts.hideCancel ? '' : '<button class="btn btn-ghost" id="adm-cf-cancel">' + _esc(_t('confirm-cancel')) + '</button>') +
                        '<button class="btn ' + (opts.danger ? 'btn-danger' : 'btn-primary') + '" id="adm-cf-ok">' + _esc(opts.okText || _t('adm-upg-confirm')) + '</button>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(ov);
            const cleanup = () => ov.remove();
            ov.querySelector('#adm-cf-ok').addEventListener('click', () => { cleanup(); resolve(true); });
            const cb = ov.querySelector('#adm-cf-cancel');
            if (cb) cb.addEventListener('click', () => { cleanup(); resolve(false); });
            ov.addEventListener('click', e => { if (e.target === ov) { cleanup(); resolve(false); } });
        });
    }

    // ============ v118.44.1 用户详情抽屉 ============
    window.__admOpenUserDrawer = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        const old = document.getElementById('adm-drawer-overlay');
        if (old) old.remove();
        const ov = document.createElement('div');
        ov.className = 'adm-drawer-overlay';
        ov.id = 'adm-drawer-overlay';
        ov.dataset.uid = uid;
        ov.innerHTML =
            '<div class="adm-drawer">' +
                '<div class="adm-drawer-head">' +
                    '<div class="adm-drawer-title">' + _esc(_t('adm-drawer-title')) + '</div>' +
                    '<button class="adm-drawer-close" id="adm-drawer-close" aria-label="close">' +
                        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg>' +
                    '</button>' +
                '</div>' +
                '<div class="adm-drawer-body" id="adm-drawer-body">' +
                    '<div class="adm-drawer-loading">' + _esc(_t('adm-drawer-loading')) + '</div>' +
                '</div>' +
            '</div>';
        document.body.appendChild(ov);
        requestAnimationFrame(() => ov.classList.add('show'));
        const close = () => { ov.classList.remove('show'); setTimeout(() => ov.remove(), 250); };
        ov.querySelector('#adm-drawer-close').addEventListener('click', close);
        ov.addEventListener('click', e => { if (e.target === ov) close(); });
        function escH(e) {
            if (e.key === 'Escape' && document.getElementById('adm-drawer-overlay')) {
                close();
                document.removeEventListener('keydown', escH);
            }
        }
        document.addEventListener('keydown', escH);
        try {
            const r = await fetch('/api/admin/users/' + uid, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) {
                document.getElementById('adm-drawer-body').innerHTML = '<div class="adm-drawer-error">' + _esc(_t('adm-drawer-error')) + '</div>';
                return;
            }
            const u = await r.json();
            _renderAdmUserDrawer(u);
        } catch (e) {
            document.getElementById('adm-drawer-body').innerHTML = '<div class="adm-drawer-error">' + _esc(_t('adm-drawer-error')) + '</div>';
        }
    };

    function _renderAdmUserDrawer(u) {
        const body = document.getElementById('adm-drawer-body');
        if (!body) return;
        const fmt = (s) => {
            if (!s) return '—';
            try { return new Date(s).toLocaleString(); } catch (e) { return s; }
        };
        const lineStatus = u.line_user_id
            ? '<span class="adm-drawer-pill adm-pill-success">✓ ' + _esc(_t('adm-drawer-line-linked')) + '</span>'
            : '<span class="adm-drawer-pill adm-pill-warn">○ ' + _esc(_t('adm-drawer-line-not-linked')) + '</span>';
        const riskBadge = u.has_risk_signal
            ? '<span class="adm-drawer-pill adm-pill-danger">⚠ ' + _esc(_t('adm-drawer-risky')) + '</span>'
            : '';
        const sec = (title, grid, extra) =>
            '<div class="adm-drawer-section"><div class="adm-drawer-section-title">' + _esc(title) + (extra ? ' ' + extra : '') + '</div><div class="adm-drawer-grid">' + grid + '</div></div>';
        const row = (lbl, val) =>
            '<div class="adm-drawer-label">' + _esc(lbl) + '</div><div class="adm-drawer-value">' + val + '</div>';
        body.innerHTML =
            '<div class="adm-drawer-header-row">' +
                '<div class="adm-drawer-avatar">' + _esc((u.email || u.username || '?').charAt(0).toUpperCase()) + '</div>' +
                '<div class="adm-drawer-header-text">' +
                    '<div class="adm-drawer-name">' + _esc(u.email || u.username || '') + '</div>' +
                    '<div class="adm-drawer-sub">' + _esc(u.company_name || _t('adm-drawer-no-company')) + '</div>' +
                '</div>' +
            '</div>' +
            sec(_t('adm-drawer-sec-account'),
                row(_t('adm-drawer-plan'), '<span class="adm-plan-badge adm-plan-' + _esc(u.plan || 'trial') + '">' + _esc(_planLabel(u.plan)) + '</span>' + (u.days_left != null ? ' · ' + u.days_left + 'd' : '')) +
                row(_t('adm-drawer-status'), u.is_active === false ? _esc(_t('adm-drawer-banned')) : _esc(_t('adm-drawer-active'))) +
                row(_t('adm-drawer-line'), lineStatus) +
                row(_t('adm-drawer-role'), u.is_super_admin ? '⭐ Super Admin' : _esc(u.role || 'owner'))
            ) +
            sec(_t('adm-drawer-sec-contact'),
                row(_t('adm-drawer-email'), _esc(u.email || '—')) +
                row(_t('adm-drawer-phone'), _esc(u.phone || '—')) +
                row(_t('adm-drawer-line-id'), _esc(u.line_id || '—')) +
                row(_t('adm-drawer-country'), _esc(u.country || '—'))
            ) +
            sec(_t('adm-drawer-sec-signup'),
                row(_t('adm-drawer-signed-up'), _esc(fmt(u.created_at))) +
                row(_t('adm-drawer-source'), _esc(u.signup_source || _t('adm-drawer-source-direct'))) +
                row(_t('adm-drawer-ip'), '<span class="adm-drawer-mono">' + _esc(u.signup_ip || '—') + '</span>') +
                row(_t('adm-drawer-fingerprint'), '<span class="adm-drawer-mono">' + _esc((u.signup_fingerprint || '—').slice(0, 16)) + (u.signup_fingerprint ? '...' : '') + '</span>'),
                riskBadge
            ) +
            sec(_t('adm-drawer-sec-usage'),
                row(_t('adm-drawer-month-ocr'), (u.ocr_used_month || 0) + ' / ' + (u.ocr_quota || _t('adm-drawer-unlimited'))) +
                row(_t('adm-drawer-total-ocr'), u.ocr_total || 0) +
                row(_t('adm-drawer-last-ocr'), _esc(fmt(u.last_ocr_at))) +
                row(_t('adm-drawer-last-login'), _esc(fmt(u.last_login_at)))
            ) +
            sec(_t('adm-drawer-sec-payment'),
                row(_t('adm-drawer-payments'), u.payment_count || 0) +
                row(_t('adm-drawer-last-payment'), _esc(fmt(u.last_payment_at)))
            ) +
            (!u.is_super_admin ?
                '<div class="adm-drawer-section adm-drawer-actions-section">' +
                    '<div class="adm-drawer-section-title">' + _esc(_t('adm-drawer-sec-actions')) + '</div>' +
                    '<div class="adm-drawer-actions-grid">' +
                        '<button class="btn btn-primary" onclick="window.__admQuickUpgrade(\'' + _esc(u.id) + '\',\'' + _esc(u.email || '') + '\')">' + _esc(_t('adm-drawer-btn-upgrade')) + '</button>' +
                        (u.is_active === false
                            ? '<button class="btn btn-ghost" onclick="window.__admUnbanUser(\'' + _esc(u.id) + '\')">' + _esc(_t('adm-drawer-btn-unban')) + '</button>'
                            : '<button class="btn btn-danger" onclick="window.__admBanUser(\'' + _esc(u.id) + '\',\'' + _esc(u.email || '') + '\')">' + _esc(_t('adm-drawer-btn-ban')) + '</button>'
                        ) +
                        '<button class="btn btn-danger" onclick="window.__admCascadeDelete(\'' + _esc(u.id) + '\',\'' + _esc(u.username || u.email || '') + '\')">' + _esc(_t('adm-cascade-del')) + '</button>' +
                    '</div>' +
                '</div>'
                : ''
            );
    }

    // ============ v118.44.1 升级 modal ============
    window.__admQuickUpgrade = function(uid, email) {
        const old = document.getElementById('adm-upgrade-overlay');
        if (old) old.remove();
        const plans = [
            { id: 'trial', label: _t('upg-plan-trial'), desc: _t('upg-plan-trial-desc') },
            { id: 'monthly', label: _t('upg-plan-monthly'), desc: _t('upg-plan-monthly-desc') },
            { id: 'yearly', label: _t('upg-plan-yearly'), desc: _t('upg-plan-yearly-desc') },
            { id: 'lifetime', label: _t('upg-plan-lifetime'), desc: _t('upg-plan-lifetime-desc') },
        ];
        const ov = document.createElement('div');
        ov.id = 'adm-upgrade-overlay';
        ov.className = 'cpw-forgot-overlay';
        ov.innerHTML =
            '<div class="cpw-forgot-modal" style="max-width:480px">' +
                '<div class="cpw-forgot-head"><div class="cpw-forgot-title">' + _esc(_t('adm-upgrade-title')) + '</div>' +
                    '<button class="cpw-forgot-close" id="adm-upg-close"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg></button>' +
                '</div>' +
                '<div class="cpw-forgot-body">' +
                    '<p class="cpw-forgot-desc">' + _esc(email) + '</p>' +
                    '<div class="adm-plan-options">' +
                        plans.map(p =>
                            '<label class="adm-plan-option">' +
                                '<input type="radio" name="adm-target-plan" value="' + p.id + '">' +
                                '<div class="adm-plan-option-body">' +
                                    '<div class="adm-plan-option-label">' + _esc(p.label) + '</div>' +
                                    '<div class="adm-plan-option-desc">' + _esc(p.desc) + '</div>' +
                                '</div>' +
                            '</label>'
                        ).join('') +
                    '</div>' +
                '</div>' +
                '<div class="cpw-forgot-foot">' +
                    '<button class="btn btn-ghost" id="adm-upg-cancel">' + _esc(_t('cpw-forgot-cancel')) + '</button>' +
                    '<button class="btn btn-primary" id="adm-upg-confirm">' + _esc(_t('adm-upg-confirm')) + '</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(ov);
        const close = () => ov.remove();
        ov.querySelector('#adm-upg-close').addEventListener('click', close);
        ov.querySelector('#adm-upg-cancel').addEventListener('click', close);
        ov.addEventListener('click', e => { if (e.target === ov) close(); });
        ov.querySelector('#adm-upg-confirm').addEventListener('click', async () => {
            const sel = ov.querySelector('input[name="adm-target-plan"]:checked');
            if (!sel) { _toast(_t('adm-pick-plan'), 'error'); return; }
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch('/api/admin/users/upgrade', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: uid, target_plan: sel.value, note: 'manual_admin' }),
                });
                if (r.ok) { _toast(_t('adm-upgrade-ok'), 'success'); close(); _renderUsersPage(); }
                else { const d = await r.json().catch(() => ({})); _toast(d.detail || _t('adm-upgrade-fail'), 'error'); }
            } catch (e) { _toast(_t('adm-upgrade-fail'), 'error'); }
        });
    };

    // ============ v118.44.1 封停 modal ============
    window.__admBanUser = function(uid, email) {
        const old = document.getElementById('adm-ban-overlay');
        if (old) old.remove();
        const ov = document.createElement('div');
        ov.id = 'adm-ban-overlay';
        ov.className = 'cpw-forgot-overlay';
        ov.innerHTML =
            '<div class="cpw-forgot-modal" style="max-width:420px">' +
                '<div class="cpw-forgot-head"><div class="cpw-forgot-title">' + _esc(_t('adm-ban-title')) + '</div>' +
                    '<button class="cpw-forgot-close" id="adm-ban-close"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg></button>' +
                '</div>' +
                '<div class="cpw-forgot-body">' +
                    '<p class="cpw-forgot-desc">' + _esc(email) + '</p>' +
                    '<p class="cpw-forgot-tip">' + _esc(_t('adm-ban-warn')) + '</p>' +
                    '<div style="margin-top:12px">' +
                        '<label style="display:block;font-size:13px;color:#475569;margin-bottom:6px">' + _esc(_t('adm-ban-reason')) + '</label>' +
                        '<input type="text" id="adm-ban-reason-input" class="cpw-input" autocomplete="off" placeholder="' + _esc(_t('adm-ban-reason-ph')) + '" value="abuse">' +
                    '</div>' +
                '</div>' +
                '<div class="cpw-forgot-foot">' +
                    '<button class="btn btn-ghost" id="adm-ban-cancel">' + _esc(_t('cpw-forgot-cancel')) + '</button>' +
                    '<button class="btn btn-danger" id="adm-ban-confirm">' + _esc(_t('adm-ban-confirm')) + '</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(ov);
        const close = () => ov.remove();
        ov.querySelector('#adm-ban-close').addEventListener('click', close);
        ov.querySelector('#adm-ban-cancel').addEventListener('click', close);
        ov.addEventListener('click', e => { if (e.target === ov) close(); });
        ov.querySelector('#adm-ban-confirm').addEventListener('click', async () => {
            const reason = (ov.querySelector('#adm-ban-reason-input').value || '').trim() || 'abuse';
            const tok = localStorage.getItem('mrpilot_token');
            try {
                const r = await fetch('/api/admin/users/' + uid + '/ban?reason=' + encodeURIComponent(reason), {
                    method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
                });
                if (r.ok) {
                    _toast(_t('adm-ban-ok'), 'success'); close();
                    const drw = document.getElementById('adm-drawer-overlay');
                    if (drw) drw.remove();
                    _renderUsersPage();
                }
                else { const d = await r.json().catch(() => ({})); _toast(d.detail || _t('adm-ban-fail'), 'error'); }
            } catch (e) { _toast(_t('adm-ban-fail'), 'error'); }
        });
    };

    // ============ v118.44.1 解封 ============
    window.__admUnbanUser = async function(uid) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/users/' + uid + '/unban', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) {
                _toast(_t('adm-unbanned'), 'success');
                const drw = document.getElementById('adm-drawer-overlay');
                if (drw) drw.remove();
                _renderUsersPage();
            } else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };

    // ============ v118.44.1 级联删除 ============
    window.__admCascadeDelete = async function(uid, username) {
        const tok = localStorage.getItem('mrpilot_token');
        let preview;
        try {
            const r = await fetch('/api/admin/users/' + encodeURIComponent(uid) + '/cascade-preview', {
                headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (!r.ok) { _toast(_t('adm-cd-preview-fail'), 'error'); return; }
            preview = await r.json();
        } catch (e) { _toast(_t('adm-cd-preview-fail'), 'error'); return; }
        const c = preview.counts || {};
        const t_owner = preview.owner || {};
        const t_tenant = preview.tenant || {};
        const old = document.getElementById('adm-cd-overlay');
        if (old) old.remove();
        const ov = document.createElement('div');
        ov.id = 'adm-cd-overlay';
        ov.className = 'cpw-forgot-overlay';
        ov.innerHTML =
            '<div class="cpw-forgot-modal" style="max-width:520px">' +
                '<div class="cpw-forgot-head"><div class="cpw-forgot-title" style="color:#dc2626">⚠ ' + _esc(_t('adm-cd-title')) + '</div>' +
                    '<button class="cpw-forgot-close" id="adm-cd-close"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 3l10 10M3 13L13 3"/></svg></button>' +
                '</div>' +
                '<div class="cpw-forgot-body">' +
                    '<p class="cpw-forgot-tip" style="background:#fef2f2;border-color:#fecaca;color:#991b1b">' + _esc(_t('adm-cd-warn')) + '</p>' +
                    '<div style="background:#f4f4f0;border-radius:8px;padding:12px 14px;margin:12px 0;font-size:13px">' +
                        '<div style="font-weight:600;margin-bottom:8px;color:#0f172a">' + _esc(t_owner.username || t_owner.email || username) + '</div>' +
                        '<div style="color:#64748b;margin-bottom:10px">' + _esc(t_tenant.name || '—') + (t_tenant.tenant_type ? ' · ' + _esc(t_tenant.tenant_type) : '') + '</div>' +
                        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;color:#475569">' +
                            '<div>' + _esc(_t('adm-cd-c-employees')) + ': <b>' + (c.employees || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-ocr')) + ': <b>' + (c.ocr_records || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-clients')) + ': <b>' + (c.clients || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-erp')) + ': <b>' + (c.erp_endpoints || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-pushlog')) + ': <b>' + (c.erp_push_logs || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-email')) + ': <b>' + (c.email_accounts || 0) + '</b></div>' +
                            '<div>' + _esc(_t('adm-cd-c-bank')) + ': <b>' + (c.bank_recon_sessions || 0) + '</b></div>' +
                        '</div>' +
                    '</div>' +
                    '<label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569">' + _esc(_t('adm-cd-type-username').replace('{n}', t_owner.username || username)) + '</label>' +
                    '<input type="text" id="adm-cd-username" autocomplete="off" placeholder="' + _esc(t_owner.username || username) + '" style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box">' +
                    '<label style="display:block;margin:12px 0 4px;font-size:13px;color:#475569">' + _esc(_t('adm-cd-type-password')) + '</label>' +
                    '<input type="password" id="adm-cd-password" autocomplete="current-password" style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box">' +
                '</div>' +
                '<div class="cpw-forgot-foot">' +
                    '<button class="btn btn-ghost" id="adm-cd-cancel">' + _esc(_t('confirm-cancel')) + '</button>' +
                    '<button class="btn btn-danger" id="adm-cd-submit">' + _esc(_t('adm-cd-submit')) + '</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(ov);
        const close = () => ov.remove();
        ov.querySelector('#adm-cd-close').addEventListener('click', close);
        ov.querySelector('#adm-cd-cancel').addEventListener('click', close);
        ov.addEventListener('click', e => { if (e.target === ov) close(); });
        ov.querySelector('#adm-cd-submit').addEventListener('click', async () => {
            const uVal = (ov.querySelector('#adm-cd-username').value || '').trim();
            const pVal = ov.querySelector('#adm-cd-password').value || '';
            const expected = (t_owner.username || username || '').trim();
            if (uVal !== expected) { _toast(_t('adm-cd-username-mismatch'), 'error'); return; }
            if (!pVal) { _toast(_t('adm-cd-password-required'), 'error'); return; }
            try {
                const r = await fetch('/api/admin/users/' + encodeURIComponent(uid) + '/cascade-delete', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ confirm_username: uVal, confirm_password: pVal }),
                });
                const d = await r.json().catch(() => ({}));
                if (r.ok) {
                    _toast(_t('adm-cd-ok'), 'success'); close();
                    const drw = document.getElementById('adm-drawer-overlay');
                    if (drw) drw.remove();
                    _renderUsersPage();
                } else {
                    const map = {
                        'admin.password_invalid': _t('adm-cd-password-invalid'),
                        'admin.username_mismatch': _t('adm-cd-username-mismatch'),
                        'admin.cannot_delete_self': _t('adm-cd-cannot-self'),
                        'admin.not_an_owner': _t('adm-cd-not-owner'),
                        'admin.cascade_delete_failed': _t('adm-cd-fail'),
                    };
                    _toast(map[d.detail] || (typeof d.detail === 'string' ? d.detail : _t('adm-cd-fail')), 'error');
                }
            } catch (e) { _toast(_t('adm-cd-fail'), 'error'); }
        });
    };

    // ============ v118.44.1 待审付款操作 ============
    window.__admApprovePay = async function(id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/payments/' + id + '/review?action=approve', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) { _toast(_t('adm-approved'), 'success'); _renderUsersPage(); }
            else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };
    window.__admRejectPay = async function(id) {
        const ok = await _admConfirm(_t('adm-confirm-reject'), { danger: true, title: _t('adm-reject') });
        if (!ok) return;
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/payments/' + id + '/review?action=reject', {
                method: 'POST', headers: { 'Authorization': 'Bearer ' + tok },
            });
            if (r.ok) { _toast(_t('adm-rejected'), 'success'); _renderUsersPage(); }
            else _toast(_t('adm-action-fail'), 'error');
        } catch (e) { _toast(_t('adm-action-fail'), 'error'); }
    };
    window.__admViewSlip = async function(id) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/payments/' + id + '/screenshot', { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) { _toast(_t('adm-load-fail'), 'error'); return; }
            const blob = await r.blob();
            const url = URL.createObjectURL(blob);
            const ov = document.createElement('div');
            ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:10001;display:flex;align-items:center;justify-content:center;padding:30px;cursor:pointer';
            ov.innerHTML = '<img src="' + url + '" style="max-width:100%;max-height:100%;border-radius:8px">';
            ov.addEventListener('click', () => { URL.revokeObjectURL(url); ov.remove(); });
            document.body.appendChild(ov);
        } catch (e) { _toast(_t('adm-load-fail'), 'error'); }
    };

    // ============ v118.44.1 员工 tab ============
    async function _loadAdmEmployees() {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/admin/employees', { headers: { 'Authorization': 'Bearer ' + tok } });
            if (r.status === 403) return;
            const d = await r.json();
            _admEmployeesCache.rows = d.employees || [];
            _renderAdmEmployees();
        } catch (e) { console.error('emp', e); }
    }
    function _renderAdmEmployees() {
        const wrap = document.getElementById('adm-employees-table');
        if (!wrap) return;
        const q = (document.getElementById('adm-employee-search')?.value || '').toLowerCase().trim();
        let rows = _admEmployeesCache.rows;
        if (q) rows = rows.filter(e =>
            (e.username || '').toLowerCase().includes(q) ||
            (e.email || '').toLowerCase().includes(q) ||
            (e.tenant_name || '').toLowerCase().includes(q) ||
            (e.owner_username || '').toLowerCase().includes(q));
        if (!rows.length) {
            wrap.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-employees-empty')) + '</div>';
            return;
        }
        wrap.innerHTML =
            '<div class="adm-emp-readonly-tip">' + _esc(_t('adm-emp-readonly-tip')) + '</div>' +
            '<div class="adm-emp-row adm-emp-row-head">' +
                '<div>' + _esc(_t('adm-emp-col-name')) + '</div>' +
                '<div>' + _esc(_t('adm-emp-col-owner')) + '</div>' +
                '<div>' + _esc(_t('adm-emp-col-tenant')) + '</div>' +
                '<div>' + _esc(_t('adm-emp-col-status')) + '</div>' +
                '<div>' + _esc(_t('adm-emp-col-last-login')) + '</div>' +
            '</div>' +
            rows.map(e => {
                const statusCls = (e.is_active === false) ? 'adm-emp-status-disabled' : 'adm-emp-status-active';
                const statusTxt = (e.is_active === false) ? _t('team-status-disabled') : _t('team-status-active');
                const lastLogin = e.last_login_at ? new Date(e.last_login_at).toLocaleDateString() : _t('team-never-login');
                return '<div class="adm-emp-row">' +
                    '<div><div class="adm-emp-cell-strong">' + _esc(e.username || '?') + '</div><div class="adm-emp-cell-mute">' + _esc(e.email || '—') + '</div></div>' +
                    '<div>' + (e.owner_id ? '<a class="adm-emp-owner-link" style="cursor:pointer;color:#111111" onclick="window.__admOpenUserDrawer(\'' + _esc(e.owner_id) + '\')">' + _esc(e.owner_username || e.owner_email || '—') + '</a>' : '—') + '</div>' +
                    '<div class="adm-emp-cell-mute">' + _esc(e.tenant_name || '—') + '</div>' +
                    '<div class="' + statusCls + '">' + _esc(statusTxt) + '</div>' +
                    '<div class="adm-emp-cell-mute">' + _esc(lastLogin) + '</div>' +
                '</div>';
            }).join('');
    }

    // ============ v118.44.1 操作日志 tab ============
    async function _loadAdmLogs(page) {
        const tok = localStorage.getItem('mrpilot_token');
        const tbl = document.getElementById('adm-logs-table');
        if (tbl) tbl.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-logs-loading')) + '</div>';
        _admLogsState.page = page || 1;
        try {
            const url = '/api/admin/logs?page=' + _admLogsState.page + '&per_page=' + _admLogsState.per_page + '&q=' + encodeURIComponent(_admLogsState.q || '');
            const r = await fetch(url, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) throw new Error('http_' + r.status);
            const d = await r.json();
            _admLogsState.rows = d.logs || [];
            _admLogsState.total = d.total || 0;
            _renderAdmLogs();
            _renderAdmLogsPager();
        } catch (e) {
            if (tbl) tbl.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-logs-fail')) + '</div>';
        }
    }
    function _renderAdmLogs() {
        const tbl = document.getElementById('adm-logs-table');
        if (!tbl) return;
        const rows = _admLogsState.rows || [];
        if (!rows.length) { tbl.innerHTML = '<div class="adm-empty">' + _esc(_t('adm-logs-empty')) + '</div>'; return; }
        tbl.innerHTML =
            '<div class="adm-log-row adm-log-head">' +
                '<div>' + _esc(_t('adm-log-time')) + '</div>' +
                '<div>' + _esc(_t('adm-log-actor')) + '</div>' +
                '<div>' + _esc(_t('adm-log-action')) + '</div>' +
                '<div>' + _esc(_t('adm-log-target')) + '</div>' +
                '<div>' + _esc(_t('adm-log-ip')) + '</div>' +
            '</div>' +
            rows.map(l => {
                let t = '';
                if (l.created_at) { try { t = new Date(l.created_at).toLocaleString(); } catch (e) { t = l.created_at; } }
                const actor = (l.actor_username || '-') + (l.actor_is_super ? ' ⭐' : '');
                return '<div class="adm-log-row">' +
                    '<div class="adm-log-time">' + _esc(t) + '</div>' +
                    '<div class="adm-log-actor">' + _esc(actor) + '</div>' +
                    '<div><span class="adm-log-action">' + _esc(l.action || '-') + '</span></div>' +
                    '<div class="adm-log-target">' + _esc(l.target_name || l.target_type || '-') + '</div>' +
                    '<div class="adm-log-ip">' + _esc(l.ip || '-') + '</div>' +
                '</div>';
            }).join('');
    }
    function _renderAdmLogsPager() {
        const wrap = document.getElementById('adm-pager-logs');
        if (!wrap) return;
        const total = _admLogsState.total || 0;
        const page = _admLogsState.page || 1;
        const per = _admLogsState.per_page || 50;
        const totalPages = Math.max(1, Math.ceil(total / per));
        wrap.style.display = '';
        wrap.innerHTML =
            '<div class="adm-pager-info">' + _esc(_t('adm-pager-total').replace('{n}', total)) + '</div>' +
            '<div class="adm-pager-ctrl">' +
                '<button class="adm-pager-btn" type="button" data-adm-page="' + (page - 1) + '" data-adm-pager-scope="logs" ' + (page <= 1 ? 'disabled' : '') + '>← ' + _esc(_t('adm-pager-prev')) + '</button>' +
                '<span class="adm-pager-page">' + _esc(_t('adm-pager-page').replace('{p}', page).replace('{t}', totalPages)) + '</span>' +
                '<button class="adm-pager-btn" type="button" data-adm-page="' + (page + 1) + '" data-adm-pager-scope="logs" ' + (page >= totalPages ? 'disabled' : '') + '>' + _esc(_t('adm-pager-next')) + ' →</button>' +
            '</div>';
    }

    // ============ v118.44.1 tab 切换 + 搜索 + 分页 ============
    function _bindAdmTabsAndFilters() {
        document.addEventListener('click', function(ev) {
            const tabBtn = ev.target.closest('.adm-tab[data-adm-tab]');
            if (tabBtn) {
                const target = tabBtn.dataset.admTab;
                _admCurTab = target;
                document.querySelectorAll('.adm-tab[data-adm-tab]').forEach(b =>
                    b.classList.toggle('active', b.dataset.admTab === target));
                document.querySelectorAll('[data-adm-tab-pane]').forEach(p => {
                    p.style.display = (p.dataset.admTabPane === target) ? '' : 'none';
                });
                document.querySelectorAll('[data-adm-tab-filter]').forEach(f => {
                    f.style.display = (f.dataset.admTabFilter === target) ? '' : 'none';
                });
                if (target === 'employees' && !_admEmployeesCache.rows.length) _loadAdmEmployees();
                if (target === 'logs' && !_admLogsState.rows.length) _loadAdmLogs(1);
                return;
            }
            const pgBtn = ev.target.closest('.adm-pager-btn[data-adm-page]');
            if (pgBtn && !pgBtn.disabled) {
                const p = parseInt(pgBtn.dataset.admPage, 10);
                const scope = pgBtn.dataset.admPagerScope;
                if (scope === 'logs') _loadAdmLogs(p);
                return;
            }
        });
        document.addEventListener('input', function(ev) {
            if (!ev.target) return;
            if (ev.target.id === 'adm-user-search') {
                _renderAdmUserList(_admPageState.users || []);
            }
            if (ev.target.id === 'adm-employee-search') {
                _renderAdmEmployees();
            }
            if (ev.target.id === 'adm-logs-search') {
                clearTimeout(window.__admLogsSearchTimer);
                window.__admLogsSearchTimer = setTimeout(function() {
                    _admLogsState.q = (ev.target.value || '').trim();
                    _loadAdmLogs(1);
                }, 350);
            }
        });
        document.addEventListener('change', function(ev) {
            if (ev.target && ev.target.id === 'adm-plan-filter') {
                _renderAdmUserList(_admPageState.users || []);
            }
        });
    }

    // ============ v118.44.1 CSV 下载 ============
    async function _csvDownload(url, filename) {
        const tok = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch(url, { headers: { 'Authorization': 'Bearer ' + tok } });
            if (!r.ok) { _toast(_t('adm-csv-failed'), 'error'); return; }
            const blob = await r.blob();
            const objUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = objUrl; a.download = filename;
            document.body.appendChild(a); a.click();
            setTimeout(() => { URL.revokeObjectURL(objUrl); a.remove(); }, 100);
            _toast(_t('adm-csv-ok'), 'success');
        } catch (e) { _toast(_t('adm-csv-failed'), 'error'); }
    }

    // ============ 业务按钮 ============
    function _bindButtons() {
        // 刷新成本
        _on('btn-cost-refresh', 'click', function () {
            _toast(_t('cost-refresh') + '…');
            _renderCostPage();
        });
        // 在 Google 查最新
        const gbtn = document.getElementById('btn-billing-google');
        if (gbtn) {
            gbtn.setAttribute('href', 'https://aistudio.google.com/app/apikey');
            gbtn.setAttribute('target', '_blank');
            gbtn.setAttribute('rel', 'noopener');
        }
        // 更新余额
        _on('btn-billing-update', 'click', async function () {
            const input = await _admPrompt(
                _curLang === 'th' ? 'ยอดคงเหลือ Google จริง (THB):' : 'Google 实际余额(THB):',
                {
                    title: _curLang === 'th' ? 'อัปเดตยอดคงเหลือ Google' : '更新 Google 余额',
                    type: 'number',
                    placeholder: '0.00',
                }
            );
            if (!input) return;
            const bal = parseFloat(input);
            if (isNaN(bal) || bal < 0) { _toast(_curLang === 'th' ? 'ตัวเลขไม่ถูกต้อง' : '数字格式错误', 'error'); return; }
            try {
                await _adminFetch('/api/admin/billing/balance', {
                    method: 'POST',
                    body: { real_balance_thb: bal },
                });
                _toast(_curLang === 'th' ? 'บันทึกแล้ว' : '已保存', 'success');
                _renderCostPage();
            } catch (e) { _toast(_t('adm-load-fail') + ' · ' + e.message, 'error'); }
        });
        // 导出 CSV(成本)
        _on('btn-cost-export', 'click', async function () {
            try {
                const tok = localStorage.getItem('mrpilot_token');
                const r = await fetch('/api/admin/cost/export?days=30', { headers: { 'Authorization': 'Bearer ' + tok } });
                if (!r.ok) throw new Error('HTTP ' + r.status);
                const blob = await r.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'pearnly_cost_' + new Date().toISOString().slice(0, 10) + '.csv'; a.click();
                URL.revokeObjectURL(url);
            } catch (e) { _toast(_t('adm-load-fail') + ' · ' + e.message, 'error'); }
        });
        // v118.35.0.22 · 导出 Credits 扣费明细
        _on('btn-credits-export', 'click', async function () {
            try {
                const tok = localStorage.getItem('mrpilot_token');
                const r = await fetch('/api/admin/credits/export?days=30', { headers: { 'Authorization': 'Bearer ' + tok } });
                if (!r.ok) throw new Error('HTTP ' + r.status);
                const blob = await r.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'pearnly_credits_' + new Date().toISOString().slice(0, 10) + '.csv'; a.click();
                URL.revokeObjectURL(url);
            } catch (e) { _toast(_t('adm-load-fail') + ' · ' + e.message, 'error'); }
        });
        // 刷新 pending
        _on('adm-refresh-pending', 'click', function () { _renderUsersPage(); });
        // CSV 下载(v118.44.1 真实下载 · 替换原占位)
        _on('adm-users-csv-btn', 'click', function () { _csvDownload('/api/admin/users.csv', 'pearnly_users.csv'); });
        _on('adm-logs-csv-btn', 'click', function () {
            const q = encodeURIComponent(_admLogsState.q || '');
            _csvDownload('/api/admin/logs.csv?q=' + q, 'pearnly_logs.csv');
        });
    }

    // ============ 主启动流程 ============
    async function _boot() {
        const user = await _verifySuperAdmin();
        if (!user) return;
        // 初始 lang
        try {
            let cur = localStorage.getItem('mrpilot_lang') || 'zh';
            if (!['zh', 'th'].includes(cur)) cur = 'zh';
            _curLang = cur;
        } catch (_) {}
        _applyI18n(_curLang);
        _bindAvatar(user);
        _bindLang();
        _bindLogout();
        _bindButtons();
        _bindAdmTabsAndFilters();
        _renderUptime();
        _bindSidebar();
        _switchView(_resolveRoute());
        try { localStorage.removeItem('mrpilot_settings_tab'); } catch (_) {}
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _boot);
    } else {
        _boot();
    }
})();
