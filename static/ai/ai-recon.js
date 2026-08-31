/*
 * Pearnly AI · ai-recon.js · 银行对账(E2)区块编排:折叠开关 + 原图模态
 *
 * 挂在工单详情(wo 视图)的关键数字之下,数据源是 ai-client.js renderWo() 已取到的
 * order_detail().bank_recon(不再发第二次网络请求)。只读为主(MVP 拍板:不做改配
 * override,那是批次 M 的事),交互面只有折叠/展开四清单与点行看原图。
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

    function freshState(api, orderId, clientId, bankRecon, stalled) {
        return {
            api: api,
            orderId: orderId,
            clientId: clientId,
            bankRecon: bankRecon,
            // 对账没产出时用来分「还没跑到」和「后台停住了」两种 null(见 reconRender.pageHtml)。
            stalled: !!stalled,
            // 自动匹配默认折叠(已处理好的,不占版面);其余三张默认展开(需要会计过目)。
            open: { auto: false, review: true, missing: true, unmatched: true },
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
        // 进场动效只在首开播一次(同 ai-pkg.js renderEvidModal 先例)。
        if (!existing) mask.classList.add('enter');
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

    // ============ 事件委托 ============

    function onClick(e, container) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');
        if (action === 'brx-fold') toggleFold(el.getAttribute('data-kind'), container);
        else if (action === 'brx-view')
            openView(el.getAttribute('data-kind'), el.getAttribute('data-key'));
    }

    // ============ 挂载 ============
    // container 由调用方(ai-client.js renderWo)传入,bankRecon 是已取到的 order_detail
    // 字段——同一次 getOrder() 复用,不重复发请求。

    function mount(api, orderId, clientId, bankRecon, container, stalled) {
        S = freshState(api, orderId, clientId, bankRecon, stalled);
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
