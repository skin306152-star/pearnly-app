(function () {
    'use strict';
    var I = window.coworkIntakeI18n;
    var F = window.coworkFieldEditor;
    var lang = (localStorage.getItem('pearnly_lang') || 'th').slice(0, 2);
    function draftFromLocation() {
        var query = new URLSearchParams(location.search);
        var direct = query.get('draft');
        if (direct) return direct;
        var state = query.get('liff.state');
        if (state) {
            var stateUrl = new URL(state, location.origin);
            var fromState = stateUrl.searchParams.get('draft');
            if (fromState) return fromState;
            var stateMatch = stateUrl.pathname.match(/\/liff\/cowork-intake\/([^/?#]+)/);
            if (stateMatch && stateMatch[1]) return stateMatch[1];
        }
        var match = location.pathname.match(/\/liff\/cowork-intake\/([^/?#]+)/);
        return match && match[1] ? match[1] : '';
    }
    var draftId = draftFromLocation();
    var state = document.getElementById('state');
    var form = document.getElementById('editor');
    var model = null;
    var busy = false;
    var stateKey = 'loading';
    var stateKind = '';

    function t(key) {
        return I.text(lang, key);
    }
    function data(value) {
        return value && value.data !== undefined ? value.data : value;
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
        return fetch(path, options).then(function (response) {
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
                    return data(body);
                });
        });
    }
    function targets() {
        return Array.isArray(model.targets) ? model.targets : [];
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
        if (connected == null)
            connected = /online|configured/.test(String(target.connection_state || ''));
        var values = [connected ? 'connected' : 'disconnected'];
        if (checks.companion_online != null)
            values.push(checks.companion_online ? 'online' : 'offline');
        if (checks.profile_matches != null)
            values.push(checks.profile_matches ? 'matched' : 'unmatched');
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
                    F.esc(t(key)) +
                    '</span>'
                );
            })
            .join('');
    }
    function targetPanel() {
        var options = targets()
            .map(function (target) {
                var key = targetKey(target),
                    active = selectedTarget() === target;
                var workspace =
                    target.workspace_label ||
                    target.workspace_name ||
                    (target.workspace_client_id == null
                        ? t('autoWorkspace')
                        : t('workspace') + ' #' + target.workspace_client_id);
                return (
                    '<button type="button" class="target-card' +
                    (active ? ' active' : '') +
                    (isBlocked(target) ? ' blocked' : '') +
                    '" data-target="' +
                    F.esc(key) +
                    '"' +
                    (isBlocked(target) ? ' aria-disabled="true"' : '') +
                    '><strong>' +
                    F.esc(workspace) +
                    '</strong><span>' +
                    F.esc(
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
        var mode =
            adapter === 'express'
                ? '<label class="field"><span>' +
                  F.esc(t('mode')) +
                  '</span><select data-selection="posting_kind"><option value="">—</option><option value="stock"' +
                  (selection().posting_kind === 'stock' ? ' selected' : '') +
                  '>' +
                  F.esc(t('stock')) +
                  '</option><option value="service"' +
                  (selection().posting_kind === 'service' ? ' selected' : '') +
                  '>' +
                  F.esc(t('service')) +
                  '</option></select></label>'
                : '<label class="field"><span>' +
                  F.esc(t('payment')) +
                  '</span><select data-selection="payment"><option value="">—</option>' +
                  (purchase
                      ? ''
                      : '<option value="cash"' +
                        (selection().payment === 'cash' ? ' selected' : '') +
                        '>' +
                        F.esc(t('cash')) +
                        '</option>') +
                  '<option value="credit"' +
                  (selection().payment === 'credit' ? ' selected' : '') +
                  '>' +
                  F.esc(t('credit')) +
                  '</option></select></label>';
        return (
            '<section class="panel"><h2>' +
            F.esc(t('target')) +
            '</h2><div class="target-list">' +
            (options || '<p class="empty">' + F.esc(t('noTarget')) + '</p>') +
            '</div><div class="selection-grid"><label class="field"><span>' +
            F.esc(t('direction')) +
            '</span><select data-selection="direction"><option value="">—</option><option value="purchase"' +
            (selection().direction === 'purchase' ? ' selected' : '') +
            '>' +
            F.esc(t('purchase')) +
            '</option><option value="sales"' +
            (selection().direction === 'sales' ? ' selected' : '') +
            '>' +
            F.esc(t('sales')) +
            '</option></select></label>' +
            mode +
            '</div>' +
            (target && isBlocked(target)
                ? '<p class="block-note">' + F.esc(t('blocked')) + '</p>'
                : '') +
            '</section>'
        );
    }
    function previews(record) {
        var urls = record.preview_urls || (record.preview_url ? [record.preview_url] : []);
        return (
            urls
                .map(function (url) {
                    return (
                        '<div class="preview" data-preview="' +
                        F.esc(url) +
                        '">' +
                        F.esc(t('loading')) +
                        '</div>'
                    );
                })
                .join('') || '<div class="empty">—</div>'
        );
    }
    function render() {
        var records = Array.isArray(model.records) ? model.records : [];
        form.innerHTML =
            '<h1>' +
            F.esc(t('title')) +
            '</h1>' +
            targetPanel() +
            records
                .map(function (record, index) {
                    var fields = record.pages?.[0]?.fields || {};
                    return (
                        '<article class="record"><section class="panel"><h2>' +
                        F.esc(t('original')) +
                        '</h2>' +
                        previews(record) +
                        '</section><section class="panel"><h2>' +
                        F.esc(t('fields')) +
                        '</h2>' +
                        F.renderFields(fields, index, lang, I.label) +
                        '</section><section class="panel"><h2>' +
                        F.esc(t('items')) +
                        '</h2>' +
                        F.renderItems(fields, index, lang, I.label) +
                        '</section></article>'
                    );
                })
                .join('') +
            '<div class="actions"><button class="pu-btn pu-btn--secondary" type="button" data-action="save">' +
            F.esc(t('save')) +
            '</button><button class="pu-btn pu-btn--primary" type="button" data-action="confirm">' +
            F.esc(t('confirm')) +
            '</button><button class="pu-btn pu-btn--danger" type="button" data-action="discard">' +
            F.esc(t('discard')) +
            '</button></div>';
        form.hidden = false;
        state.hidden = true;
        form.querySelectorAll('[data-field]').forEach(function (element) {
            element.oninput = function () {
                F.apply(records, element);
            };
        });
        form.querySelectorAll('[data-selection]').forEach(function (element) {
            element.onchange = function () {
                changeSelection(element.dataset.selection, element.value || null);
            };
        });
        form.querySelectorAll('[data-target]').forEach(function (button) {
            button.onclick = function () {
                chooseTarget(button.dataset.target);
            };
        });
        form.querySelectorAll('[data-action]').forEach(function (button) {
            button.onclick = function () {
                act(button.dataset.action);
            };
        });
        hydratePreviews();
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
        render();
    }
    function changeSelection(key, value) {
        selection()[key] = value;
        var target = selectedTarget();
        if (key === 'direction' && String((target || {}).adapter || '').toLowerCase() === 'mrerp') {
            if (value === 'purchase' && selection().payment !== 'credit')
                selection().payment = null;
            render();
        }
    }
    function hydratePreviews() {
        form.querySelectorAll('[data-preview]').forEach(function (element) {
            fetch(element.dataset.preview, { headers: { Authorization: 'Bearer ' + token() } })
                .then(function (response) {
                    if (!response.ok) throw Error('preview');
                    return response.blob();
                })
                .then(function (blob) {
                    var url = URL.createObjectURL(blob);
                    element.innerHTML =
                        '<a href="' +
                        url +
                        '" target="_blank" rel="noopener"><img src="' +
                        url +
                        '" alt="' +
                        F.esc(t('original')) +
                        '"></a>';
                })
                .catch(function () {
                    element.textContent = t('previewFailed');
                });
        });
    }
    function payload() {
        return {
            records: model.records,
            workspace_client_id: selection().workspace_client_id,
            endpoint_id: selection().endpoint_id,
            direction: selection().direction,
            adapter: selection().adapter,
            target_label: selection().target_label,
            posting_kind: selection().posting_kind,
            payment: selection().payment,
        };
    }
    function valid() {
        var target = selectedTarget(),
            adapter = String((target || {}).adapter || '').toLowerCase();
        var workspaceReady =
            selection().workspace_client_id != null ||
            target?.setup_action === 'auto_create_workspace';
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
    function save() {
        return api('/api/cowork-line/intake/draft/' + encodeURIComponent(draftId), {
            method: 'PUT',
            body: JSON.stringify(payload()),
        }).then(function (updated) {
            model = Object.assign(model, updated);
            render();
            return model;
        });
    }
    function show(key, kind) {
        stateKey = key;
        stateKind = kind || '';
        state.className = 'state ' + stateKind;
        state.textContent = t(key);
        state.hidden = false;
    }
    function setBusy(value) {
        busy = value;
        form.querySelectorAll('button,select,input,textarea').forEach(function (element) {
            element.disabled = value;
        });
    }
    function act(action) {
        if (busy) return;
        if (action === 'discard') {
            openDiscard();
            return;
        }
        if (!valid()) {
            show('required', 'error');
            return;
        }
        setBusy(true);
        var request = save().then(function () {
            if (action !== 'confirm') return null;
            if (!valid()) {
                var error = new Error('preflight');
                error.status = 422;
                throw error;
            }
            return api(
                '/api/cowork-line/intake/draft/' + encodeURIComponent(draftId) + '/confirm',
                { method: 'POST' }
            );
        });
        request
            .then(function (result) {
                if (action === 'save') {
                    show('saved');
                    return;
                }
                if (!result || result.saved !== true) {
                    form.hidden = false;
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
            .catch(handleError)
            .finally(function () {
                setBusy(false);
            });
    }
    function openDiscard() {
        var dialog = document.getElementById('discard-dialog');
        dialog.hidden = false;
        dialog.setAttribute('aria-hidden', 'false');
        document.getElementById('dialog-title').textContent = t('confirmDiscard');
        dialog.querySelectorAll('[data-dialog-cancel]').forEach(function (button) {
            button.textContent = button.tagName === 'BUTTON' ? t('cancel') : '';
            button.onclick = closeDiscard;
        });
        var confirm = dialog.querySelector('[data-dialog-confirm]');
        confirm.textContent = t('discard');
        confirm.onclick = discard;
    }
    function closeDiscard() {
        var dialog = document.getElementById('discard-dialog');
        dialog.hidden = true;
        dialog.setAttribute('aria-hidden', 'true');
    }
    function discard() {
        closeDiscard();
        setBusy(true);
        api('/api/cowork-line/intake/draft/' + encodeURIComponent(draftId) + '/discard', {
            method: 'POST',
        })
            .then(function () {
                form.hidden = true;
                show('discarded');
            })
            .catch(handleError)
            .finally(function () {
                setBusy(false);
            });
    }
    function handleError(error) {
        var detail = String((error.body || {}).detail || '');
        if (
            error.status === 401 ||
            error.status === 403 ||
            /draft_(expired|forbidden)/.test(detail)
        ) {
            show('expired', 'error');
            return;
        }
        show(error.status === 409 ? 'recoverable' : 'failed', 'error');
    }
    function boot() {
        return api('/api/cowork-line/intake/liff/config').then(function (config) {
            if (!config.liff_id || !window.liff) throw Error('liff_config_missing');
            return liff
                .init({ liffId: config.liff_id })
                .then(function () {
                    if (!liff.isLoggedIn()) {
                        liff.login();
                        throw Error('liff_login_required');
                    }
                    return api('/api/cowork-line/intake/liff/auth', {
                        method: 'POST',
                        body: JSON.stringify({ id_token: liff.getIDToken(), draft_id: draftId }),
                    });
                })
                .then(function (auth) {
                    sessionStorage.setItem('cowork_line_intake_token', auth.token);
                });
        });
    }
    document.getElementById('lang').value = lang;
    document.getElementById('lang').onchange = function (event) {
        lang = event.target.value;
        localStorage.setItem('pearnly_lang', lang);
        if (model) render();
        else show(stateKey, stateKind);
    };
    show('loading');
    boot()
        .then(function () {
            return api('/api/cowork-line/intake/draft/' + encodeURIComponent(draftId));
        })
        .then(function (value) {
            model = value;
            render();
        })
        .catch(handleError);
})();
