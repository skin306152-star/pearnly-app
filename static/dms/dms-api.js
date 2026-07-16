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
                    if (r.ok) return data;
                    var detail = data && data.detail;
                    var code =
                        (detail && (detail.code || detail)) || (data && data.code) || 'generic';
                    return Promise.reject({ status: r.status, code: String(code), data: data });
                });
        });
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
            // 门禁探针:轻量 DMS 端点(仅府级列表)。401=未登录/失效;404=闸关;403=非 dms 入口。
            probe: function () {
                return call('GET', '/api/dms/geo?level=provinces');
            },
            // 推送记录:恒按 mrerp_dms 适配器筛(记录页只呈现身份证 → DMS 的推送)。
            pushLogs: function (limit) {
                return call('GET', '/api/erp/logs?adapter=mrerp_dms&limit=' + (limit || 50));
            },
        };
    }

    root.DXAPI = { create: create, authHeaders: authHeaders };
})(typeof self !== 'undefined' ? self : this);
