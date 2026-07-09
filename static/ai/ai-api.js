/*
 * Pearnly AI · ai-api.js · 后端调用薄层(工单制 API + 只读账套主体 API)
 *
 * 鉴权复用既有登录会话(localStorage mrpilot_token,同 console.js/pos.js 先例)——
 * 不新建登录态。闸行为(2026-07-09 拍板):M1 闸关或未登录一律拿到 404/401,
 * 调用方据此整页跳回 /home,不在本页渲染任何业务内容(fail-closed)。
 */
(function (root) {
    'use strict';

    // 错误码 → i18n key 的确定性映射(纯函数,DOM 层用 window.at(mapApiErrorKey(code)) 取文案)。
    function mapApiErrorKey(code) {
        if (!code) return 'err_generic';
        var key = 'err_' + String(code).replace(/\./g, '_');
        return key;
    }

    function apiFactory(opts) {
        opts = opts || {};
        var getToken =
            opts.getToken ||
            function () {
                return root.localStorage.getItem('mrpilot_token');
            };

        function call(method, path, body) {
            var token = getToken();
            var headers = {};
            if (token) headers.Authorization = 'Bearer ' + token;
            if (body) headers['Content-Type'] = 'application/json';
            return root
                .fetch(path, {
                    method: method,
                    headers: headers,
                    body: body ? JSON.stringify(body) : undefined,
                })
                .then(function (r) {
                    return r
                        .json()
                        .catch(function () {
                            return {};
                        })
                        .then(function (j) {
                            if (!r.ok) {
                                var code = j.detail || (j.error && j.error.code) || 'generic';
                                var err = new Error(String(code));
                                err.status = r.status;
                                err.code = code;
                                throw err;
                            }
                            return j;
                        });
                });
        }

        return {
            listOrders: function (query) {
                var qs = query
                    ? '?' +
                      Object.keys(query)
                          .filter(function (k) {
                              return query[k] !== undefined && query[k] !== null && query[k] !== '';
                          })
                          .map(function (k) {
                              return encodeURIComponent(k) + '=' + encodeURIComponent(query[k]);
                          })
                          .join('&')
                    : '';
                return call('GET', '/api/workorder/orders' + qs);
            },
            getOrder: function (id) {
                return call('GET', '/api/workorder/orders/' + encodeURIComponent(id));
            },
            createOrder: function (body) {
                return call('POST', '/api/workorder/orders', body);
            },
            listDeliverables: function (id) {
                return call(
                    'GET',
                    '/api/workorder/orders/' + encodeURIComponent(id) + '/deliverables'
                );
            },
            listClients: function () {
                return call('GET', '/api/workspace/clients');
            },
            getClient: function (id) {
                return call('GET', '/api/workspace/clients/' + encodeURIComponent(id));
            },
            runOrder: function (id) {
                return call('POST', '/api/workorder/orders/' + encodeURIComponent(id) + '/run');
            },
            decide: function (orderId, body) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/decisions',
                    body
                );
            },
            // 原图直出(W3 审核队列):鉴权头是 Bearer,<img src> 发不了自定义头,调用方
            // 拿 blob 自建 object URL 挂 <img>(同 console.js 导出下载的 fetch+blob 先例)。
            getItemImageBlob: function (orderId, itemId) {
                var token = getToken();
                var headers = {};
                if (token) headers.Authorization = 'Bearer ' + token;
                return root
                    .fetch(
                        '/api/workorder/orders/' +
                            encodeURIComponent(orderId) +
                            '/items/' +
                            encodeURIComponent(itemId) +
                            '/image',
                        { headers: headers }
                    )
                    .then(function (r) {
                        if (!r.ok) {
                            var err = new Error('workorder.item_image_not_found');
                            err.status = r.status;
                            throw err;
                        }
                        return r.blob();
                    });
            },
        };
    }

    var apiExport = { mapApiErrorKey: mapApiErrorKey, create: apiFactory };
    if (typeof module !== 'undefined' && module.exports) module.exports = apiExport;
    if (root) {
        root.AI = root.AI || {};
        root.AI.api = apiExport;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
