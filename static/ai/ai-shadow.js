/*
 * Pearnly AI · ai-shadow.js · 影子底稿(F3)区块编排:折叠开关挂载
 *
 * 挂在工单详情(wo 视图)银行对账区之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().shadow_draft(不再发第二次网络请求)。只读区,唯一交互是三个分区的
 * 折叠开关——同 ai-recon.js 的折叠机制,少了原图模态/推 LINE 待问(那是银行对账特有的
 * 交互;影子底稿这版 MVP 不做改配,改配落真账本是批次 M 的事)。
 */
(function () {
    'use strict';

    var S = null;

    function freshState(shadowDraft) {
        return {
            shadowDraft: shadowDraft,
            // 三分区默认展开——影子底稿数据量通常不大(一期工单几十条分录内),且本身
            // 就是会计要核对的主内容,折叠反而增加点击成本(同 E2 auto 默认收起取舍相反:
            // 那是"已处理好不占版面",这里是"打开就是要看的东西")。
            open: { entries: true, accounts: true, gl: true },
        };
    }

    function render(container) {
        if (!S) return;
        container.innerHTML = AI.shadowRender.pageHtml(S.shadowDraft, S);
    }

    function toggleFold(kind, container) {
        if (!(kind in S.open)) return;
        S.open[kind] = !S.open[kind];
        render(container);
    }

    function onClick(e, container) {
        var el = e.target.closest('[data-action="sdw-fold"]');
        if (!el) return;
        toggleFold(el.getAttribute('data-kind'), container);
    }

    // container 由调用方(ai-client.js renderWo)传入,shadowDraft 是已取到的 order_detail
    // 字段——同一次 getOrder() 复用,不重复发请求。
    function mount(shadowDraft, container) {
        S = freshState(shadowDraft);
        container.onclick = function (e) {
            onClick(e, container);
        };
        render(container);
    }

    window.AI = window.AI || {};
    window.AI.shadow = { mount: mount };
})();
