// ============================================================
// REFACTOR-C1-home-batch4 (2026-05-31) · 发票记录页【抽屉+菜单+事件绑定】从 home.js 抽出为独立 ES module
//
// 来源:home.js verbatim 0 改逻辑 · openHistoryDrawer / openHistoryDrawerAndFocusAmount /
//   injectHistorySaveButton / _checkDrawerPushStatus / pushHistoryToErp / saveHistoryEdits /
//   openHistoryMenu + initHistoryPage IIFE(行/菜单/复选/搜索/分页监听)。
// 复用 ocr-results.js 的抽屉(openDrawer/closeDrawer 经 window)· 列表侧函数(loadHistoryPage 等)
//   经 window 桥(history-list.js 提供)· 共享态 _historyState/_historySelected 在 home.js bare 读。
// 桥回:window.openHistoryDrawer(home.js L2850 guarded 调)。
// 加载顺序:与 history-list.js 互调均在事件回调/异步内(延迟解析)· 顺序无关。
// ============================================================
/* global escapeHtml, token, mergeFields, showAlert, hideAlerts, showConfirm, _results, _drawerIdx:writable, _historyState, _historySelected, loadHistoryPage, updateHistoryBatchBar, clearHistorySelection, openDrawer, closeDrawer */

type HistDrawerRow = {
    id: string;
    invoice_no?: unknown;
    has_pdf?: boolean;
    filename?: string;
    [key: string]: unknown;
};

// 详情/保存/删除/PDF 都按 active workspace 硬边界(PO-4)过滤 → 统一带鉴权 + 账套头(缺则记录被滤掉、抽屉静默打不开)。
function _hdrAuthWs(): Record<string, string> {
    return Object.assign(
        { Authorization: 'Bearer ' + token },
        typeof window._wsHeader === 'function' ? window._wsHeader() : {}
    );
}

