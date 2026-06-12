// ============================================================
// Workspace 账套主体切换器(顶栏富下拉 · "在为哪家公司做账")。
//
// 账套主体 = 硬边界:业务必须归属一个主体(个人模式已退场)。无 active 套账 → 套账硬门(workspace-gate)
// 强制选择,不在此自动猜测(1 个也要明确选)。本模块只管顶栏切换器 + active 读写 + 惰性守卫。
//
// 与发票买方(history.client_id)是两个维度。数据源 GET /api/workspace/clients。
// 暴露(window):getActiveWorkspaceClientId / setActiveWorkspaceClientId / requireWorkspace /
//   openWorkspaceChooser(→硬门)/ renderWorkspaceControl / fetchWorkspaceClients / wsEmptyHtml。
// 事件:pearnly:workspace-changed。顶栏下拉 orgPop 照 01-交互原型逐屏搬。
// ============================================================
import { injectStyle } from './acct-common.js';
import { WSG_CSS, wsgIcon, wsgInitials } from './workspace-gate-html.js';

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

    const _esc = (s: unknown) =>
        String(s == null ? '' : s).replace(/[&<>"']/g, (m: string) => {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[
                m as '&' | '<' | '>' | '"' | "'"
            ];
        });

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
        if (id == null || id === 0) localStorage.removeItem(LS_ID);
        else localStorage.setItem(LS_ID, String(id));
        if (String(old) !== String(id)) _emit(id);
    }

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

    // 惰性守卫:已选 → onOk();否则起套账硬门(不自动选)。
    async function requireWorkspace(onOk: (() => void) | null) {
        if (getActiveWorkspaceClientId() != null) {
            if (typeof onOk === 'function') onOk();
            return true;
        }
        if (typeof window.showWorkspaceGate === 'function') window.showWorkspaceGate();
        return false;
    }

    // openWorkspaceChooser:对外保留名,统一走硬门(company-profile 空态 / wsEmptyHtml 按钮调用)。
    function openWorkspaceChooser() {
        if (typeof window.showWorkspaceGate === 'function') window.showWorkspaceGate();
    }

    // ---------- 顶栏富下拉切换器(orgPop · 照 01)----------
    type Client = { id: number; name?: string; tax_id?: string; subject_type?: string };
    let _popOpen = false;
    let _popKw = '';

    function _clients(): Client[] {
        return (window._workspaceClientsCache as Client[]) || [];
    }

    function _subline(c: Client): string {
        if (String(c.subject_type) === 'personal')
            return _esc(_t('wsg-personal-sub', '个人主体 · 仅开收据'));
        return c.tax_id
            ? _esc(_t('wsg-tax-prefix', '税号')) + ' ' + _esc(c.tax_id)
            : _esc(_t('wsg-no-tax', '未填税号'));
    }

    function _orgPopHtml(): string {
        const list = _clients();
        const active = getActiveWorkspaceClientId();
        const kw = _popKw.trim().toLowerCase();
        const filtered = kw
            ? list.filter(
                  (c) =>
                      (c.name || '').toLowerCase().includes(kw) ||
                      (c.tax_id || '').toLowerCase().includes(kw)
              )
            : list;
        const items = filtered.length
            ? filtered
                  .map((c) => {
                      const on = active != null && Number(active) === Number(c.id);
                      return (
                          `<button class="orgsw-item${on ? ' on' : ''}" data-orgpick="${c.id}">` +
                          `<span class="oco">${wsgInitials(c.name || '#' + c.id)}</span>` +
                          `<span class="oinfo"><span class="onm">${_esc(c.name || '#' + c.id)}</span>` +
                          `<span class="ocm">${_subline(c)}</span></span>` +
                          (on ? wsgIcon('check', 'ochk') : '') +
                          '</button>'
                      );
                  })
                  .join('')
            : `<div class="orgsw-empty">${_esc(_t('wsg-pop-nomatch', '无匹配主体'))}</div>`;
        const foot = _isOwner()
            ? `<div class="orgsw-foot"><button class="orgsw-fa" data-orgcreate="1">${wsgIcon('plus')}${_esc(_t('wsg-create', '新建主体'))}</button>` +
              `<button class="orgsw-fa" data-orgmanage="1">${wsgIcon('users')}${_esc(_t('wsg-manage-all', '管理全部客户'))}</button></div>`
            : '';
        return (
            '<div class="orgsw-pop" id="orgsw-pop">' +
            `<div class="orgsw-srch">${wsgIcon('search')}<input id="orgsw-srch-in" placeholder="${_esc(_t('wsg-search-ph', '搜索公司 / 税号'))}" value="${_esc(_popKw)}"></div>` +
            `<div class="orgsw-cap">${_esc(_t('wsg-my-subjects', '我管理的主体').replace('{n}', String(list.length)))}</div>` +
            `<div class="orgsw-list">${items}</div>` +
            foot +
            '</div>'
        );
    }

    function renderWorkspaceControl(el?: HTMLElement | null) {
        const root = el || document.getElementById('workspace-switcher-root');
        if (!root) return;
        injectStyle('wsg-css', WSG_CSS);
        const id = getActiveWorkspaceClientId();
        const list = _clients();
        const c = list.find((x) => Number(x.id) === Number(id));
        const label = id != null && c ? c.name || '#' + id : _t('ws-empty-pick', '选择账套');
        const coInit = id != null && c ? wsgInitials(c.name || '#' + id) : wsgIcon('building');
        root.innerHTML =
            '<div class="orgsw">' +
            `<button class="wsw" id="ws-ctrl-btn" type="button"><span class="wsw-co">${coInit}</span>` +
            `<span class="wsw-nm">${_esc(label)}</span>${wsgIcon('chev')}</button>` +
            (_popOpen ? _orgPopHtml() : '') +
            '</div>';
    }

    // 顶栏下拉的事件委托(单次绑定到 document)。
    function _bindPop() {
        document.addEventListener('click', (e) => {
            const target = e.target as HTMLElement;
            if (target.closest('#ws-ctrl-btn')) {
                _popOpen = !_popOpen;
                renderWorkspaceControl();
                return;
            }
            const pick = target.closest('[data-orgpick]') as HTMLElement | null;
            if (pick) {
                setActiveWorkspaceClientId(Number(pick.dataset.orgpick));
                _popOpen = false;
                renderWorkspaceControl();
                return;
            }
            if (target.closest('[data-orgcreate]')) {
                _popOpen = false;
                renderWorkspaceControl();
                // 系统内创建走统一专屏;建好切到新主体(active 变更发事件 → 自动重载)。
                if (typeof window.openSubjectCreate === 'function') {
                    window.openSubjectCreate({
                        onCreated: (id) =>
                            fetchWorkspaceClients().then((l) => {
                                window._workspaceClientsCache = l;
                                setActiveWorkspaceClientId(Number(id));
                                renderWorkspaceControl();
                            }),
                    });
                }
                return;
            }
            if (target.closest('[data-orgmanage]')) {
                _popOpen = false;
                renderWorkspaceControl();
                if (typeof window.routeTo === 'function') window.routeTo('clients');
                return;
            }
            // 点下拉外 → 收起(搜索框内点击不收)。
            if (_popOpen && !target.closest('#orgsw-pop') && !target.closest('#ws-ctrl-btn')) {
                _popOpen = false;
                renderWorkspaceControl();
            }
        });
        document.addEventListener('input', (e) => {
            const inp = e.target as HTMLInputElement;
            if (inp && inp.id === 'orgsw-srch-in') {
                _popKw = inp.value;
                const pop = document.getElementById('orgsw-pop');
                if (pop) pop.outerHTML = _orgPopHtml();
                const re = document.getElementById('orgsw-srch-in') as HTMLInputElement | null;
                if (re) {
                    re.focus();
                    re.setSelectionRange(re.value.length, re.value.length);
                }
            }
        });
    }

    window.addEventListener('pearnly:workspace-changed', () => renderWorkspaceControl());

    // ---------- 暴露 ----------
    window.getActiveWorkspaceClientId = getActiveWorkspaceClientId;
    window.setActiveWorkspaceClientId = setActiveWorkspaceClientId;
    window.requireWorkspace = requireWorkspace;
    window.openWorkspaceChooser = openWorkspaceChooser;
    window.renderWorkspaceControl = renderWorkspaceControl;
    window.fetchWorkspaceClients = fetchWorkspaceClients;

    // 列表缓存(供顶栏显示)· 不自动选中(硬门负责选择)。
    fetchWorkspaceClients().then((l) => {
        window._workspaceClientsCache = l;
        renderWorkspaceControl();
    });
    _bindPop();

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('workspace-switcher', renderWorkspaceControl);
    }
})();
