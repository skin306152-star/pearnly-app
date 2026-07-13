/*
 * Pearnly AI · ai-review-inbox-flagged.js · 异常票据分区状态机(MC1-b2)
 *
 * 拆出独立于 ai-review-inbox.js 主编排(单文件<500 铁律,同 ai-review-inbox-signoff.js
 * 拆自同一预算线的先例):review-queue 只给按 flag_reason 分组的计数,本模块对每个
 * flagged_total>0 的工单并行拉 getOrder() 详情,跨工单按 flag_reason 重新分组,持有
 * 组内批量(A/X)与逐张(A/E/X/P/S/N)两套裁决状态——裁决 payload 构造复用
 * ai-review-queue.js(与单工单人审队列 W3 同一份,不重造),不重算/不重估任何钱。
 *
 * hooks(调用方 ai-review-inbox.js 传入):
 *   onChange()            状态变化后触发重渲染(loading/分组/裁决态任一变化都调)。
 *   afterMutate()         裁决/批量落库成功后触发(调用方据此刷新工单卡计数)。
 *   showToast(msg, undo)  提示(undo 传函数则显 3 秒撤销 toast,不传则普通失败提示)。
 */
(function () {
    'use strict';

    function create(api, hooks) {
        var st = {
            detailLoading: false,
            orderDetail: {}, // work_order_id -> {detail, clientName, period} | null
            itemIndex: {}, // item_id -> merged flagged item
            flaggedGroups: [],
            groupUi: {}, // flag_reason -> {busy, itemUi:{}, local:{}}
        };

        function groupUiFor(flagReason) {
            if (!st.groupUi[flagReason])
                st.groupUi[flagReason] = { busy: false, itemUi: {}, local: {} };
            return st.groupUi[flagReason];
        }
        function itemUiFor(flagReason, itemId) {
            var g = groupUiFor(flagReason);
            if (!g.itemUi[itemId]) g.itemUi[itemId] = {};
            return g.itemUi[itemId];
        }

        function loadFor(targets) {
            if (!targets.length) {
                st.flaggedGroups = [];
                st.itemIndex = {};
                hooks.onChange();
                return Promise.resolve();
            }
            st.detailLoading = true;
            hooks.onChange();
            return Promise.all(
                targets.map(function (t) {
                    return api
                        .getOrder(t.id)
                        .then(function (detail) {
                            st.orderDetail[t.id] = {
                                detail: detail,
                                clientName: t.client.client_name,
                                period: t.period,
                            };
                        })
                        .catch(function () {
                            st.orderDetail[t.id] = null;
                        });
                })
            ).then(function () {
                st.detailLoading = false;
                rebuildGroups();
                hooks.onChange();
            });
        }

        function rebuildGroups() {
            var byReason = {};
            var index = {};
            Object.keys(st.orderDetail).forEach(function (orderId) {
                var rec = st.orderDetail[orderId];
                if (!rec) return;
                (rec.detail.flagged || []).forEach(function (item) {
                    var g = groupUiFor(item.flag_reason);
                    var local = g.local[item.item_id];
                    if (local && local.state === 'done') return; // 已裁决(乐观态)不再进队列
                    var merged = Object.assign({}, item, {
                        work_order_id: orderId,
                        client_name: rec.clientName,
                        period: rec.period,
                    });
                    index[item.item_id] = merged;
                    var bucket =
                        byReason[item.flag_reason] ||
                        (byReason[item.flag_reason] = {
                            flagReason: item.flag_reason,
                            severity: AI.reviewQueue.flagSeverity(item.flag_reason),
                            items: [],
                        });
                    bucket.items.push(merged);
                });
            });
            st.itemIndex = index;
            st.flaggedGroups = Object.keys(byReason)
                .map(function (k) {
                    return byReason[k];
                })
                .sort(function (a, b) {
                    return b.items.length - a.items.length; // 大组优先(先啃能一键批量的高值组)
                });
        }

        function byOrder(items) {
            var out = {};
            items.forEach(function (it) {
                (out[it.work_order_id] = out[it.work_order_id] || []).push(it);
            });
            return out;
        }

        function errKeyOf(err) {
            var key = AI.api.mapApiErrorKey(err && err.code);
            return key !== 'err_generic' && at(key) !== key ? key : null;
        }

        function findGroup(flagReason) {
            return st.flaggedGroups.filter(function (g) {
                return g.flagReason === flagReason;
            })[0];
        }

        function runGroupBatch(flagReason, template) {
            var group = findGroup(flagReason);
            if (!group || !group.items.length) return;
            var g = groupUiFor(flagReason);
            if (g.busy) return;
            g.busy = true;
            hooks.onChange();
            var grouped = byOrder(group.items);
            var orderIds = Object.keys(grouped);
            Promise.all(
                orderIds.map(function (oid) {
                    var decisions = grouped[oid].map(function (it) {
                        return Object.assign({ item_id: it.item_id }, template);
                    });
                    return api
                        .batchDecisions(oid, decisions)
                        .then(function (res) {
                            return { oid: oid, res: res };
                        })
                        .catch(function (err) {
                            return { oid: oid, err: err };
                        });
                })
            ).then(function (results) {
                g.busy = false;
                var ok = 0,
                    fail = 0,
                    touchedIds = [];
                results.forEach(function (r) {
                    if (r.err) {
                        grouped[r.oid].forEach(function (it) {
                            g.local[it.item_id] = { state: 'failed', errKey: errKeyOf(r.err) };
                            fail += 1;
                        });
                        return;
                    }
                    (r.res.results || []).forEach(function (row) {
                        if (row.ok) {
                            g.local[row.item_id] = { state: 'done', decision: template };
                            touchedIds.push(row.item_id);
                            ok += 1;
                        } else {
                            g.local[row.item_id] = { state: 'failed', errKey: null };
                            fail += 1;
                        }
                    });
                });
                rebuildGroups();
                hooks.onChange();
                hooks.showToast(at('riq_bulk_result', { ok: ok, fail: fail }), function () {
                    touchedIds.forEach(function (id) {
                        delete g.local[id];
                    });
                    rebuildGroups();
                    hooks.onChange();
                });
                hooks.afterMutate();
            });
        }

        function onBulk(flagReason) {
            var group = findGroup(flagReason);
            if (!group || !AI.reviewVerdict.groupCanBulk(group.items)) return;
            runGroupBatch(flagReason, AI.reviewVerdict.bulkDecisionTemplate(flagReason));
        }

        function onExcludeAll(flagReason) {
            runGroupBatch(flagReason, { decision: 'exclude' });
        }

        function decideItem(itemId, action, vatRaw) {
            var item = st.itemIndex[itemId];
            if (!item) return;
            var payload = AI.reviewQueue.buildDecisionPayload(itemId, action, vatRaw);
            var g = groupUiFor(item.flag_reason);
            var iu = itemUiFor(item.flag_reason, itemId);
            if (!payload) {
                iu.editErr = true;
                hooks.onChange();
                return;
            }
            g.local[itemId] = { state: 'pending' };
            iu.editing = false;
            iu.editErr = false;
            hooks.onChange();
            api.decide(item.work_order_id, payload)
                .then(function () {
                    g.local[itemId] = { state: 'done', decision: payload };
                    if (action === 'exclude') {
                        hooks.showToast(
                            AI.reviewQueue.fileName(item.file_ref) + ' · ' + at('rv_chip_excluded'),
                            function () {
                                delete g.local[itemId];
                                rebuildGroups();
                                hooks.onChange();
                            }
                        );
                    }
                    rebuildGroups();
                    hooks.onChange();
                    hooks.afterMutate();
                })
                .catch(function (err) {
                    g.local[itemId] = { state: 'failed', errKey: errKeyOf(err) };
                    hooks.onChange();
                });
        }

        function startEdit(itemId, focusFn) {
            var item = st.itemIndex[itemId];
            if (!item) return;
            var iu = itemUiFor(item.flag_reason, itemId);
            iu.editing = true;
            iu.editErr = false;
            iu.editValue = (item.ocr_read || {}).vat || '';
            hooks.onChange();
            if (focusFn) focusFn();
        }

        // 原图模态:生产同款查看器(AI.viewer 缩放/拖拽/旋转 + LRU 缓存,UI-Canon 惯例;
        // 骨架复用 AI.reconRender.viewModalHtml,同 ai-recon.js 原图模态先例)。此前裸
        // window.open(objectURL)既没有查看器交互也不 revoke;载入失败由查看器 noimg 态
        // 诚实呈现。挂 document.body,路由切走由编排层调 closeImage 收。
        function viewImage(orderId, itemId) {
            closeImage();
            document.body.insertAdjacentHTML(
                'beforeend',
                AI.reconRender.viewModalHtml({ kind: 'invoice' })
            );
            var mask = document.getElementById('brxViewMask');
            mask.classList.add('enter');
            mask.querySelector('.mclose').onclick = closeImage;
            mask.addEventListener('click', function (e) {
                if (e.target === mask) closeImage();
            });
            AI.viewer.remountViewer('riq-img', mask.querySelector('.pkg-evid-view'), {
                key: itemId,
                loader: function () {
                    return api.getItemImageBlob(orderId, itemId).then(function (blob) {
                        return URL.createObjectURL(blob);
                    });
                },
            });
        }

        function closeImage() {
            AI.viewer.remountViewer('riq-img', null, {});
            var mask = document.getElementById('brxViewMask');
            if (mask) mask.remove();
        }

        function firstUndecidedItem(group) {
            return group.items.filter(function (it) {
                var local = groupUiFor(group.flagReason).local[it.item_id];
                return !local || local.state === 'failed';
            })[0];
        }

        return {
            isLoading: function () {
                return st.detailLoading;
            },
            groups: function () {
                return st.flaggedGroups;
            },
            groupUiMap: function () {
                return st.groupUi;
            },
            itemById: function (itemId) {
                return st.itemIndex[itemId];
            },
            loadFor: loadFor,
            onBulk: onBulk,
            onExcludeAll: onExcludeAll,
            decideItem: decideItem,
            startEdit: startEdit,
            viewImage: viewImage,
            closeImage: closeImage,
            findGroup: findGroup,
            firstUndecidedItem: firstUndecidedItem,
        };
    }

    window.AI = window.AI || {};
    window.AI.reviewInboxFlagged = { create: create };
})();
