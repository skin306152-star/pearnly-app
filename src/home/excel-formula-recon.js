// ============================================================
// REFACTOR-C1 (2026-05-27) · Excel公式对账内测(skin-only) excel-formula-recon 从 home.js 抽出为 ES module
//
// 来源:home.js L12984-13664 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global showConfirm, currentLang */

/* ============================================================
 * v118.32.4.9.5 · Excel 公式对账内测(skin306152 only)
 * 完全独立 IIFE · 不依赖现有 VAT 模块状态
 * ============================================================ */
(function () {
    'use strict';

    const MAX_INV = 1000;
    const MAX_REP = 30;
    // P1-1 修(2026-05-25 销项税回归):此前只允许 pdf/jpg/png/webp · 但 UI 文案 + accept 宣传
    //   支持 Excel/CSV/Word → 用户选了被静默丢弃(开始按钮还禁用)。放开到与 accept 一致 ·
    //   后端发票侧/报告侧都已能解析这些格式(报告 parse_vat_report 全格式 · 发票走 pipeline)。
    const ALLOWED_EXT = /\.(pdf|jpe?g|png|webp|tiff?|xlsx?|xlsm|csv|tsv|docx?)$/i;

    const $ = (id) => document.getElementById(id);
    function _authHeader() {
        return { Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || '') };
    }
    function _esc(s) {
        return String(s == null ? '' : s).replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
        );
    }
    function _fmtSize(b) {
        if (b < 1024) return b + ' B';
        if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
        return (b / 1024 / 1024).toFixed(1) + ' MB';
    }

    let _invoiceFiles = [];
    let _reportFiles = [];
    let _running = false;
    let _vexAllRows = [];
    let _vexExpanded = false;
    let _previewLimitInv = 50,
        _previewLimitRep = 50;
    let _previewSearchInv = '',
        _previewSearchRep = '';

    // ── KPI 刷新 ──
    async function _loadVexKpi() {
        try {
            const r = await fetch('/api/vat_excel/tasks?page=1&page_size=1', {
                headers: _authHeader(),
            });
            if (!r.ok) return;
            const d = await r.json();
            const k = d.kpi || {};
            [
                ['vex-kpi-month-val', k.this_month],
                ['vex-kpi-running-val', k.running],
                ['vex-kpi-done-val', k.done],
                ['vex-kpi-failed-val', k.failed],
            ].forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val == null ? 0 : val;
            });
        } catch (e) {}
    }

    // ── 任务列表加载 ──
    async function _loadVexTaskList() {
        try {
            // P1-5 修(2026-05-25):后端限制 page_size le=100 · 此前发 200 → 持续 422。改 100。
            const r = await fetch('/api/vat_excel/tasks?page=1&page_size=100', {
                headers: _authHeader(),
            });
            if (!r.ok) return;
            const d = await r.json();
            _renderVexTaskList(d.rows || []);
        } catch (e) {}
    }

    const VEX_PAGE_SIZE = 10;
    var _vexPage = 1;

    function _applyVexSearch() {
        var q = ((document.getElementById('vex-task-search') || {}).value || '')
            .trim()
            .toLowerCase();
        _vexPage = 1;
        _renderVexTaskList(_vexAllRows);
        if (!q) return;
        var tbody = document.getElementById('vex-task-tbody');
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach(function (tr) {
            if (!tr.dataset.taskId) return;
            tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
        });
    }

    function _renderVexTaskList(rows) {
        _vexAllRows = rows || _vexAllRows;
        const tbody = document.getElementById('vex-task-tbody');
        if (!tbody) return;
        if (!_vexAllRows.length) {
            tbody.innerHTML =
                '<tr><td colspan="9" class="vex-task-empty">' +
                (t('sv-empty-title') || '还没有对账任务') +
                '</td></tr>';
            _vexRenderPager(0);
            return;
        }
        const totalPages = Math.ceil(_vexAllRows.length / VEX_PAGE_SIZE);
        if (_vexPage > totalPages) _vexPage = totalPages;
        const start = (_vexPage - 1) * VEX_PAGE_SIZE;
        _doRenderVexRows(_vexAllRows.slice(start, start + VEX_PAGE_SIZE));
        _vexRenderPager(_vexAllRows.length);
    }

    function _vexRenderPager(total) {
        const pager = document.getElementById('vex-task-pager');
        const info = document.getElementById('vex-task-pager-info');
        const prev = document.getElementById('vex-task-prev');
        const next = document.getElementById('vex-task-next');
        if (!pager) return;
        if (total <= VEX_PAGE_SIZE) {
            pager.style.display = 'none';
            return;
        }
        pager.style.display = '';
        const totalPages = Math.ceil(total / VEX_PAGE_SIZE);
        if (info) info.textContent = _vexPage + ' / ' + totalPages;
        if (prev) prev.disabled = _vexPage <= 1;
        if (next) next.disabled = _vexPage >= totalPages;
    }

    function _doRenderVexRows(rows) {
        const tbody = document.getElementById('vex-task-tbody');
        if (!tbody) return;
        const statusLabel = {
            pending: t('vex-status-pending') || '待处理',
            running: t('vex-status-running') || '处理中',
            done: t('vex-status-done') || '已完成',
            failed: t('vex-status-failed') || '失败',
        };
        const statusClass = {
            pending: 'badge-gray',
            running: 'badge-blue',
            done: 'badge-green',
            failed: 'badge-red',
        };
        const dlSvg = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>`;
        const delSvg = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>`;
        tbody.innerHTML = rows
            .map((row) => {
                const dt = row.created_at
                    ? new Date(row.created_at).toLocaleString([], {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                      })
                    : '—';
                const period = row.period || '—';
                const kpiStr =
                    row.matched_count != null
                        ? row.matched_count + ' ✓ · ' + row.mismatched_count + ' ⚠'
                        : '—';
                const diff =
                    row.mismatch_amount != null
                        ? '฿ ' + Number(row.mismatch_amount).toLocaleString()
                        : '—';
                const elapsed =
                    row.elapsed_seconds != null ? row.elapsed_seconds.toFixed(1) + ' s' : '—';
                const st = row.status || 'pending';
                const clientDisplay =
                    row.client_name && row.client_name !== 'client'
                        ? row.client_name
                        : t('vex-client-all') || '全部客户';
                return `<tr class="vex-task-row" data-task-id="${_esc(row.id)}" style="cursor:pointer">
                <td>${dt}</td>
                <td>${_esc(clientDisplay)}</td>
                <td>${_esc(period)}</td>
                <td>${(row.invoice_count || 0) + ' / ' + (row.report_count || 0)}</td>
                <td>${kpiStr}</td>
                <td>${diff}</td>
                <td><span class="badge ${statusClass[st] || 'badge-gray'}">${statusLabel[st] || st}</span></td>
                <td>${elapsed}</td>
                <td><div class="vex-task-actions">
                    <button class="vex-task-dl-btn" data-task-id="${_esc(row.id)}" title="${t('hist_export') || '导出'}">${dlSvg}</button>
                    <button class="vex-task-del-btn" data-task-id="${_esc(row.id)}" title="${t('vex-task-delete-confirm-title') || '删除'}">${delSvg}</button>
                </div></td>
            </tr>`;
            })
            .join('');
        // 下载按钮
        tbody.querySelectorAll('.vex-task-dl-btn').forEach((btn) => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const taskId = btn.dataset.taskId;
                try {
                    const resp = await fetch(
                        '/api/vat_excel/tasks/' + encodeURIComponent(taskId) + '/download',
                        { credentials: 'include', headers: _authHeader() }
                    );
                    if (resp.status === 410) {
                        showToast(t('vex-toast-expired') || '数据已过期 · 请重新对账', 'warn');
                        return;
                    }
                    if (!resp.ok) {
                        showToast(t('vex-toast-dl-fail') || '下载失败 · 请重试', 'error');
                        return;
                    }
                    const blob = await resp.blob();
                    const cd = resp.headers.get('Content-Disposition') || '';
                    const m = cd.match(/filename\*?=(?:UTF-8''|")?([^";]+)/i);
                    const filename = m ? decodeURIComponent(m[1]) : 'vat_recon_' + taskId + '.xlsx';
                    const url = URL.createObjectURL(blob);
                    const tmpA = document.createElement('a');
                    tmpA.href = url;
                    tmpA.download = filename;
                    tmpA.click();
                    setTimeout(() => URL.revokeObjectURL(url), 1000);
                } catch (_) {
                    showToast(t('vex-toast-dl-fail') || '下载失败 · 请重试', 'error');
                }
            });
        });
        // 删除按钮
        tbody.querySelectorAll('.vex-task-del-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                _confirmDeleteVatTask(btn.dataset.taskId);
            });
        });
        _applyVexSearch();
    }

    function _vexInitPager() {
        var prev = document.getElementById('vex-task-prev');
        var next = document.getElementById('vex-task-next');
        if (prev && !prev._vexBound) {
            prev._vexBound = true;
            prev.addEventListener('click', function () {
                if (_vexPage > 1) {
                    _vexPage--;
                    _renderVexTaskList();
                }
            });
        }
        if (next && !next._vexBound) {
            next._vexBound = true;
            next.addEventListener('click', function () {
                var totalPages = Math.ceil(_vexAllRows.length / VEX_PAGE_SIZE);
                if (_vexPage < totalPages) {
                    _vexPage++;
                    _renderVexTaskList();
                }
            });
        }
    }

    async function _confirmDeleteVatTask(taskId) {
        const title = t('vex-task-delete-confirm-title') || '删除对账任务?';
        const body = t('vex-task-delete-confirm-body') || '同时清掉对应的发票识别缓存 · 不可恢复';
        const ok = await showConfirm(body, {
            title,
            danger: true,
            okText: t('vex-task-delete-confirm-title') || '确认删除',
        });
        if (!ok) return;
        try {
            const resp = await fetch('/api/vat_excel/tasks/' + encodeURIComponent(taskId), {
                method: 'DELETE',
                credentials: 'include',
                headers: _authHeader(),
            });
            if (!resp.ok) throw new Error(resp.status);
            showToast(t('vex-task-delete-ok') || '已删除', 'success');
            _loadVexTaskList();
            _loadVexKpi();
        } catch (_) {
            showToast(t('vex-task-delete-fail') || '删除失败', 'error');
        }
    }

    async function _clearOldTasks() {
        const msg = t('vex-clear-old-confirm') || '确定清除 7 天前的对账任务?此操作不可撤销';
        const ok = await showConfirm(msg, { danger: true });
        if (!ok) return;
        try {
            const resp = await fetch('/api/vat_excel/tasks/clear_old?days=7', {
                method: 'DELETE',
                credentials: 'include',
                headers: _authHeader(),
            });
            if (!resp.ok) throw new Error(resp.status);
            const data = await resp.json();
            const n = data.deleted || 0;
            showToast(
                (t('vex-clear-old-success') || '已清除 {n} 条任务').replace('{n}', n),
                'success'
            );
            _loadVexTaskList();
            _loadVexKpi();
        } catch (_) {
            showToast(t('vex-task-delete-fail') || '操作失败', 'error');
        }
    }

    // P1-1:不支持格式的明确提示(4 语)· 取代此前静默丢弃
    function _vexToastRejected(n) {
        const lang = window._currentLang || 'th';
        const M = {
            zh: `已忽略 ${n} 个不支持的文件 · 仅支持 PDF / 图片 / Excel / CSV / Word`,
            th: `ข้ามไฟล์ที่ไม่รองรับ ${n} ไฟล์ · รองรับเฉพาะ PDF / รูปภาพ / Excel / CSV / Word`,
            en: `Ignored ${n} unsupported file(s) · only PDF / image / Excel / CSV / Word are supported`,
            ja: `非対応ファイル ${n} 件をスキップ · 対応形式は PDF / 画像 / Excel / CSV / Word のみ`,
        };
        showToast(M[lang] || M.th, 'warn');
    }

    // ── 文件入队(去重 + 上限) ──
    function _addInvoices(files) {
        const seen = new Set(_invoiceFiles.map((f) => f.name + '|' + f.size));
        let _rejected = 0; // P1-1:不支持格式不再静默丢弃 · 计数后给明确 toast
        for (const f of files) {
            if (!ALLOWED_EXT.test(f.name)) {
                _rejected++;
                continue;
            }
            const k = f.name + '|' + f.size;
            if (seen.has(k)) continue;
            seen.add(k);
            _invoiceFiles.push(f);
            if (_invoiceFiles.length >= MAX_INV) break;
        }
        if (_rejected > 0) _vexToastRejected(_rejected);
        if (_invoiceFiles.length > MAX_INV) {
            _invoiceFiles = _invoiceFiles.slice(0, MAX_INV);
            showToast(t('vex-toast-cap-inv'), 'warn');
        }
        _renderFiles();
    }

    function _addReports(files) {
        const seen = new Set(_reportFiles.map((f) => f.name + '|' + f.size));
        let _rejected = 0; // P1-1:不支持格式不再静默丢弃
        for (const f of files) {
            if (!ALLOWED_EXT.test(f.name)) {
                _rejected++;
                continue;
            }
            const k = f.name + '|' + f.size;
            if (seen.has(k)) continue;
            seen.add(k);
            _reportFiles.push(f);
            if (_reportFiles.length >= MAX_REP) break;
        }
        if (_rejected > 0) _vexToastRejected(_rejected);
        if (_reportFiles.length > MAX_REP) {
            _reportFiles = _reportFiles.slice(0, MAX_REP);
            showToast(t('vex-toast-cap-rep'), 'warn');
        }
        _renderFiles();
    }

    function _removeInvoice(idx) {
        _invoiceFiles.splice(idx, 1);
        _renderFiles();
    }
    function _removeReport(idx) {
        _reportFiles.splice(idx, 1);
        _renderFiles();
    }

    function _renderFiles() {
        const il = $('vex-list-invoice');
        const rl = $('vex-list-report');
        const _cntInv = $('vex-count-invoice'),
            _cntRep = $('vex-count-report');
        if (_cntInv) _cntInv.textContent = _invoiceFiles.length;
        if (_cntRep) _cntRep.textContent = _reportFiles.length;

        const _row = (f, idx, kind) => `<div class="vex-fi">
            <svg class="vex-fi-ic" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l4 4v8a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/><path d="M10 2v4h4"/></svg>
            <span class="vex-fi-n" title="${_esc(f.name)}">${_esc(f.name)}</span>
            <span class="vex-fi-s">${_fmtSize(f.size)}</span>
            <button class="vex-fi-x" type="button" data-vex-kind="${kind}" data-vex-idx="${idx}" aria-label="remove">×</button>
        </div>`;
        if (il)
            il.innerHTML =
                _invoiceFiles.map((f, i) => _row(f, i, 'inv')).join('') ||
                `<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>`;
        if (rl)
            rl.innerHTML =
                _reportFiles.map((f, i) => _row(f, i, 'rep')).join('') ||
                `<div class="vex-fi-empty" data-i18n="vex-no-files">还没文件</div>`;

        // 删除按钮事件
        document.querySelectorAll('.vex-fi-x').forEach((b) => {
            b.addEventListener('click', (e) => {
                const k = b.dataset.vexKind;
                const i = parseInt(b.dataset.vexIdx, 10);
                if (k === 'inv') _removeInvoice(i);
                else _removeReport(i);
            });
        });

        // 启用 / 禁用「生成 Excel」按钮
        const ok = _invoiceFiles.length > 0 && _reportFiles.length > 0;
        $('vex-build').disabled = !ok || _running;
        const info = $('vex-action-info');
        if (info) {
            if (!_invoiceFiles.length || !_reportFiles.length) {
                info.textContent = t('vex-need-both') || '需要至少 1 张发票 + 1 份 VAT 报告';
                info.className = 'vex-action-info muted';
            } else {
                info.textContent = (t('vex-ready') || '已就绪 · {a} 张发票 · {b} 份报告')
                    .replace('{a}', _invoiceFiles.length)
                    .replace('{b}', _reportFiles.length);
                info.className = 'vex-action-info ok';
            }
        }
        _renderPreviewPanel();
    }

    // ── 预览面板 ──
    const _ppInvIcon = `<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>`;
    const _ppRepIcon = `<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`;
    const _ppDelIcon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

    function _renderPreviewPanel() {
        const panel = $('vex-preview-panel');
        if (!panel || panel.style.display === 'none') return;
        _renderPreviewColFull('inv');
        _renderPreviewColFull('rep');
        const guide = $('vex-pp-guide');
        if (guide) guide.style.display = _invoiceFiles.length > 100 ? 'flex' : 'none';
    }

    function _renderPreviewColFull(kind) {
        const colEl = $(kind === 'inv' ? 'vex-pp-invoice-col' : 'vex-pp-report-col');
        if (!colEl) return;
        const files = kind === 'inv' ? _invoiceFiles : _reportFiles;
        const searchVal = kind === 'inv' ? _previewSearchInv : _previewSearchRep;
        const title =
            t(kind === 'inv' ? 'vex-preview-invoice' : 'vex-preview-report') ||
            (kind === 'inv' ? '销售发票' : 'VAT 报告');
        const ph = _esc(t('vex-preview-search') || '搜索文件名...');
        const clearLbl = _esc(t('vex-preview-clear-all') || '全清');

        colEl.innerHTML = `
            <div class="vex-pp-col-title">
                <span class="vex-pp-col-name">${_esc(title)} <span class="vex-pp-col-count">${files.length}</span></span>
            </div>
            <div class="vex-pp-search-row">
                <input class="vex-pp-search" id="vex-pp-search-${kind}" type="text"
                       placeholder="${ph}" value="${_esc(searchVal)}" autocomplete="off">
                <button class="vex-pp-clear-btn" id="vex-pp-clearall-${kind}" type="button">${clearLbl}</button>
            </div>
            <div class="vex-pp-file-list" id="vex-pp-${kind}-list"></div>
            <div class="vex-pp-pagination" id="vex-pp-${kind}-pg"></div>`;

        const si = $('vex-pp-search-' + kind);
        if (si)
            si.addEventListener('input', (e) => {
                if (kind === 'inv') {
                    _previewSearchInv = e.target.value;
                    _previewLimitInv = 50;
                } else {
                    _previewSearchRep = e.target.value;
                    _previewLimitRep = 50;
                }
                _renderFileListOnly(kind);
            });

        const ca = $('vex-pp-clearall-' + kind);
        if (ca)
            ca.addEventListener('click', () => {
                if (kind === 'inv') {
                    _invoiceFiles = [];
                    _previewSearchInv = '';
                    _previewLimitInv = 50;
                } else {
                    _reportFiles = [];
                    _previewSearchRep = '';
                    _previewLimitRep = 50;
                }
                _renderFiles();
            });

        _renderFileListOnly(kind);
    }

    function _renderFileListOnly(kind) {
        const listEl = $('vex-pp-' + kind + '-list');
        const pgEl = $('vex-pp-' + kind + '-pg');
        if (!listEl) return;
        const files = kind === 'inv' ? _invoiceFiles : _reportFiles;
        const searchVal = kind === 'inv' ? _previewSearchInv : _previewSearchRep;
        const limit = kind === 'inv' ? _previewLimitInv : _previewLimitRep;
        const icon = kind === 'inv' ? _ppInvIcon : _ppRepIcon;

        const indexed = files.map((f, i) => ({ f, i }));
        const filtered = searchVal
            ? indexed.filter(({ f }) => f.name.toLowerCase().includes(searchVal.toLowerCase()))
            : indexed;
        const shown = filtered.slice(0, limit);

        listEl.innerHTML =
            shown
                .map(
                    ({ f, i }) => `
            <div class="vex-pp-file-row">
                ${icon}
                <span class="vex-pp-fi-name" title="${_esc(f.name)}">${_esc(f.name)}</span>
                <span class="vex-pp-fi-size">${_fmtSize(f.size)}</span>
                <button class="vex-pp-fi-del" type="button" data-kind="${kind}" data-ridx="${i}" aria-label="remove">${_ppDelIcon}</button>
            </div>`
                )
                .join('') +
            `<div id="vex-pp-sentinel-${kind}" style="height:1px;flex-shrink:0"></div>`;

        listEl.querySelectorAll('.vex-pp-fi-del').forEach((btn) => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.ridx, 10);
                if (btn.dataset.kind === 'inv') _removeInvoice(idx);
                else _removeReport(idx);
            });
        });

        if (pgEl) {
            const tpl = t('vex-preview-count') || '显示前 {n} / 共 {m}';
            pgEl.textContent = tpl.replace('{n}', shown.length).replace('{m}', filtered.length);
        }
        _bindPreviewObserver(kind, filtered.length);
    }

    function _bindPreviewObserver(kind, totalFiltered) {
        const limit = kind === 'inv' ? _previewLimitInv : _previewLimitRep;
        if (limit >= totalFiltered) return;
        const sentinel = $('vex-pp-sentinel-' + kind);
        const listEl = $('vex-pp-' + kind + '-list');
        if (!sentinel || !listEl) return;
        const obs = new IntersectionObserver(
            (entries) => {
                if (!entries[0].isIntersecting) return;
                obs.disconnect();
                if (kind === 'inv') _previewLimitInv += 50;
                else _previewLimitRep += 50;
                _renderFileListOnly(kind);
            },
            { root: listEl, threshold: 0.8 }
        );
        obs.observe(sentinel);
    }

    // ── 拖拽事件 ──
    function _bindDropzone(zoneId, inputId, onFiles, wrongKindHint) {
        const zone = $(zoneId);
        const input = $(inputId);
        if (!zone || !input) return;
        zone.addEventListener('click', () => input.click());
        zone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                input.click();
            }
        });
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            const arr = Array.from(e.dataTransfer.files);
            const ok = arr.filter((f) => ALLOWED_EXT.test(f.name));
            if (!ok.length) {
                showToast(t('vex-toast-bad-ext'), 'error');
                return;
            }
            onFiles(ok);
        });
        input.addEventListener('change', () => {
            const arr = Array.from(input.files);
            onFiles(arr);
            input.value = '';
        });
    }

    // ── 生成 Excel ──
    async function _onBuild() {
        if (_running) return;
        if (!_invoiceFiles.length || !_reportFiles.length) return;
        _running = true;
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
            .replace('{a}', _invoiceFiles.length)
            .replace('{b}', _reportFiles.length);

        const _tick = setInterval(() => {
            const s = Math.floor((Date.now() - startAt) / 1000);
            $('vex-progress-sub').textContent = (
                t('vex-progress-elapsed') || '已 {s} 秒 · {a} 张发票 + {b} 份报告'
            )
                .replace('{s}', s)
                .replace('{a}', _invoiceFiles.length)
                .replace('{b}', _reportFiles.length);
        }, 1000);

        try {
            const fd = new FormData();
            for (const f of _invoiceFiles) fd.append('invoices', f);
            for (const f of _reportFiles) fd.append('reports', f);
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
            _running = false;
            $('vex-build').disabled = false;
        }
    }

    function _reset() {
        _invoiceFiles = [];
        _reportFiles = [];
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
