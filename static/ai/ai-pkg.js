/*
 * Pearnly AI · ai-pkg.js · 交付包视图(W5)编排:草稿卡 + 交付物下载 + 证据点验回链
 *
 * 契约:M1-施工任务包 W5 行 + §五状态诚实条款。数据源两条:getOrder(needs/blocked_reasons/
 * status,判草稿是否已生成)+ listDeliverables(五种交付物 + has_file + evidence_index 的
 * 逐数字证据)。证据模态框独立挂在 document.body(同 ai-review.js showToast 先例,不随
 * cv-pkg 的 innerHTML 重渲染被打断查看器实例)。
 *
 * 依赖 window.AI.state/format/api/viewer/pkgRender 与全局 at(),排在它们之后、ai-client.js
 * 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var NUM_LABEL_KEY = { output_vat: 'pkg_line_output', input_vat: 'pkg_line_input' };

    var S = null;
    var wired = false;

    function body() {
        return $('cv-pkg');
    }

    function freshState(api, order, clientId) {
        return {
            api: api,
            orderId: order.id,
            clientId: clientId,
            detail: null,
            deliverables: [],
            calcOpen: false,
            downloading: null,
            evid: null, // {numKey, label, entry, selectedItemId} | null
        };
    }

    function findDeliverable(kind) {
        return (S.deliverables || []).filter(function (d) {
            return d.kind === kind;
        })[0];
    }

    // ============ 渲染 ============

    function render() {
        body().innerHTML = AI.pkgRender.pageHtml({
            detail: S.detail,
            deliverables: S.deliverables,
            pp30: findDeliverable('pp30_draft'),
            calcOpen: S.calcOpen,
            downloading: S.downloading,
        });
        renderEvidModal();
    }

    function renderEvidModal() {
        var existing = $('pkgEvidMask');
        if (!S.evid) {
            if (existing) existing.remove();
            AI.viewer.remountViewer('pkg', null, {});
            return;
        }
        var html = AI.pkgRender.evidModalHtml(S.evid);
        if (existing) existing.outerHTML = html;
        else document.body.insertAdjacentHTML('beforeend', html);
        // 进场动效只在首开播一次:选证据行等状态变化走 outerHTML 重渲染,不重放。
        if (!existing) $('pkgEvidMask').classList.add('enter');

        var mask = $('pkgEvidMask');
        mask.querySelector('.mclose').onclick = closeEvid;
        mask.addEventListener('click', function (e) {
            if (e.target === mask) closeEvid();
        });
        mask.querySelectorAll('[data-action="pkg-evid-item"]').forEach(function (el) {
            el.onclick = function () {
                selectItem(el.getAttribute('data-item-id'));
            };
        });

        var items = (S.evid.entry && S.evid.entry.items) || [];
        var selected = items.filter(function (it) {
            return it.item_id === S.evid.selectedItemId;
        })[0];
        if (selected && AI.pkgRender.isImageFileName(selected.file_name)) {
            AI.viewer.remountViewer('pkg', mask.querySelector('.pkg-evid-view'), {
                key: selected.item_id,
                loader: itemImageLoader(selected.item_id),
            });
        } else {
            AI.viewer.remountViewer('pkg', null, {});
        }
    }

    function itemImageLoader(itemId) {
        return function () {
            return S.api.getItemImageBlob(S.orderId, itemId).then(function (blob) {
                return URL.createObjectURL(blob);
            });
        };
    }

    // ============ 拉数据 ============

    function loadDetail() {
        body().innerHTML = AI.state.loadingHtml();
        var session = S;
        Promise.all([S.api.getOrder(S.orderId), S.api.listDeliverables(S.orderId)])
            .then(function (r) {
                if (S !== session) return; // 已切走
                S.detail = r[0];
                S.deliverables = r[1].deliverables || [];
                render();
            })
            .catch(function () {
                if (S !== session) return;
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn) btn.onclick = loadDetail;
            });
    }

    // ============ 交互 ============

    function toggleCalc() {
        S.calcOpen = !S.calcOpen;
        render();
    }

    function openEvid(numKey) {
        var evidenceRow = findDeliverable('evidence_index');
        var entry = ((evidenceRow && evidenceRow.numbers) || {})[numKey] || {};
        S.evid = {
            numKey: numKey,
            label: at(NUM_LABEL_KEY[numKey] || numKey),
            entry: entry,
            selectedItemId: null,
        };
        renderEvidModal();
    }

    function closeEvid() {
        S.evid = null;
        renderEvidModal();
    }

    function selectItem(itemId) {
        if (!S.evid) return;
        S.evid.selectedItemId = itemId;
        renderEvidModal();
    }

    function download(kind) {
        if (S.downloading) return; // 禁双击重复触发(Canon §7:提交必有 loading 态)
        var session = S;
        S.downloading = kind;
        render();
        S.api
            .downloadDeliverable(S.orderId, kind)
            .then(function (r) {
                if (S !== session) return;
                var url = URL.createObjectURL(r.blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = r.filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            })
            .catch(function () {
                /* 下载失败:交付物在库里登记过却读不到文件是服务端异常,重试一次即可,
                 * 不在下载这种一次性动作上堆错误态 UI——按钮解禁即可再点。 */
            })
            .then(function () {
                if (S !== session) return;
                S.downloading = null;
                render();
            });
    }

    // ============ 事件接线 ============

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var a = el.getAttribute('data-action');
        if (a === 'pkg-evid') openEvid(el.getAttribute('data-num'));
        else if (a === 'pkg-calc') toggleCalc();
        else if (a === 'pkg-download') download(el.getAttribute('data-kind'));
    }

    function onKeydown(e) {
        if (e.key === 'Escape' && S && S.evid) {
            e.preventDefault();
            closeEvid();
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        body().addEventListener('click', onClick);
        document.addEventListener('keydown', onKeydown);
    }

    // ============ 挂载 ============

    function mount(api, order, clientId) {
        S = freshState(api, order, clientId);
        wireOnce();
        loadDetail();
    }

    // 离开交付包 tab 时被 ai-client.js 调用:证据模态框挂在 document.body(不在 cv-pkg
    // 的 innerHTML 里),tab 切走不会自动隐藏它,不主动收就会悬在别的视图上方。
    function onLeave() {
        if (S && S.evid) closeEvid();
    }

    window.AI = window.AI || {};
    window.AI.pkg = { mount: mount, onLeave: onLeave };
})();
