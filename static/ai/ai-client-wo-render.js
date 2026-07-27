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

    // 「后台停住了」的单一判据:stuck 且后端报了 blocked_reasons(缺料造成的 stuck 不报
    // reasons,那是等人补料不是跑挂了)。银行对账/影子底稿两区拿它把「还没跑到」和「跑挂了」
    // 两种 null 分开——与状态头那条 systemBlockedHtml 同一判据,不另造第二套认定。
    function engineStalled(d) {
        return (d || {}).status === 'stuck' && ((d || {}).blocked_reasons || []).length > 0;
    }

    // 影子底稿 / 报表包这两区的坏法有两种,说的话也得是两种:
    //   stalled  = 引擎整体停住(engineStalled),已完成的数据还在,可以从断点重跑;
    //   degraded = 那一步自己跑挂了只留残影(后端 *_state='degraded'),工单照样走到 review,
    //              status 里一点痕迹都没有 —— 只认 stuck 的话这里会一直说「不用管它,会自动
    //              生成」,而它不会再自己好。degraded 优先:它是更具体的那个诊断。
    function sectionFault(d, stateKey) {
        if ((d || {})[stateKey] === 'degraded') return 'degraded';
        return engineStalled(d) ? 'stalled' : '';
    }

    var pure = {
        guidanceCount: guidanceCount,
        engineStalled: engineStalled,
        sectionFault: sectionFault,
    };
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

    // 审核 / 交付包 tab 在本客户还没有工单时的空态。两个 tab 共用一份:它们的先决条件是
    // 同一个(工单),分头写迟早漂。旧文案「请先在其它入口开单」既不点名也不给按钮,而那个
    // 入口就是紧挨着的「工单」tab —— 这里点名 tab 名并直接给跳过去的按钮。
    // 不带 period:本客户一张工单都没有,没有「当期」可带,落到 ai-client.js 的默认选期。
    function noOrderEmptyHtml(clientId) {
        return root.AI.state.emptyHtml({
            title: at('emp_wo_none_t'),
            sub: at('emp_wo_none_s'),
            actionLabel: at('emp_wo_none_btn'),
            actionHref: root.AI.router.buildClientHash(clientId, 'wo'),
        });
    }

    // 后台停住了的出路。原因码走 AI.format 的四语映射(此前 join('、') 原样上屏,用户读到的是
    // "insufficient_balance" 这种生标识符);余额不足另给「去充值」并降级重试按钮 —— 没充值的
    // 重试 100% 立刻再 stuck(classify 开跑前 wallet.exhausted() 就返),把它摆成唯一出路等于
    // 造一个死循环。配额/内部成本封顶两个码则相反:重试就是全部出路,不该出充值按钮。
    function systemBlockedHtml(d, guideCount) {
        var reasons = d.blocked_reasons || [];
        if (d.status !== 'stuck' || guideCount > 0 || !reasons.length) return '';
        var fmt = root.AI.format;
        var needsTopup = fmt.blockedNeedsTopup(reasons);
        var topup = needsTopup
            ? '<a class="btn sm pri" data-action="wo-topup" href="' +
              esc(root.AI.failRender.TOPUP_HASH) +
              '">' +
              esc(at('fail_topup_btn')) +
              '</a>'
            : '';
        return (
            '<div class="wo-guide"><p class="rv-blocked">' +
            esc(
                at(needsTopup ? 'system_blocked_topup' : 'system_blocked_detail', {
                    list: fmt.blockedReasonList(reasons),
                })
            ) +
            '</p>' +
            topup +
            '<button type="button" class="btn sm' +
            (needsTopup ? '' : ' pri') +
            '" data-action="wo-retry-stuck">' +
            esc(at('retry')) +
            '</button></div>'
        );
    }

    function woSummaryHtml(d, clientId) {
        var cells = cellsHtml(d);
        var guideCount = guidanceCount(d, root.AI.reviewQueue);
        var needs = (d.needs || [])
            .map(function (n) {
                return '<div class="ni">' + esc(root.AI.format.fieldLabel(n)) + '</div>';
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
        var progress =
            d.status === 'running' || d.status === 'stuck' ? d.progress || d.bank_progress : null;
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
            guidanceHtml(d, clientId, guideCount) +
            systemBlockedHtml(d, guideCount) +
            collectingHintHtml(d, clientId) +
            '</div></div>'
        );
    }

    root.AI = root.AI || {};
    root.AI.clientWoRender = {
        guidanceCount: guidanceCount,
        engineStalled: engineStalled,
        sectionFault: sectionFault,
        woSummaryHtml: woSummaryHtml,
        noOrderEmptyHtml: noOrderEmptyHtml,
    };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
