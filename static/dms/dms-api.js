/* Pearnly DMS · 后端调用薄层 window.DXAPI(登录门面 + 门禁探针 + 推送记录)。
 * 身份证向导自身直接 fetch /api/dms/*(移植保真,不经此层);此层只承载壳级调用:
 *   login(entry:'dms')/getMe/probe(闸判定)/pushLogs(记录页)。
 * 错误契约同 ai-api:HTTP 4xx/5xx 拒绝值带 {status,code}(gate 据此报人话);
 * 网络失败(fetch 自身 reject)无 status(状态诚实:断网 ≠ 密码错)。 */
(function (root) {
    'use strict';

    function authHeaders(json) {
        var tk = '';
        try {
            tk = localStorage.getItem('mrpilot_token') || '';
        } catch (e) {
            tk = '';
        }
        var h = {};
        if (tk) h.Authorization = 'Bearer ' + tk;
        if (json) h['Content-Type'] = 'application/json';
        return h;
    }

    function _reject(r, data) {
        var detail = data && data.detail;
        var code = (detail && (detail.code || detail)) || (data && data.code) || 'generic';
        return Promise.reject({ status: r.status, code: String(code), data: data });
    }
    function call(method, path, body) {
        var opt = { method: method, headers: authHeaders(!!body) };
        if (body) opt.body = JSON.stringify(body);
        return fetch(path, opt).then(function (r) {
            return r
                .json()
                .catch(function () {
                    return {};
                })
                .then(function (data) {
                    return r.ok ? data : _reject(r, data);
                });
        });
    }
    // 表单上传(凭证图):不设 Content-Type,交给浏览器带 multipart boundary。
    function callForm(method, path, form) {
        return fetch(path, { method: method, headers: authHeaders(false), body: form }).then(
            function (r) {
                return r
                    .json()
                    .catch(function () {
                        return {};
                    })
                    .then(function (data) {
                        return r.ok ? data : _reject(r, data);
                    });
            }
        );
    }

    function create() {
        return {
            // 未登录态调用(不带 Authorization)· entry:'dms' 让后端烙 dms 入口 token。
            login: function (username, password, remember) {
                return call('POST', '/api/login', {
                    username: username,
                    password: password,
                    remember: !!remember,
                    entry: 'dms',
                });
            },
            // token 有效性探针(非闸接口):闸关 404 时借它分辨"未登录/失效"与"未受邀"。
            getMe: function () {
                return call('GET', '/api/me');
            },
            // 门禁探针:后端 /api/dms/session 只跑入口守卫、无业务副作用。
            // 200=进壳;401=未登录/失效;404=闸关;403=非 dms 入口(语义由守卫天然给出)。
            probe: function () {
                return call('GET', '/api/dms/session');
            },
            // 推送记录:恒按 mrerp_dms 适配器筛(记录页只呈现身份证 → DMS 的推送)。
            pushLogs: function (limit) {
                return call('GET', '/api/erp/logs?adapter=mrerp_dms&limit=' + (limit || 50));
            },
            // ── 套餐与余额(波1 计费搬家 · 计费端点全用 get_current_user 鉴权,dms token 直调)──
            getSubscription: function () {
                return call('GET', '/api/me/subscription');
            },
            subscribe: function (planCode) {
                return call('POST', '/api/subscription/subscribe', { plan_code: planCode });
            },
            cancelSubscription: function () {
                return call('POST', '/api/subscription/cancel');
            },
            getCredits: function () {
                return call('GET', '/api/me/credits');
            },
            topupRequest: function (amountThb) {
                return call('POST', '/api/credits/topup/request', { amount_thb: amountThb });
            },
            uploadSlip: function (requestId, file, payerName, note) {
                var form = new FormData();
                form.append('file', file, file.name);
                if (payerName) form.append('payer_name', payerName);
                if (note) form.append('note', note);
                return callForm('POST', '/api/credits/topup/upload-slip/' + requestId, form);
            },
            // 记录明细(扣费/充值):tab=usage|topup · period=all|day|month|year · date=YYYY-MM-DD · 分页。
            records: function (p) {
                var q =
                    'tab=' +
                    encodeURIComponent(p.tab) +
                    '&period=' +
                    encodeURIComponent(p.period || 'all') +
                    '&limit=' +
                    (p.limit || 10) +
                    '&offset=' +
                    (p.offset || 0);
                if (p.date) q += '&date=' + encodeURIComponent(p.date);
                return call('GET', '/api/credits/records?' + q);
            },
            // ── 操作员花名册(波3 · DL-8 · owner-only,非 owner 后端 403)──
            listOperators: function () {
                return call('GET', '/api/dms/operators');
            },
            createOperator: function (payload) {
                return call('POST', '/api/dms/operators', payload);
            },
            updateOperator: function (userId, payload) {
                return call('PATCH', '/api/dms/operators/' + encodeURIComponent(userId), payload);
            },
            setOperatorStatus: function (userId, status) {
                return call(
                    'POST',
                    '/api/dms/operators/' + encodeURIComponent(userId) + '/status',
                    {
                        status: status,
                    }
                );
            },
            operatorBindCode: function (userId) {
                return call(
                    'POST',
                    '/api/dms/operators/' + encodeURIComponent(userId) + '/bind-code'
                );
            },
            // 记录页 owner 视角:全租户 mrerp_dms 推送 + 操作员归属列(C6)。
            tenantRecords: function (limit) {
                return call('GET', '/api/dms/records?limit=' + (limit || 100));
            },
        };
    }

    root.DXAPI = { create: create, authHeaders: authHeaders };
})(typeof self !== 'undefined' ? self : this);
