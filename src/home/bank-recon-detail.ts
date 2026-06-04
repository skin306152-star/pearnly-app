// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 会话详情 + 流水表 + 匹配/删除/忽略处理 · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================
/* global token, showConfirm */
import { S } from './bank-recon-store.js';
import { fmtAmt, formatPeriod, formatDate, esc } from './bank-recon-helpers.js';
import { showDetailMode, showListMode, refreshSessions } from './bank-recon-sessions.js';
import { openCandDrawer, closeCandDrawer } from './bank-recon-drawer.js';

type BankSession = {
    id: string;
    bank_code?: string;
    account_last4?: string;
    source_filename?: string;
    period_start?: string;
    period_end?: string;
    opening_balance?: number;
    total_inflow?: number;
    total_outflow?: number;
    closing_balance?: number;
};
type BankTx = {
    id: string;
    match_status?: string;
    direction?: string;
    channel?: string;
    description?: string;
    amount?: number;
    tx_date?: string;
};

async function loadSessionDetail(sessionId: string) {
    try {
        const url =
            '/api/bank-recon/sessions/' +
            encodeURIComponent(sessionId) +
            (S.currentFilter !== 'all' ? '?filter=' + S.currentFilter : '');
        const resp = await fetch(url, { headers: { Authorization: 'Bearer ' + token } });
        if (!resp.ok) throw new Error('detail:' + resp.status);
        const data = await resp.json();
        S.currentSession = data.session;
        S.currentTxs = data.transactions || [];
        showDetailMode();
    } catch (e) {
        console.warn('[bank-recon] loadSessionDetail failed', e);
        showToast(t('bank-load-failed'), 'error');
    }
}

async function handleRunMatch() {
    if (!S.currentSession) return;
    const btn = document.getElementById('btn-bank-run-match') as HTMLButtonElement;
    const origHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>' + t('bank-matching') + '</span>';
    try {
        const resp = await fetch(
            '/api/bank-recon/sessions/' +
                encodeURIComponent((S.currentSession as BankSession).id) +
                '/match',
            {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
            }
        );
        if (!resp.ok) throw new Error('match:' + resp.status);
        const stats = await resp.json();
        showToast(
            t('bank-match-done')
                .replace('{matched}', stats.matched)
                .replace('{suggested}', stats.suggested)
                .replace('{unmatched}', stats.unmatched),
            'success'
        );
        // 刷详情
        await loadSessionDetail((S.currentSession as BankSession).id);
        await refreshSessions();
    } catch (e) {
        console.warn('[bank-recon] match failed', e);
        showToast(t('bank-match-failed'), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = origHTML;
    }
}

async function handleDeleteSession() {
    if (!S.currentSession) return;
    const ok = await showConfirm(t('bank-delete-confirm'), { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch(
            '/api/bank-recon/sessions/' + encodeURIComponent((S.currentSession as BankSession).id),
            {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            }
        );
        if (!resp.ok) throw new Error('delete:' + resp.status);
        showToast(t('bank-deleted'), 'success');
        S.currentSession = null;
        S.currentTxs = [];
        showListMode();
        await refreshSessions();
    } catch (e) {
        console.warn('[bank-recon] delete failed', e);
        showToast(t('bank-delete-failed'), 'error');
    }
}

async function handleIgnoreTx() {
    if (!S.currentTxForDrawer) return;
    try {
        const resp = await fetch(
            '/api/bank-recon/tx/' +
                encodeURIComponent((S.currentTxForDrawer as BankTx).id) +
                '/override',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: 'ignored' }),
            }
        );
        if (!resp.ok) throw new Error('ignore:' + resp.status);
        closeCandDrawer();
        await loadSessionDetail((S.currentSession as BankSession).id);
    } catch (e) {
        showToast(t('bank-action-failed'), 'error');
    }
}

async function handlePickCandidate(historyId: string) {
    if (!S.currentTxForDrawer) return;
    try {
        const resp = await fetch(
            '/api/bank-recon/tx/' +
                encodeURIComponent((S.currentTxForDrawer as BankTx).id) +
                '/override',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + token,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: 'matched', history_id: historyId }),
            }
        );
        if (!resp.ok) throw new Error('pick:' + resp.status);
        showToast(t('bank-matched-ok'), 'success');
        closeCandDrawer();
        await loadSessionDetail((S.currentSession as BankSession).id);
    } catch (e) {
        showToast(t('bank-action-failed'), 'error');
    }
}

