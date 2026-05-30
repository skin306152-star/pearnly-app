// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送异常块 从 exceptions.js 抽出为独立 ES module
//
// 来源:exceptions.js L428-1089 · verbatim 0 改逻辑(原 deadline 注释「搬到 src/home/erp-exceptions.js」兑现)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// 与 exceptions.js 联动:window.loadErpExceptions(异常页 loadExceptionsPage 调)·
//   window._rerenderErpExceptions + window._erpExcState(切语言重渲读)。
// ============================================================
/* global escapeHtml, showConfirm, humanizeError, currentLang */
/* eslint-disable no-useless-assignment -- verbatim exceptions.js · 非 bug */

(function () {
    // ─────────────────────────────────────────────────────────
    // ERP 推送异常块(Zihao 2026-05-26 · 独立来源 · 派生自 erp_push_logs · 铁律 #12)
    // ⚠️ 暂塞 home.js(并入现有异常页 DOM · 与 _excState 同作用域共享 t/escapeHtml/showToast)·
    //    迁出 deadline:REFACTOR-C1 拆 home.js 时一并搬到 src/home/erp-exceptions.js。
    // 闭环:修复(picker 下一块)+ [重试推送] 都在卡片内完成 · 重试走同一 /retry 端点
    //       (重新解析+反查+推送)· 成功 → 卡片消失(单一源自动同步)· 不来回跳日志页。
    // ─────────────────────────────────────────────────────────
    let _erpExcState = {
        items: [],
        q: '',
        cat: '',
        selected: new Set(),
        total: 0,
        categories: {},
        pageSize: 30,
        loading: false,
        focusSearch: false,
        searchCaret: 0,
    };
    let _erpExcSearchTimer = null;

    function _erpExcTok() {
        return localStorage.getItem('mrpilot_token') || '';
    }

    function _erpExcFriendly(it) {
        // P2-C (B7) · 优先后端 4 语友好原因(不裸透泰文)→ 退 humanizeError(网络错误)→ category 文案
        const _efLang =
            (typeof currentLang === 'string' && currentLang) || window._currentLang || 'th';
        const _ef = it.error_friendly && it.error_friendly[_efLang];
        if (_ef) return _ef;
        if (typeof humanizeError === 'function' && it.error_msg) {
            try {
                return humanizeError(it.error_msg);
            } catch (_) {
                /* fall through */
            }
        }
        return t('erp-exc-reason-' + (it.category || 'other'));
    }

    function _erpExcUpdateBatchBar() {
        const bar = document.getElementById('erp-exc-batch');
        if (!bar) return;
        const n = _erpExcState.selected.size;
        bar.hidden = n === 0;
        const cnt = bar.querySelector('.erp-exc-batch-count');
        if (cnt) cnt.textContent = String(n);
    }

    function renderErpExceptions() {
        const block = document.getElementById('erp-exc-block');
        if (!block) return;
        const st = _erpExcState;
        // 真正空(无异常 + 无搜索/筛选)→ 隐藏整块;搜索/筛选 0 结果 → 显示空态(留搜索框)
        const show = st.total > 0 || !!st.q || !!st.cat;
        if (!show) {
            block.hidden = true;
            block.innerHTML = '';
            return;
        }
        block.hidden = false;

        // category chips(计数来自后端 · 当前搜索范围内)
        const cats = st.categories || {};
        const allCount = Object.keys(cats).reduce((s, k) => s + cats[k], 0);
        let chipsHtml =
            `<button class="erp-exc-chip ${st.cat === '' ? 'active' : ''}" data-erpexc-cat="">` +
            `<span>${escapeHtml(t('erp-exc-cat-all'))}</span><span class="erp-exc-chip-count">${allCount}</span></button>`;
        Object.keys(cats).forEach((c) => {
            chipsHtml +=
                `<button class="erp-exc-chip ${st.cat === c ? 'active' : ''}" data-erpexc-cat="${escapeHtml(c)}">` +
                `<span>${escapeHtml(t('erp-exc-cat-' + c))}</span><span class="erp-exc-chip-count">${cats[c]}</span></button>`;
        });

        const items = st.items || [];
        const allChecked = items.length > 0 && items.every((it) => st.selected.has(it.id));
        const rowsHtml = items
            .map((it) => {
                const stateCls =
                    it.state === 'needs_action'
                        ? 'needs'
                        : it.state === 'retrying'
                          ? 'retry'
                          : 'fail';
                const stateLbl = t('erp-exc-state-' + (it.state || 'failed'));
                const reason = _erpExcFriendly(it);
                const checked = st.selected.has(it.id) ? 'checked' : '';
                return `<div class="erp-exc-row" data-erpexc-id="${escapeHtml(it.id)}">
                <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(it.id)}" ${checked}></span>
                <span class="ex-inv" title="${escapeHtml(it.invoice_no || '')}">${escapeHtml(it.invoice_no || '—')}</span>
                <span class="ex-seller" title="${escapeHtml(it.seller_name || '')}">${escapeHtml(it.seller_name || '—')}</span>
                <span class="ex-buyer" title="${escapeHtml(it.ocr_buyer_name || '')}">${escapeHtml(it.ocr_buyer_name || '—')}</span>
                <span class="ex-state"><span class="erp-exc-state ${stateCls}">${escapeHtml(stateLbl)}</span></span>
                <span class="ex-reason" title="${escapeHtml(reason)}">${escapeHtml(reason)}${it.error_code ? ` <span class="erp-exc-code">${escapeHtml(it.error_code)}</span>` : ''}</span>
                <span class="ex-act"><button class="btn btn-sm btn-secondary" type="button" data-erpexc-retry="${escapeHtml(it.id)}">${escapeHtml(t('erp-exc-retry'))}</button></span>
            </div>`;
            })
            .join('');

        const emptyHtml =
            items.length === 0
                ? `<div class="erp-exc-empty">${escapeHtml(t('erp-exc-empty'))}</div>`
                : '';
        const moreHtml =
            items.length < st.total
                ? `<button class="erp-exc-more" type="button" id="erp-exc-more">${escapeHtml(t('erp-exc-load-more'))} (${items.length}/${st.total})</button>`
                : st.total > 0
                  ? `<div class="erp-exc-count">${escapeHtml(t('erp-exc-shown', { n: items.length, total: st.total }))}</div>`
                  : '';

        block.innerHTML = `
            <div class="erp-exc-head">
                <h2 class="erp-exc-title">${escapeHtml(t('erp-exc-title'))}</h2>
                <span class="erp-exc-sub">${escapeHtml(t('erp-exc-sub'))}</span>
                <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t('erp-exc-search-ph'))}" value="${escapeHtml(st.q)}">
            </div>
            <div class="erp-exc-chips">${chipsHtml}</div>
            <div class="erp-exc-batch" id="erp-exc-batch" ${st.selected.size ? '' : 'hidden'}>
                <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${st.selected.size}</span> ${escapeHtml(t('erp-exc-batch-selected'))}</span>
                <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t('erp-exc-batch-retry'))}</button>
                <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t('erp-exc-batch-delete'))}</button>
                <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t('erp-exc-batch-clear'))}</button>
            </div>
            <div class="erp-exc-rows">
                <div class="erp-exc-row erp-exc-row-head">
                    <span class="ex-cb"><input type="checkbox" class="erp-exc-cb-all" id="erp-exc-cb-all" ${allChecked ? 'checked' : ''}></span>
                    <span class="ex-inv">${escapeHtml(t('erp-exc-f-invoice'))}</span>
                    <span class="ex-seller">${escapeHtml(t('erp-exc-f-seller'))}</span>
                    <span class="ex-buyer">${escapeHtml(t('erp-exc-f-buyer'))}</span>
                    <span class="ex-state">${escapeHtml(t('erp-exc-f-state'))}</span>
                    <span class="ex-reason">${escapeHtml(t('erp-exc-f-reason'))}</span>
                    <span class="ex-act"></span>
                </div>
                ${rowsHtml}${emptyHtml}
            </div>
            <div class="erp-exc-foot">${moreHtml}</div>`;

        // 搜索框(debounce · 保持焦点 + 光标)
        const search = document.getElementById('erp-exc-search');
        if (search) {
            if (st.focusSearch) {
                search.focus();
                try {
                    search.setSelectionRange(st.searchCaret, st.searchCaret);
                } catch (_) {}
            }
            search.addEventListener('input', () => {
                st.q = search.value;
                st.focusSearch = true;
                st.searchCaret = search.selectionStart || search.value.length;
                clearTimeout(_erpExcSearchTimer);
                _erpExcSearchTimer = setTimeout(() => loadErpExceptions(false), 350);
            });
            search.addEventListener('blur', () => {
                st.focusSearch = false;
            });
        }
        // chips
        block.querySelectorAll('.erp-exc-chip').forEach((btn) => {
            btn.addEventListener('click', () => {
                st.cat = btn.dataset.erpexcCat || '';
                loadErpExceptions(false);
            });
        });
        // 单条 retry
        block.querySelectorAll('[data-erpexc-retry]').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                _erpExcRetry(btn.dataset.erpexcRetry, btn);
            });
        });
        // 单选 checkbox(直接改 set + 更新批量栏 · 不整块重渲 · 防丢焦点)
        block.querySelectorAll('.erp-exc-cb').forEach((cb) => {
            cb.addEventListener('change', () => {
                const id = cb.dataset.erpexcCb;
                if (cb.checked) st.selected.add(id);
                else st.selected.delete(id);
                const head = document.getElementById('erp-exc-cb-all');
                if (head)
                    head.checked = items.length > 0 && items.every((it) => st.selected.has(it.id));
                _erpExcUpdateBatchBar();
            });
        });
        // 全选(当前页)
        const cbAll = document.getElementById('erp-exc-cb-all');
        if (cbAll)
            cbAll.addEventListener('change', () => {
                items.forEach((it) => {
                    if (cbAll.checked) st.selected.add(it.id);
                    else st.selected.delete(it.id);
                });
                block.querySelectorAll('.erp-exc-cb').forEach((c) => {
                    c.checked = cbAll.checked;
                });
                _erpExcUpdateBatchBar();
            });
        // 批量
        block.querySelectorAll('[data-erpexc-batch]').forEach((btn) => {
            btn.addEventListener('click', () => _erpExcBatch(btn.dataset.erpexcBatch));
        });
        // 加载更多
        const more = document.getElementById('erp-exc-more');
        if (more) more.addEventListener('click', () => loadErpExceptions(true));
        // 单击行(非 checkbox/按钮)→ 编辑弹窗(下一步)· 现暂留 hook
        block.querySelectorAll('.erp-exc-row:not(.erp-exc-row-head)').forEach((row) => {
            row.addEventListener('click', (e) => {
                if (e.target.closest('input,button')) return;
                if (typeof window._erpExcOpenEdit === 'function')
                    window._erpExcOpenEdit(row.dataset.erpexcId);
            });
        });
    }

    async function _erpExcRetry(logId, btn) {
        if (!logId) return;
        if (btn) {
            btn.disabled = true;
            btn.textContent = t('erp-exc-retrying');
        }
        try {
            const resp = await fetch('/api/erp/logs/' + encodeURIComponent(logId) + '/retry', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + _erpExcTok() },
            });
            const data = await resp.json().catch(() => ({}));
            showToast(
                resp.ok && data.ok ? t('erp-exc-retry-ok') : t('erp-exc-retry-fail'),
                resp.ok && data.ok ? 'success' : 'error'
            );
        } catch (e) {
            showToast(t('erp-exc-retry-fail'), 'error');
        }
        // 单一源:重拉队列 · 成功的行自动消失 · 失败的换新原因(铁律 #12 · 不维护乐观态)
        _erpExcState.selected.delete(logId);
        loadErpExceptions(false);
        if (typeof window.refreshExcBadge === 'function') {
            try {
                window.refreshExcBadge();
            } catch (_) {}
        }
    }

    async function _erpExcBatch(action) {
        const ids = Array.from(_erpExcState.selected);
        if (action === 'clear') {
            _erpExcState.selected.clear();
            renderErpExceptions();
            return;
        }
        if (ids.length === 0) return;
        if (action === 'delete') {
            // 用产品风格确认弹窗替换浏览器原生 confirm()(2026-05-26 · 符合设计语言)
            const ok = await showConfirm(t('erp-exc-batch-delete-confirm', { n: ids.length }), {
                danger: true,
            });
            if (!ok) return;
            try {
                const resp = await fetch('/api/erp/logs/batch-delete', {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + _erpExcTok(),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ log_ids: ids.slice(0, 200) }),
                });
                const d = await resp.json().catch(() => ({}));
                showToast(
                    resp.ok
                        ? t('erp-exc-batch-delete-ok', { n: d.deleted || 0 })
                        : t('erp-exc-retry-fail'),
                    resp.ok ? 'success' : 'error'
                );
            } catch (e) {
                showToast(t('erp-exc-retry-fail'), 'error');
            }
        } else if (action === 'retry') {
            try {
                const resp = await fetch('/api/erp/logs/batch-retry', {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + _erpExcTok(),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ log_ids: ids.slice(0, 50) }),
                });
                const d = await resp.json().catch(() => ({}));
                showToast(
                    resp.ok
                        ? t('erp-exc-batch-retry-ok', {
                              ok: d.succeeded || 0,
                              fail: (d.failed || 0) + (d.skipped || 0),
                          })
                        : t('erp-exc-retry-fail'),
                    resp.ok ? 'success' : 'error'
                );
            } catch (e) {
                showToast(t('erp-exc-retry-fail'), 'error');
            }
        }
        _erpExcState.selected.clear();
        loadErpExceptions(false);
        if (typeof window.refreshExcBadge === 'function') {
            try {
                window.refreshExcBadge();
            } catch (_) {}
        }
    }

    async function loadErpExceptions(append) {
        const block = document.getElementById('erp-exc-block');
        if (!block || _erpExcState.loading) return;
        _erpExcState.loading = true;
        try {
            const params = new URLSearchParams();
            if (_erpExcState.q) params.set('q', _erpExcState.q);
            if (_erpExcState.cat) params.set('category', _erpExcState.cat);
            params.set('limit', String(_erpExcState.pageSize));
            params.set('offset', String(append ? _erpExcState.items.length : 0));
            const resp = await fetch('/api/erp/exceptions?' + params.toString(), {
                headers: { Authorization: 'Bearer ' + _erpExcTok() },
            });
            if (!resp.ok) {
                if (!append) {
                    block.hidden = true;
                }
                return;
            }
            const data = await resp.json();
            const newItems = data.items || [];
            _erpExcState.items = append ? _erpExcState.items.concat(newItems) : newItems;
            _erpExcState.total = data.total || 0;
            _erpExcState.categories = data.categories || {};
            renderErpExceptions();
        } catch (e) {
            if (!append) block.hidden = true;
        } finally {
            _erpExcState.loading = false;
        }
    }
    // ── 单条异常编辑弹窗(Zihao 2026-05-26 · 闭环最后一环:选/绑 ERP 客户 + 重试)──
    // 通用:ERP 客户列表走 /endpoints/{id}/customers(adapter 通用接口)· 绑定走
    // /mappings/clients(通用 client_id→erp_code)· 重试走同一 /retry(重新解析)。
    // 不写死 MR.ERP:erp_type=endpoint_adapter · 仅"客户不符"且有买方 client 时显 picker。
    let _erpExcCustCache = {}; // endpoint_id → [{code,name,...}]

    function _erpExcCloseModal() {
        const ov = document.getElementById('erp-exc-modal');
        if (ov) ov.remove();
    }

    window._erpExcOpenEdit = function (id) {
        const it = (_erpExcState.items || []).find((x) => String(x.id) === String(id));
        if (!it) return;
        const canPickCustomer = !!it.history_client_id && it.category === 'customer_mismatch';
        // 商品不符 picker(对称客户 picker · Zihao 2026-05-26)· 通用 adapter · 不写死 MR.ERP。
        const canPickProduct =
            it.category === 'product_mismatch' && !!it.history_id && !!it.endpoint_id;
        const reason = _erpExcFriendly(it);
        const stateCls =
            it.state === 'needs_action' ? 'needs' : it.state === 'retrying' ? 'retry' : 'fail';
        const dRow = (lbl, val) =>
            `<div class="erp-exc-m-row"><span class="erp-exc-m-k">${escapeHtml(lbl)}</span><span class="erp-exc-m-v">${escapeHtml(val || '—')}</span></div>`;

        let fixHtml = '';
        if (canPickCustomer) {
            fixHtml = `
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t('erp-exc-edit-pick'))}</div>
                    <input type="search" class="erp-exc-m-search" id="erp-exc-m-search" placeholder="${escapeHtml(t('erp-exc-edit-pick-ph'))}">
                    <div class="erp-exc-m-custlist" id="erp-exc-m-custlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t('erp-exc-edit-pick-loading'))}</div>
                    </div>
                </div>`;
        } else if (canPickProduct) {
            fixHtml = `
                <div class="erp-exc-m-fix">
                    <div class="erp-exc-m-fix-title">${escapeHtml(t('erp-exc-edit-prod-intro'))}</div>
                    <div class="erp-exc-m-custlist" id="erp-exc-m-prodlist">
                        <div class="erp-exc-m-loading">${escapeHtml(t('erp-exc-edit-prod-loading'))}</div>
                    </div>
                </div>`;
        } else {
            const hintKey = 'erp-exc-edit-hint-' + (it.category || 'other');
            let hint = t(hintKey);
            if (!hint || hint === hintKey) hint = reason;
            fixHtml = `<div class="erp-exc-m-hint">${escapeHtml(hint)}</div>`;
        }

        const ov = document.createElement('div');
        ov.id = 'erp-exc-modal';
        ov.className = 'erp-exc-modal-overlay';
        ov.innerHTML = `
            <div class="erp-exc-modal" role="dialog" aria-modal="true">
                <div class="erp-exc-m-head">
                    <h3>${escapeHtml(t('erp-exc-edit-title'))}</h3>
                    <button class="erp-exc-m-close" type="button" id="erp-exc-m-close" aria-label="close">×</button>
                </div>
                <div class="erp-exc-m-body">
                    <div class="erp-exc-m-reason"><span class="erp-exc-state ${stateCls}">${escapeHtml(t('erp-exc-state-' + (it.state || 'failed')))}</span> ${escapeHtml(reason)}${it.error_code ? ` <span class="erp-exc-code">${escapeHtml(it.error_code)}</span>` : ''}</div>
                    ${dRow(t('erp-exc-f-invoice'), it.invoice_no)}
                    ${dRow(t('erp-exc-f-seller'), it.seller_name)}
                    ${dRow(t('erp-exc-f-buyer'), it.ocr_buyer_name)}
                    ${dRow(t('erp-exc-edit-field-current'), it.client_name)}
                    ${fixHtml}
                </div>
                <div class="erp-exc-m-foot">
                    <button class="btn btn-sm btn-ghost" type="button" id="erp-exc-m-cancel">${escapeHtml(t('erp-exc-edit-close'))}</button>
                    <button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-retry">${escapeHtml(t('erp-exc-edit-retry'))}</button>
                    ${canPickCustomer ? `<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind" disabled>${escapeHtml(t('erp-exc-edit-bind-retry'))}</button>` : ''}
                    ${canPickProduct ? `<button class="btn btn-sm btn-primary" type="button" id="erp-exc-m-bind-prod" disabled>${escapeHtml(t('erp-exc-edit-bind-prod-retry'))}</button>` : ''}
                </div>
            </div>`;
        document.body.appendChild(ov);

        ov.addEventListener('click', (e) => {
            if (e.target === ov) _erpExcCloseModal();
        });
        document.getElementById('erp-exc-m-close').addEventListener('click', _erpExcCloseModal);
        document.getElementById('erp-exc-m-cancel').addEventListener('click', _erpExcCloseModal);
        document.getElementById('erp-exc-m-retry').addEventListener('click', () => {
            _erpExcCloseModal();
            _erpExcRetry(it.id, null);
        });

        if (canPickCustomer) {
            let _selectedCode = '';
            const bindBtn = document.getElementById('erp-exc-m-bind');
            const listEl = document.getElementById('erp-exc-m-custlist');
            const searchEl = document.getElementById('erp-exc-m-search');

            const renderCustList = (custs, filter) => {
                const q = (filter || '').trim().toLowerCase();
                const shown = q
                    ? custs.filter(
                          (c) =>
                              (c.code || '').toLowerCase().includes(q) ||
                              (c.name || '').toLowerCase().includes(q)
                      )
                    : custs;
                if (shown.length === 0) {
                    listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-pick-empty'))}</div>`;
                    return;
                }
                listEl.innerHTML = shown
                    .slice(0, 100)
                    .map(
                        (c) =>
                            `<div class="erp-exc-m-cust" data-cust-code="${escapeHtml(c.code || '')}">
                        <span class="erp-exc-m-cust-name">${escapeHtml(c.name || '')}</span>
                        <span class="erp-exc-m-cust-code">${escapeHtml(c.code || '')}</span>
                    </div>`
                    )
                    .join('');
                listEl.querySelectorAll('.erp-exc-m-cust').forEach((el) => {
                    el.addEventListener('click', () => {
                        _selectedCode = el.dataset.custCode || '';
                        listEl
                            .querySelectorAll('.erp-exc-m-cust')
                            .forEach((x) => x.classList.remove('sel'));
                        el.classList.add('sel');
                        if (bindBtn) bindBtn.disabled = !_selectedCode;
                    });
                });
            };

            const loadCusts = async () => {
                const epId = it.endpoint_id;
                if (_erpExcCustCache[epId]) {
                    renderCustList(_erpExcCustCache[epId], '');
                    return;
                }
                try {
                    const resp = await fetch(
                        '/api/erp/endpoints/' + encodeURIComponent(epId) + '/customers',
                        {
                            headers: { Authorization: 'Bearer ' + _erpExcTok() },
                        }
                    );
                    const data = await resp.json().catch(() => ({}));
                    if (!resp.ok || !data.ok) {
                        listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-pick-fail'))}</div>`;
                        return;
                    }
                    const custs = data.customers || [];
                    _erpExcCustCache[epId] = custs;
                    renderCustList(custs, '');
                } catch (e) {
                    listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-pick-fail'))}</div>`;
                }
            };
            if (searchEl)
                searchEl.addEventListener('input', () =>
                    renderCustList(_erpExcCustCache[it.endpoint_id] || [], searchEl.value)
                );
            loadCusts();

            if (bindBtn)
                bindBtn.addEventListener('click', async () => {
                    if (!_selectedCode) return;
                    bindBtn.disabled = true;
                    bindBtn.textContent = t('erp-exc-retrying');
                    try {
                        // 1) 绑定买方 client → ERP 客户码(通用 client mapping)
                        const mResp = await fetch('/api/erp/mappings/clients', {
                            method: 'POST',
                            headers: {
                                Authorization: 'Bearer ' + _erpExcTok(),
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                client_id: it.history_client_id,
                                erp_type: it.endpoint_adapter,
                                erp_code: _selectedCode,
                            }),
                        });
                        if (!mResp.ok) {
                            showToast(t('erp-exc-retry-fail'), 'error');
                            bindBtn.disabled = false;
                            bindBtn.textContent = t('erp-exc-edit-bind-retry');
                            return;
                        }
                        showToast(t('erp-exc-edit-bound-ok'), 'success');
                        _erpExcCloseModal();
                        // 2) 重试(重新解析 → 用上新映射 → 推送)
                        await _erpExcRetry(it.id, null);
                    } catch (e) {
                        showToast(t('erp-exc-retry-fail'), 'error');
                        bindBtn.disabled = false;
                        bindBtn.textContent = t('erp-exc-edit-bind-retry');
                    }
                });
        }

        // ── 商品不符 picker(对称客户 picker)──
        // 逐行列出发票商品 · 每行一个 ERP 商品下拉(原生 select · 键盘可搜)·
        // 选中后写 /mappings/products(item_name→erp_code · 通用)· 再走同一 /retry 重解析推送。
        if (canPickProduct) {
            const bindBtn = document.getElementById('erp-exc-m-bind-prod');
            const listEl = document.getElementById('erp-exc-m-prodlist');
            const sel = {}; // item_name → {code, name}
            let _products = [];

            const optionsHtml = () =>
                '<option value="">' +
                escapeHtml(t('erp-exc-edit-prod-choose')) +
                '</option>' +
                _products
                    .slice(0, 500)
                    .map(
                        (p) =>
                            `<option value="${escapeHtml(p.code || '')}" data-pname="${escapeHtml(p.name || '')}">` +
                            escapeHtml((p.name || '') + ' · ' + (p.code || '')) +
                            '</option>'
                    )
                    .join('');

            const renderItems = (names) => {
                if (!names.length) {
                    listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-prod-noitems'))}</div>`;
                    return;
                }
                listEl.innerHTML = names
                    .map(
                        (nm) =>
                            `<div class="erp-exc-m-cust" style="cursor:default">
                        <span class="erp-exc-m-cust-name" title="${escapeHtml(nm)}">${escapeHtml(nm)}</span>
                        <select class="erp-exc-m-prod-sel" data-item="${escapeHtml(nm)}" style="max-width:55%;flex:0 0 auto;padding:4px 6px;border:1px solid var(--border,#e5e7eb);border-radius:6px;font-size:12px">${optionsHtml()}</select>
                    </div>`
                    )
                    .join('');
                listEl.querySelectorAll('.erp-exc-m-prod-sel').forEach((s) => {
                    s.addEventListener('change', () => {
                        const nm = s.dataset.item;
                        const opt = s.options[s.selectedIndex];
                        if (s.value)
                            sel[nm] = { code: s.value, name: opt ? opt.dataset.pname || '' : '' };
                        else delete sel[nm];
                        if (bindBtn) bindBtn.disabled = Object.keys(sel).length === 0;
                    });
                });
            };

            const loadAll = async () => {
                try {
                    const hResp = await fetch('/api/history/' + encodeURIComponent(it.history_id), {
                        headers: { Authorization: 'Bearer ' + _erpExcTok() },
                    });
                    const hData = await hResp.json().catch(() => ({}));
                    const pages = (hData && hData.pages) || [];
                    const names = [];
                    const seen = {};
                    (Array.isArray(pages) ? pages : []).forEach((pg) => {
                        const items = (pg && pg.fields && pg.fields.items) || [];
                        (Array.isArray(items) ? items : []).forEach((li) => {
                            const nm = ((li && (li.name || li.description)) || '').trim();
                            if (nm && !seen[nm]) {
                                seen[nm] = 1;
                                names.push(nm);
                            }
                        });
                    });
                    const pResp = await fetch(
                        '/api/erp/endpoints/' + encodeURIComponent(it.endpoint_id) + '/products',
                        {
                            headers: { Authorization: 'Bearer ' + _erpExcTok() },
                        }
                    );
                    const pData = await pResp.json().catch(() => ({}));
                    if (!pResp.ok || !pData.ok) {
                        listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-prod-fail'))}</div>`;
                        return;
                    }
                    _products = pData.products || [];
                    renderItems(names);
                } catch (e) {
                    listEl.innerHTML = `<div class="erp-exc-m-empty">${escapeHtml(t('erp-exc-edit-prod-fail'))}</div>`;
                }
            };
            loadAll();

            if (bindBtn)
                bindBtn.addEventListener('click', async () => {
                    const entries = Object.entries(sel);
                    if (!entries.length) return;
                    bindBtn.disabled = true;
                    bindBtn.textContent = t('erp-exc-retrying');
                    try {
                        for (const [itemName, v] of entries) {
                            const mResp = await fetch('/api/erp/mappings/products', {
                                method: 'POST',
                                headers: {
                                    Authorization: 'Bearer ' + _erpExcTok(),
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    erp_type: it.endpoint_adapter,
                                    item_name: itemName,
                                    erp_code: v.code,
                                    erp_name: v.name,
                                }),
                            });
                            if (!mResp.ok) {
                                showToast(t('erp-exc-retry-fail'), 'error');
                                bindBtn.disabled = false;
                                bindBtn.textContent = t('erp-exc-edit-bind-prod-retry');
                                return;
                            }
                        }
                        showToast(t('erp-exc-edit-prod-bound-ok'), 'success');
                        _erpExcCloseModal();
                        await _erpExcRetry(it.id, null);
                    } catch (e) {
                        showToast(t('erp-exc-retry-fail'), 'error');
                        bindBtn.disabled = false;
                        bindBtn.textContent = t('erp-exc-edit-bind-prod-retry');
                    }
                });
        }
    };

    window._rerenderErpExceptions = renderErpExceptions;

    // 暴露给 exceptions.js(loadExceptionsPage 触发加载 · 切语言重渲读状态)
    window.loadErpExceptions = loadErpExceptions;
    window._erpExcState = _erpExcState;
})();
