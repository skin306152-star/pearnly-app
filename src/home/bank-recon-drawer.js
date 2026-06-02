// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 候选匹配抽屉 · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================
/* global token, showConfirm */
import { S } from './bank-recon-store.js';
import { _scoreBadge, fmtAmt, formatDate, esc } from './bank-recon-helpers.js';
import { loadSessionDetail, handlePickCandidate } from './bank-recon-detail.js';

// ---------- v118.26.2 · 右半屏候选 pane(取代旧 fixed drawer)----------
async function openCandDrawer(tx) {
    S.currentTxForDrawer = tx;
    // 切到 grid 双栏(桌面) · 移动端样式自动改成底部 drawer
    const detailBody = document.getElementById('bank-detail-body');
    if (detailBody) detailBody.classList.add('has-pane');

    const titleEl = document.getElementById('bank-cand-pane-title');
    const subEl = document.getElementById('bank-cand-pane-sub');
    const foot = document.getElementById('bank-cand-pane-foot');
    if (titleEl) titleEl.textContent = t('bank-cand-pane-current');
    if (subEl) {
        const sign = tx.direction === 'OUT' ? '-' : '+';
        const cls = tx.direction === 'OUT' ? 'bank-out' : 'bank-in';
        subEl.innerHTML = `${esc(formatDate(tx.tx_date))}
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <span>${esc(tx.description || '-')}</span>
            <span style="margin:0 6px;color:#D1D5DB">·</span>
            <strong class="${cls}">${sign}${fmtAmt(tx.amount)}</strong>`;
    }
    if (foot) foot.style.display = '';

    const body = document.getElementById('bank-cand-pane-body');
    if (!body) return;
    body.innerHTML = `<div class="bank-empty">${t('bank-cand-loading')}</div>`;

    // 拉 top 5 候选 + 发票字段
    try {
        const resp = await fetch(
            '/api/bank-recon/tx/' + encodeURIComponent(tx.id) + '/candidates',
            {
                headers: { Authorization: 'Bearer ' + token },
            }
        );
        if (!resp.ok) throw new Error('cands:' + resp.status);
        const data = await resp.json();
        renderCandBody(tx, data.candidates || []);
    } catch (e) {
        body.innerHTML = `<div class="bank-empty">${t('bank-cand-load-failed')}</div>`;
    }
}

function _candCard(tx, c, isCurrentMatched) {
    const hid = c.history_id;
    const inv = c.invoice_no || '-';
    const vendor = c.vendor || '-';
    const amt =
        c.amount_total !== null && c.amount_total !== undefined ? fmtAmt(c.amount_total) : '-';
    const idate = c.invoice_date ? formatDate(c.invoice_date) : '-';
    const fname = c.filename || '';

    const isPicked = !!isCurrentMatched && tx.matched_history_id === hid;
    const cardCls =
        'bank-cand-card' + (c.is_auto_picked ? ' is-auto' : '') + (isPicked ? ' is-picked' : '');

    let actHtml = '';
    if (isPicked) {
        actHtml =
            '<button class="btn btn-ghost btn-small" data-act="unmatch">' +
            '<span>' +
            t('bank-cand-unmatch') +
            '</span>' +
            '</button>';
    } else {
        actHtml =
            '<button class="btn btn-primary btn-small" data-act="pick" data-hid="' +
            esc(hid) +
            '">' +
            '<span>' +
            t(c.is_auto_picked ? 'bank-cand-confirm' : 'bank-cand-pick-this') +
            '</span>' +
            '</button>';
    }

    return (
        '<div class="' +
        cardCls +
        '" data-hid="' +
        esc(hid) +
        '">' +
        '<div class="bank-cand-card-head">' +
        '<div class="bank-cand-card-vendor">' +
        esc(vendor) +
        '</div>' +
        _scoreBadge(c.score) +
        '</div>' +
        '<div class="bank-cand-card-fields">' +
        '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
        t('bank-cand-fld-invoice-no') +
        '</span> ' +
        esc(inv) +
        '</span>' +
        '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
        t('bank-cand-fld-amount') +
        '</span> ' +
        amt +
        '</span>' +
        '<span class="bank-cand-field"><span class="bank-cand-flabel">' +
        t('bank-cand-fld-date') +
        '</span> ' +
        esc(idate) +
        '</span>' +
        '</div>' +
        (fname
            ? '<div class="bank-cand-card-file" title="' + esc(fname) + '">' + esc(fname) + '</div>'
            : '') +
        (c.reason ? '<div class="bank-cand-card-reason">' + esc(c.reason) + '</div>' : '') +
        '<div class="bank-cand-card-actions">' +
        actHtml +
        '</div>' +
        '</div>'
    );
}

