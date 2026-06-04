// ============================================================
// REFACTOR-C1 (2026-05-27) · ERP 字段映射底座 erp-mappings 从 home.js 抽出为 ES module
//
// 来源:home.js L11805-12280 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
/* eslint-disable no-useless-assignment -- verbatim 防御式初始化 `let payload = {}` 从 home.js 原样搬来 · 0 改逻辑 */

// ============================================================
// v118.27.0 · ERP 字段映射底座(客户 / 科目 / 税码 3 个 sub-tab)
// v118.27.0.1 · 搬到「自动化 → ERP 对接 → 字段映射」子面板内
// 老板可写 / 员工只读 / skin 白名单一键插测试映射
// ============================================================
import {
    _state,
    _esc,
    _toast,
    _isOwner,
    _isSkin,
    _renderHead,
    _renderAddRow,
    _renderItemRow,
} from './erp-mappings-render.js'; // REFACTOR-WB-modularize · 视图层拆出
type ErpSub = keyof typeof _state.loaded;
(function () {
    'use strict';

    // ─── 显隐 owner-only nav 入口(借用现有 .set-tab-owner-only)
    // @ts-expect-error TS6133 verbatim 占位空函数(同名 class 已控显隐)· 0 改逻辑保留
    function _applyVisibility() {
        // 已由 access-log 的 _applyVisibility 同名 class 控制 · 这里不重复
    }

    // ─── 拉数据 ────────────────────────────────────
    async function _fetchSub(sub: ErpSub, force?: boolean) {
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        if (_state.loaded[sub] && !force) return;
        try {
            const r = await fetch('/api/erp/mappings/' + sub, {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            const data = await r.json();
            _state.items[sub] = data.items || [];
            _state.loaded[sub] = true;
        } catch (e) {
            _state.items[sub] = [];
            _state.loaded[sub] = false;
        }
    }

    async function _fetchClients(force?: boolean) {
        if (_state.clientLoaded && !force) return;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const r = await fetch('/api/clients?include_inactive=false', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            const data = await r.json();
            _state.clientList = (data.clients || data.items || []).filter(
                (c: { is_active?: boolean }) => c.is_active !== false
            );
            _state.clientLoaded = true;
        } catch (e) {
            _state.clientList = [];
        }
    }

    // ─── 渲染 ──────────────────────────────────────
    function _renderRoot() {
        const wrap = document.getElementById('erp-map-pane-wrap');
        if (!wrap) return;
        // 切 owner / member readonly banner
        const readonly = !_isOwner();
        let html = '';
        if (readonly) {
            html +=
                '<div class="erp-map-readonly-banner">' +
                '<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="8"/><path d="M10 6v4M10 13v0.01"/></svg>' +
                _esc(t('erp-map-readonly-tip')) +
                '</div>';
        }
        html += '<div class="erp-map-toolbar">';
        if (!readonly && _state.sub !== 'products') {
            html +=
                '<button class="btn btn-primary" type="button" id="erp-map-add-btn" data-i18n="erp-map-add-row">' +
                _esc(t('erp-map-add-row')) +
                '</button>';
        }
        html += '</div>';
        html += '<div class="erp-map-table" id="erp-map-table-host"></div>';
        wrap.innerHTML = html;
        _renderTable();

        // skin 白名单 dev 工具栏显隐
        const dev = document.getElementById('erp-map-dev-bar');
        if (dev) dev.style.display = _isOwner() && _isSkin() ? '' : 'none';
    }

    function _renderTable() {
        const host = document.getElementById('erp-map-table-host');
        if (!host) return;
        const sub = _state.sub as ErpSub;
        const items = _state.items[sub] || [];
        const adding = _state.addingNew[sub];
        const readonly = !_isOwner();

        // 空状态(且不在加新行)
        if (!items.length && !adding) {
            host.innerHTML =
                '<div class="erp-map-empty">' +
                '<strong>' +
                _esc(t('erp-map-empty-' + sub)) +
                '</strong>' +
                _esc(t('erp-map-empty-' + sub + '-sub')) +
                '</div>';
            return;
        }

        let html = '';
        // 表头
        html += _renderHead(sub);
        // 加新行
        if (adding && !readonly) {
            html += _renderAddRow(sub);
        }
        // 数据行
        (items as unknown[]).forEach(function (it: unknown) {
            html += _renderItemRow(sub, it, readonly);
        });
        host.innerHTML = html;
    }

    // ─── 操作 ──────────────────────────────────────
    async function _save(rowEl: HTMLElement) {
        const sub = _state.sub as ErpSub;
        const fields: Record<string, string> = {};
        rowEl.querySelectorAll('[data-erp-field]').forEach(function (el: Element) {
            fields[(el as HTMLElement).dataset.erpField as string] = (
                (el as HTMLInputElement).value || ''
            ).trim();
        });
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;

        let payload = {};
        let url = '/api/erp/mappings/' + sub;
        if (sub === 'clients') {
            if (!fields.client_id || !fields.erp_type || !fields.erp_code) {
                _toast(t('erp-map-save-fail'), 'error');
                return;
            }
            payload = {
                client_id: parseInt(fields.client_id, 10),
                erp_type: fields.erp_type,
                erp_code: fields.erp_code,
                notes: fields.notes || '',
            };
        } else if (sub === 'accounts') {
            if (!fields.erp_type || !fields.pearnly_category || !fields.erp_code) {
                _toast(t('erp-map-save-fail'), 'error');
                return;
            }
            payload = {
                erp_type: fields.erp_type,
                pearnly_category: fields.pearnly_category,
                erp_code: fields.erp_code,
                erp_name: fields.erp_name || '',
                notes: fields.notes || '',
            };
        } else {
            if (!fields.erp_type || !fields.pearnly_tax_kind || !fields.erp_code) {
                _toast(t('erp-map-save-fail'), 'error');
                return;
            }
            payload = {
                erp_type: fields.erp_type,
                pearnly_tax_kind: fields.pearnly_tax_kind,
                erp_code: fields.erp_code,
                notes: fields.notes || '',
            };
        }
        try {
            const r = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + tk },
                body: JSON.stringify(payload),
            });
            if (!r.ok) throw new Error('http_' + r.status);
            _state.addingNew[sub] = false;
            await _fetchSub(sub, true);
            _renderTable();
            _toast(t('erp-map-saved-toast'), 'success');
        } catch (e) {
            _toast(t('erp-map-save-fail'), 'error');
        }
    }

    async function _delete(id: string) {
        const ok = await window.pearnlyConfirm(t('erp-map-confirm-delete'));
        if (!ok) return;
        const sub = _state.sub;
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/erp/mappings/' + sub + '/' + encodeURIComponent(id), {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (!r.ok) throw new Error('http_' + r.status);
            await _fetchSub(sub as ErpSub, true);
            _renderTable();
            _toast(t('erp-map-deleted-toast'), 'success');
        } catch (e) {
            _toast(t('erp-map-delete-fail'), 'error');
        }
    }

    // ─── 进入 tab + 切 sub-tab ─────────────────────
    async function _enterTab() {
        await _fetchClients(false);
        await _fetchSub(_state.sub as ErpSub, false);
        _renderRoot();
    }

    function _switchSub(sub: ErpSub) {
        if (sub === _state.sub) return;
        _state.sub = sub;
        _state.addingNew[sub] = false;
        // 切 sub 时清旧 sub 的 add 状态
        ['clients', 'accounts', 'taxes', 'products'].forEach(function (s) {
            if (s !== sub) _state.addingNew[s as ErpSub] = false;
        });
        // 更新 sub-tab 高亮
        document.querySelectorAll('.erp-map-subtab').forEach(function (b: Element) {
            b.classList.toggle('active', (b as HTMLElement).dataset.erpSubtab === sub);
        });
        _fetchSub(sub, false).then(function () {
            _renderRoot();
        });
    }

    // ─── 事件代理 ─────────────────────────────────
    function _bind() {
        if (_state.bound) return;
        _state.bound = true;

        // 进入 ERP 对接 panel 内的「字段映射」子面板时拉数据
        document.addEventListener('click', function (ev) {
            const erpSubBtn = (ev.target as HTMLElement).closest('.erp-subtab[data-erp-subtab]');
            if (erpSubBtn) {
                ev.preventDefault();
                const target = (erpSubBtn as HTMLElement).dataset.erpSubtab; // "connect" | "mappings"
                document.querySelectorAll('.erp-subtab').forEach(function (b: Element) {
                    b.classList.toggle('active', (b as HTMLElement).dataset.erpSubtab === target);
                });
                document.querySelectorAll('.erp-subpanel').forEach(function (p: Element) {
                    p.classList.toggle('active', (p as HTMLElement).dataset.erpSubpanel === target);
                });
                if (target === 'mappings') {
                    setTimeout(_enterTab, 50);
                }
                return;
            }
            // 映射内部 sub-tab 切换(客户 / 科目 / 税码)
            const subBtn = (ev.target as HTMLElement).closest('.erp-map-subtab[data-erp-subtab]');
            if (subBtn) {
                ev.preventDefault();
                _switchSub((subBtn as HTMLElement).dataset.erpSubtab as ErpSub);
                return;
            }
            // 加新行
            const addBtn = (ev.target as HTMLElement).closest('#erp-map-add-btn');
            if (addBtn) {
                ev.preventDefault();
                if (!_isOwner()) return;
                _state.addingNew[_state.sub as ErpSub] = true;
                _renderTable();
                return;
            }
            // 保存
            const saveBtn = (ev.target as HTMLElement).closest('[data-erp-save="new"]');
            if (saveBtn) {
                ev.preventDefault();
                const row = saveBtn.closest('[data-erp-row="new"]');
                if (row) _save(row as HTMLElement);
                return;
            }
            // 删除
            const delBtn = (ev.target as HTMLElement).closest('[data-erp-del]');
            if (delBtn) {
                ev.preventDefault();
                _delete((delBtn as HTMLElement).dataset.erpDel as string);
                return;
            }
        });
    }

    function _rerenderAll() {
        // 切语言重渲(若已进 tab)
        const wrap = document.getElementById('erp-map-pane-wrap');
        if (wrap && wrap.children.length > 0) {
            _renderRoot();
        }
        // sub-tab label 也需要更新
        document.querySelectorAll('.erp-map-subtab').forEach(function (b: Element) {
            const k = 'erp-map-subtab-' + (b as HTMLElement).dataset.erpSubtab;
            const lbl = t(k);
            if (lbl && lbl !== k) b.textContent = lbl;
        });
    }

    // 初始化
    _bind();
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('erp-mappings', _rerenderAll);
    }
})();
