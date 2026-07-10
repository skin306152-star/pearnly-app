// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送日志「详情弹窗 + 复制单号」从 erp-integration.js 抽出
//
// 来源:erp-integration.js copyErpDocNo + showLogDetail(日志详情 modal · ~270 行)· verbatim 0 改逻辑。
// 列表/批量/轮询组留 erp-integration.js。initAutomationPage 行点击经 window.showLogDetail/copyErpDocNo 调本模块。
// 详情内「重试推送」按钮经 window.retryPushLog 调 erp-integration.js(留在那)。
//
// P3c (2026-07-10) · adapter=='mrerp' 分支挂 posting-editor.ts 的共用改判入口(现/赊 +
// 货/费两轴人工裁决),补上 MR.ERP 此前完全没有的改判能力,与 Express 卡走同一控件。
// ============================================================
/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

// 临时任务 (Zihao 2026-05-26) · 复制 ERP 单号(列表 / 凭证弹窗共用)·
// 带 clipboard API 失败时的 textarea+execCommand 降级(http 环境 / 权限禁用)。
async function copyErpDocNo(docNo: any) {
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

async function showLogDetail(logId: any) {
    // 销项重做:推送详情从居中 modal → 右侧抽屉 + 推送轨迹 timeline(对齐草稿)
    const overlay = document.createElement('div');
    overlay.className = 'erp-detail-overlay';
    const drawer = document.createElement('aside');
    drawer.className = 'erp-detail-drawer';
    drawer.innerHTML = `<div class="erp-detail-body"><div class="log-detail-loading">${escapeHtml(t('log-detail-loading'))}</div></div>`;
    document.body.appendChild(overlay);
    document.body.appendChild(drawer);
    requestAnimationFrame(() => {
        overlay.classList.add('show');
        drawer.classList.add('show');
    });
    const closeAll = () => {
        overlay.remove();
        drawer.remove();
    };
    overlay.addEventListener('click', closeAll);
    drawer.addEventListener('click', async (e) => {
        const tgt = e.target as HTMLElement;
        if (tgt.closest('.erp-detail-close')) {
            closeAll();
            return;
        }
        const copyEl = tgt.closest('[data-receipt-copy]') as HTMLElement | null;
        if (copyEl) {
            copyErpDocNo(copyEl.dataset.receiptCopy);
            return;
        }
        const actEl = tgt.closest('[data-receipt-action]') as HTMLElement | null;
        if (actEl) {
            const act = actEl.dataset.receiptAction;
            if (act === 'copy-err') {
                copyErpDocNo(actEl.dataset.errText);
                return;
            }
            if (act === 'retry') window.retryPushLog!(actEl.dataset.logId);
            else if (act === 'exceptions') {
                if (typeof routeTo === 'function') routeTo('exceptions');
            } else if (act === 'mappings' || act === 'source') {
                if (typeof routeTo === 'function') routeTo('integrations');
            }
            closeAll();
            return;
        }
    });

    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}`, {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            closeAll();
            return;
        }
        const log = await resp.json();

        // 临时任务 (Zihao 2026-05-26) · 把"成功/失败提示"升级成"ERP 推送凭证弹窗"。
        // 端点名优先用后端 join 出来的 endpoint_name(详情 API 已带),兜底查本地 cache。
        const ep = window._erpEndpoints!.find((x) => x.id === log.endpoint_id);
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

        // 凭证主体:一行一项 key-value(label 固定宽 · value 自适应 · 见 .erp-receipt-row CSS)
        const rowsHtml: string[] = [];
        const addRow = (label: any, valueHtml: any) => {
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

        // 失败态:错误码 + 友好原因(只放「失败原因」框)· 建议处理改成建议文案(草稿对齐)·
        // 动作按钮统一收到抽屉页脚(复制错误/查看原始单据/重新推送)· 不再塞进建议处理区。
        let failBlockHtml = '';
        let adviceText = '';
        if (!isOk) {
            const errCodeMatch = (log.error_msg || '').match(/ERR_[A-Z0-9_]+/);
            const errCode = errCodeMatch ? errCodeMatch[0] : '';
            const _efLang =
                (typeof currentLang === 'string' && currentLang) || window._currentLang || 'th';
            const _ef = log.error_friendly && log.error_friendly[_efLang];
            const friendly =
                _ef || (log.error_msg ? humanizeError(log.error_msg) : t('erp-receipt-no-error'));
            const isMappingErr =
                /ERR_NO_CUSTOMER_MAPPING|ERR_NO_CLIENT|ERR_NO_SEED_CUSTOMER|ERR_NO_SEED_PRODUCT|ERR_PRODUCT_NAME_MISMATCH|ERR_CUSTOMER_NAME_MISMATCH/.test(
                    log.error_msg || ''
                );
            adviceText = isIdCard
                ? t('erp-detail-advice-dms')
                : isMappingErr
                  ? t('erp-detail-advice-mapping')
                  : t('erp-detail-advice-generic');
            failBlockHtml = `
                <div class="erp-receipt-fail-box">
                    ${errCode ? `<div class="erp-receipt-errcode">${escapeHtml(errCode)}</div>` : ''}
                    <div class="erp-receipt-friendly">${escapeHtml(friendly)}</div>
                </div>`;
        }

        const typeLabel = isIdCard ? t('erp-log-type-idcard') : t('erp-log-type-invoice');
        const isRetrying2 =
            log.status === 'failed' &&
            log.next_retry_at &&
            new Date(log.next_retry_at).getTime() > Date.now() - 60000;
        // 推送轨迹 · 诚实多步:数据里有的步骤就显,没有就退通用三步(不伪造)。
        // 身份证订车(DMS):创建 → 客户资料写入(有 customer_id 才显)→ 订单创建。
        const tlItem = (cls: string, dot: string, title: string, sub: string) =>
            `<div class="erp-tl-row ${cls}"><div class="erp-tl-dot">${dot}</div><div class="erp-tl-copy"><b>${escapeHtml(title)}</b><span>${escapeHtml(sub)}</span></div></div>`;
        const tl: string[] = [];
        tl.push(tlItem('ok', '✓', t('erp-tl-created'), time + ' · ' + t('erp-tl-created-sub')));
        const rb = (log.request_body || {}) as Record<string, unknown>;
        const dmsCustId = rb.customer_id || rb.dms_customer_id;
        if (isIdCard && dmsCustId) {
            // 客户写入步骤(数据里有 customer_id 才显)
            tl.push(
                tlItem(
                    'ok',
                    '✓',
                    t('erp-tl-customer-ok'),
                    t('erp-tl-dms-customer', { id: String(dmsCustId) })
                )
            );
            if (isOk) tl.push(tlItem('ok', '✓', t('erp-tl-order-ok'), t('erp-tl-ok')));
            else if (isRetrying2)
                tl.push(
                    tlItem(
                        'mid',
                        '↻',
                        t('erp-tl-retrying'),
                        t('erp-retry-attempt', {
                            n: log.retry_count || 0,
                            max: log.max_retries || 3,
                        })
                    )
                );
            else
                tl.push(
                    tlItem('fail', '✗', t('erp-tl-order-fail'), 'HTTP ' + (log.http_status || '—'))
                );
        } else {
            tl.push(
                tlItem(isOk ? 'ok' : 'mid', '↗', t('erp-tl-pushed'), epName + ' · ' + triggerText)
            );
            if (isOk)
                tl.push(tlItem('ok', '✓', t('erp-tl-ok'), 'HTTP ' + (log.http_status || '200')));
            else if (isRetrying2)
                tl.push(
                    tlItem(
                        'mid',
                        '↻',
                        t('erp-tl-retrying'),
                        t('erp-retry-attempt', {
                            n: log.retry_count || 0,
                            max: log.max_retries || 3,
                        })
                    )
                );
            else tl.push(tlItem('fail', '✗', t('erp-tl-fail'), 'HTTP ' + (log.http_status || '—')));
        }

        const foot = `<div class="erp-detail-foot">
            ${!isOk && log.error_msg ? `<button class="btn btn-ghost" type="button" data-receipt-action="copy-err" data-err-text="${escapeHtml((log.error_msg || '').slice(0, 500))}">${escapeHtml(t('erp-detail-copy-err'))}</button>` : ''}
            <button class="btn btn-ghost" type="button" data-receipt-action="source">${escapeHtml(t('erp-detail-open-source'))}</button>
            ${log.history_id && log.endpoint_id ? `<button class="btn btn-primary" type="button" data-receipt-action="retry" data-log-id="${escapeHtml(log.id)}">${escapeHtml(t('erp-receipt-act-retry'))}</button>` : ''}
        </div>`;

        const cell = (label: string, val: string) =>
            `<div class="erp-detail-cell"><label>${escapeHtml(label)}</label><strong>${escapeHtml(val)}</strong></div>`;

        // Express 分录预览(P3b · 最小 adapter=='express' 分支)· 其它 adapter expSec 恒为 ''(零影响)。
        const expSec =
            adapter === 'express' && (window as any).ExpressDetail
                ? (window as any).ExpressDetail.section(log)
                : '';
        // MR.ERP 人工改判入口(P3c · 挂时间线上方)· MR.ERP 载荷里没有 doctype_src/item_src
        // 可读(不像 Express mapper 会把判据留痕进 request_body)· 徽标缺省不显示、两轴
        // select 初值全「自动」——保存后同样是「已保存 · 点重试推送生效」的诚实三态文案。
        // 无 history_id(理论不该发生 · 兜底)不渲染,防御与 Express 卡一致。
        const mrerpEditorSec =
            adapter === 'mrerp' && log.history_id && (window as any).PostingEditor
                ? (window as any).PostingEditor.section(log.history_id, {})
                : '';

        drawer.querySelector('.erp-detail-body')!.innerHTML = `
            <div class="erp-detail-head">
                <div class="erp-detail-title">${escapeHtml(t('erp-detail-title'))}</div>
                <button class="erp-detail-close" type="button">✕</button>
            </div>
            <div class="erp-detail-scroll">
                <section class="erp-detail-sec">
                    <h3>${escapeHtml(t('erp-detail-sec-basic'))}</h3>
                    <div class="erp-detail-grid">
                        ${cell(t('erp-detail-f-task'), (isIdCard ? typeLabel + ' · ' : '') + (log.invoice_no || '-'))}
                        ${cell(t('erp-detail-f-type'), typeLabel)}
                        ${cell(t('erp-log-col-target'), epName)}
                        ${cell(t('erp-detail-f-trigger'), triggerText)}
                        ${cell(t('erp-detail-f-start'), time)}
                        ${cell(t('erp-detail-f-total'), (log.elapsed_ms != null ? log.elapsed_ms : '-') + 'ms')}
                    </div>
                </section>
                ${
                    // express:自带识别字段 + 分录预览 + 诚实时间线(expSec)· mrerp:改判入口
                    // 挂时间线上方(mrerpEditorSec · 空字符串对非 mrerp adapter 零影响)。
                    expSec ||
                    `${mrerpEditorSec}<section class="erp-detail-sec">
                    <h3>${escapeHtml(t('erp-detail-sec-timeline'))}</h3>
                    <div class="erp-detail-timeline">${tl.join('')}</div>
                </section>`
                }
                ${isOk && extDocNo ? `<section class="erp-detail-sec"><h3>${escapeHtml(t('erp-receipt-doc-no'))}</h3><div class="erp-detail-docno"><strong>${escapeHtml(extDocNo)}</strong><button class="erp-receipt-copy-btn" type="button" data-receipt-copy="${escapeHtml(extDocNo)}">${escapeHtml(t('erp-receipt-copy-btn'))}</button></div>${hintHtml}</section>` : ''}
                ${failBlockHtml ? `<section class="erp-detail-sec"><h3>${escapeHtml(t('erp-receipt-fail-reason'))}</h3>${failBlockHtml}</section>` : ''}
                ${adviceText ? `<section class="erp-detail-sec"><h3>${escapeHtml(t('erp-receipt-suggest'))}</h3><div class="erp-detail-advice">${escapeHtml(adviceText)}</div></section>` : ''}
                <section class="erp-detail-sec">
                    <h3>${escapeHtml(t('erp-receipt-tech-toggle'))}</h3>
                    <pre class="erp-detail-code">${escapeHtml('HTTP ' + (log.http_status || '-') + ' · ' + (log.elapsed_ms != null ? log.elapsed_ms + 'ms' : '-') + '\n\nREQUEST\n' + reqJson + '\n\nRESPONSE\n' + respDisplay)}</pre>
                </section>
            </div>
            ${foot}
        `;
    } catch (e) {
        console.error(e);
        closeAll();
    }
}

// ── 模块外调用入口(initAutomationPage 行点击 / 其它模块经 window 调)──
window.copyErpDocNo = copyErpDocNo;
window.showLogDetail = showLogDetail;
