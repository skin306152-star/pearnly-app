(function () {
    'use strict';

    // This page belongs to the current LINE binding, never the shared web login.
    var token = '';
    var renewalKey = 'dms-line-login-renewed';

    // LINE opens the configured endpoint and carries the original query inside liff.state;
    // outside LINE the same query sits on location.search. The OA key must survive both.
    function param(name) {
        var sp = new URLSearchParams(window.location.search);
        var state = sp.get('liff.state');
        if (state) {
            var queryStart = state.indexOf('?');
            state = queryStart >= 0 ? state.slice(queryStart + 1) : state;
            return new URLSearchParams(state).get(name) || '';
        }
        return sp.get(name) || '';
    }

    function entryChannel() {
        return (param('channel') || '').trim();
    }

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
        var channel = entryChannel();
        var configUrl = '/api/line/dms-booking/config';
        if (channel) configUrl += '?channel=' + encodeURIComponent(channel);
        var config = await fetch(configUrl).then(function (response) {
            return response.json();
        });
        var liffId = config && config.data && config.data.liff_id;
        var channelKey = (config && config.data && config.data.channel_key) || channel;
        if (!liffId || !window.liff) {
            var unavailable = new Error('dms_booking.liff_unavailable');
            unavailable.code = 'dms_booking.liff_unavailable';
            unavailable.status = 503;
            throw unavailable;
        }
        await window.liff.init({ liffId: liffId });
        if (forceLogin) return renewLineLogin();
        if (!window.liff.isLoggedIn()) {
            window.liff.login({ redirectUri: window.location.href });
            return new Promise(function () {});
        }
        var response = await fetch('/api/line/dms-booking/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id_token: window.liff.getIDToken() || '',
                channel: channelKey || '',
            }),
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
