// ============================================================
// REFACTOR-C1 (2026-05-27) · GL vs 销项税报告对账模块 gl-vat-recon 从 home.js 抽出为 ES module
//
// 来源:home.js L13669-14416 · verbatim 0 改逻辑(仅 prettier 重排)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* ════════════════════════════════════════════════════════════════════
 * v118.32.5 · GL vs 销项税报告 对账模块
 * ════════════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    const $ = (id) => document.getElementById(id);
    const _token = () => localStorage.getItem('mrpilot_token') || '';
    // v118.32.5.1 · 优先读 window.currentLang（实时切换不依赖 localStorage 刷新）
    const _lang = () => {
        if (typeof window.currentLang === 'string' && window.currentLang) return window.currentLang;
        return localStorage.getItem('mrpilot_lang') || 'th';
    };
    const _authH = () => ({ Authorization: 'Bearer ' + _token() });

    const STATE = {
        inited: false,
        // v118.35.0.3 · 多文件 · File[]
        glFile: [],
        vatFile: [],
        running: false,
        currentTaskId: null,
        lastDetail: [],
        lastSummary: null,
    };

    // ── 多语言文本（与后端 _I18N 字典同源） ──────────────────────────
    const I18N = {
        th: {
            not_found: 'ไม่พบข้อมูล',
            running: 'กำลังกระทบยอด…',
            error: 'เกิดข้อผิดพลาด',
            need_files: 'กรุณาเลือกไฟล์ทั้งสอง',
            done: 'เสร็จสิ้น',
            hint_need_both: 'อัปโหลด ① รายงานภาษีขาย + ② GL',
            hint_need_one_more: 'อัปโหลดอีก 1 ไฟล์',
            hint_ready: 'พร้อมแล้ว · กดเริ่มกระทบยอด',
            hist_load: 'โหลด',
            hist_export: 'ส่งออก',
            hist_delete: 'ลบ',
            confirm_delete: 'ยืนยันการลบงานนี้?',
            s_gl_total: 'ยอดรวมตามบัญชีแยกประเภท',
            s_minus_gl_cr: 'หัก : รายการเครดิตที่ไม่มีในรายงานภาษีขาย',
            s_plus_gl_dr: 'บวก : รายการเดบิตที่ไม่มีในรายงานภาษีขาย',
            s_plus_vat_p: 'บวก : รายการยอดขายที่ไม่มีในบัญชีแยกประเภท',
            s_minus_vat_n: 'หัก : รายการลดหนี้ที่ไม่มีในบัญชีแยกประเภท',
            s_vat_total: 'ยอดรวมตามรายงานภาษีขาย',
        },
        zh: {
            not_found: '未找到数据',
            running: '正在对账中...',
            error: '出错了',
            need_files: '请先选择两个文件',
            done: '完成',
            hint_need_both: '请上传① 销项税报告 + ② 总账 GL',
            hint_need_one_more: '还需上传 1 份文件',
            hint_ready: '已就绪 · 点击开始对账',
            hist_load: '加载',
            hist_export: '导出',
            hist_delete: '删除',
            confirm_delete: '确认删除此任务？',
            s_gl_total: '总账金额合计',
            s_minus_gl_cr: '减：销项税报告中未列的贷方记录',
            s_plus_gl_dr: '加：销项税报告中未列的借方记录',
            s_plus_vat_p: '加：总账中未列的销售记录',
            s_minus_vat_n: '减：总账中未列的贷项凭单(credit note)记录',
            s_vat_total: '销项税报告金额合计',
        },
        en: {
            not_found: 'Not found',
            running: 'Reconciling...',
            error: 'Error',
            need_files: 'Please select both files',
            done: 'Done',
            hint_need_both: 'Upload ① Output VAT report + ② GL file',
            hint_need_one_more: '1 more file required',
            hint_ready: 'Ready · click Run to start',
            hist_load: 'Load',
            hist_export: 'Export',
            hist_delete: 'Delete',
            confirm_delete: 'Delete this task?',
            s_gl_total: 'Total per General Ledger',
            s_minus_gl_cr: 'Less: GL credits not in VAT Report',
            s_plus_gl_dr: 'Add: GL debits not in VAT Report',
            s_plus_vat_p: 'Add: Sales in VAT Report not in GL',
            s_minus_vat_n: 'Less: Credit notes in VAT Report not in GL',
            s_vat_total: 'Total per VAT Sales Report',
        },
        ja: {
            not_found: 'データなし',
            running: '照合中…',
            error: 'エラー',
            need_files: '両方のファイルを選択してください',
            done: '完了',
            hint_need_both: '① 売上税報告 + ② GL をアップロード',
            hint_need_one_more: 'あと 1 ファイル必要',
            hint_ready: '準備完了 · 「開始」をクリック',
            hist_load: '読込',
            hist_export: '出力',
            hist_delete: '削除',
            confirm_delete: 'このタスクを削除しますか?',
            s_gl_total: '総勘定元帳合計',
            s_minus_gl_cr: '減：売上税報告にないGL貸方記録',
            s_plus_gl_dr: '加：売上税報告にないGL借方記録',
            s_plus_vat_p: '加：GLにない売上記録',
            s_minus_vat_n: '減：GLにない赤伝記録',
            s_vat_total: '売上税報告合計',
        },
    };
    const _t = (key) => (I18N[_lang()] || I18N.th)[key] || key;

    // M3-2:收入对账失败 error_code → 4 语可读原因 + 引导(取代泛化 "เกิดข้อผิดพลาด")
    function _glvFailMsg(code) {
        const lang = _lang();
        const M = {
            gl_no_revenue_rows: {
                zh: 'GL 中未找到收入科目行。请确认「收入科目前缀」是否正确(收入科目通常以 4 开头),改对后重试。',
                th: 'ไม่พบรายการบัญชีรายได้ใน GL · ตรวจสอบ «คำนำหน้าบัญชีรายได้» (รายได้มักขึ้นต้นด้วย 4) แล้วลองใหม่',
                en: 'No revenue-account rows found in the GL. Check the “revenue account prefix” (revenue usually starts with 4) and retry.',
                ja: 'GL に収益科目の行が見つかりません。「収益科目プレフィックス」(通常 4 で始まる)を確認して再試行してください。',
            },
            gl_parse_failed: {
                zh: 'GL 文件解析失败。请确认文件含日期/科目/借贷列,或换清晰的 Excel/CSV 重传。',
                th: 'อ่านไฟล์ GL ไม่สำเร็จ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต-เครดิต หรืออัปโหลด Excel/CSV ที่ชัดเจน',
                en: 'Failed to parse the GL file. Ensure it has date/account/debit-credit columns, or re-upload a clean Excel/CSV.',
                ja: 'GL ファイルの解析に失敗しました。日付/科目/借方貸方列を確認するか、Excel/CSV を再アップロードしてください。',
            },
            vat_no_rows: {
                zh: '销项税报告里没有可对账的数据行。请确认上传了正确的销项税报告。',
                th: 'ไม่พบแถวข้อมูลในรายงานภาษีขาย · ตรวจสอบว่าอัปโหลดรายงานที่ถูกต้อง',
                en: 'No rows found in the sales-VAT report. Please check you uploaded the correct report.',
                ja: '売上VATレポートに行が見つかりません。正しいレポートをアップロードしたか確認してください。',
            },
            vat_parse_failed: {
                zh: '销项税报告解析失败。请换更清晰的版本,或转成 Excel/PDF 重传。',
                th: 'อ่านรายงานภาษีขายไม่สำเร็จ · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น Excel/PDF',
                en: 'Failed to parse the sales-VAT report. Try a clearer version, or convert to Excel/PDF.',
                ja: '売上VATレポートの解析に失敗しました。より鮮明な版か、Excel/PDF に変換してください。',
            },
        };
        const m = M[code];
        return m ? m[lang] || m.th || m.en : _t('error') || 'Error';
    }

    const _fmt = (n) => {
        if (n === null || n === undefined || isNaN(n)) return '';
        return Number(n).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };

    // ── 文件选择 + 拖拽 ─────────────────────────────────────────────
    // v118.35.0.3 · 销项税报告核查改多文件 · STATE.vatFile / STATE.glFile 现在是 File[]
    function _bindUpload(cardId, inputId, nameId, target) {
        const card = $(cardId);
        const input = $(inputId);
        const name = $(nameId);
        if (!card || !input || !name) return;

        const addFiles = (files) => {
            if (!files || !files.length) return;
            const arr = Array.isArray(STATE[target]) ? STATE[target].slice() : [];
            const seen = new Set(arr.map((f) => f.name + '|' + f.size));
            for (const f of files) {
                if (!f) continue;
                const k = f.name + '|' + f.size;
                if (!seen.has(k)) {
                    arr.push(f);
                    seen.add(k);
                }
            }
            STATE[target] = arr;
            _renderCardSummary(name, arr);
            _updateRunButton();
            _updateStatus();
            // 同步 panel(若已展开)
            if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
                window._reconCollapse.renderGlvPreview();
            }
        };

        card.addEventListener('click', () => input.click());
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                input.click();
            }
        });
        input.addEventListener('change', () => {
            addFiles(Array.from(input.files || []));
            // 清空原生 input,允许重复选同名文件 · 同时避免 panel 仍从 input.files 取
            input.value = '';
        });

        // 拖拽
        card.addEventListener('dragover', (e) => {
            e.preventDefault();
            card.classList.add('drag-over');
        });
        card.addEventListener('dragleave', () => card.classList.remove('drag-over'));
        card.addEventListener('drop', (e) => {
            e.preventDefault();
            card.classList.remove('drag-over');
            const files =
                e.dataTransfer && e.dataTransfer.files ? Array.from(e.dataTransfer.files) : [];
            addFiles(files);
        });
    }

    function _renderCardSummary(nameEl, arr) {
        if (!nameEl) return;
        if (!arr || arr.length === 0) {
            nameEl.textContent = '';
            return;
        }
        const totalKB = arr.reduce((s, f) => s + Math.round(f.size / 1024), 0);
        if (arr.length === 1) {
            nameEl.textContent = arr[0].name + '  (' + totalKB + ' KB)';
        } else {
            const tpl = (window.t && window.t('glv-files-count')) || '{n} 个文件';
            nameEl.textContent = tpl.replace('{n}', arr.length) + '  (' + totalKB + ' KB)';
        }
    }

    function _glvFiles(target) {
        const v = STATE[target];
        return Array.isArray(v) ? v : v ? [v] : [];
    }

    function _updateRunButton() {
        const btn = $('btn-glv-run');
        if (!btn) return;
        const has = _glvFiles('glFile').length > 0 && _glvFiles('vatFile').length > 0;
        btn.disabled = !has || STATE.running;
    }

    function _updateStatus() {
        const status = $('glv-status');
        if (!status) return;
        if (STATE.running) return; // 跑中不覆盖
        const vN = _glvFiles('vatFile').length;
        const gN = _glvFiles('glFile').length;
        if (vN === 0 && gN === 0) {
            status.className = 'vex-action-info muted';
            status.innerHTML = '<span>' + _t('hint_need_both') + '</span>';
        } else if (vN > 0 && gN > 0) {
            status.className = 'vex-action-info ok';
            status.innerHTML = '<span>' + _t('hint_ready') + '</span>';
        } else {
            status.className = 'vex-action-info muted';
            status.innerHTML = '<span>' + _t('hint_need_one_more') + '</span>';
        }
    }

    // v118.32.5.5.25 · 删文件(X 按钮 / 全清按钮)· 真清 STATE + UI + 刷 panel
    // v118.35.0.3 · 支持多文件 · idx=null 时整列清空 · idx=N 时只删第 N 个
    function _removeFile(kind, idx) {
        const target = kind === 'vat' ? 'vatFile' : 'glFile';
        const inputId = kind === 'vat' ? 'glv-vat-input' : 'glv-gl-input';
        const nameId = kind === 'vat' ? 'glv-vat-name' : 'glv-gl-name';
        const arr = _glvFiles(target);
        if (idx == null) {
            STATE[target] = [];
        } else {
            STATE[target] = arr.filter((_, i) => i !== idx);
        }
        const inp = $(inputId);
        if (inp) inp.value = '';
        _renderCardSummary($(nameId), _glvFiles(target));
        _updateRunButton();
        _updateStatus();
        if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
            window._reconCollapse.renderGlvPreview();
        }
    }
    window._glvRemoveFile = _removeFile;

    function _reset() {
        STATE.glFile = [];
        STATE.vatFile = [];
        STATE.currentTaskId = null;
        STATE.lastDetail = [];
        STATE.lastSummary = null;
        const vi = $('glv-vat-input');
        if (vi) vi.value = '';
        const gi = $('glv-gl-input');
        if (gi) gi.value = '';
        const vn = $('glv-vat-name');
        if (vn) vn.textContent = '';
        const gn = $('glv-gl-name');
        if (gn) gn.textContent = '';
        const rs = $('glv-result');
        if (rs) rs.style.display = 'none';
        const kpi = $('glv-kpi-strip');
        if (kpi) kpi.style.display = 'none';
        _updateRunButton();
        _updateStatus();
        if (window._glvClearPreviewSearch) window._glvClearPreviewSearch();
        if (window._reconCollapse && window._reconCollapse.renderGlvPreview) {
            window._reconCollapse.renderGlvPreview();
        }
    }

    // ── 渲染 ────────────────────────────────────────────────────────
    function _renderTable(detail) {
        const tbody = $('glv-tbody');
        if (!tbody) return;
        _setDetailCount(detail.length);
        tbody.innerHTML = '';
        const nf = _t('not_found');
        const frag = document.createDocumentFragment();

        detail.forEach((r) => {
            const tr = document.createElement('tr');

            const td = (txt, cls) => {
                const c = document.createElement('td');
                if (cls) c.className = cls;
                c.textContent = txt;
                return c;
            };

            const noGl = r.gl_amount === null || r.gl_amount === undefined;
            const diff = r.diff;
            let diffCls = 'glv-num';
            let glCls = 'glv-num';
            if (noGl) {
                glCls += ' glv-cell-missing';
                diffCls += ' glv-cell-missing';
            } else if (Math.abs(diff || 0) < 0.005) diffCls += ' glv-cell-ok';
            else diffCls += ' glv-cell-diff';

            tr.appendChild(td(r.doc_no || '', 'glv-doc'));
            tr.appendChild(td(r.date || '', ''));
            tr.appendChild(td(r.customer_name || '', ''));
            tr.appendChild(td(_fmt(r.vat_amount), 'glv-num'));
            tr.appendChild(td(noGl ? nf : _fmt(r.gl_amount), glCls));
            tr.appendChild(td(noGl ? nf : _fmt(r.diff), diffCls));
            tr.appendChild(td(r.account_codes || '', 'glv-doc'));
            frag.appendChild(tr);
        });
        tbody.appendChild(frag);
    }

    function _renderSummary(summary) {
        const tbody = $('glv-summary-table') && $('glv-summary-table').querySelector('tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        const rows = [
            {
                label: _t('s_gl_total'),
                amount: summary.gl_total,
                emph: true,
                items: [],
                negate: false,
            },
            {
                label: _t('s_minus_gl_cr'),
                amount: -(summary.gl_only_credit || 0),
                emph: false,
                items: summary.gl_only_credit_items || [],
                negate: true,
            },
            {
                label: _t('s_plus_gl_dr'),
                amount: summary.gl_only_debit || 0,
                emph: false,
                items: summary.gl_only_debit_items || [],
                negate: false,
            },
            {
                label: _t('s_plus_vat_p'),
                amount: summary.vat_only_positive || 0,
                emph: false,
                items: summary.vat_only_positive_items || [],
                negate: false,
            },
            {
                label: _t('s_minus_vat_n'),
                amount: summary.vat_only_negative || 0,
                emph: false,
                items: summary.vat_only_negative_items || [],
                negate: false,
            },
            {
                label: _t('s_vat_total'),
                amount: summary.vat_total,
                emph: true,
                items: [],
                negate: false,
            },
        ];
        rows.forEach(({ label, amount, emph, items, negate }) => {
            const tr = document.createElement('tr');
            tr.className = emph ? 'glv-summary-total' : 'glv-summary-sect';
            const td1 = document.createElement('td');
            const td2 = document.createElement('td');
            td1.textContent = label;
            td2.textContent = emph ? _fmt(amount) : '';
            tr.appendChild(td1);
            tr.appendChild(td2);
            tbody.appendChild(tr);
            (items || []).forEach((it) => {
                const itr = document.createElement('tr');
                itr.className = 'glv-summary-item';
                const itd1 = document.createElement('td');
                const itd2 = document.createElement('td');
                const parts = [it.doc_no, it.date, it.name].filter(Boolean);
                itd1.textContent = '· ' + parts.join('  ·  ');
                const dispAmt = negate ? -(it.amount || 0) : it.amount || 0;
                itd2.textContent = _fmt(dispAmt);
                itr.appendChild(itd1);
                itr.appendChild(itd2);
                tbody.appendChild(itr);
            });
        });
    }

    function _renderKpi(stats) {
        if ($('glv-kpi-matched'))
            $('glv-kpi-matched').textContent = stats && stats.matched != null ? stats.matched : '—';
        if ($('glv-kpi-diff'))
            $('glv-kpi-diff').textContent = stats && stats.diff != null ? stats.diff : '—';
        if ($('glv-kpi-unmatched'))
            $('glv-kpi-unmatched').textContent =
                stats && stats.unmatched != null ? stats.unmatched : '—';
    }

    // ── 历史任务列表 ─────────────────────────────────────────────────
    function _fmtTime(s) {
        if (!s) return '';
        try {
            const d = new Date(s);
            if (isNaN(d.getTime())) return s;
            const pad = (n) => String(n).padStart(2, '0');
            return (
                d.getFullYear() +
                '-' +
                pad(d.getMonth() + 1) +
                '-' +
                pad(d.getDate()) +
                ' ' +
                pad(d.getHours()) +
                ':' +
                pad(d.getMinutes())
            );
        } catch (_) {
            return s;
        }
    }

    const GLV_PAGE_SIZE = 10;
    var _glvAllTasks = [];
    var _glvPage = 1;

    function _applyGlvSearch() {
        _glvPage = 1;
        _renderGlvPage();
        var q = (($('glv-hist-search') || {}).value || '').trim().toLowerCase();
        if (!q) return;
        var tbody = $('glv-history-tbody');
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach(function (tr) {
            if (!tr.dataset.taskId) return;
            tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
        });
    }

    function _renderGlvPage() {
        const tableEl = $('glv-history-table-wrap');
        const emptyEl = $('glv-history-empty');
        const tbody = $('glv-history-tbody');
        const pager = $('glv-history-pager');
        const info = $('glv-history-pager-info');
        const prev = $('glv-history-prev');
        const next = $('glv-history-next');
        if (!tbody) return;
        tbody.innerHTML = '';
        if (!_glvAllTasks.length) {
            if (tableEl) tableEl.style.display = 'none';
            if (emptyEl) emptyEl.style.display = '';
            if (pager) pager.style.display = 'none';
            return;
        }
        if (tableEl) tableEl.style.display = '';
        if (emptyEl) emptyEl.style.display = 'none';
        const totalPages = Math.ceil(_glvAllTasks.length / GLV_PAGE_SIZE);
        if (_glvPage > totalPages) _glvPage = totalPages;
        const start = (_glvPage - 1) * GLV_PAGE_SIZE;
        const pageTasks = _glvAllTasks.slice(start, start + GLV_PAGE_SIZE);
        if (pager) {
            pager.style.display = _glvAllTasks.length > GLV_PAGE_SIZE ? '' : 'none';
            if (info) info.textContent = _glvPage + ' / ' + totalPages;
            if (prev) prev.disabled = _glvPage <= 1;
            if (next) next.disabled = _glvPage >= totalPages;
        }
        const tasks = pageTasks;
        tasks.forEach((t) => {
            const tr = document.createElement('tr');
            tr.dataset.taskId = t.id; // v118.32.5.5.20 · 批量删多选用
            const cellTime = document.createElement('td');
            cellTime.textContent = _fmtTime(t.created_at);
            const cellFiles = document.createElement('td');
            cellFiles.className = 'glv-history-file';
            cellFiles.title = (t.vat_filename || '') + ' + ' + (t.gl_filename || '');
            cellFiles.textContent = (t.vat_filename || '?') + ' + ' + (t.gl_filename || '?');
            const cellRows = document.createElement('td');
            cellRows.className = 'glv-num';
            cellRows.textContent = (t.vat_row_count || 0) + ' / ' + (t.gl_row_count || 0);
            const cellMatched = document.createElement('td');
            cellMatched.className = 'glv-num';
            cellMatched.textContent = t.matched_count || 0;
            const cellDiff = document.createElement('td');
            cellDiff.className = 'glv-num';
            cellDiff.textContent = t.diff_count || 0;
            const cellMiss = document.createElement('td');
            cellMiss.className = 'glv-num';
            cellMiss.textContent = t.unmatched_count || 0;
            const cellAct = document.createElement('td');
            cellAct.className = 'glv-history-actions';
            // 三个图标按钮（hover 显示 tooltip · 同销项税对账风格）
            const mkBtn = (svg, title, cls, onClick) => {
                const b = document.createElement('button');
                b.type = 'button';
                if (cls) b.className = cls;
                b.title = title;
                b.setAttribute('aria-label', title);
                b.innerHTML = svg;
                b.onclick = onClick;
                return b;
            };
            const SVG_LOAD =
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M2 8a6 6 0 1 0 12 0A6 6 0 0 0 2 8z"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>';
            const SVG_DL =
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>';
            const SVG_DEL =
                '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';
            cellAct.appendChild(mkBtn(SVG_LOAD, _t('hist_load'), '', () => _loadTask(t.id)));
            cellAct.appendChild(mkBtn(SVG_DL, _t('hist_export'), '', () => _exportTask(t.id)));
            cellAct.appendChild(
                mkBtn(SVG_DEL, _t('hist_delete'), 'glv-del', () => _deleteTask(t.id))
            );
            [cellTime, cellFiles, cellRows, cellMatched, cellDiff, cellMiss, cellAct].forEach((c) =>
                tr.appendChild(c)
            );
            tbody.appendChild(tr);
        });
    }

    function _glvInitPager() {
        var prev = $('glv-history-prev');
        var next = $('glv-history-next');
        if (prev && !prev._glvBound) {
            prev._glvBound = true;
            prev.addEventListener('click', function () {
                if (_glvPage > 1) {
                    _glvPage--;
                    _renderGlvPage();
                }
            });
        }
        if (next && !next._glvBound) {
            next._glvBound = true;
            next.addEventListener('click', function () {
                var totalPages = Math.ceil(_glvAllTasks.length / GLV_PAGE_SIZE);
                if (_glvPage < totalPages) {
                    _glvPage++;
                    _renderGlvPage();
                }
            });
        }
    }

    async function _loadHistory() {
        try {
            const res = await fetch('/api/recon/gl-vat/tasks', { headers: _authH() });
            const data = await res.json();
            _glvAllTasks = (data && data.tasks) || [];
            _glvPage = 1;
            _renderGlvPage();
            _glvInitPager();
        } catch (e) {
            console.error('[gl-vat] history load failed:', e);
        }
    }

    async function _loadTask(taskId) {
        try {
            const res = await fetch('/api/recon/gl-vat/' + taskId, { headers: _authH() });
            const data = await res.json();
            if (!data || !data.ok) throw new Error('load_failed');
            STATE.currentTaskId = taskId;
            STATE.lastDetail = data.detail || [];
            STATE.lastSummary = data.summary || {};
            _renderKpi(data.stats || {});
            _renderTable(STATE.lastDetail);
            _renderSummary(STATE.lastSummary);
            const rs = $('glv-result');
            if (rs) rs.style.display = '';
            _expandResults();
            window.scrollTo({ top: rs ? rs.offsetTop - 80 : 0, behavior: 'smooth' });
        } catch (e) {
            console.error('[gl-vat] load task failed:', e);
            alert(_t('error') + ': ' + (e.message || e));
        }
    }

    async function _exportTask(taskId) {
        try {
            const url =
                '/api/recon/gl-vat/' + taskId + '/export?lang=' + encodeURIComponent(_lang());
            const res = await fetch(url, { headers: _authH() });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'GL_VAT_recon_' + taskId + '.xlsx';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                URL.revokeObjectURL(a.href);
                a.remove();
            }, 200);
        } catch (e) {
            console.error('[gl-vat] exportTask failed:', e);
            if (typeof showToast === 'function')
                showToast(_t('error') + ': ' + (e.message || e), 'error');
        }
    }

    async function _deleteTask(taskId) {
        // v118.32.5.4 · 用产品自带 showConfirm 替换原生 confirm()
        let ok;
        if (typeof window.showConfirm === 'function') {
            ok = await window.showConfirm(_t('confirm_delete'), { danger: true });
        } else {
            ok = confirm(_t('confirm_delete')); // 兜底
        }
        if (!ok) return;
        try {
            const res = await fetch('/api/recon/gl-vat/' + taskId, {
                method: 'DELETE',
                headers: _authH(),
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            _loadHistory();
        } catch (e) {
            console.error('[gl-vat] delete failed:', e);
            if (typeof showToast === 'function')
                showToast(_t('error') + ': ' + (e.message || e), 'error');
        }
    }

    // ── 跑对账 ──────────────────────────────────────────────────────
    async function _run() {
        if (!STATE.glFile || !STATE.vatFile) {
            if (typeof showToast === 'function') showToast(_t('need_files'), 'warn');
            return;
        }
        STATE.running = true;
        _updateRunButton();
        const status = $('glv-status');
        const progress = $('glv-progress');
        const progressSub = $('glv-progress-sub');
        if (status) {
            status.className = 'vex-action-info muted';
            status.style.color = '';
            status.innerHTML = '<span>' + _t('running') + '</span>';
        }
        if (progress) progress.style.display = '';
        if (progressSub)
            progressSub.textContent =
                (STATE.vatFile.name || 'VAT') + ' + ' + (STATE.glFile.name || 'GL');

        const fd = new FormData();
        // v118.35.0.3 · multi-file · 同 key 多次 append → 后端 List[UploadFile]
        const _vats = _glvFiles('vatFile');
        const _gls = _glvFiles('glFile');
        for (const f of _vats) fd.append('vat_files', f, f.name);
        for (const f of _gls) fd.append('gl_files', f, f.name);
        const prefix = (($('glv-prefix') && $('glv-prefix').value) || '4').trim() || '4';
        fd.append('revenue_prefix', prefix);
        fd.append('lang', _lang()); // v118.32.5 · 后端按 lang 返回错误消息

        try {
            // BUG-FIX-RECON-ASYNC #16 · 改异步:submit 秒回 job_id → 轮询 → 用 result_id 取结果
            const submitRes = await fetch('/api/recon/gl-vat/submit', {
                method: 'POST',
                headers: _authH(),
                body: fd,
            });
            // 兜底:网关非 JSON 错误页不再抛 "Unexpected token '<'"
            let sub = null;
            try {
                sub = await submitRes.json();
            } catch (_) {
                sub = null;
            }
            if (!submitRes.ok || !sub || !sub.ok || !sub.job_id) {
                throw new Error(
                    (sub && sub.detail) || (sub && sub.error) || 'HTTP ' + submitRes.status
                );
            }
            // 轮询 · 转圈旁实时显示「共 X/Y 个文件」
            const _glvSub = $('glv-progress-sub');
            const job = await window._reconPollJob(sub.job_id, _token(), {
                onProgress: (p) => {
                    if (_glvSub) _glvSub.textContent = window._reconProgressText(p, _lang());
                },
            });
            if (!job || job.status !== 'done' || !job.result_id) {
                // M3-2 修(2026-05-25):失败时用后端 error_code 映射成可读文案 · 不再泛化 "เกิดข้อผิดพลาด"
                if (job && job.status === 'failed' && job.error_code) {
                    throw new Error(_glvFailMsg(job.error_code));
                }
                throw new Error(_t('error') || 'Error');
            }
            // 用 result_id 调现有结果接口(GET 形状与 run 一致)
            const res = await fetch('/api/recon/gl-vat/' + encodeURIComponent(job.result_id), {
                headers: _authH(),
            });
            let data = null;
            try {
                data = await res.json();
            } catch (_) {
                data = null;
            }
            if (!res.ok || !data || !data.ok) {
                throw new Error(
                    (data && data.detail) || (data && data.error) || 'HTTP ' + res.status
                );
            }
            STATE.currentTaskId = data.task_id;
            STATE.lastDetail = data.detail || [];
            STATE.lastSummary = data.summary || {};
            _renderKpi(data.stats || {});
            _renderTable(STATE.lastDetail);
            _renderSummary(STATE.lastSummary);
            const rs = $('glv-result');
            if (rs) rs.style.display = '';
            _expandResults();
            if (status) {
                status.className = 'vex-action-info ok';
                status.style.color = '';
                status.innerHTML =
                    '<span>' +
                    _t('done') +
                    ' · GL ' +
                    (data.gl_row_count || 0) +
                    ' · VAT ' +
                    (data.vat_row_count || 0) +
                    '</span>';
            }
            // M3-1 修(2026-05-25):成功后刷新「近期对账任务」· 此前只渲染结果区 · 历史表不更新
            _loadHistory();
        } catch (e) {
            console.error('[gl-vat] run failed:', e);
            if (status) {
                status.className = 'vex-action-info';
                status.style.color = '#ef4444';
                status.innerHTML = '<span>' + _t('error') + ': ' + (e.message || e) + '</span>';
            }
        } finally {
            STATE.running = false;
            if (progress) progress.style.display = 'none';
            _updateRunButton();
        }
    }

    // ── 导出 Excel ──────────────────────────────────────────────────
    async function _export() {
        if (!STATE.currentTaskId) return;
        try {
            const url =
                '/api/recon/gl-vat/' +
                STATE.currentTaskId +
                '/export?lang=' +
                encodeURIComponent(_lang());
            const res = await fetch(url, { headers: _authH() });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'GL_VAT_recon_' + STATE.currentTaskId + '.xlsx';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                URL.revokeObjectURL(a.href);
                a.remove();
            }, 200);
        } catch (e) {
            console.error('[gl-vat] export failed:', e);
            if (typeof showToast === 'function')
                showToast(_t('error') + ': ' + (e.message || e), 'error');
        }
    }

    // ── 语言切换时重渲（不依赖离开/返回 tab） ───────────────────────
    function _onLangChange() {
        // 1. 状态条
        if (!STATE.running) _updateStatus();
        // 2. 历史表（按钮 title / 空状态文案都靠 _t() 动态生成）
        _loadHistory();
        // 3. 当前明细表（表头由 data-i18n 处理，但单元格里 "未找到" 等动态文案要重渲）
        if (STATE.lastDetail && STATE.lastDetail.length) {
            _renderTable(STATE.lastDetail);
        }
        if (STATE.lastSummary) {
            _renderSummary(STATE.lastSummary);
        }
    }

    // ── 可折叠分区 ────────────────────────────────────────────────
    function _expandResults() {
        var kpi = $('glv-kpi-strip');
        if (kpi) kpi.style.display = '';
        var ss = $('glv-section-summary');
        if (ss) ss.setAttribute('data-collapsed', 'false');
        var sd = $('glv-section-detail');
        if (sd) sd.setAttribute('data-collapsed', 'false');
    }

    function _bindSectionToggle() {
        document.querySelectorAll('.glv-section-head[data-toggle]').forEach((head) => {
            const targetId = head.getAttribute('data-toggle');
            const target = document.getElementById(targetId);
            if (!target) return;
            const toggle = (e) => {
                // 不要让头部里的按钮（导出）触发折叠
                if (
                    e.target &&
                    e.target.closest('button') !== null &&
                    !e.target.classList.contains('glv-section-head')
                ) {
                    return;
                }
                const collapsed = target.getAttribute('data-collapsed') === 'true';
                target.setAttribute('data-collapsed', collapsed ? 'false' : 'true');
            };
            head.addEventListener('click', toggle);
            head.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggle(e);
                }
            });
        });
    }

    function _setDetailCount(n) {
        const el = $('glv-detail-count');
        if (el) el.textContent = n != null ? String(n) : '';
    }

    // ── 初始化（首次进入 tab 时调用） ────────────────────────────────
    function ensureInit() {
        if (STATE.inited) {
            _loadHistory(); // 二次进入也刷新历史
            return;
        }
        STATE.inited = true;
        _bindUpload('glv-drop-gl', 'glv-gl-input', 'glv-gl-name', 'glFile');
        _bindUpload('glv-drop-vat', 'glv-vat-input', 'glv-vat-name', 'vatFile');
        const btnRun = $('btn-glv-run');
        if (btnRun) btnRun.addEventListener('click', _run);
        const btnExp = $('btn-glv-export');
        if (btnExp) btnExp.addEventListener('click', _export);
        const btnReset = $('btn-glv-reset');
        if (btnReset) btnReset.addEventListener('click', _reset);
        const glvSearchEl = $('glv-hist-search');
        if (glvSearchEl) glvSearchEl.addEventListener('input', _applyGlvSearch);
        _bindSectionToggle();
        _renderKpi(null); // 初始 KPI 显示 '—'
        _updateStatus();
        window._loadGlvHistory = _loadHistory;
        _loadHistory();
        // v118.32.5.1 · 订阅 i18n 切换总线 · 切语言实时刷新动态文案
        if (typeof window.subscribeI18n === 'function') {
            window.subscribeI18n('gl-vat-recon', _onLangChange);
        }
    }

    window.GlVatRecon = { ensureInit };
    // v118.35.0.3 · 让 preview panel(在另一个 IIFE)能拿到多文件 STATE
    window._glvPreviewFiles = function (kind) {
        return _glvFiles(kind === 'vat' ? 'vatFile' : 'glFile');
    };
})();
