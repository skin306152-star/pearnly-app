/*
 * Pearnly AI · ai-board-tools-render.js · 看板工具条纯函数(筛选判据 + 缺单条 + 批量条 HTML)
 *
 * 三样能力从「事务所矩阵」搬进五列看板(2026-07-27 拍板:矩阵答「谁缺什么」、看板答
 * 「这单走到哪」,两个视图都留),判据一份收在这里,不在两个视图各写一遍:
 *   缺料/待审/风险(逾期)行筛选 —— 状态类筛选认「这东西脸上写的那个词」(FILTER_STATES
 *     是唯一映射表),风险按顺延后的 e-Filing 截止日判;
 *   「本期还缺哪几张单」 —— pending_order 徽章 = 这客户这项义务本期没开单;
 *   批量开单条 —— 已选数量 + 一键执行(账期写在按钮上,不让用户猜开的是哪期)。
 * 矩阵(ai-matrix-render.js)也从这里取 isOverdue/matchesFilters:同一个「缺料/待审/风险」
 * 在两个视图里必须是同一句判断,各写一份迟早漂成两套口径。两边证据粒度不同(看板有逐单
 * detail,矩阵只有工单粗态),差别只体现在传不传 cardState,判据本身仍是这一份。
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

    // chip(data-filter)→ 它认哪些状态词。状态类筛选只有这一张表。
    //
    // 筛选谓词必须与被筛对象脸上写着的那个词同源,否则点击语义就反了:此前两个视图一律
    // 吃后端徽章,而看板卡面写的是逐单 detail 细分出来的子态——后端把 stuck 折进
    // pending_review(engine.STATUS_GROUPS 的粗粒度组名),卡片却按 detail.needs 写
    // 「缺料」,于是点「待审」筛出一张写着「缺料」的卡(2026-07-27 真浏览器实测)。
    //
    // 表里两套词并列不是重复:看板卡的词是 AI.format.statusChip 的词条 key(有逐单
    // detail,细),矩阵格子的词是后端徽章码(只有工单粗态,粗)。粒度差是真实的证据差,
    // 但"哪个词算哪个 chip"只此一处,不在两个视图各判一遍。
    var FILTER_STATES = {
        missing: ['chip_needs_materials', 'status_collecting', BADGE_MISSING],
        review: ['status_stuck', 'status_review', BADGE_REVIEW],
    };

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

    // 格子是否「逾期风险」:仍未办结(非无需申报/已冻结)且截止日已过今天。
    // 逾期锚点日的权威定义在 services/workorder/matrix.py::_cell(顺延后的 e-Filing 日),
    // 前端不另立口径:读 due_efiling_deferred,缺该字段(老缓存/降级响应)回落原始 due_efiling。
    // 已知未收口:智能管家 services/steward/tools_close.py 答「已逾期几项」时锚在
    // 纸质截止日,泰国月度表 e-Filing 比纸质晚 8 天 —— 那一周里两处会给两个数。本批不动
    // 管家(改它要连带动它的口径测试),改口径时以 matrix.py::_cell 的注释为准。
    function isOverdue(cell, todayIso) {
        if (!cell) return false;
        var due = cell.due_efiling_deferred || cell.due_efiling;
        if (!due) return false;
        if (cell.badge === BADGE_NO_NEED || cell.badge === BADGE_FROZEN) return false;
        return due < (todayIso || todayIsoBangkok());
    }

    // 一个客户 → 是否命中激活筛选(任一格/卡面词命中任一筛选即命中):筛选问的是
    // 「这个客户本期有没有这类事」,不是逐格隐藏。无激活筛选 = 全命中。
    // cardState:看板传这张卡脸上那个状态词的词条 key(AI.format.statusChip),状态类
    // 筛选一律以它为准——用户点了「待审」,留下的必须是写着「待审/等你审」的卡。
    // 不传(矩阵没有逐单 detail)才退回按格子徽章判。
    function matchesFilters(cells, activeFilters, todayIso, cardState) {
        var active = activeFilters || [];
        if (!active.length) return true;
        var day = todayIso || todayIsoBangkok();
        var list = cells || [];
        return active.some(function (f) {
            if (f === 'risk') {
                return list.some(function (c) {
                    return isOverdue(c, day);
                });
            }
            var want = FILTER_STATES[f];
            if (!want) return false;
            if (cardState) return want.indexOf(cardState) >= 0;
            return list.some(function (c) {
                return want.indexOf(c.badge) >= 0;
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

    // 缺单条里的义务名走官方表号短码(PND1 / ภ.ง.ด.1),与矩阵列头同一个词典键
    // (obl_short_*,见 ai-matrix-render.js::obligationShortLabel)——后端 display_names
    // 给的是「工资薪金预扣税申报(PND1)」这种全名,两个名字塞进 164px 宽的卡里必被裁掉
    // 半句(2026-07-27 桌面 1280 实测 scrollHeight 64 > clientHeight 48,第二项义务名整个
    // 看不到)。词典没这个码时回落全名,再回落原始码,不编名字。
    function obligationName(code, labels, lang) {
        var key = 'obl_short_' + code;
        var short = t(key);
        if (short && short !== key) return short;
        var l = labels && labels[code];
        if (!l) return String(code);
        return l[lang] || l.zh || String(code);
    }

    // 这家本期到底有没有该办的事:只要有一格义务不是「无需申报/已冻结」就算有。
    // 一格都没物化(cells 为空)也算有——那是画像没存过,不是"这个月不用交"。
    function hasDuty(cells) {
        if (!cells.length) return true;
        return cells.some(function (c) {
            return c.badge !== BADGE_NO_NEED && c.badge !== BADGE_FROZEN;
        });
    }

    // 本期一张单都没开的客户 → { period, names }(names = 该客户本期 pending_order 的义务名,
    // 按截止日先后排,同日按义务码)。本期已开过任一张单的客户不进表——批量开单一次只开一张
    // (POST /api/workorder/orders · intent=monthly_vat),给已有单的客户再挂个勾选框会让人
    // 以为能补开别的义务单,是许了做不到的事。义务一条都没物化过时 names 为空数组,
    // 由渲染层退成「本期还没开单」一句,不编造义务名。
    // 本期全部义务都是「无需申报/已冻结」的客户同样不进表:后端 missing_order 只答"本期
    // 没有工单",答不了"本期该不该有单"(services/workorder/matrix.py::build)。不排掉的话
    // 卡上会冒出黄底「还没开单」告警条 + 勾选框,会计一勾就给一个本期无义务的客户真开出
    // 一张单——后端幂等只保证不重复,不保证不该开。
    function missingByClient(matrix, lang) {
        var m = matrix || {};
        var byClient = cellsByClient(m);
        var out = {};
        (m.clients || []).forEach(function (c) {
            if (!c.missing_order) return;
            if (!hasDuty(byClient[String(c.id)] || [])) return;
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
