(function () {
    'use strict';

    var R = window.lineIntakeBatchReview;
    var S = window.lineIntakeSourcePage;
    var I = window.erpLineIntakeI18n;
    var F = window.erpLineFieldRenderer;
    var T = window.lineIntakeTargetSelect;
    var lang = (localStorage.getItem('pearnly_lang') || 'th').slice(0, 2);
    var state = document.getElementById('state');
    var form = document.getElementById('editor');
    var model = null;
    var draftId = '';
    var busy = false;
    var review = null;
    var targetSelect = null;

    var COMMON_ORDER = ['invoice_number', 'date', 'document_type'];
    var PURCHASE_ORDER = [
        'seller_name',
        'seller_tax',
        'seller_branch',
        'seller_addr',
        'seller_address',
        'buyer_name',
        'buyer_tax',
        'buyer_branch',
        'buyer_addr',
        'buyer_address',
    ];
    var SALES_ORDER = [
        'buyer_name',
        'buyer_tax',
        'buyer_branch',
        'buyer_addr',
        'buyer_address',
        'seller_name',
        'seller_tax',
        'seller_branch',
        'seller_addr',
        'seller_address',
    ];
    var AMOUNT_ORDER = ['subtotal', 'vat', 'total_amount', 'notes'];
    var HIDDEN_FIELDS = new Set(['items', 'additional_invoices', 'source_refs']);

    function t(key, values) {
        return I.text(lang, key, values);
    }

    function label(key) {
        return I.label(lang, key);
    }

    function token() {
        return sessionStorage.getItem('erp_line_token') || '';
    }

    function api(path, options) {
        options = options || {};
        options.headers = Object.assign(
            { 'Content-Type': 'application/json' },
            token() ? { Authorization: 'Bearer ' + token() } : {},
            options.headers || {}
        );
        return fetch(path, options).then(window.lineIntakeLiff.responseJson);
    }

    function rows() {
        return model && Array.isArray(model.records) ? model.records : [];
    }

    function direction() {
        return (
            (targetSelect && targetSelect.selection().direction) ||
            (model && (model.direction || model.mode)) ||
            'purchase'
        );
    }

    function expressTarget() {
        return targetSelect && targetSelect.adapter() === 'express';
    }

    function applyPostingDefault(value) {
        if (!/^(stock|service)$/.test(value || '')) return;
        rows().forEach(function (record) {
            fieldsOf(record).items.forEach(function (item) {
                item.posting_kind = value;
            });
        });
    }

    function moveAlias(target, canonical, alias) {
        if (!target[canonical] && target[alias]) target[canonical] = target[alias];
        if (alias !== canonical) delete target[alias];
    }

    function fieldsOf(record) {
        var fields = R.canonicalFields(record);
        moveAlias(fields, 'invoice_number', 'invoice_no');
        moveAlias(fields, 'date', 'invoice_date');
        if (!Array.isArray(fields.items) || !fields.items.length) {
            fields.items = [{ name: '', qty: '', price: '', subtotal: '', posting_kind: '' }];
        }
        fields.items.forEach(function (item) {
            moveAlias(item, 'name', 'description');
            moveAlias(item, 'qty', 'quantity');
            moveAlias(item, 'price', 'unit_price');
            moveAlias(item, 'subtotal', 'amount');
        });
        return fields;
    }

    function section(title, body) {
        return '<section class="section"><h2>' + R.escape(title) + '</h2>' + body + '</section>';
    }

    function preferredKeys(fields) {
        var preferred = COMMON_ORDER.concat(
            direction() === 'sales' ? SALES_ORDER : PURCHASE_ORDER,
            AMOUNT_ORDER
        );
        return preferred
            .filter(function (key) {
                return Object.prototype.hasOwnProperty.call(fields, key);
            })
            .concat(
                Object.keys(fields).filter(function (key) {
                    return !HIDDEN_FIELDS.has(key) && preferred.indexOf(key) < 0;
                })
            );
    }

    function requiredField(key) {
        return direction() === 'sales'
            ? ['invoice_number', 'date'].indexOf(key) >= 0
            : ['seller_name', 'date', 'total_amount'].indexOf(key) >= 0;
    }

    function renderOriginals(record) {
        return S.originalsHtml(record, t);
    }

    function renderDetail(record, recordIndex) {
        var fields = fieldsOf(record);
        var fieldGrid = preferredKeys(fields)
            .map(function (key) {
                return F.render(
                    key,
                    fields[key],
                    requiredField(key),
                    recordIndex + ':field:' + key,
                    label,
                    R.escape,
                    S.fieldPage(record, key)
                );
            })
            .join('');
        var items = fields.items
            .map(function (item, itemIndex) {
                var keys = ['name', 'qty', 'unit', 'price', 'subtotal'].filter(function (key) {
                    return Object.prototype.hasOwnProperty.call(item, key);
                });
                Object.keys(item).forEach(function (key) {
                    if (key !== 'posting_kind' && keys.indexOf(key) < 0) keys.push(key);
                });
                var posting = expressTarget()
                    ? '<div class="field"><label>' +
                      R.escape(t('kind')) +
                      ' *</label><select data-kind="' +
                      recordIndex +
                      ':' +
                      itemIndex +
                      '" data-source-page="' +
                      S.fieldPage(record, '', itemIndex) +
                      '"><option value="">' +
                      R.escape(t('pick')) +
                      '</option><option value="stock"' +
                      (item.posting_kind === 'stock' ? ' selected' : '') +
                      '>' +
                      R.escape(t('stock')) +
                      '</option><option value="service"' +
                      (item.posting_kind === 'service' ? ' selected' : '') +
                      '>' +
                      R.escape(t('service')) +
                      '</option></select></div>'
                    : '';
                return (
                    '<div class="item"><div class="grid">' +
                    keys
                        .map(function (key) {
                            return F.render(
                                key,
                                item[key],
                                ['name', 'qty'].indexOf(key) >= 0,
                                recordIndex + ':item:' + itemIndex + ':' + key,
                                label,
                                R.escape,
                                S.fieldPage(record, key, itemIndex)
                            );
                        })
                        .join('') +
                    posting +
                    '</div></div>'
                );
            })
            .join('');
        return (
            section(t('original'), renderOriginals(record)) +
            section(t('fields'), '<div class="grid">' + fieldGrid + '</div>') +
            section(t('items'), items)
        );
    }

    function applyField(element) {
        var parts = element.dataset.field.split(':');
        var fields = fieldsOf(rows()[Number(parts[0])]);
        var target = fields;
        var key = parts[2];
        if (parts[1] === 'item') {
            target = fields.items[Number(parts[2])];
            key = parts[3];
        }
        var value = element.value;
        if (typeof target[key] === 'boolean') value = value === 'true';
        if (element.tagName === 'TEXTAREA' && target[key] && typeof target[key] === 'object') {
            try {
                value = JSON.parse(value);
            } catch {
                return;
            }
        }
        target[key] = value;
    }

    function bindDetail(root, _recordIndex, changed) {
        root.querySelectorAll('[data-field]').forEach(function (element) {
            element.oninput = function () {
                applyField(element);
                changed();
            };
        });
        root.querySelectorAll('[data-kind]').forEach(function (element) {
            element.onchange = function () {
                var parts = element.dataset.kind.split(':');
                fieldsOf(rows()[Number(parts[0])]).items[Number(parts[1])].posting_kind =
                    element.value;
                changed();
            };
        });
    }

    function show(key, kind) {
        state.className = 'state ' + (kind || '');
        state.textContent = t(key);
        state.hidden = false;
    }

    function save() {
        var selection = targetSelect.selection();
        return api('/api/line/erp/draft/' + encodeURIComponent(draftId), {
            method: 'PUT',
            body: JSON.stringify({
                records: rows(),
                endpoint_id: selection.endpoint_id,
                workspace_client_id: selection.workspace_client_id,
                direction: selection.direction,
                adapter: selection.adapter,
                target_label: selection.target_label,
                account_root: selection.account_root,
                account_set: selection.account_set,
                posting_kind: selection.posting_kind,
                payment: selection.payment,
            }),
        }).then(function (updated) {
            if (updated) model = Object.assign(model, updated);
            return updated;
        });
    }

    function act(action) {
        if (busy || (action === 'confirm' && !review.canConfirm())) return;
        busy = true;
        review.setBusy(true);
        var base = '/api/line/erp/draft/' + encodeURIComponent(draftId);
        var request =
            action === 'discard'
                ? api(base + '/discard', { method: 'POST' })
                : save().then(function () {
                      return action === 'confirm'
                          ? api(base + '/confirm', { method: 'POST' })
                          : null;
                  });
        request
            .then(function () {
                show(
                    action === 'save' ? 'saved' : action === 'confirm' ? 'confirmed' : 'discarded'
                );
                if (action === 'save') review.render();
                else form.hidden = true;
            })
            .catch(function (error) {
                show(error.status === 401 || error.status === 403 ? 'expired' : 'failed', 'error');
            })
            .finally(function () {
                busy = false;
                if (!form.hidden) review.setBusy(false);
            });
    }

    function buildReview() {
        targetSelect = T.create({
            model: function () {
                return model;
            },
            text: t,
            escape: R.escape,
            lockDirection: true,
            onChange: function (field, value) {
                if (field === 'posting_kind') applyPostingDefault(value);
            },
        });
        review = R.create({
            root: form,
            records: rows,
            direction: direction,
            text: t,
            title: function () {
                return t(
                    direction() === 'sales'
                        ? 'salesTitle'
                        : direction() === 'purchase'
                          ? 'purchaseTitle'
                          : 'title'
                );
            },
            issues: function (record) {
                fieldsOf(record);
                return R.documentIssues(record, direction(), {
                    requirePostingKind: expressTarget(),
                });
            },
            globalReady: function () {
                return targetSelect.valid();
            },
            renderPrefix: function () {
                return targetSelect.html();
            },
            bindPrefix: function (root, render) {
                targetSelect.bind(root, render);
            },
            renderDetail: renderDetail,
            bindDetail: bindDetail,
            onAction: act,
            authHeaders: function () {
                return { Authorization: 'Bearer ' + token() };
            },
        });
        review.render();
        state.hidden = true;
    }

    document.getElementById('lang').value = lang;
    document.getElementById('lang').onchange = function (event) {
        lang = event.target.value;
        localStorage.setItem('pearnly_lang', lang);
        if (review) review.render();
        else show('loading');
    };
    show('loading');
    window.lineIntakeLiff
        .boot({
            flow: 'erp-intake',
            configUrl: '/api/line/erp/liff/config',
            authUrl: '/api/line/erp/liff/auth',
            tokenKey: 'erp_line_token',
        })
        .then(function (auth) {
            draftId = auth.draftId;
            return api('/api/line/erp/draft/' + encodeURIComponent(draftId));
        })
        .then(function (value) {
            model = value;
            buildReview();
        })
        .catch(function (error) {
            show(error.status === 401 || error.status === 403 ? 'expired' : 'failed', 'error');
        });
})();
