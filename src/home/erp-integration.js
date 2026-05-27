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

let _erpEndpoints = [];
window._erpEndpoints = _erpEndpoints;
let _epEditingId = null; // 当前编辑中的 endpoint id,null = 新增模式

let _logFilter = { key: 'all', val: '' };
// v118.25.1 · 推送日志多选状态(批量重推)
let _erpSelected = new Set();

async function loadErpLogs(silent) {
    const listEl = document.getElementById('erp-logs-list');
    if (!listEl) return;

    // v0.10 · 立即显示 loading 态 · 让用户知道点到了(silent=自动轮询刷新·不闪 loading)
    if (!silent)
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-loading'))}</div>`;

    // 今日统计同步刷新(不等)
    loadErpTodayStats();

    try {
        const params = new URLSearchParams({ limit: '30' });
        if (_logFilter.key === 'status') params.set('status', _logFilter.val);
        if (_logFilter.key === 'trigger') params.set('trigger', _logFilter.val);
        // 批 3 改动 6 (v118.34.34) · adapter filter chip (mrerp / xero / flowaccount).
        if (_logFilter.key === 'adapter') params.set('adapter', _logFilter.val);
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
            items.some(function (l) {
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
            .filter(function (l) {
                var isR =
                    l.status === 'failed' &&
                    l.next_retry_at &&
                    new Date(l.next_retry_at).getTime() > Date.now() - 60000;
                return !isR;
            })
            .map(function (l) {
                return l.id;
            });
        const headerRow =
            '<div class="erp-log-row erp-log-row-header" data-log-header>' +
            (selectableIds.length > 0
                ? `<input type="checkbox" class="erp-log-cb erp-log-cb-all" data-log-select-all title="${escapeHtml(t('erp-log-select-all-tip'))}">`
                : `<span class="erp-log-cb-spacer"></span>`) +
            `<span class="log-time">${escapeHtml(t('erp-log-col-time'))}</span>` +
            `<span class="log-status">${escapeHtml(t('erp-log-col-status'))}</span>` +
            `<span class="log-tag-header">${escapeHtml(t('erp-log-col-trigger'))}</span>` +
            `<span class="log-invoice">${escapeHtml(t('erp-log-col-invoice'))}</span>` +
            // P1-C 后端列 (2026-05-26) · 工作空间(账套归属)· join ocr_history.workspace_client_id
            `<span class="log-workspace">${escapeHtml(t('erp-log-col-workspace'))}</span>` +
            // 批 1 改动 5 (v118.34.33) · 新增 "发票买方" 列 · 跟 "发票卖方" 分开
            `<span class="log-client">${escapeHtml(t('erp-log-col-client'))}</span>` +
            `<span class="log-seller">${escapeHtml(t('erp-log-col-seller'))}</span>` +
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
                .map((log) => {
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
                            ? `<button class="log-retry-btn" data-log-retry="${escapeHtml(log.id)}" title="${escapeHtml(t('log-retry-title'))}">↻</button>`
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
                    const clientCell = buyerName
                        ? `<span class="log-client" title="${escapeHtml(buyerName)}">${escapeHtml(buyerName.substring(0, 18))}</span>`
                        : `<span class="log-client log-client-empty" title="${escapeHtml(t('erp-log-client-unassigned-tip'))}">${escapeHtml(t('erp-log-client-unassigned'))}</span>`;
                    // 工作空间/账套列 = 发票卖方自动分拣结果(Zihao 2026-05-26)。
                    // 切换器只是查看过滤器、不决定归属;seller 没匹配到 workspace → 显「未归属/待确认卖方」
                    //(不再显「个人事务」,避免误以为切换器决定归属)。
                    const wsCell = log.workspace_name
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
                    <span class="log-status" title="${escapeHtml(statusLabel + (retryInfo ? ' · ' + retryInfo : ''))}">${statusIcon}</span>
                    ${triggerTag}
                    <span class="log-invoice">${escapeHtml(log.invoice_no || '-')}</span>
                    ${wsCell}
                    ${clientCell}
                    <span class="log-seller">${escapeHtml((log.seller_name || '').substring(0, 20))}</span>
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
        const visibleIds = new Set(items.map((x) => x.id));
        for (const id of Array.from(_erpSelected)) {
            if (!visibleIds.has(id)) _erpSelected.delete(id);
        }
        _refreshErpBatchBar();
    } catch (e) {
        console.error('load erp logs failed', e);
        listEl.innerHTML = `<div class="erp-logs-empty">${escapeHtml(t('erp-logs-error'))}</div>`;
    }
}

// v118.25.1 · 批量栏可见性 + 计数刷新
function _refreshErpBatchBar() {
    const bar = document.getElementById('erp-logs-batch-bar');
    const countEl = document.getElementById('erp-logs-batch-count');
    // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 同步表头全选 checkbox 状态.
    // none → unchecked · all → checked · partial → indeterminate.
    const headerCb = document.querySelector('[data-log-select-all]');
    if (headerCb) {
        const visibleCbs = document.querySelectorAll('[data-log-cb]');
        const total = visibleCbs.length;
        const sel = _erpSelected.size;
        if (sel === 0) {
            headerCb.checked = false;
            headerCb.indeterminate = false;
        } else if (sel >= total) {
            headerCb.checked = true;
            headerCb.indeterminate = false;
        } else {
            headerCb.checked = false;
            headerCb.indeterminate = true;
        }
    }
    if (!bar || !countEl) return;
    const n = _erpSelected.size;
    if (n === 0) {
        bar.style.display = 'none';
        return;
    }
    bar.style.display = '';
    countEl.textContent = t('erp-batch-selected', { n });
}

// v118.25.1 · 批量重推执行 · 调 /api/erp/logs/batch-retry · 提示成功/失败/跳过计数
async function _runErpBatchRetry() {
    console.info('[ErpBatch] retry triggered · selected=', _erpSelected.size);
    const ids = Array.from(_erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(t('erp-batch-confirm', { n: ids.length }));
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-retry', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        const msg = t('erp-batch-result', {
            ok: r.succeeded || 0,
            fail: r.failed || 0,
            skip: r.skipped || 0,
        });
        const kind = r.failed && r.failed > 0 ? 'warn' : 'success';
        showToast(msg, kind);
        _erpSelected.clear();
        loadErpLogs();
    } catch (e) {
        console.error('batch retry failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除执行
async function _runErpBatchDelete() {
    console.info('[ErpBatch] delete triggered · selected=', _erpSelected.size);
    const ids = Array.from(_erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(t('erp-batch-delete-confirm', { n: ids.length }), {
        danger: true,
    });
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-delete', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        // 问题 C (Zihao 2026-05-19 拍板 · v118.34.25) · 立即从 DOM 移除被删 row ·
        // 不等 reload · 用户视觉立刻反馈"消失了". 然后再 reload 拉新数据填充
        // (DB 还有别的 log · 自动接着显示 · 不是"日志又弹出来"的 bug · 是正常分页).
        ids.forEach(function (id) {
            var row = document.querySelector('[data-log-detail="' + id + '"]');
            if (row) row.remove();
        });
        // 立即 hide batch bar(_erpSelected.clear 后 _refreshErpBatchBar 也会做 ·
        // 但提前 hide 防止短暂残留视觉).
        var bar = document.getElementById('erp-logs-batch-bar');
        if (bar) bar.style.display = 'none';
        showToast(
            t('erp-batch-delete-result', {
                n: r.deleted || 0,
                skip: r.skipped || 0,
            }),
            r.deleted > 0 ? 'success' : 'warn'
        );
        _erpSelected.clear();
        // 延迟 500ms reload · 让用户先看到 "消失了" 效果 + toast · 再拉新数据
        setTimeout(loadErpLogs, 500);
    } catch (e) {
        console.error('batch delete failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 5 fix (v118.34.23) · defensive: 直接绑定到按钮 + 也保留事件委托
// 防 IIFE document-level handler 某些情况下没接管. 用 capture phase 保证 fire.
(function _bindErpBatchButtonsDirect() {
    function _bind() {
        var btnRetry = document.getElementById('btn-erp-batch-retry');
        var btnDelete = document.getElementById('btn-erp-batch-delete');
        var btnClear = document.getElementById('btn-erp-batch-clear');
        if (btnRetry && !btnRetry.dataset.boundDirect) {
            btnRetry.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _runErpBatchRetry();
            });
            btnRetry.dataset.boundDirect = '1';
        }
        if (btnDelete && !btnDelete.dataset.boundDirect) {
            btnDelete.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _runErpBatchDelete();
            });
            btnDelete.dataset.boundDirect = '1';
        }
        if (btnClear && !btnClear.dataset.boundDirect) {
            btnClear.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _erpSelected.clear();
                document.querySelectorAll('.erp-log-cb').forEach(function (x) {
                    x.checked = false;
                });
                _refreshErpBatchBar();
            });
            btnClear.dataset.boundDirect = '1';
        }
    }
    // Bind at DOM ready + also on every tab switch / log load via mutation observer.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bind);
    } else {
        _bind();
    }
    // 兜底: 隔 2s 重试 binding(防早期 DOM 还没渲染)
    setTimeout(_bind, 2000);
    setTimeout(_bind, 5000);
    window._bindErpBatchButtons = _bind;
})();

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
                retryPushLog(actEl.dataset.logId);
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
        const ep = _erpEndpoints.find((x) => x.id === log.endpoint_id);
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
            t('erp-receipt-invoice-no'),
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

        addRow(t('erp-receipt-client'), escapeHtml(clientName));
        addRow(t('erp-receipt-seller'), escapeHtml(sellerName));
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

async function retryPushLog(logId) {
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
        loadErpEndpoints();
    } catch (e) {
        showToast(t('log-retry-fail'), 'error');
    }
}

