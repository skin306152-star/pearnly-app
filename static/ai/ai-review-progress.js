/*
 * Pearnly AI · ai-review-progress.js · 裁决后进度轮询状态机纯函数(MC2-A3 · F10)
 *
 * 零 DOM/网络(同 ai-review-queue.js 先例):浏览器挂 window.AI.reviewProgress,node(测试)
 * 走 module.exports。替掉 ai-review-inbox.js 的单发 2.5s 猜时器——裁决落库后引擎自驱重跑
 * (review→running→…→review)是异步的,单发定时器要么太早(还在 running)要么太晚。这里给
 * 指数退避 + 有限次数的排期,配合「队列里 running 工单会消失、跑完回 review 才重现」的读模型
 * 语义(review_queue 只收 review/stuck),把「刚被裁决的工单是否重跑落定」做成可脱管单测的判据。
 */
(function (root) {
    'use strict';

    var MAX_ATTEMPTS = 6; // 有限次:1.5+3+6+12+12+12 ≈ 46s 封顶,够一轮重跑落回 review。
    var BASE_MS = 1500;
    var CAP_MS = 12000;

    // 第 attempt(0 起)次轮询的延时;超出有限次返回 null(调用方据此停轮询)。
    function nextDelayMs(attempt) {
        if (attempt >= MAX_ATTEMPTS) return null;
        return Math.min(BASE_MS * Math.pow(2, attempt), CAP_MS);
    }

    // 轮询前快照:队列内各工单的 updated_at(工单 id → 时间戳)。重跑会改 updated_at,据此认落定。
    function baseline(queue) {
        var map = {};
        ((queue && queue.clients) || []).forEach(function (c) {
            (c.orders || []).forEach(function (o) {
                map[o.work_order_id] = o.updated_at;
            });
        });
        return map;
    }

    // 是否可以停止轮询:基线里每张工单都「落定」——要么重新出现在队列(重跑跑完回了 review/stuck),
    // 要么其 updated_at 已推进(状态动过)。仍缺席(还在 running,队列读模型看不到)则未落定,继续退避。
    function settled(queue, baselineMap) {
        var now = {};
        ((queue && queue.clients) || []).forEach(function (c) {
            (c.orders || []).forEach(function (o) {
                now[o.work_order_id] = o.updated_at;
            });
        });
        return Object.keys(baselineMap || {}).every(function (id) {
            return Object.prototype.hasOwnProperty.call(now, id);
        });
    }

    var api = {
        MAX_ATTEMPTS: MAX_ATTEMPTS,
        nextDelayMs: nextDelayMs,
        baseline: baseline,
        settled: settled,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.reviewProgress = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
