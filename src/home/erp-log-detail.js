// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送日志「详情弹窗 + 复制单号」从 erp-integration.js 抽出
//
// 来源:erp-integration.js copyErpDocNo + showLogDetail(日志详情 modal · ~270 行)· verbatim 0 改逻辑。
// 列表/批量/轮询组留 erp-integration.js。initAutomationPage 行点击经 window.showLogDetail/copyErpDocNo 调本模块。
// 详情内「重试推送」按钮经 window.retryPushLog 调 erp-integration.js(留在那)。
// ============================================================
/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

// 临时任务 (Zihao 2026-05-26) · 复制 ERP 单号(列表 / 凭证弹窗共用)·
// 带 clipboard API 失败时的 textarea+execCommand 降级(http 环境 / 权限禁用)。
async function copyErpDocNo(docNo) {
    docNo = (docNo || '').trim();
    if (!docNo) return;
    try {
        await navigator.clipboard.writeText(docNo);
        showToast(t('erp-doc-copy-ok', { no: docNo }), 'success');
    } catch (err) {
        try {
            const ta = document.createElement('textarea');
            ta.value = docNo;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            ta.remove();
            showToast(t('erp-doc-copy-ok', { no: docNo }), 'success');
        } catch (e2) {
            showToast(t('erp-doc-copy-fail'), 'error');
        }
    }
}