async function loadErpEndpoints() {
    try {
        const resp = await fetch('/api/erp/endpoints', {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (resp.status === 401) {
            localStorage.removeItem('mrpilot_token');
            const _bd = await resp.json().catch(() => ({}));
            const _dc =
                typeof _bd.detail === 'string' ? _bd.detail : (_bd.detail && _bd.detail.code) || '';
            if (_dc === 'auth.session_revoked') {
                _showSessionRevokedModal();
                return;
            }
            window.location.href = '/';
            return;
        }
        const data = await resp.json();
        _erpEndpoints = data.items || [];
        window._erpEndpoints = _erpEndpoints;
        renderErpEndpointsList();
    } catch (e) {
        console.error('load endpoints failed', e);
    }
}

// v118.34.34 (批 2 改动 7) · 外部模块 (erp-mrerp-connect.js) 调
// PATCH /api/erp/endpoints/:id 切 enabled 后,要让 home.js 的全局
// _erpEndpoints 同步 · 不然 OCR drawer 推送按钮还在用旧 list (会显示
// 已停用的 endpoint 在 picker 里).
window._refreshErpEndpointsCache = function () {
    return loadErpEndpoints();
};

// v0.17 · M5 · 今日 ERP 推送统计 · 显示在 ERP 对接 tab 头部
async function loadErpTodayStats() {
    const host = document.getElementById('erp-today-stats');
    if (!host) return;
    host.innerHTML = '';
    try {
        const resp = await fetch('/api/erp/stats/today', {
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) return;
        const data = await resp.json();
        const total = data.total || 0;
        const success = data.success || 0;
        const failed = data.failed || 0;
        const autoCnt = data.auto_cnt || 0;
        if (total === 0) {
            host.innerHTML = `<span class="erp-today-empty">${escapeHtml(t('erp-today-none'))}</span>`;
            return;
        }
        const parts = [];
        parts.push(
            `<span class="erp-today-item"><strong>${total}</strong> ${escapeHtml(t('erp-today-total'))}</span>`
        );
        if (success > 0)
            parts.push(
                `<span class="erp-today-item ok"><strong>${success}</strong> ${escapeHtml(t('erp-today-success'))}</span>`
            );
        if (failed > 0)
            parts.push(
                `<span class="erp-today-item fail"><strong>${failed}</strong> ${escapeHtml(t('erp-today-failed'))}</span>`
            );
        if (autoCnt > 0)
            parts.push(
                `<span class="erp-today-item auto"><strong>${autoCnt}</strong> ${escapeHtml(t('erp-today-auto'))}</span>`
            );
        host.innerHTML = parts.join('');
    } catch (e) {
        console.warn('loadErpTodayStats failed', e);
    }
}

function renderErpEndpointsList() {
    const list = document.getElementById('erp-endpoints-list');
    const summary = document.getElementById('erp-status-summary');
    const addBtn = document.getElementById('btn-add-endpoint');

    if (!list) {
        console.warn('erp-endpoints-list 容器不存在');
        return;
    }

    // v0.8 · 按 endpoints_limit 灰化新增按钮
    if (addBtn && _userInfo) {
        const limit = _userInfo.endpoints_limit;
        if (limit !== -1 && _erpEndpoints.length >= limit) {
            addBtn.disabled = true;
            addBtn.title = t('ep-limit-reached', { limit });
            addBtn.classList.add('btn-disabled-plus');
        } else {
            addBtn.disabled = false;
            addBtn.title = '';
            addBtn.classList.remove('btn-disabled-plus');
        }
    }

    if (_erpEndpoints.length === 0) {
        list.innerHTML = `<div class="erp-empty">${escapeHtml(t('ep-list-empty'))}</div>`;
        if (summary) {
            summary.textContent = t('auto-status-none');
            summary.className = 'auto-status-pill none';
        }
        return;
    }

    const autoOn = _erpEndpoints.some((e) => e.auto_push && e.enabled);
    if (summary) {
        summary.textContent = t('auto-status-active', {
            n: _erpEndpoints.length,
            mode: autoOn ? t('auto-status-on') : t('auto-status-off'),
        });
        summary.className = 'auto-status-pill ' + (autoOn ? 'active' : 'ready');
    }
    // v0.17 · M5 · 异步加载今日统计 · 追加到 summary 区域下方
    loadErpTodayStats();

    list.innerHTML = _erpEndpoints
        .map((ep) => {
            const cfg = ep.config || {};
            const url = escapeHtml(cfg.url || '');
            const hasToken = !!cfg._token_set;
            const enabled = ep.enabled !== false;

            const badges = [];
            if (ep.is_default)
                badges.push(`<span class="ep-badge default">${escapeHtml(t('ep-default'))}</span>`);
            if (ep.auto_push)
                badges.push(
                    `<span class="ep-badge auto">${escapeHtml(t('ep-auto-push-on'))}</span>`
                );
            if (!enabled)
                badges.push(
                    `<span class="ep-badge disabled">${escapeHtml(t('ep-disabled'))}</span>`
                );

            const stats = [];
            if (ep.success_count > 0)
                stats.push(
                    `<span class="ep-stat ok">${escapeHtml(t('ep-success', { n: ep.success_count }))}</span>`
                );
            if (ep.failure_count > 0)
                stats.push(
                    `<span class="ep-stat fail">${escapeHtml(t('ep-failure', { n: ep.failure_count }))}</span>`
                );

            return `
            <div class="erp-endpoint" data-ep-id="${escapeHtml(ep.id)}">
                <div class="ep-main">
                    <div class="ep-title-row">
                        <div class="ep-name">${escapeHtml(ep.name)}</div>
                        <div class="ep-badges">${badges.join('')}</div>
                    </div>
                    <div class="ep-url">${url || '-'}</div>
                    <div class="ep-stats">${stats.join(' · ')}</div>
                </div>
                <div class="ep-actions">
                    <button class="btn btn-ghost btn-small" data-ep-edit="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-edit'))}</span>
                    </button>
                    <button class="btn btn-ghost btn-small btn-danger" data-ep-del="${escapeHtml(ep.id)}">
                        <span>${escapeHtml(t('ep-delete'))}</span>
                    </button>
                </div>
            </div>
        `;
        })
        .join('');

    // v0.8.1 · 列表下方显示上限提示(根据 plan)
    if (_userInfo && _userInfo.endpoints_limit !== -1) {
        const usedN = _erpEndpoints.length;
        const limit = _userInfo.endpoints_limit;
        const plan = _userInfo.plan;
        const hint = document.createElement('div');
        hint.className = 'erp-limit-hint';
        if (plan === 'free') {
            hint.innerHTML = `${escapeHtml(t('ep-free-limit-hint', { used: usedN, limit }))} <a data-upgrade="plus">${escapeHtml(t('upgrade-to-plus'))}</a>`;
        } else {
            hint.textContent = t('ep-plus-limit-hint', { used: usedN, limit });
        }
        list.appendChild(hint);
    }
}

// 打开新增对话框
function openEndpointModal(editingId) {
    _epEditingId = editingId || null;
    const modal = document.getElementById('endpoint-modal');
    const titleEl = document.getElementById('endpoint-modal-title');
    titleEl.textContent = editingId ? t('ep-modal-title-edit') : t('ep-modal-title-new');

    const nameEl = document.getElementById('ep-name');
    const urlEl = document.getElementById('ep-url');
    const tokenEl = document.getElementById('ep-token');
    const isDefEl = document.getElementById('ep-is-default');
    const autoPushEl = document.getElementById('ep-auto-push');
    const resultEl = document.getElementById('ep-test-result');

    resultEl.style.display = 'none';
    resultEl.textContent = '';

    // 清掉上次遗留的错误提示
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();

    if (editingId) {
        const ep = _erpEndpoints.find((e) => e.id === editingId);
        if (!ep) return;
        nameEl.value = ep.name || '';
        urlEl.value = (ep.config || {}).url || '';
        tokenEl.value = (ep.config || {})._token_set ? ep.config.token || '' : '';
        tokenEl.placeholder = (ep.config || {})._token_set
            ? '（已保存 · 留空保持不变）'
            : t('ep-token-ph');
        isDefEl.checked = !!ep.is_default;
        autoPushEl.checked = !!ep.auto_push;
    } else {
        nameEl.value = '';
        urlEl.value = '';
        tokenEl.value = '';
        tokenEl.placeholder = t('ep-token-ph');
        isDefEl.checked = _erpEndpoints.length === 0; // 第一个默认选中
        // v118.27.8.1.15 · 新建 endpoint 默认开启自动推送(0 操作上 ERP)· 老 endpoint 不变(走 14132 读 ep.auto_push)
        autoPushEl.checked = true;
    }

    // v0.15 · 扁平权限 · 所有人都能自动推送
    const autoPushRow = autoPushEl.closest('.form-switch-row');
    autoPushEl.disabled = false;
    if (autoPushRow) {
        autoPushRow.classList.remove('disabled-plus');
        autoPushRow.title = '';
        autoPushRow.style.cursor = '';
        autoPushRow.onclick = null;
        const b = autoPushRow.querySelector('.plus-badge');
        if (b) b.remove();
    }

    modal.style.display = '';
    setTimeout(() => nameEl.focus(), 50);
}

function closeEndpointModal() {
    document.getElementById('endpoint-modal').style.display = 'none';
    _epEditingId = null;
    // 关闭时清错误提示,避免下次打开残留
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.remove();
}

function _sanitizeUrl(raw) {
    // v0.9.1 · 清理常见"复制糟粕"(Copy to clipboard / 空格后跟可疑词)
    if (!raw) return '';
    let u = raw.trim();
    // 只保留到第一个空格前(URL 不能含空格)
    const spIdx = u.search(/\s/);
    if (spIdx >= 0) u = u.slice(0, spIdx);
    return u;
}

function readEndpointForm() {
    const name = document.getElementById('ep-name').value.trim();
    const url = _sanitizeUrl(document.getElementById('ep-url').value);
    const tokenVal = document.getElementById('ep-token').value;
    const isDefault = document.getElementById('ep-is-default').checked;
    const autoPush = document.getElementById('ep-auto-push').checked;

    const config = { url };
    // token:编辑模式下如果留空,发 "***" 占位(后端会保留旧值);否则发新值
    if (_epEditingId) {
        if (tokenVal) config.token = tokenVal;
    } else {
        if (tokenVal) config.token = tokenVal;
    }

    return { name, url, tokenVal, isDefault, autoPush, config };
}

async function testEndpointConnection() {
    const { name, url, config } = readEndpointForm();
    const resultEl = document.getElementById('ep-test-result');
    if (!url) {
        resultEl.style.display = '';
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-required');
        return;
    }
    resultEl.style.display = '';
    resultEl.className = 'form-test-result running';
    resultEl.textContent = t('ep-test-running');

    try {
        const resp = await fetch('/api/erp/test-connection', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ adapter: 'webhook', config }),
        });
        const data = await resp.json();
        if (data.success) {
            resultEl.className = 'form-test-result ok';
            resultEl.textContent = t('ep-test-ok', {
                status: data.http_status,
                ms: data.elapsed_ms,
            });
        } else {
            resultEl.className = 'form-test-result fail';
            resultEl.textContent = t('ep-test-fail', { err: data.error_msg || 'unknown' });
        }
    } catch (e) {
        resultEl.className = 'form-test-result fail';
        resultEl.textContent = t('ep-test-fail', { err: e.message });
    }
}

