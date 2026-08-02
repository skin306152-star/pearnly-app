// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 · 会话列表/汇总/列表模式 · 从 bank-recon.js 抽出
// verbatim 0 改逻辑。
// ============================================================
/* global token, showConfirm */
import { S } from './bank-recon-store.js';
import { formatDate, formatPeriod, esc } from './bank-recon-helpers.js';
import { loadSessionDetail, renderDetailMeta, renderTxTable } from './bank-recon-detail.js';
import { _renderClientBadge } from './bank-recon-picker.js';
import { listErrorHtml } from './list-error-state.js';

type Session = Record<string, any>;

// 取数失败 ≠ 一份对账都没传过。清成 [] 就只剩「长度 0」这一个信号,渲染必然落空态。
let _sessionsFailed = false;

// ---------- API 调用 ----------
async function refreshSessions() {
    try {
        const resp = await fetch('/api/bank-recon/sessions?limit=30', {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) throw new Error('sessions:' + resp.status);
        S.sessions = await resp.json();
        _sessionsFailed = false;
        renderSessionList();
    } catch (e) {
        console.warn('[bank-recon] loadSessions failed', e);
        _sessionsFailed = true;
        S.sessions = [];
        renderSessionList();
    }
}

// ---------- 渲染 ----------
function refreshSummary() {
    const pill = document.getElementById('bank-status-summary');
    if (!pill) return;
    // 拉不到就别摆状态:此前 total===0 一律说「还没有对账」,失败时那句话是替后端编的。
    pill.style.display = _sessionsFailed ? 'none' : '';
    if (_sessionsFailed) return;
    const total = S.sessions.length;
    if (total === 0) {
        pill.textContent = t('bank-pill-none');
        return;
    }
    // 统计未完全匹配的
    let pending = 0;
    for (const s of S.sessions as Session[]) {
        if (s.parse_status === 'parsed' && (s.unmatched_count || 0) > 0) pending++;
    }
    pill.textContent =
        pending > 0
            ? t('bank-pill-pending').replace('{n}', pending as unknown as string)
            : t('bank-pill-ok');
}

function renderSessionList() {
    const list = document.getElementById('bank-sessions-list');
    if (!list) return;
    // 重试委托挂一次(错误态的钮由本模块渲染,后续重渲不重复绑)。
    if (!(list as HTMLElement).dataset.bankSessRetryBound) {
        (list as HTMLElement).dataset.bankSessRetryBound = '1';
        list.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).closest('[data-bank-sess-retry]')) refreshSessions();
        });
    }
    if (_sessionsFailed) {
        list.innerHTML = listErrorHtml('bank-sessions-error-title', 'data-bank-sess-retry');
        return;
    }
    // 筛选
    let visible = S.sessions || [];
    if (S.sessionFilter === 'parsed') {
        visible = (visible as Session[]).filter((s: Session) => s.parse_status === 'parsed');
    } else if (S.sessionFilter === 'failed') {
        visible = (visible as Session[]).filter((s: Session) => s.parse_status === 'parse_failed');
    }
    if (!S.sessions || S.sessions.length === 0) {
        list.innerHTML =
            '<div class="bank-empty" data-i18n="bank-sessions-empty">' +
            t('bank-sessions-empty') +
            '</div>';
        return;
    }
    if (visible.length === 0) {
        list.innerHTML = '<div class="bank-empty">' + t('bank-sess-filter-empty') + '</div>';
        return;
    }
    list.innerHTML = (visible as Session[]).map((s: Session) => renderSessionRow(s)).join('');
    // 行点击 → 进会话详情 · 但点垃圾桶不能触发
    list.querySelectorAll('.bank-session-row').forEach((row) => {
        row.addEventListener('click', (e) => {
            if ((e.target as HTMLElement).closest('.bank-session-trash')) return; // 点的是垃圾桶 · 跳过
            loadSessionDetail((row as HTMLElement).dataset.sessionId!);
        });
    });
    // 垃圾桶绑定
    list.querySelectorAll('.bank-session-trash').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const sid = (btn as HTMLElement).dataset.sessionId;
            const fname = (btn as HTMLElement).dataset.sessionName || '';
            handleDeleteSessionFromList(sid, fname);
        });
    });
}

