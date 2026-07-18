/* Pearnly DMS · 套餐与余额视图 · 逻辑层(挂 window.DXBILLING · 模板 dms-billing-html · 充值向导
 * dms-billing-topup · 记录明细 dms-billing-records)。照主站 subscription.ts/billing.ts 语义复刻。
 * 职责:拉 /api/me/credits + /api/me/subscription → 顶部双卡 + 套餐三卡 + 记录明细四态渲染;
 * 订阅(402→自动开充值弹窗)/取消(体系内 danger 确认)/充值(三步弹窗)接线;余额 30s 轮询兜底
 * (页面可见 + 停在计费视图 + 非豁免才轮,涨额 toast + 刷新)。老板/员工判据:credits 无 balance_thb 即员工。 */
(function (root) {
    'use strict';
    function H() {
        return root.DXBILLINGHTML;
    }
    function api() {
        return root.DXAPI.create();
    }
    function t(k, v) {
        return typeof root.t === 'function' ? root.t(k, v) : k;
    }
    function toast(msg, kind) {
        if (typeof root.showToast === 'function') root.showToast(msg, kind);
    }

    var S = { host: null, busy: false, isExempt: false, pollTimer: null, lastBal: null };

    function load(host) {
        S.host = host;
        S.busy = false;
        host.innerHTML = H().state('loading', t('dms-bill-loading'), false);
        api()
            .getCredits()
            .then(function (credits) {
                if (credits.balance_thb === undefined) {
                    stopPoll();
                    host.innerHTML = H().employee();
                    return null;
                }
                return api()
                    .getSubscription()
                    .then(function (sub) {
                        renderOwner(host, credits, sub || {});
                    });
            })
            .catch(function () {
                host.innerHTML = H().state('error', t('dms-bill-error'), true);
            });
    }

    function renderOwner(host, credits, sub) {
        var subscription = sub.subscription || null;
        var plans = sub.plans || [];
        var currentCode = subscription ? subscription.plan_code : '';
        S.isExempt = !!(sub.is_billing_exempt || credits.is_billing_exempt);
        S.lastBal = credits.balance_thb;
        host.innerHTML = H().page(
            '<div class="dms-bill-top">' +
                H().planNowCard(subscription) +
                '<div id="dms-bill-balance-wrap">' +
                H().balanceCard(credits, S.isExempt) +
                '</div></div>' +
                H().storeCards(plans, currentCode) +
                H().recordsCard('usage')
        );
        var recCard = host.querySelector('#dms-bill-rec-body');
        if (recCard && recCard.closest('.dms-bill-card')) {
            root.DXBILLRECORDS.mount(recCard.closest('.dms-bill-card'));
        }
        startPoll();
    }

    function refreshBalance() {
        api()
            .getCredits()
            .then(function (c) {
                if (!c || c.balance_thb === undefined) return;
                S.lastBal = c.balance_thb;
                var bw = S.host && S.host.querySelector('#dms-bill-balance-wrap');
                if (bw) bw.innerHTML = H().balanceCard(c, S.isExempt);
                if (root.DXBILLRECORDS && root.DXBILLRECORDS.reload) root.DXBILLRECORDS.reload();
            })
            .catch(function () {
                /* 刷新失败不影响已展示内容(状态诚实) */
            });
    }

    function openTopup() {
        root.DXBILLTOPUP.open({ onClose: refreshBalance });
    }

    function doSubscribe(code) {
        var host = S.host;
        if (S.busy) return;
        S.busy = true;
        var btn = host.querySelector('[data-bill-sub="' + code + '"]');
        var label = btn ? btn.textContent : '';
        if (btn) {
            btn.disabled = true;
            btn.textContent = t('dms-bill-subscribing');
        }
        api()
            .subscribe(code)
            .then(function () {
                toast(t('dms-bill-sub-ok'), 'success');
                load(host);
            })
            .catch(function (err) {
                S.busy = false;
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = label;
                }
                if (err && err.status === 402) {
                    toast(t('dms-err-insufficient_balance'), 'error');
                    openTopup(); // 402 自动开充值弹窗(照主站 _openTopupModal)
                } else {
                    toast(t('dms-bill-sub-fail'), 'error');
                }
            });
    }

    function doCancel() {
        if (S.busy) return;
        root.pearnlyConfirm(t('dms-bill-cancel-confirm')).then(function (ok) {
            if (!ok) return;
            S.busy = true;
            api()
                .cancelSubscription()
                .then(function () {
                    toast(t('dms-bill-cancel-ok'), 'success');
                    load(S.host);
                })
                .catch(function () {
                    S.busy = false;
                    toast(t('dms-bill-cancel-fail'), 'error');
                });
        });
    }

    function onClick(e) {
        var host = S.host;
        if (e.target.closest('#dms-bill-retry')) return void load(host);
        if (e.target.closest('[data-bill-topup]')) return void openTopup();
        if (e.target.closest('#dms-bill-jump-plans')) {
            var card = host.querySelector('#dms-bill-plans-card');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
            return;
        }
        var sb = e.target.closest('[data-bill-sub]');
        if (sb) return void doSubscribe(sb.getAttribute('data-bill-sub'));
        if (e.target.closest('[data-bill-cancel]')) return void doCancel();
    }

    // ── 余额 30s 轮询(照主站 billing.ts:涨额 toast + 刷新;隐藏/离开计费视图/豁免时跳过)──
    function stopPoll() {
        if (S.pollTimer) {
            clearInterval(S.pollTimer);
            S.pollTimer = null;
        }
    }
    function pollTick() {
        if (document.hidden || S.isExempt) return;
        var view = document.getElementById('dms-view-billing');
        if (!view || !view.classList.contains('on')) return;
        var tk = '';
        try {
            tk = localStorage.getItem('mrpilot_token') || '';
        } catch (e) {
            tk = '';
        }
        if (!tk) return;
        api()
            .getCredits()
            .then(function (c) {
                var bal = c && c.balance_thb;
                if (bal === undefined) return;
                if (S.lastBal !== null && bal > S.lastBal) {
                    toast(t('dms-bill-credits-updated'), 'success');
                    refreshBalance();
                }
                S.lastBal = bal;
            })
            .catch(function () {});
    }
    function startPoll() {
        stopPoll();
        if (S.isExempt) return;
        S.pollTimer = setInterval(pollTick, 30000);
    }

    function mount(hostSel) {
        var host = document.querySelector(hostSel);
        if (!host) return;
        if (!host._billingWired) {
            host.addEventListener('click', onClick);
            host._billingWired = true;
        }
        load(host);
    }

    root.DXBILLING = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
