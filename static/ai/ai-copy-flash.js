/*
 * Pearnly AI · ai-copy-flash.js · 「复制 → 按钮闪一下『已复制』→ 还原原文」的共享出口
 *
 * 管家红条尾巴上的错误码复制(ai-steward-actions.js)与充值弹窗的收款账号复制
 * (ai-billing.js)此前各写一份逐字相同的 flash():点下去才抓 textContent 当原文,
 * 1.5 秒内连点第二次抓到的已经是「已复制」,还原就还原成「已复制」——按钮从此再也
 * 变不回来(2026-07-30 真浏览器走查实测)。原文只在第一次闪时记一次,连点只顺延计时器。
 *
 * 零依赖:不碰 AI.*、不碰 at(),剪贴板内容与「已复制」文案都由调用方给。
 * node(tests/unit/test_ai_copy_flash.py)注入假 window + 假按钮直接跑,不需要浏览器。
 */
(function (root) {
    'use strict';

    var HOLD_MS = 1500;
    // 挂在按钮元素上,不进模块级 Map:按钮被重渲染换掉时状态跟着一起没,不留悬挂条目。
    var PREV = '_copyFlashPrev';
    var TIMER = '_copyFlashTimer';

    // win 可注入(node 测试给假的 setTimeout/clearTimeout/navigator),缺省用全局。
    function flash(btn, doneLabel, opts) {
        if (!btn) return;
        opts = opts || {};
        var win = opts.win || root;
        if (btn[TIMER]) win.clearTimeout(btn[TIMER]);
        else btn[PREV] = btn.textContent;
        btn.textContent = doneLabel;
        btn[TIMER] = win.setTimeout(function () {
            btn.textContent = btn[PREV];
            btn[TIMER] = null;
        }, opts.ms || HOLD_MS);
    }

    // 复制失败也闪:剪贴板 API 在非安全上下文/无权限时直接抛或 reject,此时按钮什么都不
    // 动等于没反应,用户只会再点一次。两条路都走 flash——闪的是「点到了」,不谎称写成功。
    function copy(btn, text, doneLabel, opts) {
        var win = (opts && opts.win) || root;
        var done = function () {
            flash(btn, doneLabel, opts);
        };
        try {
            win.navigator.clipboard.writeText(String(text == null ? '' : text)).then(done, done);
        } catch {
            done();
        }
    }

    var api = { copy: copy, flash: flash, HOLD_MS: HOLD_MS };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.copyFlash = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
