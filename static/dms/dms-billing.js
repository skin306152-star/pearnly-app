/* Pearnly DMS · 套餐与余额视图 · 逻辑层(挂 window.DXBILLING · 模板在 dms-billing-html.js)。
 * 职责:拉 /api/me/credits + /api/me/subscription + 充值记录 → 四态渲染;订阅/取消/充值三流程接线。
 * 老板/员工判据:credits 响应无 balance_thb 即员工(整视图落「仅限老板」空态)。计费端点全用
 * get_current_user 鉴权,entry=dms token 直调(不走 require_perm)。语言切换由 boot 重挂 mount 重渲。
 * 事件监听在 mount 一次性挂到 host(重渲不掉),避免语言重挂叠加。 */
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
    function showErr(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.style.display = '';
    }

    var S = { host: null, busy: false, reqId: null, amount: 0, isExempt: false };

    function load(host) {
        S.host = host;
        S.busy = false;
        S.reqId = null;
        host.innerHTML = H().state('loading', t('dms-bill-loading'), false);
        api()
            .getCredits()
            .then(function (credits) {
                // 员工视角:后端只回 my_invoice_count,无 balance_thb → 整视图落老板专属空态。
                if (credits.balance_thb === undefined) {
                    host.innerHTML = H().employee();
                    return null;
                }
                return Promise.all([api().getSubscription(), api().topupHistory()]).then(
                    function (res) {
                        renderOwner(host, credits, res[0] || {}, res[1] || []);
                    }
                );
            })
            .catch(function () {
                host.innerHTML = H().state('error', t('dms-bill-error'), true);
            });
    }

    function renderOwner(host, credits, sub, history) {
        var subscription = sub.subscription || null;
        var plans = sub.plans || [];
        var currentCode = subscription ? subscription.plan_code : '';
        S.isExempt = !!(sub.is_billing_exempt || credits.is_billing_exempt);
        host.innerHTML = H().page(
            '<div id="dms-bill-balance-wrap">' +
                H().balanceCard(credits, S.isExempt) +
                '</div>' +
                H().planCard(subscription) +
                H().storeCards(plans, currentCode) +
                H().topupCard() +
                '<div id="dms-bill-hist-wrap">' +
                H().historyCard(history) +
                '</div>'
        );
    }

    // 充值/自动到账后就地刷新余额卡 + 记录卡(不重渲整页,保留充值回执面)。
    function refreshAfterTopup() {
        Promise.all([api().getCredits(), api().topupHistory()])
            .then(function (res) {
                var bw = S.host.querySelector('#dms-bill-balance-wrap');
                if (bw && res[0] && res[0].balance_thb !== undefined) {
                    bw.innerHTML = H().balanceCard(res[0], S.isExempt);
                }
                var hw = S.host.querySelector('#dms-bill-hist-wrap');
                if (hw) hw.innerHTML = H().historyCard(res[1] || []);
            })
            .catch(function () {
                /* 刷新失败不影响已展示的回执面(状态诚实:回执自身仍准确) */
            });
    }

    function doTopupRequest() {
        var host = S.host;
        var amtEl = host.querySelector('#dms-bill-amt');
        var errEl = host.querySelector('#dms-bill-amt-err');
        var amt = Math.floor(Number((amtEl && amtEl.value) || 0));
        if (!(amt >= 10)) return void showErr(errEl, t('dms-bill-topup-min'));
        if (S.busy) return;
        S.busy = true;
        var btn = host.querySelector('#dms-bill-topup-next');
        if (btn) btn.disabled = true;
        api()
            .topupRequest(amt)
            .then(function (res) {
                S.reqId = res.request_id;
                S.amount = amt;
                host.querySelector('#dms-bill-topup-body').innerHTML = H().topupStep2(
                    res.request_id,
                    amt
                );
            })
            .catch(function () {
                toast(t('dms-bill-topup-req-fail'), 'error');
                if (btn) btn.disabled = false;
            })
            .then(function () {
                S.busy = false;
            });
    }

    function doUploadSlip(file) {
        var host = S.host;
        if (!file || S.busy || !S.reqId) return;
        S.busy = true;
        var errEl = host.querySelector('#dms-bill-slip-err');
        var pick = host.querySelector('#dms-bill-slip-pick');
        if (pick) {
            pick.disabled = true;
            pick.textContent = t('dms-bill-topup-uploading');
        }
        api()
            .uploadSlip(S.reqId, file)
            .then(function (res) {
                host.querySelector('#dms-bill-topup-body').innerHTML = H().topupDone(
                    !!res.auto_approved
                );
                refreshAfterTopup();
            })
            .catch(function () {
                showErr(errEl, t('dms-bill-topup-fail'));
                if (pick) {
                    pick.disabled = false;
                    pick.textContent = t('dms-bill-topup-pick');
                }
            })
            .then(function () {
                S.busy = false;
            });
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
                load(host); // 全量重渲:反映新套餐 + 扣费后余额
            })
            .catch(function (err) {
                S.busy = false;
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = label;
                }
                if (err && err.status === 402) {
                    toast(t('dms-err-insufficient_balance'), 'error');
                    var body = host.querySelector('#dms-bill-topup-body');
                    if (body) body.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
        var q = e.target.closest('[data-bill-qamt]');
        if (q) {
            var amtEl = host.querySelector('#dms-bill-amt');
            if (amtEl) amtEl.value = q.getAttribute('data-bill-qamt');
            return;
        }
        if (e.target.closest('#dms-bill-topup-next')) return void doTopupRequest();
        if (e.target.closest('#dms-bill-slip-pick')) {
            var f = host.querySelector('#dms-bill-slip');
            if (f) f.click();
            return;
        }
        if (e.target.closest('#dms-bill-topup-again')) {
            S.reqId = null;
            host.querySelector('#dms-bill-topup-body').innerHTML = H().topupStep1();
            return;
        }
        var sb = e.target.closest('[data-bill-sub]');
        if (sb) return void doSubscribe(sb.getAttribute('data-bill-sub'));
        if (e.target.closest('[data-bill-cancel]')) return void doCancel();
    }

    function onChange(e) {
        if (e.target && e.target.id === 'dms-bill-slip') {
            doUploadSlip(e.target.files && e.target.files[0]);
        }
    }

    function mount(hostSel) {
        var host = document.querySelector(hostSel);
        if (!host) return;
        if (!host._billingWired) {
            host.addEventListener('click', onClick);
            host.addEventListener('change', onChange);
            host._billingWired = true;
        }
        load(host);
    }

    root.DXBILLING = { mount: mount };
})(typeof self !== 'undefined' ? self : this);