function renderCandBody(tx, candidates) {
    // v118.26.2 · 渲染目标改成新 inline pane body
    const body = document.getElementById('bank-cand-pane-body');
    if (!body) return;
    const list = candidates || [];

    // 头部小提示:auto-picked / suggested / unmatched 三种状态
    let headHint = '';
    if (tx.match_status === 'matched') {
        headHint =
            '<div class="bank-cand-hint hint-matched">' +
            t('bank-cand-hint-matched').replace('{n}', list.length) +
            '</div>';
    } else if (tx.match_status === 'suggested') {
        headHint =
            '<div class="bank-cand-hint hint-suggested">' +
            t('bank-cand-hint-suggested').replace('{n}', list.length) +
            '</div>';
    } else if (list.length > 0) {
        headHint =
            '<div class="bank-cand-hint hint-low">' +
            t('bank-cand-hint-low').replace('{n}', list.length) +
            '</div>';
    } else {
        // 0 候选 · 空态卡片
        body.innerHTML = '<div class="bank-empty">' + t('bank-cand-no-match-detail') + '</div>';
        return;
    }

    const isMatched = tx.match_status === 'matched';
    const cards = list.map((c) => _candCard(tx, c, isMatched)).join('');
    body.innerHTML = headHint + '<div class="bank-cand-list">' + cards + '</div>';

    // 绑事件
    body.querySelectorAll('[data-act="pick"]').forEach((btn) => {
        btn.addEventListener('click', () => {
            handlePickCandidate(btn.dataset.hid);
        });
    });
    body.querySelectorAll('[data-act="unmatch"]').forEach((btn) => {
        btn.addEventListener('click', async () => {
            try {
                await fetch('/api/bank-recon/tx/' + encodeURIComponent(tx.id) + '/override', {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: 'unmatched' }),
                });
                closeCandDrawer();
                await loadSessionDetail(S.currentSession.id);
            } catch (e) {
                showToast(t('bank-action-failed'), 'error');
            }
        });
    });
}

function closeCandDrawer() {
    // v118.26.2 · 关闭 = 从 grid 双栏退出 + 清空 pane + 取消行高亮
    const detailBody = document.getElementById('bank-detail-body');
    if (detailBody) detailBody.classList.remove('has-pane');
    const titleEl = document.getElementById('bank-cand-pane-title');
    const subEl = document.getElementById('bank-cand-pane-sub');
    const body = document.getElementById('bank-cand-pane-body');
    const foot = document.getElementById('bank-cand-pane-foot');
    if (titleEl) titleEl.textContent = t('bank-cand-pane-empty-title');
    if (subEl) subEl.textContent = t('bank-cand-pane-empty-sub');
    if (foot) foot.style.display = 'none';
    if (body) {
        body.innerHTML =
            '<div class="bank-cand-pane-empty">' +
            '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">' +
            '<rect x="14" y="10" width="36" height="44" rx="3"/>' +
            '<path d="M22 22h20M22 30h20M22 38h12"/></svg>' +
            '<div>' +
            t('bank-cand-pane-empty-hint') +
            '</div></div>';
    }
    const tbody = document.getElementById('bank-tx-tbody');
    if (tbody) {
        tbody.querySelectorAll('tr.is-selected').forEach((r) => r.classList.remove('is-selected'));
    }
    S.currentTxForDrawer = null;
}

export { openCandDrawer, closeCandDrawer };
