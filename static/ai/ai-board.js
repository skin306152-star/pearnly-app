/*
 * Pearnly AI · ai-board.js · 五列看板的分列/摘要/账期纯函数(M1-W2)
 *
 * 四个纯函数,不碰 DOM、不查 window.at——调用方(ai-dashboard.js/ai-kanban-render.js)
 * 负责渲染与 i18n:
 *   mapOrderToColumn(order, detail) → 五列之一(等资料/AI在做/等你审/待签字/已归档)
 *   summarizeCard(order, detail)    → 卡片摘要行的 i18n key + 变量
 *   currentPeriodBE(date)           → 公历日期换算佛历账期 "YYYY-MM"(开单默认账期)
 *   periodOptions(count, date)      → 开单可选账期列表(当月在前,往前 count-1 个月)
 *   needsDetail(status)             → 该状态的卡是否需逐单拉 detail 才能诚实渲染
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

    // stuck 单是否真有待人裁决的审核队列(J-12:看板别把"卡住但队列已判完/没队列"的单
    // 也塞进「等你审」——点进去空的,状态词骗人)。借道 root.AI.reviewQueue(同 money()
    // 的 root.AI.format 借道先例),未加载(脱管单测未 require 它)时保守当"有待审"处理,
    // 不能悄悄把真实场景判没——判定错的方向必须是"多分去等你审"而不是反过来漏判。
    function _hasPendingReviewQueue(detail) {
        var flagged = _arr(detail, 'flagged');
        if (!flagged.length) return false;
        if (
            root &&
            root.AI &&
            root.AI.reviewQueue &&
            typeof root.AI.reviewQueue.filterPurchaseQueue === 'function' &&
            typeof root.AI.reviewQueue.splitByDecision === 'function'
        ) {
            return (
                root.AI.reviewQueue.splitByDecision(
                    root.AI.reviewQueue.filterPurchaseQueue(flagged)
                ).undecided.length > 0
            );
        }
        return true;
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

    // status → 五列 key。真实后端产出五态 collecting/running/stuck/review/archive,
    // 词汇随 services/workorder/engine.py 的 ALL_STATUSES 同步——前端无法 import
    // python,手工对齐,改词必须两处同步(C4-R1 教训:首版手打 'signed'/'archived'
    // 两个臆造词,全仓不存在,真冻结单落 fallthrough 错标「未评估」)。
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
                // J-12 根治:只有真有待人裁决的审核队列(flagged 里的进项票/方向不明票,
                // 同 W3 审核队列口径)才归「等你审」——此前只看 blocked_reasons 非空就分
                // 去这一列,漏了"卡住但队列已判完/根本没有队列条目"这种真实场景(点进去
                // 空的,状态词骗人)。没有逐条 detail(看板首屏用 list 端点批量拉)时
                // _hasPendingReviewQueue 保守当"有待审"不误判成"没事"。
                if (_hasPendingReviewQueue(detail)) return { column: 'review' };
                return { column: 'materials' };
            case 'review':
                return { column: 'sign' };
            case 'archive':
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
            return { key: 'card_system_blocked_n', vars: { n: blocked.length } };
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

    // 顶部「待你处理」胶囊的计数(2026-07-17 S4):review-queue 里 status 为 review/stuck
    // 的工单数——与 #/pool 同一数据源同一口径。不含 running(那是 AI 的事不是人的)。
    // 矩阵/看板此前各自从格子/订单推的两套口径与 pool 数字实测同屏 0 vs 1 打架,废除。
    function pendingReviewCount(queue) {
        var n = 0;
        ((queue || {}).clients || []).forEach(function (c) {
            (c.orders || []).forEach(function (o) {
                if (o.status === 'review') {
                    n += 1;
                    return;
                }
                if (o.status !== 'stuck') return;
                if (!Array.isArray(o.flagged_groups)) {
                    n += 1;
                    return;
                }
                if (
                    o.flagged_groups.some(function (g) {
                        return typeof g.undecided_count === 'number'
                            ? g.undecided_count > 0
                            : (g.count || 0) > 0;
                    })
                )
                    n += 1;
            });
        });
        return n;
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

    // 哪些状态的卡必须逐单拉 detail 才能诚实渲染:stuck/review 读 blocked_reasons/
    // flagged,collecting 读 needs(缺什么)——判定贴着 mapOrderToColumn/summarizeCard
    // 这张规范表放,消费方(ai-dashboard.js)只调谓词,不各自镜像一份状态清单。
    function needsDetail(status) {
        return status === 'stuck' || status === 'review' || status === 'collecting';
    }

    var api = {
        COLUMNS: COLUMNS,
        mapOrderToColumn: mapOrderToColumn,
        summarizeCard: summarizeCard,
        pendingReviewCount: pendingReviewCount,
        currentPeriodBE: currentPeriodBE,
        periodOptions: periodOptions,
        needsDetail: needsDetail,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.board = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
