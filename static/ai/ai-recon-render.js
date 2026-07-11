/*
 * Pearnly AI · ai-recon-render.js · 银行对账(E2)四清单的纯逻辑 + HTML 拼装
 *
 * 上半段(hasGap/diffState/buildMissingStagePayload)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_recon_pure.py)直接 require 断言;下半段 HTML 拼装依赖
 * at()/AI.state/AI.format/AI.viewer,只在浏览器根挂载——同 ai-pkg-render.js 的
 * 双段先例。真正的挂载/交互(折叠开关/查看器模态/推 LINE 待问网络调用)在
 * ai-recon.js,排在本文件之后加载。
 *
 * 数据源:services/workorder/api.py::order_detail 的 bank_recon 字段,原样透传
 * services/recon/workorder_recon_adapter.py::ReconResult.as_gate_payload 的四清单
 * (auto_matched/review/missing_invoice/unmatched_invoice/diff)——本文件只读不改
 * 其形状,禁区(E1 引擎)一行不碰。
 */
(function (root) {
    'use strict';

    // 有实质差异(缺票或未达非空)才算"需要会计过目",review 队列本身不算差异——
    // 那是待裁决而非对不平,折叠头用不同颜色区分(见 foldChip)。
    function hasGap(bankRecon) {
        var r = bankRecon || {};
        return (r.missing_invoice || []).length > 0 || (r.unmatched_invoice || []).length > 0;
    }

    // 净差展示态:{ok, net} · ok=true 时 net 一律置 '0'(全清爽,不必纠结格式化后的
    // '0.00'/'0' 差异——那是 Decimal 输入精度的副作用,不是真差异)。
    function diffState(bankRecon) {
        var r = bankRecon || {};
        var ok = !hasGap(r);
        return { ok: ok, net: ok ? '0' : (r.diff || {}).net || '0' };
    }

    // 缺票行(有流水无票)→ 推 LINE 待问的 payload。item_id 锚在银行流水件本身
    // (缺票行没有对应的票据 item,问的就是"这张流水缺哪张票"——见 ai-recon.js/
    // services/workorder/api.py::_bank_recon 顶注)。question_type 固定 freeform:
    // 现有四型(direction/amount/drop)语义都对不上"帮我们找这张流水的收据"这句问话,
    // note 由调用方(ai-recon.js)用 at() 拼好整句传入,本函数只负责打包,不夹带文案。
    function buildMissingStagePayload(bankItemId, note) {
        if (!bankItemId) return null;
        return {
            item_id: bankItemId,
            question_type: 'freeform',
            payload: { supplier: '', invno: '', amount: '', note: note || '' },
        };
    }

    var pure = {
        hasGap: hasGap,
        diffState: diffState,
        buildMissingStagePayload: buildMissingStagePayload,
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
    function txDirLabel(direction) {
        return direction === 'IN' ? at('brx_tx_in') : at('brx_tx_out');
    }
    function txLineText(tx) {
        tx = tx || {};
        return (
            (tx.tx_date || '—') +
            ' · ' +
            esc(txDirLabel(tx.direction)) +
            ' · ' +
            money(tx.amount) +
            (tx.description ? ' · ' + esc(tx.description) : '')
        );
    }

    function viewBtn(kind, key, labelKey) {
        if (!key) return '';
        return (
            '<button type="button" class="btn sm brx-view" data-action="brx-view" data-kind="' +
            esc(kind) +
            '" data-key="' +
            esc(key) +
            '">' +
            esc(at(labelKey || 'pkg_evid_open')) +
            '</button>'
        );
    }

    function candidateLineHtml(c) {
        return (
            '<div class="brx-cand">' +
            viewBtn('invoice', c.candidate_id) +
            '<span class="brx-score">' +
            esc(at('brx_score_label')) +
            ' ' +
            (c.score != null ? c.score : '—') +
            '</span>' +
            (c.reason ? '<span class="brx-reason">' + esc(c.reason) + '</span>' : '') +
            '</div>'
        );
    }

    function autoRowHtml(entry) {
        return (
            '<div class="brx-row">' +
            '<span class="brx-tx">' +
            txLineText(entry.tx) +
            '</span>' +
            candidateLineHtml({
                candidate_id: entry.candidate_id,
                score: entry.score,
                reason: entry.reason,
            }) +
            '</div>'
        );
    }

    function reviewRowHtml(entry) {
        var cands = (entry.candidates || []).map(candidateLineHtml).join('');
        return (
            '<div class="brx-row">' +
            '<span class="brx-tx">' +
            txLineText(entry.tx) +
            '</span>' +
            '<div class="brx-cands">' +
            cands +
            '</div>' +
            '</div>'
        );
    }

    // missingState: {busy, done, errKey} | undefined(按行 idx 独立持有,ai-recon.js 状态机)。
    function missingRowHtml(entry, idx, missingState) {
        missingState = missingState || {};
        var action;
        if (missingState.done) {
            action = '<span class="chip s">' + esc(at('rv_pool_done')) + '</span>';
        } else {
            action =
                '<button type="button" class="btn sm" data-action="brx-stage" data-idx="' +
                idx +
                '"' +
                (missingState.busy ? ' disabled' : '') +
                '>' +
                esc(missingState.busy ? at('brx_pool_busy') : at('rv_key_pool')) +
                '</button>';
        }
        var err = missingState.errKey
            ? '<div class="brx-err">' + esc(at(missingState.errKey)) + '</div>'
            : '';
        return (
            '<div class="brx-row">' +
            '<span class="brx-tx">' +
            txLineText(entry) +
            '</span>' +
            '<div class="brx-actions">' +
            viewBtn('bank', entry._bankItemId) +
            action +
            '</div>' +
            err +
            '</div>'
        );
    }

    function unmatchedRowHtml(entry, clientId) {
        var vendor = entry.vendor ? esc(entry.vendor) : '—';
        var invno = entry.invoice_no ? esc(entry.invoice_no) : '—';
        return (
            '<div class="brx-row">' +
            '<span class="brx-tx">' +
            vendor +
            ' · ' +
            invno +
            ' · ' +
            money(entry.amount) +
            '</span>' +
            '<div class="brx-actions">' +
            viewBtn('invoice', entry.candidate_id) +
            '</div>' +
            '<p class="brx-hint">' +
            esc(at('brx_unmatched_hint')) +
            ' · <a href="' +
            esc(root.AI.router.buildClientHash(clientId, 'intake')) +
            '">' +
            esc(at('brx_unmatched_goto')) +
            '</a></p>' +
            '</div>'
        );
    }

    // 折叠头:kind → chip 颜色(auto/review 用中性/sage,missing/unmatched 有内容时用 warn——
    // 这两张才是真正"需要会计去补"的差异清单)。
    var _WARN_KINDS = { missing: true, unmatched: true };
    function foldChip(kind, count) {
        if (count === 0) return '<span class="chip n">0</span>';
        if (_WARN_KINDS[kind]) return '<span class="chip w">' + count + '</span>';
        return '<span class="chip s">' + count + '</span>';
    }

    function sectionHtml(kind, titleKey, count, open, rowsHtml, emptyKey) {
        var body = count === 0 ? '<p class="brx-empty">' + esc(at(emptyKey)) + '</p>' : rowsHtml;
        return (
            '<div class="brx-section' +
            (open ? ' on' : '') +
            '" data-brx-kind="' +
            kind +
            '">' +
            '<button type="button" class="brx-fold" data-action="brx-fold" data-kind="' +
            kind +
            '">' +
            '<span>' +
            esc(at(titleKey, { n: count })) +
            '</span>' +
            foldChip(kind, count) +
            '<span class="brx-caret">' +
            (open ? esc(at('brx_collapse')) : esc(at('brx_expand'))) +
            '</span>' +
            '</button>' +
            '<div class="brx-body">' +
            body +
            '</div>' +
            '</div>'
        );
    }

    // ui: {open:{auto,review,missing,unmatched}, missing:{idx:{busy,done,errKey}}}
    function pageHtml(bankRecon, ui, clientId) {
        if (!bankRecon) {
            return (
                '<div class="panel"><div class="hd"><h3>' +
                esc(at('brx_title')) +
                '</h3></div><div class="bd">' +
                root.AI.state.emptyHtml({
                    title: at('brx_disabled_t'),
                    sub: at('brx_disabled_s'),
                }) +
                '</div></div>'
            );
        }
        var auto = bankRecon.auto_matched || [];
        var review = bankRecon.review || [];
        var missing = bankRecon.missing_invoice || [];
        var unmatched = bankRecon.unmatched_invoice || [];
        var diff = diffState(bankRecon);
        var bankItemId = (bankRecon.bank_item_ids || [])[0] || null;

        var missingRows = missing
            .map(function (entry, idx) {
                return missingRowHtml(
                    Object.assign({ _bankItemId: bankItemId }, entry),
                    idx,
                    (ui.missing || {})[idx]
                );
            })
            .join('');

        var diffChip = diff.ok
            ? '<span class="chip g">' + esc(at('brx_ok_chip')) + '</span>'
            : '<span class="chip w">' + esc(at('brx_diff_chip')) + '</span>';

        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('brx_title')) +
            ' ' +
            diffChip +
            '<span class="note" style="margin-left:auto">' +
            esc(at('brx_diff_net', { net: money(diff.net) })) +
            '</span></h3></div><div class="bd brx-body-wrap">' +
            sectionHtml(
                'auto',
                'brx_auto_title',
                auto.length,
                ui.open.auto,
                auto.map(autoRowHtml).join(''),
                'brx_auto_empty'
            ) +
            sectionHtml(
                'review',
                'brx_review_title',
                review.length,
                ui.open.review,
                review.map(reviewRowHtml).join(''),
                'brx_review_empty'
            ) +
            sectionHtml(
                'missing',
                'brx_missing_title',
                missing.length,
                ui.open.missing,
                missingRows,
                'brx_missing_empty'
            ) +
            sectionHtml(
                'unmatched',
                'brx_unmatched_title',
                unmatched.length,
                ui.open.unmatched,
                unmatched
                    .map(function (e) {
                        return unmatchedRowHtml(e, clientId);
                    })
                    .join(''),
                'brx_unmatched_empty'
            ) +
            '</div></div>'
        );
    }

    // 单窗格原图模态(v4 .pkg-mask/.pkg-modal 复用,单张聚焦不需要 pkg 那种列表+查看器
    // 分栏——点哪行看哪行,同 ai-review.js 单卡查看器的取舍)。
    function viewModalHtml(view) {
        var titleKey = view.kind === 'bank' ? 'brx_view_title_bank' : 'brx_view_title_invoice';
        return (
            '<div class="pkg-mask on brx-view-mask" id="brxViewMask">' +
            '<div class="pkg-modal brx-view-modal">' +
            '<div class="mh"><div><h3>' +
            esc(at(titleKey)) +
            '</h3></div>' +
            '<button class="mclose" type="button" data-action="brx-view-close" aria-label="' +
            esc(at('pkg_evid_close')) +
            '">&times;</button></div>' +
            '<div class="mb brx-view-mb"><div class="pkg-evid-view" id="brxViewPane">' +
            root.AI.viewer.imageViewerHtml({
                hint: at('imgv_hint'),
                noimg: at('imgv_noimg'),
                loading: at('imgv_loading'),
            }) +
            '</div></div>' +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.reconRender = {
        hasGap: hasGap,
        diffState: diffState,
        buildMissingStagePayload: buildMissingStagePayload,
        pageHtml: pageHtml,
        viewModalHtml: viewModalHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
