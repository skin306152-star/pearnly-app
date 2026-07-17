/*
 * Pearnly AI · ai-client-wo-render.js · 工单页状态头(顶部摘要)纯拼装
 *
 * 拆自 ai-client.js(S2 状态头六修落地后破单文件 500 行红线)——同 ai-recon-render.js
 * 先例:上半段 guidanceCount 零 DOM/零 i18n 依赖(reviewQueue 作参数注入),node
 * (tests/unit/test_ai_pure_modules.py)直接 require 断言;下半段 HTML 拼装依赖
 * at()/AI.state/AI.format/AI.router,只在浏览器根挂载。挂载/轮询编排仍在
 * ai-client.js(woSummaryPanel 重画调这里),排在本文件之后加载。
 */
(function (root) {
    'use strict';

    // 引导链②(J-B):stuck 单有真待裁决票、或已到 review 待签批,工单页给出口——N 用
    // 真数字,不臆造。stuck 与审核页同一份已判判据(reviewQueue.splitByDecision,不重造
    // 第二套认定),只数未判票:裁决落库后轮询自然递减(S2 §1:此前把已判票也数进去,
    // 裁决完了工单还在喊旧数)。review(TERMINAL_STATUS,待人审签批)本身就是一件事,记 1。
    function guidanceCount(d, reviewQueue) {
        if (d.status === 'stuck') {
            return reviewQueue.splitByDecision(reviewQueue.filterPurchaseQueue(d.flagged || []))
                .undecided.length;
        }
        if (d.status === 'review') return 1;
        return 0;
    }

    var pure = { guidanceCount: guidanceCount };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;

    // ===== 以下为浏览器 HTML 拼装(依赖 at()/AI.state/AI.format/AI.router,node 不调用)=====
    if (!root) return;

    function esc(s) {
        return root.AI.state.esc(s);
    }

    function cellsHtml(d) {
        return Object.keys(d.numbers || {})
            .map(function (k) {
                var v = (d.numbers || {})[k];
                // N-3 修复:prior_period_check 是对象({status:...}),不能走通用
                // esc(v) 路径(会字面显示 [object Object])——单独映射成人话文案。
                var display =
                    k === 'prior_period_check'
                        ? root.AI.format.priorPeriodCheckText(v)
                        : /vat|amount|due/.test(k)
                          ? root.AI.format.money(v)
                          : esc(v);
                return (
                    '<div class="cell"><div class="lb">' +
                    esc(root.AI.format.fieldLabel(k)) +
                    '</div><div class="v num">' +
                    display +
                    '</div></div>'
                );
            })
            .join('');
    }

    // 待办出口分叉(S2 §1-补):有未判票=去本客户审核 tab 就地判(带期,判完回来还在
    // 同一单);review=轮到签批,维持跳「待我处理」聚合页——签批动作只在那里有。
    function guidanceHtml(d, clientId, guideCount) {
        if (d.status === 'review') {
            return (
                '<div class="wo-guide"><button type="button" class="btn sm" data-action="wo-goto-pool">' +
                esc(at('wo_todo_banner', { n: guideCount })) +
                '</button></div>'
            );
        }
        if (guideCount > 0) {
            return (
                '<div class="wo-guide"><a class="btn sm" data-action="wo-goto-review" href="' +
                esc(root.AI.router.buildClientHash(clientId, 'review', d.period)) +
                '">' +
                esc(at('wo_todo_review', { n: guideCount })) +
                '</a></div>'
            );
        }
        return '';
    }

    // collecting 不再空壳(S2 §5 · 2026-07-17 真跑实测):还没资料时指路收料 tab,
    // hash 同 tab 切换的构造方式(带当期,过去回来还在同一期)。
    function collectingHintHtml(d, clientId) {
        if (d.status !== 'collecting') return '';
        return (
            '<div class="wo-guide">' +
            esc(at('wo_collecting_hint')) +
            ' <a href="' +
            esc(root.AI.router.buildClientHash(clientId, 'intake', d.period)) +
            '">' +
            esc(at('wo_goto_intake')) +
            '</a></div>'
        );
    }

    function woSummaryHtml(d, clientId) {
        var cells = cellsHtml(d);
        var needs = (d.needs || [])
            .map(function (n) {
                return '<div class="ni">' + esc(n) + '</div>';
            })
            .join('');
        // 步骤位只对「AI 在跑」有意义,人审终态甩流程步位=状态打架(2026-07-17 真跑实测)。
        var stepNote =
            d.status === 'running'
                ? '<span class="note">' +
                  esc(at('wo_step')) +
                  ': ' +
                  esc(root.AI.format.stepLabel(d.current_step)) +
                  '</span>'
                : '';
        // 进度行同理只对 AI 在跑有意义,人审终态挂「0/10」=没人在读却像卡死(S2 §3-补)。
        var progress = d.status === 'running' ? d.progress || d.bank_progress : null;
        // running 期间逐件心跳续约刷 updated_at(=last_active_at),5s 轮询全量重画自然
        // 刷新,不加计时器;后端没给就不拼,不臆造「活着」。
        var lastActive =
            d.status === 'running' && d.last_active_at
                ? ' · ' +
                  at('wo_last_active', {
                      t: root.AI.format.relAgo(d.last_active_at, Date.now()),
                  })
                : '';
        var progressLine = progress
            ? '<p class="wo-progress">' +
              esc(root.AI.format.progressLabel(progress) + lastActive) +
              '</p>'
            : '';
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(at('tab_wo')) +
            ' ' +
            root.AI.format.chipHtml(d.status, d) +
            stepNote +
            '</h3></div><div class="bd">' +
            progressLine +
            (cells ? '<div class="wosum">' + cells + '</div>' : '') +
            (needs ? '<div class="needs-list">' + needs + '</div>' : '') +
            guidanceHtml(d, clientId, guidanceCount(d, root.AI.reviewQueue)) +
            collectingHintHtml(d, clientId) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.clientWoRender = {
        guidanceCount: guidanceCount,
        woSummaryHtml: woSummaryHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
