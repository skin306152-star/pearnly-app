/*
 * Pearnly AI · ai-format.js · 纯格式化函数(金额 / 账期 / 状态文案 / 字段标签)
 *
 * 无 DOM 依赖,浏览器挂 window.AI.format,node(测试)走 module.exports ——
 * 同 pos-totals.js 的 UMD 先例。等价性/边界由 tests/unit/test_ai_pure_modules.py 用真 node 跑本文件守门。
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

    // 工单 status/current_step → 状态胶囊 class + label key(W2:五列看板落地,
    // 真实四态 collecting/running/stuck/review 全接;signed/archived 前向兼容——
    // 当前引擎不产出,但客户端不因未来值崩溃,统一按「已归档」胶囊显示)。
    // 注:W1 曾误写 status 值 'archive'(真实值是 'archived'),此处一并订正。
    var ARCHIVED_CHIP = { cls: 's', key: 'status_archive' };
    var STATUS_MAP = {
        collecting: { cls: 'n', key: 'status_collecting' },
        running: { cls: 'a', key: 'status_running' },
        stuck: { cls: 'b', key: 'status_stuck' },
        review: { cls: 'a', key: 'status_review' },
        signed: ARCHIVED_CHIP,
        archived: ARCHIVED_CHIP,
    };

    // status(+可选 detail)→ 状态胶囊 {cls, key}。stuck 且逐条 needs 非空时是缺料的具体
    // 子态——看板卡片与客户详情页此前各自手判「是不是缺料」,同一张工单两处文案能对不上;
    // 统一收进这一处,谁传了 detail 谁就拿到诚实的子态,不传就退化成通用 stuck 胶囊。
    function statusChip(status, detail) {
        if (
            status === 'stuck' &&
            detail &&
            Array.isArray(detail.needs) &&
            detail.needs.length > 0
        ) {
            return { cls: 'w', key: 'chip_needs_materials' };
        }
        return STATUS_MAP[status] || { cls: 'n', key: 'status_unknown' };
    }

    function escHtml(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    // statusChip 拼成 <span class="chip …">…</span>(看板卡片、客户详情页工单头共用,
    // 不再各拼一遍)。未知 status 原样显示状态值,不假装认识(状态诚实)。
    function chipHtml(status, detail) {
        var sc = statusChip(status, detail);
        var label = status;
        if (sc.key !== 'status_unknown' && root && typeof root.at === 'function') {
            label = root.at(sc.key);
        }
        return '<span class="chip ' + sc.cls + '">' + escHtml(label) + '</span>';
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

    // 交付物/工单数字字段名 → 四语人话短标签(补 W1 降级点 7)。查表在 ai-i18n.js 的
    // field_<key>;at() 对完全不存在的 key 会原样回退成传入字符串本身,据此判定"没有翻译"。
    function fieldLabel(key) {
        var lookupKey = 'field_' + key;
        if (root && typeof root.at === 'function') {
            var label = root.at(lookupKey);
            if (label !== lookupKey) return label;
        }
        return key;
    }

    var api = {
        money: money,
        splitPeriod: splitPeriod,
        statusChip: statusChip,
        chipHtml: chipHtml,
        jwtDisplayName: jwtDisplayName,
        fieldLabel: fieldLabel,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.format = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
