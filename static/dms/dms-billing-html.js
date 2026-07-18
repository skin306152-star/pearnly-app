/* Pearnly DMS · 套餐与余额视图 · HTML 模板层(挂 window.DXBILLINGHTML)。
 * 纯字符串构建,不含事件/请求(逻辑在 dms-billing.js / dms-billing-topup.js / dms-billing-records.js)。
 * 照主站 subscription.ts/billing.ts 语义在 DMS 蓝色令牌系复刻;金额走 fmtBaht(฿ 千分位),文案走 t()。
 * 收款账户为固定值(非 i18n)。✓ 用内联 SVG(避开 emoji 闸),不用字符。 */
(function (root) {
    'use strict';
    function t(k, v) {
        return typeof root.t === 'function' ? root.t(k, v) : k;
    }
    function esc(s) {
        return typeof root.escapeHtml === 'function'
            ? root.escapeHtml(s == null ? '' : s)
            : String(s);
    }
    function fmtBaht(n) {
        var num = Number(n || 0);
        var frac = num % 1 ? 2 : 0;
        return (
            '฿' +
            num.toLocaleString('en-US', { minimumFractionDigits: frac, maximumFractionDigits: 2 })
        );
    }
    function fmtInt(n) {
        return Number(n || 0).toLocaleString('en-US');
    }
    function fmtRate(n) {
        return '฿' + Number(n || 0).toFixed(2);
    }
    function fmtDate(v) {
        if (!v) return '—';
        var d = new Date(v);
        if (isNaN(d.getTime())) return String(v);
        var p = function (x) {
            return (x < 10 ? '0' : '') + x;
        };
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
    }

    var BANK = {
        name: 'ธนาคาร กรุงเทพ',
        branch: 'สาขาโชคชัย 4 ลาดพร้าว',
        acct: '230-0-91368-4',
        holder: 'บจ. มิสเตอร์ อี อาร์ พี',
    };
    var CHECK =
        '<svg class="dms-bill-ck" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3.2 3.2L13 5"/></svg>';

    function page(inner) {
        return (
            '<div class="dms-page-head"><h1>' +
            esc(t('dms-bill-title')) +
            '</h1><p>' +
            esc(t('dms-bill-sub')) +
            '</p></div><div class="dms-bill">' +
            inner +
            '</div>'
        );
    }
    function state(cls, msg, withRetry) {
        return (
            '<div class="dms-state ' +
            cls +
            '"><p>' +
            esc(msg) +
            '</p>' +
            (withRetry
                ? '<button type="button" class="btn" id="dms-bill-retry">' +
                  esc(t('dms-bill-retry')) +
                  '</button>'
                : '') +
            '</div>'
        );
    }
    function employee() {
        return (
            '<div class="dms-page-head"><h1>' +
            esc(t('dms-bill-title')) +
            '</h1></div><div class="dms-state empty"><p><b>' +
            esc(t('dms-bill-emp-title')) +
            '</b></p><p>' +
            esc(t('dms-bill-emp-sub')) +
            '</p></div>'
        );
    }
    function metric(k, v) {
        return (
            '<div class="dms-bill-metric"><div class="k">' +
            esc(k) +
            '</div><div class="v">' +
            esc(v) +
            '</div></div>'
        );
    }

    function balanceCard(credits, isExempt) {
        var rate = credits.current_rate != null ? credits.current_rate : 1.5;
        var body =
            '<h2>' +
            esc(t('dms-bill-bal-title')) +
            '</h2><div class="dms-bill-balance">' +
            esc(fmtBaht(credits.balance_thb)) +
            '</div><div class="dms-bill-metrics">' +
            metric(
                t('dms-bill-bal-used'),
                t('dms-bill-used-fmt', { n: fmtInt(credits.pages_this_month) })
            ) +
            metric(t('dms-bill-bal-rate'), t('dms-bill-rate-fmt', { r: rate })) +
            '</div>';
        if (isExempt) {
            body += '<div class="dms-bill-exempt">' + esc(t('dms-bill-exempt')) + '</div>';
        }
        body +=
            '<button type="button" class="btn primary dms-bill-topup-btn" data-bill-topup="1">' +
            esc(t('dms-bill-topup-open')) +
            '</button>';
        return '<div class="dms-bill-card">' + body + '</div>';
    }

    // 当前套餐卡:订阅态(进度条 + 取消)/ 已取消(徽标 warn + 说明 · 无取消钮)/ 无订阅(引导看套餐)。
    function planNowCard(sub) {
        var inner;
        if (!sub) {
            inner =
                '<div class="none">' +
                esc(t('dms-bill-plan-none')) +
                '</div><div class="none-sub">' +
                esc(t('dms-bill-plan-none-sub')) +
                '</div><span class="dms-bill-jump" id="dms-bill-jump-plans">' +
                esc(t('dms-bill-view-plans')) +
                '</span>';
        } else {
            var used = sub.pages_used_this_cycle || 0;
            var quota = sub.quota || 0;
            var rem = Math.max(0, quota - used);
            var pct = quota ? Math.min(100, Math.round((used / quota) * 100)) : 0;
            var cancelled = sub.status === 'cancelled';
            inner =
                '<span class="dms-bill-sub-badge ' +
                (cancelled ? 'warn' : 'ok') +
                '">' +
                esc(cancelled ? t('dms-bill-st-cancelled') : t('dms-bill-st-active')) +
                '</span><div class="dms-bill-sub-name">' +
                esc(t('dms-bill-plan-name-fmt', { code: sub.plan_code })) +
                '</div><div class="dms-bill-sub-hint">' +
                esc(t('dms-bill-plan-over-fmt', { rate: fmtRate(sub.over_rate).slice(1) })) +
                ' · ' +
                esc(t('dms-bill-plan-cycle')) +
                ' ' +
                esc(fmtDate(sub.cycle_end)) +
                '</div><div class="dms-bill-prog"><span style="width:' +
                pct +
                '%"></span></div><div class="dms-bill-usage-line">' +
                esc(t('dms-bill-plan-used')) +
                ' <b>' +
                esc(fmtInt(used)) +
                '</b> / ' +
                esc(fmtInt(quota)) +
                ' ' +
                esc(t('dms-bill-used-unit')) +
                ' · ' +
                esc(t('dms-bill-remaining')) +
                ' <b>' +
                esc(fmtInt(rem)) +
                '</b></div>' +
                (cancelled
                    ? '<div class="dms-bill-sub-note">' +
                      esc(t('dms-bill-plan-cancelled')) +
                      '</div>'
                    : '<button type="button" class="btn dms-bill-cancel-btn" data-bill-cancel="1">' +
                      esc(t('dms-bill-plan-cancel')) +
                      '</button>');
        }
        return (
            '<div class="dms-bill-card dms-bill-plan-now"><h2>' +
            esc(t('dms-bill-plan-title')) +
            '</h2>' +
            inner +
            '</div>'
        );
    }

    function onePlan(p, currentCode) {
        var isCurrent = currentCode && p.code === currentCode;
        var btn = isCurrent
            ? '<button type="button" class="btn" disabled>' +
              esc(t('dms-bill-current-badge')) +
              '</button>'
            : '<button type="button" class="btn primary" data-bill-sub="' +
              esc(p.code) +
              '">' +
              esc(currentCode ? t('dms-bill-switch') : t('dms-bill-subscribe')) +
              '</button>';
        return (
            '<div class="dms-bill-plan' +
            (isCurrent ? ' current' : '') +
            '"><div class="dms-bill-plan-top"><div class="dms-bill-plan-letter">' +
            esc(p.code) +
            '</div><div><div class="dms-bill-plan-name">' +
            esc(t('dms-bill-plan-name-fmt', { code: p.code })) +
            '</div><div class="dms-bill-plan-price">' +
            esc(fmtInt(p.fee)) +
            ' <span>' +
            esc(t('dms-bill-per-month')) +
            '</span></div></div></div><ul class="dms-bill-feats"><li>' +
            CHECK +
            esc(t('dms-bill-plan-quota-fmt', { n: fmtInt(p.quota) })) +
            '</li><li>' +
            CHECK +
            esc(t('dms-bill-plan-over-fmt', { rate: fmtRate(p.over_rate).slice(1) })) +
            '</li></ul>' +
            btn +
            '</div>'
        );
    }
    function storeCards(plans, currentCode) {
        var cards = (plans || [])
            .map(function (p) {
                return onePlan(p, currentCode);
            })
            .join('');
        return (
            '<div class="dms-bill-card" id="dms-bill-plans-card"><h2>' +
            esc(t('dms-bill-store-title')) +
            '</h2><p class="sub">' +
            esc(t('dms-bill-store-sub')) +
            '</p><div class="dms-bill-plans">' +
            cards +
            '</div></div>'
        );
    }

    // 记录明细卡外壳:头(标题 + 导出)+ 双 tab;筛选/列表/分页由 records 控制器填 #dms-bill-rec-body。
    function recordsCard(activeTab) {
        function tab(id, key) {
            return (
                '<button type="button" class="dms-bill-rec-tab' +
                (activeTab === id ? ' on' : '') +
                '" data-bill-rectab="' +
                id +
                '">' +
                esc(t(key)) +
                '</button>'
            );
        }
        return (
            '<div class="dms-bill-card"><div class="dms-bill-rec-head"><div class="dms-bill-rec-tabs">' +
            tab('usage', 'dms-bill-rec-tab-usage') +
            tab('topup', 'dms-bill-rec-tab-topup') +
            '</div><button type="button" class="btn" id="dms-bill-rec-export">' +
            esc(t('dms-bill-rec-export')) +
            '</button></div><div id="dms-bill-rec-body"></div></div>'
        );
    }

    root.DXBILLINGHTML = {
        BANK: BANK,
        CHECK: CHECK,
        fmtBaht: fmtBaht,
        fmtInt: fmtInt,
        fmtRate: fmtRate,
        fmtDate: fmtDate,
        page: page,
        state: state,
        employee: employee,
        balanceCard: balanceCard,
        planNowCard: planNowCard,
        storeCards: storeCards,
        recordsCard: recordsCard,
    };
})(typeof self !== 'undefined' ? self : this);
