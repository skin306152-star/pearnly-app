/* Pearnly DMS · 套餐与余额视图 · HTML 模板层(挂 window.DXBILLINGHTML)。
 * 纯字符串构建,不含事件/请求(逻辑在 dms-billing.js · 同 dms-intake-html 分片先例)。
 * 金额一律走 fmtBaht(฿ 千分位);所有文案走 t()(四语)。收款账户为固定值(非 i18n)。 */
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
    // ฿ 千分位:整数不带小数,非整数保留 2 位(不引入 float 噪声)。
    function fmtBaht(n) {
        var num = Number(n || 0);
        var frac = Math.round(num % 1 ? 2 : 0);
        return (
            '฿' +
            num.toLocaleString('en-US', { minimumFractionDigits: frac, maximumFractionDigits: 2 })
        );
    }
    function fmtInt(n) {
        return Number(n || 0).toLocaleString('en-US');
    }
    function fmtDate(v) {
        if (!v) return '—';
        var d = new Date(v);
        if (isNaN(d.getTime())) return String(v);
        var p = function (x) {
            return (x < 10 ? '0' : '') + x;
        };
        return (
            d.getFullYear() +
            '-' +
            p(d.getMonth() + 1) +
            '-' +
            p(d.getDate()) +
            ' ' +
            p(d.getHours()) +
            ':' +
            p(d.getMinutes())
        );
    }

    // 固定收款账户(与主站 src/home/billing.ts 一致 · 银行资料非译文,四语共用)。
    var BANK = {
        name: 'ธนาคาร กรุงเทพ',
        branch: 'สาขาโชคชัย 4 ลาดพร้าว',
        acct: '230-0-91368-4',
        holder: 'บจ. มิสเตอร์ อี อาร์ พี',
    };
    var QUICK_AMOUNTS = [100, 500, 1000, 2000];

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
    // 员工空态:整视图仅老板可操作(判据由逻辑层给出,无 balance_thb 即员工)。
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
            '<div class="dms-bill-rule"><div class="rt">' +
            esc(t('dms-bill-rule-title')) +
            '</div><div class="rb">' +
            esc(t('dms-bill-rule-body')) +
            '</div></div>';
        return '<div class="dms-bill-card">' + body + '</div>';
    }

    function planCard(sub) {
        var inner;
        if (!sub) {
            inner =
                '<div class="none">' +
                esc(t('dms-bill-plan-none')) +
                '</div><div class="none-sub">' +
                esc(t('dms-bill-plan-none-sub')) +
                '</div>';
        } else {
            inner =
                '<span class="pill">' +
                esc(t('dms-bill-plan-name-fmt', { code: sub.plan_code })) +
                '</span><div class="row">' +
                metric(
                    t('dms-bill-plan-remain'),
                    t('dms-bill-used-fmt', { n: fmtInt(sub.remaining) })
                ) +
                metric(t('dms-bill-plan-cycle'), fmtDate(sub.cycle_end)) +
                '</div>';
            inner +=
                sub.auto_renew === false
                    ? '<div class="cancelled">' + esc(t('dms-bill-plan-cancelled')) + '</div>'
                    : '';
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
            ? '<button type="button" class="btn" data-bill-cancel="1">' +
              esc(t('dms-bill-plan-cancel')) +
              '</button>'
            : '<button type="button" class="btn primary" data-bill-sub="' +
              esc(p.code) +
              '">' +
              esc(currentCode ? t('dms-bill-switch') : t('dms-bill-subscribe')) +
              '</button>';
        return (
            '<div class="dms-bill-plan' +
            (isCurrent ? ' current' : '') +
            '">' +
            (isCurrent ? '<div class="fact">' + esc(t('dms-bill-current-badge')) + '</div>' : '') +
            '<div class="code">' +
            esc(p.code) +
            '</div><div class="fee">' +
            esc(t('dms-bill-plan-fee-fmt', { fee: fmtInt(p.fee) })) +
            '</div><div class="fact">' +
            esc(t('dms-bill-plan-quota-fmt', { n: fmtInt(p.quota) })) +
            '</div><div class="fact">' +
            esc(t('dms-bill-plan-over-fmt', { rate: p.over_rate })) +
            '</div>' +
            btn +
            '</div>'
        );
    }
    function storeCards(plans, currentCode) {
        var cards = (plans || []).map(function (p) {
            return onePlan(p, currentCode);
        });
        return (
            '<div class="dms-bill-card"><h2>' +
            esc(t('dms-bill-store-title')) +
            '</h2><p class="sub">' +
            esc(t('dms-bill-store-sub')) +
            '</p><div class="dms-bill-plans">' +
            cards.join('') +
            '</div></div>'
        );
    }

    // 充值卡:head + 可切换的 body(step1 金额 / step2 转账+上传 / done 回执)。
    function topupCard() {
        return (
            '<div class="dms-bill-card"><h2>' +
            esc(t('dms-bill-topup-title')) +
            '</h2><p class="sub">' +
            esc(t('dms-bill-topup-sub')) +
            '</p><div id="dms-bill-topup-body">' +
            topupStep1() +
            '</div></div>'
        );
    }
    function topupStep1() {
        var quick = QUICK_AMOUNTS.map(function (a) {
            return (
                '<button type="button" class="btn dms-bill-qamt" data-bill-qamt="' +
                a +
                '">' +
                esc(fmtBaht(a)) +
                '</button>'
            );
        }).join('');
        return (
            '<div class="dms-bill-qamts">' +
            quick +
            '</div><input type="number" min="10" step="1" class="dms-bill-input" id="dms-bill-amt" placeholder="' +
            esc(t('dms-bill-topup-amt-ph')) +
            '"><div class="dms-bill-err" id="dms-bill-amt-err" style="display:none"></div>' +
            '<div class="dms-bill-upload-row"><button type="button" class="btn primary" id="dms-bill-topup-next">' +
            esc(t('dms-bill-topup-next')) +
            '</button></div>'
        );
    }
    function topupStep2(reqId, amount) {
        return (
            '<p class="sub">' +
            esc(t('dms-bill-topup-bank')) +
            ' · ' +
            esc(fmtBaht(amount)) +
            '</p><div class="dms-bill-bank"><div class="bn">' +
            esc(BANK.name) +
            '</div><div class="bb">' +
            esc(BANK.branch) +
            '</div><div class="ba">' +
            esc(BANK.acct) +
            '</div><div class="bh">' +
            esc(BANK.holder) +
            '</div></div><div class="dms-bill-reqid">' +
            esc(t('dms-bill-topup-reqid-fmt', { id: reqId })) +
            '</div><div class="dms-bill-note">' +
            esc(t('dms-bill-topup-note')) +
            '</div><div class="dms-bill-upload-row"><input type="file" id="dms-bill-slip" accept="image/*,.pdf" style="display:none"><button type="button" class="btn primary" id="dms-bill-slip-pick">' +
            esc(t('dms-bill-topup-pick')) +
            '</button><span class="dms-bill-note" style="margin:0">' +
            esc(t('dms-bill-topup-upload-hint')) +
            '</span></div><div class="dms-bill-err" id="dms-bill-slip-err" style="display:none"></div>'
        );
    }
    function topupDone(autoApproved) {
        var ok = !!autoApproved;
        return (
            '<div class="dms-bill-topup-done ' +
            (ok ? 'ok' : 'wait') +
            '"><div class="ic">' +
            (ok ? '✓' : '⏳') +
            '</div><div class="msg">' +
            esc(ok ? t('dms-bill-topup-auto-ok') : t('dms-bill-topup-manual')) +
            '</div><button type="button" class="btn" id="dms-bill-topup-again">' +
            esc(t('dms-bill-topup-again')) +
            '</button></div>'
        );
    }

    function histStatus(s) {
        if (s === 'approved')
            return '<span class="dms-badge ok">' + esc(t('dms-bill-hist-approved')) + '</span>';
        if (s === 'rejected')
            return '<span class="dms-badge fail">' + esc(t('dms-bill-hist-rejected')) + '</span>';
        return '<span class="dms-badge pending">' + esc(t('dms-bill-hist-pending')) + '</span>';
    }
    function historyCard(items) {
        var inner;
        if (!items || !items.length) {
            inner =
                '<div class="dms-state empty"><p>' + esc(t('dms-bill-hist-empty')) + '</p></div>';
        } else {
            inner = items
                .slice(0, 20)
                .map(function (r) {
                    return (
                        '<div class="dms-bill-hist-row"><span class="time">' +
                        esc(fmtDate(r.created_at)) +
                        '</span><span class="amt">' +
                        esc(fmtBaht(r.amount_thb)) +
                        '</span>' +
                        histStatus(r.status) +
                        '</div>'
                    );
                })
                .join('');
        }
        return (
            '<div class="dms-bill-card"><h2>' +
            esc(t('dms-bill-hist-title')) +
            '</h2>' +
            inner +
            '</div>'
        );
    }

    root.DXBILLINGHTML = {
        fmtBaht: fmtBaht,
        page: page,
        state: state,
        employee: employee,
        balanceCard: balanceCard,
        planCard: planCard,
        storeCards: storeCards,
        topupCard: topupCard,
        topupStep1: topupStep1,
        topupStep2: topupStep2,
        topupDone: topupDone,
        historyCard: historyCard,
    };
})(typeof self !== 'undefined' ? self : this);
