// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送异常块 从 exceptions.js 抽出为独立 ES module
//
// 来源:exceptions.js L428-1089 · verbatim 0 改逻辑(原 deadline 注释「搬到 src/home/erp-exceptions.js」兑现)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// 与 exceptions.js 联动:window.loadErpExceptions(异常页 loadExceptionsPage 调)·
//   window._rerenderErpExceptions + window._erpExcState(切语言重渲读)。
// ============================================================
/* global escapeHtml, showConfirm, humanizeError, currentLang */

// ─────────────────────────────────────────────────────────
// ERP 推送异常块(Zihao 2026-05-26 · 独立来源 · 派生自 erp_push_logs · 铁律 #12)
// 暂塞 home.js(并入现有异常页 DOM · 与 _excState 同作用域共享 t/escapeHtml/showToast)·
//    迁出 deadline:REFACTOR-C1 拆 home.js 时一并搬到 src/home/erp-exceptions.js。
// 闭环:修复(picker 下一块)+ [重试推送] 都在卡片内完成 · 重试走同一 /retry 端点
//       (重新解析+反查+推送)· 成功 → 卡片消失(单一源自动同步)· 不来回跳日志页。
// ─────────────────────────────────────────────────────────
type ErpExcItem = {
    id: string;
    state?: string;
    push_type?: string;
    invoice_no?: string;
    seller_name?: string;
    id_card_tail?: string;
    ocr_buyer_name?: string;
    error_code?: string;
    error_msg?: string;
    category?: string;
    error_friendly?: Record<string, string>;
};
let _erpExcState: {
    items: ErpExcItem[];
    q: string;
    cat: string;
    adapter: string;
    selected: Set<string>;
    total: number;
    categories: Record<string, number>;
    pageSize: number;
    loading: boolean;
    focusSearch: boolean;
    searchCaret: number;
} = {
    items: [],
    q: '',
    cat: '',
    adapter: '', // DMS 闭环修正(Zihao 2026-06-01)· 异常栏与推送日志同理:ERP 系统下拉筛选
    selected: new Set(),
    total: 0,
    categories: {},
    pageSize: 30,
    loading: false,
    focusSearch: false,
    searchCaret: 0,
};
let _erpExcSearchTimer: ReturnType<typeof setTimeout> | null = null;

function _erpExcTok() {
    return localStorage.getItem('mrpilot_token') || '';
}

// 原始报错串(HTML 错误页 / 栈 / ERR_ 码 / 超长串)不该露给用户 → 退回类别文案
function _erpExcLooksRaw(s: string) {
    return /<!?\s*doctype|<html|<\/?[a-z]+>|\bTraceback\b|^\s*ERR_[A-Z]/i.test(s) || s.length > 200;
}

