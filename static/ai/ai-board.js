/*
 * Pearnly AI · ai-board.js · 五列看板的分列/摘要/账期纯函数(M1-W2)
 *
 * 四个纯函数,不碰 DOM、不查 window.at——调用方(ai-dashboard.js/ai-kanban-render.js)
 * 负责渲染与 i18n:
 *   mapOrderToColumn(order, detail) → 五列之一(等资料/AI在做/等你审/待签字/已归档)
 *   summarizeCard(order, detail)    → 卡片摘要行的 i18n key + 变量
 *   currentPeriodBE(date)           → 公历日期换算佛历账期 "YYYY-MM"(开单默认账期)
 *   periodOptions(count, date)      → 开单可选账期列表(当月在前,往前 count-1 个月)
 *   needsOpenControl(entry, cur)    → 卡片是否要渲染开单控件(当期没有工单)
 * COLUMNS 是五列的规范表(key + 顺序 + 列头圆点色),ai-kanban-render.js 渲染与
 * ai-dashboard.js 分组初始化都从这里派生,不各自维护第二份列清单。
 *
 * money() 借道 root.AI.format(若已加载),未加载时原样透传——保持本文件在无 ai-format
 * 的环境下仍可单测(同 UMD 先例,浏览器挂 window.AI.board,node 走 module.exports)。
 */
(function (root) {
    'use strict';

    function money(v) {
        if (root && root.AI && root.AI.format && typeof root.AI.format.money === 'function') {
            return root.AI.format.money(v);
        }
        return v;
    }

    // v4 §2 kanban 五列固定顺序与色标(UI-Canon-v4 §5·1:1 抄 .dot 类名,禁自配色)。
    var COLUMNS = [
        { key: 'materials', dot: 'n', titleKey: 'col_materials' },
        { key: 'working', dot: 'a', titleKey: 'col_working' },
        { key: 'review', dot: 'b', titleKey: 'col_review' },
        { key: 'sign', dot: 'a', titleKey: 'col_sign' },
        { key: 'archived', dot: 's', titleKey: 'col_archived' },
    ];

    // detail[key] 安全取数组:非法/缺失一律回落空数组(mapOrderToColumn/summarizeCard
    // 都要判空取 needs/blocked_reasons,收成一个小工具复用,不各写一遍)。
    function _arr(detail, key) {
        return detail && Array.isArray(detail[key]) ? detail[key] : [];
    }

    // status → 五列 key。真实后端只产出 collecting/running/stuck/review 四态,
    // signed/archived 是引擎尚未建的 W5 终态——前向兼容,不因未知值崩溃。
    function mapOrderToColumn(order, detail) {
        if (!order) return { column: 'materials' };

        var needs = _arr(detail, 'needs');

        switch (order.status) {
            case 'collecting':
                return { column: 'materials' };
            case 'running':
                return { column: 'working' };
            case 'stuck':
                if (needs.length > 0) return { column: 'materials' };
                // 没有逐条 needs(看板首屏用 list 端点批量拉,不逐条拉 detail)——stuck 本质
                // 是需要人看,保守分到「等你审」,不假装能细分出缺料/挂起(blocked_reasons
                // 与此兜底同值,不再单独判断)。
                return { column: 'review' };
            case 'review':
                return { column: 'sign' };
            case 'signed':
            case 'archived':
                return { column: 'archived' };
            default:
                return { column: 'materials', unknown: true };
        }
    }

    // order/detail → 卡片摘要的 {key, vars},诚实降级:没有 detail 就只报账期,不编内容。
    function summarizeCard(order, detail) {
        if (!order) return { key: 'card_no_order' };

        var blocked = _arr(detail, 'blocked_reasons');
        if (blocked.length > 0) {
            return { key: 'card_blocked_n', vars: { n: blocked.length } };
        }

        var needs = _arr(detail, 'needs');
        if (needs.length > 0) {
            return { key: 'card_needs_list', vars: { list: needs.join('、') } };
        }

        if (order.status === 'running') {
            return { key: 'card_running_step', vars: { step: order.current_step } };
        }

        if (order.status === 'review') {
            var numbers = (detail && detail.numbers) || {};
            if (numbers.tax_due != null && numbers.tax_due !== '') {
                return { key: 'card_tax_due', vars: { amount: money(numbers.tax_due) } };
            }
        }

        return { key: 'card_period_only', vars: { p: order.period } };
    }

    // 公历 Date → 佛历账期 "YYYY-MM"(泰国会计年 = 公历年 + 543)。不传 date 用当下时刻。
    function currentPeriodBE(date) {
        var d = date instanceof Date && !isNaN(date.getTime()) ? date : new Date();
        var beYear = d.getFullYear() + 543;
        var month = String(d.getMonth() + 1);
        if (month.length < 2) month = '0' + month;
        return beYear + '-' + month;
    }

    // 开单可选账期(影子月跑历史月份的前置刚需):当月在前,往前推 count-1 个月,共 count 个
    // 选项。默认 count=14(当月 + 往前 13 个月)。Date 的月份运算原生处理跨年借位
    // (new Date(y, -1, 1) 自动落到上一年 12 月),不用手写借位算术。
    function periodOptions(count, date) {
        var n = count > 0 ? count : 14;
        var base = date instanceof Date && !isNaN(date.getTime()) ? date : new Date();
        var out = [];
        for (var i = 0; i < n; i++) {
            out.push(currentPeriodBE(new Date(base.getFullYear(), base.getMonth() - i, 1)));
        }
        return out;
    }

    // 开单控件是否要出现在卡片上:当期(currentPeriod)没有工单——没有任何单,或
    // entry 携带的最新单不是本期。此前判定是「entry.order 存在就不给开单控件」,
    // 真实客户永远有历史单(如某客户仅有 2569-05 旧单),导致历史账期开单(A3)在
    // 真实客户上永远不可达,prod 抓到实锤后改判据(见项目记忆 g1-first-run-direction
    // -blackhole 同类教训:方向/开关判据只挑一种情形会在真实数据上打对折)。
    function needsOpenControl(entry, currentPeriod) {
        return !entry.order || entry.order.period !== currentPeriod;
    }

    var api = {
        COLUMNS: COLUMNS,
        mapOrderToColumn: mapOrderToColumn,
        summarizeCard: summarizeCard,
        currentPeriodBE: currentPeriodBE,
        periodOptions: periodOptions,
        needsOpenControl: needsOpenControl,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.board = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
