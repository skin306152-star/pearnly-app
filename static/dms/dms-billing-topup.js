/* Pearnly DMS · 充值三步弹窗向导(挂 window.DXBILLTOPUP · 照主站 billing.ts 状态机复刻)。
 * 步1 金额(四快捷 + 自由输入 min10 max500000)→ POST topup/request;步2 银行卡 + 复制账号 +
 * 恰好金额警告;步3 点击/拖拽上传凭证(+付款人/备注选填)→ POST upload-slip/{id}。
 * auto_approved=true → success toast;否则 info toast。× / 遮罩 / ESC 关闭;每次 open 全复位。
 * 用 dms-shell 的 .modal-overlay/.modal 原子 + dms-billing.css 的步骤条/上传区。 */
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
    function api() {
        return root.DXAPI.create();
    }
    function toast(m, k) {
        if (typeof root.showToast === 'function') root.showToast(m, k || 'info');
    }
    function H() {
        return root.DXBILLINGHTML;
    }

    var QUICK = [100, 500, 2000, 5000];
    var MIN = 10;
    var MAX = 500000;
    var DONE_OK =
        '<svg viewBox="0 0 44 44" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="22" cy="22" r="19"/><path d="M14 22.5l5.5 5.5L31 16"/></svg>';
    var DONE_WAIT =
        '<svg viewBox="0 0 44 44" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="22" cy="22" r="19"/><path d="M22 13v10l6 4"/></svg>';

    var S = { ov: null, step: 1, reqId: null, amount: 0, file: null, busy: false, onClose: null };

    function $(id) {
        return S.ov ? S.ov.querySelector('#' + id) : null;
    }
    function stepsBar() {
        function dot(n) {
            return (
                '<div class="dms-bill-step-dot' +
                (S.step >= n ? ' active' : '') +
                '">' +
                n +
                '</div>'
            );
        }
        return (
            '<div class="dms-bill-steps">' +
            dot(1) +
            '<div class="dms-bill-step-line"></div>' +
            dot(2) +
            '<div class="dms-bill-step-line"></div>' +
            dot(3) +
            '</div>'
        );
    }
    function step1() {
        var quick = QUICK.map(function (a) {
            return (
                '<button type="button" class="btn dms-bill-qamt" data-tv-amt="' +
                a +
                '">' +
                esc(H().fmtBaht(a)) +
                '</button>'
            );
        }).join('');
        return (
            '<div class="dms-bill-step on" data-step="1"><label class="dms-bill-field"><span>' +
            esc(t('dms-bill-topup-amt-label')) +
            '</span><div class="dms-bill-qamts">' +
            quick +
            '</div><input type="number" min="10" step="1" class="dms-bill-input" id="tv-amt" placeholder="' +
            esc(t('dms-bill-topup-amt-ph')) +
            '"></label><div class="dms-bill-err" id="tv-amt-err" style="display:none"></div><p class="sub" style="margin-top:10px">' +
            esc(t('dms-bill-rule-body')) +
            '</p></div>'
        );
    }
    function step2() {
        var B = H().BANK;
        return (
            '<div class="dms-bill-step" data-step="2"><div class="dms-bill-bank"><div class="bn">' +
            esc(B.name) +
            '</div><div class="bb">' +
            esc(B.branch) +
            '</div><div class="ba-row"><span class="ba">' +
            esc(B.acct) +
            '</span><button type="button" class="btn small" id="tv-copy">' +
            esc(t('dms-bill-topup-copy')) +
            '</button></div><div class="bh">' +
            esc(B.holder) +
            '</div></div><div class="dms-bill-warn" id="tv-warn"></div></div>'
        );
    }
    function step3() {
        return (
            '<div class="dms-bill-step" data-step="3"><input type="file" id="tv-file" accept="image/*,.pdf" style="display:none"><div class="dms-bill-dz" id="tv-dz">' +
            esc(t('dms-bill-topup-slip-drop')) +
            '</div><div class="dms-bill-field"><span>' +
            esc(t('dms-bill-topup-payer')) +
            '</span><input type="text" class="dms-bill-input" id="tv-payer"></div><div class="dms-bill-field"><span>' +
            esc(t('dms-bill-topup-note-label')) +
            '</span><input type="text" class="dms-bill-input" id="tv-note"></div><div class="dms-bill-err" id="tv-slip-err" style="display:none"></div></div>'
        );
    }
    function shell() {
        return (
            '<div class="modal"><div class="modal-head">' +
            esc(t('dms-bill-topup-title')) +
            '</div><div class="modal-body" id="tv-body">' +
            stepsBar() +
            step1() +
            step2() +
            step3() +
            '</div><div class="dms-bill-modal-foot"><button type="button" class="btn" id="tv-back">' +
            esc(t('dms-bill-topup-cancel')) +
            '</button><button type="button" class="btn primary" id="tv-next">' +
            esc(t('dms-bill-topup-next-btn')) +
            '</button></div></div>'
        );
    }

    function setStep(n) {
        S.step = n;
        S.ov.querySelectorAll('.dms-bill-step').forEach(function (el) {
            el.classList.toggle('on', el.getAttribute('data-step') === String(n));
        });
        var bar = S.ov.querySelector('.dms-bill-steps');
        if (bar) bar.outerHTML = stepsBar();
        var back = $('tv-back');
        var next = $('tv-next');
        if (back)
            back.textContent = n === 1 ? t('dms-bill-topup-cancel') : t('dms-bill-topup-back');
        if (next) {
            next.style.display = '';
            next.disabled = false;
            next.textContent = n === 3 ? t('dms-bill-topup-submit') : t('dms-bill-topup-next-btn');
        }
        if (n === 2) {
            var w = $('tv-warn');
            if (w)
                w.innerHTML = t('dms-bill-topup-banknote', { amount: esc(H().fmtBaht(S.amount)) });
        }
    }

    function step1Next() {
        var el = $('tv-amt');
        var err = $('tv-amt-err');
        var amt = Math.floor(Number((el && el.value) || 0));
        if (!(amt >= MIN)) return void showErr(err, t('dms-bill-topup-min'));
        if (amt > MAX) return void showErr(err, t('dms-bill-topup-max'));
        if (S.busy) return;
        S.busy = true;
        var next = $('tv-next');
        if (next) {
            next.disabled = true;
            next.textContent = '…';
        }
        api()
            .topupRequest(amt)
            .then(function (r) {
                S.reqId = r.request_id;
                S.amount = amt;
                S.busy = false;
                setStep(2);
            })
            .catch(function () {
                S.busy = false;
                showErr(err, t('dms-bill-topup-req-fail'));
                if (next) {
                    next.disabled = false;
                    next.textContent = t('dms-bill-topup-next-btn');
                }
            });
    }
    function submitSlip() {
        var err = $('tv-slip-err');
        if (!S.file) return void showErr(err, t('dms-bill-topup-slip-required'));
        if (S.busy) return;
        S.busy = true;
        var next = $('tv-next');
        if (next) {
            next.disabled = true;
            next.textContent = t('dms-bill-topup-uploading');
        }
        var payer = ($('tv-payer') || {}).value || '';
        var note = ($('tv-note') || {}).value || '';
        api()
            .uploadSlip(S.reqId, S.file, payer, note)
            .then(function (r) {
                renderDone(!!r.auto_approved);
                toast(
                    r.auto_approved ? t('dms-bill-topup-auto-ok') : t('dms-bill-topup-manual'),
                    r.auto_approved ? 'success' : 'info'
                );
            })
            .catch(function () {
                S.busy = false;
                showErr(err, t('dms-bill-topup-fail'));
                if (next) {
                    next.disabled = false;
                    next.textContent = t('dms-bill-topup-submit');
                }
            });
    }
    function renderDone(ok) {
        S.busy = false;
        var body = $('tv-body');
        if (body)
            body.innerHTML =
                '<div class="dms-bill-done ' +
                (ok ? 'ok' : 'wait') +
                '"><div class="ic">' +
                (ok ? DONE_OK : DONE_WAIT) +
                '</div><div class="msg">' +
                esc(ok ? t('dms-bill-topup-auto-ok') : t('dms-bill-topup-manual')) +
                '</div></div>';
        var back = $('tv-back');
        if (back) back.textContent = t('dms-op-modal-close');
        var next = $('tv-next');
        if (next) next.style.display = 'none';
        if (typeof S.onClose === 'function') S.onClose(); // 刷新余额/记录(回执面仍在)
    }
    function showErr(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.style.display = '';
    }

    function onNext() {
        if (S.step === 1) return void step1Next();
        if (S.step === 2) return void setStep(3);
        submitSlip();
    }
    function onBack() {
        if (S.step === 1) return void close();
        if (S.step === 3) return void setStep(2);
        setStep(1);
    }
    function copyAcct() {
        var digits = '2300913684';
        var btn = $('tv-copy');
        function flash() {
            if (!btn) return;
            var prev = btn.textContent;
            btn.textContent = t('dms-bill-topup-copied');
            setTimeout(function () {
                btn.textContent = prev;
            }, 1500);
        }
        try {
            navigator.clipboard.writeText(digits).then(flash, flash);
        } catch (e) {
            flash();
        }
    }
    function onFile(f) {
        if (!f) return;
        S.file = f;
        var dz = $('tv-dz');
        if (dz) {
            dz.classList.add('has-file');
            dz.textContent = f.name;
        }
    }

    function wire() {
        $('tv-next').addEventListener('click', onNext);
        $('tv-back').addEventListener('click', onBack);
        S.ov.querySelectorAll('[data-tv-amt]').forEach(function (b) {
            b.addEventListener('click', function () {
                var amtEl = $('tv-amt');
                if (amtEl) amtEl.value = b.getAttribute('data-tv-amt');
                S.ov.querySelectorAll('[data-tv-amt]').forEach(function (x) {
                    x.classList.toggle('on', x === b);
                });
            });
        });
        var copy = $('tv-copy');
        if (copy) copy.addEventListener('click', copyAcct);
        var dz = $('tv-dz');
        var file = $('tv-file');
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
    function onKey(e) {
        if (e.key === 'Escape') close();
    }
    function close() {
        document.removeEventListener('keydown', onKey);
        if (S.ov) {
            S.ov.remove();
            S.ov = null;
        }
    }

    function open(opts) {
        opts = opts || {};
        close();
        S.step = 1;
        S.reqId = null;
        S.amount = 0;
        S.file = null;
        S.busy = false;
        S.onClose = opts.onClose || null;
        var ov = document.createElement('div');
        ov.className = 'modal-overlay';
        ov.innerHTML = shell();
        document.body.appendChild(ov);
        S.ov = ov;
        ov.addEventListener('click', function (e) {
            if (e.target === ov) close();
        });
        document.addEventListener('keydown', onKey);
        wire();
        setStep(1);
    }

    root.DXBILLTOPUP = { open: open, close: close };
})(typeof self !== 'undefined' ? self : this);