async function showLogDetail(logId) {
    // v0.10 · 立即弹窗显示 loading · 再请求
    const modal = document.createElement('div');
    modal.className = 'log-detail-modal';
    modal.innerHTML = `
        <div class="log-detail-box">
            <div class="log-detail-loading">${escapeHtml(t('log-detail-loading'))}</div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', async (e) => {
        if (e.target === modal || e.target.classList.contains('log-detail-close')) {
            modal.remove();
            return;
        }
        // 临时任务 (Zihao 2026-05-26) · 凭证弹窗里的复制 ERP 单号
        const copyEl = e.target.closest('[data-receipt-copy]');
        if (copyEl) {
            copyErpDocNo(copyEl.dataset.receiptCopy);
            return;
        }
        // 失败态建议动作 · 跳转后关弹窗
        const actEl = e.target.closest('[data-receipt-action]');
        if (actEl) {
            const act = actEl.dataset.receiptAction;
            if (act === 'retry') {
                window.retryPushLog(actEl.dataset.logId);
            } else if (act === 'exceptions') {
                if (typeof routeTo === 'function') routeTo('exceptions');
            } else if (act === 'mappings') {
                if (typeof routeTo === 'function') routeTo('integrations');
            }
            modal.remove();
            return;
        }
    });

    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}`, {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            modal.remove();
            return;
        }
        const log = await resp.json();

        // 临时任务 (Zihao 2026-05-26) · 把"成功/失败提示"升级成"ERP 推送凭证弹窗"。
        // 端点名优先用后端 join 出来的 endpoint_name(详情 API 已带),兜底查本地 cache。
        const ep = window._erpEndpoints.find((x) => x.id === log.endpoint_id);
        const epName =
            log.endpoint_name ||
            (ep ? ep.name : log.endpoint_id ? t('erp-log-endpoint-deleted') : '-');
        const adapter = (log.endpoint_adapter || (ep && ep.adapter) || '').toLowerCase();

        const time = new Date(log.created_at).toLocaleString();
        const triggerText =
            log.trigger === 'auto'
                ? t('log-tag-auto')
                : log.trigger === 'retry'
                  ? t('log-tag-retry')
                  : t('log-tag-manual');

        const reqJson = log.request_body
            ? JSON.stringify(log.request_body, null, 2)
            : t('erp-receipt-no-tech');
        const respBody = log.response_body || t('erp-receipt-no-tech');

        const isOk = log.status === 'success';
        // P2-10: 成功推送时友好显示行数
        let respDisplay =
            typeof respBody === 'string' ? respBody : JSON.stringify(respBody, null, 2);
        if (isOk) {
            try {
                const rj =
                    typeof log.response_body === 'string'
                        ? JSON.parse(log.response_body)
                        : log.response_body || {};
                const rows =
                    rj.row_count || (Array.isArray(rj.imported_rows) ? rj.imported_rows.length : 0);
                if (rows > 0) respDisplay = t('log-push-rows').replace('{n}', String(rows));
            } catch (e) {
                /* 保留原始 */
            }
        }

        // 通用 ERP 单号字段(后端日志 API 派生 · 不写死 MR.ERP)
        const extDocNo = (log.external_doc_no || '').trim();
        const extUrl = (log.external_url || '').trim();
        const extHint = (log.external_doc_hint || '').trim();

        // 发票买方(OCR 真买方名优先 · 退回已归属 client_name)+ 卖家 + 金额格式化
        const clientName = (log.ocr_buyer_name || '').trim() || log.client_name || '-';
        const sellerName = log.seller_name || '-';
        // DMS 闭环修正(Zihao 2026-06-01)· 身份证订车推送详情按 DMS 字段:发票号→订车单号、
        // 发票卖方→客户;无"发票买方"概念 → 跳过该行。不再用发票标签框身份证订车。
        const isIdCard = log.push_type === 'id_card';
        let amountStr = '-';
        const amtNum = Number(log.total_amount);
        if (log.total_amount != null && log.total_amount !== '' && !isNaN(amtNum)) {
            amountStr = amtNum.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
        }

        const summaryText = isOk ? t('erp-receipt-title-ok') : t('erp-receipt-title-fail');
        const summaryIcon = isOk ? '✓' : '✗';

        // 凭证主体:一行一项 key-value(label 固定宽 · value 自适应 · 见 .erp-receipt-row CSS)
        const rowsHtml = [];
        const addRow = (label, valueHtml) => {
            rowsHtml.push(`
                <div class="erp-receipt-row">
                    <span class="erp-receipt-key">${escapeHtml(label)}</span>
                    <span class="erp-receipt-val">${valueHtml}</span>
                </div>`);
        };
        // 成功 + 失败都显示:发票号 / ERP 系统 / Pearnly 客户 / 卖家 / 推送时间 / 耗时。
        // 仅成功额外显示:ERP 单号(带复制)+ 金额(失败时没单号没金额 · 不留空行)。
        addRow(
            isIdCard ? t('erp-log-col-booking') : t('erp-receipt-invoice-no'),
            `<strong>${escapeHtml(log.invoice_no || '-')}</strong>`
        );
        addRow(t('erp-receipt-erp-name'), escapeHtml(epName));

        if (isOk) {
            // ERP 单号行:有单号 → 单号 + 复制按钮;成功但空 → "未生成 ERP 单号"
            let docValHtml;
            if (extDocNo) {
                docValHtml =
                    `<strong class="erp-receipt-docno">${escapeHtml(extDocNo)}</strong>` +
                    `<button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-doc-copy-tip'))}">${escapeHtml(t('erp-receipt-copy-btn'))}</button>`;
            } else {
                docValHtml = `<span class="erp-receipt-docno-missing">${escapeHtml(t('erp-log-doc-missing'))}</span>`;
            }
            addRow(t('erp-receipt-doc-no'), docValHtml);
        }

        // 身份证订车无"发票买方"概念 → 跳过买方行;卖方行改标「客户」(seller_name 即客户名)
        if (!isIdCard) addRow(t('erp-receipt-client'), escapeHtml(clientName));
        addRow(
            isIdCard ? t('erp-log-col-customer') : t('erp-receipt-seller'),
            escapeHtml(sellerName)
        );
        if (isOk) {
            addRow(t('erp-receipt-amount'), escapeHtml(amountStr));
        }
        addRow(t('erp-receipt-time'), escapeHtml(time));
        addRow(
            t('erp-receipt-elapsed'),
            escapeHtml((log.elapsed_ms != null ? log.elapsed_ms : '-') + 'ms')
        );

        // 主操作按钮:有 external_url → 打开 ERP;否则有单号 → 复制 ERP 单号
        let primaryActionHtml = '';
        if (isOk && extUrl) {
            primaryActionHtml = `<a class="erp-receipt-primary-btn" href="${escapeHtml(extUrl)}" target="_blank" rel="noopener">${escapeHtml(t('erp-receipt-open-erp'))}</a>`;
        } else if (isOk && extDocNo) {
            primaryActionHtml = `<button class="erp-receipt-primary-btn" type="button" data-receipt-copy="${escapeHtml(extDocNo)}">${escapeHtml(t('erp-receipt-copy-docno'))}</button>`;
        }

        // adapter 专属提示(MR.ERP:去哪搜单号)· 仅成功 + 有单号 + 提示码时显示
        let hintHtml = '';
        if (isOk && extDocNo && extHint) {
            const hintKey = 'erp-receipt-hint-' + extHint;
            const hintText = t(hintKey);
            if (hintText && hintText !== hintKey) {
                // 铁律:线性 SVG 图标 · 不用 emoji
                const infoIc = `<svg class="erp-receipt-hint-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
                hintHtml = `<div class="erp-receipt-hint">${infoIc}<span>${escapeHtml(hintText)}</span></div>`;
            }
        }

        // 失败态:错误码 + 友好原因 + 建议动作
        let failBlockHtml = '';
        if (!isOk) {
            const errCodeMatch = (log.error_msg || '').match(/ERR_[A-Z0-9_]+/);
            const errCode = errCodeMatch ? errCodeMatch[0] : '';
            // P2-C (B7) · 优先后端 4 语友好原因(不裸透泰文)· 没命中再回退 humanizeError(网络错误)
            const _efLang =
                (typeof currentLang === 'string' && currentLang) || window._currentLang || 'th';
            const _ef = log.error_friendly && log.error_friendly[_efLang];
            const friendly =
                _ef || (log.error_msg ? humanizeError(log.error_msg) : t('erp-receipt-no-error'));
            const isMappingErr =
                /ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT/.test(
                    log.error_msg || ''
                );
            const canRetry = !!(log.history_id && log.endpoint_id);
            const actionBtns = [];
            actionBtns.push(
                `<button class="erp-receipt-action-btn" type="button" data-receipt-action="exceptions">${escapeHtml(t('erp-receipt-act-exceptions'))}</button>`
            );
            if (isMappingErr) {
                actionBtns.push(
                    `<button class="erp-receipt-action-btn" type="button" data-receipt-action="mappings">${escapeHtml(t('erp-receipt-act-mapping'))}</button>`
                );
            }
            if (canRetry) {
                actionBtns.push(
                    `<button class="erp-receipt-action-btn primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(log.id)}">${escapeHtml(t('erp-receipt-act-retry'))}</button>`
                );
            }
            failBlockHtml = `
                <div class="erp-receipt-fail-reason-label">${escapeHtml(t('erp-receipt-fail-reason'))}</div>
                <div class="erp-receipt-fail-box">
                    ${errCode ? `<div class="erp-receipt-errcode">${escapeHtml(errCode)}</div>` : ''}
                    <div class="erp-receipt-friendly">${escapeHtml(friendly)}</div>
                </div>
                <div class="erp-receipt-actions-label">${escapeHtml(t('erp-receipt-suggest'))}</div>
                <div class="erp-receipt-actions">${actionBtns.join('')}</div>`;
        }

        modal.querySelector('.log-detail-box').innerHTML = `
            <div class="log-detail-head">
                <div class="log-detail-title">
                    <span class="log-detail-status-icon ${isOk ? 'ok' : 'fail'}">${summaryIcon}</span>
                    ${escapeHtml(summaryText)}
                    <span class="log-tag ${log.trigger}">${escapeHtml(triggerText)}</span>
                </div>
                <button class="log-detail-close" type="button">✕</button>
            </div>

            <div class="erp-receipt-body">
                ${rowsHtml.join('')}
            </div>

            ${hintHtml}
            ${primaryActionHtml ? `<div class="erp-receipt-primary-wrap">${primaryActionHtml}</div>` : ''}
            ${failBlockHtml}

            <details class="log-detail-collapsible">
                <summary>${escapeHtml(t('erp-receipt-tech-toggle'))}</summary>
                <div class="log-detail-meta" style="margin-top:8px;">
                    <span>HTTP ${log.http_status || '-'}</span>
                    <span>${log.elapsed_ms}ms</span>
                    <span>${escapeHtml(t('log-detail-attempt', { n: log.attempt || 1 }))}</span>
                </div>
                <div class="log-detail-section" style="margin-top:12px;">
                    <div class="log-detail-label">${escapeHtml(t('log-detail-request-human'))}</div>
                    <pre>${escapeHtml(reqJson)}</pre>
                </div>
                <div class="log-detail-section">
                    <div class="log-detail-label">${escapeHtml(t('log-detail-response-human'))}</div>
                    <pre>${escapeHtml(respDisplay)}</pre>
                </div>
            </details>
        `;
    } catch (e) {
        console.error(e);
        modal.remove();
    }
}

// ── 模块外调用入口(initAutomationPage 行点击 / 其它模块经 window 调)──
window.copyErpDocNo = copyErpDocNo;
window.showLogDetail = showLogDetail;
