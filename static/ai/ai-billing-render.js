/*
 * Pearnly AI · ai-billing-render.js · 设置页计费区纯函数 + HTML 拼装(B5 老站对齐 #16)
 *
 * 照老站 src/home/billing.ts 三步充值流复刻语义(金额→转账→凭证,Jakob:/home、/dms
 * 已验证过的同一套支付范式),视觉走 /ai 自己的令牌系(.panel/.btn/.st-badge)。
 * 不碰 DOM,只拼字符串——编排/事件在 ai-billing.js。UMD 同 ai-state.js 先例,
 * tests/unit/test_ai_billing_render.py 用真 node 跑本文件断言。
 */
(function (root) {
    'use strict';

    // 收款账户为固定值(非 i18n,与 /home、/dms 同源常量)。
    var BANK = {
        name: 'ธนาคาร กรุงเทพ',
        branch: 'สาขาโชคชัย 4 ลาดพร้าว',
        acct: '230-0-91368-4',
        holder: 'บจ. มิสเตอร์ อี อาร์ พี',
        digits: '2300913684',
    };
    var QUICK = [100, 500, 1000, 2000];
    var MIN_THB = 10;
    var MAX_THB = 500000; // 后端 _TopupRequestBody le=500000,前端先挡一步免白跑网络

    // 浏览器走 at()(ai-i18n.js 必先加载);node(单测)无词典 → 回退「key + 插值参数」,
    // 让"金额有没有真传进文案"在 node 里可断言,而不是被回退静默吞掉。
    function t(k, v) {
        if (typeof root.at === 'function') return root.at(k, v);
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
    function money(v) {
        if (root && root.AI && root.AI.format && typeof root.AI.format.money === 'function') {
            return root.AI.format.money(v);
        }
        return String(v);
    }

    // 快捷金额是整千整百,不带小数位(照老站 ฿100/฿500 的显示口径)。
    function fmtBahtInt(n) {
        return '฿' + Number(n || 0).toLocaleString('en-US');
    }

    // 金额校验:整数化后 <10/解不出 → invalid,>500000 → max,合法 → null(错误即 i18n key)。
    function topupAmountError(raw) {
        var amt = Math.floor(Number(raw));
        if (!isFinite(amt) || amt < MIN_THB) return 'bill_amt_invalid';
        if (amt > MAX_THB) return 'bill_amt_max';
        return null;
    }

    // 充值申请状态 → 状态词典色族(B1:全站状态的脸只从 ai-states.css 取)。
    function statusChipCls(status) {
        if (status === 'approved') return 'st-ok';
        if (status === 'rejected') return 'st-err';
        if (status === 'pending') return 'st-wait';
        return 'st-off';
    }

    function fmtDate(iso) {
        var d = new Date(String(iso || ''));
        if (isNaN(d.getTime())) return '—';
        var p = function (x) {
            return (x < 10 ? '0' : '') + x;
        };
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
    }

    function metricCell(label, value) {
        return (
            '<div class="cell"><div class="lb">' +
            esc(label) +
            '</div><div class="v">' +
            value +
            '</div></div>'
        );
    }

    // 余额面板:老板=余额/本月用量/费率三格 + 充值按钮;员工=只报自己用量,不露钱
    // (口径随后端:/api/me/credits 员工视角本就无 balance_thb,前端不猜)。
    //
    // 员工分支还是失败卡「去充值」深链的落点(#/settings?focus=billing)。只留一句「余额与
    // 充值仅负责人可见」就是死胡同:文案许了出路,落地一个可点的都没有。补一句说清该找谁、
    // 让谁在哪儿点——这是员工手上真能走的唯一一条路,不是安慰话。
    function balancePanelHtml(credits) {
        var c = credits || {};
        var body;
        if (c.balance_thb == null) {
            body =
                '<p class="bill-emp-hint">' +
                esc(t('bill_employee_hint')) +
                '</p><p class="bill-emp-path">' +
                esc(t('bill_employee_topup_path')) +
                '</p>' +
                (c.my_invoice_count != null
                    ? '<p class="bill-emp-count">' +
                      esc(t('bill_employee_count', { n: c.my_invoice_count })) +
                      '</p>'
                    : '');
        } else {
            body =
                '<div class="wosum">' +
                metricCell(
                    t('bill_balance_label'),
                    '<span class="bill-balance-v">' + esc(money(c.balance_thb)) + '</span>'
                ) +
                metricCell(
                    t('bill_month_label'),
                    esc(t('bill_pages_fmt', { n: Number(c.pages_this_month || 0) }))
                ) +
                metricCell(
                    t('bill_rate_label'),
                    esc(
                        t('bill_rate_fmt', {
                            r: money(c.current_rate != null ? c.current_rate : 1.5),
                        })
                    )
                ) +
                '</div>' +
                (c.is_billing_exempt
                    ? '<div class="bill-exempt"><span class="st-badge st-ok">' +
                      esc(t('bill_exempt')) +
                      '</span></div>'
                    : '') +
                '<div class="bill-actions"><button type="button" class="btn pri" data-action="bill-topup">' +
                esc(t('bill_topup_open')) +
                '</button></div>';
        }
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(t('bill_title')) +
            '</h3></div><div class="bd">' +
            body +
            '</div></div>'
        );
    }

    function historyRowHtml(r) {
        var noteText = r.status === 'rejected' && r.review_note ? r.review_note : '';
        return (
            '<div class="bill-hrow"><span class="d">' +
            esc(fmtDate(r.created_at)) +
            '</span><span class="amt">' +
            esc(money(r.amount_thb)) +
            '</span><span class="st-badge ' +
            statusChipCls(r.status) +
            '">' +
            esc(t('bill_st_' + r.status)) +
            '</span>' +
            (noteText ? '<span class="bill-hnote">' + esc(noteText) + '</span>' : '') +
            '</div>'
        );
    }

    // 充值记录面板:空态指路(去点上方充值按钮),不是干巴巴的"暂无数据"。
    function historyPanelHtml(rows) {
        var list = rows || [];
        var body;
        if (!list.length) {
            var emptyHtml =
                root && root.AI && root.AI.state
                    ? root.AI.state.emptyHtml({
                          title: t('bill_history_empty_t'),
                          sub: t('bill_history_empty_s'),
                      })
                    : esc(t('bill_history_empty_t'));
            body = emptyHtml;
        } else {
            body = '<div data-state="ok">' + list.map(historyRowHtml).join('') + '</div>';
        }
        return (
            '<div class="panel"><div class="hd"><h3>' +
            esc(t('bill_history_title')) +
            '</h3></div><div class="bd">' +
            body +
            '</div></div>'
        );
    }

    function stepsBarHtml(step) {
        function one(n, key) {
            return (
                '<div class="bill-step' +
                (step >= n ? ' on' : '') +
                '"><span class="bill-dot">' +
                n +
                '</span><span>' +
                esc(t(key)) +
                '</span></div>'
            );
        }
        return (
            '<div class="bill-steps">' +
            one(1, 'bill_step1') +
            '<div class="bill-line"></div>' +
            one(2, 'bill_step2') +
            '<div class="bill-line"></div>' +
            one(3, 'bill_step3') +
            '</div>'
        );
    }

    function step1Html(m) {
        var quick = QUICK.map(function (a) {
            return (
                '<button type="button" class="btn bill-qamt' +
                (Number(m.amount) === a ? ' on' : '') +
                '" data-bill-amt="' +
                a +
                '">' +
                esc(fmtBahtInt(a)) +
                '</button>'
            );
        }).join('');
        return (
            '<label class="bill-lb" for="billAmt">' +
            esc(t('bill_amt_label')) +
            '</label><div class="bill-qamts">' +
            quick +
            '</div><input type="number" min="10" step="1" class="bill-input" id="billAmt" value="' +
            (m.amount ? esc(String(m.amount)) : '') +
            '" placeholder="' +
            esc(t('bill_amt_ph')) +
            '"><div class="bill-err" id="billErr"></div>'
        );
    }

    function step2Html(m) {
        return (
            '<p class="bill-lb">' +
            esc(t('bill_bank_label')) +
            '</p><div class="bill-bank"><div class="bn">' +
            esc(BANK.name) +
            '</div><div class="bb">' +
            esc(BANK.branch) +
            '</div><div class="ba-row"><span class="ba">' +
            esc(BANK.acct) +
            '</span><button type="button" class="btn sm" data-action="bill-copy">' +
            esc(t('bill_copy')) +
            '</button></div><div class="bh">' +
            esc(BANK.holder) +
            '</div></div><div class="bill-warn">' +
            esc(t('bill_bank_note', { amount: money(m.amount) })) +
            '</div>'
        );
    }

    function step3Html(m) {
        return (
            '<input type="file" id="billFile" accept="image/*,.pdf" style="display:none"><div class="bill-dz' +
            (m.fileName ? ' has-file' : '') +
            '" id="billDz">' +
            esc(m.fileName || t('bill_slip_drop')) +
            '</div><label class="bill-lb" for="billPayer">' +
            esc(t('bill_payer_label')) +
            '</label><input type="text" maxlength="200" class="bill-input" id="billPayer" value="' +
            esc(m.payerName || '') +
            '"><label class="bill-lb" for="billNote">' +
            esc(t('bill_note_label')) +
            '</label><input type="text" maxlength="500" class="bill-input" id="billNote" value="' +
            esc(m.note || '') +
            '"><div class="bill-err" id="billErr"></div>'
        );
    }

    // 三步弹窗骨架:pkg-mask/pkg-modal 通用模态外壳(ai-client-new.js 同款复用先例)。
    function modalHtml(m) {
        var body = m.step === 1 ? step1Html(m) : m.step === 2 ? step2Html(m) : step3Html(m);
        return (
            '<div class="pkg-mask on" id="billTopupMask"><div class="pkg-modal bill-modal" role="dialog" aria-modal="true">' +
            '<div class="mh"><div><h3>' +
            esc(t('bill_topup_title')) +
            '</h3></div><button class="mclose" type="button" data-action="bill-close" aria-label="' +
            esc(t('bill_btn_close')) +
            '">&times;</button></div>' +
            '<div class="mb" style="grid-template-columns:1fr">' +
            stepsBarHtml(m.step) +
            '<div id="billStepBody">' +
            body +
            '</div>' +
            '<div class="bill-foot"><button type="button" class="btn" data-action="bill-back">' +
            esc(t(m.step === 1 ? 'bill_btn_cancel' : 'bill_btn_back')) +
            '</button><button type="button" class="btn pri" data-action="bill-next">' +
            esc(t(m.step === 3 ? 'bill_btn_submit' : 'bill_btn_next')) +
            '</button></div>' +
            '</div></div></div>'
        );
    }

    // 收尾态:自动核验入账(绿勾)vs 转人工审核(黄钟)——两种结果如实分开说,
    // 不许把"收到凭证待审"说成"已入账"(状态诚实)。
    function doneHtml(autoApproved) {
        var icon = autoApproved
            ? '<svg viewBox="0 0 44 44" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="22" cy="22" r="19"/><path d="M14 22.5l5.5 5.5L31 16"/></svg>'
            : '<svg viewBox="0 0 44 44" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="22" cy="22" r="19"/><path d="M22 13v10l6 4"/></svg>';
        return (
            '<div class="bill-done ' +
            (autoApproved ? 'ok' : 'wait') +
            '"><div class="ic">' +
            icon +
            '</div><div class="msg">' +
            esc(t(autoApproved ? 'bill_auto_ok' : 'bill_manual')) +
            '</div></div>'
        );
    }

    var api = {
        BANK: BANK,
        QUICK: QUICK,
        fmtBahtInt: fmtBahtInt,
        fmtDate: fmtDate,
        topupAmountError: topupAmountError,
        statusChipCls: statusChipCls,
        balancePanelHtml: balancePanelHtml,
        historyPanelHtml: historyPanelHtml,
        modalHtml: modalHtml,
        doneHtml: doneHtml,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.billingRender = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
