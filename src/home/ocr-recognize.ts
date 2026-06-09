// ============================================================
// REFACTOR-C1-home-batch5 (2026-05-31) · OCR 识别主流程【开始/停止/汇总/重复弹窗】从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · btn-start 识别 handler(滑窗并行调度 + 逐文件 processOneFile +
//   缓存/降级/重复/自动推送提示)· _summaryAbortedToast / _summaryFailToast · btn-stop 监听。
//   window._reprocessFile/_ocrAborted/_ocrCtrls/_dupQueue 经 window 共享。
// 调出:renderResults(ocr-results.js)· renderFileList/updateStartButton(upload-files.js)·
//   mergeFields(home.js 留)· showDuplicateDialog(ocr-duplicate-dialog.js 经 window)·
//   均经 window/bare 全局。属 OCR 热路径(铁律#26)· 真账号 E2E 严验。
// ============================================================
/* global _selectedFiles:writable, _results:writable, _quota, renderResults, renderFileList, updateStartButton, mergeFields, showDuplicateDialog, renderInfoBar, renderQuotaBanner, startEnginePolling, stopEnginePolling, _showSessionRevokedModal, getMaxFiles, token, showAlert, hideAlerts, escapeHtml, svgIcon */
import { _runDmsIdCardFlow } from './ocr-dms-idcard.js'; // REFACTOR-WB-modularize · DMS 身份证流程拆出