function renderDetailMeta() {
    if (!S.currentSession) return;
    const s = S.currentSession as BankSession;
    document.getElementById('bank-detail-title')!.textContent =
        (s.bank_code || '-') +
        (s.account_last4 ? ' ···' + s.account_last4 : '') +
        ' · ' +
        (s.source_filename || '');
    document.getElementById('bank-meta-period')!.textContent =
        formatPeriod(s.period_start, s.period_end) || '-';
    document.getElementById('bank-meta-opening')!.textContent = fmtAmt(s.opening_balance);
    document.getElementById('bank-meta-inflow')!.textContent = '+' + fmtAmt(s.total_inflow);
    document.getElementById('bank-meta-outflow')!.textContent = '-' + fmtAmt(s.total_outflow);
    document.getElementById('bank-meta-closing')!.textContent = fmtAmt(s.closing_balance);

    // v118.26.1 · 4 个 chip 全部从 S.currentTxs 实时数 · 不读 session 字段
    // (修上次发现的 bug:save_bank_recon_parse 没回写 unmatched_count · 顶部 chip 永远 0)
    const txs = S.currentTxs || [];
    const total = txs.length;
    let nMatched = 0,
        nSuggested = 0,
        nUnmatched = 0;
    for (const x of txs as BankTx[]) {
        const ms = x.match_status || 'unmatched';
        if (ms === 'matched') nMatched++;
        else if (ms === 'suggested') nSuggested++;
        else nUnmatched++; // unmatched + ignored 都计入未匹配
    }
    document.getElementById('bank-stat-total')!.textContent = total as unknown as string;
    document.getElementById('bank-stat-matched')!.textContent = nMatched as unknown as string;
    document.getElementById('bank-stat-suggested')!.textContent = nSuggested as unknown as string;
    document.getElementById('bank-stat-unmatched')!.textContent = nUnmatched as unknown as string;
}

function renderTxTable() {
    const tbody = document.getElementById('bank-tx-tbody');
    if (!tbody) return;
    let txs = S.currentTxs || [];
    if (S.currentFilter !== 'all') {
        txs = (txs as BankTx[]).filter((x: BankTx) => {
            if (S.currentFilter === 'matched') return x.match_status === 'matched';
            if (S.currentFilter === 'suggested') return x.match_status === 'suggested';
            if (S.currentFilter === 'unmatched')
                return x.match_status === 'unmatched' || x.match_status === 'ignored';
            return true;
        });
    }
    if (txs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="bank-empty">${t('bank-tx-empty')}</td></tr>`;
        return;
    }
    tbody.innerHTML = txs.map((tx) => renderTxRow(tx as BankTx)).join('');
    tbody.querySelectorAll('tr[data-tx-id]').forEach((row) => {
        row.addEventListener('click', () => {
            const id = (row as HTMLElement).dataset.txId;
            const tx = (S.currentTxs as BankTx[]).find((x: BankTx) => x.id === id);
            if (!tx) return;
            // v118.26.2 · 高亮选中行 · 切到新行清旧
            tbody
                .querySelectorAll('tr.is-selected')
                .forEach((r) => r.classList.remove('is-selected'));
            row.classList.add('is-selected');
            openCandDrawer(tx);
        });
    });
    // v118.26.2 · 重渲后保持上次选中(切 filter 不丢)
    if (S.currentTxForDrawer) {
        const sel = tbody.querySelector(
            'tr[data-tx-id="' + (S.currentTxForDrawer as BankTx).id + '"]'
        );
        if (sel) sel.classList.add('is-selected');
    }
}

function renderTxRow(tx: BankTx) {
    const isOut = tx.direction === 'OUT';
    const sign = isOut ? '-' : '+';
    const cls = isOut ? 'bank-out' : 'bank-in';
    const status = tx.match_status || 'unmatched';
    const statusLabel = t('bank-match-' + status) || status;
    const date = formatDate(tx.tx_date);
    const channel = tx.channel ? `<span class="bank-tx-channel">${esc(tx.channel)}</span>` : '';
    return `
        <tr data-tx-id="${esc(tx.id)}">
            <td class="bank-tx-date">${esc(date)}</td>
            <td class="bank-tx-desc">${channel}${esc(tx.description || '-')}</td>
            <td class="bank-td-amount ${cls}">${sign}${fmtAmt(tx.amount)}</td>
            <td><span class="bank-tx-match mt-${status}">${esc(statusLabel)}</span></td>
        </tr>
    `;
}

export {
    loadSessionDetail,
    handleRunMatch,
    handleDeleteSession,
    handleIgnoreTx,
    handlePickCandidate,
    renderDetailMeta,
    renderTxTable,
};
