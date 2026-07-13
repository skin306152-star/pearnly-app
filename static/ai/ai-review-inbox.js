/*
 * Pearnly AI · ai-review-inbox.js · 全所审核收件箱(MC1-b2)编排:三分区聚合页
 *
 * 方案:桌面\pearnly ai\设计稿\MC1b-审核队列与签批闭环-方案.md §2 b2。接管 `#/pool`
 * 顶层路由(window.AI.pool = {mount, onLeave},取代此前只有「客户待答」一块的旧实现):
 *   ① 待审工单(GET review-queue,到期近→前)+ 签批闭环按钮,状态机在
 *      ai-review-inbox-signoff.js。
 *   ② 异常票据(按 flag_reason 跨工单分组的裁决卡三件套 + 批量/逐张键盘流),状态机在
 *      ai-review-inbox-flagged.js——本文件只管挂载/渲染分发/toast,不重复业务逻辑。
 *   ③ 客户待答:原样委托 ai-client-pool.js(现更名 AI.clientPool,腾出 AI.pool 给本
 *      文件),挂进自己的子容器,零改动零回归。
 *
 * 依赖 window.AI.state/format/api/reviewRender/reviewInboxRender/reviewInboxSignoff/
 * reviewInboxFlagged/clientPool 与全局 at(),排在它们之后、ai.js 之前加载。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false;
    var focusedFlag = null; // 键盘流当前聚焦的组(点组头/组内元素时更新,跨渲染保留)。

    function woBody() {
        return $('riqWoBody');
    }
    function flaggedBody() {
        return $('riqFlaggedBody');
    }

    // 同 ai-review.js currentActorLabel 先例:本次刚提交的动作没有服务端 actor 回显,
    // 用当前登录态占位,刷新后从服务端读到的值会是同一个字符串。
    function currentActorLabel() {
        var token = localStorage.getItem('mrpilot_token');
        var name = AI.format.jwtDisplayName(token);
        if (name) return name;
        var payload = AI.format.jwtPayload(token);
        return payload && payload.sub ? 'user:' + payload.sub : '';
    }

    function freshState(api) {
        return {
            api: api,
            loading: true,
            error: false,
            queue: null,
            signoff: AI.reviewInboxSignoff.create(api),
            flagged: AI.reviewInboxFlagged.create(api, {
                onChange: function () {
                    renderFlagged();
                },
                afterMutate: function () {
                    renderWo();
                    startProgressPoll();
                },
                showToast: AI.reviewRender.showToast,
            }),
            actorLabel: currentActorLabel(),
            refreshTimer: null,
            pollAttempt: 0,
            pollBaseline: {},
        };
    }

    // ============ 渲染 ============

    // 两个分区共用同一副 loading/error 外壳,只有 loading 判据与内容拼装不同。
    function renderSection(el, loading, contentFn) {
        if (!el || !S) return;
        if (loading) {
            el.innerHTML = AI.state.loadingHtml();
            return;
        }
        if (S.error) {
            el.innerHTML = AI.state.errorHtml({
                title: at('error_t'),
                sub: at('error_s'),
                retryLabel: at('retry'),
            });
            var btn = el.querySelector('[data-action="retry"]');
            if (btn) btn.onclick = load;
            return;
        }
        el.innerHTML = contentFn();
    }

    function renderWo() {
        renderSection(woBody(), S && S.loading, function () {
            var uiByOrder = {};
            (S.queue.clients || []).forEach(function (c) {
                c.orders.forEach(function (o) {
                    uiByOrder[o.work_order_id] = S.signoff.forOrder(o.work_order_id);
                });
            });
            return AI.reviewInboxRender.woSectionHtml(S.queue.clients || [], uiByOrder);
        });
    }

    function renderFlagged() {
        renderSection(flaggedBody(), S && S.loading, function () {
            return AI.reviewInboxRender.flaggedSectionHtml(
                S.flagged.groups(),
                S.flagged.groupUiMap()
            );
        });
    }

    // ============ 加载(review-queue 一次带回工单卡 + 跨工单 flagged item feed) ============

    function load() {
        S.loading = true;
        S.error = false;
        renderWo();
        renderFlagged();
        var session = S;
        S.api
            .getReviewQueue()
            .then(function (data) {
                if (S !== session) return;
                S.queue = data;
                S.loading = false;
                renderWo();
                S.flagged.setFeed(data.flagged_items || []); // 后端下发,不再逐单 getOrder(F1)
            })
            .catch(function () {
                if (S !== session) return;
                S.loading = false;
                S.error = true;
                renderWo();
                renderFlagged();
            });
    }

    // 裁决落库后引擎自驱重跑(review→running→…→review)是异步的:指数退避有限次轮询
    // review-queue(F10),复用进度读模型语义(running 工单从队列消失、跑完回 review 才重现),
    // 每轮刷工单卡 + feed,直到基线内工单都落定或退避次数用尽。替掉此前单发 2.5s 猜时器。
    function startProgressPoll() {
        S.pollAttempt = 0;
        S.pollBaseline = AI.reviewProgress.baseline(S.queue);
        scheduleNextPoll();
    }

    function scheduleNextPoll() {
        var delay = AI.reviewProgress.nextDelayMs(S.pollAttempt);
        if (delay == null) return; // 退避次数用尽,停轮询
        if (S.refreshTimer) clearTimeout(S.refreshTimer);
        var session = S;
        S.refreshTimer = setTimeout(function () {
            S.api.getReviewQueue().then(function (data) {
                if (S !== session) return;
                S.queue = data;
                S.flagged.setFeed(data.flagged_items || []);
                renderWo();
                S.pollAttempt += 1;
                if (!AI.reviewProgress.settled(data, S.pollBaseline)) scheduleNextPoll();
            });
        }, delay);
    }

    // ============ 异常票据分区:事件委托 → 交给 flagged 状态机 ============
    // toast 收敛在 AI.reviewRender.showToast/hideToast(与单工单人审队列共用)。

    function onFlaggedClick(e) {
        var groupEl = e.target.closest('.riq-group');
        if (groupEl) focusedFlag = groupEl.getAttribute('data-flag');
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');
        var itemId = el.getAttribute('data-item');
        var flagReason = el.getAttribute('data-flag');
        if (action === 'riq-bulk') S.flagged.onBulk(flagReason);
        else if (action === 'riq-exclude-all') S.flagged.onExcludeAll(flagReason);
        else if (action === 'riq-accept') S.flagged.decideItem(itemId, 'accept');
        else if (action === 'riq-edit') {
            S.flagged.startEdit(itemId, function () {
                var input = flaggedBody().querySelector(
                    '.riq-vat-input[data-item="' + itemId + '"]'
                );
                if (input) {
                    input.focus();
                    input.select();
                }
            });
        } else if (action === 'riq-exclude') S.flagged.decideItem(itemId, 'exclude');
        else if (action === 'riq-dir-purchase') S.flagged.decideItem(itemId, 'assign_purchase');
        else if (action === 'riq-dir-sales') S.flagged.decideItem(itemId, 'assign_sales');
        else if (action === 'riq-dir-nontax') S.flagged.decideItem(itemId, 'assign_nontax');
        else if (action === 'riq-recalc-submit') {
            var input2 = flaggedBody().querySelector('.riq-vat-input[data-item="' + itemId + '"]');
            S.flagged.decideItem(itemId, 'recalc', input2 ? input2.value : '');
        } else if (action === 'riq-view-img') {
            S.flagged.viewImage(el.getAttribute('data-wo'), itemId);
        }
    }

    // E 键(逐张审):把当前组第一张未裁决的票滚入视口并高亮,不切一套新 UI——按钮/键盘
    // 对同一张卡效力相同,高亮只是视觉引导(同 Canon §7 微动效,120-200ms)。
    function focusItemEl(itemId) {
        var prev = flaggedBody().querySelector('.riq-item-focus');
        if (prev) prev.classList.remove('riq-item-focus');
        var el = flaggedBody().querySelector('[data-item="' + itemId + '"]');
        if (el) {
            el.classList.add('riq-item-focus');
            el.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
    }

    function onKeydown(e) {
        var view = $('v-pool');
        if (!view || !view.classList.contains('on')) return;
        var tag = e.target && e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        if (!focusedFlag) return;
        var group = S.flagged.findGroup(focusedFlag);
        if (!group) return;
        if (e.key === 'a' || e.key === 'A') {
            e.preventDefault();
            S.flagged.onBulk(focusedFlag);
        } else if (e.key === 'x' || e.key === 'X') {
            e.preventDefault();
            S.flagged.onExcludeAll(focusedFlag);
        } else if (e.key === 'e' || e.key === 'E') {
            e.preventDefault();
            var next = S.flagged.firstUndecidedItem(group);
            if (next) focusItemEl(next.item_id);
        }
    }

    // ============ 待审工单分区:事件委托 → 交给 signoff 状态机 ============

    function onWoClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');
        var orderId = el.getAttribute('data-wo');
        if (!orderId) return;
        if (action === 'riq-signoff') S.signoff.signoff(orderId, S.actorLabel, renderWo);
        else if (action === 'riq-archive') S.signoff.archive(orderId, S.actorLabel, renderWo);
        else if (action === 'riq-reject-open') S.signoff.openReject(orderId, renderWo);
        else if (action === 'riq-reject-cancel') S.signoff.cancelReject(orderId, renderWo);
        else if (action === 'riq-reject-submit') S.signoff.submitReject(orderId, renderWo, load);
        else if (action === 'riq-self-declare') S.signoff.selfDeclare(orderId, renderWo);
    }

    function onWoInput(e) {
        var ta = e.target.closest('.riq-reject-textarea');
        if (ta) S.signoff.setRejectValue(ta.getAttribute('data-wo'), ta.value);
    }

    function onWoChange(e) {
        var fileInput = e.target.closest('.riq-receipt-input');
        if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
        S.signoff.attachReceipt(fileInput.getAttribute('data-wo'), fileInput.files[0], renderWo);
    }

    // ============ 挂载 ============

    function wireOnce() {
        if (wired) return;
        wired = true;
        woBody().addEventListener('click', onWoClick);
        woBody().addEventListener('input', onWoInput);
        woBody().addEventListener('change', onWoChange);
        flaggedBody().addEventListener('click', onFlaggedClick);
        document.addEventListener('keydown', onKeydown);
        var refreshBtn = $('riqRefreshBtn');
        if (refreshBtn) refreshBtn.addEventListener('click', load);
    }

    function mount(api) {
        S = freshState(api);
        focusedFlag = null;
        wireOnce();
        load();
        AI.clientPool.mount(api);
    }

    function onLeave() {
        AI.reviewRender.hideToast();
        if (S) {
            if (S.refreshTimer) clearTimeout(S.refreshTimer);
            S.flagged.closeImage(); // 原图模态挂 document.body,切走路由要主动收
        }
        if (AI.clientPool) AI.clientPool.onLeave();
    }

    window.AI = window.AI || {};
    window.AI.pool = { mount: mount, onLeave: onLeave };
})();
