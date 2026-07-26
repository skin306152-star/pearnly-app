/*
 * Pearnly AI · ai-api-billing.js · OCR 余额/充值四端点的后端调用薄层(拆自 ai-api.js 体例)
 *
 * 单文件<500 行铁律:ai-api.js 已在预算线上,计费端点自成一族 —— 同 ai-api-steward.js/
 * ai-api-client-import.js 先例拆出去,调用方感知不到这层拆分。
 *
 * 四端点全部现成且经 /home 生产验证(routes/billing_credits_routes.py /
 * billing_topup_routes.py),本文件零新增钱逻辑:
 *   GET  /api/me/credits                        → 余额/本月用量/费率(员工视角无 balance_thb)
 *   POST /api/credits/topup/request             → {request_id}
 *   POST /api/credits/topup/upload-slip/{id}    → {auto_approved}(multipart,不走 call())
 *   GET  /api/credits/topup/history             → 近 20 条充值申请
 */
(function (root) {
    'use strict';

    function create(root, authHeaders, handleResponse, call) {
        return {
            getCredits: function () {
                return call('GET', '/api/me/credits');
            },
            topupRequest: function (amountThb) {
                return call('POST', '/api/credits/topup/request', { amount_thb: amountThb });
            },
            // 付款人/备注在第 3 步随凭证一起交(后端 upload-slip 补写这两列,见
            // billing_topup_routes.py)——空串不上传,别把占位空值写进人工审核台账。
            uploadTopupSlip: function (requestId, file, payerName, note) {
                var fd = new FormData();
                fd.append('file', file);
                if (payerName) fd.append('payer_name', payerName);
                if (note) fd.append('note', note);
                return root
                    .fetch('/api/credits/topup/upload-slip/' + encodeURIComponent(requestId), {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            getTopupHistory: function () {
                return call('GET', '/api/credits/topup/history');
            },
        };
    }

    if (typeof module !== 'undefined' && module.exports) module.exports = { create: create };
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiBilling = { create: create };
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
