// ============================================================
// REFACTOR-C1 (2026-05-27) · 客户分配 modal(老板分客户给员工)从 home.js 抽出为 ES module
//
// 来源:home.js L18163-18326(v118.28.1)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑。
// 入口 window.openAssignClientsModal 由 home.js 事件委托(L1742 · [data-assign-clients])
//   经 window 调用 · 抽成 defer module 后仍安全(用户交互远晚于模块加载)。
// 依赖的全局(home.js 暴露 · bare 调 · 不 import):t / escapeHtml / showToast / apiGet /
//   apiPost / window.subscribeI18n。
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================
/* global apiGet, apiPost, escapeHtml, loadTeamList */
// ============================================================
// v118.28.1 · 客户分配 modal(老板分客户给员工)
// 使用 subscribeI18n · 切语言时 modal 重渲
// ============================================================
(function () {
    'use strict';
    let _state = {
        employeeId: null,
        employeeName: '',
        clients: [],
        selected: new Set(),
        opened: false,
    };

    function _modal() {
        return document.getElementById('assign-clients-modal');
    }
    function _list() {
        return document.getElementById('assign-clients-list');
    }
    function _selAll() {
        return document.getElementById('assign-select-all');
    }
    function _countLabel() {
        return document.getElementById('assign-selected-count');
    }
    function _target() {
        return document.getElementById('assign-modal-target');
    }

    function _renderList() {
        const el = _list();
        if (!el) return;
        if (!_state.clients.length) {
            el.innerHTML =
                '<div class="assign-empty">' +
                escapeHtml(t('assign-no-clients') || '暂无客户 · 请先到「客户管理」添加') +
                '</div>';
            return;
        }
        el.innerHTML = _state.clients
            .map((c) => {
                const cid = String(c.id);
                const checked = _state.selected.has(cid) ? 'checked' : '';
                const name = escapeHtml(c.name || c.label || '#' + cid);
                const code = c.code
                    ? '<span class="assign-row-code">' + escapeHtml(c.code) + '</span>'
                    : '';
                return (
                    '<label class="assign-row"><input type="checkbox" data-cid="' +
                    escapeHtml(cid) +
                    '" ' +
                    checked +
                    '><span class="assign-row-name">' +
                    name +
                    '</span>' +
                    code +
                    '</label>'
                );
            })
            .join('');
        _refreshCount();
    }

    function _refreshCount() {
        const lab = _countLabel();
        if (lab) {
            const fmt = t('assign-selected-count') || '已选 {n} / {total}';
            lab.textContent = fmt
                .replace('{n}', _state.selected.size)
                .replace('{total}', _state.clients.length);
        }
        const sa = _selAll();
        if (sa)
            sa.checked =
                _state.clients.length > 0 && _state.selected.size === _state.clients.length;
    }

    function _renderTarget() {
        const el = _target();
        if (el) el.textContent = _state.employeeName ? ' · ' + _state.employeeName : '';
    }

    async function open(employeeId, employeeName) {
        _state.employeeId = employeeId;
        _state.employeeName = employeeName || '';
        _state.opened = true;
        _state.selected = new Set();
        _state.clients = [];
        _renderTarget();
        const el = _list();
        if (el)
            el.innerHTML =
                '<div class="assign-empty">' +
                escapeHtml(t('assign-loading') || '加载中...') +
                '</div>';
        const m = _modal();
        if (m) m.style.display = 'flex';

        try {
            const [allClients, assigned] = await Promise.all([
                apiGet('/api/clients?include_inactive=false'),
                apiGet('/api/team/employees/' + encodeURIComponent(employeeId) + '/assignments'),
            ]);
            _state.clients = (allClients && allClients.clients) || [];
            const ids = (assigned && assigned.client_ids) || [];
            _state.selected = new Set(ids.map(String));
            _renderList();
        } catch (err) {
            console.error('[assign-clients] load failed', err);
            const el2 = _list();
            if (el2)
                el2.innerHTML =
                    '<div class="assign-empty">' +
                    escapeHtml(t('assign-load-failed') || '加载失败 · 请重试') +
                    '</div>';
        }
    }

    function close() {
        _state.opened = false;
        const m = _modal();
        if (m) m.style.display = 'none';
    }

    async function save() {
        if (!_state.employeeId) return;
        const ids = Array.from(_state.selected)
            .map((s) => parseInt(s, 10))
            .filter((n) => !isNaN(n));
        const btn = document.getElementById('assign-modal-save');
        if (btn) btn.disabled = true;
        try {
            const r = await apiPost(
                '/api/team/employees/' + encodeURIComponent(_state.employeeId) + '/assignments',
                { client_ids: ids }
            );
            if (r && r.ok !== false) {
                showToast(
                    (t('assign-saved') || '已保存 {n} 个客户分配').replace('{n}', ids.length),
                    'success'
                );
                close();
                if (typeof loadTeamList === 'function') loadTeamList();
            } else {
                showToast(t('assign-save-failed') || '保存失败', 'error');
            }
        } catch (err) {
            console.error('[assign-clients] save failed', err);
            showToast(t('assign-save-failed') || '保存失败', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    function _bindOnce() {
        const m = _modal();
        if (!m || m.dataset.bound === '1') return;
        m.dataset.bound = '1';

        const closeBtn = document.getElementById('assign-modal-close');
        if (closeBtn) closeBtn.addEventListener('click', close);
        const cancelBtn = document.getElementById('assign-modal-cancel');
        if (cancelBtn) cancelBtn.addEventListener('click', close);
        const saveBtn = document.getElementById('assign-modal-save');
        if (saveBtn) saveBtn.addEventListener('click', save);

        // overlay 点击空白关
        m.addEventListener('click', function (ev) {
            if (ev.target === m) close();
        });

        // 全选
        const sa = _selAll();
        if (sa)
            sa.addEventListener('change', function () {
                if (sa.checked) {
                    _state.selected = new Set(_state.clients.map((c) => String(c.id)));
                } else {
                    _state.selected = new Set();
                }
                _renderList();
            });

        // 单项 toggle(事件委托)
        const list = _list();
        if (list)
            list.addEventListener('change', function (ev) {
                const cb = ev.target.closest('input[type="checkbox"][data-cid]');
                if (!cb) return;
                const cid = cb.dataset.cid;
                if (cb.checked) _state.selected.add(cid);
                else _state.selected.delete(cid);
                _refreshCount();
            });
    }

    function _rerenderAll() {
        if (!_state.opened) return;
        _renderTarget();
        _renderList();
    }

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('assign-clients-modal', _rerenderAll);
    }

    // 暴露 open 给事件代理
    window.openAssignClientsModal = function (empId, empName) {
        _bindOnce();
        open(empId, empName);
    };
})();
