(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var S = null;
    var wired = false; // 照 ai-client.js chromeWired 先例:监听器只挂一次,不随每次 mount 重挂。
    var runPoll = null; // 当前重跑轮询的 AI.poll 句柄(mount()/换会话时先停旧的再起新的)
    var lastItemByOrder = {};

    function currentActorLabel() {
        return AI.format.actorLabel(null, localStorage.getItem('mrpilot_token'));
    }

    function freshState(api, order, clientId) {
        return {
            api: api,
            orderId: order.id,
            clientId: clientId,
            queue: [], // 未判票(J-C · 只有这些走单张聚焦流,已判票分流进 decidedEntries)
            decidedEntries: [], // 已判票(mount 时 entry.decision 已有值),折叠分组只读展示
            idx: 0,
            local: {}, // item_id -> {state: 'pending'|'accepted'|'recalc'|'excluded'|'assigned'|'failed', decision}
            poolHandle: AI.reviewPool.create(), // D2-S9 · 推 LINE 待问状态机(ai-review-pool.js)
            bulkHandle: AI.reviewBulk.create(), // J-C · 全部按建议处理批量确认状态机(ai-review-bulk.js)
            editing: false,
            editErr: false,
            editValue: null,
            editSuggestion: null, // J-A 建议值消费(J-C):当前编辑票命中的 amount_read_suggested 投影(无则 null)
            editSuggestValues: null, // 五字段编辑值 {invoice_number, invoice_date, net, vat, grand}
            sessionDecided: 0,
            sessionCorrected: 0,
            mode: 'card', // 'card' | 'done'
            rerunState: 'idle',
            blockedInfo: null,
            rerunProgress: null, // classify 步逐件进度快照 {step,processed,total} · R2F-R3 #5
            autoRunGraceUntil: 0, // 最后一笔裁决响应早于 BackgroundTasks 起跑时,容忍短暂旧 stuck 投影
            // R4 税号错录守护卡:alerts=order_detail.alerts;wsClientId=账套主体 id(改税号目标);
            // canManage=settings.workspace.manage 探针结果(按钮显隐);realignBusy/Err=一键改状态。
            alerts: [],
            wsClientId: order.workspace_client_id || null,
            canManage: false,
            realignBusy: false,
            realignErr: false,
        };
    }

    function body() {
        return $('cv-review');
    }

    // ============ 渲染 ============

    // 队列顶部 chrome(J-C):批量确认横幅(算未判队列里能一键处理的同类组)+ R4 税号错录
    // 守护卡,两者都在顶部注入、不打断裁决键盘流。合成一段字符串一次插入而非各自
    // insertAdjacentHTML('afterbegin')——后者多次调用会反序(每次都插到容器最前面)。
    function injectChrome(container) {
        var groups = S.bulkHandle.bulkableGroups(S.queue, S.local);
        var bulkState = S.bulkHandle.state();
        var html =
            AI.reviewFoldRender.bulkBannerHtml(groups, bulkState.busyFlag) +
            AI.reviewFoldRender.bulkConfirmHtml(bulkState.confirmGroup) +
            AI.reviewRender.taxidAlertHtml(S.alerts, {
                canManage: S.canManage,
                busy: S.realignBusy,
                errKey: S.realignErr,
            });
        if (html) container.insertAdjacentHTML('afterbegin', html);
    }

    // 已判票折叠分组(J-C):挪出主聚焦流的已判票在卡片下方常驻可见,展开可逐张改判
    // (ai-review-fold-render.js::decidedGroupHtml,点击走 revisitDecided)。
    function injectDecidedGroup(container) {
        var html = AI.reviewFoldRender.decidedGroupHtml(S.decidedEntries);
        if (html) container.insertAdjacentHTML('beforeend', html);
    }

    function renderCurrent() {
        var container = body();
        if (S.mode !== 'card' || !S.queue.length) return renderDone();
        var entry = S.queue[S.idx];
        container.innerHTML = AI.reviewRender.cardHtml({
            entry: entry,
            idx: S.idx,
            total: S.queue.length,
            undecidedRemaining: AI.reviewQueue.undecidedCount(S.queue, S.local),
            // 「共 n」不设独立状态:revisit 只在 queue/decidedEntries 间搬条目,两者之和恒为总数
            totalCount: S.queue.length + S.decidedEntries.length,
            local: S.local[entry.item_id],
            editing: S.editing,
            editErr: S.editErr,
            editValue: S.editValue,
            editSuggestion: S.editSuggestion,
            editSuggestValues: S.editSuggestValues,
            pool: S.poolHandle.forItem(entry.item_id),
        });
        injectChrome(container);
        if (S.editing) {
            var input = $('rvVatInput');
            if (input) {
                input.focus();
                input.select();
            }
        }
        injectDecidedGroup(container);
        attachImage(entry);
        preloadNext();
    }

    function renderDone() {
        S.mode = 'done';
        var container = body();
        if (!S.queue.length && !S.decidedEntries.length && !S.blockedInfo) {
            container.innerHTML = AI.reviewRender.emptyOkHtml();
            injectChrome(container);
            return;
        }
        var stats = decisionStats();
        container.innerHTML = AI.reviewRender.clearedHtml(
            stats.decided,
            stats.corrected,
            S.rerunState,
            S.blockedInfo,
            S.rerunProgress
        );
        injectChrome(container);
        injectDecidedGroup(container);
    }

    function decisionStats() {
        var seen = {};
        var stats = { decided: 0, corrected: 0 };
        S.queue.concat(S.decidedEntries).forEach(function (entry) {
            if (!entry || seen[entry.item_id]) return;
            seen[entry.item_id] = true;
            var local = S.local[entry.item_id];
            var decision = (local && local.decision) || entry.decision;
            if (!decision || !decision.decision) return;
            stats.decided += 1;
            if (decision.decision === 'recalc') stats.corrected += 1;
        });
        return stats;
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
    // stateKey=工单 id:同单跨张保持缩放/旋转(S3 §8c,状态存取在 AI.viewer)。
    function attachImage(entry) {
        AI.viewer.remountViewer('review', $('rvImgWrap'), {
            key: entry.item_id,
            loader: itemImageLoader(entry.item_id),
            stateKey: S.orderId,
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
        // 改数态统一提交票号、日期与三项金额；没有确定性建议时也必须让人能修 OCR 原值。
        var vatRaw = action === 'recalc' ? $('rvVatInput') && $('rvVatInput').value : null;
        var fullValues =
            action === 'recalc' && S.editSuggestValues
                ? {
                      net: $('rvNetInput') && $('rvNetInput').value,
                      vat: $('rvVatInput') && $('rvVatInput').value,
                      grand: $('rvGrandInput') && $('rvGrandInput').value,
                      invoice_number: $('rvInvoiceNoInput') && $('rvInvoiceNoInput').value,
                      invoice_date: $('rvInvoiceDateInput') && $('rvInvoiceDateInput').value,
                  }
                : null;
        var payload = AI.reviewQueue.buildDecisionPayload(
            entry.item_id,
            action,
            vatRaw,
            fullValues
        );
        if (!payload) {
            S.editErr = true;
            renderCurrent();
            return;
        }
        var session = S; // 快照当前会话——回调落地时若已切走(S 已指向新会话)一律不认。
        var submittedIdx = S.idx;
        var submittedItemId = entry.item_id;
        var finishing = AI.reviewQueue.undecidedCount(S.queue, S.local) === 1;
        lastItemByOrder[S.orderId] = submittedItemId;
        setLocal(submittedItemId, { state: 'pending' });
        S.editing = false;
        S.editErr = false;
        S.editValue = null;
        S.editSuggestion = null;
        S.editSuggestValues = null;
        S.sessionDecided += 1;
        if (action === 'recalc') S.sessionCorrected += 1;
        if (finishing) S.rerunState = 'waiting';
        if (finishing) renderDone();
        else advanceFocus();

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
                if (finishing) beginAutoRunPolling(session);
                else if (S.mode === 'card') renderCurrent();
                if (action === 'exclude') {
                    AI.reviewRender.showToast(
                        AI.reviewQueue.fileName(entry.file_ref) + ' · ' + at('rv_chip_excluded'),
                        function () {
                            undoExclude(submittedIdx);
                        }
                    );
                } else {
                    // 契约 A 动作回执(2026-07-17 Canon):采纳/改数/定向也要一句落库确认,
                    // 不能只有剔除有回执。
                    AI.reviewRender.showToast(at('review_saved_toast'), null);
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
                S.rerunState = 'idle';
                S.autoRunGraceUntil = 0;
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
            lastItemByOrder[S.orderId] = S.queue[S.idx].item_id;
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
        // AI.reviewQueue.editStartValues 统一生成票号、日期和三项金额的编辑起始值。
        var vals = AI.reviewQueue.editStartValues(S.alerts, entry, decided);
        S.editSuggestion = vals.suggestion;
        S.editValue = vals.editValue;
        S.editSuggestValues = vals.suggestValues;
        renderCurrent();
    }

    function cancelEdit() {
        S.editing = false;
        S.editErr = false;
        S.editValue = null;
        S.editSuggestion = null;
        S.editSuggestValues = null;
        renderCurrent();
    }

    // ============ 已判折叠分组:改判(J-C) ============

    // 从折叠分组把该票挪回未判队列最前并立刻聚焦——复用同一套 A/E/X 裁决(latest-wins),
    // 不重造第二套改判路径;entry.decision 仍在(旧裁决),卡片正常显示旧结果 + 可再裁决。
    function revisitDecided(itemId) {
        var pos = -1;
        for (var i = 0; i < S.decidedEntries.length; i++) {
            if (S.decidedEntries[i].item_id === itemId) {
                pos = i;
                break;
            }
        }
        if (pos < 0) return;
        var entry = S.decidedEntries.splice(pos, 1)[0];
        S.queue.unshift(entry);
        S.idx = 0;
        S.mode = 'card';
        renderCurrent();
    }

    // ============ 批量确认「全部按建议处理」(J-C) ============

    function runBulk(flagReason) {
        var group = S.bulkHandle.bulkableGroups(S.queue, S.local).filter(function (g) {
            return g.flagReason === flagReason;
        })[0];
        if (!group) return;
        S.bulkHandle.requestConfirm(group);
        renderCurrent();
    }

    function archiveBulkDecisions() {
        var split = AI.reviewQueue.splitByDecision(S.queue, S.local);
        var moved = split.decided.map(function (entry) {
            var local = S.local[entry.item_id];
            return Object.assign({}, entry, {
                decision: (local && local.decision) || entry.decision,
            });
        });
        S.queue = split.undecided;
        S.decidedEntries = S.decidedEntries.concat(moved);
        S.idx = Math.min(S.idx, Math.max(0, S.queue.length - 1));
    }

    function confirmBulk() {
        var session = S; // 快照——网络落地时若已切走(S 已指向新会话)一律不认。
        S.bulkHandle.runConfirmed(S.api, S.orderId, function (res) {
            if (S !== session) return;
            if (res) {
                var template = S.bulkHandle.state().lastTemplate;
                var action = AI.reviewQueue.actionOfDecision(template);
                (res.results || []).forEach(function (row) {
                    if (!row.ok) return;
                    setLocal(row.item_id, {
                        state: _stateForAction(action),
                        decision: Object.assign(
                            { actor: currentActorLabel(), at: new Date().toISOString() },
                            template
                        ),
                    });
                });
                S.sessionDecided += res.ok_count || 0;
                archiveBulkDecisions();
            }
            if (S.mode === 'card' && S.queue.length) renderCurrent();
            else beginAutoRunPolling(session);
        });
    }

    function cancelBulk() {
        S.bulkHandle.cancelConfirm();
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

    function beginAutoRunPolling(session) {
        S.rerunState = 'waiting';
        S.blockedInfo = null;
        S.rerunProgress = null;
        S.autoRunGraceUntil = Date.now() + 5000;
        renderDone();
        runPollFor(session);
    }

    function startRerun() {
        var session = S; // 快照——重跑是长链路(网络 + 轮询),切走后续段一律不认。
        S.rerunState = 'waiting';
        S.blockedInfo = null;
        S.rerunProgress = null;
        S.autoRunGraceUntil = Date.now() + 5000;
        renderDone();
        S.api
            .runOrder(S.orderId)
            .then(function () {
                if (S !== session) return; // 已切走
                runPollFor(session);
            })
            .catch(function (err) {
                if (S !== session) return; // 已切走
                var errKey = AI.api.mapApiErrorKey(err && err.code);
                // 409(工单已在跑):不是失败,是我们来晚了——继续轮询,只是带上
                // "正在跑"专属文案(同 ai-intake.js::startRerun 先例)。
                if (errKey === 'err_workorder_run_in_progress') {
                    S.blockedInfo = { reasons: [at(errKey)], hasQueue: false };
                    renderDone();
                    runPollFor(session);
                    return;
                }
                S.rerunState = 'idle';
                S.autoRunGraceUntil = 0;
                S.blockedInfo = { reasons: [at(errKey)], hasQueue: false };
                renderDone();
            });
    }

    // fetch/onTick/isTerminal 三段式收在一处(AI.poll 收编·N-6 债:此前与 ai-intake.js
    // 各写一份手写 setTimeout 链,逐字节重复)。换会话/重复触发时先停旧轮询再起新的。
    function runPollFor(session) {
        if (runPoll) runPoll.stop();
        runPoll = AI.poll.create({
            fetch: function () {
                return session.api.getOrder(session.orderId);
            },
            onTick: function (detail) {
                if (S !== session) return;
                // classify(逐张识别)与 reconcile(逐张读对账单)两步的真进度,谁在跑显谁,
                // 不空转省略号(J-1/J-9)。
                var progress = detail.progress || detail.bank_progress;
                if (progress) {
                    S.rerunProgress = progress;
                    renderDone();
                }
            },
            isTerminal: function (detail) {
                if (S !== session) return true; // 已切走会话,静默收口,不做任何副作用
                return routeAfter(detail, session);
            },
            onTimeout: function () {
                if (S !== session) return;
                // 轮询次数用尽不等于"仍卡住需要你判断"(那是 rv_still_blocked 的语义)——
                // 大概率只是引擎还在后台跑,比预算的时间窗慢。诚实区分开,给手动刷新钮
                // (timedOut,R2F-R3 #5),不跟真实的"缺料/需裁决"混成一句话。
                S.rerunState = 'idle';
                S.blockedInfo = { reasons: [], hasQueue: S.queue.length > 0, timedOut: true };
                renderDone();
            },
        });
        runPoll.start();
    }

    // 一次轮询拿到的 detail → 是否终态(true=停轮询,调用方已在这里做完全部导航/呈现副作用)。
    function routeAfter(detail, session) {
        var status = detail.status || '';
        if (status === 'collecting' || status === 'running') return false;
        if (status === 'review' || status === 'archive') {
            window.location.hash = AI.router.buildClientHash(session.clientId, 'pkg');
            return true;
        }
        if (status !== 'stuck') return false;

        var fresh = AI.reviewQueue.filterPurchaseQueue(detail.flagged || []);
        var split = AI.reviewQueue.splitByDecision(fresh);
        if (!split.undecided.length && Date.now() < S.autoRunGraceUntil) return false;

        var reasons = [].concat(detail.blocked_reasons || [], detail.needs || []);
        if (reasons.length || split.undecided.length) {
            S.queue = split.undecided;
            S.decidedEntries = split.decided;
            S.rerunState = 'idle';
            S.autoRunGraceUntil = 0;
            S.blockedInfo = {
                reasons: reasons,
                hasQueue: split.undecided.length > 0,
                system:
                    (detail.blocked_reasons || []).length > 0 &&
                    !(detail.needs || []).length &&
                    !split.undecided.length,
            };
            renderDone();
            return true;
        }
        return false;
    }

    // 轮询超时后的手动"刷新查看"(R2F-R3 #5,同 ai-intake.js::refreshAfterTimeout 先例):
    // 重新起一轮完整轮询,不是点一下只探一次就又撒手。
    function refreshStatus() {
        if (S.rerunState === 'waiting') return;
        S.rerunState = 'waiting';
        renderDone();
        runPollFor(S);
    }

    function backToQueue() {
        S.idx = 0;
        S.mode = 'card';
        S.blockedInfo = null;
        renderCurrent();
    }

    // ============ R4 税号错录守护卡:一键改正 + 重锚 ============

    // settings.workspace.manage 探针(复用 can-create 端点,同 ai-client-new 先例):成功=有权限,
    // 显真按钮;失败(403 等)保持无按钮的诚实降级文案。探到再重渲染当前视图,不阻塞首屏。
    function probeCanManage(session) {
        S.api
            .canCreateWorkspaceClient()
            .then(function () {
                if (S !== session) return;
                S.canManage = true;
                if (S.mode === 'card') renderCurrent();
                else renderDone();
            })
            .catch(function () {}); // 无权限=保持降级文案,不喧哗
    }

    // 一键改正:先改账套主体税号(既有 PATCH),成功后触发工单重锚(后端自驱重跑,有跨单去重
    // 零 OCR 成本),进入轮询直到重判完成 → 跳交付包 / 回队列。任一步失败保住已裁决,只提示重试。
    function doRealign() {
        if (S.realignBusy || !S.alerts.length || !S.canManage) return;
        var a = S.alerts[0];
        if (a.type !== 'taxid_typo_suspected' || !S.wsClientId) return;
        var session = S;
        S.realignBusy = true;
        S.realignErr = false;
        if (S.mode === 'card') renderCurrent();
        else renderDone();
        S.api
            .updateWorkspaceClient(S.wsClientId, { tax_id: a.suspected })
            .then(function () {
                return S.api.realignTaxid(S.orderId, a.registered, a.suspected);
            })
            .then(function () {
                if (S !== session) return;
                S.alerts = []; // 已改并重锚,撤卡
                S.realignBusy = false;
                S.rerunState = 'waiting'; // 重锚触发引擎自驱重跑,进轮询(有去重通常很快)
                S.blockedInfo = null;
                renderDone();
                runPollFor(session);
            })
            .catch(function () {
                if (S !== session) return;
                S.realignBusy = false;
                S.realignErr = true;
                if (S.mode === 'card') renderCurrent();
                else renderDone();
            });
    }

    // ============ 键盘 + 点击委托 ============

    function onKeydown(e) {
        // 键盘监听挂在 document 上且只挂一次(wireOnce),换 tab/换视图后仍在——
        // 不判活会导致切到「工单」等其他 tab 时按 A/E/X 仍偷偷裁决审核队列(契约外行为)。
        var view = $('cv-review');
        if (!view || !view.classList.contains('on')) return;
        if (S.bulkHandle.state().confirmGroup) {
            if (e.key === 'Escape') {
                e.preventDefault();
                cancelBulk();
            }
            return;
        }
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
        else if (action === 'rv-refresh-status') refreshStatus();
        else if (action === 'rv-taxid-realign') doRealign();
        else if (action === 'rv-revisit') revisitDecided(el.getAttribute('data-item'));
        else if (action === 'rv-bulk-run') runBulk(el.getAttribute('data-flag'));
        else if (action === 'rv-bulk-confirm') confirmBulk();
        else if (action === 'rv-bulk-cancel') cancelBulk();
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
        // 换单/换客户挂载新会话:旧会话的轮询没有存在意义(isTerminal/onTick 虽已靠 S!==
        // session 卫哨自认失效,但让它继续空转到超时才停也没必要,当场收掉更干净)。
        if (runPoll) {
            runPoll.stop();
            runPoll = null;
        }
        wireOnce();
        api.getOrder(order.id)
            .then(function (detail) {
                if (!S || S.orderId !== order.id) return; // 已切走
                // 未判/已判两分(J-C):主聚焦流只走未判票,已判票折叠(见 injectDecidedGroup)。
                var split = AI.reviewQueue.splitByDecision(
                    AI.reviewQueue.filterPurchaseQueue(detail.flagged || [])
                );
                S.queue = split.undecided;
                S.decidedEntries = split.decided;
                S.idx = 0;
                var blockers = detail.blocked_reasons || [];
                if (detail.status === 'stuck' && !S.queue.length && blockers.length) {
                    S.blockedInfo = {
                        reasons: blockers,
                        hasQueue: false,
                        system: true,
                    };
                }
                // 契约 C:回到上次操作那张(仍未判才聚焦,已判/不在则维持第一张未判)。
                var lastId = lastItemByOrder[order.id];
                for (var i = 0; lastId && i < S.queue.length; i++) {
                    if (S.queue[i].item_id === lastId) {
                        S.idx = i;
                        break;
                    }
                }
                S.mode = 'card';
                S.alerts = detail.alerts || [];
                if (detail.workspace_client_id) S.wsClientId = detail.workspace_client_id;
                var polling = detail.status === 'collecting' || detail.status === 'running';
                if (polling && !S.queue.length) S.rerunState = 'waiting';
                renderCurrent();
                if (polling && !S.queue.length) runPollFor(S);
                // 有守护卡才探 settings.workspace.manage(按钮显隐 · 探到再重渲染,不阻塞首屏)。
                if (S.alerts.length) probeCanManage(S);
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
