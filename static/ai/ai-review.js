/*
 * Pearnly AI · ai-review.js · 人审队列(W3 · 产品心脏)编排:键盘流 + 乐观 UI + 续跑轮询
 *
 * 契约:桌面\pearnly ai\施工\W3-交互契约.md。单张聚焦(同 v4 rv1/rv2 切换,不做滚动列表)——
 * A 采纳票面 / E 改数(仅 VAT)/ X 剔除,乐观标终态 + 失败回滚(§2);裁决完只引导重新跑,
 * 不在前端重估 R1(§4,别重造算钱逻辑);四态 + 空队列好事态(§6)。
 *
 * 依赖 window.AI.state/format/api/viewer/reviewQueue/reviewRender 与全局 at(),故必须排在
 * 它们之后加载(见 scripts/build-home-js.mjs 的 bundle 顺序)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };
    var POLL_INTERVAL_MS = 2000;
    var POLL_MAX_TRIES = 30;

    var S = null;
    var wired = false; // 照 ai-client.js chromeWired 先例:监听器只挂一次,不随每次 mount 重挂。

    // 本次刚提交的裁决没有服务端 actor 回显(响应体只有 event_id),用当前登录态的展示名
    // 占位(AI.format.actorLabel 回落链:邮箱前缀 → sub 短八位)——不再拼 "user:<uuid>"
    // 糊脸(清单 #2 同源修法,后端落库的 actor 串不变)。
    function currentActorLabel() {
        return AI.format.actorLabel(null, localStorage.getItem('mrpilot_token'));
    }

    function freshState(api, order, clientId) {
        return {
            api: api,
            orderId: order.id,
            clientId: clientId,
            queue: [],
            idx: 0,
            local: {}, // item_id -> {state: 'pending'|'accepted'|'recalc'|'excluded'|'assigned'|'failed', decision}
            poolHandle: AI.reviewPool.create(), // D2-S9 · 推 LINE 待问状态机(ai-review-pool.js)
            editing: false,
            editErr: false,
            editValue: null,
            sessionDecided: 0,
            sessionCorrected: 0,
            mode: 'card', // 'card' | 'done'
            rerunState: 'idle',
            blockedInfo: null,
        };
    }

    function body() {
        return $('cv-review');
    }

    // ============ 渲染 ============

    function renderCurrent() {
        var container = body();
        if (S.mode !== 'card' || !S.queue.length) return renderDone();
        var entry = S.queue[S.idx];
        container.innerHTML = AI.reviewRender.cardHtml({
            entry: entry,
            idx: S.idx,
            total: S.queue.length,
            local: S.local[entry.item_id],
            editing: S.editing,
            editErr: S.editErr,
            editValue: S.editValue,
            pool: S.poolHandle.forItem(entry.item_id),
        });
        if (S.editing) {
            var input = $('rvVatInput');
            if (input) {
                input.focus();
                input.select();
            }
        }
        attachImage(entry);
        preloadNext();
    }

    function renderDone() {
        S.mode = 'done';
        var container = body();
        if (!S.queue.length && !S.sessionDecided) {
            container.innerHTML = AI.reviewRender.emptyOkHtml();
            return;
        }
        container.innerHTML = AI.reviewRender.clearedHtml(
            S.sessionDecided,
            S.sessionCorrected,
            S.rerunState,
            S.blockedInfo
        );
    }

    // ============ 原图(生产同款查看器,AI.viewer 接手拖拽/缩放/旋转/全屏)============
    // 鉴权头 <img> 拿不到,loader 走 fetch+blob(AI.viewer 内部转 objectURL 并 LRU 缓存,
    // mount 与预加载共用同一份,不再各自维护一份 blob 缓存)。

    function itemImageLoader(itemId) {
        return function () {
            return S.api.getItemImageBlob(S.orderId, itemId).then(function (blob) {
                return URL.createObjectURL(blob);
            });
        };
    }

    // 换卡先清旧查看器实例(mountKey 固定 'review' · 单张聚焦不会有并存的第二个实例)。
    function attachImage(entry) {
        AI.viewer.remountViewer('review', $('rvImgWrap'), {
            key: entry.item_id,
            loader: itemImageLoader(entry.item_id),
        });
    }

    function preloadNext() {
        var next = S.queue[S.idx + 1];
        if (next) AI.viewer.preload(next.item_id, itemImageLoader(next.item_id));
    }

    // ============ 乐观裁决 + 回滚(契约 §2) ============

    function setLocal(itemId, patch) {
        S.local[itemId] = Object.assign({}, S.local[itemId], patch);
    }

    // ============ D2-S9:第四动作「推 LINE 待问」(A/E/X 之外,不串裁决键盘流) ============
    // 状态机本体在 ai-review-pool.js(单文件<500 铁律拆出),这里只接线当前卡片 + 会话卫哨。

    function togglePoolPicker() {
        var entry = S.queue[S.idx];
        if (!entry || S.editing) return;
        if (S.poolHandle.toggle(entry.item_id)) renderCurrent();
    }

    function stageToPool(questionType) {
        var entry = S.queue[S.idx];
        if (!entry) return;
        var session = S; // 快照——回调落地时若已切走(S 已指向新会话)一律不认。
        S.poolHandle.stage(S.api, S.orderId, entry, questionType, function () {
            if (S !== session) return;
            if (S.mode === 'card') renderCurrent();
        });
    }

    function decide(action) {
        var entry = S.queue[S.idx];
        if (!entry) return;
        var vatRaw = action === 'recalc' ? $('rvVatInput') && $('rvVatInput').value : null;
        var payload = AI.reviewQueue.buildDecisionPayload(entry.item_id, action, vatRaw);
        if (!payload) {
            S.editErr = true;
            renderCurrent();
            return;
        }
        var session = S; // 快照当前会话——回调落地时若已切走(S 已指向新会话)一律不认。
        var submittedIdx = S.idx;
        var submittedItemId = entry.item_id;
        setLocal(submittedItemId, { state: 'pending' });
        S.editing = false;
        S.editErr = false;
        S.editValue = null;
        S.sessionDecided += 1;
        if (action === 'recalc') S.sessionCorrected += 1;
        advanceFocus();

        S.api
            .decide(S.orderId, payload)
            .then(function () {
                if (S !== session) return; // 已切走
                setLocal(submittedItemId, {
                    state: _stateForAction(action),
                    decision: {
                        decision: payload.decision,
                        kind: payload.kind, // 方向裁决(assign_kind)携带,金额裁决为 undefined
                        values: payload.values,
                        actor: currentActorLabel(),
                        at: new Date().toISOString(),
                    },
                });
                if (S.mode === 'card') renderCurrent();
                if (action === 'exclude') {
                    AI.reviewRender.showToast(
                        AI.reviewQueue.fileName(entry.file_ref) + ' · ' + at('rv_chip_excluded'),
                        function () {
                            undoExclude(submittedIdx);
                        }
                    );
                }
            })
            .catch(function (err) {
                if (S !== session) return; // 已切走
                // 错误码 → 具体文案(命中才用,不命中退化成通用失败提示)——toast 与卡上
                // chip 同源(都读 local.errKey),不各拼一套文案。
                var errKey = AI.api.mapApiErrorKey(err && err.code);
                var hit = errKey !== 'err_generic' && at(errKey) !== errKey;
                setLocal(submittedItemId, { state: 'failed', errKey: hit ? errKey : null });
                S.idx = submittedIdx;
                S.mode = 'card';
                renderCurrent();
                AI.reviewRender.showToast(
                    hit ? at(errKey) : at('rv_decision_failed', { n: submittedIdx + 1 }),
                    null
                );
            });
    }

    // 乐观终态标签(非 pending/failed 即视为已裁决,statusChip 据 decision 显 chip)。
    // 方向裁决三键归一到 'assigned',金额裁决沿用各自终态。
    function _stateForAction(action) {
        if (action === 'accept') return 'accepted';
        if (action === 'exclude') return 'excluded';
        if (action === 'recalc') return 'recalc';
        return 'assigned';
    }

    function advanceFocus() {
        if (S.idx + 1 < S.queue.length) {
            S.idx += 1;
            renderCurrent();
        } else {
            renderDone();
        }
    }

    function undoExclude(idx) {
        var entry = S.queue[idx];
        if (!entry) return;
        // 契约 §2:撤销 = 清回未裁决态由人重判,不代人猜下一步该按哪个键。
        delete S.local[entry.item_id];
        S.idx = idx;
        S.mode = 'card';
        S.sessionDecided = Math.max(0, S.sessionDecided - 1);
        AI.reviewRender.hideToast();
        renderCurrent();
    }

    // ============ 改数态(E) ============

    function startEdit() {
        S.editing = true;
        S.editErr = false;
        var entry = S.queue[S.idx];
        var decided = (S.local[entry.item_id] && S.local[entry.item_id].decision) || entry.decision;
        var prior =
            decided && decided.decision === 'recalc' && decided.values && decided.values.vat;
        S.editValue = prior || (entry.ocr_read || {}).vat || '';
        renderCurrent();
    }

    function cancelEdit() {
        S.editing = false;
        S.editErr = false;
        S.editValue = null;
        renderCurrent();
    }

    // ============ 导航(↑↓←→,只移焦点不裁决) ============

    function moveNext() {
        if (S.idx + 1 < S.queue.length) {
            S.idx += 1;
            renderCurrent();
        }
    }
    function movePrev() {
        if (S.idx > 0) {
            S.idx -= 1;
            renderCurrent();
        }
    }

    // ============ 重新跑 + 轮询(契约 §4) ============

    function startRerun() {
        var session = S; // 快照——重跑是长链路(网络 + 轮询),切走后续段一律不认。
        S.rerunState = 'waiting';
        S.blockedInfo = null;
        renderDone();
        S.api
            .runOrder(S.orderId)
            .then(function () {
                if (S !== session) return; // 已切走
                pollAfterRun(session, 0);
            })
            .catch(function () {
                if (S !== session) return; // 已切走
                S.rerunState = 'idle';
                S.blockedInfo = { reasons: [at('err_generic')], hasQueue: false };
                renderDone();
            });
    }

    function pollAfterRun(session, count) {
        if (count >= POLL_MAX_TRIES) {
            S.rerunState = 'idle';
            S.blockedInfo = { reasons: [], hasQueue: S.queue.length > 0 };
            renderDone();
            return;
        }
        setTimeout(function () {
            if (S !== session) return; // 已切走·每个轮询 tick 开头判活
            S.api
                .getOrder(S.orderId)
                .then(function (detail) {
                    if (S !== session) return; // 已切走
                    var freshQueue = AI.reviewQueue.filterPurchaseQueue(detail.flagged || []);
                    var hasNumbers = Object.keys(detail.numbers || {}).length > 0;
                    if (detail.status !== 'stuck' || !freshQueue.length || hasNumbers) {
                        window.location.hash = AI.router.buildClientHash(S.clientId, 'pkg');
                        return;
                    }
                    var reasons = [].concat(detail.blocked_reasons || [], detail.needs || []);
                    if (reasons.length) {
                        S.queue = freshQueue;
                        S.rerunState = 'idle';
                        S.blockedInfo = { reasons: reasons, hasQueue: freshQueue.length > 0 };
                        renderDone();
                        return;
                    }
                    pollAfterRun(session, count + 1);
                })
                .catch(function () {
                    if (S !== session) return; // 已切走
                    pollAfterRun(session, count + 1);
                });
        }, POLL_INTERVAL_MS);
    }

    function backToQueue() {
        S.idx = 0;
        S.mode = 'card';
        S.blockedInfo = null;
        renderCurrent();
    }

    // ============ 键盘 + 点击委托 ============

    function onKeydown(e) {
        // 键盘监听挂在 document 上且只挂一次(wireOnce),换 tab/换视图后仍在——
        // 不判活会导致切到「工单」等其他 tab 时按 A/E/X 仍偷偷裁决审核队列(契约外行为)。
        var view = $('cv-review');
        if (!view || !view.classList.contains('on')) return;
        if (S.mode !== 'card') return;
        if (S.editing) {
            if (e.key === 'Enter') {
                e.preventDefault();
                decide('recalc');
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEdit();
            }
            return;
        }
        var tag = e.target && e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        // 第四动作(D2-S9):Q 切换「推 LINE 待问」选择面板,方向票/金额票通用,
        // 不占用 A/E/X/P/S 任何既有键位,独立分支不落进下面两套裁决键盘流。
        if (e.key === 'q' || e.key === 'Q') {
            e.preventDefault();
            togglePoolPicker();
            return;
        }
        var entry = S.queue[S.idx];
        // 方向不明票:键位切换成 P 进项 / S 销项 / X 非税(assign_kind),不走金额票的 A/E/X。
        if (entry && AI.reviewQueue.isDirectionTicket(entry)) {
            if (e.key === 'p' || e.key === 'P') {
                e.preventDefault();
                decide('assign_purchase');
            } else if (e.key === 's' || e.key === 'S') {
                e.preventDefault();
                decide('assign_sales');
            } else if (e.key === 'x' || e.key === 'X') {
                e.preventDefault();
                decide('assign_nontax');
            } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                e.preventDefault();
                moveNext();
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                e.preventDefault();
                movePrev();
            }
            return;
        }
        if (e.key === 'a' || e.key === 'A') {
            e.preventDefault();
            decide('accept');
        } else if (e.key === 'e' || e.key === 'E') {
            e.preventDefault();
            startEdit();
        } else if (e.key === 'x' || e.key === 'X') {
            e.preventDefault();
            decide('exclude');
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            moveNext();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            movePrev();
        }
    }

    function onContainerClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el) return;
        var action = el.getAttribute('data-action');
        if (action === 'rv-accept') decide('accept');
        else if (action === 'rv-edit') startEdit();
        else if (action === 'rv-exclude') decide('exclude');
        else if (action === 'rv-dir-purchase') decide('assign_purchase');
        else if (action === 'rv-dir-sales') decide('assign_sales');
        else if (action === 'rv-dir-nontax') decide('assign_nontax');
        else if (action === 'rv-pool-toggle') togglePoolPicker();
        else if (action === 'rv-pool-pick') stageToPool(el.getAttribute('data-qtype'));
        else if (action === 'rv-rerun') startRerun();
        else if (action === 'rv-back-to-queue') backToQueue();
        else if (action === 'rv-goto-pkg') {
            window.location.hash = AI.router.buildClientHash(S.clientId, 'pkg');
        }
    }

    function wireOnce() {
        if (wired) return;
        wired = true;
        body().addEventListener('click', onContainerClick);
        document.addEventListener('keydown', onKeydown);
    }

    // ============ 挂载 ============

    function mount(api, order, clientId) {
        S = freshState(api, order, clientId);
        body().innerHTML = AI.state.loadingHtml();
        wireOnce();
        api.getOrder(order.id)
            .then(function (detail) {
                if (!S || S.orderId !== order.id) return; // 已切走
                S.queue = AI.reviewQueue.filterPurchaseQueue(detail.flagged || []);
                S.idx = 0;
                S.mode = 'card';
                renderCurrent();
            })
            .catch(function () {
                body().innerHTML = AI.state.errorHtml({
                    title: at('error_t'),
                    sub: at('error_s'),
                    retryLabel: at('retry'),
                });
                var btn = body().querySelector('[data-action="retry"]');
                if (btn)
                    btn.onclick = function () {
                        mount(api, order, clientId);
                    };
            });
    }

    window.AI = window.AI || {};
    window.AI.review = { mount: mount };
})();
