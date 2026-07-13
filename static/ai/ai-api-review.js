/*
 * Pearnly AI · ai-api-review.js · 审核收件箱 + 签批闭环的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:同 ai-api-payroll.js 先例拆出,体量独立、依赖面窄。MC1-b1 四端点
 * (review-queue/decisions:batch/review-reject/self-review-declare)+ 既有三端点(review
 * 签批/archive 冻结/receipt 回执补挂,C3 批次已落地但此前无前端调用方)。
 *
 * 工厂函数 create(root, authHeaders, handleResponse, call, queryString) 由 ai-api.js 的
 * apiFactory() 调用(五个都是它的内部闭包量,call/queryString 与主组共用同一份,不重抄),
 * 返回的方法对象被 Object.assign 进 AI.api.create() 的结果里,调用方(ai-review-inbox.js)
 * 感知不到这层拆分。
 */
(function (root) {
    'use strict';

    function create(root, authHeaders, handleResponse, call, queryString) {
        return {
            // 全所审核队列(MC1-b1·客户×工单聚合):待审工单 + flagged 按 flag_reason 分组 +
            // 客户池 pending 数 + 义务到期日 + 返工标记。query 缺省字段不上串(queryString
            // 与 listOrders 同一份过滤)。
            getReviewQueue: function (query) {
                return call('GET', '/api/workorder/review-queue' + queryString(query));
            },
            // 批量裁决(MC1-b1):部分成功诚实逐条返回,调用方不假装整批成功。
            batchDecisions: function (orderId, decisions) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/decisions:batch',
                    { decisions: decisions }
                );
            },
            // 驳回重做(MC1-b1):原因必填,后端自动重跑受影响步,出新版本交付物。
            reviewReject: function (orderId, reason) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/review-reject',
                    { reason: reason }
                );
            },
            // 单人所自审声明(MC1-b1 · 方案决策 5 声明制不豁免制)。
            declareSelfReview: function (orderId) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/self-review-declare'
                );
            },
            // 复核签批(C3 四权分立):review 态内落 append-only review_signoff 事件。
            reviewSignoff: function (orderId, note) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/review',
                    { note: note || '' }
                );
            },
            // 冻结归档(C3):review→archive 原子出 freeze_manifest,冻结后只读。
            archiveOrder: function (orderId) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/archive'
                );
            },
            // 申报回执补挂(C3):冻结后唯一可写路径,multipart 单文件,同 addMaterials
            // 不能走 call()(要让浏览器带 multipart boundary)。
            attachReceipt: function (orderId, file) {
                var headers = authHeaders();
                var fd = new FormData();
                fd.append('file', file);
                return root
                    .fetch('/api/workorder/orders/' + encodeURIComponent(orderId) + '/receipt', {
                        method: 'POST',
                        headers: headers,
                        body: fd,
                    })
                    .then(handleResponse);
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiReview = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
