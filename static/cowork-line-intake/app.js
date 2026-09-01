(function () {
    'use strict';

    var R = window.lineIntakeBatchReview;
    var I = window.coworkIntakeI18n;
    var F = window.coworkFieldEditor;
    var lang = (localStorage.getItem('pearnly_lang') || 'th').slice(0, 2);
    var state = document.getElementById('state');
    var form = document.getElementById('editor');
    var model = null;
    var draftId = '';
    var busy = false;
    var review = null;

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

    function targets() {
        return model && Array.isArray(model.targets) ? model.targets : [];
    }

    function selection() {
        return model.selection || (model.selection = {});
    }

    function targetId(target) {
        return String(target.endpoint_id || target.id || '');
    }

    function targetKey(target) {
        return (
            targetId(target) +
            ':' +
            String(target.workspace_client_id == null ? 'auto' : target.workspace_client_id)
        );
    }

    function selectedTarget() {
        return targets().find(function (target) {
            return (
                targetId(target) === String(selection().endpoint_id || '') &&
                String(target.workspace_client_id == null ? '' : target.workspace_client_id) ===
                    String(
                        selection().workspace_client_id == null
                            ? ''
                            : selection().workspace_client_id
                    )
            );
        });
    }

    function isBlocked(target) {
        return (
            !target ||
            target.selectable === false ||
            target.configured === false ||
            Boolean(target.block_reason) ||
            (Array.isArray(target.missing) && target.missing.length > 0)
        );
    }

    function targetStatus(target) {
        var checks = target.ready_checks || {};
        var connected = checks.erp_connection;
        if (connected == null) {
            connected = /online|configured/.test(String(target.connection_state || ''));
        }
        var values = [connected ? 'connected' : 'disconnected'];
        if (checks.companion_online != null) {
            values.push(checks.companion_online ? 'online' : 'offline');
        }
        if (checks.profile_matches != null) {
            values.push(checks.profile_matches ? 'matched' : 'unmatched');
        }
        if (checks.local_account_lock === 'waiting_lock') values.push('occupied');
        else if (checks.cloud_in_flight) values.push('inFlight');
        values.push(
            checks.document_preflight == null
                ? 'preflightPending'
                : checks.document_preflight
                  ? 'available'
                  : 'occupied'
        );
        return values
            .map(function (key) {
                return (
                    '<span class="check ' +
                    (/disconnected|offline|unmatched|occupied/.test(key) ? 'bad' : '') +
                    '">' +
                    R.escape(t(key)) +
                    '</span>'
                );
            })
            .join('');
    }

    function targetPanel() {
        var options = targets()
            .map(function (target) {
                var workspace =
                    target.workspace_label ||
                    target.workspace_name ||
                    (target.workspace_client_id == null
                        ? t('autoWorkspace')
                        : t('workspace') + ' #' + target.workspace_client_id);
                return (
                    '<button type="button" class="target-card' +
                    (selectedTarget() === target ? ' active' : '') +
                    (isBlocked(target) ? ' blocked' : '') +
                    '" data-target="' +
                    R.escape(targetKey(target)) +
                    '"' +
                    (isBlocked(target) ? ' aria-disabled="true"' : '') +
                    '><strong>' +
                    R.escape(workspace) +
                    '</strong><span>' +
                    R.escape(
                        target.label ||
                            target.target_label ||
                            target.name ||
                            target.adapter ||
                            t('erp')
                    ) +
                    '</span><div class="checks">' +
                    targetStatus(target) +
                    '</div></button>'
                );
            })
            .join('');
        var target = selectedTarget();
        var adapter = String((target || {}).adapter || selection().adapter || '').toLowerCase();
        var purchase = selection().direction === 'purchase';
        var postingMode =
            adapter === 'express'
                ? '<label class="field"><span>' +
                  R.escape(t('mode')) +
                  '</span><select data-selection="posting_kind"><option value="">—</option><option value="stock"' +
                  (selection().posting_kind === 'stock' ? ' selected' : '') +
                  '>' +
                  R.escape(t('stock')) +
                  '</option><option value="service"' +
                  (selection().posting_kind === 'service' ? ' selected' : '') +
                  '>' +
                  R.escape(t('service')) +
                  '</option></select></label>'
                : '<label class="field"><span>' +
                  R.escape(t('payment')) +
                  '</span><select data-selection="payment"><option value="">—</option>' +
                  (purchase
                      ? ''
                      : '<option value="cash"' +
                        (selection().payment === 'cash' ? ' selected' : '') +
                        '>' +
                        R.escape(t('cash')) +
                        '</option>') +
                  '<option value="credit"' +
                  (selection().payment === 'credit' ? ' selected' : '') +
                  '>' +
                  R.escape(t('credit')) +
                  '</option></select></label>';
        return (
            '<section class="panel"><h2>' +
            R.escape(t('target')) +
            '</h2><div class="target-list">' +
            (options || '<p class="empty">' + R.escape(t('noTarget')) + '</p>') +
            '</div><div class="selection-grid"><label class="field"><span>' +
            R.escape(t('direction')) +
            '</span><select data-selection="direction"><option value="">—</option><option value="purchase"' +
            (selection().direction === 'purchase' ? ' selected' : '') +
            '>' +
            R.escape(t('purchase')) +
            '</option><option value="sales"' +
            (selection().direction === 'sales' ? ' selected' : '') +
            '>' +
            R.escape(t('sales')) +
            '</option></select></label>' +
            postingMode +
            '</div>' +
            (target && isBlocked(target)
                ? '<p class="block-note">' + R.escape(t('blocked')) + '</p>'
                : '') +
            '</section>'
        );
    }

    function chooseTarget(key) {
        var target = targets().find(function (row) {
            return targetKey(row) === key;
        });
        if (!target || isBlocked(target)) return;
        Object.assign(selection(), {
            endpoint_id: target.endpoint_id || target.id,
            workspace_client_id: target.workspace_client_id,
            adapter: target.adapter,
            target_label: target.label || target.target_label || target.name,
            posting_kind: null,
            payment: null,
        });
    }

    function validSelection() {
        var target = selectedTarget();
        var adapter = String((target || {}).adapter || '').toLowerCase();
        var workspaceReady =
            selection().workspace_client_id != null ||
            (target && target.setup_action === 'auto_create_workspace');
        var modeReady =
            adapter === 'express'
                ? Boolean(selection().posting_kind)
                : selection().direction === 'purchase'
                  ? selection().payment === 'credit'
                  : /^(cash|credit)$/.test(selection().payment || '');
        return Boolean(
            target && !isBlocked(target) && workspaceReady && selection().direction && modeReady
        );
    }

    function bindPrefix(root, render) {
        root.querySelectorAll('[data-target]').forEach(function (button) {
            button.onclick = function () {
                chooseTarget(button.dataset.target);
                render();
            };
        });
        root.querySelectorAll('[data-selection]').forEach(function (element) {
            element.onchange = function () {
                selection()[element.dataset.selection] = element.value || null;
                if (element.dataset.selection === 'direction') selection().payment = null;
                render();
            };
        });
    }

    function section(title, body) {
        return '<section class="panel"><h2>' + R.escape(title) + '</h2>' + body + '</section>';
    }

    function renderOriginals(record) {
        var urls = R.previewUrls(record);
        return urls.length
            ? '<div class="review-originals">' +
                  urls
                      .map(function (url) {
                          return (
                              '<div class="review-original" data-review-preview="' +
                              R.escape(url) +
                              '">' +
                              R.escape(t('loadingPreview')) +
                              '</div>'
                          );
                      })
                      .join('') +
                  '</div>'
            : '<p class="empty">—</p>';
    }

    function renderDetail(record, recordIndex) {
        var fields = R.canonicalFields(record);
        return (
            section(t('original'), renderOriginals(record)) +
            section(t('fields'), F.renderFields(fields, recordIndex, lang, I.label)) +
            section(t('items'), F.renderItems(fields, recordIndex, lang, I.label))
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
        return {
            records: records(),
            workspace_client_id: selection().workspace_client_id,
            endpoint_id: selection().endpoint_id,
            direction: selection().direction,
            adapter: selection().adapter,
            target_label: selection().target_label,
            posting_kind: selection().posting_kind,
            payment: selection().payment,
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
        review = R.create({
            root: form,
            records: records,
            direction: function () {
                return selection().direction || 'purchase';
            },
            text: t,
            title: function () {
                return t('title');
            },
            issues: function (record) {
                return R.documentIssues(record, selection().direction, {
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
    window.lineIntakeLiff
        .boot({
            flow: 'cowork-intake',
            configUrl: '/api/cowork-line/intake/liff/config',
            authUrl: '/api/cowork-line/intake/liff/auth',
            tokenKey: 'cowork_line_intake_token',
        })
        .then(function (auth) {
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
