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
/* global escapeHtml */
(function () {
    'use strict';

    const ERP_OPTIONS = ['flowaccount', 'peak', 'xero', 'quickbooks', 'express'];
    const ERP_LABELS = {
        flowaccount: 'FlowAccount',
        peak: 'PEAK',
        xero: 'Xero',
        quickbooks: 'QuickBooks',
        express: 'Express',
    };
    const CATEGORY_OPTIONS = [
        'expense_office',
        'expense_travel',
        'expense_utility',
        'asset_inventory',
        'asset_fixed',
        'liability_ap',
        'revenue_sales',
        'revenue_service',
        'other',
    ];
    const TAX_KIND_OPTIONS = ['vat_7', 'vat_0', 'vat_exempt', 'wht_1', 'wht_3', 'wht_5', 'non_vat'];
    const TEST_USER_ID = '468b50c1-5593-4fd6-990d-515ce8085563'; // skin

    let _state = {
        sub: 'clients', // clients / accounts / taxes / products
        loaded: { clients: false, accounts: false, taxes: false, products: false },
        items: { clients: [], accounts: [], taxes: [], products: [] },
        clientList: [], // 客户下拉数据 · 一次拿
        clientLoaded: false,
        addingNew: { clients: false, accounts: false, taxes: false, products: false },
        bound: false,
    };

    function _isOwner() {
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        return !!(u && (u.role === 'owner' || u.is_super_admin));
    }
    function _isSkin() {
        const u = typeof _userInfo !== 'undefined' ? _userInfo : null;
        return !!(u && u.id === TEST_USER_ID);
    }

    function _esc(s) {
        return typeof escapeHtml === 'function'
            ? escapeHtml(s == null ? '' : String(s))
            : String(s == null ? '' : s);
    }
    function _toast(msg, kind) {
        try {
            if (typeof showToast === 'function') showToast(msg, kind || 'info');
        } catch (e) {}
    }

    // ─── 显隐 owner-only nav 入口(借用现有 .set-tab-owner-only)
    function _applyVisibility() {
        // 已由 access-log 的 _applyVisibility 同名 class 控制 · 这里不重复
    }

    // ─── 拉数据 ────────────────────────────────────
    async function _fetchSub(sub, force) {
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

    async function _fetchClients(force) {
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
                (c) => c.is_active !== false
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
        const sub = _state.sub;
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
        items.forEach(function (it) {
            html += _renderItemRow(sub, it, readonly);
        });
        host.innerHTML = html;
    }

    function _renderHead(sub) {
        if (sub === 'clients') {
            return (
                '<div class="erp-map-row erp-map-head row-clients">' +
                '<div>' +
                _esc(t('erp-map-col-client')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp-code')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-notes')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-actions')) +
                '</div>' +
                '</div>'
            );
        }
        if (sub === 'accounts') {
            return (
                '<div class="erp-map-row erp-map-head row-accounts">' +
                '<div>' +
                _esc(t('erp-map-col-erp')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-category')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp-code')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp-name')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-notes')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-actions')) +
                '</div>' +
                '</div>'
            );
        }
        if (sub === 'products') {
            return (
                '<div class="erp-map-row erp-map-head row-products">' +
                '<div>' +
                _esc(t('erp-map-col-item-name')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp-product-code')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-erp-name')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-notes')) +
                '</div>' +
                '<div>' +
                _esc(t('erp-map-col-actions')) +
                '</div>' +
                '</div>'
            );
        }
        // taxes
        return (
            '<div class="erp-map-row erp-map-head row-taxes">' +
            '<div>' +
            _esc(t('erp-map-col-erp')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-tax')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-erp-tax-code')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-notes')) +
            '</div>' +
            '<div>' +
            _esc(t('erp-map-col-actions')) +
            '</div>' +
            '</div>'
        );
    }

    function _erpSelect(currentValue, fieldKey) {
        let s = '<select class="form-input" data-erp-field="' + fieldKey + '">';
        s += '<option value="">' + _esc(t('erp-map-pick-erp')) + '</option>';
        ERP_OPTIONS.forEach(function (k) {
            const sel = k === currentValue ? ' selected' : '';
            s += '<option value="' + k + '"' + sel + '>' + _esc(ERP_LABELS[k]) + '</option>';
        });
        s += '</select>';
        return s;
    }

    function _clientSelect(currentClientId) {
        let s = '<select class="form-input" data-erp-field="client_id">';
        s += '<option value="">' + _esc(t('erp-map-pick-client')) + '</option>';
        (_state.clientList || []).forEach(function (c) {
            const sel = String(c.id) === String(currentClientId) ? ' selected' : '';
            s +=
                '<option value="' +
                c.id +
                '"' +
                sel +
                '>' +
                _esc(c.name || '#' + c.id) +
                '</option>';
        });
        s += '</select>';
        return s;
    }

    function _categorySelect(currentValue) {
        let s = '<select class="form-input" data-erp-field="pearnly_category">';
        s += '<option value="">' + _esc(t('erp-map-pick-cat')) + '</option>';
        CATEGORY_OPTIONS.forEach(function (k) {
            const sel = k === currentValue ? ' selected' : '';
            s +=
                '<option value="' + k + '"' + sel + '>' + _esc(t('erp-map-cat-' + k)) + '</option>';
        });
        s += '</select>';
        return s;
    }

    function _taxKindSelect(currentValue) {
        let s = '<select class="form-input" data-erp-field="pearnly_tax_kind">';
        s += '<option value="">' + _esc(t('erp-map-pick-tax')) + '</option>';
        TAX_KIND_OPTIONS.forEach(function (k) {
            const sel = k === currentValue ? ' selected' : '';
            s +=
                '<option value="' + k + '"' + sel + '>' + _esc(t('erp-map-tax-' + k)) + '</option>';
        });
        s += '</select>';
        return s;
    }

    function _renderAddRow(sub) {
        const saveBtn =
            '<button class="btn btn-primary" type="button" data-erp-save="new" style="padding:6px 12px;height:32px;">' +
            _esc(t('erp-map-save')) +
            '</button>';
        if (sub === 'clients') {
            return (
                '<div class="erp-map-row erp-map-row-add row-clients" data-erp-row="new">' +
                '<div data-label="' +
                _esc(t('erp-map-col-client')) +
                '">' +
                _clientSelect('') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp')) +
                '">' +
                _erpSelect('', 'erp_type') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-code')) +
                '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
                _esc(t('erp-map-ph-erp-code')) +
                '"></div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-notes')) +
                '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
                _esc(t('erp-map-ph-notes')) +
                '"></div>' +
                '<div>' +
                saveBtn +
                '</div>' +
                '</div>'
            );
        }
        if (sub === 'accounts') {
            return (
                '<div class="erp-map-row erp-map-row-add row-accounts" data-erp-row="new">' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp')) +
                '">' +
                _erpSelect('', 'erp_type') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-category')) +
                '">' +
                _categorySelect('') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-code')) +
                '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
                _esc(t('erp-map-ph-acc-code')) +
                '"></div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-name')) +
                '"><input type="text" class="form-input" data-erp-field="erp_name" placeholder="' +
                _esc(t('erp-map-ph-acc-name')) +
                '"></div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-notes')) +
                '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
                _esc(t('erp-map-ph-notes')) +
                '"></div>' +
                '<div>' +
                saveBtn +
                '</div>' +
                '</div>'
            );
        }
        // taxes
        return (
            '<div class="erp-map-row erp-map-row-add row-taxes" data-erp-row="new">' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            _erpSelect('', 'erp_type') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-tax')) +
            '">' +
            _taxKindSelect('') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-tax-code')) +
            '"><input type="text" class="form-input" data-erp-field="erp_code" placeholder="' +
            _esc(t('erp-map-ph-tax-code')) +
            '"></div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '"><input type="text" class="form-input" data-erp-field="notes" placeholder="' +
            _esc(t('erp-map-ph-notes')) +
            '"></div>' +
            '<div>' +
            saveBtn +
            '</div>' +
            '</div>'
        );
    }

    function _renderItemRow(sub, it, readonly) {
        const delBtn = readonly
            ? ''
            : '<button class="erp-map-del-btn" type="button" data-erp-del="' +
              _esc(it.id) +
              '" title="' +
              _esc(t('erp-map-delete')) +
              '">' +
              '<svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 11h6l1-11"/></svg>' +
              '</button>';
        const erpBadge =
            '<span class="erp-map-erp-badge">' +
            _esc(ERP_LABELS[it.erp_type] || it.erp_type) +
            '</span>';
        if (sub === 'clients') {
            return (
                '<div class="erp-map-row row-clients">' +
                '<div data-label="' +
                _esc(t('erp-map-col-client')) +
                '" class="erp-map-cell-name">' +
                _esc(it.client_name || '#' + it.client_id) +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp')) +
                '">' +
                erpBadge +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-code')) +
                '" class="erp-map-code">' +
                _esc(it.erp_code || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-notes')) +
                '">' +
                _esc(it.notes || '') +
                '</div>' +
                '<div>' +
                delBtn +
                '</div>' +
                '</div>'
            );
        }
        if (sub === 'accounts') {
            const catLabel =
                t('erp-map-cat-' + (it.pearnly_category || 'other')) || it.pearnly_category;
            return (
                '<div class="erp-map-row row-accounts">' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp')) +
                '">' +
                erpBadge +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-category')) +
                '" class="erp-map-cell-name">' +
                _esc(catLabel) +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-code')) +
                '" class="erp-map-code">' +
                _esc(it.erp_code || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-name')) +
                '">' +
                _esc(it.erp_name || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-notes')) +
                '">' +
                _esc(it.notes || '') +
                '</div>' +
                '<div>' +
                delBtn +
                '</div>' +
                '</div>'
            );
        }
        if (sub === 'products') {
            return (
                '<div class="erp-map-row row-products">' +
                '<div data-label="' +
                _esc(t('erp-map-col-item-name')) +
                '" class="erp-map-cell-name">' +
                _esc(it.item_name || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-product-code')) +
                '" class="erp-map-code">' +
                _esc(it.erp_code || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-erp-name')) +
                '">' +
                _esc(it.erp_name || '') +
                '</div>' +
                '<div data-label="' +
                _esc(t('erp-map-col-notes')) +
                '">' +
                _esc(it.notes || '') +
                '</div>' +
                '<div>' +
                delBtn +
                '</div>' +
                '</div>'
            );
        }
        // taxes
        const taxLabel = t('erp-map-tax-' + (it.pearnly_tax_kind || '')) || it.pearnly_tax_kind;
        return (
            '<div class="erp-map-row row-taxes">' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp')) +
            '">' +
            erpBadge +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-tax')) +
            '" class="erp-map-cell-name">' +
            '<span class="erp-map-tax-badge">' +
            _esc(taxLabel) +
            '</span></div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-erp-tax-code')) +
            '" class="erp-map-code">' +
            _esc(it.erp_code || '') +
            '</div>' +
            '<div data-label="' +
            _esc(t('erp-map-col-notes')) +
            '">' +
            _esc(it.notes || '') +
            '</div>' +
            '<div>' +
            delBtn +
            '</div>' +
            '</div>'
        );
    }

    // ─── 操作 ──────────────────────────────────────
    async function _save(rowEl) {
        const sub = _state.sub;
        const fields = {};
        rowEl.querySelectorAll('[data-erp-field]').forEach(function (el) {
            fields[el.dataset.erpField] = (el.value || '').trim();
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

    async function _delete(id) {
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
            await _fetchSub(sub, true);
            _renderTable();
            _toast(t('erp-map-deleted-toast'), 'success');
        } catch (e) {
            _toast(t('erp-map-delete-fail'), 'error');
        }
    }

    // ─── 进入 tab + 切 sub-tab ─────────────────────
    async function _enterTab() {
        await _fetchClients(false);
        await _fetchSub(_state.sub, false);
        _renderRoot();
    }

    function _switchSub(sub) {
        if (sub === _state.sub) return;
        _state.sub = sub;
        _state.addingNew[sub] = false;
        // 切 sub 时清旧 sub 的 add 状态
        ['clients', 'accounts', 'taxes', 'products'].forEach(function (s) {
            if (s !== sub) _state.addingNew[s] = false;
        });
        // 更新 sub-tab 高亮
        document.querySelectorAll('.erp-map-subtab').forEach(function (b) {
            b.classList.toggle('active', b.dataset.erpSubtab === sub);
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
            const erpSubBtn = ev.target.closest('.erp-subtab[data-erp-subtab]');
            if (erpSubBtn) {
                ev.preventDefault();
                const target = erpSubBtn.dataset.erpSubtab; // "connect" | "mappings"
                document.querySelectorAll('.erp-subtab').forEach(function (b) {
                    b.classList.toggle('active', b.dataset.erpSubtab === target);
                });
                document.querySelectorAll('.erp-subpanel').forEach(function (p) {
                    p.classList.toggle('active', p.dataset.erpSubpanel === target);
                });
                if (target === 'mappings') {
                    setTimeout(_enterTab, 50);
                }
                return;
            }
            // 映射内部 sub-tab 切换(客户 / 科目 / 税码)
            const subBtn = ev.target.closest('.erp-map-subtab[data-erp-subtab]');
            if (subBtn) {
                ev.preventDefault();
                _switchSub(subBtn.dataset.erpSubtab);
                return;
            }
            // 加新行
            const addBtn = ev.target.closest('#erp-map-add-btn');
            if (addBtn) {
                ev.preventDefault();
                if (!_isOwner()) return;
                _state.addingNew[_state.sub] = true;
                _renderTable();
                return;
            }
            // 保存
            const saveBtn = ev.target.closest('[data-erp-save="new"]');
            if (saveBtn) {
                ev.preventDefault();
                const row = saveBtn.closest('[data-erp-row="new"]');
                if (row) _save(row);
                return;
            }
            // 删除
            const delBtn = ev.target.closest('[data-erp-del]');
            if (delBtn) {
                ev.preventDefault();
                _delete(delBtn.dataset.erpDel);
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
        document.querySelectorAll('.erp-map-subtab').forEach(function (b) {
            const k = 'erp-map-subtab-' + b.dataset.erpSubtab;
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