// v118.26.1.1 · 共用删除函数 · 自动化 tab 列表 + 对账中心列表都用
async function handleDeleteSessionFromList(sessionId: any, fname: any) {
    if (!sessionId) return;
    const msg = (t('bank-session-delete-confirm') || '确定删除这条对账记录吗?').replace(
        '{name}',
        fname || ''
    );
    const ok = await showConfirm(msg, { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch('/api/bank-recon/sessions/' + encodeURIComponent(sessionId), {
            method: 'DELETE',
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) throw new Error('delete:' + resp.status);
        showToast(t('bank-deleted'), 'success');
        // 如果当前正打开这个会话 · 退回列表
        if (S.currentSession && (S.currentSession as Session).id === sessionId) {
            S.currentSession = null;
            S.currentTxs = [];
            showListMode();
        }
        await refreshSessions();
        // 对账中心首页也刷
        if (typeof window.loadReconcilePage === 'function') {
            window.loadReconcilePage();
        }
    } catch (e) {
        console.warn('[bank-recon] delete failed', e);
        showToast(t('bank-delete-failed'), 'error');
    }
}

function renderSessionRow(s: Session) {
    const bank = (s.bank_code || 'OTHER').toUpperCase();
    const period = formatPeriod(s.period_start, s.period_end);
    const acct = s.account_last4 ? '···' + s.account_last4 : '';
    const counts = renderSessionCounts(s);
    const dateStr = formatDate(s.created_at);
    return `
        <div class="bank-session-row" data-session-id="${esc(s.id)}">
            <div class="bank-session-bank bk-${esc(bank)}">${esc(bank)}</div>
            <div class="bank-session-info">
                <div class="bank-session-title">${esc(s.source_filename || period || '-')}</div>
                <div class="bank-session-meta">${esc(period)} · ${esc(acct)} · ${esc(dateStr)}</div>
            </div>
            <div class="bank-session-counts">${counts}</div>
            <button class="bank-session-trash" data-session-id="${esc(s.id)}" data-session-name="${esc(s.source_filename || '')}" title="${esc(t('bank-session-delete-tip') || '删除')}">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/>
                </svg>
            </button>
            <div class="bank-session-arrow">
                <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
            </div>
        </div>
    `;
}

function renderSessionCounts(s: Session) {
    if (s.parse_status === 'parse_failed') {
        return `<span class="bank-session-count cnt-failed">${t('bank-count-parse-failed')}</span>`;
    }
    if (s.parse_status !== 'parsed') {
        return `<span class="bank-session-count">${t('bank-count-parsing')}</span>`;
    }
    const total = s.tx_count || 0;
    const matched = s.matched_count || 0;
    const unmatched = s.unmatched_count || 0;
    const parts = [`<span class="bank-session-count">${total} ${t('bank-count-tx')}</span>`];
    if (matched > 0)
        parts.push(
            `<span class="bank-session-count cnt-matched">${matched} ${t('bank-count-matched')}</span>`
        );
    if (unmatched > 0)
        parts.push(
            `<span class="bank-session-count cnt-unmatched">${unmatched} ${t('bank-count-unmatched')}</span>`
        );
    return parts.join('');
}

function showDetailMode() {
    document.getElementById('bank-detail')!.style.display = '';
    (document.querySelector('.bank-sessions-section') as HTMLElement).style.display = 'none';
    renderDetailMeta();
    renderTxTable();
    // v118.26.2 · 渲染客户徽章
    _renderClientBadge();
}

function showListMode() {
    document.getElementById('bank-detail')!.style.display = 'none';
    (document.querySelector('.bank-sessions-section') as HTMLElement).style.display = '';
    // v118.26.2 · 退出 detail 顺手关 pane(切回列表不残留)
    const detailBody = document.getElementById('bank-detail-body');
    if (detailBody) detailBody.classList.remove('has-pane');
    S.currentTxForDrawer = null;
}

export {
    refreshSessions,
    refreshSummary,
    renderSessionList,
    handleDeleteSessionFromList,
    showDetailMode,
    showListMode,
};
