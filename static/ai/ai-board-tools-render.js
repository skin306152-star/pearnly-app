/*
 * Pearnly AI · ai-board-tools-render.js · 看板工具条纯函数(筛选判据 + 缺单条 + 批量条 HTML)
 *
 * 三样能力从「事务所矩阵」搬进五列看板(2026-07-27 拍板:矩阵答「谁缺什么」、看板答
 * 「这单走到哪」,两个视图都留),判据一份收在这里,不在两个视图各写一遍:
 *   缺料/待审/风险(逾期)行筛选 —— 判据吃 /api/tax-profile/matrix 的格子徽章与截止日;
 *   「本期还缺哪几张单」 —— pending_order 徽章 = 这客户这项义务本期没开单;
 *   批量开单条 —— 已选数量 + 一键执行(账期写在按钮上,不让用户猜开的是哪期)。
 * 矩阵(ai-matrix-render.js)也从这里取 isOverdue/matchesFilters:同一个「缺料/待审/风险」
 * 在两个视图里必须是同一句判断,各写一份迟早漂成两套口径。
 *
 * 不碰 DOM、不查后端,只算判据与拼字符串——编排/事件在 ai-dashboard.js + ai-board-bulk.js。
 * UMD 同 ai-state.js 先例,tests/unit/test_ai_board_tools_render.py 用真 node 跑本文件断言。
 */
