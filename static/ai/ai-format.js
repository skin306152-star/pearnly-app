/*
 * Pearnly AI · ai-format.js · 纯格式化函数(金额 / 账期 / 状态文案)
 *
 * 无 DOM 依赖,浏览器挂 window.AI.format,node(测试)走 module.exports ——
 * 同 pos-totals.js 的 UMD 先例。等价性/边界由 tests/unit/test_ai_format.py 用真 node 跑本文件守门。
 */
(function (root) {
    'use strict';

    // 泰铢金额:两位小数 + 千分位,负数原样带负号(工单差额可能为负)。
    function money(v) {
        var n = Number(v);
        if (!isFinite(n)) return '—';
        var sign = n < 0 ? '-' : '';
        var s = Math.abs(n).toFixed(2);
        var parts = s.split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return sign + '฿' + parts.join('.');
    }

    // 账期 "2569-05" → 佛历年 + 月份(zh 文案;th/en/ja 由调用方套 i18n 月名,这里只拆结构)。
    function splitPeriod(period) {
        var m = /^(\d{4})-(\d{2})$/.exec(String(period || ''));
        if (!m) return null;
        return { year: Number(m[1]), month: Number(m[2]) };
    }

    // 工单 status/current_step → 状态胶囊 class + label key(真实三态:running/stuck/review)。
    // v4 演示的 5 列分类(等资料/AI在做/等你审/待签字/已归档)需要 items 级数据(B2/W2 才有),
    // W1 只用 list 端点已给的字段,不假装能分出更细的类目。
    var STATUS_MAP = {
        running: { cls: 'a', key: 'status_running' },
        stuck: { cls: 'b', key: 'status_stuck' },
        review: { cls: 's', key: 'status_review' },
        archive: { cls: 'g', key: 'status_archive' },
    };
    function statusChip(status) {
        return STATUS_MAP[status] || { cls: 'n', key: 'status_unknown' };
    }

    // JWT payload 解码(不验签,仅取展示用字段——token 本就是浏览器已信任的登录态)。
    // 无角色/成员数据源(M1 降级表:多成员/角色 M3 才有)→ 只取邮箱本地部分做头像/姓名占位,
    // 不伪造姓名或权限文案。
    function jwtDisplayName(token) {
        try {
            var parts = String(token || '').split('.');
            if (parts.length < 2) return null;
            var json = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
            var email = json.email || json.username || '';
            // token payload 实测常只有 sub(不透明 UUID),没有邮箱/用户名就不展示——
            // 露一串 UUID 比不展示更误导(状态诚实:没有数据不假装有意义)。
            if (!email || email.indexOf('@') < 0) return null;
            return String(email).split('@')[0];
        } catch (e) {
            return null;
        }
    }

    var api = {
        money: money,
        splitPeriod: splitPeriod,
        statusChip: statusChip,
        jwtDisplayName: jwtDisplayName,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.format = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
