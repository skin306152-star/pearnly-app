/*
 * Pearnly · copy-flash.js · 「复制 → 按钮闪一下『已复制』→ 还原原文」的共享出口
 *
 * 各处复制按钮此前各写一份逐字相同的 flash():点下去才抓 textContent 当原文,1.5 秒内
 * 连点第二次抓到的已经是「已复制」,还原就还原成「已复制」——按钮从此再也变不回来
 * (2026-07-30 真浏览器走查实测)。原文只在第一次闪时记一次,连点只顺延计时器。
 *
 * 住 static/shared/ 而不是某个壳里:/ai 与 /dms 两个壳都用它,而它们由同一条 esbuild
 * 拼接管道(scripts/build-home-js.mjs)各自打包 —— 共用一份只是在两张清单里各列一行。
 * 挂 root.CopyFlash 不挂 root.AI.*:两个壳共用的东西顶着另一个壳的名字,下一个人会以为
 * /dms 依赖了 /ai。(/home 走的是 Vite ESM 那套独立构建图,进不来,自己有一份 TS 版。)
 *
 * 零依赖:不碰任何壳的全局、不碰 i18n,剪贴板内容与「已复制」文案都由调用方给。
 * node(tests/unit/test_copy_flash.py)注入假 window + 假按钮直接跑,不需要浏览器。
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
    if (root) root.CopyFlash = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