(function (root) {
    'use strict';

    // 徽章码来自后端 services/workorder/matrix.py 的 BADGE_*,前端不重新判业务状态;
    // 筛选名(missing/review/risk)是 chip 的 data-filter 值,与矩阵同名同义。
    var BADGE_MISSING = 'missing_materials';
    var BADGE_REVIEW = 'pending_review';
    var BADGE_PENDING_ORDER = 'pending_order';
    var BADGE_NO_NEED = 'no_need';
    var BADGE_FROZEN = 'frozen';

    var BANGKOK_OFFSET_MS = 7 * 60 * 60 * 1000;

    // 浏览器走 at()(ai-i18n.js 必先加载);node(单测)无词典 → 回退「key + 插值参数」,
    // 让"账期/义务名有没有真进文案"在 node 里可断言(同 ai-billing-render.js 先例)。
    function t(k, v) {
        if (root && typeof root.at === 'function') return root.at(k, v);
        if (!v) return k;
        return (
            k +
            ' ' +
            Object.keys(v)
                .map(function (x) {
                    return v[x];
                })
                .join(' ')
        );
    }

    function esc(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    // 逾期按曼谷日历判,不按 UTC:UTC 的"今天"在曼谷 00:00-07:00 还停在昨天,拿它当尺子
    // 会让刚过期的单晚 7 小时才标红(同 memory:ci-date-flake-utc-vs-bangkok 的老坑)。
    function todayIsoBangkok(now) {
        var ms = now instanceof Date && !isNaN(now.getTime()) ? now.getTime() : Date.now();
        return new Date(ms + BANGKOK_OFFSET_MS).toISOString().slice(0, 10);
    }

    // 格子是否「逾期风险」:仍未办结(非无需申报/已冻结)且截止日已过今天。截止日读顺延后的
    // due_efiling_deferred(周末/假日顺延),缺该字段(老缓存/降级响应)回落原始 due_efiling。
    function isOverdue(cell, todayIso) {
        if (!cell) return false;
        var due = cell.due_efiling_deferred || cell.due_efiling;
        if (!due) return false;
        if (cell.badge === BADGE_NO_NEED || cell.badge === BADGE_FROZEN) return false;
        return due < (todayIso || todayIsoBangkok());
    }

    // 一个客户的所有格子 → 是否命中激活筛选(任一格命中任一筛选即命中):筛选问的是
    // 「这个客户本期有没有这类事」,不是逐格隐藏。无激活筛选 = 全命中。
    function matchesFilters(cells, activeFilters, todayIso) {
        var active = activeFilters || [];
        if (!active.length) return true;
        var day = todayIso || todayIsoBangkok();
        return (cells || []).some(function (c) {
            return active.some(function (f) {
                if (f === 'missing') return c.badge === BADGE_MISSING;
                if (f === 'review') return c.badge === BADGE_REVIEW;
                if (f === 'risk') return isOverdue(c, day);
                return false;
            });
        });
    }

    function cellsByClient(matrix) {
        var out = {};
        ((matrix || {}).cells || []).forEach(function (c) {
            var key = String(c.client_id);
            (out[key] = out[key] || []).push(c);
        });
        return out;
    }

    function obligationName(code, labels, lang) {
        var l = labels && labels[code];
        if (!l) return String(code);
        return l[lang] || l.zh || String(code);
    }

    // 本期一张单都没开的客户 → { period, names }(names = 该客户本期 pending_order 的义务名,
    // 按截止日先后排,同日按义务码)。本期已开过任一张单的客户不进表——批量开单一次只开一张
    // (POST /api/workorder/orders · intent=monthly_vat),给已有单的客户再挂个勾选框会让人
    // 以为能补开别的义务单,是许了做不到的事。义务一条都没物化过时 names 为空数组,
    // 由渲染层退成「本期还没开单」一句,不编造义务名。
    function missingByClient(matrix, lang) {
        var m = matrix || {};
        var byClient = cellsByClient(m);
        var out = {};
        (m.clients || []).forEach(function (c) {
            if (!c.missing_order) return;
            var pending = (byClient[String(c.id)] || [])
                .filter(function (cell) {
                    return cell.badge === BADGE_PENDING_ORDER;
                })
                .sort(function (a, b) {
                    var da = a.due_efiling_deferred || a.due_efiling || '';
                    var db = b.due_efiling_deferred || b.due_efiling || '';
                    if (da !== db) return da < db ? -1 : 1;
                    return String(a.obligation_code) < String(b.obligation_code) ? -1 : 1;
                });
            out[String(c.id)] = {
                period: m.period,
                names: pending.map(function (cell) {
                    return obligationName(cell.obligation_code, m.obligation_labels, lang);
                }),
            };
        });
        return out;
    }

    // 卡片内「本期缺单」条:说清缺的是哪一期、哪几张单,勾选框就在同一行——批量开单的
    // 选择对象与「缺什么」是同一件事,分开放会让人不知道勾的是什么。
    function missingStripHtml(missing, client) {
        if (!missing) return '';
        var names = missing.names || [];
        var text = names.length
            ? t('kb_missing_list', {
                  p: missing.period,
                  n: names.length,
                  list: names.join('、'),
              })
            : t('kb_missing_unknown', { p: missing.period });
        return (
            '<label class="kmiss"><input type="checkbox" class="kb-check" data-client-id="' +
            esc(client.id) +
            '" aria-label="' +
            esc(t('kb_check_aria', { name: client.name })) +
            '" /><span class="kmiss-t" title="' +
            esc(text) +
            '">' +
            esc(text) +
            '</span></label>'
        );
    }

    // 批量操作条(选中 ≥1 才浮出 · 显示已选数量 · 一键执行 —— Gmail/Loyverse 同款范式)。
    // note 是调用方已翻译好的结果文案(成功几张/失败几张),常态为空。
    function bulkBarHtml(state) {
        var s = state || {};
        var openLabel = s.busy ? t('kb_bulk_open_busy') : t('kb_bulk_open', { p: s.period });
        return (
            '<span class="kb-bulk-n">' +
            esc(t('kb_bulk_selected', { n: s.count || 0 })) +
            '</span>' +
            (s.note ? '<span class="kb-bulk-note">' + esc(s.note) + '</span>' : '') +
            '<button type="button" class="btn sm" data-action="bulk-clear">' +
            esc(t('kb_bulk_clear')) +
            '</button>' +
            '<button type="button" class="btn sm pri" data-action="bulk-open"' +
            (s.busy ? ' disabled' : '') +
            '>' +
            esc(openLabel) +
            '</button>'
        );
    }

    var api = {
        todayIsoBangkok: todayIsoBangkok,
        isOverdue: isOverdue,
        matchesFilters: matchesFilters,
        cellsByClient: cellsByClient,
        obligationName: obligationName,
        missingByClient: missingByClient,
        missingStripHtml: missingStripHtml,
        bulkBarHtml: bulkBarHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.boardTools = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