async function saveEndpoint() {
    const form = readEndpointForm();
    const errBox = document.getElementById('ep-save-error');
    if (errBox) errBox.style.display = 'none';

    if (!form.name || !form.url) {
        showEpSaveError(t('ep-required'));
        return;
    }
    const payload = {
        name: form.name,
        adapter: 'webhook',
        config: form.config,
        is_default: form.isDefault,
        auto_push: form.autoPush,
    };

    const btn = document.getElementById('btn-ep-save');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add('loading');

    try {
        let resp;
        if (_epEditingId) {
            resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(_epEditingId)}`, {
                method: 'PATCH',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        } else {
            resp = await fetch('/api/erp/endpoints', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
        }
        if (!resp.ok) {
            const errData = await resp.json().catch(() => ({}));
            const detail = errData.detail || `HTTP ${resp.status}`;
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        // 成功 · 静默关窗 + 小 toast
        closeEndpointModal();
        showToast(t('ep-save-ok'));
        loadErpEndpoints();
    } catch (e) {
        showEpSaveError(`${t('ep-save-fail')} · ${e.message || 'unknown'}`);
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
        btn.innerHTML = originalText;
    }
}

function showEpSaveError(msg) {
    let box = document.getElementById('ep-save-error');
    if (!box) {
        const foot = document.querySelector('#endpoint-modal .modal-foot');
        if (!foot) return;
        box = document.createElement('div');
        box.id = 'ep-save-error';
        box.className = 'ep-inline-error';
        foot.parentNode.insertBefore(box, foot);
    }
    box.textContent = msg;
    box.style.display = '';
}

async function deleteEndpoint(endpointId) {
    const ep = _erpEndpoints.find((e) => e.id === endpointId);
    if (!ep) return;
    const ok = await showConfirm(t('ep-delete-confirm', { name: ep.name }), { danger: true });
    if (!ok) return;
    try {
        const resp = await fetch(`/api/erp/endpoints/${encodeURIComponent(endpointId)}`, {
            method: 'DELETE',
            headers: { Authorization: 'Bearer ' + token },
        });
        if (!resp.ok) throw new Error();
        showToast(t('ep-delete-ok'));
        loadErpEndpoints();
    } catch {
        showToast(t('ep-save-fail'), 'fail');
    }
}

// 事件绑定
(function initAutomationPage() {
    // 点新增按钮
    document
        .getElementById('btn-add-endpoint')
        .addEventListener('click', () => openEndpointModal(null));

    // 对话框关闭
    document.getElementById('endpoint-modal-close').addEventListener('click', closeEndpointModal);
    document.getElementById('btn-ep-cancel').addEventListener('click', closeEndpointModal);

    // 点遮罩不关闭(避免误触丢失填写的内容 · 只能通过关闭按钮/取消按钮关闭)

    // 测试连接
    document.getElementById('btn-ep-test').addEventListener('click', testEndpointConnection);

    // 保存
    document.getElementById('btn-ep-save').addEventListener('click', saveEndpoint);

    // v0.9.1 · URL 输入框失焦自动清理"Copy to clipboard"等粘贴糟粕
    document.getElementById('ep-url').addEventListener('blur', (e) => {
        const cleaned = _sanitizeUrl(e.target.value);
        if (cleaned !== e.target.value.trim()) {
            e.target.value = cleaned;
        }
    });

    // 列表里的编辑/删除按钮(事件委托)
    document.addEventListener('click', (e) => {
        const editBtn = e.target.closest('[data-ep-edit]');
        const delBtn = e.target.closest('[data-ep-del]');
        if (editBtn) openEndpointModal(editBtn.dataset.epEdit);
        if (delBtn) deleteEndpoint(delBtn.dataset.epDel);

        // v0.9.1 · 推送日志交互
        const retryBtn = e.target.closest('[data-log-retry]');
        if (retryBtn) {
            e.stopPropagation();
            retryPushLog(retryBtn.dataset.logRetry);
            return;
        }
        // v118.25.1 · 批量勾选
        const cb = e.target.closest('[data-log-cb]');
        if (cb) {
            e.stopPropagation();
            const id = cb.dataset.logCb;
            if (cb.checked) _erpSelected.add(id);
            else _erpSelected.delete(id);
            _refreshErpBatchBar();
            return;
        }
        // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 表头全选 checkbox
        const selectAllCb = e.target.closest('[data-log-select-all]');
        if (selectAllCb) {
            e.stopPropagation();
            const checkAll = selectAllCb.checked;
            const allCbs = document.querySelectorAll('[data-log-cb]');
            allCbs.forEach(function (rowCb) {
                rowCb.checked = checkAll;
                const id = rowCb.dataset.logCb;
                if (checkAll) _erpSelected.add(id);
                else _erpSelected.delete(id);
            });
            _refreshErpBatchBar();
            return;
        }
        // v118.25.1 · 批量重推按钮
        if (e.target.closest('#btn-erp-batch-retry')) {
            e.stopPropagation();
            _runErpBatchRetry();
            return;
        }
        // v118.25.1 · 取消选择
        if (e.target.closest('#btn-erp-batch-clear')) {
            e.stopPropagation();
            _erpSelected.clear();
            document.querySelectorAll('.erp-log-cb').forEach((x) => {
                x.checked = false;
            });
            _refreshErpBatchBar();
            return;
        }
        const logRow = e.target.closest('[data-log-detail]');
        if (logRow) {
            // 点 checkbox 不算点 row
            if (e.target.closest('[data-log-cb]')) return;
            // 临时任务 (Zihao 2026-05-26) · 点 ERP 单号 → 复制 · 不打开详情
            const copyDocEl = e.target.closest('[data-copy-doc]');
            if (copyDocEl) {
                e.stopPropagation();
                copyErpDocNo(copyDocEl.dataset.copyDoc);
                return;
            }
            // 点「打开」链接 → 让 <a> 默认在新标签打开 · 不打开详情
            if (e.target.closest('.log-doc-open')) return;
            showLogDetail(logRow.dataset.logDetail);
            return;
        }
        const filterChip = e.target.closest('.chip-filter');
        if (filterChip) {
            document
                .querySelectorAll('#erp-logs-filters .chip-filter')
                .forEach((c) => c.classList.remove('active'));
            filterChip.classList.add('active');
            _logFilter = { key: filterChip.dataset.filterKey, val: filterChip.dataset.filterVal };
            loadErpLogs();
            return;
        }
        if (e.target.closest('#btn-refresh-logs')) {
            const btn = e.target.closest('#btn-refresh-logs');
            btn.classList.add('spinning');
            setTimeout(() => btn.classList.remove('spinning'), 600);
            loadErpLogs();
            return;
        }

        // v0.10 · 自动化子菜单切换(guard: 只处理有 data-auto-tab 的按钮，防止对账中心等共用 .auto-nav-item 类名的按钮触发 switchAutomationTab(undefined))
        const autoNav = e.target.closest('.auto-nav-item');
        if (autoNav && autoNav.dataset.autoTab) {
            switchAutomationTab(autoNav.dataset.autoTab);
            return;
        }
    });
})();

// ============================================================
// 模块外调用入口(home.js routeTo / 核心 / 其它模块经 window 调)·
// 参照 test-center.js 末尾 window 暴露范式。
// ============================================================
window.loadErpLogs = loadErpLogs;
window.loadErpEndpoints = loadErpEndpoints;
window.loadErpTodayStats = loadErpTodayStats;
window.renderErpEndpointsList = renderErpEndpointsList;
window.showLogDetail = showLogDetail;
window.retryPushLog = retryPushLog;
window.copyErpDocNo = copyErpDocNo;
window.openEndpointModal = openEndpointModal;
window.closeEndpointModal = closeEndpointModal;
window.saveEndpoint = saveEndpoint;
window.deleteEndpoint = deleteEndpoint;
window.testEndpointConnection = testEndpointConnection;
