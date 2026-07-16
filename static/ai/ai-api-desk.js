/*
 * Pearnly AI · ai-api-desk.js · 总台(FD-0d)前门四端点的后端调用薄层(拆自 ai-api.js)
 *
 * 单文件<500 行铁律:ai-api.js 已在预算线上(见 ai-api-payroll.js 顶注同款理由),
 * front_desk 四端点(建草稿+暂存投料/大脑解析/人确认开工/消息流重建)体量独立,
 * 依赖面窄(root/authHeaders/handleResponse/call 四个 apiFactory 内部闭包量),拆出去
 * 零行为改变——同 ai-api-payroll.js/ai-api-client-import.js/ai-api-review.js 先例。
 *
 * 工厂函数 create(root, authHeaders, handleResponse, call) 由 ai-api.js 的 apiFactory()
 * 调用,返回的方法对象被 Object.assign 进 AI.api.create() 的结果里,调用方(ai-desk.js)
 * 感知不到这层拆分。
 */
(function (root) {
    'use strict';

    function create(root, authHeaders, handleResponse, call) {
        return {
            // 建草稿合同 + 暂存投料(multipart,不能走 call()):client/period/intent 均可选
            // (先投料出盘点卡,后说目标填合同卡)。响应 {contract, inventory}。
            createDeskContract: function (opts) {
                opts = opts || {};
                var fd = new FormData();
                if (opts.clientId) fd.append('workspace_client_id', opts.clientId);
                if (opts.period) fd.append('period', opts.period);
                if (opts.intent) fd.append('intent', opts.intent);
                (opts.files || []).forEach(function (f) {
                    fd.append('files', f);
                });
                return root
                    .fetch('/api/ai/front-desk/contracts', {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 一句话目标 → 大脑意图/客户/期间建议。fail-closed:闸关/超时/异常都收敛成
            // {degraded:true} 信封,不上抛(见 services/front_desk/interpret.py)。
            interpretDeskGoal: function (contractId, utterance) {
                return call('POST', '/api/ai/front-desk/interpret', {
                    contract_id: contractId,
                    utterance: utterance,
                });
            },
            // 人点确认:定客户/期间/意图 → 开工单(幂等)+ 暂存料入料。
            confirmDeskContract: function (body) {
                return call('POST', '/api/ai/front-desk/confirm', body);
            },
            // 重建消息流(该租户按客户筛的合同倒序)。limit 缺省 50,同后端默认口径。
            // clientId 传 null/undefined 时不筛(全租户),也用作闸探针(GET limit=1)。
            getDeskFeed: function (clientId, limit) {
                var qs = '?limit=' + encodeURIComponent(limit || 50);
                if (clientId != null && clientId !== '')
                    qs += '&client_id=' + encodeURIComponent(clientId);
                return call('GET', '/api/ai/front-desk/feed' + qs);
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiDesk = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
