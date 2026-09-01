(function () {
    'use strict';

    function unwrap(value) {
        return value && value.data !== undefined ? value.data : value;
    }

    function responseJson(response) {
        return response
            .json()
            .catch(function () {
                return {};
            })
            .then(function (body) {
                if (!response.ok) {
                    var error = new Error(String(response.status));
                    error.status = response.status;
                    error.body = body;
                    throw error;
                }
                return unwrap(body);
            });
    }

    function stateParams(raw) {
        if (!raw) return new URLSearchParams();
        try {
            var parsed = new URL(raw, location.origin);
            return parsed.searchParams.size
                ? parsed.searchParams
                : new URLSearchParams(parsed.pathname.replace(/^\/?\?/, ''));
        } catch {
            return new URLSearchParams(String(raw).replace(/^\?/, ''));
        }
    }

    function draftFromLocation(expectedFlow) {
        var direct = new URLSearchParams(location.search);
        var directFlow = direct.get('flow') || '';
        var directDraft = direct.get('draft') || '';
        if (directDraft && (!directFlow || directFlow === expectedFlow)) return directDraft;
        var state = stateParams(direct.get('liff.state'));
        var stateFlow = state.get('flow') || '';
        var stateDraft = state.get('draft') || '';
        return stateDraft && (!stateFlow || stateFlow === expectedFlow) ? stateDraft : '';
    }

    function boot(options) {
        return fetch(options.configUrl)
            .then(responseJson)
            .then(function (config) {
                if (!config.liff_id || !window.liff) throw Error('liff_config_missing');
                return window.liff.init({ liffId: config.liff_id });
            })
            .then(function () {
                if (!window.liff.isLoggedIn()) {
                    window.liff.login();
                    throw Error('liff_login_required');
                }
                var draftId = draftFromLocation(options.flow);
                var idToken = window.liff.getIDToken && window.liff.getIDToken();
                if (!draftId) throw Error('liff_draft_missing');
                if (!idToken) throw Error('liff_token_missing');
                return fetch(options.authUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_token: idToken, draft_id: draftId }),
                })
                    .then(responseJson)
                    .then(function (auth) {
                        if (!auth.token) throw Error('liff_scoped_token_missing');
                        sessionStorage.setItem(options.tokenKey, auth.token);
                        return { draftId: draftId, token: auth.token };
                    });
            });
    }

    window.lineIntakeLiff = {
        boot: boot,
        draftFromLocation: draftFromLocation,
        responseJson: responseJson,
        unwrap: unwrap,
    };
})();
