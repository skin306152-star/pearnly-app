// ============================================================
// REFACTOR-C1 (2026-05-27) · Excel公式对账内测(skin-only) excel-formula-recon 从 home.js 抽出为 ES module
//
// 来源:home.js L12984-13664 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global currentLang */
import { S, $, _authHeader } from './excel-recon-store.js';
import {
    _loadVexKpi,
    _loadVexTaskList,
    _applyVexSearch,
    _vexInitPager,
} from './excel-recon-tasklist.js';
import {
    _addInvoices,
    _addReports,
    _renderFiles,
    _renderPreviewPanel,
    _bindDropzone,
} from './excel-recon-files.js';
/* ============================================================
 * v118.32.4.9.5 · Excel 公式对账内测(skin306152 only)
 * 完全独立 IIFE · 不依赖现有 VAT 模块状态
 * ============================================================ */
(function () {
    'use strict';
    // ── 生成 Excel ──
    async function _onBuild() {
        if (S.running) return;
        if (!S.invoiceFiles.length || !S.reportFiles.length) return;
        S.running = true;
        $('vex-build').disabled = true;
        $('vex-progress').style.display = 'flex';
        var _dlBtnHide = document.getElementById('vex-download');
        if (_dlBtnHide) _dlBtnHide.style.display = 'none';
        ['vex-summary-collapse', 'vex-detail-collapse'].forEach(function (id) {
            var el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        const startAt = Date.now();
        $('vex-progress-title').textContent = t('vex-progress-running') || 'AI 抽取中';
        $('vex-progress-sub').textContent = (
            t('vex-progress-sub') || '{a} 张发票 + {b} 份报告 · 并行处理'
        )
            .replace('{a}', S.invoiceFiles.length)
            .replace('{b}', S.reportFiles.length);

        const _tick = setInterval(() => {
            const s = Math.floor((Date.now() - startAt) / 1000);
            $('vex-progress-sub').textContent = (
                t('vex-progress-elapsed') || '已 {s} 秒 · {a} 张发票 + {b} 份报告'
            )
                .replace('{s}', s)
                .replace('{a}', S.invoiceFiles.length)
                .replace('{b}', S.reportFiles.length);
        }, 1000);

        try {
            const fd = new FormData();
            for (const f of S.invoiceFiles) fd.append('invoices', f);
            for (const f of S.reportFiles) fd.append('reports', f);
            const _curLang =
                (typeof currentLang === 'string' && currentLang) ||
                localStorage.getItem('mrpilot_lang') ||
                'th';
            fd.append('lang', _curLang);

            // BUG-FIX-RECON-ASYNC #16 · 改异步:submit 秒回 job_id → 轮询 → 取结果 + 下载已生成 Excel
            const _vexTok = localStorage.getItem('mrpilot_token') || '';
            const submitRes = await fetch('/api/vat_excel/submit', {
                method: 'POST',
                headers: _authHeader(),
                body: fd,
            });
            // 兜底:网关非 JSON 错误页不再抛 "Unexpected token '<'"
            let sub = null;
            try {
                sub = await submitRes.json();
            } catch (e) {
                sub = null;
            }
            if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
                clearInterval(_tick);
                throw new Error((sub && sub.detail) || 'HTTP ' + submitRes.status);
            }
            // 轮询 · 转圈旁实时显示「共 X/Y 个文件」
            const _vexSub = $('vex-progress-sub');
            const job = await window._reconPollJob(sub.job_id, _vexTok, {
                onProgress: (p) => {
                    if (_vexSub) _vexSub.textContent = window._reconProgressText(p, _curLang);
                },
            });
            clearInterval(_tick);
            if (!job || job.status !== 'done' || !job.result_id) {
                throw new Error(t('vex-toast-fail') || '生成失败');
            }
            const taskId = job.result_id;

            // P1-4 修(2026-05-25):OCR 失败数改用后端解析层字段 invoice_ocr_failed_count ·
            //   此前用 n_total-n_ok(对账差异行数)当 OCR 失败数 → 正常匹配/普通差异都被误报"OCR 失败"。
            //   失败数由 _fetchAndFillVexPreview 从 raw 读出并返回(顺带设 window._vexLastTask)。
            let fail = 0;

            // 下载已生成的 Excel(GET 需带 token · 用 fetch+blob · 裸 <a href> 不会带 Authorization)
            const res = await fetch(
                '/api/vat_excel/tasks/' + encodeURIComponent(taskId) + '/download',
                { headers: _authHeader() }
            );
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const cd = res.headers.get('Content-Disposition') || '';
            const m = cd.match(/filename="([^"]+)"/);
            const fname = (m && m[1]) || 'vat_recon_' + Date.now() + '.xlsx';

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const dl = $('vex-download');
            dl.href = url;
            dl.download = fname;

            // 触发自动下载 1 次(用户也能手动再点)
            try {
                const _a = document.createElement('a');
                _a.href = url;
                _a.download = fname;
                document.body.appendChild(_a);
                _a.click();
                setTimeout(() => _a.remove(), 100);
            } catch (e) {}

            $('vex-progress').style.display = 'none';
            var _dlBtn = document.getElementById('vex-download');
            if (_dlBtn) _dlBtn.style.display = '';
            // P1-3 修:先 await 填好「当前任务」详情(设 window._vexLastTask + 返回 OCR 失败数)·
            //   再触发结果展示/toast · 否则汇总卡和 toast 用的是上一轮任务数据(滞后一轮)。
            if (taskId) fail = await _fetchAndFillVexPreview(taskId);
            if (window._onVexResultShown) window._onVexResultShown();

            if (fail > 0) {
                showToast(
                    (t('vex-toast-some-fail') || '有 {n} 张发票 OCR 失败').replace('{n}', fail),
                    'warn'
                );
            } else {
                showToast(t('vex-toast-done') || 'Excel 已生成', 'success');
            }
            // 刷新 KPI 卡 + 任务列表
            _loadVexKpi();
            setTimeout(_loadVexTaskList, 800);
        } catch (e) {
            clearInterval(_tick);
            $('vex-progress').style.display = 'none';
            const msg = (t('vex-toast-fail') || '生成失败') + ': ' + (e.message || e);
            showToast(msg, 'error');
        } finally {
            S.running = false;
            $('vex-build').disabled = false;
        }
    }

    function _reset() {
        S.invoiceFiles = [];
        S.reportFiles = [];
        var _dlBtn2 = document.getElementById('vex-download');
        if (_dlBtn2) _dlBtn2.style.display = 'none';
        _renderFiles();
    }

    function _fmtAmt(v) {
        if (v == null) return '—';
        var n = parseFloat(v);
        return isNaN(n)
            ? '—'
            : n.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    async function _fetchAndFillVexPreview(taskId) {
        // P1-4:返回发票 OCR 失败数(解析层真值 invoice_ocr_failed_count)· 调用方据此弹 toast。异常返回 0。
        try {
            var r = await fetch('/api/vat_excel/tasks/' + encodeURIComponent(taskId), {
                headers: _authHeader(),
            });
            if (!r.ok) throw new Error(r.status);
            var data = await r.json();
            var raw = data.raw_data_json;
            if (typeof raw === 'string') {
                try {
                    raw = JSON.parse(raw);
                } catch (e) {
                    raw = {};
                }
            }
            raw = raw || {};
            var backendRows = raw.rows || [];
            var diffRows = [];
            backendRows.forEach(function (row) {
                if (row.kind === 'invoice_orphan') {
                    diffRows.push({
                        invoice_no: row.invoice_no || '',
                        field: '仅发票有',
                        report_value: '—',
                        invoice_value: _fmtAmt(row.amount_inv),
                        kind: row.kind,
                    });
                } else if (row.kind === 'report_orphan') {
                    diffRows.push({
                        invoice_no: row.invoice_no || '',
                        field: '仅报告有',
                        report_value: _fmtAmt(row.amount_rep),
                        invoice_value: '—',
                        kind: row.kind,
                    });
                } else if (row.dims && Object.keys(row.dims).length > 0) {
                    Object.keys(row.dims).forEach(function (dim) {
                        var val = String(row.dims[dim] || '');
                        var parts = val.split(' ≠ ');
                        diffRows.push({
                            invoice_no: row.invoice_no || '',
                            field: dim,
                            report_value: parts[0] || val,
                            invoice_value: parts.length > 1 ? parts[1] : '—',
                            kind: 'diff',
                        });
                    });
                }
            });
            var cashCount = backendRows.filter(function (row) {
                return row.kind === 'matched_cash';
            }).length;
            var failCount = Math.max(0, parseInt(raw.invoice_ocr_failed_count || 0, 10));
            window._vexLastTask = {
                total: raw.n_total || 0,
                matched: raw.n_ok || 0,
                diff: raw.n_diff || 0,
                incomplete: failCount,
                cash: cashCount,
                diff_rows: diffRows,
                task_id: taskId,
            };
            if (window._fillVexSummary) window._fillVexSummary();
            if (window._fillVexDetail) window._fillVexDetail();
            return failCount;
        } catch (e) {
            return 0;
        }
    }

    // ── i18n rerender ──
    function _rerenderAll() {
        const pane = document.getElementById('vex-pane');
        if (pane)
            pane.querySelectorAll('[data-i18n]').forEach((el) => {
                const v = t(el.dataset.i18n);
                if (v) el.textContent = v;
            });
        _renderFiles();
        // 切语言时重渲任务列表 tbody(状态/客户列用 t() 渲染需刷新)
        _loadVexTaskList();
    }

    // ── init ──
    function _init() {
        // 双拖拽
        _bindDropzone('vex-drop-invoice', 'vex-input-invoice', _addInvoices);
        _bindDropzone('vex-drop-report', 'vex-input-report', _addReports);
        // 按钮
        const buildBtn = $('vex-build');
        const resetBtn = $('vex-reset');
        if (buildBtn) buildBtn.addEventListener('click', _onBuild);
        if (resetBtn) resetBtn.addEventListener('click', _reset);
        // 进销项税 tab 时刷 KPI
        document.querySelectorAll('[data-recon-tab="sale-vat"]').forEach((btn) => {
            btn.addEventListener('click', () => {
                _loadVexKpi();
                _loadVexTaskList();
            });
        });
        _vexInitPager();
        const vexSearchEl = document.getElementById('vex-task-search');
        if (vexSearchEl) vexSearchEl.addEventListener('input', _applyVexSearch);
        const previewToggleBtn = document.getElementById('vex-toggle-preview');
        if (previewToggleBtn)
            previewToggleBtn.addEventListener('click', () => {
                const panel = $('vex-preview-panel');
                const label = $('vex-toggle-preview-label');
                const isOpen = panel && panel.style.display !== 'none';
                if (panel) panel.style.display = isOpen ? 'none' : '';
                if (previewToggleBtn) previewToggleBtn.classList.toggle('open', !isOpen);
                if (label)
                    label.textContent = isOpen
                        ? t('vex-toggle-preview-open') || '查看清单'
                        : t('vex-toggle-preview-close') || '收起清单';
                if (!isOpen) _renderPreviewPanel();
            });
        _renderFiles();
        _loadVexKpi();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _init);
    } else {
        _init();
    }

    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('vex-excel', _rerenderAll);
        window.subscribeI18n('vex-preview-panel', _renderPreviewPanel);
    }
})();