function _erpExcFriendly(it: ErpExcItem) {
    // P2-C (B7) · 优先后端 4 语友好原因(不裸透泰文)→ 退 humanizeError(网络错误)→ category 文案
    const _efLang = (typeof currentLang === 'string' && currentLang) || window._currentLang || 'th';
    const _ef = it.error_friendly && it.error_friendly[_efLang];
    if (_ef) return _ef;
    if (typeof humanizeError === 'function' && it.error_msg && !_erpExcLooksRaw(it.error_msg)) {
        try {
            const h = humanizeError(it.error_msg);
            if (h && !_erpExcLooksRaw(h)) return h;
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
                it.state === 'needs_action' ? 'needs' : it.state === 'retrying' ? 'retry' : 'fail';
            const stateLbl = t('erp-exc-state-' + (it.state || 'failed'));
            const reason = _erpExcFriendly(it);
            const checked = st.selected.has(it.id) ? 'checked' : '';
            // DMS 闭环修正 · 身份证订车异常按 DMS 字段:单据=订车单号、对方=客户、无买方;加类型标。
            const isId = it.push_type === 'id_card';
            const idBadge = isId
                ? `<span class="erp-exc-type-idcard">${escapeHtml(t('erp-log-type-idcard'))}</span> `
                : '';
            const invCell = isId
                ? `<span class="ex-inv" title="${escapeHtml(t('erp-log-col-booking'))}">${idBadge}${escapeHtml(it.invoice_no || '—')}</span>`
                : `<span class="ex-inv" title="${escapeHtml(it.invoice_no || '')}">${escapeHtml(it.invoice_no || '—')}</span>`;
            const sellerCell = isId
                ? `<span class="ex-seller" title="${escapeHtml(t('erp-log-col-customer'))}">${escapeHtml(it.seller_name || '—')}</span>`
                : `<span class="ex-seller" title="${escapeHtml(it.seller_name || '')}">${escapeHtml(it.seller_name || '—')}</span>`;
            const buyerCell = isId
                ? `<span class="ex-buyer" title="${escapeHtml(t('erp-log-col-idcard'))}">${it.id_card_tail ? '••••' + escapeHtml(it.id_card_tail) : '—'}</span>`
                : `<span class="ex-buyer" title="${escapeHtml(it.ocr_buyer_name || '')}">${escapeHtml(it.ocr_buyer_name || '—')}</span>`;
            return `<div class="erp-exc-row" data-erpexc-id="${escapeHtml(it.id)}">
            <span class="ex-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(it.id)}" ${checked}></span>
            ${invCell}
            ${sellerCell}
            ${buyerCell}
            <span class="ex-state"><span class="erp-exc-state ${stateCls}">${escapeHtml(stateLbl)}</span></span>
            <span class="ex-reason" title="${escapeHtml(reason)}${it.error_code ? ' (' + escapeHtml(it.error_code) + ')' : ''}">${escapeHtml(reason)}</span>
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

    // DMS 闭环修正 · ERP 系统下拉(真实配置端点 · 按 adapter 去重)+ 选中 DMS 时表头切 订车单号/客户
    const isDmsView = st.adapter === 'mrerp_dms';
    const _eps = Array.isArray(window._erpEndpoints) ? window._erpEndpoints : [];
    const _seenAd = new Set();
    let _erpOpts = `<option value="">${escapeHtml(t('erp-logs-erp-all'))}</option>`;
    _eps.forEach((e) => {
        const ad = (((e && e.adapter) || '') as string).toLowerCase();
        if (!ad || _seenAd.has(ad)) return;
        _seenAd.add(ad);
        _erpOpts += `<option value="${escapeHtml(ad)}"${ad === st.adapter ? ' selected' : ''}>${escapeHtml((e && e.name) || ad)}</option>`;
    });
    const colExcInv = isDmsView ? t('erp-log-col-booking') : t('erp-exc-f-invoice');
    const colExcSeller = isDmsView ? t('erp-log-col-customer') : t('erp-exc-f-seller');
    const colExcBuyer = isDmsView ? t('erp-log-col-idcard') : t('erp-exc-f-buyer');
    block.innerHTML = `
        <div class="erp-exc-head">
            <h2 class="erp-exc-title">${escapeHtml(t('erp-exc-title'))}</h2>
            <span class="erp-exc-sub">${escapeHtml(t('erp-exc-sub'))}</span>
            <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${_erpOpts}</select>
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
                <span class="ex-inv">${escapeHtml(colExcInv)}</span>
                <span class="ex-seller">${escapeHtml(colExcSeller)}</span>
                <span class="ex-buyer">${escapeHtml(colExcBuyer)}</span>
                <span class="ex-state">${escapeHtml(t('erp-exc-f-state'))}</span>
                <span class="ex-reason">${escapeHtml(t('erp-exc-f-reason'))}</span>
                <span class="ex-act"></span>
            </div>
            ${rowsHtml}${emptyHtml}
        </div>
        <div class="erp-exc-foot">${moreHtml}</div>`;

    // 搜索框(debounce · 保持焦点 + 光标)
    const search = document.getElementById('erp-exc-search') as HTMLInputElement | null;
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
            clearTimeout(_erpExcSearchTimer!);
            _erpExcSearchTimer = setTimeout(() => loadErpExceptions(false), 350);
        });
        search.addEventListener('blur', () => {
            st.focusSearch = false;
        });
    }
    // chips
    block.querySelectorAll('.erp-exc-chip').forEach((btn) => {
        btn.addEventListener('click', () => {
            st.cat = (btn as HTMLElement).dataset.erpexcCat || '';
            loadErpExceptions(false);
        });
    });
    // ERP 系统下拉(DMS 闭环修正 · 异常栏与推送日志同理 · 选一个看一个)
    const erpSel = document.getElementById('erp-exc-erp-select') as HTMLSelectElement | null;
    if (erpSel) {
        erpSel.addEventListener('change', () => {
            st.adapter = erpSel.value || '';
            loadErpExceptions(false);
        });
    }
    // 单条 retry
    block.querySelectorAll('[data-erpexc-retry]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            _erpExcRetry((btn as HTMLElement).dataset.erpexcRetry, btn as HTMLButtonElement);
        });
    });
    // 单选 checkbox(直接改 set + 更新批量栏 · 不整块重渲 · 防丢焦点)
    block.querySelectorAll('.erp-exc-cb').forEach((cb) => {
        cb.addEventListener('change', () => {
            const id = (cb as HTMLInputElement).dataset.erpexcCb as string;
            if ((cb as HTMLInputElement).checked) st.selected.add(id);
            else st.selected.delete(id);
            const head = document.getElementById('erp-exc-cb-all') as HTMLInputElement | null;
            if (head)
                head.checked = items.length > 0 && items.every((it) => st.selected.has(it.id));
            _erpExcUpdateBatchBar();
        });
    });
    // 全选(当前页)
    const cbAll = document.getElementById('erp-exc-cb-all') as HTMLInputElement | null;
    if (cbAll)
        cbAll.addEventListener('change', () => {
            items.forEach((it) => {
                if (cbAll.checked) st.selected.add(it.id);
                else st.selected.delete(it.id);
            });
            block.querySelectorAll('.erp-exc-cb').forEach((c) => {
                (c as HTMLInputElement).checked = cbAll.checked;
            });
            _erpExcUpdateBatchBar();
        });
    // 批量
    block.querySelectorAll('[data-erpexc-batch]').forEach((btn) => {
        btn.addEventListener('click', () => _erpExcBatch((btn as HTMLElement).dataset.erpexcBatch));
    });
    // 加载更多
    const more = document.getElementById('erp-exc-more');
    if (more) more.addEventListener('click', () => loadErpExceptions(true));
    // 单击行(非 checkbox/按钮)→ 编辑弹窗(下一步)· 现暂留 hook
    block.querySelectorAll('.erp-exc-row:not(.erp-exc-row-head)').forEach((row) => {
        row.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).closest('input,button')) return;
            if (typeof window._erpExcOpenEdit === 'function')
                window._erpExcOpenEdit((row as HTMLElement).dataset.erpexcId);
        });
    });
}

async function _erpExcRetry(logId: string | undefined, btn: HTMLButtonElement | null) {
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

async function _erpExcBatch(action: string | undefined) {
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

async function loadErpExceptions(append?: boolean) {
    const block = document.getElementById('erp-exc-block');
    if (!block || _erpExcState.loading) return;
    _erpExcState.loading = true;
    try {
        // ERP 系统下拉的选项来自真实配置端点 · 异常页可能先于集成页打开 → 懒缓存一次
        if (!Array.isArray(window._erpEndpoints) || !window._erpEndpoints.length) {
            try {
                const er = await fetch('/api/erp/endpoints', {
                    headers: { Authorization: 'Bearer ' + _erpExcTok() },
                });
                if (er.ok) {
                    const ed = await er.json();
                    window._erpEndpoints = (ed && (ed.items || ed)) || [];
                }
            } catch (_) {
                /* 下拉退化为仅「全部 ERP」· 不致命 */
            }
        }
        const params = new URLSearchParams();
        if (_erpExcState.q) params.set('q', _erpExcState.q);
        if (_erpExcState.cat) params.set('category', _erpExcState.cat);
        if (_erpExcState.adapter) params.set('adapter', _erpExcState.adapter);
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

export { _erpExcState, _erpExcFriendly, _erpExcRetry, _erpExcTok };

window._rerenderErpExceptions = renderErpExceptions;

// 暴露给 exceptions.js(loadExceptionsPage 触发加载 · 切语言重渲读状态)
window.loadErpExceptions = loadErpExceptions;
window._erpExcState = _erpExcState;
