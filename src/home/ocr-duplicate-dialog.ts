// ============================================================
// REFACTOR-C1-home-batch5 (2026-05-31) · OCR 重复发票警告对话框 从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · showDuplicateDialog(逐张处理 window._dupQueue)。
// 桥回:window.showDuplicateDialog(ocr-recognize.js 的 btn-start handler 批量识别完调)。
// ============================================================
/* global _results, escapeHtml, openHistoryDrawer, token */

// v0.13 · 重复发票警告对话框(逐张处理 · 用户操作完一条 → 显示下一条)
function showDuplicateDialog() {
    if (!window._dupQueue || !window._dupQueue.length) return;
    const w = window._dupQueue!.shift()! as {
        level?: unknown;
        invoice_total: number;
        invoice_index?: unknown;
        matched_fields?: string[];
        filename?: unknown;
        current: Record<string, unknown>;
        match: Record<string, unknown>;
        new_history_id?: unknown;
    };

    const isExact = w.level === 'exact';
    const titleKey = isExact ? 'dup-title-exact' : 'dup-title-likely';
    const descKey = isExact ? 'dup-desc-exact' : 'dup-desc-likely';
    const titleColor = isExact ? '#DC2626' : '#D97706';
    const titleBg = isExact ? '#FEE2E2' : '#FEF3C7';

    const fmtAmt = (v: unknown) =>
        v != null
            ? Number(v).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
              })
            : '—';
    const fmtDate = (v: unknown) => v || '—';
    const fmtCreated = (v: unknown) => {
        try {
            const d = new Date(v as string);
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        } catch {
            return v;
        }
    };
    const partLabel =
        w.invoice_total > 1
            ? ` · ${t('invoice-part-of', { i: w.invoice_index, n: w.invoice_total })}`
            : '';

    const matchedFieldsHtml = (w.matched_fields || [])
        .map((k) => {
            const lbl = t('dup-field-' + k.replace('_', '-')) || k;
            return `<span class="dup-field-chip">${escapeHtml(lbl)}</span>`;
        })
        .join(' ');

    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box dup-dialog">
            <div class="dup-head" style="background:${titleBg};">
                <div class="dup-title" style="color:${titleColor};">
                    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:22px;height:22px;vertical-align:-5px;margin-right:6px;">
                        <path d="M10 2.5L1 17h18L10 2.5z"/><path d="M10 8v4M10 14v0.5"/>
                    </svg>
                    ${escapeHtml(t(titleKey))}
                </div>
                <button class="log-detail-close dup-close" type="button">✕</button>
            </div>
            <div class="dup-body">
                <div class="dup-desc">${escapeHtml(t(descKey))}</div>
                <div class="dup-source">
                    <div class="dup-source-label">${escapeHtml(t('dup-current-file'))}${escapeHtml(partLabel)}</div>
                    <div class="dup-source-name">${escapeHtml(w.filename)}</div>
                </div>
                <div class="dup-matched-label">${escapeHtml(t('dup-matched-on'))} ${matchedFieldsHtml}</div>
                <table class="dup-compare">
                    <thead>
                        <tr>
                            <th></th>
                            <th>${escapeHtml(t('dup-this-one'))}</th>
                            <th>${escapeHtml(t('dup-existing-one'))}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>${escapeHtml(t('dup-field-invoice-no'))}</td><td>${escapeHtml(w.current.invoice_no || '—')}</td><td>${escapeHtml(w.match.invoice_no || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-invoice-date'))}</td><td>${escapeHtml(fmtDate(w.current.invoice_date))}</td><td>${escapeHtml(fmtDate(w.match.invoice_date))}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-seller-name'))}</td><td>${escapeHtml(w.current.seller_name || '—')}</td><td>${escapeHtml(w.match.seller_name || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-total-amount'))}</td><td>${fmtAmt(w.current.total_amount)}</td><td>${fmtAmt(w.match.total_amount)}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-original-file'))}</td><td>—</td><td>${escapeHtml(w.match.filename || '—')}</td></tr>
                        <tr><td>${escapeHtml(t('dup-field-uploaded-at'))}</td><td>—</td><td>${escapeHtml(fmtCreated(w.match.created_at))}</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="dup-actions">
                <button class="btn btn-ghost btn-tiny" data-action="view">${escapeHtml(t('dup-action-view'))}</button>
                <button class="btn btn-danger btn-tiny" data-action="delete">${escapeHtml(t('dup-action-delete'))}</button>
                <button class="btn btn-primary btn-tiny" data-action="keep">${escapeHtml(t('dup-action-keep'))}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    const close = () => {
        modal.remove();
        // 处理下一条
        if (window._dupQueue && window._dupQueue.length) {
            setTimeout(showDuplicateDialog, 200);
        }
    };
    modal.querySelector('.dup-close')!.addEventListener('click', close);

    modal.querySelector('[data-action="view"]')!.addEventListener('click', () => {
        // 跳到历史页 · 打开原记录抽屉
        const matchId = w.match.id;
        window.location.hash = '#/history';
        setTimeout(() => {
            if (typeof openHistoryDrawer === 'function') openHistoryDrawer(matchId);
        }, 400);
        close();
    });

    modal.querySelector('[data-action="delete"]')!.addEventListener('click', async () => {
        // 删除"刚刚新建的这条"(因为是重复 · 用户决定不要)
        const newId = w.new_history_id;
        if (!newId) {
            close();
            return;
        }
        try {
            const resp = await fetch(`/api/history/${encodeURIComponent(newId as string)}`, {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + token },
            });
            if (resp.ok) {
                showToast(t('dup-deleted-toast'), 'success');
            } else {
                showToast(t('dup-delete-failed'), 'error');
            }
        } catch (e) {
            showToast(t('dup-delete-failed'), 'error');
        }
        close();
    });

    modal.querySelector('[data-action="keep"]')!.addEventListener('click', close);
}

// 桥回:ocr-recognize.js 调
window.showDuplicateDialog = showDuplicateDialog;
