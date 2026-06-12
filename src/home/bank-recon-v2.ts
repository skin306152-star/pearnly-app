// ============================================================
// REFACTOR-C1 (2026-05-27) · 银行对账 v2(Statement vs GL)bank-recon-v2 从 home.js 抽出为 ES module
// REFACTOR-WB (2026-06-02) · store 中心化 + 拆 6 子模块(store/helpers/anchor/results/history/upload)。
//
// 依赖 window._reconPollJob(recon-job-poll module · 运行期经 window. 调用);暴露
// window._loadBankReconV2Panel / _bankReconV2Init / _brv2LoadHistory(被 recon-center/recon-batch 经 window. 运行期调用)。
// ============================================================

/* global _humanizeBackendError */
import { S } from './bank-recon-v2-store.js';
import { $, esc2, _brv2FailMsg } from './bank-recon-v2-helpers.js';
import {
    _brv2SaveLastAnchorOcr,
    _brv2RestoreAnchorPrefill,
    _brv2UpdatePrefillBannerVisibility,
} from './bank-recon-v2-anchor.js';
import {
    renderResults,
    renderTable,
    showResultSections,
    _brv2Export,
} from './bank-recon-v2-results.js';
import {
    loadHistory,
    renderHistory,
    _brv2InitPager,
    _applyBrv2Search,
} from './bank-recon-v2-history.js';
import {
    renderFileList,
    updateRunBtn,
    setupDrop,
    _initBrv2TogglePreview,
} from './bank-recon-v2-upload.js';

type ReconProgress = { stage?: string; stage_total?: number; stage_done?: number };
type ReconJob = {
    status?: string;
    mapping?: unknown;
    review?: unknown;
    error_code?: string;
    result_id?: string;
};

