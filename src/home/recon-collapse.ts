// ============================================================
// REFACTOR-C1 (2026-05-27) · 销售税核查vs收入对账 对称化折叠组件 recon-collapse 从 home.js 抽出为 ES module
//
// 来源:home.js L18264-18512 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
// ============================================================
// v118.32.5.5.19 · 销售税核查 vs 收入对账 对称化 折叠组件
// 监听 .recon-collapse-head 点击 → toggle data-collapsed
// 收入对账"查看清单" · 销售税核查"对账汇总 + 差异明细"
// 数据来源:已有的前端 state(glv 上传 file / vex 跑完 result)· 不动后端
// ============================================================
(function _reconCollapseIIFE() {
    'use strict';
    function _esc(s: unknown) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c: string) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[
                c as '&' | '<' | '>' | '"' | "'"
            ];
        });
    }
    function _fmtSize(b: unknown) {
        if (!b || isNaN(b as number)) return '';
        var n = Number(b);
        if (n < 1024) return n + ' B';
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
        return (n / 1024 / 1024).toFixed(1) + ' MB';
    }
    // 全局事件代理 · 点击 .recon-collapse-head 切换(销售税核查 vex-summary/vex-detail 用)
    document.addEventListener('click', function (e) {
        var head =
            (e.target as HTMLElement).closest &&
            (e.target as HTMLElement).closest('.recon-collapse-head');
        if (!head) return;
        // 头部内的按钮/链接(如导出)不触发折叠
        if ((e.target as HTMLElement).closest('button') || (e.target as HTMLElement).closest('a'))
            return;
        var box = head.closest('.recon-collapse');
        if (!box) return;
        var nowCollapsed = box.getAttribute('data-collapsed') === 'true';
        box.setAttribute('data-collapsed', nowCollapsed ? 'false' : 'true');
        if (nowCollapsed) {
            if (box.id === 'vex-summary-collapse') _fillVexSummary();
            if (box.id === 'vex-detail-collapse') _fillVexDetail();
        }
    });
    // 键盘 Enter / Space
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        var head =
            (e.target as HTMLElement).closest &&
            (e.target as HTMLElement).closest('.recon-collapse-head');
        if (!head) return;
        e.preventDefault();
        (head as HTMLElement).click();
    });

    // v118.32.5.5.25 · 收入对账"查看清单" 1:1 复刻销售税核查 vex-preview-panel
    // 含:列标题 + count / 搜索框 + 全清按钮 / 文件 row + X 按钮 / 分页"显示前 N / 共 N"
    // 数据源:STATE.vatFile / STATE.glFile(跨 IIFE 通过 input.files 读)
    // X 按钮 / 全清:调 window._glvRemoveFile(kind) · 真清 STATE + UI + 刷 panel
    var _glvSearch = { vat: '', gl: '' };
    // 暴露给 _reset 调清搜索 state
    window._glvClearPreviewSearch = function () {
        _glvSearch.vat = '';
        _glvSearch.gl = '';
    };

    var _glvFileIco =
        '<svg class="vex-pp-fi-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#111111" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
    var _glvDelIco =
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';

    function _renderGlvPreviewPanel() {
        _renderGlvColumn('vat');
        _renderGlvColumn('gl');
    }

    function _glvStateFiles(kind: string): File[] {
        // v118.35.0.3 · 多文件 · 直接从 GlVatRecon STATE 拿 · input.files 已被
        // bindUpload 主动清空(允许重复选同名文件)· 所以以 STATE 为单一真相
        try {
            // 同 IIFE 内不可直接拿 STATE,这里通过 DOM/全局桥(_glvPreviewFiles)读
            if (typeof window._glvPreviewFiles === 'function') {
                return (window._glvPreviewFiles(kind) || []) as File[];
            }
        } catch (_) {}
        var inp = document.getElementById(
            kind === 'vat' ? 'glv-vat-input' : 'glv-gl-input'
        ) as HTMLInputElement;
        return inp && inp.files ? Array.from(inp.files) : [];
    }

    function _renderGlvColumn(kind: 'vat' | 'gl') {
        var colEl = document.getElementById(kind === 'vat' ? 'glv-pp-vat-col' : 'glv-pp-gl-col');
        if (!colEl) return;
        var files = _glvStateFiles(kind);
        var titleKey = kind === 'vat' ? 'glv-up-vat-title' : 'glv-up-gl-title';
        var titleFb = kind === 'vat' ? '① 销项税报告' : '② 总账 GL';
        var title = (window.t && window.t(titleKey)) || titleFb;
        var ph = _esc((window.t && window.t('vex-preview-search')) || '搜索文件名...');
        var clearLbl = _esc((window.t && window.t('vex-preview-clear-all')) || '全清');
        var searchVal = _glvSearch[kind] || '';
        var totalCount = files.length;

        colEl.innerHTML =
            '<div class="vex-pp-col-title">' +
            '<span class="vex-pp-col-name">' +
            _esc(title) +
            ' <span class="vex-pp-col-count">' +
            totalCount +
            '</span></span>' +
            '</div>' +
            '<div class="vex-pp-search-row">' +
            '<input class="vex-pp-search" id="glv-pp-search-' +
            kind +
            '" type="text" placeholder="' +
            ph +
            '" value="' +
            _esc(searchVal) +
            '" autocomplete="off">' +
            '<button class="vex-pp-clear-btn" id="glv-pp-clearall-' +
            kind +
            '" type="button">' +
            clearLbl +
            '</button>' +
            '</div>' +
            '<div class="vex-pp-file-list" id="glv-pp-' +
            kind +
            '-list"></div>' +
            '<div class="vex-pp-pagination" id="glv-pp-' +
            kind +
            '-pg"></div>';

        // 搜索 input 联动
        var si = document.getElementById('glv-pp-search-' + kind);
        if (si)
            si.addEventListener('input', function (e) {
                _glvSearch[kind] = (e.target as HTMLInputElement).value;
                _renderGlvFileListOnly(kind);
            });
        // 全清按钮
        var ca = document.getElementById('glv-pp-clearall-' + kind);
        if (ca)
            ca.addEventListener('click', function () {
                if (window._glvRemoveFile) window._glvRemoveFile(kind);
            });

        _renderGlvFileListOnly(kind);
    }

    function _renderGlvFileListOnly(kind: 'vat' | 'gl') {
        var listEl = document.getElementById('glv-pp-' + kind + '-list');
        var pgEl = document.getElementById('glv-pp-' + kind + '-pg');
        if (!listEl) return;
        var files = _glvStateFiles(kind);
        var searchVal = (_glvSearch[kind] || '').toLowerCase();
        // 记下原始索引,供 X 按钮调 _glvRemoveFile(kind, idx) 删第 N 个
        var indexed = files.map(function (f, i) {
            return { f: f, i: i };
        });
        var filtered = searchVal
            ? indexed.filter(function (it) {
                  return it.f.name.toLowerCase().indexOf(searchVal) >= 0;
              })
            : indexed;

        listEl.innerHTML = filtered
            .map(function (it) {
                var f = it.f;
                return (
                    '<div class="vex-pp-file-row">' +
                    _glvFileIco +
                    '<span class="vex-pp-fi-name" title="' +
                    _esc(f.name) +
                    '">' +
                    _esc(f.name) +
                    '</span>' +
                    '<span class="vex-pp-fi-size">' +
                    _fmtSize(f.size) +
                    '</span>' +
                    '<button class="vex-pp-fi-del" type="button" data-kind="' +
                    kind +
                    '" data-idx="' +
                    it.i +
                    '" aria-label="remove">' +
                    _glvDelIco +
                    '</button>' +
                    '</div>'
                );
            })
            .join('');

        // X 删除按钮
        listEl.querySelectorAll('.vex-pp-fi-del').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var k = (btn as HTMLElement).dataset.kind;
                var i = parseInt((btn as HTMLElement).dataset.idx as string, 10);
                if (window._glvRemoveFile) window._glvRemoveFile(k, isNaN(i) ? null : i);
            });
        });

        // 分页提示
        if (pgEl) {
            var tpl = (window.t && window.t('vex-preview-count')) || '显示前 {n} / 共 {m}';
            pgEl.textContent = tpl
                .replace('{n}', filtered.length as unknown as string)
                .replace('{m}', filtered.length as unknown as string);
        }
    }

    // 销售税核查"对账汇总"填数据 · 从最新 vex-task 行拿
    function _fillVexSummary() {
        var setVal = function (id: string, v: unknown) {
            var el = document.getElementById(id);
            if (el) el.textContent = v == null ? '—' : String(v);
        };
        var last = window._vexLastTask || {};
        setVal('vex-sum-total', last.total);
        setVal('vex-sum-matched', last.matched);
        setVal('vex-sum-diff', last.diff);
        setVal('vex-sum-incomplete', last.incomplete);
        setVal('vex-sum-cash', last.cash);
        // @ts-expect-error TS6133 verbatim 占位
        var subEl = document.getElementById('vex-summary-sub');
    }

    // 销售税核查"差异明细"填数据 · 从最新任务的 diff_rows 拿
    function _fillVexDetail() {
        var rows = ((window._vexLastTask && window._vexLastTask.diff_rows) || []) as any[];
        var tb = document.getElementById('vex-detail-tbody');
        var tbl = document.getElementById('vex-detail-table');
        var emp = document.getElementById('vex-detail-empty');
        if (!tb || !tbl || !emp) return;
        if (rows.length === 0) {
            tbl.style.display = 'none';
            emp.style.display = '';
            return;
        }
        emp.style.display = 'none';
        tbl.style.display = '';
        var html = rows
            .map(function (r) {
                return (
                    '<tr>' +
                    '<td class="recon-detail-cell-mono">' +
                    _esc(r.invoice_no || '') +
                    '</td>' +
                    '<td>' +
                    _esc(r.field || '') +
                    '</td>' +
                    '<td>' +
                    _esc(r.report_value || '') +
                    '</td>' +
                    '<td>' +
                    _esc(r.invoice_value || '') +
                    '</td>' +
                    '<td>' +
                    _esc(r.kind || '') +
                    '</td>' +
                    '</tr>'
                );
            })
            .join('');
        tb.innerHTML = html;
        var subEl = document.getElementById('vex-detail-sub');
        if (subEl) subEl.textContent = String(rows.length);
    }

    // v5.5.23 · 收入对账 toggle 按钮 + 文件变化监听 · 复刻销售税核查
    function _initGlvTogglePreview() {
        var btn = document.getElementById('glv-toggle-preview') as
            | (HTMLElement & { _reconBound?: boolean })
            | null;
        if (btn && !btn._reconBound) {
            btn._reconBound = true;
            btn.addEventListener('click', function () {
                var panel = document.getElementById('glv-preview-panel');
                var label = document.getElementById('glv-toggle-preview-label');
                var isOpen = panel && panel.style.display !== 'none';
                if (panel) panel.style.display = isOpen ? 'none' : '';
                btn!.classList.toggle('open', !isOpen);
                if (label)
                    label.textContent = isOpen
                        ? (window.t && window.t('vex-toggle-preview-open')) || '查看清单'
                        : (window.t && window.t('vex-toggle-preview-close')) || '收起清单';
                if (!isOpen) _renderGlvPreviewPanel();
            });
        }
        // 文件变化时 · 若 panel 已展开则实时刷新
        ['glv-vat-input', 'glv-gl-input'].forEach(function (id) {
            var inp = document.getElementById(id) as
                | (HTMLElement & { _reconWatched?: boolean })
                | null;
            if (!inp || inp._reconWatched) return;
            inp._reconWatched = true;
            inp.addEventListener('change', function () {
                var panel = document.getElementById('glv-preview-panel');
                if (panel && panel.style.display !== 'none') _renderGlvPreviewPanel();
            });
        });
    }
    function _onVexResultShown() {
        var box1 = document.getElementById('vex-summary-collapse');
        var box2 = document.getElementById('vex-detail-collapse');
        if (box1) box1.style.display = '';
        if (box2) box2.style.display = '';
        _fillVexSummary();
        _fillVexDetail();
    }

    window._fillVexSummary = _fillVexSummary;
    window._fillVexDetail = _fillVexDetail;
    window._onVexResultShown = _onVexResultShown;

    document.addEventListener('DOMContentLoaded', function () {
        _initGlvTogglePreview();
    });
    // 二次重试 · 防止 DOM 还没加载
    setTimeout(_initGlvTogglePreview, 1500);

    // 切语言重渲染当前打开的内容
    if (typeof window.subscribeI18n === 'function') {
        window.subscribeI18n('recon-collapse', function () {
            var panel = document.getElementById('glv-preview-panel');
            if (panel && panel.style.display !== 'none') _renderGlvPreviewPanel();
            // toggle 按钮 label 跟随展开状态
            var label = document.getElementById('glv-toggle-preview-label');
            var btn = document.getElementById('glv-toggle-preview');
            if (label && btn) {
                label.textContent = btn.classList.contains('open')
                    ? (window.t && window.t('vex-toggle-preview-close')) || '收起清单'
                    : (window.t && window.t('vex-toggle-preview-open')) || '查看清单';
            }
        });
    }
    // 调试暴露
    window._reconCollapse = {
        renderGlvPreview: _renderGlvPreviewPanel,
        fillVexSummary: _fillVexSummary,
        fillVexDetail: _fillVexDetail,
    };
})();
