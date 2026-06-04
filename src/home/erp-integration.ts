// Pearnly home · ERP 集成页(推送日志+端点)· REFACTOR-C1 copy-out
// ============================================================
// 来源:home.js 的「ERP 集成页函数群」(推送日志 + 端点管理)
//   推送日志:loadErpLogs / _refreshErpBatchBar / _runErpBatchRetry /
//     _runErpBatchDelete / copyErpDocNo / showLogDetail / retryPushLog
//   端点管理:loadErpEndpoints / loadErpTodayStats / renderErpEndpointsList /
//     openEndpointModal / closeEndpointModal / _sanitizeUrl / readEndpointForm /
//     testEndpointConnection / saveEndpoint / showEpSaveError / deleteEndpoint
//
// 加载顺序:home.html <script src=home.js>(sync)先跑 → 本 module(Vite bundle ·
//   type=module defer)后跑 · 所以 home.js 暴露的全局(t / escapeHtml / token /
//   showToast / showConfirm / humanizeError / currentLang / _userInfo /
//   routeTo / switchAutomationTab / _showSessionRevokedModal)在本 module 执行时已就绪。
//
// 自带内存(只被本组用 · 随函数搬进模块):
//   _erpEndpoints / _epEditingId / _logFilter / _erpSelected
//   注:home.js 核心 + injectOcrPushButton 经 window._erpEndpoints 读取缓存 ·
//   本模块每次 loadErpEndpoints 都写 window._erpEndpoints = _erpEndpoints 保持桥接。
//
// 留在 home.js 没搬的公共函数(本模块裸调):
//   _humanizeBackendError(bank-recon-v2 也用)· showToast(全局)·
//   humanizeError(exceptions.js 也用 · 非 ERP 专用)
//
// 重复定义去重:home.js 有两份 loadErpTodayStats(L5528 / L6048)· 二次定义
//   (target #erp-today-stats)在运行时胜出(JS 函数声明提升后者覆盖前者)·
//   本模块只保留 L6048 那份 · 丢弃 L5528 死代码(target #erp-logs-today-stats)。
//
// verbatim 搬迁 · 0 改逻辑(仅 prettier 重排格式)。
// ============================================================

/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

let _logFilter = { key: 'all', val: '' };
// DMS 推送可视化闭环(Zihao 2026-06-01)· ERP 系统筛选 = 下拉(adapter)· 独立于 status/trigger chip ·
// 选中 mrerp_dms(身份证订车)时表头/行切到 DMS 字段(订车单号/客户)· 不再用发票字段框。
let _erpAdapter = '';
let _erpSelectReady = false;
// v118.25.1 · 推送日志多选状态(批量重推)
let _erpSelected = new Set();
window._erpSelected = _erpSelected;

