/*
 * Pearnly AI · ai-review-inbox-signoff.js · 工单卡签批闭环状态机(MC1-b2)
 *
 * 拆出独立于 ai-review-inbox.js 主状态(单文件<500 铁律,同 ai-review-pool.js 拆自
 * ai-review.js 的先例):按 work_order_id 持有签批/冻结/驳回/自审声明/回执五个动作的
 * 忙态与结果,与「异常票据」裁决态平行独立、互不干扰。
 *
 * SoD 显隐(方案 §2 b2「preparer 看不到复核钮」)受限于可用数据:order-detail 不携带
 * 制单人/复核人集合(那是 events 回放,读侧投影未暴露,b2 红线不碰后端加字段)。现状:
 * 按钮常显,撞上后端 SoD 拒绝(422/409)时显示解释文案(sodErr)+ 自审声明出路;真正的
 * 按角色收起按钮升格到 MC2-A(前端提前算不准角色,猜错比不猜更危险)。
 */
(function () {
    'use strict';

    function create(api) {
        var ui = {};

        function forOrder(orderId) {
            if (!ui[orderId]) {
                ui[orderId] = {
                    signoffBusy: false,
                    signedNote: null,
                    archiveBusy: false,
                    archivedNote: null,
                    rejectOpen: false,
                    rejectValue: '',
                    rejectErr: false,
                    rejectBusy: false,
                    selfDeclareBusy: false,
                    selfDeclared: false,
                    receiptBusy: false,
                    receiptNote: null,
                    sodErr: null,
                };
            }
            return ui[orderId];
        }

        function errText(err) {
            var key = AI.api.mapApiErrorKey(err && err.code);
            return at(key) !== key ? at(key) : at('err_generic');
        }

        function signoff(orderId, actorLabel, onSettle) {
            var u = forOrder(orderId);
            if (u.signoffBusy || u.signedNote) return;
            u.signoffBusy = true;
            u.sodErr = null;
            onSettle();
            api.reviewSignoff(orderId, '')
                .then(function () {
                    u.signoffBusy = false;
                    u.signedNote = at('riq_signoff_done', { actor: actorLabel });
                    onSettle();
                })
                .catch(function (err) {
                    u.signoffBusy = false;
                    u.sodErr = errText(err);
                    onSettle();
                });
        }

        function archive(orderId, actorLabel, onSettle) {
            var u = forOrder(orderId);
            if (u.archiveBusy || u.archivedNote) return;
            u.archiveBusy = true;
            u.sodErr = null;
            onSettle();
            api.archiveOrder(orderId)
                .then(function () {
                    u.archiveBusy = false;
                    u.archivedNote = at('riq_archive_done', { actor: actorLabel });
                    onSettle();
                })
                .catch(function (err) {
                    u.archiveBusy = false;
                    u.sodErr = errText(err);
                    onSettle();
                });
        }

        function openReject(orderId, onSettle) {
            var u = forOrder(orderId);
            u.rejectOpen = true;
            u.rejectErr = false;
            onSettle();
        }

        function cancelReject(orderId, onSettle) {
            var u = forOrder(orderId);
            u.rejectOpen = false;
            u.rejectValue = '';
            u.rejectErr = false;
            onSettle();
        }

        function setRejectValue(orderId, value) {
            forOrder(orderId).rejectValue = value;
        }

        function submitReject(orderId, onSettle, onDone) {
            var u = forOrder(orderId);
            var reason = (u.rejectValue || '').trim();
            if (!reason) {
                u.rejectErr = true;
                onSettle();
                return;
            }
            u.rejectBusy = true;
            u.rejectErr = false;
            onSettle();
            api.reviewReject(orderId, reason)
                .then(function () {
                    u.rejectBusy = false;
                    u.rejectOpen = false;
                    u.rejectValue = '';
                    onSettle();
                    if (onDone) onDone();
                })
                .catch(function (err) {
                    u.rejectBusy = false;
                    u.sodErr = errText(err);
                    onSettle();
                });
        }

        function selfDeclare(orderId, onSettle) {
            var u = forOrder(orderId);
            if (u.selfDeclareBusy || u.selfDeclared) return;
            u.selfDeclareBusy = true;
            onSettle();
            api.declareSelfReview(orderId)
                .then(function () {
                    u.selfDeclareBusy = false;
                    u.selfDeclared = true;
                    u.sodErr = null;
                    onSettle();
                })
                .catch(function (err) {
                    u.selfDeclareBusy = false;
                    u.sodErr = errText(err);
                    onSettle();
                });
        }

        function attachReceipt(orderId, file, onSettle) {
            var u = forOrder(orderId);
            if (u.receiptBusy) return;
            u.receiptBusy = true;
            onSettle();
            api.attachReceipt(orderId, file)
                .then(function () {
                    u.receiptBusy = false;
                    u.receiptNote = at('riq_receipt_done');
                    onSettle();
                })
                .catch(function (err) {
                    u.receiptBusy = false;
                    u.sodErr = errText(err);
                    onSettle();
                });
        }

        return {
            forOrder: forOrder,
            signoff: signoff,
            archive: archive,
            openReject: openReject,
            cancelReject: cancelReject,
            setRejectValue: setRejectValue,
            submitReject: submitReject,
            selfDeclare: selfDeclare,
            attachReceipt: attachReceipt,
        };
    }

    window.AI = window.AI || {};
    window.AI.reviewInboxSignoff = { create: create };
})();
