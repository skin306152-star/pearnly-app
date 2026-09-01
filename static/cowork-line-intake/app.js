(function () {
    'use strict';

    var R = window.lineIntakeBatchReview;
    var S = window.lineIntakeSourcePage;
    var I = window.coworkIntakeI18n;
    var F = window.coworkFieldEditor;
    var T = window.lineIntakeTargetSelect;
    var lang = (localStorage.getItem('pearnly_lang') || 'th').slice(0, 2);
    var state = document.getElementById('state');
    var form = document.getElementById('editor');
    var model = null;
    var draftId = '';
    var busy = false;
    var review = null;
    var targetSelect = null;

    function t(key, values) {
        return I.text(lang, key, values);
    }

    function token() {
        return sessionStorage.getItem('cowork_line_intake_token') || '';
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

    function records() {
        return model && Array.isArray(model.records) ? model.records : [];
    }

    function targetPanel() {
        return targetSelect.html();
    }

    function validSelection() {
        return targetSelect.valid();
    }

    function bindPrefix(root, render) {
        targetSelect.bind(root, render);
    }

    function section(title, body) {
        return '<section class="panel"><h2>' + R.escape(title) + '</h2>' + body + '</section>';
    }

    function renderOriginals(record) {
        return S.originalsHtml(record, t);
    }

    function renderDetail(record, recordIndex) {
        var fields = R.canonicalFields(record);
        return (
            section(t('original'), renderOriginals(record)) +
            section(
                t('fields'),
                F.renderFields(fields, recordIndex, lang, I.label, function (key) {
                    return S.fieldPage(record, key);
                })
            ) +
            section(
                t('items'),
                F.renderItems(fields, recordIndex, lang, I.label, function (_key, itemIndex) {
                    return S.fieldPage(record, '', itemIndex);
                })
            )
        );
    }

    function bindDetail(root, _recordIndex, changed) {
        root.querySelectorAll('[data-field]').forEach(function (element) {
            element.oninput = function () {
                F.apply(records(), element);
                changed();
            };
        });
    }

    function payload() {
        var selection = targetSelect.selection();
        return {
            records: records(),
            workspace_client_id: selection.workspace_client_id,
            endpoint_id: selection.endpoint_id,
            direction: selection.direction,
            adapter: selection.adapter,
            target_label: selection.target_label,
            account_root: selection.account_root,
            account_set: selection.account_set,
            posting_kind: selection.posting_kind,
            payment: selection.payment,
        };
    }

    function show(key, kind) {
        state.className = 'state ' + (kind || '');
        state.textContent = t(key);
        state.hidden = false;
    }

    function save() {
        return api('/api/cowork-line/intake/draft/' + encodeURIComponent(draftId), {
            method: 'PUT',
            body: JSON.stringify(payload()),
        }).then(function (updated) {
            model = Object.assign(model, updated);
            return updated;
        });
    }

    function act(action) {
        if (busy) return;
        if (action !== 'discard' && !validSelection()) {
            show('required', 'error');
            return;
        }
        if (action === 'confirm' && !review.canConfirm()) return;
        busy = true;
        review.setBusy(true);
        var base = '/api/cowork-line/intake/draft/' + encodeURIComponent(draftId);
        var request =
            action === 'discard'
                ? api(base + '/discard', { method: 'POST' })
                : save().then(function () {
                      return action === 'confirm'
                          ? api(base + '/confirm', { method: 'POST' })
                          : null;
                  });
        request
            .then(function (result) {
                if (action === 'save') {
                    show('saved');
                    review.render();
                    return;
                }
                if (action === 'discard') {
                    form.hidden = true;
                    show('discarded');
                    return;
                }
                if (!result || result.saved !== true) {
                    show('recoverable', 'error');
                    return;
                }
                form.hidden = true;
                if (result.push_ok !== true) {
                    show('pushFailed', 'error');
                    return;
                }
                var waiting =
                    /pending|queued|retrying/.test(result.status || '') ||
                    (result.results || []).some(function (row) {
                        return /pending|queued|retrying/.test(row.status || '');
                    });
                show(waiting ? 'waiting' : 'confirmed');
            })
            .catch(function (error) {
                var detail = String((error.body || {}).detail || '');
                if (
                    error.status === 401 ||
                    error.status === 403 ||
                    /draft_(expired|forbidden)/.test(detail)
                ) {
                    show('expired', 'error');
                } else {
                    show(error.status === 409 ? 'recoverable' : 'failed', 'error');
                }
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
        });
        review = R.create({
            root: form,
            records: records,
            direction: function () {
                return targetSelect.selection().direction || 'purchase';
            },
            text: t,
            title: function () {
                return t('title');
            },
            issues: function (record) {
                return R.documentIssues(record, targetSelect.selection().direction, {
                    requirePostingKind: false,
                });
            },
            globalReady: validSelection,
            renderPrefix: targetPanel,
            bindPrefix: bindPrefix,
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
    Promise.all([
        window.lineIntakeReviewI18n.load(),
        window.lineIntakeLiff.boot({
            flow: 'cowork-intake',
            configUrl: '/api/cowork-line/intake/liff/config',
            authUrl: '/api/cowork-line/intake/liff/auth',
            tokenKey: 'cowork_line_intake_token',
        }),
    ])
        .then(function (values) {
            var auth = values[1];
            draftId = auth.draftId;
            return api('/api/cowork-line/intake/draft/' + encodeURIComponent(draftId));
        })
        .then(function (value) {
            model = value;
            buildReview();
        })
        .catch(function (error) {
            show(error.status === 401 || error.status === 403 ? 'expired' : 'failed', 'error');
        });
})();