// ============================================================
// 开始识别
// ============================================================
document.getElementById('btn-start')!.addEventListener('click', async () => {
    hideAlerts();
    (document.getElementById('btn-start') as HTMLButtonElement).disabled = true;

    // MR.ERP DMS · 身份证订车模式分流(REFACTOR-DMS 2026-05-31)。
    // 仅当 ocr-document-mode 报告当前是 thai_id_card 时走 DMS 接口;
    // invoice 模式以下逻辑完全不变(发票热路径零改动)。
    const _docMode =
        typeof window.getOcrDocumentMode === 'function' ? window.getOcrDocumentMode() : 'invoice';
    if (_docMode === 'thai_id_card') {
        try {
            await _runDmsIdCardFlow();
        } finally {
            const _b = document.getElementById('btn-start') as HTMLButtonElement | null;
            if (_b) _b.disabled = false;
        }
        return;
    }

    // 只有 Free 用户需要检查 EasyOCR 引擎是否就绪(Plus/Pro 走 Gemini 秒响应)
    if (_userInfo && _userInfo.plan === 'free') {
        const health = await fetch('/api/health')
            .then((r) => r.json())
            .catch(() => null);
        if (health && !health.ocr_ready) {
            showAlert('info', t('alert-loading-engine'));
            startEnginePolling();
        }
    }

    // v118.20.1.6 · 并行处理多 PDF · 提到 6 路(后端单 PDF 内已 3 并发 · 总并发 ≤ Gemini 60 RPM · Tier 2 安全)
    const pendingFiles = _selectedFiles.filter((f) => f.status === 'waiting');
    const PARALLEL_LIMIT = 6;

    async function processOneFile(f: SelectedFile, isAutoRetry?: boolean) {
        // v118.20.6 · 用户已点停止 · 把待跑文件标 cancelled 跳过
        if (window._ocrAborted) {
            f.status = 'cancelled';
            f.errorKey = null;
            renderFileList();
            return {};
        }
        f.status = isAutoRetry ? 'retrying' : 'processing';
        f.canRetry = false; // 重置重试标记
        renderFileList();

        // v92 · Bug 7 · 90 秒超时(AbortController)
        const ctrl = new AbortController();
        const timeoutId = setTimeout(() => ctrl.abort('timeout'), 90000);
        // v118.20.6 · 注册到全局 · 用户点停止时一次性 abort 所有 in-flight
        window._ocrCtrls = window._ocrCtrls || new Set();
        window._ocrCtrls.add(ctrl);

        try {
            const form = new FormData();
            form.append('file', f.file, f.name);
            // v27.8.1.13a · 右上角客户切换器选中时 · 自动归属到该客户
            try {
                if (typeof window.getCurrentClientId === 'function') {
                    const _cid = window.getCurrentClientId();
                    if (_cid != null) form.append('client_id', String(_cid));
                }
            } catch (_e) {}
            const resp = await fetch('/api/ocr/recognize', {
                method: 'POST',
                headers: { Authorization: 'Bearer ' + token },
                body: form,
                signal: ctrl.signal,
            });
            clearTimeout(timeoutId);
            window._ocrCtrls.delete(ctrl);

            if (resp.status === 401 || resp.status === 403) {
                // v0.15.6 · 只有真正 auth 失败才跳登录 · 其他 403(如 need_api_key)走业务错误展示
                const cloned = resp.clone();
                const body = await cloned.json().catch(() => ({}));
                const _det = body && body.detail;
                const code = typeof _det === 'string' ? _det : (_det && _det.code) || '';
                if (!code || code.startsWith('auth.')) {
                    localStorage.removeItem('mrpilot_token');
                    if (code === 'auth.session_revoked') {
                        _showSessionRevokedModal();
                    } else {
                        const _mk =
                            code === 'auth.password_changed_relogin'
                                ? 'alert-password-changed-relogin'
                                : 'alert-session';
                        showToast(t(_mk), 'error');
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 1200);
                    }
                    return { abort: true };
                }
                if (code === 'quota.need_api_key') {
                    showToast(t('err.quota.need_api_key'), 'error');
                }
                // 让下方 !resp.ok 分支接手,展示在文件卡片上
            }

            if (!resp.ok) {
                const data = await resp.json().catch(() => ({}));
                const detail = data.detail;
                if (typeof detail === 'string') {
                    f.errorKey = 'err.' + detail;
                    f.errorParams = null;
                } else if (detail && detail.code) {
                    f.errorKey = 'err.' + detail.code;
                    f.errorParams = { ...detail, mb: _quota!.max_file_size_mb };
                } else {
                    f.errorKey = 'err.unknown';
                    f.errorParams = null;
                }
                // v118.20.6 · HTTP 状态码兜底分类(detail 没说清时按 status 归类)
                if (f.errorKey === 'err.unknown' || f.errorKey === 'err.ocr.engine_error') {
                    if (resp.status === 429) f.errorKey = 'err.rate_limit';
                    else if (resp.status === 502 || resp.status === 503 || resp.status === 504)
                        f.errorKey = 'err.gemini_overloaded';
                    else if (resp.status >= 500) f.errorKey = 'err.server';
                }
                f.status = 'error';
                // v92 · Bug 7 · 服务端错误可以重试(除了格式/大小等用户侧问题)
                f.canRetry =
                    !/not_pdf|invalid_pdf|file_too_large|too_many_pages|monthly_limit_exceeded|ip_limit_exceeded|plan_not_supported|need_api_key|not_invoice/.test(
                        (f.errorKey as string) || ''
                    );
                renderFileList();
                return {};
            }

            const data = await resp.json();
            f.status = 'success';
            // v92 · Bug 8 · 标记缓存命中
            f.fromCache = !!data.from_cache;

            const merged = mergeFields(data.pages);
            const confidence =
                data.confidence || (merged.items && merged.items.length > 0 ? 'high' : 'low');

            _results.push({
                filename: data.filename,
                pages: data.pages,
                page_count: data.page_count,
                elapsed_ms: data.elapsed_ms,
                merged_fields: merged,
                edits: {},
                confidence: confidence,
                history_id: data.history_id,
                history_ids: data.history_ids || [], // v0.11
                invoice_count: data.invoice_count || 1, // v0.11
                invoices: data.invoices || [], // v118.27.5.1 · 多发票拆分修复 · 每张独立 fields
                archive_name: data.archive_name || null,
                category_tag: data.category_tag || null,
                auto_pushed: !!data.auto_pushed,
                from_cache: !!data.from_cache, // v92 · Bug 8
            });

            // v0.11 · 识别到多张发票时额外提示
            if (data.invoice_count && data.invoice_count > 1) {
                showToast(
                    t('multi-invoice-toast', {
                        file: data.filename,
                        n: data.invoice_count,
                    }),
                    'success'
                );
            }

            // P0 修 (2026-05-26) · 同页多票防静默漏:后端检测到某页发票号候选数 >
            // 实际识别数 → 明确警告用户"可能漏识别发票 · 请人工核对"· 不静默成功。
            if (data.missed_invoice_warnings && data.missed_invoice_warnings.length) {
                const _pages = data.missed_invoice_warnings
                    .map(function (w: { page?: unknown }) {
                        return w.page;
                    })
                    .filter(function (p: unknown) {
                        return p != null;
                    });
                showToast(
                    t('missed-invoice-warn', {
                        file: data.filename,
                        pages: _pages.join(', '),
                    }),
                    'warn',
                    8000
                );
                console.warn('[OCR] possible missed invoice(s)', data.missed_invoice_warnings);
            }

            // v92 · Bug 8 · 缓存命中提示
            if (data.from_cache) {
                showToast(t('cache-hit-toast', { file: data.filename }), 'info');
            }

            // v0.13 · 重复发票警告 · 入队 · 等本批所有文件处理完后统一弹窗
            if (data.duplicate_warnings && data.duplicate_warnings.length) {
                if (!window._dupQueue) window._dupQueue = [];
                for (const w of data.duplicate_warnings) {
                    window._dupQueue.push({ filename: data.filename, ...w });
                }
            }

            // v0.9 · 自动推送提示(右下 toast)
            // A2 (Zihao 2026-05-19 拍板) · 改 info 颜色 + 文案明示"已开始 ·
            // 结果看推送日志" · auto_pushed 只是"已入队 asyncio.create_task"
            // 不是"已完成" · 显示 success 绿色会跟实际失败的推送日志矛盾.
            if (data.auto_pushed) {
                showToast(t('auto-push-fired', { file: data.filename }), 'info');
            }

            if (data.quota && data.quota.used_this_month != null && _userInfo) {
                // v109.4 · 同步更新两套字段 · 让所有用量显示都即时刷新
                _userInfo.used_this_month = data.quota.used_this_month;
                _userInfo.tenant_used = data.quota.used_this_month;
                renderInfoBar();
                renderQuotaBanner();
            }

            renderFileList();
            renderResults();
            updateStartButton();
            return {};
        } catch (e) {
            clearTimeout(timeoutId);
            try {
                window._ocrCtrls && window._ocrCtrls.delete(ctrl);
            } catch (_) {
                /* silent · Set 已删 */
            }
            // v0.10.1 · 区分错误类型 · v92 · Bug 7 · 加超时
            console.error('[Upload] failed for', f.file.name, e);
            const isAbort = e && ((e as Error).name === 'AbortError' || e === 'timeout');
            const isTimeout = isAbort && (ctrl.signal.reason === 'timeout' || e === 'timeout');
            const isNetwork =
                e &&
                (e as Error).message &&
                /NetworkError|Failed to fetch/i.test((e as Error).message);
            // v118.20.6 · 用户主动停止 · 不算错误 · 不重试 · 不入失败汇总
            const isCancelled =
                isAbort && (ctrl.signal.reason === 'user_stop' || window._ocrAborted);

            if (isCancelled) {
                f.status = 'cancelled';
                f.errorKey = null;
                f.canRetry = false;
                renderFileList();
                return {};
            }
            if (isTimeout) {
                f.errorKey = 'err.timeout';
            } else if (isAbort) {
                f.errorKey = 'err.aborted';
            } else if (isNetwork) {
                f.errorKey = 'err.network';
            } else {
                f.errorKey = 'err.unknown';
                f.errorParams = {
                    msg: e && (e as Error).message ? (e as Error).message : String(e),
                };
            }
            f.status = 'error';
            // v92 · Bug 7 · 网络/超时错误可自动重试 1 次(用户停止后不重试)
            if (
                !isAutoRetry &&
                !window._ocrAborted &&
                (isNetwork || isTimeout) &&
                navigator.onLine !== false
            ) {
                f.canRetry = true;
                renderFileList();
                // 静默等 2 秒 · 自动重试 1 次
                await new Promise((r) => setTimeout(r, 2000));
                if (
                    f.status === 'error' &&
                    (navigator.onLine as boolean) !== false &&
                    !window._ocrAborted
                ) {
                    return processOneFile(f, true);
                }
            }
            f.canRetry = true; // 自动重试也失败 · 仍允许手动重试
            renderFileList();
            return {};
        }
    }
    // v92 · Bug 7 · 暴露给重试按钮事件委托使用
    window._reprocessFile = processOneFile;

    // 滑动窗口并行调度:始终保持 PARALLEL_LIMIT 个任务在跑
    let cursor = 0;
    let aborted = false;
    async function worker() {
        while (cursor < pendingFiles.length && !aborted && !window._ocrAborted) {
            const my = cursor++;
            const r = await processOneFile(pendingFiles[my]);
            if (r && r.abort) {
                aborted = true;
                return;
            }
        }
    }
    // v118.20.6 · 显示「停止识别」按钮 · 隐藏「开始识别」
    window._ocrAborted = false;
    window._ocrCtrls = window._ocrCtrls || new Set();
    const btnStartEl = document.getElementById('btn-start');
    const btnStopEl = document.getElementById('btn-stop');
    if (btnStartEl) btnStartEl.style.display = 'none';
    if (btnStopEl) btnStopEl.style.display = '';

    // v118.27.8.1.15 · 大批量(>100 张)进度条 + 关页警告 + 首次一次性提示
    try {
        if (typeof window._bigBatchStart === 'function') window._bigBatchStart(pendingFiles);
    } catch (_) {
        /* silent · 进度条 callback 极少 fail */
    }

    const workers = [];
    for (let i = 0; i < Math.min(PARALLEL_LIMIT, pendingFiles.length); i++) {
        workers.push(worker());
    }
    await Promise.all(workers);

    // v118.27.8.1.15 · 批量结束 · 拆进度条 + 拆关页警告
    try {
        if (typeof window._bigBatchStop === 'function') window._bigBatchStop();
    } catch (_) {
        /* silent · 进度条 callback 极少 fail */
    }

    // v118.20.6 · 还原按钮显示 · 清理状态
    if (btnStartEl) btnStartEl.style.display = '';
    if (btnStopEl) btnStopEl.style.display = 'none';
    const wasAborted = !!window._ocrAborted;
    window._ocrAborted = false;
    window._ocrCtrls.clear();

    updateStartButton();
    stopEnginePolling();
    if (document.getElementById('alert-info')!.classList.contains('show')) {
        showAlert('info', t('alert-engine-ready'));
        setTimeout(hideAlerts, 2000);
    }

    // v118.20.6 · 完成后汇总 toast(成功 N · 失败按类型分组 · 用户主动停止时不弹错误类)
    try {
        const sum = {
            success: 0,
            cancelled: 0,
            network: 0,
            timeout: 0,
            quota: 0,
            overloaded: 0,
            rate: 0,
            other: 0,
        };
        for (const f of pendingFiles) {
            if (f.status === 'success') sum.success++;
            else if (f.status === 'cancelled') sum.cancelled++;
            else if (f.status === 'error') {
                const k = f.errorKey || '';
                if (k === 'err.network') sum.network++;
                else if (k === 'err.timeout' || k === 'err.aborted') sum.timeout++;
                else if ((k as string).indexOf('quota') >= 0 || k === 'err.monthly_limit_exceeded')
                    sum.quota++;
                else if (k === 'err.gemini_overloaded' || k === 'err.server') sum.overloaded++;
                else if (k === 'err.rate_limit') sum.rate++;
                else sum.other++;
            }
        }
        const total = pendingFiles.length;
        if (wasAborted) {
            showToast(_summaryAbortedToast(sum, total), 'warn', 4000);
        } else if (
            total > 1 &&
            sum.network + sum.timeout + sum.quota + sum.overloaded + sum.rate + sum.other > 0
        ) {
            showToast(_summaryFailToast(sum), 'error', 4500);
        }
    } catch (_) {
        /* silent · summary toast 失败外层兜底 */
    }

    // v0.13 · 批量识别完成后 · 弹重复警告对话框(逐个处理)
    if (window._dupQueue && window._dupQueue.length) {
        showDuplicateDialog();
    }
});

