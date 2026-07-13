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
        // 2xx → 解出 JSON。JSON/multipart 请求共用同一份,不各拼一套错误契约。detail 多数是
        // 裸字符串 key,但 payroll output 端点的「无该期数据」故意回结构化 {code,message}
        // (routes/payroll_routes.py)——两种形态都取得到 code,不新开一条错误处理分叉。
        function handleResponse(r) {
            return r
                .json()
                .catch(function () {
                    return {};
                })
                .then(function (j) {
                    if (!r.ok) {
                        var detail = j.detail;
                        var code =
                            (detail && typeof detail === 'object' ? detail.code : detail) ||
                            (j.error && j.error.code) ||
                            'generic';
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

        // core.pos_api.ok() 信封({"ok":true,"data":{...}})的调用方用这个,解出 .data 让
        // 调用方拿到的形状跟其它 AI 端点(workorder/workspace,裸对象无信封)一致——
        // 别让信封差异渗进 ai-profile.js 的业务代码里(Z3-b · 供应商过账档案)。
        function callEnvelope(method, path, body) {
            return call(method, path, body).then(function (j) {
                return (j && j.data) || {};
            });
        }

        // base 拼上 ai-api-payroll.js 拆出去的工资表方法(见文末 Object.assign)——单文件
        // <500 行铁律下 apiFactory() 主体不再直接容纳工资表五个端点。
        var base = {
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
            // 销项税报告三查(N1-a · routes/vat_report_checks_routes.py):multipart 单文件上传,
            // 同 addMaterials 不能走 call()(要让浏览器带 multipart boundary)。响应即三查结果,
            // 不经 callEnvelope(该端点裸对象出线,无信封)。
            runVatReportChecks: function (file) {
                var token = getToken();
                var headers = {};
                if (token) headers.Authorization = 'Bearer ' + token;
                var fd = new FormData();
                fd.append('report', file);
                return root
                    .fetch('/api/vat_report_checks/run', {
                        method: 'POST',
                        headers: headers,
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 财务文件转换(K1b · routes/fileconv_routes.py):multipart 单文件上传,同
            // runVatReportChecks 不能走 call()。默认回 JSON 摘要;下载 Excel 是同一份
            // 文件再 POST 一次 ?format=xlsx(后端无状态两段式,引擎幂等不落服务端状态)。
            convertFile: function (file) {
                var fd = new FormData();
                fd.append('file', file);
                return root
                    .fetch('/api/fileconv/convert', {
                        method: 'POST',
                        headers: authHeaders(),
                        body: fd,
                    })
                    .then(handleResponse);
            },
            // 附件路共用(xlsx/pdf 二进制流不能进 handleResponse,它只认 JSON):成功从
            // Content-Disposition 取文件名(泰文原名在 filename*/RFC 5987,优先取;取不到
            // 退 ASCII filename),失败仍是 JSON 错误壳,借 handleResponse 抛同构 code/status
            // 错误,调用方文案不分叉。
            _downloadAttachment: function (url, file, fallbackName) {
                var fd = new FormData();
                fd.append('file', file);
                return root
                    .fetch(url, { method: 'POST', headers: authHeaders(), body: fd })
                    .then(function (r) {
                        if (!r.ok) return handleResponse(r);
                        var disp = r.headers.get('Content-Disposition') || '';
                        var star = /filename\*=UTF-8''([^;]+)/.exec(disp);
                        var plain = /filename="?([^";]+)"?/.exec(disp);
                        var filename = star
                            ? decodeURIComponent(star[1])
                            : plain
                              ? plain[1]
                              : fallbackName;
                        return r.blob().then(function (blob) {
                            return { blob: blob, filename: filename };
                        });
                    });
            },
            downloadConvertedXlsx: function (file) {
                return this._downloadAttachment(
                    '/api/fileconv/convert?format=xlsx',
                    file,
                    'convert.xlsx'
                );
            },
            // K2:规范排版 PDF 附件,lang 走当前 UI 语种(缺省 th,同 accounting_books_routes
            // 的 _lang() 兜底口径)。
            downloadConvertedPdf: function (file, lang) {
                var url =
                    '/api/fileconv/convert?format=pdf&lang=' + encodeURIComponent(lang || 'th');
                return this._downloadAttachment(url, file, 'convert.pdf');
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
            // 供应商过账档案(Z3-b · routes/supplier_posting_routes.py)。中立能力层 API,
            // clientId 即该端点的 workspace_client_id(与 tax-profile/aliases 同一账套上下文)。
            listSupplierProfiles: function (clientId) {
                return callEnvelope(
                    'GET',
                    '/api/purchase/supplier-profiles?workspace_client_id=' +
                        encodeURIComponent(clientId)
                );
            },
            putSupplierProfile: function (clientId, taxId, body) {
                return callEnvelope(
                    'PUT',
                    '/api/purchase/supplier-profiles/' + encodeURIComponent(taxId),
                    Object.assign({ workspace_client_id: clientId }, body)
                );
            },
            deleteSupplierProfile: function (clientId, taxId) {
                return callEnvelope(
                    'DELETE',
                    '/api/purchase/supplier-profiles/' +
                        encodeURIComponent(taxId) +
                        '?workspace_client_id=' +
                        encodeURIComponent(clientId)
                );
            },
            // 事务所矩阵(C4·routes/tax_profile_routes.py::get_tax_profile_matrix):客户 ×
            // 当期义务的聚合只读端点,一次请求喂全矩阵。period 缺省=后端当期。
            getTaxProfileMatrix: function (period) {
                var qs = period ? '?period=' + encodeURIComponent(period) : '';
                return call('GET', '/api/tax-profile/matrix' + qs);
            },
            // LINE 待问客户池(D2-S8+S9 · routes/client_pool_routes.py)。stage 是 W3 第四动作
            // 落点(work_order_id 由调用方按当前工单传入,同 decide() 不把 order id 塞进 body
            // 一个道理——这里例外是因为 stage 端点不挂在 /orders/{id}/ 下,body 里必须带 id)。
            stageQuestion: function (workOrderId, body) {
                return call(
                    'POST',
                    '/api/ai/client-pool/stage',
                    Object.assign({ work_order_id: workOrderId }, body)
                );
            },
            listClientPool: function (workspaceClientId) {
                var qs =
                    workspaceClientId != null
                        ? '?workspace_client_id=' + encodeURIComponent(workspaceClientId)
                        : '';
                return call('GET', '/api/ai/client-pool' + qs);
            },
            pushClientPoolBatch: function (workspaceClientId) {
                return call('POST', '/api/ai/client-pool/push-batch', {
                    workspace_client_id: workspaceClientId,
                });
            },
            decideClientPoolQuestion: function (questionId, body) {
                return call(
                    'POST',
                    '/api/ai/client-pool/questions/' + encodeURIComponent(questionId) + '/decide',
                    body
                );
            },
            // N1-P0-1:建账套主体(客户目录页「+新建客户」表单)。裸对象出线(无信封),
            // 422 走 workspace.thai_name_required / workspace.tax_id_duplicate,调用方
            // mapApiErrorKey 取四语文案(同 handleResponse 既有 code 抽取口径,detail
            // 是 {code,message} 对象还是裸字符串都取得到 code,不必在这里特判)。
            createWorkspaceClient: function (body) {
                return call('POST', '/api/workspace/clients', body);
            },
            // 按钮显隐探针(state honesty:没权限不给一个点了才 403 的假门)。
            canCreateWorkspaceClient: function () {
                return call('GET', '/api/workspace/clients/can-create');
            },
            // N1-P0-3:月度报表打印级 PDF/Excel——附件路,同 downloadConvertedPdf/
            // downloadPayrollOutput 先例(GET 带鉴权头,<a href> 发不了自定义头,调用方
            // 拿 blob 自建 object URL)。
            downloadFinancialsReport: function (orderId, format, lang) {
                var qs =
                    '?format=' +
                    encodeURIComponent(format || 'pdf') +
                    '&lang=' +
                    encodeURIComponent(lang || 'th');
                return root
                    .fetch(
                        '/api/workorder/orders/' +
                            encodeURIComponent(orderId) +
                            '/financials/download' +
                            qs,
                        { headers: authHeaders() }
                    )
                    .then(function (r) {
                        if (!r.ok) return handleResponse(r);
                        var disp = r.headers.get('Content-Disposition') || '';
                        var star = /filename\*=UTF-8''([^;]+)/.exec(disp);
                        var plain = /filename="?([^";]+)"?/.exec(disp);
                        var filename = star
                            ? decodeURIComponent(star[1])
                            : plain
                              ? plain[1]
                              : 'financials.' + (format || 'pdf');
                        return r.blob().then(function (blob) {
                            return { blob: blob, filename: filename };
                        });
                    });
            },
        };
        return Object.assign(base, AI.apiPayroll.create(root, authHeaders, handleResponse));
    }

    var apiExport = { mapApiErrorKey: mapApiErrorKey, create: apiFactory };
    if (typeof module !== 'undefined' && module.exports) module.exports = apiExport;
    if (root) {
        root.AI = root.AI || {};
        root.AI.api = apiExport;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
