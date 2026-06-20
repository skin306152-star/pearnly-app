// 推送日志卡片(销项重做 · 对齐草稿)· 把单条 erp_push_log 渲染成卡片:
//   状态图标 + 标题(单据号 + 类型/触发标签) + 买方 + 目标系统 + 操作(详情/重试)
//   + 失败摘要条(失败时) + meta 页脚(时间/ERP单号/HTTP/耗时/重试)。
// 从 erp-integration.ts 的表格行重排抽出(腾行数 + 单一职责)· 数据装配逻辑搬运 0 改 ·
// data-log-* 属性原样保留 → 现有点击委托(详情/重试/勾选/复制单号)不变。
/* global t, escapeHtml, currentLang, _erpSelected */

function buildErpLogCard(log: any): string {
    const time = new Date(log.created_at);
    const p2 = (n: number) => String(n).padStart(2, '0');
    const timeStr = `${p2(time.getMonth() + 1)}-${p2(time.getDate())} ${p2(time.getHours())}:${p2(time.getMinutes())}`;

    const isRetrying =
        log.status === 'failed' &&
        log.next_retry_at &&
        new Date(log.next_retry_at).getTime() > Date.now() - 60000;
    let statusClass: string, statusIcon: string, statusLabel: string;
    if (log.status === 'pending') {
        statusClass = 'retrying';
        statusIcon = '⟳';
        statusLabel = t('erp-status-pending');
    } else if (log.status === 'success') {
        statusClass = 'ok';
        statusIcon = '✓';
        statusLabel = t('erp-status-success');
    } else if (log.status === 'skipped_dup') {
        statusClass = 'skipped';
        statusIcon = '⏭';
        statusLabel = t('erp-status-skipped');
    } else if (isRetrying) {
        statusClass = 'retrying';
        statusIcon = '↻';
        statusLabel = t('erp-status-retrying');
    } else {
        statusClass = 'fail';
        statusIcon = '✗';
        statusLabel = t('erp-status-failed');
    }

    const isId = log.push_type === 'id_card';
    const typeBadge = isId
        ? `<span class="log-tag log-type-idcard">${escapeHtml(t('erp-log-type-idcard'))}</span>`
        : `<span class="log-tag log-type-invoice">${escapeHtml(t('erp-log-type-invoice'))}</span>`;
    const trig =
        log.trigger === 'auto'
            ? `<span class="log-tag auto">${escapeHtml(t('log-tag-auto'))}</span>`
            : log.trigger === 'retry'
              ? `<span class="log-tag retry">${escapeHtml(t('log-tag-retry'))}</span>`
              : `<span class="log-tag manual">${escapeHtml(t('log-tag-manual'))}</span>`;

    const friendlyReason =
        (log.error_friendly && (log.error_friendly[currentLang] || log.error_friendly.en)) || '';

    const rc = log.retry_count || 0;
    const mr = log.max_retries || 3;
    let retryInfo = '';
    if (isRetrying) {
        const nextMin = Math.max(0, Math.round((new Date(log.next_retry_at).getTime() - Date.now()) / 60000));
        retryInfo = `${t('erp-retry-attempt', { n: rc, max: mr })} · ${nextMin <= 0 ? t('erp-retry-next-soon') : t('erp-retry-next-min', { n: nextMin })}`;
    } else if (log.status === 'failed' && rc >= mr && !log.next_retry_at) {
        retryInfo = t('erp-retry-exhausted', { n: rc });
    }

    const canSelect = !isRetrying;
    const cb = canSelect
        ? `<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(log.id)}" ${_erpSelected.has(log.id) ? 'checked' : ''}>`
        : `<span class="erp-log-cb-spacer"></span>`;

    // 买方/客户(身份证订车显末4)· 卖方
    const buyerName = (log.ocr_buyer_name || '').trim() || (log.client_name || '').trim();
    const partyLabel = isId ? t('erp-log-col-idcard') : t('erp-log-col-buyer');
    const partyVal = isId
        ? log.id_card_tail
            ? '••••' + escapeHtml(log.id_card_tail)
            : '—'
        : buyerName
          ? escapeHtml(buyerName)
          : `<span class="log-client-empty">${escapeHtml(t('erp-log-client-unassigned'))}</span>`;
    const erpName = log.endpoint_name
        ? escapeHtml(log.endpoint_name)
        : `<span class="log-erp-deleted">${escapeHtml(t('erp-log-endpoint-deleted'))}</span>`;

    // ERP 单号(成功有则可复制 / 有链接则打开 / 成功但空则提示 / 否则不显)
    const extDocNo = (log.external_doc_no || '').trim();
    const extUrl = (log.external_url || '').trim();
    let docMeta = '';
    if (extUrl)
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><a href="${escapeHtml(extUrl)}" target="_blank" rel="noopener" class="log-doc-open">${escapeHtml(t('erp-log-doc-open'))}</a></span>`;
    else if (extDocNo)
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><span class="log-doc-copy" data-copy-doc="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-log-doc-copy-tip'))}">${escapeHtml(extDocNo)}</span></span>`;
    else if (log.status === 'success')
        docMeta = `<span><b>${escapeHtml(t('erp-log-col-doc'))}</b><span class="log-doc-missing">${escapeHtml(t('erp-log-doc-missing'))}</span></span>`;

    const retryBtn =
        log.status === 'failed' && !isRetrying
            ? `<button class="btn btn-sm btn-secondary" data-log-retry="${escapeHtml(log.id)}">${escapeHtml(t('erp-exc-retry'))}</button>`
            : '';

    const reasonStrip =
        statusClass === 'fail' && friendlyReason
            ? `<div class="erp-log-reason"><b>${escapeHtml(t('erp-log-fail-summary'))}</b><span>${escapeHtml(friendlyReason)}</span></div>`
            : '';

    return `
        <div class="erp-log-card ${statusClass}" data-log-detail="${escapeHtml(log.id)}">
            <div class="erp-log-card-main">
                <span class="erp-log-card-cb">${cb}</span>
                <span class="erp-log-state ${statusClass}" title="${escapeHtml(statusLabel)}">${statusIcon}</span>
                <div class="erp-log-titleblock">
                    <b title="${escapeHtml(log.invoice_no || '')}">${escapeHtml(log.invoice_no || '-')}</b>
                    <div class="erp-log-tags">${typeBadge}${trig}</div>
                </div>
                <div class="erp-log-party"><label>${escapeHtml(partyLabel)}</label><span>${partyVal}</span></div>
                <div class="erp-log-party"><label>${escapeHtml(t('erp-log-col-target'))}</label><span>${erpName}</span></div>
                <div class="erp-log-act">
                    ${retryBtn}
                    <button class="btn btn-sm btn-ghost" data-log-detail="${escapeHtml(log.id)}">${escapeHtml(t('erp-log-detail-btn'))}</button>
                </div>
            </div>
            ${reasonStrip}
            <div class="erp-log-meta">
                <span><b>${escapeHtml(t('erp-log-col-time'))}</b>${escapeHtml(timeStr)}</span>
                ${docMeta}
                <span><b>HTTP</b>${log.http_status || '—'}</span>
                <span><b>${escapeHtml(t('erp-log-col-elapsed'))}</b>${log.elapsed_ms != null ? log.elapsed_ms + 'ms' : '—'}</span>
                ${retryInfo ? `<span><b>${escapeHtml(t('erp-log-col-retry'))}</b>${escapeHtml(retryInfo)}</span>` : ''}
            </div>
        </div>`;
}

window.buildErpLogCard = buildErpLogCard;
