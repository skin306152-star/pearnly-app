/*
 * Pearnly AI · ai-recon.js · 银行对账(E2)区块编排:折叠开关 + 原图模态 + 推 LINE 待问
 *
 * 挂在工单详情(wo 视图)的关键数字之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().bank_recon(不再发第二次网络请求)。只读为主(MVP 拍板:不做改配
 * override,那是批次 M 的事),交互面只有三件事:折叠/展开四清单、点行看原图、
 * 缺票行推 LINE 待问——后两件都是复用既有端点(GET .../items/{id}/image、
 * POST /api/ai/client-pool/stage),本文件不新造持久化。
 *
 * 依赖 window.AI.state/format/viewer/reconRender/api 与全局 at(),排在 ai-recon-render.js
 * 之后、ai-client.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;

    function freshState(api, orderId, clientId, bankRecon) {
        return {
            api: api,
            orderId: orderId,
            clientId: clientId,
            bankRecon: bankRecon,
            // 自动匹配默认折叠(已处理好的,不占版面);其余三张默认展开(需要会计过目)。
            open: { auto: false, review: true, missing: true, unmatched: true },
            missing: {}, // idx -> {busy, done, errKey}(推 LINE 待问状态,按缺票行独立持有)
            view: null, // {kind:'invoice'|'bank', key} | null(原图模态)
        };
    }

    function render(container) {
        if (!S) return;
        container.innerHTML = AI.reconRender.pageHtml(S.bankRecon, S, S.clientId);
        renderViewModal();
    }

    // ============ 原图模态(v4 .pkg-mask 复用,挂 document.body——同 ai-pkg.js 证据
    // 模态先例,不在 cv-wo 的 innerHTML 里,tab 切走不会自动隐藏,靠 onLeave 收) ============

    function itemImageLoader(itemId) {
        return function () {
            return S.api.getItemImageBlob(S.orderId, itemId).then(function (blob) {
                return URL.createObjectURL(blob);
            });
        };
    }

    function renderViewModal() {
        var existing = $('brxViewMask');
        if (!S.view) {
            if (existing) existing.remove();
            AI.viewer.remountViewer('brx', null, {});
            return;
        }
        var html = AI.reconRender.viewModalHtml(S.view);
        if (existing) existing.outerHTML = html;
        else document.body.insertAdjacentHTML('beforeend', html);
        var mask = $('brxViewMask');
        mask.querySelector('.mclose').onclick = closeView;
        mask.addEventListener('click', function (e) {
            if (e.target === mask) closeView();
        });
        AI.viewer.remountViewer('brx', mask.querySelector('.pkg-evid-view'), {
            key: S.view.key,
            loader: itemImageLoader(S.view.key),
        });
    }

    function openView(kind, key) {
        if (!key) return;
        S.view = { kind: kind, key: key };
        renderViewModal();
    }

    function closeView() {
        S.view = null;
        renderViewModal();
    }

    // ============ 折叠开关 ============

    function toggleFold(kind, container) {
        if (!(kind in S.open)) return;
        S.open[kind] = !S.open[kind];
        render(container);
    }

    // ============ 缺票行:推 LINE 待问(复用 /api/ai/client-pool/stage,不新造端点)============

    function stageMissing(idx, container) {
        var entry = ((S.bankRecon || {}).missing_invoice || [])[idx];
        var bankItemId = ((S.bankRecon || {}).bank_item_ids || [])[0];
        var note = at('brx_pool_note_tpl', {
            date: entry.tx_date || '—',
            dir: entry.direction === 'IN' ? at('brx_tx_in') : at('brx_tx_out'),
            amount: AI.format.money(entry.amount),
        });
        var payload = AI.reconRender.buildMissingStagePayload(bankItemId, note);
        if (!payload) return;
        var session = S; // 快照——回调落地时若已切走(换客户/换账期重挂)一律不认。
        S.missing[idx] = { busy: true };
        render(container);
        S.api
            .stageQuestion(S.orderId, payload)
            .then(function () {
                if (S !== session) return;
                S.missing[idx] = { done: true };
                render(container);
            })
            .catch(function (err) {
                if (S !== session) return;
                var key = AI.api.mapApiErrorKey(err && err.code);
                S.missing[idx] = {
                    errKey: key !== 'err_generic' && at(key) !== key ? key : 'brx_pool_err',
                };
                render(container);
            });
    }

    // ============ 事件委托 ============

    function onClick(e, container) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');
        if (action === 'brx-fold') toggleFold(el.getAttribute('data-kind'), container);
        else if (action === 'brx-view') openView(el.getAttribute('data-kind'), el.getAttribute('data-key'));
        else if (action === 'brx-stage') stageMissing(Number(el.getAttribute('data-idx')), container);
    }

    // ============ 挂载 ============
    // container 由调用方(ai-client.js renderWo)传入,bankRecon 是已取到的 order_detail
    // 字段——同一次 getOrder() 复用,不重复发请求。

    function mount(api, orderId, clientId, bankRecon, container) {
        S = freshState(api, orderId, clientId, bankRecon);
        container.onclick = function (e) {
            onClick(e, container);
        };
        render(container);
    }

    // 离开 wo tab:原图模态挂在 document.body,tab 切走不会自动隐藏,须主动收
    // (同 ai-pkg.js onLeave 先例)。
    function onLeave() {
        if (S && S.view) closeView();
    }

    window.AI = window.AI || {};
    window.AI.recon = { mount: mount, onLeave: onLeave };
})();