// 点击行 → 打开抽屉查看/编辑
async function openHistoryDrawer(historyId: string) {
    try {
        const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}`, {
            headers: _hdrAuthWs(),
        });
        if (!resp.ok) return;
        const detail = await resp.json();

        // 构造与识别页一致的 result 对象,复用同一个抽屉
        const merged = mergeFields(detail.pages || []);
        const fakeResult = {
            filename: detail.filename,
            pages: detail.pages,
            page_count: detail.page_count,
            elapsed_ms: detail.elapsed_ms,
            engine: 'history',
            merged_fields: merged,
            edits: {},
            confidence: detail.confidence,
            archive_name: detail.archive_name || null,
            category_tag: detail.category_tag || null,
            _historyId: detail.id,
            _historyMode: true,
            client_id: detail.client_id || null, // v107 · 客户归属
        };
        // 推入 _results 末尾,打开抽屉后记下索引便于保存
        _results.push(fakeResult);
        _drawerIdx = _results.length - 1;
        openDrawer(_drawerIdx);

        // 额外加一个「保存修改」按钮(覆盖到抽屉底部)
        injectHistorySaveButton();

        // 销项重做:把单滚动抽屉重排成 4-tab(概览/明细/原始文件/修改记录)+ 顶部汇总条 ·
        // 只在 history 模式跑(搬 DOM 节点不重写逻辑)· 共享 openDrawer 与对账中心零影响。
        if (typeof window.historizeDrawer === 'function') window.historizeDrawer(detail);

        // v107 · 绑定客户下拉(从 detail 拿当前 client_id)
        if (typeof window.bindDrawerClient === 'function') {
            window.bindDrawerClient(detail.id, detail.client_id || null);
        }

        // P0-2: 异步检查是否已推送过(不阻塞抽屉渲染)
        _checkDrawerPushStatus(detail.id);
    } catch (e) {
        console.error('open history detail failed', e);
    }
}

// v91 · 从「缺金额 · 补金额」按钮进入 · 自动聚焦金额输入框 · 会计直接敲数字保存
async function openHistoryDrawerAndFocusAmount(historyId: string) {
    await openHistoryDrawer(historyId);
    // 下一帧 focus · 确保 drawer DOM 已渲染 + transition 已起步
    requestAnimationFrame(() => {
        const inp = document.querySelector(
            '[data-field="total_amount"]'
        ) as HTMLInputElement | null;
        if (!inp) return;
        try {
            inp.focus();
        } catch (e) {}
        try {
            inp.select();
        } catch (e) {}
        try {
            inp.scrollIntoView({ block: 'center', behavior: 'smooth' });
        } catch (e) {}
    });
}

function injectHistorySaveButton() {
    const body = document.getElementById('drawer-body');
    if (!body || document.getElementById('drawer-history-save')) return;
    const saveBar = document.createElement('div');
    saveBar.id = 'drawer-history-save';
    saveBar.className = 'drawer-history-save-bar';
    saveBar.innerHTML = `
        <span id="drawer-erp-pushed-badge" style="display:none;align-items:center;gap:4px;font-size:12px;font-weight:600;color:#059669;background:#D1FAE5;padding:3px 8px;border-radius:20px;white-space:nowrap;">
            <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:10px;height:10px;flex-shrink:0;"><path d="M2 6l3 3 5-5"/></svg>
            ${escapeHtml(t('erp-pushed-badge'))}
        </span>
        <div style="flex:1"></div>
        <button class="btn btn-primary" id="btn-save-history">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8l3 3 7-7"/></svg>
            <span>${escapeHtml(t('history-save'))}</span>
        </button>
    `;
    body.appendChild(saveBar);
    document.getElementById('btn-save-history')!.addEventListener('click', saveHistoryEdits);
}

// P0-2: 检查该发票是否已成功推送过 ERP
async function _checkDrawerPushStatus(_historyId: string) {
    /* stub */
}

async function saveHistoryEdits() {
    const r = _results[_drawerIdx];
    if (!r || !r._historyId) return;
    // 把 edits 回填到 pages 的第一页 fields(简化:只改第一页主字段,展示层)
    const newPages = JSON.parse(JSON.stringify(r.pages || []));
    if (newPages.length > 0) {
        const firstMainIdx = newPages.findIndex((p: any) => !p.is_duplicate && !p.is_copy);
        const idx = firstMainIdx >= 0 ? firstMainIdx : 0;
        const f = newPages[idx].fields || (newPages[idx].fields = {});
        // v0.17 · M2 · category_tag 是前端字段名 · 后端 db 用 fields.category · 兼容映射
        const editsForFields = { ...r.edits };
        if (editsForFields.category_tag !== undefined) {
            editsForFields.category = editsForFields.category_tag;
            delete editsForFields.category_tag;
        }
        Object.assign(f, editsForFields);
    }

    const btn = document.getElementById('btn-save-history') as HTMLButtonElement | null;
    try {
        await withLoading(btn, async () => {
            const resp = await fetch(`/api/history/${encodeURIComponent(r._historyId as string)}`, {
                method: 'PUT',
                headers: Object.assign(_hdrAuthWs(), { 'Content-Type': 'application/json' }),
                body: JSON.stringify({ pages: newPages }),
            });
            if (!resp.ok) throw new Error('save failed');
        });
        showAlert('info', t('history-save-ok'));
        setTimeout(hideAlerts, 1500);
        closeDrawer();
        // 从 _results 移除临时追加的那条
        if (r._historyMode) _results.pop();
        // 刷列表
        loadHistoryPage();
    } catch (e) {
        showAlert('error', t('history-save-fail'));
    }
}

// 「...」菜单(简单版:直接 confirm 对话框流程)
function openHistoryMenu(historyId: string, anchor: HTMLElement) {
    // 先关掉已有的 menu
    document.querySelectorAll('.history-popover').forEach((n) => n.remove());
    const rect = anchor.getBoundingClientRect();
    // v0.16 · 从行数据里取发票号 · 决定"复制发票号"是否可用
    const rec = ((_historyState.items as HistDrawerRow[]) || []).find((r) => r.id === historyId);
    const invNo = rec && rec.invoice_no ? String(rec.invoice_no) : '';
    // v114 · 是否有 PDF 留底 · 决定「下载 PDF」是否启用
    const hasPdf = rec && rec.has_pdf === true;

    const menu = document.createElement('div');
    menu.className = 'history-popover';
    menu.innerHTML = `
        <button data-act="copy-invno" ${invNo ? '' : 'disabled'}>${escapeHtml(t('history-menu-copy-invno'))}</button>
        <button data-act="download-pdf" ${hasPdf ? '' : 'disabled'}>${escapeHtml(t('history-menu-download-pdf'))}</button>
        <button data-act="download-mrerp">${escapeHtml(t('btn-mrerp-xlsx'))}</button>
        <button data-act="delete" class="danger">${escapeHtml(t('history-menu-delete'))}</button>
    `;
    menu.style.top = rect.bottom + 4 + 'px';
    menu.style.left = rect.right - 160 + 'px';
    document.body.appendChild(menu);

    const closeMenu = () => {
        menu.remove();
        document.removeEventListener('click', onDocClick, true);
    };
    const onDocClick = (e: MouseEvent) => {
        if (!menu.contains(e.target as Node) && e.target !== anchor) closeMenu();
    };
    setTimeout(() => document.addEventListener('click', onDocClick, true), 0);

    menu.addEventListener('click', async (e) => {
        const btn = (e.target as HTMLElement).closest('[data-act]') as HTMLButtonElement | null;
        if (!btn || btn.disabled) return;
        const act = btn.dataset.act;
        closeMenu();
        if (act === 'copy-invno') {
            if (!invNo) return;
            try {
                await navigator.clipboard.writeText(invNo);
                showToast(t('history-copy-invno-ok', { no: invNo }), 'success');
            } catch (err) {
                // clipboard API 被禁或 http 环境 · 降级 · textarea + execCommand
                try {
                    const ta = document.createElement('textarea');
                    ta.value = invNo;
                    ta.style.position = 'fixed';
                    ta.style.opacity = '0';
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    showToast(t('history-copy-invno-ok', { no: invNo }), 'success');
                } catch (e2) {
                    showToast(t('history-copy-invno-fail'), 'error');
                }
            }
        } else if (act === 'download-pdf') {
            // v114 · 下载 PDF 留底
            // v115 · 加 loading toast(因为大文件可能要 30s+ · 用户需要立即反馈)
            const dismissLoading = showToast(t('history-download-pdf-loading'), 'loading', 0);
            try {
                const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}/pdf`, {
                    headers: _hdrAuthWs(),
                });
                if (!resp.ok) throw new Error('download failed');
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download =
                    rec && rec.filename
                        ? rec.filename.endsWith('.pdf')
                            ? rec.filename
                            : rec.filename + '.pdf'
                        : 'invoice.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 5000);
                dismissLoading();
                showToast(t('history-download-pdf-ok'), 'success');
            } catch (err) {
                dismissLoading();
                showToast(t('history-download-pdf-fail'), 'error');
            }
        } else if (act === 'download-mrerp') {
            // MR.ERP 批量导入格式 · 单张走批量端点(传 [historyId])· 复用 erp_export_routes。
            // 后端 preflight 不合格回 422 + 错误码(缺客户映射等)→ 友好提示。
            try {
                const resp = await fetch('/api/erp/mrerp-xlsx-batch', {
                    method: 'POST',
                    headers: {
                        Authorization: 'Bearer ' + token,
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ history_ids: [historyId] }),
                });
                if (!resp.ok) {
                    let code = 'err.unknown';
                    try {
                        const d = await resp.json();
                        if (d && d.detail) code = d.detail;
                    } catch (_e) {
                        /* 非 JSON 错误体 */
                    }
                    // 把后端 preflight 错误码翻成大白话 + 指引去哪配(缺映射/缺客户/信息不全)
                    const fk =
                        code === 'ERR_NO_CUSTOMER_MAPPING'
                            ? 'mrerp-err-map'
                            : code === 'ERR_NO_CLIENT'
                              ? 'mrerp-err-client'
                              : /^ERR_NO_(INVOICE_NO|INVOICE_DATE|TOTAL_AMOUNT)$/.test(code)
                                ? 'mrerp-err-incomplete'
                                : null;
                    showToast(fk ? t(fk) : t('mrerp-xlsx-fail', { err: code }), 'error');
                    return;
                }
                const blob = await resp.blob();
                let fname = 'mrerp.xlsx';
                const cd = resp.headers.get('Content-Disposition') || '';
                const m = /filename\*=UTF-8''([^;]+)/.exec(cd);
                if (m) {
                    try {
                        fname = decodeURIComponent(m[1]);
                    } catch (_e) {
                        /* RFC5987 decode 失败用默认名 */
                    }
                }
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = fname;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 5000);
                showToast(t('mrerp-xlsx-ok'), 'success');
            } catch (err) {
                showToast(t('mrerp-xlsx-fail', { err: (err as Error).message }), 'error');
            }
        } else if (act === 'delete') {
            const ok = await showConfirm(t('history-confirm-delete'), { danger: true });
            if (!ok) return;
            try {
                const resp = await fetch(`/api/history/${encodeURIComponent(historyId)}`, {
                    method: 'DELETE',
                    headers: _hdrAuthWs(),
                });
                if (!resp.ok) throw new Error();
                showAlert('info', t('history-delete-ok'));
                setTimeout(hideAlerts, 1500);
                loadHistoryPage();
            } catch {
                showAlert('error', t('history-delete-fail'));
            }
        }
    });
}