// ── Progress helpers ──────────────────────────────────────────────
function showProgress(show: boolean) {
    const p = $('brv2-progress'),
        btn = $('brv2-run-btn') as HTMLButtonElement | null,
        err = $('brv2-error');
    if (p) p.style.display = show ? '' : 'none';
    if (btn) btn.disabled = show;
    if (err) err.style.display = 'none';
}
function showError(msg: string) {
    const err = $('brv2-error');
    if (err) {
        err.textContent = msg;
        err.style.display = '';
        err.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    showProgress(false);
    updateRunBtn();
    if (window.showToast) window.showToast(msg, 'error');
}

// ── Run reconciliation ────────────────────────────────────────────
async function runRecon() {
    if (S.stmtFiles.length === 0 || S.glFiles.length === 0) return;
    const token = localStorage.getItem('mrpilot_token') || '';
    const lang = window._currentLang || 'zh';
    const acct = (($('brv2-acct-select') || {}) as HTMLInputElement).value || '';

    showResultSections(false);
    showProgress(true);

    try {
        const fd = new FormData();
        S.stmtFiles.forEach((f) => fd.append('stmt_files', f));
        S.glFiles.forEach((f) => fd.append('gl_files', f));
        fd.append('gl_account', acct);
        fd.append('lang', lang);

        // BUG-B v118.35.0.36 · 3 个 anchor 余额手动录入 · 优先于 OCR 抽到的值
        // BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)
        const aGlClose = parseFloat(
            (($('brv2-anchor-gl-closing') || {}) as HTMLInputElement).value
        );
        const aStmtClose = parseFloat(
            (($('brv2-anchor-stmt-closing') || {}) as HTMLInputElement).value
        );
        const aStmtOpen = parseFloat(
            (($('brv2-anchor-stmt-opening') || {}) as HTMLInputElement).value
        );
        const aGlOpen = parseFloat((($('brv2-anchor-gl-opening') || {}) as HTMLInputElement).value);
        if (Number.isFinite(aGlClose))
            fd.append('gl_closing_override', aGlClose as unknown as string);
        if (Number.isFinite(aStmtClose))
            fd.append('stmt_closing_override', aStmtClose as unknown as string);
        if (Number.isFinite(aStmtOpen))
            fd.append('stmt_opening_override', aStmtOpen as unknown as string);
        if (Number.isFinite(aGlOpen))
            fd.append('gl_opening_override', aGlOpen as unknown as string);

        // BUG-FIX-RECON-ASYNC #16 · 改异步:submit 秒回 job_id → 轮询 → 用 result_id 取结果
        const submitRes = await fetch('/api/recon/bank-v2/submit', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + token },
            body: fd,
        });
        // v118.35.0.68 · 兜底:服务器返回非 JSON(网关 5xx/HTML 错误页 · 如磁盘满致 500)时
        //   res.json() 会抛 "Unexpected token '<'" · 不再原样弹给用户 · 改友好 4 语提示
        let sub = null;
        try {
            sub = await submitRes.json();
        } catch (_) {
            sub = null;
        }
        // ADR-006 · 新模板 → 弹"确认列对应"面板(确认并保存后自动重跑)· 不再报"解析失败"
        if (sub && sub.needs_mapping) {
            showProgress(false);
            if (window.ReconMapping) {
                window.ReconMapping.show(sub, {
                    token: token,
                    lang: lang,
                    onConfirmed: function () {
                        runRecon();
                    },
                });
            } else {
                showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
            }
            return;
        }
        if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
            showProgress(false);
            if (sub && (sub.detail || sub.error)) {
                showError(
                    _humanizeBackendError(
                        (sub.detail || sub.error) as string,
                        'Error ' + submitRes.status
                    )!
                );
            } else {
                showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
            }
            return;
        }

        // 轮询后台任务 · 转圈旁实时显示「共 X/Y 个文件」
        const _subEl = $('brv2-progress-sub');
        const job = (await window._reconPollJob(sub.job_id, token, {
            onProgress: (p: unknown) => {
                if (_subEl)
                    _subEl.textContent = window._reconProgressText(p as ReconProgress, lang);
            },
        })) as ReconJob;
        // BUG-FIX-RECON-GLCSV · 后台解析读到表格但不认识列(整侧 needs_mapping)→ 弹『确认列对应』。
        //   正常 CSV/Excel 在 submit 同步预检就弹了 · 这里是防御纵深(预检漏网/PDF GL 等)·
        //   守铁律「整侧失败绝不进 done 完成态」。确认保存模板后 onConfirmed 重跑(预检命中模板即过)。
        if (job && job.status === 'needs_mapping' && job.mapping) {
            showProgress(false);
            if (window.ReconMapping) {
                window.ReconMapping.show(job.mapping, {
                    token: token,
                    lang: lang,
                    onConfirmed: function () {
                        runRecon();
                    },
                });
            } else {
                showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
            }
            return;
        }
        // ADR-006 S8 · OCR 低信心/不完整 → 弹逐行核对纠错面板 · 用户改完用修正行重对账
        //   (不重 OCR、不重扣费;干净 OCR 不会到这里)· 守铁律「不静默出错」
        if (job && job.status === 'needs_review' && job.review) {
            showProgress(false);
            if (window.ReconReview) {
                window.ReconReview.show(job.review, {
                    token: token,
                    lang: lang,
                    jobId: sub.job_id,
                    onConfirmed: async function (newJobId: string) {
                        showProgress(true);
                        const j2 = (await window._reconPollJob(newJobId, token, {
                            onProgress: (p: unknown) => {
                                if (_subEl)
                                    _subEl.textContent = window._reconProgressText(
                                        p as ReconProgress,
                                        lang
                                    );
                            },
                        })) as ReconJob;
                        await _processBankJob(j2);
                    },
                });
            } else {
                showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
            }
            return;
        }
        // BUG-FIX-RECON-GLCSV · 连表格结构都没读出(PDF/OCR 失败 / 空 / 损坏 / 0 行)→ 明确失败,
        //   不再静默"完成"。按 error_code 给 4 语友好原因 + 引导(换清晰文件 / 转 Excel·CSV / 重传)。
        if (job && job.status === 'failed') {
            showProgress(false);
            showError(_brv2FailMsg(job.error_code as string, lang));
            return;
        }
        await _processBankJob(job);

        // 轮询完成后:取结果 + 渲染(初次 + S8 确认重对账共用)
        async function _processBankJob(job: ReconJob) {
            try {
                if (!job || job.status !== 'done' || !job.result_id) {
                    showProgress(false);
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                    return;
                }
                // 用 result_id 调现有结果接口(GET 已补齐顶层 stats/parse_info/warnings · 与同步跑同源)
                const res = await fetch('/api/recon/bank-v2/' + encodeURIComponent(job.result_id), {
                    headers: { Authorization: 'Bearer ' + token },
                });
                let data = null;
                try {
                    data = await res.json();
                } catch (_) {
                    data = null;
                }
                if (!res.ok || data === null || !data.ok) {
                    showProgress(false);
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                    return;
                }

                // 多账户文件:GET 不回传 gl_accounts 列表 · 单账户(绝大多数)无影响
                if ((data.gl_accounts || []).length > 1) {
                    populateAcctSelect(data.gl_accounts);
                }

                S.currentTask = data;
                S.allRows = data.detail || [];
                S.currentFilter = 'all';
                document
                    .querySelectorAll('.brv2-filter-btn')
                    .forEach((b) =>
                        b.classList.toggle('active', (b as HTMLElement).dataset.filter === 'all')
                    );

                // P0.1 BUG-B-T1 v118.35.0.37 · 后端总是落 summary._anchor_ocr · 存到 localStorage
                //   下次进对账 tab 自动预填 3 个 input · 不让用户从零填
                _brv2SaveLastAnchorOcr(data && data.summary);

                showProgress(false);
                renderResults(data);
                loadHistory();
                // 识别完成 → 自动下载对账报告一次(复用导出按钮逻辑 · 用户仍可手动再下)
                void _brv2Export((S.currentTask as any).task_id);
                const sc = $('brv2-summary-collapse');
                if (sc) sc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } catch (e) {
                showProgress(false);
                showError((e as Error).message || 'Network error');
            }
        }
    } catch (e) {
        showError((e as Error).message || 'Network error');
    }
}

