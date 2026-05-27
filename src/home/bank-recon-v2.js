// ============================================================
// REFACTOR-C1 (2026-05-27) · 银行对账 v2(Statement vs GL)bank-recon-v2 从 home.js 抽出为 ES module
//
// 来源:home.js L6832-8115 · verbatim 0 改逻辑(仅 prettier 重排)。
// 依赖 window._reconPollJob(recon-job-poll module · 运行期经 window. 调用);暴露
// window._loadBankReconV2Panel / _bankReconV2Init / _brv2LoadHistory(被 recon-center/recon-batch 经 window. 运行期调用)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================

/* global showConfirm, _humanizeBackendError */

/* ============================================================
 * v118.33.6 · Bank Reconciliation v2 (Statement vs GL)
 * Two upload zones · 3-layer matching · Excel export
 * ============================================================ */
(function () {
    'use strict';

    // ── State ─────────────────────────────────────────────────────────
    let _initialized = false; // guard: 防 init() 重复绑事件
    let _stmtFiles = []; // File objects for bank statement
    let _glFiles = []; // File objects for GL
    let _currentTask = null; // Last run result {task_id, detail, summary, stats}
    let _currentFilter = 'all';
    let _allRows = []; // parsed detail rows (flat)
    let _brv2Search = { stmt: '', gl: '' };
    let _cachedHistoryTasks = [];

    // ── DOM helpers ───────────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);
    function fmtNum(v) {
        if (v === null || v === undefined) return '—';
        const n = Number(v);
        if (isNaN(n)) return '—';
        return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function fmtDate(s) {
        if (!s) return '—';
        return String(s).slice(0, 10).split('-').reverse().join('/');
    }
    function esc2(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }
    // BUG-FIX-RECON-GLCSV · 后台整侧解析明确失败(无表格可现场修)→ 按 error_code 给 4 语友好原因 + 引导
    function _brv2FailMsg(code, lang) {
        lang = window._currentLang || lang || 'th';
        const M = {
            stmt_headers_not_found: {
                zh: '认不出银行账单表头 · 请确认文件含日期/金额/余额列,或转成清晰的 Excel/CSV 重传',
                th: 'หาหัวตารางบัญชีธนาคารไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/จำนวนเงิน/ยอดคงเหลือ หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
                en: 'Cannot detect bank statement headers · ensure the file has date/amount/balance columns, or re-upload as a clean Excel/CSV',
                ja: '銀行明細のヘッダーを認識できません · 日付/金額/残高列を確認するか、Excel/CSVに変換して再アップロードしてください',
            },
            gl_headers_not_found: {
                zh: '认不出总账表头 · 请确认文件含日期/科目/借方/贷方列,或转成清晰的 Excel/CSV 重传',
                th: 'หาหัวตาราง GL ไม่เจอ · ตรวจสอบว่ามีคอลัมน์ วันที่/บัญชี/เดบิต/เครดิต หรือแปลงเป็น Excel/CSV แล้วอัปโหลดใหม่',
                en: 'Cannot detect GL headers · ensure the file has date/account/debit/credit columns, or re-upload as a clean Excel/CSV',
                ja: 'GLのヘッダーを認識できません · 日付/科目/借方/貸方列を確認するか、Excel/CSVに変換して再アップロードしてください',
            },
            stmt_no_rows: {
                zh: '文件里没有交易数据 · 请确认上传了正确的银行流水,或换更清晰的版本重传',
                th: 'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง หรือใช้เวอร์ชันที่ชัดเจนกว่า',
                en: 'No transaction rows found · please upload the correct statement, or try a clearer version',
                ja: '取引データが見つかりません · 正しい明細をアップロードするか、より鮮明なファイルでお試しください',
            },
            no_rows: {
                zh: '解析后没有可对账的数据行 · 请确认文件内容完整,或换清晰版本重传',
                th: 'ไม่มีแถวข้อมูลให้กระทบยอดหลังการอ่าน · ตรวจสอบความสมบูรณ์ของไฟล์ หรืออัปโหลดใหม่',
                en: 'No reconcilable rows after parsing · check the file is complete, or re-upload a clearer version',
                ja: '解析後に照合可能な行がありません · ファイルの完全性を確認するか再アップロードしてください',
            },
            file_unreadable: {
                zh: '文件无法读取 · 可能已损坏或被加密 · 请换文件或转 PDF/Excel 重传',
                th: 'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส · ลองไฟล์อื่นหรือแปลงเป็น PDF/Excel',
                en: 'File cannot be read · may be corrupted or encrypted · try another file or convert to PDF/Excel',
                ja: 'ファイルを読み取れません · 破損または暗号化の可能性 · 別ファイルまたはPDF/Excelに変換してください',
            },
            file_not_supported: {
                zh: '不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
                th: 'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
                en: 'File type not supported · please upload PDF / image / Excel / CSV',
                ja: 'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロードしてください',
            },
            ocr_failed: {
                zh: '文件识别失败 · 请尝试更清晰的版本,或转成 PDF / Excel / CSV 重传',
                th: 'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่า หรือแปลงเป็น PDF / Excel / CSV',
                en: 'Could not read the file · try a clearer version, or convert to PDF / Excel / CSV',
                ja: '読み取りに失敗 · より鮮明なファイルか、PDF / Excel / CSV に変換して再試行してください',
            },
        };
        const generic = {
            zh: '解析失败 · 请换更清晰的文件,或转成 Excel / CSV 后重新上传',
            th: 'อ่านไฟล์ไม่สำเร็จ · ลองไฟล์ที่ชัดเจนกว่า หรือแปลงเป็น Excel / CSV แล้วอัปโหลดใหม่',
            en: 'Parsing failed · try a clearer file, or convert to Excel / CSV and re-upload',
            ja: '解析に失敗しました · より鮮明なファイルか、Excel / CSV に変換して再アップロードしてください',
        };
        const m = M[code] || generic;
        return m[lang] || m.th || m.en;
    }

    // ── File rendering（vex-drop-filename + preview panel） ──────────
    function renderFileList(zone) {
        const files = zone === 'stmt' ? _stmtFiles : _glFiles;
        // 更新拖拽区内摘要文字
        const nameEl = $(`brv2-${zone}-name`);
        if (nameEl) {
            if (files.length === 0) {
                nameEl.textContent = '';
            } else {
                const lang = window._currentLang || 'zh';
                const labels = { zh: '个文件', th: ' ไฟล์', en: ' file(s)', ja: ' ファイル' };
                nameEl.textContent = files.length + (labels[lang] || ' 个文件');
            }
        }
        // 若 preview panel 已展开则刷新对应列
        const panel = $('brv2-preview-panel');
        if (panel && panel.style.display !== 'none') {
            _renderBrv2Column(zone);
        }
        _updateTogglePreviewBtn();
    }

    function _updateTogglePreviewBtn() {
        const btn = $('brv2-toggle-preview');
        const panel = $('brv2-preview-panel');
        const hasFiles = _stmtFiles.length + _glFiles.length > 0;
        if (btn) btn.style.display = hasFiles ? '' : 'none';
        if (!hasFiles && panel) {
            panel.style.display = 'none';
            if (btn) btn.classList.remove('open');
        }
    }

    function _renderBrv2PreviewPanel() {
        _renderBrv2Column('stmt');
        _renderBrv2Column('gl');
    }

    function _renderBrv2Column(zone) {
        const colEl = $(zone === 'stmt' ? 'brv2-pp-stmt-col' : 'brv2-pp-gl-col');
        if (!colEl) return;
        const files = zone === 'stmt' ? _stmtFiles : _glFiles;
        const lang = window._currentLang || 'zh';
        const titleMap = {
            stmt: { zh: '① 银行账单', th: '① บัญชีธนาคาร', en: '① Bank Stmt', ja: '① 銀行明細' },
            gl: { zh: '② 总账 GL', th: '② GL รายงาน', en: '② GL Report', ja: '② GL帳簿' },
        };
        const title = (titleMap[zone] || {})[lang] || titleMap[zone].zh;
        const ph = esc2((window.t && window.t('vex-preview-search')) || '搜索文件名...');
        const clearLbl = esc2((window.t && window.t('vex-preview-clear-all')) || '全清');
        const searchVal = _brv2Search[zone] || '';

        colEl.innerHTML =
            '<div class="vex-pp-col-title">' +
            '<span class="vex-pp-col-name">' +
            esc2(title) +
            ' <span class="vex-pp-col-count">' +
            files.length +
            '</span></span>' +
            '</div>' +
            '<div class="vex-pp-search-row">' +
            '<input class="vex-pp-search" id="brv2-pp-search-' +
            zone +
            '" type="text" placeholder="' +
            ph +
            '" value="' +
            esc2(searchVal) +
            '" autocomplete="off">' +
            '<button class="vex-pp-clear-btn" id="brv2-pp-clearall-' +
            zone +
            '" type="button">' +
            clearLbl +
            '</button>' +
            '</div>' +
            '<div class="vex-pp-file-list" id="brv2-pp-' +
            zone +
            '-list"></div>' +
            '<div class="vex-pp-pagination" id="brv2-pp-' +
            zone +
            '-pg"></div>';

        const si = $('brv2-pp-search-' + zone);
        if (si)
            si.addEventListener('input', function (e) {
                _brv2Search[zone] = e.target.value;
                _renderBrv2FileList(zone);
            });
        const ca = $('brv2-pp-clearall-' + zone);
        if (ca)
            ca.addEventListener('click', function () {
                if (zone === 'stmt') _stmtFiles.length = 0;
                else _glFiles.length = 0;
                renderFileList(zone);
                updateRunBtn();
            });
        _renderBrv2FileList(zone);
    }

    function _renderBrv2FileList(zone) {
        const listEl = $('brv2-pp-' + zone + '-list');
        const pgEl = $('brv2-pp-' + zone + '-pg');
        if (!listEl) return;
        const files = zone === 'stmt' ? _stmtFiles : _glFiles;
        const q = (_brv2Search[zone] || '').toLowerCase();
        const filtered = q ? files.filter((f) => f.name.toLowerCase().includes(q)) : files.slice();
        const fileIco =
            '<svg class="vex-pp-fi-ico" viewBox="0 0 14 16" fill="none" stroke="currentColor" stroke-width="1.4" width="12" height="14"><path d="M3 1h6l3 3v11H3V1z"/><path d="M9 1v3h3"/></svg>';
        const delIco =
            '<svg viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.6" width="11" height="11"><path d="M2 4h10M5 4V2h4v2M5.5 7v4M8.5 7v4M3 4l1 8h6l1-8"/></svg>';
        listEl.innerHTML = filtered
            .map(
                (f, i) =>
                    '<div class="vex-pp-file-row">' +
                    fileIco +
                    '<span class="vex-pp-fi-name" title="' +
                    esc2(f.name) +
                    '">' +
                    esc2(f.name) +
                    '</span>' +
                    '<span class="vex-pp-fi-size">' +
                    _brv2FmtSize(f.size) +
                    '</span>' +
                    '<button class="vex-pp-fi-del" type="button" data-zone="' +
                    zone +
                    '" data-idx="' +
                    files.indexOf(f) +
                    '" aria-label="remove">' +
                    delIco +
                    '</button>' +
                    '</div>'
            )
            .join('');
        listEl.querySelectorAll('.vex-pp-fi-del').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const idx = parseInt(btn.dataset.idx, 10);
                if (btn.dataset.zone === 'stmt') _stmtFiles.splice(idx, 1);
                else _glFiles.splice(idx, 1);
                renderFileList(btn.dataset.zone);
                updateRunBtn();
            });
        });
        if (pgEl) {
            const tpl = (window.t && window.t('vex-preview-count')) || '显示 {n} / 共 {m}';
            pgEl.textContent = tpl.replace('{n}', filtered.length).replace('{m}', files.length);
        }
    }

    function _brv2FmtSize(bytes) {
        if (!bytes) return '';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // P0.1 BUG-B-T1 v118.35.0.37 · 3 anchor 预填 cache 跨会话 · localStorage 单 key 兜底
    //   不分 bank · 1 个事务所 1-2 个银行 · 简化(后续 Phase 1 P1.4 加 confidence 时再 per-bank scope)
    var _BRV2_ANCHOR_KEY = 'pearnly.brv2.lastAnchorOcr';
    function _brv2SaveLastAnchorOcr(summary) {
        try {
            var ocr = summary && summary._anchor_ocr;
            if (!ocr || typeof ocr !== 'object') return;
            var payload = {
                stmt_opening: Number.isFinite(+ocr.stmt_opening) ? +ocr.stmt_opening : null,
                gl_opening: Number.isFinite(+ocr.gl_opening) ? +ocr.gl_opening : null,
                gl_closing: Number.isFinite(+ocr.gl_closing) ? +ocr.gl_closing : null,
                stmt_closing: Number.isFinite(+ocr.stmt_closing) ? +ocr.stmt_closing : null, // BUG-FIX-T3 v118.35.0.44
                ts: Date.now(),
            };
            localStorage.setItem(_BRV2_ANCHOR_KEY, JSON.stringify(payload));
        } catch (_) {
            /* 私模 localStorage / quota / JSON 异常 · 静默(下次跑还能再存)*/
        }
    }
    function _brv2ReadLastAnchorOcr() {
        try {
            var raw = localStorage.getItem(_BRV2_ANCHOR_KEY);
            if (!raw) return null;
            var p = JSON.parse(raw);
            if (!p || typeof p !== 'object') return null;
            return p;
        } catch (_) {
            return null;
        }
    }
    function _brv2RestoreAnchorPrefill() {
        var p = _brv2ReadLastAnchorOcr();
        if (!p) return;
        var map = {
            'brv2-anchor-stmt-opening': p.stmt_opening,
            'brv2-anchor-gl-opening': p.gl_opening,
            'brv2-anchor-gl-closing': p.gl_closing,
            'brv2-anchor-stmt-closing': p.stmt_closing, // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor 预填
        };
        var prefilledCount = 0;
        Object.keys(map).forEach(function (id) {
            var el = document.getElementById(id);
            if (!el) return;
            // 用户已经手填了任何值 → 不覆盖
            if (el.value !== '') return;
            var v = map[id];
            if (!Number.isFinite(v)) return;
            el.value = v.toFixed(2);
            var cell = el.closest && el.closest('.brv2-anchor-cell');
            if (cell) cell.classList.add('is-prefilled');
            prefilledCount += 1;
        });
        // 触发期初差额提示行(如果 stmt + gl opening 都预填了)
        var eq = document.getElementById('brv2-anchor-eq');
        var eqVal = document.getElementById('brv2-anchor-eq-val');
        if (eq && eqVal && Number.isFinite(p.stmt_opening) && Number.isFinite(p.gl_opening)) {
            var diff = p.stmt_opening - p.gl_opening;
            eqVal.textContent = diff.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
            eq.style.display = '';
        }
        // BUG-FIX-T4 v118.35.0.45 · 至少 1 个 cell 被预填 → 显示橙色 banner 提示来源
        if (prefilledCount > 0) {
            var banner = document.getElementById('brv2-anchor-prefill-banner');
            if (banner) banner.classList.add('show');
        }
    }
    // BUG-FIX-T4 v118.35.0.45 · 用户改了任意一个 anchor 后 · 如果全部 cell 都没 is-prefilled · 隐藏 banner
    function _brv2UpdatePrefillBannerVisibility() {
        var banner = document.getElementById('brv2-anchor-prefill-banner');
        if (!banner) return;
        var anyPrefilled = false;
        [
            'brv2-anchor-gl-closing',
            'brv2-anchor-stmt-closing',
            'brv2-anchor-stmt-opening',
            'brv2-anchor-gl-opening',
        ].forEach(function (id) {
            var el = document.getElementById(id);
            if (!el) return;
            var cell = el.closest && el.closest('.brv2-anchor-cell');
            if (cell && cell.classList.contains('is-prefilled')) anyPrefilled = true;
        });
        banner.classList.toggle('show', anyPrefilled);
    }

    // P0.3 BUG-B-T3 v118.35.0.39 · 历史详情 / 跑完结果 显示『手动录入 anchor 对照表』
    //   读 summary._anchor_overrides · 列每个被改 anchor 的 OCR 值 vs 用户值 vs 差额
    //   动态创建 DOM 插入到 brv2-summary-collapse 之后 · 不动 home.html
    var _BRV2_ANCHOR_LABEL_KEYS = [
        ['stmt_opening', 'brv2-anchor-stmt-opening'],
        ['gl_opening', 'brv2-anchor-gl-opening'],
        ['gl_closing', 'brv2-anchor-gl-closing'],
        ['stmt_closing', 'brv2-anchor-stmt-closing'], // BUG-FIX-T3 v118.35.0.44 · 加 4th anchor
    ];
    function _brv2T(key, fallback) {
        return (window.t && window.t(key)) || fallback;
    }
    function _brv2EscHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    function _brv2FmtNum(v) {
        if (!Number.isFinite(+v)) return '—';
        return (+v).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
    function _brv2RenderAnchorAudit(summary) {
        var host = document.getElementById('brv2-summary-collapse');
        if (!host || !host.parentNode) return;
        var panel = document.getElementById('brv2-anchor-audit');
        var overrides = summary && summary._anchor_overrides;
        // 没 override → 移除既有 panel(切换不同 task 时清理)
        if (!overrides || typeof overrides !== 'object' || Object.keys(overrides).length === 0) {
            if (panel && panel.parentNode) panel.parentNode.removeChild(panel);
            return;
        }
        // 没 panel → 动态创建 · 插到 summary collapse 之后
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'brv2-anchor-audit';
            panel.style.cssText =
                'margin-top:14px;background:#fff7ed;border:1px solid #fed7aa;' +
                'border-radius:8px;padding:14px 16px;';
            host.parentNode.insertBefore(panel, host.nextSibling);
        }
        // 渲染内容
        var rows = _BRV2_ANCHOR_LABEL_KEYS
            .map(function (pair) {
                var ov = overrides[pair[0]];
                if (!ov) return '';
                var ocr = +ov.ocr || 0;
                var usr = +ov.user || 0;
                var diff = usr - ocr;
                var sign = diff > 0 ? '+' : diff < 0 ? '' : '';
                var diffColor =
                    Math.abs(diff) < 0.005 ? '#6b7280' : diff > 0 ? '#16a34a' : '#dc2626';
                return (
                    '<tr>' +
                    '<td style="padding:6px 10px;color:#111827;font-size:13px">' +
                    _brv2EscHtml(_brv2T(pair[1], pair[0])) +
                    '</td>' +
                    '<td style="padding:6px 10px;color:#6b7280;font-size:13px;text-align:right;' +
                    'font-variant-numeric:tabular-nums">' +
                    _brv2EscHtml(_brv2FmtNum(ocr)) +
                    '</td>' +
                    '<td style="padding:6px 10px;background:#fef08a;color:#92400e;font-weight:600;' +
                    'font-size:13px;text-align:right;font-variant-numeric:tabular-nums">' +
                    _brv2EscHtml(_brv2FmtNum(usr)) +
                    '</td>' +
                    '<td style="padding:6px 10px;color:' +
                    diffColor +
                    ';font-weight:500;font-size:13px;' +
                    'text-align:right;font-variant-numeric:tabular-nums">' +
                    _brv2EscHtml(sign + _brv2FmtNum(diff)) +
                    '</td>' +
                    '</tr>'
                );
            })
            .join('');
        panel.innerHTML =
            '<div style="font-weight:600;color:#92400e;font-size:13px;margin-bottom:10px">' +
            _brv2EscHtml(
                _brv2T('brv2-anchor-audit-title', '⚠ This run contains manually entered anchors')
            ) +
            '</div>' +
            '<table style="width:100%;border-collapse:collapse;font-family:inherit">' +
            '<thead><tr>' +
            '<th style="padding:6px 10px;text-align:left;color:#6b7280;font-size:11px;' +
            'font-weight:500;border-bottom:1px solid #fed7aa">' +
            _brv2EscHtml(_brv2T('brv2-anchor-audit-col-field', 'Field')) +
            '</th>' +
            '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;' +
            'font-weight:500;border-bottom:1px solid #fed7aa">' +
            _brv2EscHtml(_brv2T('brv2-anchor-audit-col-ocr', 'OCR')) +
            '</th>' +
            '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;' +
            'font-weight:500;border-bottom:1px solid #fed7aa">' +
            _brv2EscHtml(_brv2T('brv2-anchor-audit-col-user', 'User')) +
            '</th>' +
            '<th style="padding:6px 10px;text-align:right;color:#6b7280;font-size:11px;' +
            'font-weight:500;border-bottom:1px solid #fed7aa">' +
            _brv2EscHtml(_brv2T('brv2-anchor-audit-col-diff', 'Diff')) +
            '</th>' +
            '</tr></thead><tbody>' +
            rows +
            '</tbody></table>';
    }

    function _initBrv2TogglePreview() {
        const btn = $('brv2-toggle-preview');
        if (btn && !btn._reconBound) {
            btn._reconBound = true;
            btn.addEventListener('click', function () {
                const panel = $('brv2-preview-panel');
                const label = $('brv2-toggle-preview-label');
                const isOpen = panel && panel.style.display !== 'none';
                if (panel) panel.style.display = isOpen ? 'none' : '';
                btn.classList.toggle('open', !isOpen);
                if (label)
                    label.textContent = isOpen
                        ? (window.t && window.t('vex-toggle-preview-open')) || '查看清单'
                        : (window.t && window.t('vex-toggle-preview-close')) || '收起清单';
                if (!isOpen) _renderBrv2PreviewPanel();
            });
        }
    }

    function updateRunBtn() {
        const btn = $('brv2-run-btn');
        const status = $('brv2-status');
        const hasStmt = _stmtFiles.length > 0;
        const hasGl = _glFiles.length > 0;
        if (btn) btn.disabled = !(hasStmt && hasGl);
        if (status) {
            const lang = window._currentLang || 'zh';
            if (!hasStmt && !hasGl) {
                const m = {
                    zh: '请上传银行账单和 GL 文件',
                    th: 'กรุณาอัปโหลดบัญชีธนาคารและ GL',
                    en: 'Upload bank statement and GL files',
                    ja: '銀行明細と GL を両方アップロードしてください',
                };
                status.textContent = m[lang] || m.zh;
            } else if (!hasStmt) {
                const m = {
                    zh: '还缺银行账单 PDF',
                    th: 'ยังขาดไฟล์บัญชีธนาคาร PDF',
                    en: 'Missing bank statement PDF',
                    ja: '銀行明細 PDF が未アップロード',
                };
                status.textContent = m[lang] || m.zh;
            } else if (!hasGl) {
                const m = {
                    zh: '还缺 GL 文件',
                    th: 'ยังขาดไฟล์ GL',
                    en: 'Missing GL file',
                    ja: 'GL ファイルが未アップロード',
                };
                status.textContent = m[lang] || m.zh;
            } else {
                const m = {
                    zh: '两份文件已就绪',
                    th: 'พร้อมสอบทาน',
                    en: 'Ready to reconcile',
                    ja: '照合を開始できます',
                };
                status.textContent = m[lang] || m.zh;
            }
        }
    }

    // ── Drag-and-drop（整区点击 · 无独立按钮） ────────────────────────
    function setupDrop(zoneId, inputId, zone) {
        const zoneEl = $(zoneId);
        const inputEl = $(inputId);
        if (!zoneEl || !inputEl) return;

        // 整区点击 → 弹文件对话框
        zoneEl.addEventListener('click', () => inputEl.click());
        zoneEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                inputEl.click();
            }
        });

        zoneEl.addEventListener('dragover', (e) => {
            e.preventDefault();
            zoneEl.classList.add('drag-over');
        });
        zoneEl.addEventListener('dragleave', () => zoneEl.classList.remove('drag-over'));
        zoneEl.addEventListener('drop', (e) => {
            e.preventDefault();
            zoneEl.classList.remove('drag-over');
            const dropped = Array.from(e.dataTransfer.files || []);
            if (zone === 'stmt') _stmtFiles.push(...dropped);
            else _glFiles.push(...dropped);
            renderFileList(zone);
            updateRunBtn();
        });

        inputEl.addEventListener('change', () => {
            const chosen = Array.from(inputEl.files || []);
            if (zone === 'stmt') _stmtFiles.push(...chosen);
            else _glFiles.push(...chosen);
            inputEl.value = '';
            renderFileList(zone);
            updateRunBtn();
        });
    }

    // ── Progress helpers ──────────────────────────────────────────────
    function showProgress(show) {
        const p = $('brv2-progress'),
            btn = $('brv2-run-btn'),
            err = $('brv2-error');
        if (p) p.style.display = show ? '' : 'none';
        if (btn) btn.disabled = show;
        if (err) err.style.display = 'none';
    }
    function showError(msg) {
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
        if (_stmtFiles.length === 0 || _glFiles.length === 0) return;
        const token = localStorage.getItem('mrpilot_token') || '';
        const lang = window._currentLang || 'zh';
        const acct = ($('brv2-acct-select') || {}).value || '';

        showResultSections(false);
        showProgress(true);

        try {
            const fd = new FormData();
            _stmtFiles.forEach((f) => fd.append('stmt_files', f));
            _glFiles.forEach((f) => fd.append('gl_files', f));
            fd.append('gl_account', acct);
            fd.append('lang', lang);

            // BUG-B v118.35.0.36 · 3 个 anchor 余额手动录入 · 优先于 OCR 抽到的值
            // BUG-FIX-T3 v118.35.0.44 · 加第 4 个 anchor stmt_closing(Statement 期末)
            const aGlClose = parseFloat(($('brv2-anchor-gl-closing') || {}).value);
            const aStmtClose = parseFloat(($('brv2-anchor-stmt-closing') || {}).value);
            const aStmtOpen = parseFloat(($('brv2-anchor-stmt-opening') || {}).value);
            const aGlOpen = parseFloat(($('brv2-anchor-gl-opening') || {}).value);
            if (Number.isFinite(aGlClose)) fd.append('gl_closing_override', aGlClose);
            if (Number.isFinite(aStmtClose)) fd.append('stmt_closing_override', aStmtClose);
            if (Number.isFinite(aStmtOpen)) fd.append('stmt_opening_override', aStmtOpen);
            if (Number.isFinite(aGlOpen)) fd.append('gl_opening_override', aGlOpen);

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
                        _humanizeBackendError(sub.detail || sub.error, 'Error ' + submitRes.status)
                    );
                } else {
                    showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                }
                return;
            }

            // 轮询后台任务 · 转圈旁实时显示「共 X/Y 个文件」
            const _subEl = $('brv2-progress-sub');
            const job = await window._reconPollJob(sub.job_id, token, {
                onProgress: (p) => {
                    if (_subEl) _subEl.textContent = window._reconProgressText(p, lang);
                },
            });
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
                        onConfirmed: async function (newJobId) {
                            showProgress(true);
                            const j2 = await window._reconPollJob(newJobId, token, {
                                onProgress: (p) => {
                                    if (_subEl)
                                        _subEl.textContent = window._reconProgressText(p, lang);
                                },
                            });
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
                showError(_brv2FailMsg(job.error_code, lang));
                return;
            }
            await _processBankJob(job);

            // 轮询完成后:取结果 + 渲染(初次 + S8 确认重对账共用)
            async function _processBankJob(job) {
                try {
                    if (!job || job.status !== 'done' || !job.result_id) {
                        showProgress(false);
                        showError(t('brv2-err-server') || '服务器繁忙,请稍后重试');
                        return;
                    }
                    // 用 result_id 调现有结果接口(GET 已补齐顶层 stats/parse_info/warnings · 与同步跑同源)
                    const res = await fetch(
                        '/api/recon/bank-v2/' + encodeURIComponent(job.result_id),
                        {
                            headers: { Authorization: 'Bearer ' + token },
                        }
                    );
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

                    _currentTask = data;
                    _allRows = data.detail || [];
                    _currentFilter = 'all';
                    document
                        .querySelectorAll('.brv2-filter-btn')
                        .forEach((b) => b.classList.toggle('active', b.dataset.filter === 'all'));

                    // P0.1 BUG-B-T1 v118.35.0.37 · 后端总是落 summary._anchor_ocr · 存到 localStorage
                    //   下次进对账 tab 自动预填 3 个 input · 不让用户从零填
                    _brv2SaveLastAnchorOcr(data && data.summary);

                    showProgress(false);
                    renderResults(data);
                    loadHistory();
                    const sc = $('brv2-summary-collapse');
                    if (sc) sc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } catch (e) {
                    showProgress(false);
                    showError(e.message || 'Network error');
                }
            }
        } catch (e) {
            showError(e.message || 'Network error');
        }
    }

    function populateAcctSelect(accounts) {
        const sel = $('brv2-acct-select');
        if (!sel) return;
        const _al = window._currentLang || 'zh';
        const _allAcctLbl =
            { zh: '全部账户', th: 'ทุกบัญชี', en: 'All Accounts', ja: 'すべての口座' }[_al] ||
            '全部账户';
        sel.innerHTML =
            `<option value="">${_allAcctLbl}</option>` +
            accounts.map((a) => `<option value="${esc2(a)}">${esc2(a)}</option>`).join('');
        sel.style.display = '';
    }

    // ── 显示/隐藏结果折叠区 ──────────────────────────────────────────
    function showResultSections(show) {
        const sc = $('brv2-summary-collapse');
        const dc = $('brv2-detail-collapse');
        const eb = $('brv2-export-btn');
        const nb = $('brv2-new-btn');
        const pi = $('brv2-parse-info-wrap');
        if (sc) sc.style.display = show ? '' : 'none';
        if (dc) dc.style.display = show ? '' : 'none';
        if (eb) eb.style.display = show ? '' : 'none';
        if (nb) nb.style.display = show ? '' : 'none';
        if (!show && pi) pi.style.display = 'none';
        // v118.35.0.56 · 重置时一并清掉警告条(不匹配/跳过提示)· 防残留误导
        const wn = $('brv2-warnings');
        if (!show && wn) {
            wn.style.display = 'none';
            wn.innerHTML = '';
        }
    }

    // ── 文件解析诊断表 ────────────────────────────────────────────────
    function renderParseInfo(data) {
        const wrap = $('brv2-parse-info-wrap');
        const body = $('brv2-parse-info-body');
        if (!wrap || !body) return;
        const pi = data.parse_info;
        if (!pi) {
            wrap.style.display = 'none';
            return;
        }

        const lang = window._currentLang || 'zh';
        const L = {
            title: {
                zh: '文件解析状态',
                th: 'สถานะการอ่านไฟล์',
                en: 'File Parse Status',
                ja: 'ファイル解析状態',
            },
            type: { zh: '类型', th: 'ประเภท', en: 'Type', ja: '種別' },
            file: { zh: '文件名', th: 'ชื่อไฟล์', en: 'File', ja: 'ファイル' },
            rows: { zh: '解析行数', th: 'แถวที่พบ', en: 'Rows Found', ja: '解析行数' },
            bank: { zh: '银行/科目', th: 'ธนาคาร/บัญชี', en: 'Bank/Account', ja: '銀行/科目' },
            status: { zh: '状态', th: 'สถานะ', en: 'Status', ja: '状態' },
            stmt: { zh: '账单', th: 'บัญชีธนาคาร', en: 'Stmt', ja: '明細' },
            gl: { zh: '总账GL', th: 'GL', en: 'GL', ja: 'GL' },
            ok: { zh: '✓ 成功', th: '✓ สำเร็จ', en: '✓ OK', ja: '✓ 成功' },
            warn: { zh: '⚠ 0行', th: '⚠ 0 แถว', en: '⚠ 0 rows', ja: '⚠ 0行' },
            fail: { zh: '✗ 失败', th: '✗ ล้มเหลว', en: '✗ Failed', ja: '✗ 失敗' },
        };
        const t = (k) => (L[k] || {})[lang] || (L[k] || {}).zh || k;

        const rows = [
            ...(pi.stmt_files || []).map((f) => ({
                ...f,
                _type: 'stmt',
                _extra: f.bank_code || '',
            })),
            ...(pi.gl_files || []).map((f) => ({
                ...f,
                _type: 'gl',
                _extra: (f.accounts || []).join(', '),
            })),
        ];

        // v118.35.0.19 · 错误提示词翻译层:把后端 raw 技术错误翻译成用户能懂的话(4 语)
        const _ERR_MAP = {
            stmt_headers_not_found: {
                zh: '认不出表头列 · 请确认文件含日期/金额/余额列',
                th: 'หาคอลัมน์หัวตารางไม่เจอ · ตรวจสอบไฟล์มีวันที่/จำนวนเงิน/ยอดคงเหลือ',
                en: 'Cannot detect column headers · ensure file has date/amount/balance columns',
                ja: '列ヘッダーが認識できません · 日付/金額/残高列を確認してください',
            },
            stmt_no_rows: {
                zh: '文件里没有交易数据 · 请确认上传了正确的银行流水',
                th: 'ไม่พบรายการธุรกรรมในไฟล์ · ตรวจสอบว่าอัปโหลด statement ที่ถูกต้อง',
                en: 'No transaction rows found · please check the file',
                ja: '取引データが見つかりません · ファイルを確認してください',
            },
            file_not_supported: {
                zh: '不支持此文件类型 · 请上传 PDF / 图片 / Excel / CSV',
                th: 'ไม่รองรับไฟล์ประเภทนี้ · กรุณาอัปโหลด PDF / รูปภาพ / Excel / CSV',
                en: 'File type not supported · please upload PDF / image / Excel / CSV',
                ja: 'このファイル形式は非対応 · PDF / 画像 / Excel / CSV をアップロード',
            },
            file_unreadable: {
                zh: '文件无法读取 · 可能已损坏或被加密',
                th: 'อ่านไฟล์ไม่ได้ · อาจเสียหายหรือถูกเข้ารหัส',
                en: 'File cannot be read · may be corrupted or encrypted',
                ja: 'ファイルを読み取れません · 破損または暗号化の可能性',
            },
            ocr_failed: {
                zh: '文件识别失败 · 请尝试更清晰的版本或换 PDF 格式重传',
                th: 'อ่านไฟล์ไม่ออก · ลองเวอร์ชันที่ชัดเจนกว่าหรือเปลี่ยนเป็น PDF',
                en: 'Could not read file · try a clearer version or upload as PDF',
                ja: '読み取り失敗 · より鮮明なファイルまたは PDF 形式で再試行',
            },
            gl_headers_not_found: {
                zh: '认不出总账表头 · 请确认文件含科目/借方/贷方列',
                th: 'หาหัวคอลัมน์ GL ไม่เจอ · ตรวจสอบมีคอลัมน์บัญชี/เดบิต/เครดิต',
                en: 'Cannot detect GL column headers · ensure account/debit/credit columns exist',
                ja: 'GL 列ヘッダー認識不可 · 科目/借方/貸方列を確認してください',
            },
        };
        // raw error → error_code 正则映射(后端老路径未带 code 时兜底)
        const _rawToCode = (raw) => {
            const r = String(raw || '');
            if (/Cannot detect bank statement column headers/i.test(r))
                return 'stmt_headers_not_found';
            if (/Cannot detect GL column headers/i.test(r)) return 'gl_headers_not_found';
            if (/No transaction rows found|no pages parsed/i.test(r)) return 'stmt_no_rows';
            if (/unsupported format/i.test(r)) return 'file_not_supported';
            if (/Cannot read Excel|file_unreadable/i.test(r)) return 'file_unreadable';
            if (
                /Gemini.*invalid JSON|Gemini.*parsed but failed|validation errors|BankStatementDocument schema|layer2:|layer1:/i.test(
                    r
                )
            )
                return 'ocr_failed';
            return null;
        };
        const _humanizeReconError = (row) => {
            const code = row.error_code || _rawToCode(row.error);
            if (code && _ERR_MAP[code]) {
                const lng = window._currentLang || 'zh';
                return _ERR_MAP[code][lng] || _ERR_MAP[code].zh;
            }
            // 无法翻译 → 用通用 + 截断 raw(供技术支持参考)
            return String(row.error || '').slice(0, 80);
        };

        const statusCell = (row) => {
            if (!row.ok && row.error)
                return `<span style="color:#dc2626">${t('fail')} — ${esc2(_humanizeReconError(row))}</span>`;
            if (!row.rows) return `<span style="color:#d97706">${t('warn')}</span>`;
            return `<span style="color:#059669">${t('ok')} (${row.rows})</span>`;
        };

        body.innerHTML = `
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:var(--ink-2)">${t('title')}</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:4px">
                <thead>
                    <tr style="background:#f3f4f6;font-weight:600">
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('type')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb">${t('file')}</th>
                        <th style="padding:6px 8px;text-align:center;border:1px solid #e5e7eb;white-space:nowrap">${t('rows')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('bank')}</th>
                        <th style="padding:6px 8px;text-align:left;border:1px solid #e5e7eb;white-space:nowrap">${t('status')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows
                        .map(
                            (row) => `<tr>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;white-space:nowrap">${row._type === 'stmt' ? t('stmt') : t('gl')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc2(row.file || '')}">${esc2(row.file || '')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:center">${row.rows || 0}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb;color:var(--ink-2)">${esc2(row._extra || '')}</td>
                        <td style="padding:5px 8px;border:1px solid #e5e7eb">${statusCell(row)}</td>
                    </tr>`
                        )
                        .join('')}
                </tbody>
            </table>`;
        wrap.style.display = '';
    }

    // ── Export helper (fetch+blob so Auth header is sent) ─────────────
    async function _brv2Export(taskId) {
        const token = localStorage.getItem('mrpilot_token') || '';
        const l = window._currentLang || 'zh';
        try {
            const resp = await fetch('/api/recon/bank-v2/' + taskId + '/export?lang=' + l, {
                headers: { Authorization: 'Bearer ' + token },
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                if (window.showToast) window.showToast(err.detail || 'Export failed', 'error');
                return;
            }
            const blob = await resp.blob();
            const cd = resp.headers.get('content-disposition') || '';
            const m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            const filename = m ? m[1].replace(/['"]/g, '') : 'reconciliation.xlsx';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (e) {
            if (window.showToast) window.showToast('Export error: ' + e.message, 'error');
        }
    }

    // ── Render results ────────────────────────────────────────────────
    // v118.35.0.54 · 输入不匹配 / 跳过文件 警告条(期间/规模对不上 · 不让用户看不懂差额)
    function _brv2RenderWarnings(warnings, skipped) {
        const host = $('brv2-summary-collapse');
        let box = $('brv2-warnings');
        const _l = window._currentLang || 'zh';
        const skipLbl =
            {
                zh: '⏭ 已跳过无法识别的文件:',
                th: '⏭ ข้ามไฟล์ที่อ่านไม่ได้:',
                en: '⏭ Skipped unreadable file:',
                ja: '⏭ 読み取れないファイルをスキップ:',
            }[_l] || '⏭ ';
        const msgs = [];
        (skipped || []).forEach((fn) => msgs.push(skipLbl + ' ' + fn));
        (warnings || []).forEach((w) => msgs.push(w));
        if (!msgs.length) {
            if (box) box.style.display = 'none';
            return;
        }
        if (!box) {
            box = document.createElement('div');
            box.id = 'brv2-warnings';
            if (host && host.parentNode) host.parentNode.insertBefore(box, host);
            else return;
        }
        box.style.cssText =
            'display:block;margin:10px 0;padding:10px 14px;background:#FEF3C7;' +
            'border:1px solid #FCD34D;border-radius:8px;color:#92400E;font-size:13px;line-height:1.6';
        box.innerHTML = msgs.map((m) => '<div>' + esc2(m) + '</div>').join('');
    }

    function renderResults(data) {
        // Always render parse diagnostics (shown on both success and failure)
        renderParseInfo(data);
        // v118.35.0.54 · 输入不匹配 / 跳过文件 警告条
        _brv2RenderWarnings(data.warnings || [], data.skipped_files || []);

        // If parse failed, show error toast but still display the diagnostics panel
        if (!data.ok && data.error) {
            if (window.showToast) window.showToast(data.error, 'error');
        }

        const stats = data.stats || {};
        const summary = data.summary || {};

        const matched = stats.matched || 0;
        const glOnly = (stats.gl_debit_only || 0) + (stats.gl_credit_only || 0);
        const stmtOnly = (stats.stmt_withdrawal_only || 0) + (stats.stmt_deposit_only || 0);
        const fdiff = Number(summary.formula_diff || 0);
        const diffOk = Math.abs(fdiff) < 0.05;

        // KPI strip (3 cards)
        if ($('brv2-kpi-matched')) $('brv2-kpi-matched').textContent = matched;
        if ($('brv2-kpi-diff')) $('brv2-kpi-diff').textContent = fmtNum(fdiff);
        if ($('brv2-kpi-unmatched')) $('brv2-kpi-unmatched').textContent = glOnly + stmtOnly;
        // 差额图标颜色
        const diffIcon = $('brv2-kpi-diff-icon');
        if (diffIcon) {
            diffIcon.style.background = diffOk ? '#d1fae5' : '#fee2e2';
            diffIcon.style.color = diffOk ? '#065f46' : '#b91c1c';
        }

        // Formula collapse 小标题
        const formulaSub = $('brv2-formula-sub');
        if (formulaSub) {
            const _fl = window._currentLang || 'zh';
            formulaSub.textContent = diffOk
                ? { zh: '✓ 平衡', th: '✓ สมดุล', en: '✓ Balanced', ja: '✓ 一致' }[_fl] || '✓ 平衡'
                : ({ zh: '差 ', th: 'ต่าง ', en: 'Diff ', ja: '差 ' }[_fl] || '差 ') +
                  fmtNum(fdiff);
        }

        // Detail collapse 小标题
        const detailSub = $('brv2-detail-sub');
        if (detailSub) {
            const _dl = window._currentLang || 'zh';
            const _rowLbl =
                { zh: '共 {n} 行', th: 'ทั้งหมด {n} แถว', en: '{n} rows', ja: '計 {n} 行' }[_dl] ||
                '共 {n} 行';
            detailSub.textContent = _rowLbl.replace('{n}', _allRows.length);
        }

        // 公式表
        function setFrm(id, val, neg) {
            const el = $(id);
            if (!el) return;
            el.textContent =
                (neg && val > 0 ? '(' : '') +
                fmtNum(neg ? -val : val) +
                (neg && val > 0 ? ')' : '');
        }
        setFrm('brf-gl-close', summary.gl_closing || 0);
        setFrm('brf-open-diff', summary.opening_diff || 0);
        setFrm('brf-gl-debit-only', summary.gl_debit_only_amount || 0, true);
        setFrm('brf-gl-credit-only', summary.gl_credit_only_amount || 0);
        setFrm('brf-stmt-wd-only', summary.stmt_withdrawal_only_amount || 0, true);
        setFrm('brf-stmt-dep-only', summary.stmt_deposit_only_amount || 0);
        setFrm('brf-calc-close', summary.formula_stmt_closing || 0);
        setFrm('brf-stmt-close', summary.stmt_closing || 0);
        if ($('brf-diff')) {
            $('brf-diff').textContent = fmtNum(fdiff);
        }

        // 差额卡片颜色 (v118.33.12.0 · 横向公式卡片)
        const diffCell = $('brv2-fcell-diff');
        if (diffCell) {
            diffCell.classList.toggle('brv2-fcell-diff-ok', diffOk);
        }

        // 导出按钮事件
        const exportBtn = $('brv2-export-btn');
        if (exportBtn) {
            exportBtn.onclick = () => {
                if (!_currentTask) return;
                _brv2Export(_currentTask.task_id);
            };
        }

        // P0.3 BUG-B-T3 v118.35.0.39 · 渲染 anchor 手动录入对照(只在 summary._anchor_overrides 非空时显示)
        _brv2RenderAnchorAudit(summary);

        showResultSections(true);
        renderTable();
    }

    function renderTable() {
        const tbody = $('brv2-tbody');
        if (!tbody) return;

        const rows = _allRows.filter((r) => {
            if (_currentFilter === 'all') return true;
            if (_currentFilter === 'matched') return r.match_status === 'matched';
            if (_currentFilter === 'gl_only') return r.match_status.startsWith('gl_');
            if (_currentFilter === 'stmt_only') return r.match_status.startsWith('stmt_');
            return true;
        });

        if (rows.length === 0) {
            const noRows =
                { zh: '无记录', th: 'ไม่มีรายการ', en: 'No rows', ja: '行なし' }[
                    window._currentLang || 'zh'
                ] || '无记录';
            tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:20px;color:var(--ink-3)">${noRows}</td></tr>`;
            return;
        }

        const _lang2 = window._currentLang || 'zh';
        const T_OCR_WARN_BAL = {
            zh: 'OCR 余额验证未通过 · 上一行余额 ± 金额 ≠ 本行余额，请核对原 PDF',
            th: 'การตรวจสอบยอดคงเหลือไม่ผ่าน · ยอดก่อนหน้า ± จำนวน ≠ ยอดบรรทัดนี้ โปรดตรวจสอบ PDF ต้นฉบับ',
            en: 'Balance check FAILED · prev_balance ± amount ≠ this row balance — verify against the original PDF',
            ja: '残高検証エラー · 前残高 ± 金額 ≠ この行残高 — 元のPDFと照合してください',
        }[_lang2];
        const T_OCR_LOW_CONF = {
            zh: 'OCR 低置信度 · 数字模糊或难以辨认，请核对原 PDF',
            th: 'OCR ความมั่นใจต่ำ · ตัวเลขเบลอหรืออ่านยาก โปรดตรวจสอบ PDF ต้นฉบับ',
            en: 'OCR low confidence · digit was blurry or hard to read — verify against the original PDF',
            ja: 'OCR信頼度低 · 数字がぼやけている — 元のPDFと照合してください',
        }[_lang2];

        tbody.innerHTML = rows
            .map((r) => {
                const st = r.match_status;
                const layer = r.match_layer;

                let rowClass = '';
                let badge = '';
                if (st === 'matched') {
                    if (layer === 1) {
                        rowClass = 'matched';
                        badge = '<span class="brv2-status-badge brv2-badge-matched">L1 ✓</span>';
                    }
                    if (layer === 2) {
                        rowClass = 'matched-l2';
                        badge = '<span class="brv2-status-badge brv2-badge-matched-l2">L2 ~</span>';
                    }
                    if (layer === 3) {
                        rowClass = 'matched-l3';
                        badge = '<span class="brv2-status-badge brv2-badge-matched-l3">L3 ?</span>';
                    }
                } else if (st === 'gl_debit_only' || st === 'gl_credit_only') {
                    rowClass = 'gl-only';
                    badge = '<span class="brv2-status-badge brv2-badge-gl-only">GL</span>';
                } else {
                    rowClass = 'stmt-only';
                    const stmtLbl =
                        { zh: '账单', th: 'บัญชี', en: 'Stmt', ja: '明細' }[_lang2] || '账单';
                    badge = `<span class="brv2-status-badge brv2-badge-stmt-only">${stmtLbl}</span>`;
                }

                // v118.33.13.0 · OCR accuracy warning icons (balance check, confidence)
                let warnIcons = '';
                if (r.stmt_balance_ok === false) {
                    warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-bal" title="${esc2(T_OCR_WARN_BAL)}">⚠</span>`;
                    rowClass += ' brv2-row-warn';
                }
                if (r.stmt_confidence === 'low') {
                    warnIcons += `<span class="brv2-ocr-warn brv2-ocr-warn-conf" title="${esc2(T_OCR_LOW_CONF)}">◌</span>`;
                    if (!rowClass.includes('brv2-row-warn')) rowClass += ' brv2-row-warn-soft';
                }

                return `<tr class="${rowClass.trim()}">
              <td>${badge}${warnIcons}</td>
              <td>${esc2(fmtDate(r.stmt_date))}</td>
              <td title="${esc2(r.stmt_desc)}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.stmt_desc)}</td>
              <td class="num">${r.stmt_withdrawal ? fmtNum(r.stmt_withdrawal) : ''}</td>
              <td class="num">${r.stmt_deposit ? fmtNum(r.stmt_deposit) : ''}</td>
              <td>${esc2(fmtDate(r.gl_date))}</td>
              <td title="${esc2(r.gl_doc_no)}" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc2(r.gl_doc_no)}</td>
              <td class="num">${r.gl_debit ? fmtNum(r.gl_debit) : ''}</td>
              <td class="num">${r.gl_credit ? fmtNum(r.gl_credit) : ''}</td>
              <td>${layer ? 'L' + layer : '—'}</td>
            </tr>`;
            })
            .join('');
    }

    // ── History ───────────────────────────────────────────────────────
    async function loadHistory() {
        const token = localStorage.getItem('mrpilot_token') || '';
        try {
            const res = await fetch('/api/recon/bank-v2/tasks', {
                headers: { Authorization: 'Bearer ' + token },
            });
            const data = await res.json();
            renderHistory(data.tasks || []);
        } catch (e) {
            const emptyEl = $('brv2-history-empty');
            const lang = window._currentLang || 'zh';
            const errMsg =
                { zh: '加载失败', th: 'โหลดประวัติไม่ได้', en: 'Load failed', ja: '読み込み失敗' }[
                    lang
                ] || '加载失败';
            if (emptyEl) {
                emptyEl.textContent = errMsg;
                emptyEl.style.display = '';
            }
            const wrap = $('brv2-history-table-wrap');
            if (wrap) wrap.style.display = 'none';
        }
    }

    const BRV2_PAGE_SIZE = 10;
    let _brv2Page = 1;

    function _brv2RenderPager() {
        const pager = $('brv2-history-pager');
        const info = $('brv2-history-pager-info');
        const prev = $('brv2-history-prev');
        const next = $('brv2-history-next');
        if (!pager) return;
        if (_cachedHistoryTasks.length <= BRV2_PAGE_SIZE) {
            pager.style.display = 'none';
            return;
        }
        pager.style.display = '';
        const totalPages = Math.ceil(_cachedHistoryTasks.length / BRV2_PAGE_SIZE);
        if (info) info.textContent = _brv2Page + ' / ' + totalPages;
        if (prev) prev.disabled = _brv2Page <= 1;
        if (next) next.disabled = _brv2Page >= totalPages;
    }

    function _brv2InitPager() {
        const prev = $('brv2-history-prev');
        const next = $('brv2-history-next');
        if (prev && !prev._brv2Bound) {
            prev._brv2Bound = true;
            prev.addEventListener('click', () => {
                if (_brv2Page > 1) {
                    _brv2Page--;
                    renderHistory(_cachedHistoryTasks);
                }
            });
        }
        if (next && !next._brv2Bound) {
            next._brv2Bound = true;
            next.addEventListener('click', () => {
                const totalPages = Math.ceil(_cachedHistoryTasks.length / BRV2_PAGE_SIZE);
                if (_brv2Page < totalPages) {
                    _brv2Page++;
                    renderHistory(_cachedHistoryTasks);
                }
            });
        }
    }

    function renderHistory(tasks) {
        if (tasks !== undefined) {
            _cachedHistoryTasks = tasks || [];
            _brv2Page = 1;
        }
        const all = _cachedHistoryTasks;
        const emptyEl = $('brv2-history-empty');
        const wrap = $('brv2-history-table-wrap');
        const tbody = $('brv2-history-tbody');
        if (!tbody) return;

        const lang = window._currentLang || 'zh';
        if (!all.length) {
            const emptyTxt =
                { zh: '暂无对账记录', th: 'ยังไม่มีประวัติ', en: 'No records yet', ja: '記録なし' }[
                    lang
                ] || '暂无对账记录';
            if (emptyEl) {
                emptyEl.textContent = emptyTxt;
                emptyEl.style.display = '';
            }
            if (wrap) wrap.style.display = 'none';
            _brv2RenderPager();
            return;
        }
        if (emptyEl) emptyEl.style.display = 'none';
        if (wrap) wrap.style.display = '';
        const totalPages = Math.ceil(all.length / BRV2_PAGE_SIZE);
        if (_brv2Page > totalPages) _brv2Page = totalPages;
        const start = (_brv2Page - 1) * BRV2_PAGE_SIZE;
        const tasks_page = all.slice(start, start + BRV2_PAGE_SIZE);

        const token = localStorage.getItem('mrpilot_token') || '';
        const SVG_LOAD =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>';
        const SVG_DL =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>';
        const SVG_DEL =
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';

        tbody.innerHTML = '';
        tasks_page.forEach((t) => {
            const diff = Number(t.formula_diff || 0);
            const diffOk = Math.abs(diff) < 0.05;
            const stmtF = (t.stmt_files || '')
                .split(';')
                .map((s) => s.trim().split(/[/\\]/).pop())
                .filter(Boolean)
                .join(', ');
            const glF = (t.gl_files || '')
                .split(';')
                .map((s) => s.trim().split(/[/\\]/).pop())
                .filter(Boolean)
                .join(', ');
            const dt = t.created_at ? String(t.created_at).slice(0, 16).replace('T', ' ') : '';

            const tr = document.createElement('tr');
            tr.dataset.taskId = t.id;

            const tdTime = document.createElement('td');
            tdTime.textContent = dt;

            const tdFiles = document.createElement('td');
            tdFiles.className = 'glv-history-file';
            tdFiles.title = stmtF + ' + ' + glF;
            tdFiles.textContent = stmtF + ' + ' + glF;

            const tdRows = document.createElement('td');
            tdRows.className = 'glv-num';
            tdRows.textContent = (t.stmt_row_count || 0) + ' / ' + (t.gl_row_count || 0);

            const tdMatched = document.createElement('td');
            tdMatched.className = 'glv-num';
            tdMatched.textContent = t.matched_count || 0;

            const tdGlOnly = document.createElement('td');
            tdGlOnly.className = 'glv-num';
            tdGlOnly.textContent = t.unmatched_gl || 0;

            const tdStmtOnly = document.createElement('td');
            tdStmtOnly.className = 'glv-num';
            tdStmtOnly.textContent = t.unmatched_stmt || 0;

            const tdDiff = document.createElement('td');
            tdDiff.className = 'glv-num';
            tdDiff.style.color = diffOk ? '#059669' : '#dc2626';
            tdDiff.textContent = diffOk ? '✓' : fmtNum(diff);

            const tdAct = document.createElement('td');
            tdAct.className = 'glv-history-actions';
            const mkBtn = (svg, title, cls, onClick) => {
                const b = document.createElement('button');
                b.type = 'button';
                b.title = title;
                b.setAttribute('aria-label', title);
                if (cls) b.className = cls;
                b.innerHTML = svg;
                b.onclick = (e) => {
                    e.stopPropagation();
                    onClick();
                };
                return b;
            };
            const delConfirm =
                {
                    zh: '删除这条记录?',
                    th: 'ลบรายการนี้?',
                    en: 'Delete this record?',
                    ja: 'この記録を削除しますか?',
                }[lang] || '删除?';
            const lblLoad = { zh: '加载', th: 'โหลด', en: 'Load', ja: '読込' }[lang] || '加载';
            const lblExp =
                { zh: '导出', th: 'ส่งออก', en: 'Export', ja: 'エクスポート' }[lang] || '导出';
            const lblDel = { zh: '删除', th: 'ลบ', en: 'Delete', ja: '削除' }[lang] || '删除';
            tdAct.appendChild(mkBtn(SVG_LOAD, lblLoad, '', () => loadTask(t.id, token)));
            tdAct.appendChild(mkBtn(SVG_DL, lblExp, '', () => _brv2Export(t.id)));
            tdAct.appendChild(
                mkBtn(SVG_DEL, lblDel, 'glv-del', async () => {
                    if (!(await showConfirm(delConfirm, { danger: true }))) return;
                    await fetch('/api/recon/bank-v2/' + t.id, {
                        method: 'DELETE',
                        headers: { Authorization: 'Bearer ' + token },
                    });
                    loadHistory();
                })
            );

            [tdTime, tdFiles, tdRows, tdMatched, tdGlOnly, tdStmtOnly, tdDiff, tdAct].forEach((c) =>
                tr.appendChild(c)
            );
            tr.style.cursor = 'pointer';
            tr.addEventListener('click', async (e) => {
                if (e.target.closest('.glv-del') || e.target.closest('button')) return;
                await loadTask(t.id, token);
            });
            tbody.appendChild(tr);
        });
        _brv2RenderPager();
        _applyBrv2Search();
    }

    function _applyBrv2Search() {
        const q = (($('brv2-hist-search') || {}).value || '').trim().toLowerCase();
        const tbody = $('brv2-history-tbody');
        if (!tbody) return;
        tbody.querySelectorAll('tr').forEach((tr) => {
            if (!tr.dataset.taskId) return;
            tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none';
        });
    }

    async function loadTask(taskId, token) {
        try {
            const res = await fetch('/api/recon/bank-v2/' + taskId, {
                headers: { Authorization: 'Bearer ' + token },
            });
            const data = await res.json();
            if (!data.ok) return;
            _currentTask = { task_id: data.task_id, ...data };
            _allRows = data.detail || [];
            _currentFilter = 'all';
            // 重置 filter tab 到 "all"
            document
                .querySelectorAll('.brv2-filter-btn')
                .forEach((b) => b.classList.toggle('active', b.dataset.filter === 'all'));
            renderResults(_currentTask);
        } catch (e) {
            /* silent */
        }
    }

    // ── Init ──────────────────────────────────────────────────────────
    function init() {
        if (_initialized) {
            // 二次进入只刷历史
            loadHistory();
            return;
        }
        _initialized = true;

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
            const stmtOpen = parseFloat(($('brv2-anchor-stmt-opening') || {}).value);
            const glOpen = parseFloat(($('brv2-anchor-gl-opening') || {}).value);
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
                _currentTask = null;
                _allRows = [];
                _stmtFiles = [];
                _glFiles = [];
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
                        el.value = '';
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
                _currentTask = null;
                _allRows = [];
                _stmtFiles = [];
                _glFiles = [];
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
                const btn = e.target.closest('.brv2-filter-btn');
                if (!btn) return;
                _currentFilter = btn.dataset.filter;
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
        window.__i18nSubs = window.__i18nSubs.filter((s) => s.name !== 'brv2');
        window.__i18nSubs.push({
            name: 'brv2',
            fn: function () {
                updateRunBtn();
                renderFileList('stmt');
                renderFileList('gl');
                if (_currentTask) renderResults(_currentTask);
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

    // Auto-init when pane becomes visible
    document.addEventListener('DOMContentLoaded', () => {
        // Init immediately if pane is active
        if ($('brv2-run-btn')) init();
    });

    // Also init when reconcile page is navigated to
    window._bankReconV2Init = init;
})();