// 事件绑定
(function initHistoryPage() {
    document.addEventListener('click', (e) => {
        const row = (e.target as HTMLElement).closest('.history-row') as HTMLElement | null;
        const menuBtn = (e.target as HTMLElement).closest('[data-hmenu]') as HTMLElement | null;
        if (menuBtn) {
            e.stopPropagation();
            openHistoryMenu(menuBtn.dataset.hmenu!, menuBtn);
            return;
        }
        // v102 · 点统一「需复核」⚠ 直接打开抽屉(原 fill-amount 改名为 review)
        const reviewBtn = (e.target as HTMLElement).closest('[data-review]') as HTMLElement | null;
        if (reviewBtn) {
            e.stopPropagation();
            openHistoryDrawer(reviewBtn.dataset.review);
            return;
        }
        // v91 · 旧「补金额」入口 · v102 已统一到 review · 兼容旧标签保留
        const fillBtn = (e.target as HTMLElement).closest(
            '[data-fill-amount]'
        ) as HTMLElement | null;
        if (fillBtn) {
            e.stopPropagation();
            openHistoryDrawerAndFocusAmount(fillBtn.dataset.fillAmount!);
            return;
        }
        // v0.16 · 点 checkbox 不触发抽屉
        if (
            (e.target as HTMLElement).closest('.history-row-check') ||
            (e.target as HTMLElement).closest('.history-cell-check')
        ) {
            return;
        }
        if (row && !(e.target as HTMLElement).closest('[data-hmenu]')) {
            openHistoryDrawer(row.dataset.hid);
        }
    });

    // v0.16 · 单行 checkbox 勾选(用 change 更稳 · 委托到 tbody)
    const tbody = document.getElementById('history-tbody');
    if (tbody) {
        tbody.addEventListener('change', (e) => {
            const cb = (e.target as HTMLElement).closest(
                '.history-row-check'
            ) as HTMLInputElement | null;
            if (!cb) return;
            const hid = cb.dataset.hid;
            if (cb.checked) _historySelected.add(hid);
            else _historySelected.delete(hid);
            updateHistoryBatchBar();
        });
    }

    // v0.16 · "全选"checkbox · 只作用于当前页
    const checkAll = document.getElementById('history-check-all');
    if (checkAll) {
        checkAll.addEventListener('change', (e) => {
            const on = (e.target as HTMLInputElement).checked;
            for (const r of _historyState.items as HistDrawerRow[]) {
                if (on) _historySelected.add(r.id);
                else _historySelected.delete(r.id);
            }
            // 同步 DOM 里所有复选框
            document.querySelectorAll('.history-row-check').forEach((el) => {
                (el as HTMLInputElement).checked = on;
            });
            updateHistoryBatchBar();
        });
    }

    // v0.16 · 取消选择
    const cancelBtn = document.getElementById('history-batch-cancel');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            clearHistorySelection();
            document.querySelectorAll('.history-row-check').forEach((el) => {
                (el as HTMLInputElement).checked = false;
            });
        });
    }

    // v0.16 · 批量删除
    const batchDelBtn = document.getElementById('history-batch-delete');
    if (batchDelBtn) {
        batchDelBtn.addEventListener('click', async () => {
            const n = _historySelected.size;
            if (n === 0) return;
            const ok = await showConfirm(t('history-batch-confirm', { n }), { danger: true });
            if (!ok) return;
            const ids = Array.from(_historySelected);
            try {
                const resp = await fetch('/api/history/batch-delete', {
                    method: 'POST',
                    headers: Object.assign(_hdrAuthWs(), { 'Content-Type': 'application/json' }),
                    body: JSON.stringify({ ids }),
                });
                if (!resp.ok) throw new Error('batch delete failed');
                const data = await resp.json();
                showToast(t('history-batch-done', { n: data.deleted || 0 }), 'success');
                clearHistorySelection();
                loadHistoryPage();
            } catch (e) {
                console.error('batch delete', e);
                showToast(t('history-batch-fail'), 'error');
            }
        });
    }

    let searchTimer: ReturnType<typeof setTimeout> | null = null;
    document.getElementById('history-search')!.addEventListener('input', (e) => {
        const val = (e.target as HTMLInputElement).value;
        document.getElementById('history-search-clear')!.style.display = val ? '' : 'none';
        clearTimeout(searchTimer!);
        searchTimer = setTimeout(() => {
            _historyState.keyword = val.trim();
            _historyState.page = 0;
            clearHistorySelection();
            loadHistoryPage();
        }, 300);
    });
    document.getElementById('history-search-clear')!.addEventListener('click', () => {
        const input = document.getElementById('history-search') as HTMLInputElement | null;
        input!.value = '';
        _historyState.keyword = '';
        _historyState.page = 0;
        clearHistorySelection();
        document.getElementById('history-search-clear')!.style.display = 'none';
        loadHistoryPage();
        input!.focus();
    });

    document.getElementById('history-range')!.addEventListener('change', (e) => {
        _historyState.range = parseInt((e.target as HTMLSelectElement).value, 10);
        _historyState.page = 0;
        clearHistorySelection();
        loadHistoryPage();
    });

    // 汇总卡 / 状态下拉 / 来源下拉 / 上传按钮的绑定收口在 history-list(它 owns 列表态)·
    // initHistoryFilters 经 window 桥(history-list 提供 · 顺序无关)。
    if (typeof window.initHistoryFilters === 'function') window.initHistoryFilters();

    document.getElementById('history-prev')!.addEventListener('click', () => {
        if (_historyState.page > 0) {
            _historyState.page--;
            clearHistorySelection();
            loadHistoryPage();
        }
    });
    document.getElementById('history-next')!.addEventListener('click', () => {
        if ((_historyState.page + 1) * _historyState.pageSize < _historyState.total) {
            _historyState.page++;
            clearHistorySelection();
            loadHistoryPage();
        }
    });
})();

// 桥回 home.js(L2850 guarded 调)
window.openHistoryDrawer = openHistoryDrawer;
