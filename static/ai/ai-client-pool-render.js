/*
 * Pearnly AI · ai-client-pool-render.js · D2-S8 客户池页(会计端)纯 HTML 拼装
 *
 * 零 DOM/网络依赖(同 ai-review-render.js 先例):浏览器挂 window.AI.clientPoolRender,
 * node(测试)走 module.exports 的纯函数子集(STATUS_ORDER/questionTypeLabelKey 等)。
 * 编排(拉取/推批/裁决提交)在 ai-client-pool.js。
 *
 * 状态词字面量('staged'/'pending'/'manual_review'/...)手工对齐
 * services/line_binding/client_pool_vocab.py——前端无法 import python,改词必须两处
 * 同步(同 ai-format.js STATUS_MAP 顶注惯例)。
 */
(function (root) {
    'use strict';

    var STATUS_ORDER = ['staged', 'pending', 'manual_review'];
    var STATUS_CHIP_KEY = {
        staged: 'pool_status_staged',
        pending: 'pool_status_pending',
        manual_review: 'pool_status_manual_review',
    };
    var STATUS_CHIP_CLASS = { staged: 'n', pending: 's', manual_review: 'w' };

    var QUESTION_TYPE_KEY = {
        direction: 'pool_qtype_direction',
        amount: 'pool_qtype_amount',
        drop: 'pool_qtype_drop',
        freeform: 'pool_qtype_freeform',
    };

    function questionTypeLabelKey(questionType) {
        return QUESTION_TYPE_KEY[questionType] || 'pool_qtype_freeform';
    }

    var pure = {
        STATUS_ORDER: STATUS_ORDER,
        STATUS_CHIP_KEY: STATUS_CHIP_KEY,
        STATUS_CHIP_CLASS: STATUS_CHIP_CLASS,
        questionTypeLabelKey: questionTypeLabelKey,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function statusChip(status) {
        return (
            '<span class="chip ' +
            (STATUS_CHIP_CLASS[status] || 'n') +
            '">' +
            esc(at(STATUS_CHIP_KEY[status] || status)) +
            '</span>'
        );
    }

    function questionMeta(q) {
        var p = q.question_payload || {};
        var bits = [p.supplier, p.invno].filter(Boolean);
        return bits.length ? esc(bits.join(' · ')) : '';
    }

    function staticRowHtml(q) {
        return (
            '<div class="cp-q-row"><span class="cp-q-type">' +
            esc(at(questionTypeLabelKey(q.question_type))) +
            '</span><span class="cp-q-meta">' +
            questionMeta(q) +
            '</span></div>'
        );
    }

    // manual_review 裁决动作行(方案 §4.1 映射表镜像):方向票 P/S/N;drop 票单键剔除;
    // amount 票内联改数;freeform 无结构信号,退化成 W3 同款 A(采纳)/E(改数)/X(剔除)。
    function decideActionsHtml(q, opts) {
        var qt = q.question_type;
        var busy = !!opts.busy;
        var editing = opts.editing;
        if (qt === 'direction') {
            return (
                '<div class="cp-q-actions">' +
                actionBtn(q.id, 'purchase', at('pool_decide_purchase'), busy) +
                actionBtn(q.id, 'sales', at('pool_decide_sales'), busy) +
                actionBtn(q.id, 'nontax', at('pool_decide_nontax'), busy) +
                '</div>'
            );
        }
        if (qt === 'drop') {
            return (
                '<div class="cp-q-actions">' +
                actionBtn(q.id, 'exclude', at('pool_decide_exclude'), busy) +
                '</div>'
            );
        }
        if (qt === 'amount' || editing) {
            return (
                '<div class="cp-q-actions cp-q-recalc">' +
                '<input class="cp-q-vat-input" type="text" inputmode="decimal" ' +
                'data-qid="' +
                q.id +
                '" value="' +
                esc(opts.editValue || '') +
                '">' +
                actionBtn(q.id, 'recalc', at('pool_decide_recalc'), busy) +
                '</div>'
            );
        }
        // freeform:同 W3 三键语义,退化到「采纳/改数/剔除」。
        return (
            '<div class="cp-q-actions">' +
            actionBtn(q.id, 'accept', at('pool_decide_accept'), busy) +
            actionBtn(q.id, 'edit', at('pool_decide_edit'), busy) +
            actionBtn(q.id, 'exclude', at('pool_decide_exclude'), busy) +
            '</div>'
        );
    }

    function actionBtn(qid, kind, label, busy) {
        return (
            '<button type="button" class="btn sm" data-action="cp-decide" data-qid="' +
            qid +
            '" data-kind="' +
            kind +
            '"' +
            (busy ? ' disabled' : '') +
            '>' +
            esc(label) +
            '</button>'
        );
    }

    function manualRowHtml(q, opts) {
        return (
            '<div class="cp-q-row cp-q-manual">' +
            '<div class="cp-q-head"><span class="cp-q-type">' +
            esc(at(questionTypeLabelKey(q.question_type))) +
            '</span><span class="cp-q-meta">' +
            questionMeta(q) +
            '</span></div>' +
            '<div class="cp-q-answer">' +
            esc(at('pool_answer_raw', { text: q.answer_raw || '' })) +
            '</div>' +
            decideActionsHtml(q, opts) +
            '</div>'
        );
    }

    function sectionHtml(status, questions, groupCtx) {
        if (!questions || !questions.length) return '';
        var rows =
            status === 'manual_review'
                ? questions
                      .map(function (q) {
                          return manualRowHtml(q, groupCtx.decide[q.id] || {});
                      })
                      .join('')
                : questions.map(staticRowHtml).join('');
        return (
            '<div class="cp-section" data-status="' +
            status +
            '">' +
            '<div class="cp-section-hd">' +
            statusChip(status) +
            '<span class="cp-section-n">' +
            questions.length +
            '</span></div>' +
            rows +
            '</div>'
        );
    }

    // ctx per group: { pushBusy, decide: { [qid]: {busy, editing, editValue} } }
    function groupHtml(group, ctx) {
        ctx = ctx || {};
        ctx.decide = ctx.decide || {}; // 首渲染(尚未交互过)时 ctxFor() 还没建过这个 group 的条目
        var staged = group.questions.staged || [];
        var banner = !group.bound
            ? '<div class="cp-banner">' + esc(at('pool_unbound_banner')) + '</div>'
            : '';
        var pushBtn = staged.length
            ? '<button type="button" class="btn sm pri" data-action="cp-push" data-ws="' +
              group.workspace_client_id +
              '"' +
              (ctx.pushBusy ? ' disabled' : '') +
              '>' +
              esc(ctx.pushBusy ? at('pool_pushing') : at('pool_push_batch')) +
              '</button>'
            : '';
        var sections = STATUS_ORDER.map(function (s) {
            return sectionHtml(s, group.questions[s], ctx);
        }).join('');
        var label = group.name || at('pool_client_label', { id: group.workspace_client_id });
        return (
            '<div class="panel cp-group">' +
            '<div class="hd"><h3>' +
            esc(label) +
            '<span class="note" style="margin-left:auto">' +
            pushBtn +
            '</span></h3></div>' +
            '<div class="bd">' +
            banner +
            sections +
            '</div></div>'
        );
    }

    function pageHtml(groups, ctxByClient) {
        if (!groups.length) {
            return root.AI.state.emptyHtml({
                title: at('pool_empty_t'),
                sub: at('pool_empty_s'),
            });
        }
        return groups
            .map(function (g) {
                return groupHtml(g, (ctxByClient || {})[g.workspace_client_id]);
            })
            .join('');
    }

    root.AI = root.AI || {};
    root.AI.clientPoolRender = {
        STATUS_ORDER: STATUS_ORDER,
        questionTypeLabelKey: questionTypeLabelKey,
        pageHtml: pageHtml,
        groupHtml: groupHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
