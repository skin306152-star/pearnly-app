/*
 * Pearnly AI · ai-reports-render.js · 跨客户报表中心(EN-clients)纯逻辑 + HTML 拼装
 *
 * 报表本体(BS/PL/TB/影子底稿)不在本文件重拼——选到工单后直接调用既有
 * AI.financials.mount()/AI.shadow.mount()(两者早已接受任意容器参数,零改造直接复用,
 * 见 ai-financials.js/ai-shadow.js 顶注)。本文件只管:①客户+期间选择器 ②交付物下载
 * 清单(复用 ai-pkg.css 的 .pkg-files/.pfile 视觉语言,不拖 pkg 视图特有的电子签/推
 * Express/退回工单占位区——那是单张工单交付页的关切,报表中心是"查数"不是"走流程")。
 *
 * 上半段(pickOrderForPeriod/downloadableDeliverables)零 DOM/零 i18n 依赖,node
 * (tests/unit/test_ai_reports_pure.py)直接 require 断言;下半段依赖
 * at()/AI.state/AI.format,只在浏览器根挂载。
 */
(function (root) {
    'use strict';

    // 该客户该期间落地的工单(period 已在后端 listOrders 过滤,这里只挑第一条——
    // 同账套同期正常只会有一张月度工单,多条时不臆断哪张"更对",取最先建的)。
    function pickOrderForPeriod(orders, period) {
        var matches = (orders || []).filter(function (o) {
            return o.period === period;
        });
        return matches.length ? matches[0] : null;
    }

    // 只列真有文件的交付物(has_file),顺序沿用 W5 的 KIND_ORDER(不重抄一份顺序表)。
    function downloadableDeliverables(deliverables) {
        var byKind = {};
        (deliverables || []).forEach(function (d) {
            byKind[d.kind] = d;
        });
        return root && root.AI && root.AI.pkgRender
            ? root.AI.pkgRender.KIND_ORDER.filter(function (kind) {
                  return byKind[kind] && byKind[kind].has_file;
              })
            : [];
    }

    var pure = {
        pickOrderForPeriod: pickOrderForPeriod,
        downloadableDeliverables: downloadableDeliverables,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function pickerHtml(ctx) {
        var options =
            '<option value="">' +
            esc(at('reports_pick_client')) +
            '</option>' +
            (ctx.clients || [])
                .map(function (c) {
                    return (
                        '<option value="' +
                        esc(c.id) +
                        '"' +
                        (String(c.id) === String(ctx.clientId) ? ' selected' : '') +
                        '>' +
                        esc(c.name) +
                        '</option>'
                    );
                })
                .join('');
        return (
            '<div class="pr-setup-row">' +
            '<label class="pr-lb">' +
            esc(at('reports_client_label')) +
            '<select id="rptClientSel">' +
            options +
            '</select></label>' +
            '<label class="pr-lb">' +
            esc(at('reports_period_label')) +
            '<input id="rptPeriodInput" type="text" placeholder="2569-05" value="' +
            esc(ctx.period || '') +
            '" maxlength="7" /></label>' +
            '</div>'
        );
    }

    function goOpenOrderBtnHtml() {
        return (
            '<button type="button" class="btn pri" data-action="reports-open-order">' +
            esc(at('reports_open_order_btn')) +
            '</button>'
        );
    }

    // 该客户该期间没有工单——四语明说 + 去开单入口(状态诚实,不假装有数据)。
    function noOrderHtml() {
        return (
            AI.state.emptyHtml({
                title: at('reports_no_order_t'),
                sub: at('reports_no_order_s'),
            }) + goOpenOrderBtnHtml()
        );
    }

    function deliverableRowHtml(kind, row, downloading) {
        var label = root.AI.format.fieldLabel(kind);
        var busy = downloading === kind;
        return (
            '<span class="pfile">' +
            esc(label) +
            '<button type="button" data-action="reports-download" data-kind="' +
            esc(kind) +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(at('pkg_file_download')) +
            '</button></span>'
        );
    }

    function deliverablesPanelHtml(deliverables, downloading) {
        var kinds = downloadableDeliverables(deliverables);
        if (!kinds.length) return '';
        var byKind = {};
        (deliverables || []).forEach(function (d) {
            byKind[d.kind] = d;
        });
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('reports_downloads_title')) +
            '</h3></div><div class="bd"><div class="pkg-files">' +
            kinds
                .map(function (kind) {
                    return deliverableRowHtml(kind, byKind[kind], downloading);
                })
                .join('') +
            '</div></div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.reportsRender = {
        pickOrderForPeriod: pickOrderForPeriod,
        downloadableDeliverables: downloadableDeliverables,
        pickerHtml: pickerHtml,
        noOrderHtml: noOrderHtml,
        deliverablesPanelHtml: deliverablesPanelHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
