(function () {
    'use strict';

    // This page belongs to the current LINE binding, never the shared web login.
    var token = '';
    var renewalKey = 'dms-line-login-renewed';

    function responseError(response, body) {
        var detail = body && body.detail;
        var code =
            (body && body.error && body.error.code) || (typeof detail === 'string' ? detail : '');
        var error = new Error(code || 'failed');
        error.status = response.status;
        error.code = code;
        return error;
    }

    function renewLineLogin() {
        token = '';
        try {
            sessionStorage.setItem(renewalKey, String(Date.now()));
        } catch (_) {
            /* No automatic retry without storage. */
        }
        if (window.liff.isInClient()) {
            window.location.reload();
        } else {
            window.liff.logout();
            window.liff.login({ redirectUri: window.location.href });
        }
        return new Promise(function () {});
    }

    function mayRenewAutomatically() {
        try {
            var last = Number(sessionStorage.getItem(renewalKey) || '0');
            sessionStorage.setItem(renewalKey, String(last));
            return Date.now() - last > 300000;
        } catch (_) {
            return false;
        }
    }

    async function api(path, opts) {
        opts = opts || {};
        opts.headers = Object.assign(
            { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
            opts.headers || {}
        );
        var response = await fetch(path, opts);
        var body = await response.json().catch(function () {
            return null;
        });
        if (!response.ok || !body || !body.ok) {
            throw responseError(response, body);
        }
        return body.data;
    }

    async function authenticate(forceLogin) {
        token = '';
        var config = await fetch('/api/line/dms-booking/config').then(function (response) {
            return response.json();
        });
        var liffId = config && config.data && config.data.liff_id;
        if (!liffId || !window.liff) throw new Error('open_in_line');
        await window.liff.init({ liffId: liffId });
        if (forceLogin) return renewLineLogin();
        if (!window.liff.isLoggedIn()) {
            window.liff.login({ redirectUri: window.location.href });
            return new Promise(function () {});
        }
        var response = await fetch('/api/line/dms-booking/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: window.liff.getIDToken() || '' }),
        });
        var body = await response.json().catch(function () {
            return null;
        });
        if (!response.ok || !body || !body.ok) {
            var error = responseError(response, body);
            if (
                error.code === 'dms_booking.line_auth_required' &&
                !window.liff.isInClient() &&
                mayRenewAutomatically()
            ) {
                return renewLineLogin();
            }
            throw error;
        }
        try {
            sessionStorage.removeItem(renewalKey);
        } catch (_) {
            /* Login succeeded. */
        }
        token = body.data.token;
    }

    window.DmsBookingApi = {
        api: api,
        authenticate: authenticate,
    };
})();