// v118.20.6 · 汇总 toast 文案(中断态 / 失败态)
type OcrSummary = Record<string, number>;
function _summaryAbortedToast(sum: OcrSummary, total: number) {
    return t('ocr-summary-aborted')
        .replace('{success}', sum.success as unknown as string)
        .replace('{cancelled}', sum.cancelled as unknown as string)
        .replace('{total}', total as unknown as string);
}
function _summaryFailToast(sum: OcrSummary) {
    const parts = [];
    if (sum.success)
        parts.push(t('ocr-summary-success').replace('{n}', sum.success as unknown as string));
    if (sum.network)
        parts.push(t('ocr-summary-network').replace('{n}', sum.network as unknown as string));
    if (sum.timeout)
        parts.push(t('ocr-summary-timeout').replace('{n}', sum.timeout as unknown as string));
    if (sum.quota)
        parts.push(t('ocr-summary-quota').replace('{n}', sum.quota as unknown as string));
    if (sum.overloaded)
        parts.push(t('ocr-summary-overloaded').replace('{n}', sum.overloaded as unknown as string));
    if (sum.rate) parts.push(t('ocr-summary-rate').replace('{n}', sum.rate as unknown as string));
    if (sum.other)
        parts.push(t('ocr-summary-other').replace('{n}', sum.other as unknown as string));
    return parts.join(' · ');
}

// v118.20.6 · 「停止识别」按钮事件 · 中断 in-flight + 标 abort
document.addEventListener('click', (e) => {
    if (!(e.target as HTMLElement).closest('#btn-stop')) return;
    if (window._ocrAborted) return; // 防双击
    window._ocrAborted = true;
    if (window._ocrCtrls && window._ocrCtrls.size) {
        window._ocrCtrls.forEach((c) => {
            try {
                c.abort('user_stop');
            } catch (_) {
                /* silent · 已 abort */
            }
        });
    }
    const btnStopEl = document.getElementById('btn-stop') as HTMLButtonElement | null;
    if (btnStopEl) btnStopEl.disabled = true;
    if (typeof showToast === 'function') showToast(t('ocr-stop-toast'), 'warn', 2000);
    setTimeout(() => {
        if (btnStopEl) btnStopEl.disabled = false;
    }, 800);
});
