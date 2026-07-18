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
        'shadow_workpaper',
        'missing_doc_memo',
        'evidence_index',
    ];

    // 交付包页三键的工单状态词(engine.STATUS_*):review 态可签批/退回,archive=已冻结只读。
    var STATUS_REVIEW = 'review';
    var STATUS_FROZEN = 'archive';

    // 键二「导出分录到 Express」可用信号:工单有配平的影子分录(shadow_draft 是 order_detail
    // 对 gates.r5_shadow 的只读投影,无影子/未跑到 reconcile 时为 null)。
    function hasShadowEntries(detail) {
        var sd = (detail || {}).shadow_draft;
        return !!(sd && (sd.entries || []).length);
    }

    // 证据条目的文件名 → 能不能当票据照片直接用查看器打开(状态诚实:xlsx/pdf 等非图片
    // 文件不装模作样塞进 <img>,那只会碎图——铺满率≥0.8 的视觉验收血泪教训)。
    function isImageFileName(name) {
        return /\.(jpe?g|png|gif|webp|bmp)$/i.test(String(name || ''));
    }

    // 落盘名剥壳(2026-07-14 UI 记债 #1):file_name 是落盘 basename `{uuid}__原名{ext}`
    // (services/workorder/storage.py 命名惯例),证据链只该给人看原名——只剥显示层前缀,
    // 不碰存储路径/下载/manifest(冻结包字节不可变)。前缀非 uuid 形态(CLI 直喂真实路径等)
    // 原样返回,不误切用户文件名里巧合出现的 `__`。
    var _UUID_PREFIX = /^[0-9a-f]{8,32}__/;
    function displayFileName(name) {
        var s = String(name || '');
        return _UUID_PREFIX.test(s) ? s.replace(_UUID_PREFIX, '') : s;
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

    var pure = {
        KIND_ORDER: KIND_ORDER,
        isImageFileName: isImageFileName,
        displayFileName: displayFileName,
        dueDisplay: dueDisplay,
    };
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
    // needs 专指「缺料能补齐」(intake.py/reconcile.py 落的 intake_files/sales_summary 等,
    // 收料 tab 能解),blocked_reasons 是内部矛盾/闸报警(裁决在审核 tab 解,不该指去收料),
    // 故「去收料补」按钮只在 needs 非空时出现(2026-07-14 UI 记债 #3)。
    function blockedHtml(detail) {
        detail = detail || {};
        var needs = detail.needs || [];
        var reasons = [].concat(needs, detail.blocked_reasons || []);
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
            (needs.length
                ? '<button type="button" class="btn sm pri" data-action="pkg-go-intake">' +
                  esc(at('pkg_go_intake_btn')) +
                  '</button>'
                : reasons.length
                  ? '<button type="button" class="btn sm pri" data-action="pkg-retry">' +
                    esc(at('retry')) +
                    '</button>'
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
            '</div></div></div>'
        );
    }

    // ---- 三键出口区(M1-3KEY:确认待签 / 导出 Express / 退回工单) ----
    // 键一/键三 = review 态且未冻结才可点;冻结后禁用并提示「已冻结」。键二 = 有影子分录即可
    // 导(冻结单也能导,读侧派生)。签批成功后本键翻「已标记待签 · 签批人」态(同审核收件箱
    // 先例:用当前登录态展示名,不回读服务端)。状态诚实:按钮禁用带 title 说明为何不可点。
    function actionBtnHtml(action, labelKey, opts) {
        opts = opts || {};
        return (
            '<button class="btn' +
            (opts.pri ? ' pri' : '') +
            '" type="button" data-action="' +
            action +
            '"' +
            (opts.disabled ? ' disabled' : '') +
            (opts.titleKey ? ' title="' + esc(at(opts.titleKey)) + '"' : '') +
            '>' +
            esc(at(labelKey)) +
            '</button>'
        );
    }

    function actionsHtml(ctx) {
        var detail = ctx.detail || {};
        var frozen = detail.status === STATUS_FROZEN;
        var reviewable = detail.status === STATUS_REVIEW && !frozen;
        var entries = hasShadowEntries(detail);
        var frozenTitle = frozen ? 'pkg_frozen_hint' : null;

        // 引导链③(J-B):标记待签后按钮变灰,旁边给「去签批 →」出口——同工单页②同一个
        // 待我处理聚合队列(该单接下来的复核/冻结动作也在那里发生,不是原地死胡同)。
        var signBtn = ctx.signed
            ? '<button class="btn pri" type="button" disabled>' +
              esc(at('pkg_signed_done', { actor: ctx.signedActor || '' })) +
              '</button>' +
              '<button class="btn sm" type="button" data-action="pkg-goto-pool">' +
              esc(at('pkg_goto_signoff')) +
              '</button>'
            : actionBtnHtml('pkg-sign', 'pkg_sign_btn', {
                  pri: true,
                  disabled: !reviewable || ctx.signing,
                  titleKey: frozenTitle,
              });
        var exportBtn = actionBtnHtml('pkg-export', 'pkg_export_btn', {
            disabled: !entries || ctx.exporting,
            titleKey: entries ? null : 'pkg_export_no_entries',
        });
        var returnBtn = actionBtnHtml('pkg-return', 'pkg_return_btn', {
            disabled: !reviewable || ctx.returning,
            titleKey: frozenTitle,
        });

        var notice = ctx.notice
            ? '<p class="pkg-action-note ' +
              esc(ctx.notice.type) +
              '">' +
              esc(ctx.notice.text) +
              '</p>'
            : '';
        return (
            '<div class="panel"><div class="bd pkg-actions">' +
            '<div class="pkg-action-row">' +
            signBtn +
            exportBtn +
            returnBtn +
            '</div>' +
            notice +
            '</div></div>'
        );
    }

    // 空态指路(§6 死路批 · 2026-07-17,复测修订):按真实阻塞分叉——还有未判票时
    // 报表出不来的原因是「票没判完」,指去审核(带真数);没有未判票才指收料。判据与
    // 工单页 banner 同一份(reviewQueue.splitByDecision),不另造第二套。detail 还没
    // 到手(极端时序)不硬造链接。
    function emptyIntakeLinkHtml(detail) {
        var d = detail || {};
        if (d.workspace_client_id == null) return '';
        var undecided = root.AI.reviewQueue.splitByDecision(
            root.AI.reviewQueue.filterPurchaseQueue(d.flagged || [])
        ).undecided.length;
        var href = root.AI.router.buildClientHash(
            d.workspace_client_id,
            undecided > 0 ? 'review' : 'intake',
            d.period
        );
        var label = undecided > 0 ? at('wo_todo_review', { n: undecided }) : at('wo_goto_intake');
        return (
            '<p class="note" style="text-align:center;margin-top:8px"><a href="' +
            href +
            '">' +
            esc(label) +
            '</a></p>'
        );
    }

    // ---- 整页(交付物为空 → 复用既有 pkg_empty 四态空态,不重造一份文案) ----
    function pageHtml(ctx) {
        if (!ctx.deliverables || !ctx.deliverables.length) {
            var detail = ctx.detail || {};
            if ((detail.needs || []).length || (detail.blocked_reasons || []).length) {
                return blockedHtml(detail);
            }
            return (
                root.AI.state.emptyHtml({ title: at('pkg_empty_t'), sub: at('pkg_empty_s') }) +
                emptyIntakeLinkHtml(ctx.detail)
            );
        }
        var pp30Card = ctx.pp30
            ? pp30CardHtml(ctx.pp30.numbers || {}, ctx.calcOpen, (ctx.detail || {}).status)
            : blockedHtml(ctx.detail);
        return pp30Card + filesListHtml(ctx.deliverables, ctx.downloading) + actionsHtml(ctx);
    }

    // ---- 证据模态框(v4 .mask/.modal/.ev-row 1:1;点验回链:数字 → 证据行 → 原图,≤2 击) ----
    function evidRowHtml(item, selectedId) {
        var raw = item.file_name;
        if (!raw) {
            return (
                '<div class="ev-row novisual"><span>' +
                esc(at('pkg_evid_empty')) +
                '</span><span></span></div>'
            );
        }
        var name = displayFileName(raw);
        if (!isImageFileName(raw)) {
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
        displayFileName: displayFileName,
        dueDisplay: dueDisplay,
        pageHtml: pageHtml,
        pp30CardHtml: pp30CardHtml,
        blockedHtml: blockedHtml,
        filesListHtml: filesListHtml,
        actionsHtml: actionsHtml,
        hasShadowEntries: hasShadowEntries,
        evidModalHtml: evidModalHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