function populateAcctSelect(accounts: unknown[]) {
    const sel = $('brv2-acct-select');
    if (!sel) return;
    const _al = window._currentLang || 'zh';
    const _allAcctLbl =
        { zh: '全部账户', th: 'ทุกบัญชี', en: 'All Accounts', ja: 'すべての口座' }[_al] ||
        '全部账户';
    sel.innerHTML =
        `<option value="">${_allAcctLbl}</option>` +
        accounts.map((a: unknown) => `<option value="${esc2(a)}">${esc2(a)}</option>`).join('');
    sel.style.display = '';
}

// ── Init ──────────────────────────────────────────────────────────
function init() {
    if (S.initialized) {
        // 二次进入只刷历史
        loadHistory();
        return;
    }
    S.initialized = true;

    setupDrop('brv2-stmt-zone', 'brv2-stmt-input', 'stmt');
    setupDrop('brv2-gl-zone', 'brv2-gl-input', 'gl');

    // BUG-B v118.35.0.36 · 3 个 anchor 余额手动录入 · 实时算期初差额
    const anchorIds = [
        'brv2-anchor-gl-closing',
        'brv2-anchor-stmt-closing',
        'brv2-anchor-stmt-opening',
        'brv2-anchor-gl-opening',
    ];
    function _brv2UpdateAnchorEq() {
        const stmtOpen = parseFloat(
            (($('brv2-anchor-stmt-opening') || {}) as HTMLInputElement).value
        );
        const glOpen = parseFloat((($('brv2-anchor-gl-opening') || {}) as HTMLInputElement).value);
        const eq = $('brv2-anchor-eq');
        const eqVal = $('brv2-anchor-eq-val');
        if (!eq || !eqVal) return;
        if (Number.isFinite(stmtOpen) && Number.isFinite(glOpen)) {
            const diff = stmtOpen - glOpen;
            eqVal.textContent = diff.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            eq.style.display = '';
        } else {
            eq.style.display = 'none';
        }
    }
    anchorIds.forEach((id) => {
        const el = $(id);
        if (!el) return;
        el.addEventListener('input', _brv2UpdateAnchorEq);
        // P0.1 BUG-B-T1 v118.35.0.37 · 用户敲一个字 = 真用户输入 · 移除 prefilled 灰字态
        // BUG-FIX-T4 v118.35.0.45 · 同时检查 banner 是否还要显示(全 cell 都被用户改 → 隐藏 banner)
        el.addEventListener('input', () => {
            const cell = el.closest('.brv2-anchor-cell');
            if (cell) cell.classList.remove('is-prefilled');
            _brv2UpdatePrefillBannerVisibility();
        });
    });

    // P0.1 BUG-B-T1 v118.35.0.37 · 进 tab 时用上次 OCR 抽到的 3 anchor 值预填 input
    _brv2RestoreAnchorPrefill();

    const runBtn = $('brv2-run-btn');
    if (runBtn) runBtn.addEventListener('click', runRecon);

    // 清空按钮
    const resetBtn = $('brv2-reset-btn');
    if (resetBtn)
        resetBtn.addEventListener('click', () => {
            S.currentTask = null;
            S.allRows = [];
            S.stmtFiles = [];
            S.glFiles = [];
            renderFileList('stmt');
            renderFileList('gl');
            updateRunBtn();
            showResultSections(false);
            // 重置 acct select
            const sel = $('brv2-acct-select');
            if (sel) sel.style.display = 'none';
            // BUG-B v118.35.0.36 · 重置 anchor 录入框 + 隐藏 eq 行
            // BUG-FIX-T4 v118.35.0.45 · 清空时也移除 .is-prefilled + 隐藏 banner
            anchorIds.forEach((id) => {
                const el = $(id);
                if (el) {
                    (el as HTMLInputElement).value = '';
                    const cell = el.closest && el.closest('.brv2-anchor-cell');
                    if (cell) cell.classList.remove('is-prefilled');
                }
            });
            const eq = $('brv2-anchor-eq');
            if (eq) eq.style.display = 'none';
            const banner = $('brv2-anchor-prefill-banner');
            if (banner) banner.classList.remove('show');
        });

    // 新建按钮（在折叠头里）
    const newBtn = $('brv2-new-btn');
    if (newBtn)
        newBtn.addEventListener('click', () => {
            S.currentTask = null;
            S.allRows = [];
            S.stmtFiles = [];
            S.glFiles = [];
            renderFileList('stmt');
            renderFileList('gl');
            updateRunBtn();
            showResultSections(false);
        });

    // 过滤 tab（事件冒泡拦截，不触发折叠）
    const filterTabs = $('brv2-filter-tabs');
    if (filterTabs) {
        filterTabs.addEventListener('click', (e) => {
            e.stopPropagation(); // 防止触发 recon-collapse-head 折叠
            const btn = (e.target as HTMLElement).closest('.brv2-filter-btn');
            if (!btn) return;
            S.currentFilter = (btn as HTMLElement).dataset.filter!;
            filterTabs
                .querySelectorAll('.brv2-filter-btn')
                .forEach((b) => b.classList.toggle('active', b === btn));
            renderTable();
        });
    }

    _initBrv2TogglePreview();
    _brv2InitPager();
    const hs = $('brv2-hist-search');
    if (hs) hs.addEventListener('input', _applyBrv2Search);

    loadHistory();
    updateRunBtn();
    window._brv2LoadHistory = loadHistory;

    // Subscribe to global language changes so dynamic content re-renders
    if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
    window.__i18nSubs = (window.__i18nSubs as { name?: string }[]).filter((s) => s.name !== 'brv2');
    window.__i18nSubs.push({
        name: 'brv2',
        fn: function () {
            updateRunBtn();
            renderFileList('stmt');
            renderFileList('gl');
            if (S.currentTask) renderResults(S.currentTask);
            renderHistory();
        },
    });
}

// Expose load function for panel system
window._loadBankReconV2Panel = function (containerId) {
    // Re-mount into given container if different (used by int-drawer)
    const container = containerId ? document.getElementById(containerId) : null;
    if (container && container.id !== 'recon-pane-bank') {
        container.innerHTML = `<div style="padding:16px;font-size:13px;color:var(--ink-3)">
            银行对账 v2 · 请前往对账中心使用</div>`;
    }
    init();
};

// 仅当落地路由就是对账页时即时 init;否则等导航到对账页由 loadReconcilePage→_bankReconV2Init 触发,
// 避免首屏在别的页(如 dashboard)也白拉一次 recon/bank-v2/tasks 跨区往返。
document.addEventListener('DOMContentLoaded', () => {
    const pane = document.getElementById('page-reconcile');
    if (pane && pane.classList.contains('active') && $('brv2-run-btn')) init();
});

// Also init when reconcile page is navigated to
window._bankReconV2Init = init;
