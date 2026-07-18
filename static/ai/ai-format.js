/*
 * Pearnly AI · ai-format.js · 纯格式化函数(金额 / 账期 / 状态文案 / 字段标签)
 *
 * 无 DOM 依赖,浏览器挂 window.AI.format,node(测试)走 module.exports ——
 * 同 pos-totals.js 的 UMD 先例。等价性/边界由 tests/unit/test_ai_pure_modules.py 用真 node 跑本文件守门。
 */
(function (root) {
    'use strict';

    // 金额输入串 → 规范化十进制串(去千分位/空白,最多两位小数)或 null,解不出/超形一律 null。
    // 真正的 Decimal 换算留给后端,前端只挡形。allowNegative 由调用方按字段语义定夺(销项
    // 销售额/税额不认负号;人审 VAT 改数允许负号覆盖)——ai-intake-render.js 的 parseAmount
    // 与 ai-review-queue.js 的 parseVat 曾各自定义同一条正则,收到这里共享一份。
    function parseAmount(raw, allowNegative) {
        var s = String(raw == null ? '' : raw)
            .trim()
            .replace(/,/g, '');
        var re = allowNegative ? /^-?\d+(\.\d{1,2})?$/ : /^\d+(\.\d{1,2})?$/;
        if (!s || !re.test(s)) return null;
        return s;
    }

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

    // 比率(0.925 或其字符串形态)→ 百分比串("92.5%"),解不出/非有限 → "—"。
    // ai-bank-sales-render.js 的 pctText 与 ai-corrob.js 的 pct 曾各自定义同一实现,收敛于此。
    function pct(ratio) {
        var n = parseFloat(ratio);
        return isFinite(n) ? (n * 100).toFixed(1) + '%' : '—';
    }

    // 账期 "2569-05" → 佛历年 + 月份(zh 文案;th/en/ja 由调用方套 i18n 月名,这里只拆结构)。
    function splitPeriod(period) {
        var m = /^(\d{4})-(\d{2})$/.exec(String(period || ''));
        if (!m) return null;
        return { year: Number(m[1]), month: Number(m[2]) };
    }

    // 工单 status/current_step → 状态胶囊 class + label key(W2:五列看板落地,
    // 真实五态全接:collecting/running/stuck/review/archive)。词汇随
    // services/workorder/engine.py 的 ALL_STATUSES 同步——前端无法 import python,
    // 手工对齐,改词必须两处同步(C4-R1 教训:首版手打 'signed'/'archived' 两个
    // 臆造词,全仓不存在,真冻结单在矩阵/看板双双落 fallthrough 错标)。
    var STATUS_MAP = {
        collecting: { cls: 'n', key: 'status_collecting' },
        running: { cls: 'a', key: 'status_running' },
        stuck: { cls: 'b', key: 'status_stuck' },
        review: { cls: 'a', key: 'status_review' },
        archive: { cls: 's', key: 'status_archive' },
    };

    // status(+可选 detail)→ 状态胶囊 {cls, key}。stuck/collecting 且逐条 needs 非空时是
    // 缺料的具体子态——看板卡片与客户详情页此前各自手判「是不是缺料」,同一张工单两处文案
    // 能对不上;统一收进这一处,谁传了 detail 谁就拿到诚实的子态,不传就退化成通用胶囊。
    // collecting 纳入(2026-07-17 S4):此前 collecting 只给通用「等资料」,缺什么全靠猜,
    // 与看板「等资料」列名对齐同走缺料胶囊。
    function statusChip(status, detail) {
        var canBeNeedy = status === 'stuck' || status === 'collecting';
        if (canBeNeedy && detail && Array.isArray(detail.needs) && detail.needs.length > 0) {
            return { cls: 'w', key: 'chip_needs_materials' };
        }
        if (
            status === 'stuck' &&
            detail &&
            Array.isArray(detail.blocked_reasons) &&
            detail.blocked_reasons.length > 0
        ) {
            var reviewQueue = root && root.AI && root.AI.reviewQueue;
            var hasPending =
                reviewQueue &&
                typeof reviewQueue.filterPurchaseQueue === 'function' &&
                typeof reviewQueue.splitByDecision === 'function' &&
                reviewQueue.splitByDecision(reviewQueue.filterPurchaseQueue(detail.flagged || []))
                    .undecided.length > 0;
            if (!hasPending) return { cls: 'b', key: 'status_system_failed' };
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

    // JWT payload 解码(不验签,只取展示用字段——token 本就是浏览器已信任的登录态)。
    // 解不出(格式不对/非法 base64/非 JSON)一律 null,调用方据此各自回落。
    function jwtPayload(token) {
        try {
            var parts = String(token || '').split('.');
            if (parts.length < 2) return null;
            return JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
        } catch (e) {
            return null;
        }
    }

    // 无角色/成员数据源(M1 降级表:多成员/角色 M3 才有)→ 只取邮箱本地部分做头像/姓名占位,
    // 不伪造姓名或权限文案。
    function jwtDisplayName(token) {
        var json = jwtPayload(token);
        if (!json) return null;
        var email = json.email || json.username || '';
        // token payload 实测常只有 sub(不透明 UUID),没有邮箱/用户名就不展示——
        // 露一串 UUID 比不展示更误导(状态诚实:没有数据不假装有意义)。
        if (!email || email.indexOf('@') < 0) return null;
        return String(email).split('@')[0];
    }

    // 签批区 actor 展示(v5 §五3 与左下角同源):/api/me 的 users.username → 邮箱前缀 →
    // 登录态 sub 短八位。绝不拼 "user:<uuid>" 糊脸(2026-07-14 清单 #2);短八位是最后
    // 兜底,让「谁签的」至少可比对不刷屏。me 未返回时传 null,走 token 侧回落链。
    function actorLabel(me, token) {
        me = me || {};
        if (me.username) return String(me.username);
        var email = String(me.email || '');
        if (email.indexOf('@') > 0) return email.split('@')[0];
        var name = jwtDisplayName(token);
        if (name) return name;
        var payload = jwtPayload(token);
        var sub = payload && payload.sub ? String(payload.sub) : '';
        return sub ? sub.slice(0, 8) : '';
    }

    // 服务端事件流回显的 actor 串("user:<uuid>",routes 落库格式)→ 展示名:浏览器端
    // 没有他人 uuid→用户名 的解析端点,退 uuid 短八位;非该格式(用户名/邮箱前缀占位)
    // 原样透传。与 actorLabel 的最后兜底同口径。
    function actorDisplay(raw) {
        var s = String(raw || '');
        return s.indexOf('user:') === 0 ? s.slice(5, 13) : s;
    }

    // prior_period_check(compute.py 产出的对象,{status:'no_prior_period'} 或 {status:'compared',
    // prior_period, prior_tax_due, delta})→ i18n key + 插值(N-3 修复:B2-e 前 ai-client.js 把
    // 整个对象直接扔进 esc() 显示成字面 "[object Object]")。如实展示原始差额数字,不臆断
    // "多缴/少缴"方向(状态诚实)。
    function priorPeriodCheckStatus(check) {
        check = check || {};
        if (check.status === 'compared') {
            return {
                key: 'ppc_compared',
                vars: { period: check.prior_period, delta: money(check.delta) },
            };
        }
        return { key: 'ppc_no_prior', vars: null };
    }

    // 浏览器专用:上面纯函数的结果套 at()+esc(),给 renderWo 的单元格直接用。
    function priorPeriodCheckText(check) {
        var d = priorPeriodCheckStatus(check);
        if (!root || typeof root.at !== 'function') return d.key;
        return escHtml(root.at(d.key, d.vars || undefined));
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

    // 引擎步骤 key(services/workorder/engine.py::STEPS)→ 四语人话短标签(S2:工单页
    // 此前裸显 classify/reconcile 英文键)。同 fieldLabel 的「查不到回退原值」范式。
    function stepLabel(stepKey) {
        var lookupKey = 'step_' + stepKey;
        if (root && typeof root.at === 'function') {
            var label = root.at(lookupKey);
            if (label !== lookupKey) return label;
        }
        return stepKey;
    }

    // classify(逐张识别)/ reconcile(逐张读对账单)的进度文案(simplify 收口:此前
    // intake/review/wo 三个渲染层各持一份逐字相同的实现,key 映射漂移无人守——收归这里,
    // 与 stepLabel 同居,node 单测覆盖)。
    function progressLabel(progress) {
        var key = progress.step === 'reconcile' ? 'wo_bank_progress' : 'wo_classify_progress';
        if (root && typeof root.at === 'function') {
            return root.at(key, { done: progress.processed, total: progress.total });
        }
        return key;
    }

    // 最后活动相对时间(S2):<60s 秒 / <60min 分 / <24h 时 / 其余天,n 向下取整;时钟
    // 偏差出的负差归零(显「0 秒前」比负数诚实);iso 解析不出回空串,调用方据此整段不渲染。
    function relAgo(iso, nowMs) {
        var t = Date.parse(String(iso || ''));
        if (!isFinite(t)) return '';
        var sec = Math.max(0, Math.floor((Number(nowMs) - t) / 1000));
        var unit =
            sec < 60
                ? { key: 'time_ago_s', n: sec }
                : sec < 3600
                  ? { key: 'time_ago_m', n: Math.floor(sec / 60) }
                  : sec < 86400
                    ? { key: 'time_ago_h', n: Math.floor(sec / 3600) }
                    : { key: 'time_ago_d', n: Math.floor(sec / 86400) };
        if (root && typeof root.at === 'function') return root.at(unit.key, { n: unit.n });
        return unit.key;
    }

    var api = {
        parseAmount: parseAmount,
        money: money,
        pct: pct,
        splitPeriod: splitPeriod,
        statusChip: statusChip,
        chipHtml: chipHtml,
        jwtPayload: jwtPayload,
        jwtDisplayName: jwtDisplayName,
        actorLabel: actorLabel,
        actorDisplay: actorDisplay,
        fieldLabel: fieldLabel,
        stepLabel: stepLabel,
        progressLabel: progressLabel,
        relAgo: relAgo,
        priorPeriodCheckStatus: priorPeriodCheckStatus,
        priorPeriodCheckText: priorPeriodCheckText,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.format = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
