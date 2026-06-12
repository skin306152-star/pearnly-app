// ============================================================
// Workspace 账套主体切换器(右上角唯一入口 · "在为哪家公司做账")。
//
// 账套主体 = 硬边界:业务必须归属一个主体(个人模式已退场 · 个人也是正经"个人主体")。
// 与发票买方(history.client_id)是两个维度:买方按每张发票识别,不在此切换。
//
// 数据源:GET /api/workspace/clients(workspace_routes.py)。
// 业务请求带 header X-Workspace-Client-Id = getActiveWorkspaceClientId()。
//
// 0/1/N 分流:1 个 → 加载时自动选中;0/N 且未选 → 业务动作经 requireWorkspace 按需弹选择器
// (不在登录时强弹);chooser 空态引导建主体(owner)或联系管理员(成员)。
//
// 暴露(window):getActiveWorkspaceClientId / setActiveWorkspaceClientId / requireWorkspace /
//   openWorkspaceChooser / renderWorkspaceControl / fetchWorkspaceClients / wsEmptyHtml /
//   openWorkspaceChooserUI。事件:pearnly:workspace-changed。
// ============================================================
(function () {
    'use strict';

    const LS_ID = 'pearnly_active_workspace_client_id';

    function _t(key: string, fallback: string) {
        if (typeof window.t === 'function') {
            const s = window.t(key);
            if (s && s !== key) return s;
        }
        return fallback;
    }

    // 「先选账套」阻断态全站统一一版(kit .pn-empty)· 库存/桌台/收款/收银员四屏共用。
    window.wsEmptyHtml = function (btnId: string): string {
        const ico =
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="24" height="24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>';
        return (
            `<div class="pn-empty fill"><div class="ill">${ico}</div>` +
            `<div class="t">${_t('ws-empty-title', '先选择账套')}</div>` +
            `<div class="s">${_t('ws-empty-sub', '这个页面按账套隔离 · 选好后才会显示数据')}</div>` +
            `<div class="act"><button class="btn btn-primary btn-sm" id="${btnId}">${_t('ws-empty-pick', '选择账套')}</button></div></div>`
        );
    };

    function _isOwner() {
        // owner 判定要宽松:自行注册/白名单/付费主账号默认都是 owner(绝不把 owner 当成员工)。
        const u = window._userInfo || {};
        const role = String(u.role || '').toLowerCase();
        const trole = String(u.tenant_role || '').toLowerCase();
        return (
            u.is_super_admin === true ||
            u.is_owner === true ||
            role === 'owner' ||
            role === 'admin' ||
            trole === 'owner' ||
            trole === 'admin'
        );
    }

    // ---------- 状态 ----------
    function getActiveWorkspaceClientId() {
        const v = localStorage.getItem(LS_ID);
        if (!v || v === 'null' || v === '0' || v === '') return null;
        const n = parseInt(v, 10);
        return isNaN(n) ? null : n;
    }

    function _emit(id: number | null) {
        try {
            window.dispatchEvent(
                new CustomEvent('pearnly:workspace-changed', { detail: { id: id } })
            );
        } catch {
            /* no-op */
        }
    }

    function setActiveWorkspaceClientId(id: number | null) {
        const old = getActiveWorkspaceClientId();
        if (id == null || id === 0) {
            localStorage.removeItem(LS_ID);
        } else {
            localStorage.setItem(LS_ID, String(id));
        }
        if (String(old) !== String(id)) _emit(id);
    }

    // ---------- 数据 ----------
    async function fetchWorkspaceClients() {
        try {
            const fn = window.apiGet;
            if (typeof fn !== 'function') return [];
            const res = await fn('/api/workspace/clients');
            return (res && (res.clients || res.items)) || [];
        } catch {
            return [];
        }
    }

    // ---------- 惰性守卫 ----------
    // 业务功能入口调用:已选账套 → onOk();否则弹选择器(选完直接进原功能)。
    async function requireWorkspace(onOk: (() => void) | null) {
        if (getActiveWorkspaceClientId() != null) {
            if (typeof onOk === 'function') onOk();
            return true;
        }
        openWorkspaceChooser(onOk);
        return false;
    }

    // ---------- 选择面板(选/建账套主体 · 唯一入口)----------
    // afterSelect:选定后回调(惰性守卫复用:选完直接进原功能)。
    async function openWorkspaceChooser(afterSelect: (() => void) | null) {
        const list = await fetchWorkspaceClients();
        // 惰性触发(带 afterSelect)且恰好 1 个 → 自动选中直接进,不弹。
        if (typeof afterSelect === 'function' && list.length === 1) {
            setActiveWorkspaceClientId(Number(list[0].id));
            afterSelect();
            return;
        }
        if (typeof window.openWorkspaceChooserUI === 'function') {
            window.openWorkspaceChooserUI({
                clients: list,
                active: getActiveWorkspaceClientId(),
                onPick: function (id: number | string) {
                    setActiveWorkspaceClientId(Number(id));
                    if (typeof afterSelect === 'function') afterSelect();
                },
                emptyHint: list.length
                    ? null
                    : _isOwner()
                      ? _t(
                            'ws-empty-owner',
                            '还没有账套主体。创建一个主体后即可开始记账、开票与对账。'
                        )
                      : _t('ws-empty-employee', '你还没有被分配账套主体,请联系管理员分配。'),
                emptyOwner: !list.length && _isOwner(),
            });
            return;
        }
        if (!list.length) {
            const hint = _isOwner()
                ? _t('ws-empty-owner', '还没有账套主体。创建一个主体后即可开始记账、开票与对账。')
                : _t('ws-empty-employee', '你还没有被分配账套主体,请联系管理员分配。');
            if (typeof window.showToast === 'function') window.showToast(hint, 'info');
        }
    }

    // ---------- 右上角标签(home.js 挂载点调用)----------
    function renderWorkspaceControl(el?: HTMLElement | null) {
        const root = el || document.getElementById('workspace-switcher-root');
        if (!root) return;
        const id = getActiveWorkspaceClientId();
        let text;
        if (id != null) {
            const list = window._workspaceClientsCache || [];
            const c = (list as Array<{ id: number; name: string }>).find(
                (x) => Number(x.id) === Number(id)
            );
            text = c ? c.name : _t('ws-current-label', '当前账套主体');
        } else {
            text = _t('ws-empty-pick', '选择账套');
        }
        root.innerHTML =
            '<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">' +
            _icon('building') +
            '<span class="ws-ctrl-label">' +
            _esc(text) +
            '</span></button>';
        const btn = root.querySelector('#ws-ctrl-btn');
        if (btn) btn.addEventListener('click', () => openWorkspaceChooser(null));
    }

    function _esc(s: unknown) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (m: string) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[
                m as '&' | '<' | '>' | '"' | "'"
            ];
        });
    }

    // 铁律(UI):只用 SVG line 图标(feather/lucide)· 禁止 emoji 当图标。
    function _icon(name: string) {
        const open =
            '<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
        if (name === 'building') {
            return (
                open +
                '<rect x="2" y="7" width="20" height="14" rx="2"/>' +
                '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
            );
        }
        return open + '<path d="M12 5v14M5 12h14"/></svg>';
    }

    function openWorkspaceChooserUI(opts: {
        clients?: Array<{ id: number; name?: string; tax_id?: string }>;
        active?: number | null;
        emptyHint?: string | null;
        emptyOwner?: boolean;
        onPick?: (id: number | string) => void;
    }) {
        opts = opts || {};
        const clients = opts.clients || [];
        const active = opts.active;
        const old = document.getElementById('ws-modal');
        if (old) old.remove();

        const overlay = document.createElement('div');
        overlay.id = 'ws-modal';
        overlay.className = 'ws-modal';

        // 账套主体下拉(列表多时更紧凑)。
        let selectHtml = '';
        if (clients.length) {
            const options = [
                '<option value="">' + _esc(_t('ws-select-ph', '— 选择账套主体 —')) + '</option>',
            ].concat(
                clients.map(function (c) {
                    const isActive = active != null && Number(active) === Number(c.id);
                    return (
                        '<option value="' +
                        _esc(c.id) +
                        '"' +
                        (isActive ? ' selected' : '') +
                        '>' +
                        _esc(c.name || '#' + c.id) +
                        '</option>'
                    );
                })
            );
            selectHtml =
                '<div class="ws-modal-item ws-modal-item-account">' +
                '<span class="ws-modal-item-ic">' +
                _icon('building') +
                '</span>' +
                '<span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;flex:1;">' +
                '<span class="ws-modal-item-name">' +
                _esc(_t('ws-select-label', '账套主体')) +
                '</span>' +
                '<select class="ws-modal-select" data-ws-select="1" style="margin-top:6px;width:100%;">' +
                options.join('') +
                '</select>' +
                '</span>' +
                '</div>';
        }

        const emptyHtml =
            !clients.length && opts.emptyHint
                ? '<div class="ws-modal-empty">' + _esc(opts.emptyHint) + '</div>'
                : '';
        // 有主体:提示去客户管理新增;空 + owner:直接给「新建主体」CTA(起引导向导)。
        const footHtml = opts.emptyOwner
            ? '<div class="ws-modal-hint" style="padding:6px 4px 2px;"><button class="btn btn-primary btn-sm" data-ws-create="1" style="width:100%;">' +
              _esc(_t('ws-create', '新建主体')) +
              '</button></div>'
            : clients.length
              ? '<div class="ws-modal-hint" style="font-size:12px;color:var(--ink2);padding:10px 4px 2px;line-height:1.5;white-space:normal;">' +
                _esc(_t('ws-add-hint', '如需新增账套主体,请前往「客户管理」添加')) +
                '</div>'
              : '';

        overlay.innerHTML =
            '<div class="ws-modal-box" role="dialog" aria-modal="true">' +
            '<div class="ws-modal-head">' +
            '<span class="ws-modal-title">' +
            _esc(_t('ws-chooser-title', '选择账套主体')) +
            '</span>' +
            '<button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button>' +
            '</div>' +
            '<div class="ws-modal-subtitle" style="font-size:12px;color:var(--ink2);padding:2px 4px 12px;line-height:1.45;white-space:normal;">' +
            _esc(
                _t(
                    'ws-chooser-subtitle',
                    '账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。'
                )
            ) +
            '</div>' +
            '<div class="ws-modal-list">' +
            selectHtml +
            '</div>' +
            emptyHtml +
            footHtml +
            '</div>';

        document.body.appendChild(overlay);

        const selEl = overlay.querySelector('[data-ws-select]') as HTMLSelectElement | null;
        if (selEl) {
            selEl.addEventListener('change', function () {
                const id = selEl.value;
                if (!id) return;
                if (typeof opts.onPick === 'function') opts.onPick(id);
                close();
                renderWorkspaceControl();
            });
        }

        function close() {
            overlay.remove();
        }

        overlay.addEventListener('click', function (e) {
            if (e.target === overlay || (e.target as HTMLElement).closest('[data-ws-close]')) {
                close();
                return;
            }
            // 空态 owner:新建主体 → 起引导向导(兜底去客户管理)。
            if ((e.target as HTMLElement).closest('[data-ws-create]')) {
                close();
                if (typeof window.startOnboardingFlow === 'function') window.startOnboardingFlow();
                else if (typeof window.routeTo === 'function') window.routeTo('clients');
                return;
            }
        });
    }

    window.openWorkspaceChooserUI = openWorkspaceChooserUI;

    window.addEventListener('pearnly:workspace-changed', function () {
        renderWorkspaceControl();
    });

    // ---------- 暴露 ----------
    window.getActiveWorkspaceClientId = getActiveWorkspaceClientId;
    window.setActiveWorkspaceClientId = setActiveWorkspaceClientId;
    window.requireWorkspace = requireWorkspace;
    window.openWorkspaceChooser = openWorkspaceChooser;
    window.renderWorkspaceControl = renderWorkspaceControl;
    window.fetchWorkspaceClients = fetchWorkspaceClients;

    // 列表缓存 + 0/1/N:恰好 1 个且未选 → 自动选中(无打扰);0/N 交给按需 requireWorkspace。
    fetchWorkspaceClients().then((l) => {
        window._workspaceClientsCache = l;
        if (getActiveWorkspaceClientId() == null && Array.isArray(l) && l.length === 1) {
            setActiveWorkspaceClientId(Number((l[0] as { id: number }).id));
        }
        renderWorkspaceControl();
    });

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('workspace-switcher', renderWorkspaceControl);
    }
})();
