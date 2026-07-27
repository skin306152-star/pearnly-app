/*
 * Pearnly AI · ai-blocked-notice.js · 工单跑批停住那一屏说什么、给什么按钮
 *
 * 一屏必须答完三问:跑了几件(共几件)· 为什么停(差多少)· 现在怎么办(点哪)。
 * 此前只有一句「后台在这里停住:{原因}」——会计知道停了,不知道停在第几件,也不知道
 * 充多少够把剩下的跑完。
 *
 * 两个钱码永远分开,合并一次就等于向用户报错账:
 *   insufficient_balance = 用户钱包空了 → 出路是充值(带缺口金额,后端 ocr_balance
 *                          .shortfall_reason 以 "code:฿数" 形态带上来);
 *   ocr_cost_cap_exceeded = 我们付给模型厂商的内部预算到顶 → 跟用户的余额无关,给他
 *                          「去充值」等于把我们的成本问题记到他账上。
 * 其余码(配额待补 / 将来新增)走原样列举的兜底句,不臆造出路。
 *
 * 纯字符串拼装,零 DOM;t()/money() 在 node 无词典时优雅退化,
 * tests/unit/test_ai_blocked_reasons.py 装真词典跑真 node 断言用户看到的那句话。
 */
(function (root) {
    'use strict';

    var TOPUP_CODE = 'insufficient_balance';
    var COST_CAP_CODE = 'ocr_cost_cap_exceeded';

    // 后端原因码形态:纯码,或 "码:参数"(ocr_quota_deferred:3 / insufficient_balance:6.00)。
    function codeOf(raw) {
        return String(raw == null ? '' : raw).split(':')[0];
    }

    function argOf(raw) {
        var s = String(raw == null ? '' : raw);
        var i = s.indexOf(':');
        return i > 0 ? s.slice(i + 1) : '';
    }

    function firstOf(reasons, code) {
        for (var i = 0; i < reasons.length; i++) {
            if (codeOf(reasons[i]) === code) return reasons[i];
        }
        return null;
    }

    function count(v) {
        var n = Number(v);
        return isFinite(n) && n >= 0 ? n : null;
    }

    /**
     * detail → 这一屏的骨架(纯数据,不碰文案):主因是哪一类、缺口多少、跑了几件、
     * 还有哪些次要原因也得说。
     *
     * 主因取「用户自己动得了的那条」:没钱他能充,内部封顶只能等我们放预算——两条同时
     * 成立时先说前者,后者退到「另外还有」里,仍然点名,只是不抢按钮。
     * 件数取 detail.progress(后端 classify_progress 只在卡在 classify 步时给);拿不到
     * 就少说这一句,不从别处凑一个数出来。
     */
    function plan(detail) {
        var d = detail || {};
        var reasons = (d.blocked_reasons || []).slice();
        var primary = firstOf(reasons, TOPUP_CODE) || firstOf(reasons, COST_CAP_CODE);
        var kind = primary ? (codeOf(primary) === TOPUP_CODE ? 'topup' : 'cost_cap') : 'generic';
        var progress = d.progress || {};
        var done = count(progress.processed);
        var total = count(progress.total);
        var left = done !== null && total !== null && total > done ? total - done : null;
        return {
            kind: kind,
            shortfall: kind === 'topup' && argOf(primary) ? argOf(primary) : null,
            done: done,
            total: total,
            left: left,
            others: reasons.filter(function (r) {
                return r !== primary;
            }),
        };
    }

    // 浏览器走 at();node(单测)无词典时回退原 key(同 ai-fail-render.js 的 t() 先例)。
    function t(key, vars) {
        return typeof root.at === 'function' ? root.at(key, vars) : key;
    }

    function fmt() {
        return (root.AI && root.AI.format) || null;
    }

    function money(v) {
        var f = fmt();
        return f && typeof f.money === 'function' ? f.money(v) : '฿' + v;
    }

    function reasonList(reasons) {
        var f = fmt();
        return f && typeof f.blockedReasonList === 'function'
            ? f.blockedReasonList(reasons)
            : reasons.join('、');
    }

    /** 骨架 → 一句一件事的文案数组(每句独立降级,缺哪个数就少说哪一句)。 */
    function sentences(p) {
        var out = [];
        if (p.done !== null && p.total !== null) {
            out.push(t('wo_blocked_ran', { done: p.done, total: p.total }));
        }
        if (p.kind === 'topup') {
            out.push(
                p.left ? t('wo_blocked_credit_why', { left: p.left }) : t('wo_blocked_credit_rest')
            );
            if (p.shortfall) out.push(t('wo_blocked_credit_need', { amount: money(p.shortfall) }));
            out.push(t('wo_blocked_credit_how'));
        } else if (p.kind === 'cost_cap') {
            out.push(t('wo_blocked_cap_why'));
            out.push(t('wo_blocked_cap_how'));
        } else {
            // 兜底:没有已知主因,原样列举(未知码由 blockedReasonLabel 如实回显原码)。
            out.push(t('system_blocked_detail', { list: reasonList(p.others) }));
        }
        if (p.kind !== 'generic' && p.others.length) {
            out.push(t('wo_blocked_also', { list: reasonList(p.others) }));
        }
        return out;
    }

    function esc(s) {
        if (root && root.AI && root.AI.state && typeof root.AI.state.esc === 'function') {
            return root.AI.state.esc(s);
        }
        return String(s == null ? '' : s);
    }

    function topupHref() {
        return (root.AI && root.AI.failRender && root.AI.failRender.TOPUP_HASH) || '';
    }

    /**
     * 整块 HTML:一段人话 + 至多两个按钮(充值 / 就地重试)。
     *
     * 重试永远在:充值完回到本页点它就从断点接着跑,文案里点名的就是这个按钮。余额不足时
     * 它降级成次按钮——没充值就重试 100% 立刻再 stuck(classify 开跑前 wallet.exhausted()
     * 即返),把它摆成主出路等于造一个死循环。
     */
    function html(detail) {
        var p = plan(detail);
        var topup =
            p.kind === 'topup'
                ? '<a class="btn sm pri" data-action="wo-topup" href="' +
                  esc(topupHref()) +
                  '">' +
                  esc(t('fail_topup_btn')) +
                  '</a>'
                : '';
        return (
            '<div class="wo-guide"><p class="rv-blocked">' +
            sentences(p).map(esc).join(' ') +
            '</p>' +
            topup +
            '<button type="button" class="btn sm' +
            (topup ? '' : ' pri') +
            '" data-action="wo-retry-stuck">' +
            esc(t('retry')) +
            '</button></div>'
        );
    }

    var api = { plan: plan, sentences: sentences, html: html };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.blockedNotice = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
