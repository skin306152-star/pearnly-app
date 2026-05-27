// ============================================================
// B4 + B2 (2026-05-26) · Workspace 工作模式切换器(账套主体 = "在为哪家公司做账")
//
// 取代旧 ClientSwitcher(买方过滤)成为右上角唯一入口(Zihao 拍板·选项 A)。
// 工作模式(B2 · 不做登录硬拦截):
//   - personal(个人事务):不选客户·正常进系统·业务功能惰性提示。
//   - client(客户业务):选定 workspace·本会话业务默认归属它。
// 与发票买方(history.client_id)是两个维度:买方按每张发票识别·不在此切换。
//
// 数据源:GET /api/workspace/clients(workspace_routes.py · B4 后端)。
// 业务请求带 header X-Workspace-Client-Id = getActiveWorkspaceClientId()(home.js api 包装器读)。
//
// 暴露(window):getWorkMode / getActiveWorkspaceClientId / setActiveWorkspaceClientId /
//   enterPersonalMode / requireWorkspace / openWorkspaceChooser / renderWorkspaceControl /
//   fetchWorkspaceClients。事件:pearnly:workspace-changed。
//
// ⚠️ home.js 挂载点 + api header 接线 + 移除旧 ClientSwitcher = 单独一步(需浏览器验)。
// ============================================================
(function () {
    'use strict';

    const LS_ID = 'pearnly_active_workspace_client_id';
    const LS_MODE = 'pearnly_work_mode'; // 'personal' | 'client'

    function _t(key, fallback) {
        if (typeof window.t === 'function') {
            const s = window.t(key);
            if (s && s !== key) return s;
        }
        return fallback;
    }

    function _isOwner() {
        // B4 修 (2026-05-26) · owner 判定要宽松:自行注册/白名单/付费主账号默认都是 owner。
        // 兼容多种后端字段命名 · 任一命中即 owner。绝不能把 owner 当成员工(否则空 workspace
        // 会错显"请联系老板分配")。要求 home.js 已同步 window._userInfo(/api/me 加载后)。
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
    function getWorkMode() {
        return localStorage.getItem(LS_MODE) === 'client' ? 'client' : 'personal';
    }

    function getActiveWorkspaceClientId() {
        const v = localStorage.getItem(LS_ID);
        if (!v || v === 'null' || v === '0' || v === '') return null;
        const n = parseInt(v, 10);
        return isNaN(n) ? null : n;
    }

    function _emit(id) {
        try {
            window.dispatchEvent(
                new CustomEvent('pearnly:workspace-changed', {
                    detail: { id: id, mode: getWorkMode() },
                })
            );
        } catch {
            /* no-op */
        }
    }

    function setActiveWorkspaceClientId(id) {
        const old = getActiveWorkspaceClientId();
        if (id == null || id === 0) {
            localStorage.removeItem(LS_ID);
        } else {
            localStorage.setItem(LS_ID, String(id));
            localStorage.setItem(LS_MODE, 'client'); // 选了客户即进客户业务模式
        }
        if (String(old) !== String(id)) _emit(id);
    }

    function enterPersonalMode() {
        const hadId = getActiveWorkspaceClientId();
        localStorage.setItem(LS_MODE, 'personal');
        localStorage.removeItem(LS_ID);
        if (hadId != null) _emit(null);
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

    // ---------- 惰性守卫(B2 核心)----------
    // 业务功能入口调用:有 workspace → onOk();否则轻提示「这个功能需要先选择客户」。
    async function requireWorkspace(onOk) {
        if (getWorkMode() === 'client' && getActiveWorkspaceClientId() != null) {
            if (typeof onOk === 'function') onOk();
            return true;
        }
        // 个人模式 / 未选 → 轻提示(不阻塞全站 · 只挡这个动作)
        const msg = _t('ws-need-client', '这个功能需要先选择工作空间');
        const pick = _t('ws-btn-pick', '选择工作空间');
        const cancel = _t('ws-btn-cancel', '取消');
        // home.js 的 showConfirm(msg, opts) 返回 Promise<bool> · 用 okText/cancelText 自定义按钮。
        if (typeof window.showConfirm === 'function') {
            const ok = await window.showConfirm(msg, { okText: pick, cancelText: cancel });
            if (ok) openWorkspaceChooser(onOk);
        } else if (window.confirm(msg + '\n\n[' + pick + ' / ' + cancel + ']')) {
            openWorkspaceChooser(onOk);
        }
        return false;
    }

    // ---------- 选择面板(work mode + 选/建工作空间 · 唯一入口)----------
    // afterSelect:选定 workspace 后回调(惰性守卫复用:选完直接进原功能)。
    async function openWorkspaceChooser(afterSelect) {
        const list = await fetchWorkspaceClients();
        // 只剩 1 个时自动选中 · 不弹 —— 但**仅限业务动作惰性触发**(带 afterSelect 回调)。
        // 修(2026-05-26 Zihao 报):用户手动点右上角(afterSelect 为空)必须永远弹窗,
        // 否则只有 1 个工作空间时点右上角会命中这条 → 自动选中后 return → 永远打不开
        // 弹层 → 没法切换/新建/回个人事务。
        if (
            typeof afterSelect === 'function' &&
            getWorkMode() !== 'personal' &&
            list.length === 1
        ) {
            setActiveWorkspaceClientId(Number(list[0].id));
            afterSelect();
            return;
        }
        if (typeof window.openWorkspaceChooserUI === 'function') {
            // home.js 挂载步骤提供真实弹层 UI;本模块给它数据 + 回调
            window.openWorkspaceChooserUI({
                clients: list,
                canCreate: _isOwner(),
                active: getActiveWorkspaceClientId(),
                onPersonal: enterPersonalMode,
                onPick: function (id) {
                    setActiveWorkspaceClientId(Number(id));
                    if (typeof afterSelect === 'function') afterSelect();
                },
                emptyHint: list.length
                    ? null
                    : _isOwner()
                      ? _t(
                            'ws-empty-owner',
                            '还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。'
                        )
                      : _t('ws-empty-employee', '你还没有可用的工作空间,请联系管理员分配。'),
            });
            return;
        }
        // 兜底(UI 未挂载时):0 个不死循环,只给提示
        if (!list.length) {
            const hint = _isOwner()
                ? _t(
                      'ws-empty-owner',
                      '还没有工作空间。创建一个公司后,上传、对账和 ERP 推送都会归属到该公司。'
                  )
                : _t('ws-empty-employee', '你还没有可用的工作空间,请联系管理员分配。');
            if (typeof window.showToast === 'function') window.showToast(hint, 'info');
        }
    }

    // ---------- 右上角两态标签(home.js 挂载点调用)----------
    function renderWorkspaceControl(el) {
        const root = el || document.getElementById('workspace-switcher-root');
        if (!root) return;
        const mode = getWorkMode();
        const id = getActiveWorkspaceClientId();
        let icon, text;
        if (mode === 'client' && id != null) {
            const list = window._workspaceClientsCache || [];
            const c = list.find((x) => Number(x.id) === Number(id));
            icon = _icon('building');
            text = c ? c.name : _t('ws-current-label', '当前工作空间');
        } else {
            icon = _icon('user');
            text = _t('ws-personal', '个人事务');
        }
        root.innerHTML =
            '<button class="ws-ctrl-btn" id="ws-ctrl-btn" type="button">' +
            icon +
            '<span class="ws-ctrl-label">' +
            _esc(text) +
            '</span></button>';
        const btn = root.querySelector('#ws-ctrl-btn');
        if (btn) btn.addEventListener('click', () => openWorkspaceChooser(null));
    }

    // ---------- 选择面板真实 UI(B4 · 自包含弹层 · 不进 home.js 巨石)----------
    // openWorkspaceChooser 调 window.openWorkspaceChooserUI(opts) · opts 见下。
    function _esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    // 铁律(UI):只用 SVG line 图标(feather/lucide)· 禁止 emoji 当图标。
    function _icon(name) {
        const open =
            '<svg class="ws-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
        if (name === 'building') {
            // feather briefcase(客户业务)
            return (
                open +
                '<rect x="2" y="7" width="20" height="14" rx="2"/>' +
                '<path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
            );
        }
        // feather user(个人事务)
        return (
            open +
            '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>' +
            '<circle cx="12" cy="7" r="4"/></svg>'
        );
    }

    function openWorkspaceChooserUI(opts) {
        opts = opts || {};
        const clients = opts.clients || [];
        const active = opts.active;
        // 关掉已存在的弹层(防叠层)
        const old = document.getElementById('ws-modal');
        if (old) old.remove();

        const overlay = document.createElement('div');
        overlay.id = 'ws-modal';
        overlay.className = 'ws-modal';

        const personalActive = getWorkMode() === 'personal' || active == null;
        // 个人事务(固定按钮 · 不动 —— Zihao 2026-05-27)
        const personalHtml =
            '<button type="button" class="ws-modal-item' +
            (personalActive ? ' active' : '') +
            '" data-ws-personal="1">' +
            '<span class="ws-modal-item-ic">' +
            _icon('user') +
            '</span>' +
            '<span class="ws-modal-item-text" style="display:flex;flex-direction:column;align-items:flex-start;min-width:0;">' +
            '<span class="ws-modal-item-name">' +
            _esc(_t('ws-personal', '个人事务')) +
            '</span>' +
            '<span class="ws-modal-item-desc" style="font-size:11px;color:#6b7280;font-weight:400;margin-top:2px;line-height:1.35;white-space:normal;">' +
            _esc(_t('ws-personal-desc', '用于临时识别、测试或处理不归属任何公司的文件。')) +
            '</span>' +
            '</span>' +
            '</button>';

        // 账套主体:下拉选择(Zihao 2026-05-27 · 列表多时更紧凑;个人事务保持按钮不动)
        let selectHtml = '';
        if (clients.length) {
            const opts = [
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
                '<div class="ws-modal-select-row">' +
                '<label class="ws-modal-select-label">' +
                _esc(_t('ws-select-label', '账套主体')) +
                '</label>' +
                '<select class="ws-modal-select" data-ws-select="1">' +
                opts.join('') +
                '</select>' +
                '</div>';
        }

        const emptyHtml =
            !clients.length && opts.emptyHint
                ? '<div class="ws-modal-empty">' + _esc(opts.emptyHint) + '</div>'
                : '';
        const createHtml = opts.canCreate
            ? '<div class="ws-modal-create">' +
              '<button type="button" class="ws-modal-create-toggle" data-ws-create-toggle="1">+ ' +
              _esc(_t('ws-create-client', '新建工作空间')) +
              '</button>' +
              '<div class="ws-modal-create-form" data-ws-create-form style="display:none;">' +
              '<input type="text" class="ws-modal-create-input" data-ws-create-name placeholder="' +
              _esc(_t('ws-create-ph', '公司名称,例如 BAKELAB')) +
              '">' +
              '<button type="button" class="ws-modal-create-submit" data-ws-create-submit="1">' +
              _esc(_t('ws-create-submit', '创建')) +
              '</button>' +
              '</div>' +
              '</div>'
            : '';

        overlay.innerHTML =
            '<div class="ws-modal-box" role="dialog" aria-modal="true">' +
            '<div class="ws-modal-head">' +
            '<span class="ws-modal-title">' +
            _esc(_t('ws-chooser-title', '选择工作空间')) +
            '</span>' +
            '<button type="button" class="ws-modal-close" data-ws-close="1" aria-label="close">✕</button>' +
            '</div>' +
            // B1 (P3) · 副标题点明:工作空间 = 你的公司(发票卖方)· 跟"买方客户"对称
            '<div class="ws-modal-subtitle" style="font-size:12px;color:#6b7280;padding:2px 4px 12px;line-height:1.45;white-space:normal;">' +
            _esc(
                _t(
                    'ws-chooser-subtitle',
                    '账套主体 = 你的公司(发票卖方/开票方)。选择正在为哪家公司做账。'
                )
            ) +
            '</div>' +
            '<div class="ws-modal-list">' +
            personalHtml +
            selectHtml +
            '</div>' +
            emptyHtml +
            createHtml +
            '</div>';

        document.body.appendChild(overlay);

        // 账套主体下拉:change 即选定(不在上面的 click 委托里)
        const selEl = overlay.querySelector('[data-ws-select]');
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
            if (e.target === overlay || e.target.closest('[data-ws-close]')) {
                close();
                return;
            }
            const personalBtn = e.target.closest('[data-ws-personal]');
            if (personalBtn) {
                if (typeof opts.onPersonal === 'function') opts.onPersonal();
                close();
                renderWorkspaceControl();
                return;
            }
            const pickBtn = e.target.closest('[data-ws-pick]');
            if (pickBtn) {
                const id = pickBtn.getAttribute('data-ws-pick');
                if (typeof opts.onPick === 'function') opts.onPick(id);
                close();
                renderWorkspaceControl();
                return;
            }
            const toggle = e.target.closest('[data-ws-create-toggle]');
            if (toggle) {
                const form = overlay.querySelector('[data-ws-create-form]');
                if (form) {
                    form.style.display = form.style.display === 'none' ? 'flex' : 'none';
                    const inp = form.querySelector('[data-ws-create-name]');
                    if (inp) inp.focus();
                }
                return;
            }
            const submit = e.target.closest('[data-ws-create-submit]');
            if (submit) {
                _doCreate(overlay, opts, close);
                return;
            }
        });
    }

    async function _doCreate(overlay, opts, close) {
        const inp = overlay.querySelector('[data-ws-create-name]');
        const name = inp ? (inp.value || '').trim() : '';
        if (!name) {
            if (inp) inp.focus();
            return;
        }
        let res = null;
        try {
            if (typeof window.apiPost === 'function') {
                const r = await window.apiPost('/api/workspace/clients', { name: name });
                res = r && typeof r.json === 'function' ? await r.json().catch(() => null) : r;
            }
        } catch {
            res = null;
        }
        const newId = res && (res.id || (res.client && res.client.id));
        if (!newId) {
            if (typeof window.showToast === 'function') {
                window.showToast(_t('ws-create-fail', '新建工作空间失败 · 请重试'), 'error');
            }
            return;
        }
        // 刷新缓存(让右上角标签能解析到新客户名)再选中它
        window._workspaceClientsCache = await fetchWorkspaceClients();
        setActiveWorkspaceClientId(Number(newId));
        if (typeof opts.onPick === 'function') {
            // onPick 已在弹层里再调一次 setActive 也幂等 · 但 _doCreate 直接走完整闭环更稳
        }
        close();
        renderWorkspaceControl();
    }

    window.openWorkspaceChooserUI = openWorkspaceChooserUI;

    // 任何工作模式/选定客户变化 → 右上角标签即时刷新。
    window.addEventListener('pearnly:workspace-changed', function () {
        renderWorkspaceControl();
    });

    // ---------- 暴露 ----------
    window.getWorkMode = getWorkMode;
    window.getActiveWorkspaceClientId = getActiveWorkspaceClientId;
    window.setActiveWorkspaceClientId = setActiveWorkspaceClientId;
    window.enterPersonalMode = enterPersonalMode;
    window.requireWorkspace = requireWorkspace;
    window.openWorkspaceChooser = openWorkspaceChooser;
    window.renderWorkspaceControl = renderWorkspaceControl;
    window.fetchWorkspaceClients = fetchWorkspaceClients;

    // ---------- 登录软弹(B2 · Zihao 2026-05-27 上线 · 软弹不硬拦)----------
    // 登录后若还没选账套主体且未明确进个人事务 → 自动弹一次让用户选(可关 / 可选个人事务)。
    // 每会话仅一次(sessionStorage),不在每次刷新都打扰。
    function _maybeLoginPrompt() {
        try {
            if (sessionStorage.getItem('pearnly_ws_login_prompted') === '1') return;
            if (getActiveWorkspaceClientId() != null) return; // 已选账套 → 不打扰
            if (localStorage.getItem(LS_MODE) === 'personal') return; // 明确选过个人事务 → 不打扰
            sessionStorage.setItem('pearnly_ws_login_prompted', '1');
            // 略等 /api/me 就绪(owner 判定 + 新建表单可见性靠 window._userInfo)
            setTimeout(function () {
                openWorkspaceChooser(null);
            }, 800);
        } catch (e) {
            /* no-op */
        }
    }

    // 列表缓存(供标签显示客户名)
    fetchWorkspaceClients().then((l) => {
        window._workspaceClientsCache = l;
        renderWorkspaceControl();
        _maybeLoginPrompt();
    });

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('workspace-switcher', renderWorkspaceControl);
    }
})();
