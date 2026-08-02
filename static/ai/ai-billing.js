/*
 * Pearnly AI · ai-billing.js · 设置页计费区编排(B5 老站对齐 #16 · 挂 AI.billing)
 *
 * 老站退役后 /ai 用户看余额/充值的唯一入口。数据/事件编排 + 三步弹窗状态机,
 * HTML 全部来自 ai-billing-render.js 纯函数;端点全部现成(ai-api-billing.js),
 * 零新增钱逻辑。由 ai-settings.js 在渲染完设置页后挂载(mount(api, host))。
 *
 * 余额 30s 轮询照老站 billing.ts 语义:人工审核通过后停在设置页也能看到余额到账。
 * 只在设置页可见 + 老板视角 + 非豁免时真发请求;涨额就地重渲染余额与记录。
 */
(function (root) {
    'use strict';

    var POLL_MS = 30000;

    var S = null;
    var pollTimer = null;

    function R() {
        return root.AI.billingRender;
    }

    function settingsVisible() {
        var view = root.document.getElementById('v-settings');
        return !!(view && view.classList.contains('on'));
    }

    // ── 计费区(余额 + 充值记录)────────────────────────────────

    function renderSection() {
        S.host.innerHTML =
            R().balancePanelHtml(S.credits) +
            (S.credits && S.credits.balance_thb != null ? R().historyPanelHtml(S.history) : '');
    }

    function renderError() {
        S.host.innerHTML = root.AI.state.errorHtml({
            title: root.at('error_t'),
            sub: root.at('error_s'),
            retryLabel: root.at('retry'),
        });
    }

    function load() {
        var session = S;
        S.host.innerHTML = root.AI.state.loadingHtml();
        S.api
            .getCredits()
            .then(function (credits) {
                if (S !== session) return null;
                S.credits = credits;
                // 员工视角无余额也无充值权限(后端 owner_only),记录面板整个不请求不渲染。
                if (!credits || credits.balance_thb == null) {
                    renderSection();
                    return null;
                }
                return S.api.getTopupHistory().then(function (rows) {
                    if (S !== session) return;
                    S.history = rows || [];
                    renderSection();
                    startPoll();
                });
            })
            .catch(function () {
                if (S !== session) return;
                renderError();
            });
    }

    // 轮询只刷数据不动弹窗:涨额说明审核到账,余额与记录一起就地更新。
    function pollTick() {
        if (!S || root.document.hidden || !settingsVisible()) return;
        if (!S.credits || S.credits.balance_thb == null || S.credits.is_billing_exempt) return;
        var session = S;
        S.api
            .getCredits()
            .then(function (credits) {
                if (S !== session || !credits || credits.balance_thb == null) return;
                var grew = Number(credits.balance_thb) > Number(S.credits.balance_thb);
                S.credits = credits;
                if (!grew) return;
                return S.api.getTopupHistory().then(function (rows) {
                    if (S !== session) return;
                    S.history = rows || [];
                    renderSection();
                });
            })
            .catch(function () {
                /* 轮询失败不打扰:已展示内容仍是上次真实数据(状态诚实) */
            });
    }

    function startPoll() {
        if (pollTimer) return;
        pollTimer = root.setInterval(pollTick, POLL_MS);
    }

    // ── 三步充值弹窗 ─────────────────────────────────────────────

    function mask() {
        return root.document.getElementById('billTopupMask');
    }
    function $m(id) {
        return root.document.getElementById(id);
    }

    function showErr(key) {
        var el = $m('billErr');
        if (el) el.textContent = root.at(key);
    }

    function renderModal(firstOpen) {
        var existing = mask();
        var html = R().modalHtml(S.modal);
        if (existing) existing.outerHTML = html;
        else root.document.body.insertAdjacentHTML('beforeend', html);
        var m = mask();
        if (firstOpen) m.classList.add('enter');
        m.addEventListener('click', function (e) {
            if (e.target === m) closeModal();
            else onModalClick(e);
        });
        wireStepInputs();
    }

    function wireStepInputs() {
        var amt = $m('billAmt');
        if (amt) {
            amt.addEventListener('input', function () {
                S.modal.amount = amt.value;
                var el = $m('billErr');
                if (el) el.textContent = '';
                var msk = mask();
                msk.querySelectorAll('[data-bill-amt]').forEach(function (b) {
                    b.classList.toggle(
                        'on',
                        Number(b.getAttribute('data-bill-amt')) === Math.floor(Number(amt.value))
                    );
                });
            });
        }
        var dz = $m('billDz');
        var file = $m('billFile');
        if (dz && file) {
            dz.addEventListener('click', function () {
                file.click();
            });
            dz.addEventListener('dragover', function (e) {
                e.preventDefault();
                dz.classList.add('drag-over');
            });
            dz.addEventListener('dragleave', function () {
                dz.classList.remove('drag-over');
            });
            dz.addEventListener('drop', function (e) {
                e.preventDefault();
                dz.classList.remove('drag-over');
                onFile(e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]);
            });
            file.addEventListener('change', function () {
                onFile(file.files && file.files[0]);
            });
        }
    }

    // 选中文件存状态不存 <input>(步骤切换整体重渲染,input 的选择会丢;上传时用 S.modal.file)。
    function onFile(f) {
        if (!f) return;
        S.modal.file = f;
        S.modal.fileName = f.name;
        var dz = $m('billDz');
        if (dz) {
            dz.classList.add('has-file');
            dz.textContent = f.name;
        }
        var el = $m('billErr');
        if (el) el.textContent = '';
    }

    function captureStep3Inputs() {
        var payer = $m('billPayer');
        var note = $m('billNote');
        if (payer) S.modal.payerName = payer.value;
        if (note) S.modal.note = note.value;
    }

    function setStep(n) {
        if (S.modal.step === 3) captureStep3Inputs();
        S.modal.step = n;
        renderModal(false);
    }

    function setBusy(busy, labelKey) {
        S.modal.busy = busy;
        var next = mask() && mask().querySelector('[data-action="bill-next"]');
        if (next) {
            next.disabled = busy;
            if (labelKey) next.textContent = root.at(labelKey);
        }
    }

    function step1Next() {
        var amtRaw = ($m('billAmt') || {}).value || S.modal.amount;
        var errKey = R().topupAmountError(amtRaw);
        if (errKey) {
            showErr(errKey);
            return;
        }
        if (S.modal.busy) return;
        var amt = Math.floor(Number(amtRaw));
        setBusy(true);
        S.api
            .topupRequest(amt)
            .then(function (r) {
                S.modal.busy = false;
                S.modal.reqId = r.request_id;
                S.modal.amount = amt;
                setStep(2);
            })
            .catch(function () {
                setBusy(false);
                showErr('bill_req_fail');
            });
    }

    function step3Submit() {
        if (!S.modal.file) {
            showErr('bill_slip_required');
            return;
        }
        if (S.modal.busy) return;
        captureStep3Inputs();
        setBusy(true, 'bill_uploading');
        S.api
            .uploadTopupSlip(
                S.modal.reqId,
                S.modal.file,
                (S.modal.payerName || '').trim(),
                (S.modal.note || '').trim()
            )
            .then(function (r) {
                renderDone(!!r.auto_approved);
            })
            .catch(function () {
                setBusy(false, 'bill_btn_submit');
                showErr('bill_upload_fail');
            });
    }

    function renderDone(autoApproved) {
        S.modal.busy = false;
        S.modal.done = true;
        var body = $m('billStepBody');
        if (body) body.innerHTML = R().doneHtml(autoApproved);
        var m = mask();
        var back = m.querySelector('[data-action="bill-back"]');
        if (back) back.textContent = root.at('bill_btn_close');
        var next = m.querySelector('[data-action="bill-next"]');
        if (next) next.style.display = 'none';
        var steps = m.querySelector('.bill-steps');
        if (steps) steps.style.display = 'none';
        load(); // 余额/记录立即补真(自动入账当场可见;人工路径记录里多一条待审核)
    }

    function onModalClick(e) {
        if (e.target.closest('[data-action="bill-close"]')) return void closeModal();
        var qa = e.target.closest('[data-bill-amt]');
        if (qa) {
            S.modal.amount = Number(qa.getAttribute('data-bill-amt'));
            var amtEl = $m('billAmt');
            if (amtEl) amtEl.value = String(S.modal.amount);
            mask()
                .querySelectorAll('[data-bill-amt]')
                .forEach(function (b) {
                    b.classList.toggle('on', b === qa);
                });
            var errEl = $m('billErr');
            if (errEl) errEl.textContent = '';
            return;
        }
        if (e.target.closest('[data-action="bill-copy"]')) return void copyAcct(e);
        if (e.target.closest('[data-action="bill-back"]')) {
            if (S.modal.done || S.modal.step === 1) return void closeModal();
            return void setStep(S.modal.step - 1);
        }
        if (e.target.closest('[data-action="bill-next"]')) {
            if (S.modal.step === 1) return void step1Next();
            if (S.modal.step === 2) return void setStep(3);
            return void step3Submit();
        }
    }

    function copyAcct(e) {
        var btn = e.target.closest('[data-action="bill-copy"]');
        root.CopyFlash.copy(btn, R().BANK.digits, root.at('bill_copied'), { win: root });
    }

    function onKeydown(e) {
        if (e.key === 'Escape') closeModal();
    }

    function openTopup() {
        S.modal = {
            step: 1,
            reqId: null,
            amount: '',
            file: null,
            fileName: '',
            payerName: '',
            note: '',
            busy: false,
            done: false,
        };
        renderModal(true);
        root.document.addEventListener('keydown', onKeydown);
    }

    function closeModal() {
        S.modal = null;
        root.document.removeEventListener('keydown', onKeydown);
        var m = mask();
        if (m) m.remove();
    }

    function onHostClick(e) {
        if (e.target.closest('[data-action="bill-topup"]')) return void openTopup();
        if (e.target.closest('[data-action="retry"]')) return void load();
    }

    // host 是设置页里的容器 div(每次进设置页重建,监听不会重复叠加)。
    function mount(api, host) {
        S = { api: api, host: host, credits: null, history: [], modal: null };
        host.addEventListener('click', onHostClick);
        load();
    }

    root.AI = root.AI || {};
    root.AI.billing = { mount: mount };
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
