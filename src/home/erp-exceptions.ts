// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送异常块 从 exceptions.js 抽出为独立 ES module
//
// 来源:exceptions.js L428-1089 · verbatim 0 改逻辑(原 deadline 注释「搬到 src/home/erp-exceptions.js」兑现)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// 与 exceptions.js 联动:window.loadErpExceptions(异常页 loadExceptionsPage 调)·
//   window._rerenderErpExceptions + window._erpExcState(切语言重渲读)。
// ============================================================
/* global escapeHtml, showConfirm, humanizeError, currentLang */

import {
    _erpExcRetry,
    _erpExcBatch,
    _erpExcAcctPanel,
    _erpExcAccountFix,
    _erpExcBindPanel,
    _erpExcEnsureClients,
    _erpExcWireBind,
} from './erp-exc-actions.js';

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
    endpoint_id?: string;
    endpoint_name?: string;
    error_friendly?: Record<string, string>;
    account_fix?: { direction?: string; slots?: string[]; bad_code?: string };
};

let _erpExcState: {
    items: ErpExcItem[];
    q: string;
    cat: string;
    pushType: string;
    adapter: string;
    selected: Set<string>;
    total: number;
    categories: Record<string, number>;
    idCardCount: number;
    pageSize: number;
    loading: boolean;
    focusSearch: boolean;
    searchCaret: number;
} = {
    items: [],
    q: '',
    cat: '',
    pushType: '', // 身份证订车失败统计卡筛选(push_type=id_card)
    adapter: '', // DMS 闭环修正(Zihao 2026-06-01)· 异常栏与推送日志同理:ERP 系统下拉筛选
    selected: new Set(),
    total: 0,
    categories: {},
    idCardCount: 0,
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
    // Express 留人工码(EXPRESS_MANUAL: no_revenue_account 等)→ 复用日志卡的人话映射,
    // 否则异常页会把英文技术码裸露给用户(此前不翻 Express 码)。
    const _exFn = (window as any)._expressFriendlyReason;
    if (
        typeof _exFn === 'function' &&
        it.error_msg &&
        it.error_msg.indexOf('EXPRESS_MANUAL') >= 0
    ) {
        try {
            const ex = _exFn(it.error_msg);
            if (ex) return ex;
        } catch (_) {
            /* fall through */
        }
    }
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
    // 真正空(无异常 + 无任何筛选)→ 隐藏整块;搜索/分类/ERP 筛选 0 结果 → 仍渲染面板
    // (留下拉/搜索/统计卡 + 空态文案)· 否则选了空 ERP 会把能切回去的下拉也藏掉 → 困死。
    const show = st.total > 0 || !!st.q || !!st.cat || !!st.adapter || !!st.pushType;
    if (!show) {
        block.hidden = true;
        block.innerHTML = '';
        return;
    }
    block.hidden = false;

    // 统计卡(草稿对齐 · 固定 4 张:全部异常 / 商品不符 / 客户不符 / 身份证订车失败)·
    // 计数来自后端当前搜索范围 · 点击按 category 或 push_type 筛选 · 各卡专属说明文案。
    const cats = st.categories || {};
    const allCount = Object.keys(cats).reduce((s, k) => s + cats[k], 0);
    const customerCount = (cats.customer_mismatch || 0) + (cats.no_client || 0);
    // [label, num, sub, cat, kind, active]
    const stats: Array<[string, number, string, string, string, boolean]> = [
        [
            t('erp-exc-stat-all'),
            allCount,
            t('erp-exc-stat-sub-all'),
            '',
            '',
            !st.cat && !st.pushType,
        ],
        [
            t('erp-exc-cat-account_missing'),
            cats.account_missing || 0,
            t('erp-exc-stat-sub-account'),
            'account_missing',
            '',
            st.cat === 'account_missing',
        ],
        [
            t('erp-exc-cat-product_mismatch'),
            cats.product_mismatch || 0,
            t('erp-exc-stat-sub-product'),
            'product_mismatch',
            '',
            st.cat === 'product_mismatch',
        ],
        [
            t('erp-exc-cat-customer_mismatch'),
            customerCount,
            t('erp-exc-stat-sub-customer'),
            'customer_mismatch',
            '',
            st.cat === 'customer_mismatch',
        ],
        [
            t('erp-exc-stat-dms'),
            st.idCardCount || 0,
            t('erp-exc-stat-sub-dms'),
            '',
            'id_card',
            st.pushType === 'id_card',
        ],
    ];
    const chipsHtml = stats
        .map(
            ([label, num, sub, cat, kind, active]) =>
                `<button class="erp-exc-stat ${active ? 'active' : ''}" data-erpexc-cat="${escapeHtml(cat)}" data-erpexc-kind="${escapeHtml(kind)}">` +
                `<span class="erp-exc-stat-label">${escapeHtml(label)}</span>` +
                `<span class="erp-exc-stat-num">${num}</span>` +
                `<span class="erp-exc-stat-sub">${escapeHtml(sub)}</span></button>`
        )
        .join('');

    const items = st.items || [];
    // 异常 issue 卡(草稿对齐):分类图标 + 单据/类型 + 失败原因 + 修复映射/重试
    const rowsHtml = items
        .map((it) => {
            const reason = _erpExcFriendly(it);
            const checked = st.selected.has(it.id) ? 'checked' : '';
            const isId = it.push_type === 'id_card';
            const cat = it.category || 'other';
            let icoLetter = '!';
            let icoCls = 'other';
            if (isId) {
                icoLetter = 'D';
                icoCls = 'dms';
            } else if (cat === 'product_mismatch') {
                icoLetter = 'P';
                icoCls = 'product';
            } else if (cat === 'customer_mismatch' || cat === 'no_client') {
                icoLetter = 'C';
                icoCls = 'customer';
            } else if (cat === 'account_missing') {
                icoLetter = 'A';
                icoCls = 'account';
            }
            // 副行:身份证订车显「客户:姓名 · 端点」(seller_name 即客户名)· 发票显「发票推送 · 端点」
            const ep = it.endpoint_name ? ' · ' + it.endpoint_name : '';
            const sub = isId
                ? t('erp-log-col-customer') + '：' + (it.seller_name || '—') + ep
                : t('erp-log-type-invoice') + ep;
            const canFix =
                !isId &&
                (cat === 'product_mismatch' || cat === 'customer_mismatch' || cat === 'no_client');
            const fixLbl =
                cat === 'product_mismatch' ? t('erp-exc-fix-product') : t('erp-exc-fix-customer');
            const isAcct = cat === 'account_missing';
            // 方向判不出且主体可绑(主体没绑/税号没读到)→ 绑主体卡;direction_not_enabled
            // (方向判出但该方向没在向导开)绑主体无用 → 走普通详情+重推。
            const isBind =
                cat === 'direction_unknown' && !/direction_not_enabled/.test(it.error_msg || '');
            const detailBtn = `<button class="btn btn-sm btn-secondary" type="button" data-erpexc-detail="${escapeHtml(it.id)}">${escapeHtml(t('erp-log-detail-btn'))}</button>`;
            // 待补科目/绑主体:详情 + 展开同款下拉面板(复用 data-erpexc-acctfix 开关);其余:修复映射/详情 + 重推。
            const actHtml =
                isAcct || isBind
                    ? `${detailBtn}
                   <button class="btn btn-sm btn-primary" type="button" data-erpexc-acctfix="${escapeHtml(it.id)}">${escapeHtml(t(isAcct ? 'erp-acctfix-open' : 'erp-bind-open'))}</button>`
                    : `${canFix ? `<button class="btn btn-sm btn-secondary" type="button" data-erpexc-fix="${escapeHtml(it.id)}">${escapeHtml(fixLbl)}</button>` : detailBtn}
                   <button class="btn btn-sm btn-primary" type="button" data-erpexc-retry="${escapeHtml(it.id)}">${escapeHtml(t('erp-exc-retry'))}</button>`;
            return `<div class="erp-exc-card${isAcct || isBind ? ' has-acctfix' : ''}" data-erpexc-id="${escapeHtml(it.id)}">
            <span class="erp-exc-card-cb"><input type="checkbox" class="erp-exc-cb" data-erpexc-cb="${escapeHtml(it.id)}" ${checked}></span>
            <div class="erp-exc-card-icon ${icoCls}">${icoLetter}</div>
            <div class="erp-exc-card-main"><b title="${escapeHtml(it.invoice_no || '')}">${escapeHtml(it.invoice_no || '—')}</b><span>${escapeHtml(sub)}</span></div>
            <div class="erp-exc-card-reason"><label>${escapeHtml(t('erp-receipt-fail-reason'))}</label><p title="${escapeHtml(reason)}${it.error_code ? ' (' + escapeHtml(it.error_code) + ')' : ''}">${escapeHtml(reason)}</p></div>
            <div class="erp-exc-card-act">${actHtml}</div>
            ${isAcct ? _erpExcAcctPanel(it) : isBind ? _erpExcBindPanel(it) : ''}
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

    // ERP 系统下拉(真实配置端点 · 按 adapter 去重)
    const _eps = Array.isArray(window._erpEndpoints) ? window._erpEndpoints : [];
    const _seenAd = new Set();
    let _erpOpts = `<option value="">${escapeHtml(t('erp-logs-erp-all'))}</option>`;
    _eps.forEach((e) => {
        const ad = (((e && e.adapter) || '') as string).toLowerCase();
        if (!ad || _seenAd.has(ad)) return;
        _seenAd.add(ad);
        _erpOpts += `<option value="${escapeHtml(ad)}"${ad === st.adapter ? ' selected' : ''}>${escapeHtml((e && e.name) || ad)}</option>`;
    });
    block.innerHTML = `
        <div class="erp-exc-head">
            <h2 class="erp-exc-title">${escapeHtml(t('erp-exc-title'))}</h2>
            <span class="erp-exc-sub">${escapeHtml(t('erp-exc-sub'))}</span>
            <select class="erp-logs-erp-select" id="erp-exc-erp-select" aria-label="ERP">${_erpOpts}</select>
            <input type="search" class="erp-exc-search" id="erp-exc-search" placeholder="${escapeHtml(t('erp-exc-search-ph'))}" value="${escapeHtml(st.q)}">
        </div>
        <div class="erp-exc-summary">${chipsHtml}</div>
        <div class="erp-exc-batch" id="erp-exc-batch" ${st.selected.size ? '' : 'hidden'}>
            <span class="erp-exc-batch-info"><span class="erp-exc-batch-count">${st.selected.size}</span> ${escapeHtml(t('erp-exc-batch-selected'))}</span>
            <button class="btn btn-sm btn-primary" type="button" data-erpexc-batch="retry">${escapeHtml(t('erp-exc-batch-retry'))}</button>
            <button class="btn btn-sm btn-danger" type="button" data-erpexc-batch="delete">${escapeHtml(t('erp-exc-batch-delete'))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-erpexc-batch="clear">${escapeHtml(t('erp-exc-batch-clear'))}</button>
        </div>
        <div class="erp-exc-cards">
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
    // 统计卡(点击按 category 或 push_type 筛选 · 互斥)
    block.querySelectorAll('.erp-exc-stat').forEach((btn) => {
        btn.addEventListener('click', () => {
            st.cat = (btn as HTMLElement).dataset.erpexcCat || '';
            st.pushType = (btn as HTMLElement).dataset.erpexcKind || '';
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
    // 修复映射/确认客户按钮 → 映射修复弹窗
    block.querySelectorAll('[data-erpexc-fix]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window._erpExcOpenEdit === 'function')
                window._erpExcOpenEdit((btn as HTMLElement).dataset.erpexcFix);
        });
    });
    // 查看详情按钮 → 推送详情抽屉(与推送日志共用 showLogDetail)
    block.querySelectorAll('[data-erpexc-detail]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (typeof window.showLogDetail === 'function')
                window.showLogDetail((btn as HTMLElement).dataset.erpexcDetail);
        });
    });
    // 待补科目:展开/收起下拉面板(同卡内 · 不跳页)
    block.querySelectorAll('[data-erpexc-acctfix]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = (btn as HTMLElement).dataset.erpexcAcctfix as string;
            const panel = block.querySelector(
                `[data-acctfix-panel="${CSS.escape(id)}"]`
            ) as HTMLElement | null;
            if (panel) panel.hidden = !panel.hidden;
        });
    });
    // 待补科目:取消(收起)
    block.querySelectorAll('[data-acctfix-cancel]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = (btn as HTMLElement).dataset.acctfixCancel as string;
            const panel = block.querySelector(
                `[data-acctfix-panel="${CSS.escape(id)}"]`
            ) as HTMLElement | null;
            if (panel) panel.hidden = true;
        });
    });
    // 待补科目:补并重推
    block.querySelectorAll('[data-acctfix-submit]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = (btn as HTMLElement).dataset.acctfixSubmit as string;
            const panel = block.querySelector(
                `[data-acctfix-panel="${CSS.escape(id)}"]`
            ) as HTMLElement | null;
            if (panel) _erpExcAccountFix(id, panel, btn as HTMLButtonElement);
        });
    });
    // 绑主体:选主体后绑定并重推(开关/取消复用上面 acctfix 句柄)
    _erpExcWireBind(block);
    // 单击卡(非 checkbox/按钮/下拉/补科目面板)→ 推送详情抽屉(草稿:点异常即看详情/轨迹)
    block.querySelectorAll('.erp-exc-card').forEach((card) => {
        card.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).closest('input,button,select,.erp-exc-acctfix')) return;
            if (typeof window.showLogDetail === 'function')
                window.showLogDetail((card as HTMLElement).dataset.erpexcId);
        });
    });
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
        // 绑主体面板的主体下拉数据(同步渲染前懒取一次 · 已有缓存则跳过)
        await _erpExcEnsureClients();
        const params = new URLSearchParams();
        if (_erpExcState.q) params.set('q', _erpExcState.q);
        if (_erpExcState.cat) params.set('category', _erpExcState.cat);
        if (_erpExcState.pushType) params.set('push_type', _erpExcState.pushType);
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
        _erpExcState.idCardCount = data.id_card_count || 0;
        renderErpExceptions();
    } catch (e) {
        if (!append) block.hidden = true;
    } finally {
        _erpExcState.loading = false;
    }
}

export type { ErpExcItem };
export {
    _erpExcState,
    _erpExcFriendly,
    _erpExcRetry,
    _erpExcTok,
    loadErpExceptions,
    renderErpExceptions,
};

window._rerenderErpExceptions = renderErpExceptions;

// 暴露给 exceptions.js(loadExceptionsPage 触发加载 · 切语言重渲读状态)
window.loadErpExceptions = loadErpExceptions;
window._erpExcState = _erpExcState;
