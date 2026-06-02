// ============================================================
// REFACTOR-WB-modularize · ERP 推送异常【单条编辑弹窗】从 erp-exceptions.js 拆出
//
// _erpExcOpenEdit(选/绑 ERP 客户 + 商品 picker + 重试)· 共享状态/助手经 erp-exceptions.js import。
// ============================================================
/* global escapeHtml */
/* eslint-disable no-useless-assignment -- verbatim exceptions.js · 非 bug */
import { _erpExcState, _erpExcFriendly, _erpExcRetry, _erpExcTok } from './erp-exceptions.js';
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
    // DMS 闭环修正(Zihao 2026-06-01)· 身份证订车弹窗按 DMS 标签(订车单号/客户·无买方/无ERP客户)·
    // 不裸露 ERR_* 码(友好原因已在上方显示)。
    const isId = it.push_type === 'id_card';
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
                <div class="erp-exc-m-reason"><span class="erp-exc-state ${stateCls}">${escapeHtml(t('erp-exc-state-' + (it.state || 'failed')))}</span> ${escapeHtml(reason)}${it.error_code && !isId ? ` <span class="erp-exc-code">${escapeHtml(it.error_code)}</span>` : ''}</div>
                ${dRow(isId ? t('erp-log-col-booking') : t('erp-exc-f-invoice'), it.invoice_no)}
                ${dRow(isId ? t('erp-log-col-customer') : t('erp-exc-f-seller'), it.seller_name)}
                ${
                    isId
                        ? dRow(
                              t('erp-log-col-idcard'),
                              it.id_card_tail ? '••••' + it.id_card_tail : '—'
                          )
                        : dRow(t('erp-exc-f-buyer'), it.ocr_buyer_name) +
                          dRow(t('erp-exc-edit-field-current'), it.client_name)
                }
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
