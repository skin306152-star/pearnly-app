/* Pearnly AI · 银行倒推销项 API 薄层；拆出避免 ai-api.js 顶格。 */
(function (root) {
    'use strict';

    function create(call) {
        function path(orderId, suffix) {
            return '/api/workorder/orders/' + encodeURIComponent(orderId) + '/bank-sales/' + suffix;
        }
        return {
            runBankSales: function (orderId) {
                return call('POST', path(orderId, 'run'));
            },
            bankSalesProgress: function (orderId) {
                return call('GET', path(orderId, 'progress'));
            },
            decideBankSales: function (orderId, body) {
                return call('POST', path(orderId, 'decide'), body);
            },
            decideBankSalesBatch: function (orderId, decisions) {
                return call('POST', path(orderId, 'decide-batch'), { decisions: decisions });
            },
        };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.apiBankSales = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
