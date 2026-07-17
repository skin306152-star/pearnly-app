/*
 * Pearnly AI · ai-review-progress.js · 裁决后进度轮询状态机纯函数(MC2-A3 · F10)
 *
 * 零 DOM/网络(同 ai-review-queue.js 先例):浏览器挂 window.AI.reviewProgress,node(测试)
 * 走 module.exports。裁决落库后引擎自驱重跑(review→running→…→review)是异步的,这里给
 * 指数退避 + 有限次数的排期,配合读模型把「刚被裁决的工单是否重跑落定」做成可脱管单测的判据。
 *
 * S3(2026-07-17)语义翻新:读模型现在连 running 工单一起下发(review.py _QUEUE_STATUSES
 * 含 running),「消失=在跑」的旧判据作废——落定改看 status 本身;封顶后由收件箱手动
 * 「刷新」钮兜底(已有)。
 */
(function (root) {
    'use strict';

    // ≈8 分钟封顶(1.5+3+6+12×37s):够慢工单一轮重跑,又防挂机标签页无限轮询。
    var MAX_ATTEMPTS = 40;
    var BASE_MS = 1500;
    var CAP_MS = 12000;

    // 第 attempt(0 起)次轮询的延时;超出有限次返回 null(调用方据此停轮询)。
    function nextDelayMs(attempt) {
        if (attempt >= MAX_ATTEMPTS) return null;
        return Math.min(BASE_MS * Math.pow(2, attempt), CAP_MS);
    }

    // 轮询前快照:队列内各工单的 updated_at(工单 id → 时间戳)。settled 只用键集
    // (哪些工单在被盯),时间戳留作调试对照。
    function baseline(queue) {
        var map = {};
        ((queue && queue.clients) || []).forEach(function (c) {
            (c.orders || []).forEach(function (o) {
                map[o.work_order_id] = o.updated_at;
            });
        });
        return map;
    }

    // 是否可以停止轮询:基线里每张工单都重现于队列,且**基线内**没有仍在 running 的单。
    // 只看基线不看全队列(simplify 收口):租户里一张与本次裁决无关的长跑单若被全队列
    // 扫描抓住,每个进 #/pool 的用户都会把退避预算烧到封顶——无关单不该绑架轮询;
    // 真死跑由后端心跳判死(180s)翻 stuck 收口,不靠前端多轮几发。
    function settled(queue, baselineMap) {
        var now = {};
        ((queue && queue.clients) || []).forEach(function (c) {
            (c.orders || []).forEach(function (o) {
                now[o.work_order_id] = o.status;
            });
        });
        return Object.keys(baselineMap || {}).every(function (id) {
            return Object.prototype.hasOwnProperty.call(now, id) && now[id] !== 'running';
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