// DMS 推送可视化闭环(Zihao 2026-06-01)· 推送日志 ERP 筛选 = 下拉「真实配置的 ERP 端点」·
// 不再硬编码 [MR.ERP/Xero/FlowAccount]。按 adapter 去重(后端按 adapter 过滤)· 标签用端点名。
// 懒填一次(loadErpLogs 首次调)· 失败回滚允许重试。
async function _ensureErpSelectOptions() {
    const sel = document.getElementById('erp-logs-erp-select');
    if (!sel || _erpSelectReady) return;
    _erpSelectReady = true;
    try {
        let eps = window._erpEndpoints;
        if (!Array.isArray(eps) || eps.length === 0) {
            const r = await fetch('/api/erp/endpoints', {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (r.ok) {
                const d = await r.json();
                eps = (d && (d.items || d)) || [];
            }
        }
        if (!Array.isArray(eps)) eps = [];
        const seen = new Set();
        const opts: { val: string; label: string }[] = [];
        (eps as any[]).forEach((e) => {
            const ad = (((e && e.adapter) || '') as string).toLowerCase();
            if (!ad || seen.has(ad)) return;
            seen.add(ad);
            opts.push({ val: ad, label: (e && e.name) || ad });
        });
        sel.innerHTML =
            `<option value="">${escapeHtml(t('erp-logs-erp-all'))}</option>` +
            opts
                .map(
                    (o) =>
                        `<option value="${escapeHtml(o.val)}"${o.val === _erpAdapter ? ' selected' : ''}>${escapeHtml(o.label)}</option>`
                )
                .join('');
    } catch (e) {
        _erpSelectReady = false; // 允许下次重试
    }
}

async function loadErpLogs(silent?: boolean) {
    const listEl = document.getElementById('erp-logs-list');
    if (!listEl) return;

    // v0.10 · 立即显示 loading 态 · 让用户知道点到了(silent=自动轮询刷新·不闪 loading)
    if (!silent)
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-loading'))}</div>`;

    // 今日统计同步刷新(不等)
    window.loadErpTodayStats();
    // ERP 系统下拉(真实配置端点)· 懒填一次
    _ensureErpSelectOptions();

    try {
        const params = new URLSearchParams({ limit: '30' });
        if (_logFilter.key === 'status') params.set('status', _logFilter.val);
        if (_logFilter.key === 'trigger') params.set('trigger', _logFilter.val);
        // DMS 推送可视化闭环 · ERP 系统筛选改下拉(_erpAdapter)· 与 status/trigger chip 独立组合
        if (_erpAdapter) params.set('adapter', _erpAdapter);
        const resp = await fetch(`/api/erp/logs?${params}`, {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
            return;
        }
        const data = await resp.json();
        const items = data.items || [];
        // 有「推送中(pending)」行 → 4s 后静默再拉一次 · 让状态原地翻成 ✓/✗(2026-05-26)·
        // 无 pending 或离开页面(下次 listEl 不在直接 return)即自动停。
        if (window._erpLogPollTimer) {
            clearTimeout(window._erpLogPollTimer);
            window._erpLogPollTimer = null;
        }
        if (
            items.some(function (l: any) {
                return l.status === 'pending';
            })
        ) {
            window._erpLogPollTimer = setTimeout(function () {
                loadErpLogs(true);
            }, 4000);
        }
        if (items.length === 0) {
            listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-empty'))}</div>`;
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头行 + 全选 checkbox.
        // 问题 D (v118.34.25) · 改成: 全选含 success log (批量删除清历史) ·
        // 仅 retrying 中的行不可选(防跟 worker 撞). 批量重试 server-side
        // 自动 skip success · 不会重复推.
        const selectableIds = items
            .filter(function (l: any) {
                var isR =
                    l.status === 'failed' &&
                    l.next_retry_at &&
                    new Date(l.next_retry_at).getTime() > Date.now() - 60000;
                return !isR;
            })
            .map(function (l: any) {
                return l.id;
            });
        // DMS 推送可视化闭环 · 选中身份证订车(mrerp_dms)时,单据列切到 DMS 语义:
        //   发票号→订车单号、发票买方→身份证(末4)、发票卖方→客户(seller_name 即客户名)· 工作空间列不适用置 —。
        const isDmsView = _erpAdapter === 'mrerp_dms';
        const colInvoice = isDmsView ? t('erp-log-col-booking') : t('erp-log-col-invoice');
        const colSeller = isDmsView ? t('erp-log-col-customer') : t('erp-log-col-seller');
        const colClient = isDmsView ? t('erp-log-col-idcard') : t('erp-log-col-client');
        const headerRow =
            '<div class="erp-log-row erp-log-row-header" data-log-header>' +
            (selectableIds.length > 0
                ? `<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t('erp-log-select-all-tip'))}">`
                : `<span class="erp-log-cb-spacer"></span>`) +
            `<span class="log-time">${escapeHtml(t('erp-log-col-time'))}</span>` +
            `<span class="log-status">${escapeHtml(t('erp-log-col-status'))}</span>` +
            `<span class="log-tag-header">${escapeHtml(t('erp-log-col-trigger'))}</span>` +
            `<span class="log-invoice">${escapeHtml(colInvoice)}</span>` +
            // P1-C 后端列 (2026-05-26) · 工作空间(账套归属)· join ocr_history.workspace_client_id
            `<span class="log-workspace">${escapeHtml(t('erp-log-col-workspace'))}</span>` +
            // 批 1 改动 5 (v118.34.33) · 新增 "发票买方" 列 · 跟 "发票卖方" 分开
            `<span class="log-client">${escapeHtml(colClient)}</span>` +
            `<span class="log-seller">${escapeHtml(colSeller)}</span>` +
            // 改动 8 · "ERP" 列(走哪个 endpoint)
            `<span class="log-erp">${escapeHtml(t('erp-log-col-erp'))}</span>` +
            // 临时任务 (Zihao 2026-05-26) · 通用「ERP 单号」列(external_doc_no · 不写死 MR.ERP)
            `<span class="log-doc">${escapeHtml(t('erp-log-col-doc'))}</span>` +
            `<span class="log-http">${escapeHtml(t('erp-log-col-http'))}</span>` +
            `<span class="log-elapsed">${escapeHtml(t('erp-log-col-elapsed'))}</span>` +
            // 固定宽操作列(重试按钮)· 每行都有 · 保证列对齐(修:失败行 ↻ 把右侧列挤歪)
            '<span class="log-actions"></span>' +
            '</div>';
        listEl.innerHTML =
            headerRow +
            items
                .map((log: any) => {
                    const time = new Date(log.created_at);
                    const timeStr = `${String(time.getMonth() + 1).padStart(2, '0')}-${String(time.getDate()).padStart(2, '0')} ${String(time.getHours()).padStart(2, '0')}:${String(time.getMinutes()).padStart(2, '0')}`;
                    // v118.25 · 三态:success / retrying(failed + 有 next_retry_at)/ failed(终态)
                    const isRetrying =
                        log.status === 'failed' &&
                        log.next_retry_at &&
                        new Date(log.next_retry_at).getTime() > Date.now() - 60000; // 兜底:就算稍微过了点也算重试中(worker 几秒就到)
                    let statusClass, statusIcon, statusLabel;
                    if (log.status === 'pending') {
                        // 识别后立刻写的「推送中」· 旋转图标 · 推完会原地变 ✓/✗(2026-05-26)
                        statusClass = 'retrying';
                        statusIcon = '⟳';
                        statusLabel = t('erp-status-pending');
                    } else if (log.status === 'success') {
                        statusClass = 'ok';
                        statusIcon = '✓';
                        statusLabel = t('erp-status-success');
                    } else if (log.status === 'skipped_dup') {
                        // 去重跳过(同发票同端点已成功推过)· 不是失败 · 中性「已存在」·
                        // 该行带原 ERP 单号(docCell 会显)· 旧逻辑掉进 else 显红叉误导用户(Codex P1)
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
                    let triggerTag;
                    if (log.trigger === 'auto')
                        triggerTag = `<span class="log-tag auto">${escapeHtml(t('log-tag-auto'))}</span>`;
                    else if (log.trigger === 'retry')
                        triggerTag = `<span class="log-tag retry">${escapeHtml(t('log-tag-retry'))}</span>`;
                    else
                        triggerTag = `<span class="log-tag manual">${escapeHtml(t('log-tag-manual'))}</span>`;
                    // DMS 推送可视化闭环 · 身份证订车行标类型 + 友好失败原因(不裸露 ERR_*)。
                    const isId = log.push_type === 'id_card';
                    const typeBadge = isId
                        ? `<span class="log-tag log-type-idcard">${escapeHtml(t('erp-log-type-idcard'))}</span>`
                        : '';
                    const friendlyReason =
                        (log.error_friendly &&
                            (log.error_friendly[currentLang] || log.error_friendly.en)) ||
                        '';
                    // v118.25 · 重试信息 · 重新设计(2026-05-26 Zihao 报对齐 bug):不再做成
                    // 行内变宽 chip(会把后面的列挤歪 · 失败行尤其明显)· 改成挂在状态图标的
                    // tooltip 里(retryInfo)· 行布局只保留固定宽的操作列 · 列永远对齐。
                    let retryInfo = '';
                    const rc = log.retry_count || 0;
                    const mr = log.max_retries || 3;
                    if (isRetrying) {
                        const nextMs = new Date(log.next_retry_at).getTime() - Date.now();
                        const nextMin = Math.max(0, Math.round(nextMs / 60000));
                        const nextLabel =
                            nextMin <= 0
                                ? t('erp-retry-next-soon')
                                : t('erp-retry-next-min', { n: nextMin });
                        const attemptLabel = t('erp-retry-attempt', { n: rc, max: mr });
                        retryInfo = `${attemptLabel} · ${nextLabel}`;
                    } else if (log.status === 'failed' && rc >= mr && !log.next_retry_at) {
                        retryInfo = t('erp-retry-exhausted', { n: rc });
                    }
                    // v118.25 · 重试中不显示手动重推按钮(避免和 worker 撞);失败终态才显示
                    const retryBtn =
                        log.status === 'failed' && !isRetrying
                            ? `<button class="log-retry-btn btn btn-icon" data-log-retry="${escapeHtml(log.id)}" title="${escapeHtml(t('log-retry-title'))}">↻</button>`
                            : '';
                    // 问题 D (Zihao 2026-05-19 拍板 · v118.34.25) · 全选要含 success.
                    // 原:只 failed 终态可选(重试中防抢 · success 没意义)
                    // 改:重试中仍不可选(防跟 worker 撞)· success 可选(批量删除清历史用)·
                    //     批量重试 server-side 跳过 success (skipped++) · 已实现.
                    const canSelect = !isRetrying;
                    const checked = _erpSelected.has(log.id) ? 'checked' : '';
                    const cb = canSelect
                        ? `<input type="checkbox" class="erp-log-cb" data-log-cb="${escapeHtml(log.id)}" ${checked}>`
                        : `<span class="erp-log-cb-spacer"></span>`;
                    // 发票买方列(Zihao 2026-05-26)· 显 OCR 真买方名(发票上印的买方)·
                    // 不是 Pearnly client 名(旧逻辑显 client_name → 未归属时误显 skin)。
                    // 优先 ocr_buyer_name(发票真买方)→ 退回 client_name(已归属客户)→ 未归属灰字。
                    const buyerName =
                        (log.ocr_buyer_name || '').trim() || (log.client_name || '').trim();
                    const clientCell = isId
                        ? `<span class="log-client" title="${escapeHtml(t('erp-log-col-idcard'))}">${log.id_card_tail ? '••••' + escapeHtml(log.id_card_tail) : '—'}</span>` // DMS:身份证(末4)
                        : buyerName
                          ? `<span class="log-client" title="${escapeHtml(buyerName)}">${escapeHtml(buyerName.substring(0, 18))}</span>`
                          : `<span class="log-client log-client-empty" title="${escapeHtml(t('erp-log-client-unassigned-tip'))}">${escapeHtml(t('erp-log-client-unassigned'))}</span>`;
                    // 工作空间/账套列 = 发票卖方自动分拣结果(Zihao 2026-05-26)。
                    // 切换器只是查看过滤器、不决定归属;seller 没匹配到 workspace → 显「未归属/待确认卖方」
                    //(不再显「个人事务」,避免误以为切换器决定归属)。
                    const wsCell = isId
                        ? `<span class="log-workspace log-workspace-unresolved">—</span>` // 身份证订车无账套归属
                        : log.workspace_name
                          ? `<span class="log-workspace">${escapeHtml((log.workspace_name || '').substring(0, 16))}</span>`
                          : `<span class="log-workspace log-workspace-unresolved" title="${escapeHtml(t('erp-log-ws-unresolved-tip'))}">${escapeHtml(t('erp-log-ws-unresolved'))}</span>`;
                    // 改动 8 (v118.34.33) · ERP 列 · endpoint 名(用户起的)
                    const erpCell = log.endpoint_name
                        ? `<span class="log-erp">${escapeHtml((log.endpoint_name || '').substring(0, 14))}</span>`
                        : `<span class="log-erp log-erp-deleted">${escapeHtml(t('erp-log-endpoint-deleted'))}</span>`;
                    // 临时任务 (Zihao 2026-05-26) · 通用「ERP 单号」列。后端日志 API 已派生
                    // external_doc_no/external_url(不写死 MR.ERP)。优先级:
                    //   有 external_url → 「打开」链接
                    //   否则有 external_doc_no → 可复制单号(点击复制 · 不触发 row 详情)
                    //   否则 status=success 但空 → "ERP 未返回单号"(不留白)
                    //   否则(失败等)→ "-"
                    const extDocNo = (log.external_doc_no || '').trim();
                    const extUrl = (log.external_url || '').trim();
                    let docCell;
                    if (extUrl) {
                        docCell = `<span class="log-doc"><a href="${escapeHtml(extUrl)}" target="_blank" rel="noopener" class="log-doc-open" title="${escapeHtml(extDocNo || '')}">${escapeHtml(t('erp-log-doc-open'))}</a></span>`;
                    } else if (extDocNo) {
                        docCell = `<span class="log-doc log-doc-copy" data-copy-doc="${escapeHtml(extDocNo)}" title="${escapeHtml(t('erp-log-doc-copy-tip'))}">${escapeHtml(extDocNo.substring(0, 18))}</span>`;
                    } else if (log.status === 'success') {
                        docCell = `<span class="log-doc log-doc-missing" title="${escapeHtml(t('erp-log-doc-missing-tip'))}">${escapeHtml(t('erp-log-doc-missing'))}</span>`;
                    } else {
                        docCell = `<span class="log-doc log-doc-empty">-</span>`;
                    }
                    return `
                <div class="erp-log-row ${statusClass}" data-log-detail="${escapeHtml(log.id)}">
                    ${cb}
                    <span class="log-time">${timeStr}</span>
                    <span class="log-status" title="${escapeHtml(statusLabel + (retryInfo ? ' · ' + retryInfo : '') + (friendlyReason ? ' · ' + friendlyReason : ''))}">${statusIcon}</span>
                    ${triggerTag}${typeBadge}
                    <span class="log-invoice"${isId ? ` title="${escapeHtml(t('erp-log-col-booking'))}"` : ''}>${escapeHtml(log.invoice_no || '-')}</span>
                    ${wsCell}
                    ${clientCell}
                    <span class="log-seller"${isId ? ` title="${escapeHtml(t('erp-log-col-customer'))}"` : ''}>${escapeHtml((log.seller_name || '').substring(0, 20))}</span>
                    ${erpCell}
                    ${docCell}
                    <span class="log-http">HTTP ${log.http_status || '-'}</span>
                    <span class="log-elapsed">${log.elapsed_ms}ms</span>
                    <span class="log-actions">${retryBtn}</span>
                </div>
            `;
                })
                .join('');
        // v118.25.1 · 重新渲染后 · 修剪掉已经不在列表里的选中项 + 刷新批量栏
        const visibleIds = new Set(items.map((x: any) => x.id));
        for (const id of Array.from(_erpSelected)) {
            if (!visibleIds.has(id)) _erpSelected.delete(id);
        }
        window._refreshErpBatchBar();
    } catch (e) {
        console.error('load erp logs failed', e);
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
    }
}

async function retryPushLog(logId: any) {
    try {
        const resp = await fetch(`/api/erp/logs/${encodeURIComponent(logId)}/retry`, {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token },
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok && data.ok) {
            showToast(t('log-retry-ok'), 'success');
        } else {
            showToast(
                t('log-retry-fail') + ' · HTTP ' + (data.http_status || resp.status),
                'error'
            );
        }
        loadErpLogs();
        window.loadErpEndpoints();
    } catch (e) {
        showToast(t('log-retry-fail'), 'error');
    }
}

// 事件绑定
(function initAutomationPage() {
    // 点新增按钮
    document
        .getElementById('btn-add-endpoint')!
        .addEventListener('click', () => window.openEndpointModal(null));

    // 对话框关闭
    document
        .getElementById('endpoint-modal-close')!
        .addEventListener('click', window.closeEndpointModal);
    document.getElementById('btn-ep-cancel')!.addEventListener('click', window.closeEndpointModal);

    // 点遮罩不关闭(避免误触丢失填写的内容 · 只能通过关闭按钮/取消按钮关闭)

    // 测试连接
    document
        .getElementById('btn-ep-test')!
        .addEventListener('click', window.testEndpointConnection);

    // 保存
    document.getElementById('btn-ep-save')!.addEventListener('click', window.saveEndpoint);

    // v0.9.1 · URL 输入框失焦自动清理"Copy to clipboard"等粘贴糟粕
    document.getElementById('ep-url')!.addEventListener('blur', (e) => {
        const cleaned = window._sanitizeUrl((e.target as HTMLInputElement).value);
        if (cleaned !== (e.target as HTMLInputElement).value.trim()) {
            (e.target as HTMLInputElement).value = cleaned;
        }
    });

    // 列表里的编辑/删除按钮(事件委托)
    document.addEventListener('click', (e) => {
        const editBtn = (e.target as HTMLElement).closest('[data-ep-edit]') as HTMLElement | null;
        const delBtn = (e.target as HTMLElement).closest('[data-ep-del]') as HTMLElement | null;
        if (editBtn) window.openEndpointModal(editBtn.dataset.epEdit);
        if (delBtn) window.deleteEndpoint(delBtn.dataset.epDel);

        // v0.9.1 · 推送日志交互
        const retryBtn = (e.target as HTMLElement).closest('[data-log-retry]') as HTMLElement;
        if (retryBtn) {
            e.stopPropagation();
            retryPushLog(retryBtn.dataset.logRetry);
            return;
        }
        // v118.25.1 · 批量勾选
        const cb = (e.target as HTMLElement).closest('[data-log-cb]') as HTMLInputElement | null;
        if (cb) {
            e.stopPropagation();
            const id = cb.dataset.logCb;
            if (cb.checked) _erpSelected.add(id);
            else _erpSelected.delete(id);
            window._refreshErpBatchBar();
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头全选 checkbox
        const selectAllCb = (e.target as HTMLElement).closest(
            '[data-log-select-all]'
        ) as HTMLInputElement | null;
        if (selectAllCb) {
            e.stopPropagation();
            const checkAll = selectAllCb.checked;
            const allCbs = document.querySelectorAll('[data-log-cb]');
            allCbs.forEach(function (rowCb: any) {
                rowCb.checked = checkAll;
                const id = rowCb.dataset.logCb;
                if (checkAll) _erpSelected.add(id);
                else _erpSelected.delete(id);
            });
            window._refreshErpBatchBar();
            return;
        }
        // v118.25.1 · 批量重推按钮
        if ((e.target as HTMLElement).closest('#btn-erp-batch-retry')) {
            e.stopPropagation();
            window._runErpBatchRetry();
            return;
        }
        // v118.25.1 · 取消选择
        if ((e.target as HTMLElement).closest('#btn-erp-batch-clear')) {
            e.stopPropagation();
            _erpSelected.clear();
            document.querySelectorAll('.erp-log-cb').forEach((x: any) => {
                x.checked = false;
            });
            window._refreshErpBatchBar();
            return;
        }
        const logRow = (e.target as HTMLElement).closest('[data-log-detail]') as HTMLElement | null;
        if (logRow) {
            // 点 checkbox 不算点 row
            if ((e.target as HTMLElement).closest('[data-log-cb]')) return;
            // 临时任务 (Zihao 2026-05-26) · 点 ERP 单号 → 复制 · 不打开详情
            const copyDocEl = (e.target as HTMLElement).closest(
                '[data-copy-doc]'
            ) as HTMLElement | null;
            if (copyDocEl) {
                e.stopPropagation();
                window.copyErpDocNo(copyDocEl.dataset.copyDoc);
                return;
            }
            // 点「打开」链接 → 让 <a> 默认在新标签打开 · 不打开详情
            if ((e.target as HTMLElement).closest('.log-doc-open')) return;
            window.showLogDetail(logRow.dataset.logDetail);
            return;
        }
        const filterChip = (e.target as HTMLElement).closest('.chip-filter') as HTMLElement | null;
        if (filterChip) {
            document
                .querySelectorAll('#erp-logs-filters .chip-filter')
                .forEach((c: Element) => c.classList.remove('active'));
            filterChip.classList.add('active');
            _logFilter = {
                key: filterChip.dataset.filterKey as string,
                val: filterChip.dataset.filterVal as string,
            };
            loadErpLogs();
            return;
        }
        if ((e.target as HTMLElement).closest('#btn-refresh-logs')) {
            const btn = (e.target as HTMLElement).closest('#btn-refresh-logs')!;
            btn.classList.add('spinning');
            setTimeout(() => btn.classList.remove('spinning'), 600);
            loadErpLogs();
            return;
        }

        // v0.10 · 自动化子菜单切换(guard: 只处理有 data-auto-tab 的按钮，防止对账中心等共用 .auto-nav-item 类名的按钮触发 switchAutomationTab(undefined))
        const autoNav = (e.target as HTMLElement).closest('.auto-nav-item') as HTMLElement | null;
        if (autoNav && autoNav.dataset.autoTab) {
            switchAutomationTab(autoNav.dataset.autoTab);
            return;
        }
    });

    // DMS 推送可视化闭环 · ERP 系统下拉切换 → 重新拉对应 ERP 的日志(不混)
    document.addEventListener('change', (e) => {
        if (e.target && (e.target as HTMLElement).id === 'erp-logs-erp-select') {
            _erpAdapter = (e.target as HTMLInputElement).value || '';
            loadErpLogs();
        }
    });
})();

// ============================================================
// 模块外调用入口(home.js routeTo / 核心 / 其它模块经 window 调)·
// 参照 test-center.js 末尾 window 暴露范式。
// ============================================================
window.loadErpLogs = loadErpLogs;
window.retryPushLog = retryPushLog;
