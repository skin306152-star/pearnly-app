/*
 * Pearnly AI · ai-pkg-render.js · 交付包视图(W5)的纯函数 + HTML 拼装
 *
 * 双导出(同 ai-intake-render.js UMD 先例):isImageFileName/dueDisplay 零 DOM 依赖,node
 * (tests/unit/test_ai_pure_modules.py)直接 require 断言;HTML 拼装依赖 at()/AI.state/
 * AI.format/AI.viewer,只在浏览器根挂载。真正的编排(挂载/下载/模态框开关)在 ai-pkg.js,
 * 排在本文件之后加载(见 scripts/build-home-js.mjs)。
 *
 * 五种交付物固定展示顺序(任务包 §5 步 6 / M1-施工任务包 W5 行),与后端 package.py 的
 * kinds dict 语义一致,只是这里排出人读顺序:草稿在前、证据索引收尾。
 */
(function (root) {
    'use strict';

    var KIND_ORDER = [
        'pp30_draft',
        'ledger_workpaper',
        'bank_workpaper',
        'missing_doc_memo',
        'evidence_index',
    ];

    // 证据条目的文件名 → 能不能当票据照片直接用查看器打开(状态诚实:xlsx/pdf 等非图片
    // 文件不装模作样塞进 <img>,那只会碎图——铺满率≥0.8 的视觉验收血泪教训)。
    function isImageFileName(name) {
        return /\.(jpe?g|png|gif|webp|bmp)$/i.test(String(name || ''));
    }

    // tax_due 的应缴/留抵展示口径:负数=留抵(如实表达,不 clamp 成 0,与 compute.py 同口径)。
    // 返回 {labelKey, amount}(amount 已取绝对值,标签自己已经说明方向,不必再显负号)。
    function dueDisplay(taxDueRaw) {
        var n = Number(taxDueRaw);
        var refund = isFinite(n) && n < 0;
        return {
            labelKey: refund ? 'pkg_line_refund' : 'pkg_line_due',
            amount: refund ? -n : n,
        };
    }

    var pure = { KIND_ORDER: KIND_ORDER, isImageFileName: isImageFileName, dueDisplay: dueDisplay };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format/AI.viewer,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }
    function money(v) {
        return v == null || v === '' ? '—' : root.AI.format.money(v);
    }
    function svgDoc() {
        return (
            '<svg viewBox="0 0 24 24" fill="none" stroke-width="2">' +
            '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>' +
            '</svg>'
        );
    }

    // ---- 销项来源标注(状态诚实条款:人工申报不与直读混同) ----
    function salesSourceHtml(numbers) {
        var source = numbers.sales_source;
        if (!source || source === 'direct_read') return '';
        var key = source === 'mixed' ? 'pkg_sales_source_mixed' : 'pkg_sales_source_manual';
        var note = numbers.sales_source_note
            ? '<br><small>' +
              esc(at('pkg_sales_source_note', { note: numbers.sales_source_note })) +
              '</small>'
            : '';
        return '<span class="chip w">' + esc(at(key)) + '</span>' + note;
    }

    // ---- ภ.พ.30 草稿卡(v4 .pkg-line/.pkg-total 1:1) ----
    function pp30CardHtml(numbers, calcOpen, status) {
        var due = dueDisplay(numbers.tax_due);
        var calcLine = at('pkg_calc_line', {
            output: money(numbers.output_vat),
            input: money(numbers.input_vat),
            due: money(numbers.tax_due),
        });
        var sourceBadge = salesSourceHtml(numbers);
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('pkg_title')) +
            ' ' +
            root.AI.format.chipHtml(status) +
            '</h3></div><div class="bd">' +
            '<div class="pkg-line"><div class="d">' +
            esc(at('pkg_line_output')) +
            (sourceBadge ? '<br>' + sourceBadge : '') +
            '</div><div class="v"><span class="n num">' +
            money(numbers.output_vat) +
            '</span><button class="evid" type="button" data-action="pkg-evid" data-num="output_vat">' +
            esc(at('pkg_evid_link')) +
            '</button></div></div>' +
            '<div class="pkg-line"><div class="d">' +
            esc(at('pkg_line_input')) +
            '</div><div class="v"><span class="n num">' +
            money(numbers.input_vat) +
            '</span><button class="evid" type="button" data-action="pkg-evid" data-num="input_vat">' +
            esc(at('pkg_evid_link')) +
            '</button></div></div>' +
            '<div class="pkg-total"><div class="d">' +
            esc(at(due.labelKey)) +
            '</div><div class="v"><span class="n num">' +
            money(due.amount) +
            '</span><button class="evid" type="button" data-action="pkg-calc">' +
            esc(at('pkg_calc_link')) +
            '</button></div></div>' +
            (calcOpen ? '<p class="pkg-calc-note">' + esc(calcLine) + '</p>' : '') +
            '</div></div>'
        );
    }

    // ---- 草稿被卡:状态诚实,不假装已生成(needs/blocked_reasons 来自 order_detail) ----
    function blockedHtml(detail) {
        detail = detail || {};
        var reasons = [].concat(detail.needs || [], detail.blocked_reasons || []);
        return (
            '<div class="panel"><div class="bd pkg-blocked">' +
            '<div class="t">' +
            esc(at('pkg_blocked_t')) +
            '</div><div class="s">' +
            esc(at('pkg_blocked_s')) +
            '</div>' +
            (reasons.length
                ? '<div class="reasons">' +
                  esc(at('pkg_blocked_reasons', { list: reasons.join('、') })) +
                  '</div>'
                : '') +
            '</div></div>'
        );
    }

    // ---- 交付物清单(v4 .pkg-files/.pfile 1:1,下载按钮换真数据) ----
    function fileRowHtml(kind, row, downloading) {
        var label = root.AI.format.fieldLabel(kind);
        if (!row || !row.has_file) {
            return (
                '<span class="pfile muted">' +
                svgDoc() +
                esc(label) +
                ' <span class="chip n">' +
                esc(at('pkg_file_pending')) +
                '</span></span>'
            );
        }
        var sub = fileSubtext(kind, row.numbers || {});
        var busy = downloading === kind;
        return (
            '<span class="pfile">' +
            svgDoc() +
            esc(label) +
            (sub ? '<small> · ' + esc(sub) + '</small>' : '') +
            '<button type="button" data-action="pkg-download" data-kind="' +
            esc(kind) +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('pkg_file_download')) +
            '</button></span>'
        );
    }

    function fileSubtext(kind, numbers) {
        if (kind === 'bank_workpaper') {
            return numbers.bank_statement_present
                ? at('pkg_bank_present', { n: numbers.bank_statement_count || 0 })
                : at('pkg_bank_missing');
        }
        if (kind === 'missing_doc_memo' && numbers.flagged_count) {
            return at('pkg_memo_flagged', { n: numbers.flagged_count });
        }
        return '';
    }

    function filesListHtml(deliverables, downloading) {
        var byKind = {};
        (deliverables || []).forEach(function (d) {
            byKind[d.kind] = d;
        });
        var rows = KIND_ORDER.map(function (kind) {
            return fileRowHtml(kind, byKind[kind], downloading);
        }).join('');
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('pkg_files_title')) +
            '</h3></div><div class="bd"><div class="pkg-files">' +
            rows +
            '</div>' +
            degradeHtml() +
            '</div></div>'
        );
    }

    // ---- M1 降级区(电子签/推 Express/退回工单未接——状态诚实,不给假按钮点了没反应) ----
    function degradeHtml() {
        var btn = function (labelKey) {
            return (
                '<button class="btn" disabled title="' +
                esc(at('pkg_not_available')) +
                '">' +
                esc(at(labelKey)) +
                '</button>'
            );
        };
        return (
            '<div class="pkg-downgrade">' +
            '<div style="display:flex;gap:10px;flex-wrap:wrap">' +
            btn('pkg_sign_btn') +
            btn('pkg_export_btn') +
            btn('pkg_return_btn') +
            '</div>' +
            '<p class="pkg-downgrade-note">' +
            esc(at('pkg_downgrade_t')) +
            ': ' +
            esc(at('pkg_sign_btn')) +
            ' · ' +
            esc(at('pkg_export_btn')) +
            ' · ' +
            esc(at('pkg_return_btn')) +
            '</p>' +
            '</div>'
        );
    }

    // ---- 整页(交付物为空 → 复用既有 pkg_empty 四态空态,不重造一份文案) ----
    function pageHtml(ctx) {
        if (!ctx.deliverables || !ctx.deliverables.length) {
            return root.AI.state.emptyHtml({ title: at('pkg_empty_t'), sub: at('pkg_empty_s') });
        }
        var pp30Card = ctx.pp30
            ? pp30CardHtml(ctx.pp30.numbers || {}, ctx.calcOpen, (ctx.detail || {}).status)
            : blockedHtml(ctx.detail);
        return pp30Card + filesListHtml(ctx.deliverables, ctx.downloading);
    }

    // ---- 证据模态框(v4 .mask/.modal/.ev-row 1:1;点验回链:数字 → 证据行 → 原图,≤2 击) ----
    function evidRowHtml(item, selectedId) {
        var name = item.file_name;
        if (!name) {
            return (
                '<div class="ev-row novisual"><span>' +
                esc(at('pkg_evid_empty')) +
                '</span><span></span></div>'
            );
        }
        if (!isImageFileName(name)) {
            return (
                '<div class="ev-row novisual"><span>' +
                esc(name) +
                '</span><span class="chip n">' +
                esc(at('pkg_evid_not_image')) +
                '</span></div>'
            );
        }
        return (
            '<div class="ev-row' +
            (item.item_id === selectedId ? ' sel' : '') +
            '"><span>' +
            esc(name) +
            '</span><button class="evid" type="button" data-action="pkg-evid-item" data-item-id="' +
            esc(item.item_id) +
            '">' +
            esc(at('pkg_evid_open')) +
            '</button></div>'
        );
    }

    function evidModalHtml(evid) {
        var entry = evid.entry || {};
        var items = entry.items || [];
        var selected = items.filter(function (it) {
            return it.item_id === evid.selectedItemId;
        })[0];
        var viewerVisible = selected && isImageFileName(selected.file_name);
        var rows = items.length
            ? items
                  .map(function (it) {
                      return evidRowHtml(it, evid.selectedItemId);
                  })
                  .join('')
            : '<div class="ev-row novisual"><span>' + esc(at('pkg_evid_empty')) + '</span></div>';
        return (
            '<div class="pkg-mask on" id="pkgEvidMask">' +
            '<div class="pkg-modal">' +
            '<div class="mh"><div><h3>' +
            esc(at('pkg_evid_title', { label: evid.label })) +
            '</h3><p>' +
            esc(at('pkg_evid_pick_hint')) +
            '</p></div>' +
            '<button class="mclose" type="button" data-action="pkg-evid-close" aria-label="' +
            esc(at('pkg_evid_close')) +
            '">&times;</button></div>' +
            '<div class="mb"><div class="pkg-evid-list">' +
            rows +
            '</div><div class="pkg-evid-view' +
            (viewerVisible ? '' : ' empty') +
            '" id="pkgEvidView">' +
            (viewerVisible
                ? root.AI.viewer.imageViewerHtml({
                      hint: at('imgv_hint'),
                      noimg: at('imgv_noimg'),
                      loading: at('imgv_loading'),
                  })
                : esc(at('pkg_evid_pick_hint'))) +
            '</div></div>' +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.pkgRender = {
        KIND_ORDER: KIND_ORDER,
        isImageFileName: isImageFileName,
        dueDisplay: dueDisplay,
        pageHtml: pageHtml,
        pp30CardHtml: pp30CardHtml,
        blockedHtml: blockedHtml,
        filesListHtml: filesListHtml,
        evidModalHtml: evidModalHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
