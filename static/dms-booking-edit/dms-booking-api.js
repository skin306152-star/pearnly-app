(function () {
    'use strict';

    var token = localStorage.getItem('mrpilot_token') || '';

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
            var error = new Error((body && body.error && body.error.detail) || 'failed');
            error.status = response.status;
            throw error;
        }
        return body.data;
    }

    async function authenticate() {
        var config = await fetch('/api/line/dms-booking/config').then(function (response) {
            return response.json();
        });
        var liffId = config && config.data && config.data.liff_id;
        if (!liffId || !window.liff) throw new Error('open_in_line');
        await window.liff.init({ liffId: liffId });
        if (!window.liff.isLoggedIn()) {
            window.liff.login();
            return new Promise(function () {});
        }
        var body = await fetch('/api/line/dms-booking/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: window.liff.getIDToken() || '' }),
        }).then(function (response) {
            return response.json();
        });
        if (!body || !body.ok) throw new Error('auth');
        token = body.data.token;
        localStorage.setItem('mrpilot_token', token);
    }

    window.DmsBookingApi = {
        api: api,
        authenticate: authenticate,
        hasDmsToken: function () {
            try {
                var encoded = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
                encoded += '='.repeat((4 - (encoded.length % 4)) % 4);
                var payload = JSON.parse(atob(encoded));
                return payload.entry === 'dms' && Number(payload.exp || 0) * 1000 > Date.now();
            } catch (_) {
                return false;
            }
        },
    };
})();
