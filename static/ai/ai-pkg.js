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
            // 三键(M1-3KEY)出口态:signed 后本键翻「已标记待签」;exporting/signing/returning
            // 是各自请求在途的防重入闸;notice = {type:'ok'|'err', text} 出口动作的人话回执/报错。
            signed: false,
            signedActor: '',
            signing: false,
            exporting: false,
            returning: false,
            notice: null,
        };
    }

    // 签批人展示名:同 ai-review.js 先例,用当前登录态展示名(不回读服务端 actor)——
    // 邮箱前缀 → JWT 名 → sub 短八位,绝不拼 "user:<uuid>" 糊脸。
    function currentActorLabel() {
        return AI.format.actorLabel(null, localStorage.getItem('mrpilot_token'));
    }

    function errNotice(err) {
        return { type: 'err', text: at(AI.api.mapApiErrorKey(err && err.code)) };
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
            signed: S.signed,
            signedActor: S.signedActor,
            signing: S.signing,
            exporting: S.exporting,
            returning: S.returning,
            notice: S.notice,
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

    // 缺料卡「去收料补」(2026-07-14 UI 记债 #3):照既有 tab 切换机制跳收料 tab,
    // 不另造路由(同 wireChrome() 里 tab 按钮走 AI.router.buildClientHash 同一条路)。
    function gotoIntake() {
        window.location.hash = AI.router.buildClientHash(S.clientId, 'intake');
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
                AI.api.saveBlob(r);
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

    // ============ 三键出口(M1-3KEY) ============

    // 键一「确认无误,标记待签」= 既有 POST /review(复核签批,append-only);成功翻「已标记
    // 待签 · 签批人」态。SoD 422 / 冻结 409 走 errNotice 人话直出(与审核收件箱同端点同语义)。
    function signOff() {
        if (S.signed || S.signing) return;
        var session = S;
        S.signing = true;
        S.notice = null;
        render();
        S.api
            .reviewSignoff(S.orderId, '')
            .then(function () {
                if (S !== session) return;
                S.signed = true;
                S.signedActor = currentActorLabel();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.notice = errNotice(err);
            })
            .then(function () {
                if (S !== session) return;
                S.signing = false;
                render();
            });
    }

    // 键二「导出分录到 Express」= GET /entries-export(读侧派生 xlsx),拿 blob 触发下载。
    // 无影子分录后端 404 no_shadow_entries → errNotice(前端按钮本已按信号 disabled,兜底提示)。
    function exportEntries() {
        if (S.exporting) return;
        var session = S;
        S.exporting = true;
        S.notice = null;
        render();
        S.api
            .downloadEntriesExport(S.orderId)
            .then(function (r) {
                if (S !== session) return;
                AI.api.saveBlob(r);
            })
            .catch(function (err) {
                if (S !== session) return;
                S.notice = errNotice(err);
            })
            .then(function () {
                if (S !== session) return;
                S.exporting = false;
                render();
            });
    }

    // 键三「退回工单」= reason 必填(500 上限对齐后端)→ 既有 POST /review-reject。成功后状态
    // 翻 running,重拉详情整页重渲染(键随新状态禁用)。run_in_progress 409 → errNotice 人话。
    function returnOrder() {
        if (S.returning) return;
        var reason = (window.prompt(at('pkg_return_reason_prompt')) || '').trim();
        if (!reason) return; // 取消 / 空:不发请求
        var session = S;
        S.returning = true;
        S.notice = null;
        render();
        S.api
            .reviewReject(S.orderId, reason.slice(0, 500))
            .then(function () {
                if (S !== session) return;
                S.returning = false;
                // 退回使工单重开:此前的「已标记待签」标记随之作废,不留一个矛盾的旧签批态。
                S.signed = false;
                S.signedActor = '';
                S.notice = { type: 'ok', text: at('pkg_returned_done') };
                loadDetail();
            })
            .catch(function (err) {
                if (S !== session) return;
                S.returning = false;
                S.notice = errNotice(err);
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
        else if (a === 'pkg-go-intake') gotoIntake();
        else if (a === 'pkg-sign') signOff();
        else if (a === 'pkg-export') exportEntries();
        else if (a === 'pkg-return') returnOrder();
        else if (a === 'pkg-goto-pool') {
            window.location.hash = AI.router.buildPoolHash();
        }
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
