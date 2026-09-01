(function () {
    'use strict';

    var TEXT = window.DMS_BOOKING_TEXT;
    var locale =
        localStorage.getItem('pearnly_lang') ||
        (/^zh/.test(navigator.language)
            ? 'zh'
            : /^ja/.test(navigator.language)
              ? 'ja'
              : /^en/.test(navigator.language)
                ? 'en'
                : 'th');
    var gateway = window.DmsBookingApi;
    var model = null;
    var masters = null;
    var form = document.getElementById('editor');
    var result = document.getElementById('result');
    var nonce = query('draft');
    var ERROR_KEYS = window.DMS_BOOKING_ERROR_KEYS;
    var portalMode = query('portal') === 'dms';
    var credentialsMode = query('credentials') === 'dms';
    if (portalMode) locale = 'th';

    function query(name) {
        var sp = new URLSearchParams(location.search);
        var state = sp.get('liff.state');
        if (state) {
            var queryStart = state.indexOf('?');
            state = queryStart >= 0 ? state.slice(queryStart + 1) : state;
            return new URLSearchParams(state).get(name) || '';
        }
        return sp.get(name) || '';
    }
    function t(key) {
        return (TEXT[locale] && TEXT[locale][key]) || TEXT.en[key] || key;
    }
    function closeAndroidLauncherAfterHandoff() {
        if (!window.liff || !window.liff.closeWindow) return;
        document.addEventListener(
            'visibilitychange',
            function () {
                try {
                    window.liff.closeWindow();
                } catch {
                    // The external browser already owns the flow; launcher cleanup is best effort.
                }
            },
            { once: true }
        );
    }
    function esc(v) {
        var d = document.createElement('div');
        d.textContent = v == null ? '' : String(v);
        return d.innerHTML;
    }
    function field(name, label, value, cls, type) {
        return (
            '<div class="field ' +
            (cls || '') +
            '"><label for="' +
            name +
            '">' +
            t(label) +
            '</label><input id="' +
            name +
            '" name="' +
            name +
            '" type="' +
            (type || 'text') +
            '" value="' +
            esc(value) +
            '"></div>'
        );
    }
    function options(rows, selected) {
        return (rows || [])
            .map(function (o) {
                return (
                    '<option value="' +
                    esc(o.id) +
                    '"' +
                    (String(o.id) === String(selected) ? ' selected' : '') +
                    '>' +
                    esc(o.label) +
                    '</option>'
                );
            })
            .join('');
    }
    function select(name, label, rows, selected, cls) {
        return (
            '<div class="field ' +
            (cls || '') +
            '"><label for="' +
            name +
            '">' +
            t(label) +
            '</label><select id="' +
            name +
            '" name="' +
            name +
            '">' +
            options(rows, selected) +
            '</select></div>'
        );
    }
    function section(title, body) {
        return '<section class="section"><h2>' + t(title) + '</h2>' + body + '</section>';
    }
    function channelOptions(selected) {
        return ['cash', 'transfer', 'cheque', 'cashier_cheque', 'card', 'other']
            .map(function (c) {
                return (
                    '<option value="' +
                    c +
                    '"' +
                    (c === selected ? ' selected' : '') +
                    '>' +
                    t(c) +
                    '</option>'
                );
            })
            .join('');
    }
    function paymentField(cls, label, value, wide) {
        return (
            '<div class="field ' +
            (wide ? 'wide' : '') +
            '"><label>' +
            t(label) +
            '</label><input class="' +
            cls +
            '" value="' +
            esc(value || '') +
            '"></div>'
        );
    }
    function legacySource(x) {
        if (x.src_bank_name || x.src_account_no) return x;
        var parts = String(x.src || '')
            .trim()
            .split(/\s+/);
        if (parts.length > 1) {
            x.src_account_no = parts.pop();
            x.src_bank_name = parts.join(' ');
        } else if (/\d/.test(parts[0] || '')) {
            x.src_account_no = parts[0];
        } else {
            x.src_bank_name = parts[0] || '';
        }
        return x;
    }
    function paymentRow(p) {
        p = p || { channel: 'cash', amount: '', extra: {} };
        var x = p.extra || {};
        if (p.channel === 'transfer') x = legacySource(x);
        var extra =
            p.channel === 'transfer'
                ? '<div class="extra grid">' +
                  paymentField('src-bank', 'sourceBank', x.src_bank_name) +
                  paymentField('src-account', 'sourceAccount', x.src_account_no) +
                  paymentField('src-name', 'sourceAccountName', x.src_account_name) +
                  paymentField('src-branch', 'sourceBranch', x.src_branch_name) +
                  paymentField('src-time', 'transferTime', x.src_time) +
                  '<div class="field wide"><label>' +
                  t('destination') +
                  '</label><select class="dst">' +
                  options(masters.company_banks, x.dst_id) +
                  '</select></div></div>'
                : p.channel === 'cash'
                  ? '<div class="extra"></div>'
                  : p.channel === 'cheque'
                    ? '<div class="extra grid">' +
                      paymentField('cheque-no', 'chequeNo', x.cheque_no || x.ref) +
                      paymentField('bank-name', 'bankName', x.bank_name) +
                      paymentField('cheque-book-no', 'chequeBookNo', x.cheque_book_no) +
                      '</div>'
                    : p.channel === 'cashier_cheque'
                      ? '<div class="extra grid">' +
                        paymentField('cashier-no', 'cashierNo', x.cashier_no || x.ref) +
                        paymentField('bank-name', 'bankName', x.bank_name) +
                        paymentField('cashier-book-no', 'cashierBookNo', x.cashier_book_no) +
                        '</div>'
                      : p.channel === 'card'
                        ? '<div class="extra grid">' +
                          paymentField('bank-name', 'bankName', x.bank_name) +
                          paymentField('card-type', 'cardType', x.card_type || x.ref) +
                          '</div>'
                        : '<div class="field extra"><label>' +
                          t('detail') +
                          '</label><input class="detail" value="' +
                          esc(x.detail || '') +
                          '"></div>';
        return (
            '<div class="payment"><div class="field channel"><label>' +
            t('channel') +
            '</label><select class="pay-channel">' +
            channelOptions(p.channel) +
            '</select></div><div class="field"><label>' +
            t('amount') +
            '</label><input class="amount" inputmode="decimal" value="' +
            esc(p.amount || '') +
            '"></div>' +
            extra +
            '<button class="pu-btn remove" type="button" aria-label="' +
            t('remove') +
            '">×</button></div>'
        );
    }
    function renderPayments(rows) {
        document.getElementById('payment-list').innerHTML = (rows || []).map(paymentRow).join('');
        wirePayments();
        syncChannelOptions();
        total();
    }
    function syncChannelOptions() {
        var selects = Array.from(document.querySelectorAll('.pay-channel'));
        var add = document.getElementById('add-payment');
        if (add) add.disabled = selects.length >= 6;
        selects.forEach(function (selectEl) {
            var usedElsewhere = new Set(
                selects
                    .filter(function (other) {
                        return other !== selectEl;
                    })
                    .map(function (other) {
                        return other.value;
                    })
            );
            Array.from(selectEl.options).forEach(function (option) {
                option.disabled = usedElsewhere.has(option.value);
            });
        });
    }
    function nextChannel() {
        var used = new Set(
            Array.from(document.querySelectorAll('.pay-channel')).map(function (el) {
                return el.value;
            })
        );
        return ['cash', 'transfer', 'cheque', 'cashier_cheque', 'card', 'other'].find(
            function (channel) {
                return !used.has(channel);
            }
        );
    }
    function wirePayments() {
        document.querySelectorAll('.payment').forEach(function (row) {
            row.querySelector('.remove').onclick = function () {
                row.remove();
                syncChannelOptions();
                total();
            };
            row.querySelector('.amount').oninput = total;
            row.querySelector('.pay-channel').onchange = function () {
                var old = {
                    channel: this.value,
                    amount: row.querySelector('.amount').value,
                    extra: {},
                };
                row.outerHTML = paymentRow(old);
                wirePayments();
                syncChannelOptions();
                total();
            };
        });
    }
    function total() {
        var n = 0;
        document.querySelectorAll('.amount').forEach(function (el) {
            n += Number(String(el.value).replace(/,/g, '')) || 0;
        });
        var el = document.getElementById('total');
        if (el)
            el.value = n.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            });
    }
    async function load() {
        if (credentialsMode) {
            return window.DmsCredentials.mount({ gateway: gateway, locale: locale, close: close });
        }
        if (portalMode) {
            try {
                if (!gateway.hasDmsToken()) await gateway.authenticate();
                var portal = await gateway.api('/api/line/dms-portal/ticket', {
                    method: 'POST',
                    body: '{}',
                });
                if (!portal || !portal.url) throw new Error('portal_unavailable');
                var portalUrl = new URL(portal.url, location.origin).toString();
                if (
                    window.liff &&
                    window.liff.isInClient &&
                    window.liff.isInClient() &&
                    window.liff.openWindow
                ) {
                    var os = typeof window.liff.getOS === 'function' ? window.liff.getOS() : '';
                    if (os === 'android') closeAndroidLauncherAfterHandoff();
                    window.liff.openWindow({ url: portalUrl, external: true });
                    if (os === 'ios' && window.liff.closeWindow) window.liff.closeWindow();
                } else {
                    location.replace(portalUrl);
                }
            } catch (e) {
                return showError('failed');
            }
            return;
        }
        if (!nonce) return showError('expired');
        try {
            if (!gateway.hasDmsToken()) await gateway.authenticate();
            model = await gateway.api(
                '/api/line/dms-booking/draft?nonce=' + encodeURIComponent(nonce)
            );
        } catch (e) {
            if (e.status === 401) {
                try {
                    await gateway.authenticate();
                    model = await gateway.api(
                        '/api/line/dms-booking/draft?nonce=' + encodeURIComponent(nonce)
                    );
                } catch (x) {
                    return showError(x.status === 409 ? 'expired' : 'failed');
                }
            } else {
                return showError(e.status === 409 ? 'expired' : 'failed');
            }
        }
        masters = model.masters;
        render();
        await hydrateGeo();
    }
    function render() {
        var c = model.form.customer,
            a = model.form.answers || {},
            f = model.form.files || {},
            adv = model.form.advisor || {};
        form.innerHTML =
            '<div class="intro"><h1>' +
            t('title') +
            '</h1><p>' +
            t('sub') +
            '</p></div>' +
            section(
                'customer',
                '<div class="grid">' +
                    select('prefix_id', 'prefix', masters.prefixes, c.prefix_id) +
                    field('name', 'name', c.name) +
                    field('people_id', 'confirmId', c.people_id) +
                    field('birthday_be', 'birth', c.birthday_be) +
                    field('phone', 'phone', c.phone) +
                    field('house_no', 'house', c.house_no) +
                    field('building', 'building', c.building) +
                    field('floor', 'floor', c.floor) +
                    field('room', 'room', c.room) +
                    field('village', 'village', c.village) +
                    field('moo', 'moo', c.moo) +
                    field('soi', 'soi', c.soi) +
                    field('road', 'road', c.road) +
                    select('province_id', 'province', [], c.province_id) +
                    select('district_id', 'district', [], c.district_id) +
                    select('subdistrict_id', 'subdistrict', [], c.subdistrict_id) +
                    select('zipcode_id', 'postcode', [], c.zipcode_id) +
                    '</div><p class="hint">' +
                    t('idWarn') +
                    '</p>'
            ) +
            section(
                'booking',
                '<div class="grid"><div class="field wide"><label>' +
                    t('advisor') +
                    '</label><input readonly value="' +
                    esc(adv.name || '') +
                    '"></div>' +
                    select('place_id', 'place', masters.places, (a.place || {}).id) +
                    select('car_id', 'car', masters.cars, (a.car || {}).id) +
                    select('paint_id', 'paint', masters.paints, (a.paint || {}).id) +
                    field('delivery_date_be', 'delivery', a.delivery_date_be) +
                    select('term_id', 'term', masters.terms, (a.term || {}).id) +
                    select('regis_id', 'regis', masters.regis, (a.regis || {}).id) +
                    field('regis_name', 'regisName', a.regis_name, 'wide') +
                    '</div>'
            ) +
            section(
                'payment',
                '<div id="payment-list"></div><button id="add-payment" class="pu-btn add" type="button">' +
                    t('addPayment') +
                    '</button><div class="field wide"><label>' +
                    t('total') +
                    '</label><input id="total" readonly></div>'
            ) +
            section(
                'files',
                '<p class="hint">' +
                    t('fileHint') +
                    '</p><div class="file-row"><span>' +
                    t('idCard') +
                    '</span><label><input id="keep-id" class="switch" type="checkbox" ' +
                    (f.id_card ? 'checked' : 'disabled') +
                    '> ' +
                    t('attached') +
                    '</label></div><div class="file-row"><span>' +
                    t('slip') +
                    '</span><label><input id="keep-slip" class="switch" type="checkbox" ' +
                    (f.slip ? 'checked' : 'disabled') +
                    '> ' +
                    t('attached') +
                    '</label></div>'
            ) +
            '<p id="form-error" class="error" role="alert"></p><div class="sticky-actions"><button id="cancel" class="pu-btn secondary" type="button">' +
            t('cancel') +
            '</button><button id="save" class="pu-btn primary" type="submit" disabled>' +
            t('save') +
            '</button></div>';
        document.getElementById('loading').hidden = true;
        form.hidden = false;
        renderPayments(model.form.payments);
        document.getElementById('add-payment').onclick = function () {
            var channel = nextChannel();
            if (!channel) return;
            var list = document.getElementById('payment-list');
            list.insertAdjacentHTML(
                'beforeend',
                paymentRow({ channel: channel, amount: '', extra: {} })
            );
            wirePayments();
            syncChannelOptions();
            total();
        };
        document.getElementById('car_id').onchange = loadPaints;
        document.getElementById('province_id').onchange = function () {
            cascade('districts', this.value, 'district_id', true);
        };
        document.getElementById('district_id').onchange = function () {
            cascade('subdistricts', this.value, 'subdistrict_id', true);
        };
        document.getElementById('subdistrict_id').onchange = function () {
            cascade('zipcodes', this.value, 'zipcode_id', true);
        };
        document.getElementById('cancel').onclick = close;
        form.onsubmit = save;
    }
    async function geo(level, parent) {
        return gateway.api(
            '/api/line/dms-booking/geo?nonce=' +
                encodeURIComponent(nonce) +
                '&level=' +
                level +
                '&parent_id=' +
                encodeURIComponent(parent || '')
        );
    }
    function setOptions(id, rows, selected) {
        var el = document.getElementById(id);
        el.innerHTML = options(rows, selected);
        if (selected) el.value = selected;
    }
    async function hydrateGeo() {
        var c = model.form.customer;
        try {
            setOptions('province_id', await geo('provinces', ''), c.province_id);
            setOptions('district_id', await geo('districts', c.province_id), c.district_id);
            setOptions(
                'subdistrict_id',
                await geo('subdistricts', c.district_id),
                c.subdistrict_id
            );
            setOptions('zipcode_id', await geo('zipcodes', c.subdistrict_id), c.zipcode_id);
            document.getElementById('save').disabled = false;
        } catch (e) {
            showFormError();
        }
    }
    async function cascade(level, parent, target, downstream) {
        try {
            var rows = await geo(level, parent);
            setOptions(target, rows, '');
            if (downstream) {
                if (target === 'district_id') {
                    setOptions('subdistrict_id', [], '');
                    setOptions('zipcode_id', [], '');
                }
                if (target === 'subdistrict_id') setOptions('zipcode_id', [], '');
            }
        } catch (e) {
            showFormError();
        }
    }
    async function loadPaints() {
        try {
            masters.paints = await gateway.api(
                '/api/line/dms-booking/paints?nonce=' +
                    encodeURIComponent(nonce) +
                    '&car_id=' +
                    encodeURIComponent(this.value)
            );
            setOptions('paint_id', masters.paints, '');
        } catch (e) {
            showFormError();
        }
    }
    var val = (id, fallback) => document.getElementById(id).value.trim() || fallback || '';
    function selectedLabel(id) {
        var el = document.getElementById(id);
        return el.selectedOptions[0] ? el.selectedOptions[0].textContent : '';
    }
    function collectPayments() {
        return Array.from(document.querySelectorAll('.payment')).map(function (row) {
            var ch = row.querySelector('.pay-channel').value,
                x = {};
            if (ch === 'transfer') {
                x.src_bank_name = row.querySelector('.src-bank').value.trim();
                x.src_account_no = row.querySelector('.src-account').value.trim();
                x.src_account_name = row.querySelector('.src-name').value.trim();
                x.src_branch_name = row.querySelector('.src-branch').value.trim();
                x.src_time = row.querySelector('.src-time').value.trim();
                x.dst_id = row.querySelector('.dst').value;
            } else if (ch === 'cheque') {
                x.cheque_no = row.querySelector('.cheque-no').value.trim();
                x.bank_name = row.querySelector('.bank-name').value.trim();
                x.cheque_book_no = row.querySelector('.cheque-book-no').value.trim();
            } else if (ch === 'cashier_cheque') {
                x.cashier_no = row.querySelector('.cashier-no').value.trim();
                x.bank_name = row.querySelector('.bank-name').value.trim();
                x.cashier_book_no = row.querySelector('.cashier-book-no').value.trim();
            } else if (ch === 'card') {
                x.bank_name = row.querySelector('.bank-name').value.trim();
                x.card_type = row.querySelector('.card-type').value.trim();
            } else if (ch === 'other') {
                x.detail = row.querySelector('.detail').value.trim();
            }
            return { channel: ch, amount: row.querySelector('.amount').value, extra: x };
        });
    }
    function payload() {
        var names = [
                'people_id',
                'prefix_id',
                'name',
                'birthday_be',
                'phone',
                'house_no',
                'building',
                'floor',
                'room',
                'village',
                'moo',
                'soi',
                'road',
                'province_id',
                'district_id',
                'subdistrict_id',
                'zipcode_id',
            ],
            customer = {};
        names.forEach(function (n) {
            customer[n] = val(n, window.DMS_BOOKING_GEO.includes(n) ? model.form.customer[n] : '');
        });
        customer.province_name = selectedLabel('province_id');
        customer.district_name = selectedLabel('district_id');
        customer.subdistrict_name = selectedLabel('subdistrict_id');
        customer.zipcode = selectedLabel('zipcode_id');
        return {
            customer: customer,
            answers: {
                place_id: val('place_id'),
                car_id: val('car_id'),
                paint_id: val('paint_id'),
                delivery_date_be: val('delivery_date_be'),
                term_id: val('term_id'),
                regis_id: val('regis_id'),
                regis_name: val('regis_name'),
            },
            payments: collectPayments(),
            keep_files: {
                id_card: document.getElementById('keep-id').checked,
                slip: document.getElementById('keep-slip').checked,
            },
        };
    }
    async function save(ev) {
        ev.preventDefault();
        var btn = document.getElementById('save');
        btn.disabled = true;
        document.getElementById('form-error').textContent = '';
        try {
            await gateway.api('/api/line/dms-booking/draft', {
                method: 'POST',
                body: JSON.stringify({ nonce: nonce, form: payload() }),
            });
            form.hidden = true;
            result.hidden = false;
            result.innerHTML =
                '<h1>' +
                t('saved') +
                '</h1><button class="pu-btn primary" type="button" id="done">' +
                t('cancel') +
                '</button>';
            document.getElementById('done').onclick = close;
            setTimeout(close, 900);
        } catch (e) {
            btn.disabled = false;
            var el = document.getElementById('form-error');
            el.textContent = t(e.status === 409 ? 'expired' : ERROR_KEYS[e.code] || 'failed');
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    function close() {
        if (window.liff && window.liff.isInClient && window.liff.isInClient())
            window.liff.closeWindow();
        else history.back();
    }
    function showFormError() {
        var el = document.getElementById('form-error');
        if (el) el.textContent = t('failed');
    }
    function showError(key) {
        document.getElementById('loading').hidden = true;
        result.hidden = false;
        result.innerHTML = '<h1>' + t(key) + '</h1>';
    }
    function applyLanguage() {
        document.documentElement.lang = locale;
        if (credentialsMode) {
            window.DmsCredentials.setLocale(locale);
            return;
        }
        document.querySelectorAll('[data-t]').forEach(function (el) {
            el.textContent = t(el.dataset.t);
        });
        if (model) {
            var current = payload();
            model.form = window.DmsBookingLanguage.snapshot(model.form, current);
            render();
            hydrateGeo();
        }
    }
    var language = document.getElementById('language');
    if (portalMode) language.hidden = true;
    language.value = locale;
    language.onchange = function () {
        locale = this.value;
        localStorage.setItem('pearnly_lang', locale);
        applyLanguage();
    };
    applyLanguage();
    load();
})();
