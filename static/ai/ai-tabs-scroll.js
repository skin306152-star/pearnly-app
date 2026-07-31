/*
 * Pearnly AI · ai-tabs-scroll.js · 横滚 tab 条的「当前项看得见」收口
 *
 * 窄视口下 .ctabs 自己横滚(ai-client.css N-5),代价是当前项可能一开始就在屏外:深链
 * 直接落在第 5 个 tab(#/client/9/profile)或泰语下的「ชุดส่งมอบ」,进页面看到的是一条
 * 没有当前项的 tab 条,还没有任何「能滑」的提示(2026-07-30 手机 390 实测:容器 79..375,
 * 当前项 315..404,右边被切掉 29px)。
 *
 * 两件事:① 把当前项推进可视区——只动 tab 条自己的 scrollLeft,不用 scrollIntoView
 * (那个会把整页一起滚,深链进来先跳一下);② 按实测滚动位置给还有内容的那一侧挂
 * tabs-more-l / tabs-more-r,CSS 据此画渐隐边——滚到底就摘掉,不给假的「还能滑」。
 *
 * 零依赖(不碰 AI.*、不碰 at()),排在任何用它的编排模块之前加载即可。
 */
(function (root) {
    'use strict';

    // 滚到位后当前项与边缘之间留的余量。贴边等于告诉人「到头了」,留一条缝才看得出还能滑;
    // 比 ai-client.css 里那道 22px 渐隐再宽一点,免得当前项自己被渐隐吃掉半边。
    var PEEK = 26;
    var WATCHED = '_tabsScrollWatched';

    // 纯函数:当前项要把 scrollLeft 推多少(>0 向右,<0 向左,0 = 已经完整露着)。
    // 两个入参是 getBoundingClientRect() 的结果,便于脱离 DOM 直接测边界。
    function edgeShift(barRect, btnRect, peek) {
        var pad = peek === undefined ? PEEK : peek;
        if (btnRect.right > barRect.right) return btnRect.right - barRect.right + pad;
        if (btnRect.left < barRect.left) return btnRect.left - barRect.left - pad;
        return 0;
    }

    // 1px 容差:滚到底时 scrollLeft 常落在分数上(390 实测量到过 .96),严格比会永远判成
    // 「还有内容」。
    function markEdges(el) {
        var rest = el.scrollWidth - el.clientWidth - el.scrollLeft;
        el.classList.toggle('tabs-more-l', el.scrollLeft > 1);
        el.classList.toggle('tabs-more-r', rest > 1);
    }

    // el 里 currentSelector 命中的那一项滚进可视区并刷新两侧提示。手指自己拖动时提示也要
    // 跟着翻,故首次调用顺带挂一次 scroll 监听(挂在元素上,重复 reveal 不会叠加)。
    function reveal(el, currentSelector) {
        if (!el) return;
        var btn = el.querySelector(currentSelector || 'button.on');
        if (btn) {
            el.scrollLeft += edgeShift(el.getBoundingClientRect(), btn.getBoundingClientRect());
        }
        markEdges(el);
        if (el[WATCHED]) return;
        el[WATCHED] = true;
        el.addEventListener('scroll', function () {
            markEdges(el);
        });
        // 自托管 Sarabun 是异步到的:首帧按回落字体算出来「一个都没被切」,字体一换 tab 条
        // 就宽了,当前项又跑到屏外(实测这一路是随机复现的)。字体落定后补算一次。
        if (typeof document !== 'undefined' && document.fonts && document.fonts.ready) {
            document.fonts.ready.then(function () {
                reveal(el, currentSelector);
            });
        }
    }

    var api = { reveal: reveal, edgeShift: edgeShift, PEEK: PEEK };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.tabsScroll = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
