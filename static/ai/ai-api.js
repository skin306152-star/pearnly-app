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

        // Bearer 头:有 token 才带,没有就是空头(fail-closed 交给后端 401)——
        // call()/getItemImageBlob/downloadDeliverable 共用同一份,不各拼一套。
        function authHeaders() {
            var token = getToken();
            return token ? { Authorization: 'Bearer ' + token } : {};
        }

        // 响应外壳统一处理:非 2xx → 抛带 code/status 的 Error(调用方 mapApiErrorKey 取文案),
        // 2xx → 解出 JSON。JSON/multipart 请求共用同一份,不各拼一套错误契约。
        function handleResponse(r) {
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
        }

        function call(method, path, body) {
            var headers = authHeaders();
            if (body) headers['Content-Type'] = 'application/json';
            return root
                .fetch(path, {
                    method: method,
                    headers: headers,
                    body: body ? JSON.stringify(body) : undefined,
                })
                .then(handleResponse);
        }

        return {
            // Z1-a · 登录门面用:未登录态调用,不带 Authorization(authHeaders 见 token 为空
            // 自然省略头)。成功回 {token, access_token, user, is_super_admin} 同 landing.js 契约。
            login: function (username, password, remember) {
                return call('POST', '/api/login', {
                    username: username,
                    password: password,
                    remember: !!remember,
                });
            },
            // 邀请制门面判别用:token 有效性探针(非闸接口)——工单闸 404 时借它分辨"未登录/
            // token 失效"与"已登录但未受邀"(见 ai.js boot() 的 resolveGateClosed)。
            getMe: function () {
                return call('GET', '/api/me');
            },
            logout: function () {
                return call('POST', '/api/logout');
            },
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
            // 人工填销项(W4 补料流):销售额/销项税/凭据备注,后端落 sales_summary 事件解锁 R2。
            submitSalesSummary: function (orderId, body) {
                return call(
                    'POST',
                    '/api/workorder/orders/' + encodeURIComponent(orderId) + '/sales-summary',
                    body
                );
            },
            // 补料上传(W4):multipart。<fetch> 发 FormData 时不能手设 Content-Type
            // (要让浏览器带 multipart boundary),故不走 call()。413 等结构化错误同源经
            // handleResponse 抛出,调用方 mapApiErrorKey 取四语文案。
            addMaterials: function (orderId, files) {
                var token = getToken();
                var headers = {};
                if (token) headers.Authorization = 'Bearer ' + token;
                var fd = new FormData();
                for (var i = 0; i < files.length; i++) fd.append('files', files[i]);
                return root
                    .fetch('/api/workorder/orders/' + encodeURIComponent(orderId) + '/materials', {
                        method: 'POST',
                        headers: headers,
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 交付物下载(W5 交付包页):鉴权头是 Bearer,<a href> 发不了自定义头,调用方拿
            // blob 自建 object URL 触发下载(同 console.js exportLog 的 fetch+blob 先例)。
            // 文件名从服务端 Content-Disposition 读(FileResponse 已带 filename=真实文件名),
            // 读不到时退化用 kind 本身,不编一个假名字。
            downloadDeliverable: function (orderId, kind) {
                return root
                    .fetch(
                        '/api/workorder/orders/' +
                            encodeURIComponent(orderId) +
                            '/deliverables/' +
                            encodeURIComponent(kind),
                        { headers: authHeaders() }
                    )
                    .then(function (r) {
                        if (!r.ok) {
                            var err = new Error('workorder.deliverable_not_found');
                            err.status = r.status;
                            throw err;
                        }
                        var disp = r.headers.get('Content-Disposition') || '';
                        var m = /filename="?([^";]+)"?/.exec(disp);
                        var filename = m ? m[1] : kind;
                        return r.blob().then(function (blob) {
                            return { blob: blob, filename: filename };
                        });
                    });
            },
            // 原图直出(W3 审核队列 / W5 证据回链):鉴权头是 Bearer,<img src> 发不了自定义头,
            // 调用方拿 blob 自建 object URL 挂 <img>(同 console.js 导出下载的 fetch+blob 先例)。
            getItemImageBlob: function (orderId, itemId) {
                return root
                    .fetch(
                        '/api/workorder/orders/' +
                            encodeURIComponent(orderId) +
                            '/items/' +
                            encodeURIComponent(itemId) +
                            '/image',
                        { headers: authHeaders() }
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
            // 税务画像/别名/义务清单(B2-e · routes/tax_profile_routes.py)。三块围绕
            // 同一个 workspace_client_id,不挂在某个具体工单下。
            getTaxProfile: function (clientId) {
                return call(
                    'GET',
                    '/api/workspace/clients/' + encodeURIComponent(clientId) + '/tax-profile'
                );
            },
            putTaxProfile: function (clientId, body) {
                return call(
                    'PUT',
                    '/api/workspace/clients/' + encodeURIComponent(clientId) + '/tax-profile',
                    body
                );
            },
            listAliases: function (clientId) {
                return call(
                    'GET',
                    '/api/workspace/clients/' + encodeURIComponent(clientId) + '/aliases'
                );
            },
            addAlias: function (clientId, body) {
                return call(
                    'POST',
                    '/api/workspace/clients/' + encodeURIComponent(clientId) + '/aliases',
                    body
                );
            },
            deactivateAlias: function (clientId, aliasId) {
                return call(
                    'POST',
                    '/api/workspace/clients/' +
                        encodeURIComponent(clientId) +
                        '/aliases/' +
                        encodeURIComponent(aliasId) +
                        '/deactivate'
                );
            },
            listObligations: function (clientId, period) {
                var qs = period ? '?period=' + encodeURIComponent(period) : '';
                return call(
                    'GET',
                    '/api/workspace/clients/' + encodeURIComponent(clientId) + '/obligations' + qs
                );
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
