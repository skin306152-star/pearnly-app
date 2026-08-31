/*
 * Pearnly AI · ai-recon-render.js · 银行对账(E2)四清单的纯逻辑 + HTML 拼装
 *
 * 上半段(hasGap/diffState/listPhase)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_recon_pure.py)直接 require 断言;下半段 HTML 拼装依赖
 * at()/AI.state/AI.format/AI.viewer,只在浏览器根挂载——同 ai-pkg-render.js 的
 * 双段先例。真正的挂载/交互(折叠开关/查看器模态)在
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

    // 某张清单为空时,到底是「没料可对」还是「对完了确实没有这一类」。四张单全空 = 对账
    // 引擎跑完但手上什么都没有(对账单没传/传了没解析出流水行),那是 idle,该指路去收料;
    // 只要有任意一张单有行,本单的空就是真结论,该说清为什么空。
    // 这里不产出 error:bankRecon 非 null 就意味着对账步已成功产出(见
    // services/workorder/api.py::_bank_recon —— 没跑到/降级一律给 None),
    // 失败态由 pageHtml 的 bankRecon==null 分支按工单是否卡死来判。
    function listPhase(bankRecon) {
        var r = bankRecon || {};
        var total =
            (r.auto_matched || []).length +
            (r.review || []).length +
            (r.missing_invoice || []).length +
            (r.unmatched_invoice || []).length;
        return total === 0 ? 'idle' : 'empty';
    }

    var pure = {
        hasGap: hasGap,
        diffState: diffState,
        listPhase: listPhase,
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

    // 三张带流水行的清单(auto/review/missing)共用外壳:流水行 + 差异化内层。
    function rowShell(txText, restHtml) {
        return (
            '<div class="brx-row"><span class="brx-tx">' + txText + '</span>' + restHtml + '</div>'
        );
    }

    function autoRowHtml(entry) {
        // auto_matched 记录自带 candidate_id/score/reason,直接喂 candidateLineHtml。
        return rowShell(txLineText(entry.tx), candidateLineHtml(entry));
    }

    function reviewRowHtml(entry) {
        var cands = (entry.candidates || []).map(candidateLineHtml).join('');
        return rowShell(txLineText(entry.tx), '<div class="brx-cands">' + cands + '</div>');
    }

    function missingRowHtml(entry) {
        return rowShell(
            txLineText(entry),
            '<div class="brx-actions">' + viewBtn('bank', entry._bankItemId) + '</div>'
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

    // 单张清单空掉时的「为什么空」。此前四张单各只有一句「暂无 X」,会计分不清是没跑、
    // 没料还是真没有;这里给的是跑完之后的真结论,所以一律 empty 相位——「什么都没得对」
    // 那种情况整块面板只说一次(见 pageHtml 的 idle 分支),不在四张单里各喊一遍。
    function sectionEmptyBody(kind, emptyKey) {
        return root.AI.state.sectionEmptyHtml({
            phase: 'empty',
            title: at(emptyKey),
            sub: at('emp_brx_' + kind + '_s'),
        });
    }

    function sectionHtml(kind, titleKey, count, open, rowsHtml, emptyKey) {
        var body = count === 0 ? sectionEmptyBody(kind, emptyKey) : rowsHtml;
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

    // ui: {open:{auto,review,missing,unmatched}}
    function pageHtml(bankRecon, ui, clientId) {
        if (!bankRecon) {
            // 后端把「还没跑到对账」与「跑挂了降级」都收敛成 null(见 api.py::_bank_recon),
            // 光凭 null 分不出来——工单卡死(stuck 且后台报了 blocked_reasons)才是跑挂了,
            // 那句「不用管它,跑到对账会自动生成」在卡死时是假话:它不会自己好。
            if (ui && ui.stalled) {
                return (
                    '<div class="panel"><div class="hd"><h3>' +
                    esc(at('brx_title')) +
                    '</h3></div><div class="bd">' +
                    root.AI.state.sectionEmptyHtml({
                        phase: 'error',
                        title: at('emp_brx_stalled_t'),
                        sub: at('emp_brx_stalled_s'),
                        retryLabel: at('retry'),
                        // 复用工单页状态头那颗断点重试(cv-wo 上的点击委托覆盖本区),
                        // 不为这一个空态另绑一套监听、更不另造第二条重试路径。
                        retryName: 'wo-retry-stuck',
                    }) +
                    '</div></div>'
                );
            }
            // 死卡指路(§6 死路批 · 2026-07-17):文案说了「传对账单」就得给入口。period
            // 没有进到本渲染层(mount 只带 clientId),深链退化不带期 → ai-client.js 落最新期。
            var intakeLink =
                clientId != null
                    ? '<p class="note" style="text-align:center;margin-top:8px"><a href="' +
                      esc(root.AI.router.buildClientHash(clientId, 'intake')) +
                      '">' +
                      esc(at('wo_goto_intake')) +
                      '</a></p>'
                    : '';
            return (
                '<div class="panel"><div class="hd"><h3>' +
                esc(at('brx_title')) +
                '</h3></div><div class="bd">' +
                root.AI.state.emptyHtml({
                    title: at('brx_disabled_t'),
                    sub: at('brx_disabled_s'),
                }) +
                intakeLink +
                '</div></div>'
            );
        }
        // 四张单全空 = 对账跑完但手上什么都没有。此时四个空折叠区各喊一遍「没料」纯属噪音,
        // 整块面板只说一次并给去收料的出口(成熟做法:一个面板一个空态,不按子清单铺开)。
        if (listPhase(bankRecon) === 'idle') {
            return (
                '<div class="panel"><div class="hd"><h3>' +
                esc(at('brx_title')) +
                '</h3></div><div class="bd">' +
                root.AI.state.sectionEmptyHtml({
                    phase: 'idle',
                    title: at('emp_brx_nodata_t'),
                    sub: at('emp_brx_nodata_s'),
                    actionLabel: clientId != null ? at('wo_goto_intake') : '',
                    actionHref:
                        clientId != null ? root.AI.router.buildClientHash(clientId, 'intake') : '',
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
            .map(function (entry) {
                return missingRowHtml(Object.assign({ _bankItemId: bankItemId }, entry));
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
        pageHtml: pageHtml,
        viewModalHtml: viewModalHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
