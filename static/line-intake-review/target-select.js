(function () {
    'use strict';

    function refreshTarget(api, refreshUrl, timing) {
        timing = timing || {};
        var startedAt = Date.now();
        var timeoutMs = timing.timeoutMs || 16 * 60 * 1000;
        var requestTimeoutMs = timing.requestTimeoutMs || 30000;

        function timedApi(path, options) {
            var remaining = timeoutMs - (Date.now() - startedAt);
            if (remaining <= 0) return Promise.reject(new Error('target_refresh_timeout'));
            var controller = new AbortController();
            var aborted = false;
            var timer = window.setTimeout(
                function () {
                    aborted = true;
                    controller.abort();
                },
                Math.max(1, Math.min(requestTimeoutMs, remaining))
            );
            return Promise.resolve()
                .then(function () {
                    return api(
                        path,
                        Object.assign({}, options || {}, { signal: controller.signal })
                    );
                })
                .catch(function (error) {
                    if (aborted) throw new Error('target_refresh_request_timeout');
                    throw error;
                })
                .finally(function () {
                    window.clearTimeout(timer);
                });
        }

        function statusUrl(requestId) {
            var split = refreshUrl.indexOf('?');
            var path = split < 0 ? refreshUrl : refreshUrl.slice(0, split);
            var query = split < 0 ? '' : refreshUrl.slice(split);
            return path + '/' + encodeURIComponent(requestId) + query;
        }

        function wait(requestId) {
            var elapsed = Date.now() - startedAt;
            if (elapsed >= timeoutMs) return Promise.reject(new Error('target_refresh_timeout'));
            return timedApi(statusUrl(requestId), { cache: 'no-store' }).then(function (result) {
                var refresh = result.refresh || result;
                var state = String(refresh.status || '');
                if (state === 'succeeded' && result.target) {
                    var revision = Number(refresh.result_revision || 0);
                    if (revision < 1) throw new Error('target_refresh_missing');
                    return {
                        target: result.target,
                        catalog_refresh_request_id: requestId,
                        catalog_refresh_revision: revision,
                    };
                }
                if (state === 'failed') {
                    throw new Error(String(refresh.error_code || 'target_refresh_failed'));
                }
                var delay = elapsed < 120000 ? 750 : 2500;
                return new Promise(function (resolve) {
                    window.setTimeout(resolve, delay);
                }).then(function () {
                    return wait(requestId);
                });
            });
        }

        return timedApi(refreshUrl, { method: 'POST', cache: 'no-store' }).then(function (refresh) {
            if (!refresh.request_id) throw new Error('target_refresh_missing');
            return wait(refresh.request_id);
        });
    }

    function create(options) {
        var model = options.model;
        var text = options.text;
        var escape = options.escape;
        var catalogRequests = {};
        var catalogArmed = {};
        var skipFocus = {};

        function current() {
            return model() || {};
        }

        function targets() {
            return Array.isArray(current().targets) ? current().targets : [];
        }

        function selection() {
            var value = current();
            return value.selection || (value.selection = {});
        }

        function endpointId(target) {
            return String(target.endpoint_id || target.id || '');
        }

        function adapterOf(target) {
            return String((target || {}).adapter || '').toLowerCase();
        }

        function connectionWorkspaceId(target) {
            if (!target) return null;
            return Object.prototype.hasOwnProperty.call(target, 'connection_workspace_client_id')
                ? target.connection_workspace_client_id
                : target.workspace_client_id;
        }

        function key(target) {
            return (
                endpointId(target) +
                ':' +
                String(
                    connectionWorkspaceId(target) == null ? 'none' : connectionWorkspaceId(target)
                )
            );
        }

        function catalogState(target) {
            return catalogRequests[key(target)] || '';
        }

        function fieldKey(target, field) {
            return key(target) + '::' + field;
        }

        function clearCatalogProof() {
            delete selection().catalog_refresh_request_id;
            delete selection().catalog_refresh_revision;
        }

        function replaceTarget(fresh) {
            var values = targets();
            var wanted = key(fresh);
            var index = values.findIndex(function (candidate) {
                return key(candidate) === wanted;
            });
            if (index < 0) throw new Error('target_changed');
            values[index] = Object.assign({}, values[index], fresh, {
                account_catalog_loaded: true,
            });
            return values[index];
        }

        function loadCatalog(target, render, field) {
            if (!target || typeof options.loadTarget !== 'function') {
                return Promise.resolve(target);
            }
            var targetKey = key(target);
            if (catalogRequests[targetKey] && catalogRequests[targetKey].promise) {
                return catalogRequests[targetKey].promise;
            }
            clearCatalogProof();
            var loadingState = { state: 'loading', field: field, long: false };
            catalogRequests[targetKey] = loadingState;
            render();
            var slowTimer = window.setTimeout(function () {
                if (catalogRequests[targetKey] !== loadingState) return;
                loadingState.long = true;
                render();
            }, 120000);
            var request = Promise.resolve()
                .then(function () {
                    return options.loadTarget(target);
                })
                .then(function (result) {
                    window.clearTimeout(slowTimer);
                    var fresh = result && result.target;
                    if (!fresh || key(fresh) !== targetKey) throw new Error('target_changed');
                    var requestId = String(result.catalog_refresh_request_id || '');
                    var revision = Number(result.catalog_refresh_revision || 0);
                    if (!requestId || revision < 1) throw new Error('target_refresh_missing');
                    delete catalogRequests[targetKey];
                    var replaced = replaceTarget(fresh);
                    selection().catalog_refresh_request_id = requestId;
                    selection().catalog_refresh_revision = revision;
                    catalogArmed[fieldKey(replaced, field)] = true;
                    render();
                    return replaced;
                })
                .catch(function () {
                    window.clearTimeout(slowTimer);
                    catalogRequests[targetKey] = { state: 'failed', field: field };
                    render();
                    return null;
                });
            catalogRequests[targetKey].promise = request;
            return request;
        }

        function choicesFor(target) {
            var choices = Array.isArray((target || {}).account_choices)
                ? target.account_choices
                : [];
            if (choices.length) return choices;
            var fallback = String(
                (target || {}).selected_account_key ||
                    (target || {}).account_set_label ||
                    (target || {}).account_set ||
                    ''
            );
            return fallback
                ? [{ key: fallback, label: accountLabel(target), account_set: fallback }]
                : [];
        }

        function accountRows(target) {
            var rows = [];
            if (!target) return rows;
            choicesFor(target).forEach(function (choice) {
                rows.push({ target: target, choice: choice });
            });
            return rows;
        }

        function accountKey(row) {
            return key(row.target) + '::' + String(row.choice.key || row.choice.account_set || '');
        }

        function selected() {
            return targets().find(function (target) {
                return (
                    endpointId(target) === String(selection().endpoint_id || '') &&
                    String(
                        connectionWorkspaceId(target) == null ? '' : connectionWorkspaceId(target)
                    ) ===
                        String(
                            connectionWorkspaceId(selection()) == null
                                ? ''
                                : connectionWorkspaceId(selection())
                        )
                );
            });
        }

        function selectedAccount() {
            var target = selected();
            if (!target) return null;
            var wanted = String(selection().account_set || '');
            if (!wanted) return null;
            var wantedRoot = String(selection().account_root || '');
            return accountRows(target).find(function (candidate) {
                return (
                    String(candidate.choice.key || candidate.choice.account_set || '') === wanted &&
                    (!wantedRoot || String(candidate.choice.root_key || '') === wantedRoot)
                );
            });
        }

        function adapter() {
            return adapterOf(selected()) || adapterOf(selection());
        }

        function adapterLabel(value) {
            return value === 'mrerp' ? 'MR.ERP' : value === 'express' ? 'Express' : value || 'ERP';
        }

        function targetOptionLabel(target) {
            var connection = target.connection_label || adapterLabel(adapterOf(target));
            var workspace = target.workspace_name || target.workspace_label || '';
            return [connection, workspace].filter(Boolean).join(' · ');
        }

        function accountLabel(target) {
            return (
                target.account_set_label ||
                target.account_set ||
                target.workspace_label ||
                target.workspace_name ||
                target.label ||
                text('accountSet')
            );
        }

        function choiceLabel(choice) {
            return (
                choice.label || choice.account_company || choice.account_set || text('accountSet')
            );
        }

        function selectedTargetLabel(target, choice) {
            var connection =
                target.connection_label ||
                (adapterOf(target) === 'mrerp'
                    ? 'MR.ERP'
                    : adapterOf(target) === 'express'
                      ? 'Express'
                      : target.label || target.target_label || 'ERP');
            return [connection, choiceLabel(choice)].filter(Boolean).join(' · ');
        }

        function rootYear(label) {
            var years = String(label || '').match(/\d{2}/g) || [];
            return years.reduce(function (latest, value) {
                return Math.max(latest, Number(value));
            }, -1);
        }

        function rootRows(target) {
            var seen = {};
            return accountRows(target)
                .reduce(function (rows, row) {
                    var rootKey = String(row.choice.root_key || '');
                    if (!rootKey || seen[rootKey]) return rows;
                    seen[rootKey] = true;
                    rows.push({
                        key: rootKey,
                        label: row.choice.root_label || rootKey,
                    });
                    return rows;
                }, [])
                .sort(function (left, right) {
                    return (
                        rootYear(right.label) - rootYear(left.label) ||
                        String(right.label).localeCompare(String(left.label), undefined, {
                            numeric: true,
                        })
                    );
                });
        }

        function currentRoot(target) {
            var roots = rootRows(target);
            var explicit = String(selection().account_root || '');
            if (
                explicit &&
                roots.some(function (row) {
                    return row.key === explicit;
                })
            ) {
                return explicit;
            }
            var selectedRow = selectedAccount();
            return String((selectedRow && selectedRow.choice.root_key) || '');
        }

        function blocked(target) {
            return (
                !target ||
                target.selectable === false ||
                target.configured === false ||
                Boolean(target.block_reason) ||
                (Array.isArray(target.missing) && target.missing.length > 0)
            );
        }

        function status(target) {
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
                .map(function (value) {
                    return (
                        '<span class="check ' +
                        (/disconnected|offline|unmatched|occupied/.test(value) ? 'bad' : '') +
                        '">' +
                        escape(text(value)) +
                        '</span>'
                    );
                })
                .join('');
        }

        function modeField(target) {
            var adapter = String((target || {}).adapter || selection().adapter || '').toLowerCase();
            var purchase = selection().direction === 'purchase';
            if (adapter === 'express') {
                return (
                    '<label class="target-field"><span>' +
                    escape(text('mode')) +
                    '</span><select data-target-selection="posting_kind"><option value="">—</option><option value="stock"' +
                    (selection().posting_kind === 'stock' ? ' selected' : '') +
                    '>' +
                    escape(text('stock')) +
                    '</option><option value="service"' +
                    (selection().posting_kind === 'service' ? ' selected' : '') +
                    '>' +
                    escape(text('service')) +
                    '</option></select></label>'
                );
            }
            return (
                '<label class="target-field"><span>' +
                escape(text('payment')) +
                '</span><select data-target-selection="payment"><option value="">—</option>' +
                (purchase
                    ? ''
                    : '<option value="cash"' +
                      (selection().payment === 'cash' ? ' selected' : '') +
                      '>' +
                      escape(text('cash')) +
                      '</option>') +
                '<option value="credit"' +
                (selection().payment === 'credit' ? ' selected' : '') +
                '>' +
                escape(text('credit')) +
                '</option></select></label>'
            );
        }

        function html() {
            var target = selected();
            var loadState = target ? catalogState(target) : '';
            var loading = loadState && loadState.state === 'loading';
            var loadFailed = loadState && loadState.state === 'failed';
            var loadingField = loadState && loadState.field;
            var loadingText = text(
                loadState && loadState.long ? 'loadingAccountsLong' : 'loadingAccounts'
            );
            var roots = rootRows(target);
            var root = currentRoot(target);
            var rows = accountRows(target).filter(function (row) {
                if (adapter() !== 'express') return true;
                return Boolean(root) && String(row.choice.root_key || '') === root;
            });
            var selectedRow = selectedAccount();
            var targetOptions = targets()
                .map(function (candidate) {
                    return (
                        '<option value="' +
                        escape(key(candidate)) +
                        '"' +
                        (target === candidate ? ' selected' : '') +
                        (blocked(candidate) ? ' disabled' : '') +
                        '>' +
                        escape(targetOptionLabel(candidate)) +
                        '</option>'
                    );
                })
                .join('');
            var optionsHtml = rows
                .map(function (row) {
                    return (
                        '<option value="' +
                        escape(accountKey(row)) +
                        '"' +
                        (selectedRow && accountKey(selectedRow) === accountKey(row)
                            ? ' selected'
                            : '') +
                        (blocked(row.target) || row.choice.writable === false ? ' disabled' : '') +
                        '>' +
                        escape(choiceLabel(row.choice)) +
                        '</option>'
                    );
                })
                .join('');
            var rootHtml = '';
            if (adapter() === 'express') {
                rootHtml =
                    '<label class="target-field"><span>' +
                    escape(text('dataRoot')) +
                    '</span><span class="target-select-control"><select data-target-root' +
                    (loading && loadingField === 'root' ? ' disabled aria-busy="true"' : '') +
                    '><option value=""' +
                    (root ? '' : ' selected') +
                    '>—</option>' +
                    roots
                        .map(function (row) {
                            return (
                                '<option value="' +
                                escape(row.key) +
                                '"' +
                                (row.key === root ? ' selected' : '') +
                                '>' +
                                escape(row.label) +
                                '</option>'
                            );
                        })
                        .join('') +
                    '</select>' +
                    (loading && loadingField === 'root'
                        ? '<span class="target-load-state" role="status" aria-live="polite"><span class="target-spinner" aria-hidden="true"></span>' +
                          escape(loadingText) +
                          '</span>'
                        : '') +
                    '</span>' +
                    (loadFailed && loadingField === 'root'
                        ? '<span class="target-load-error" role="status" aria-live="polite">' +
                          escape(text('loadAccountsFailed')) +
                          '</span>'
                        : '') +
                    '</label>';
            }
            return (
                '<section class="target-panel"><h2>' +
                escape(text('target')) +
                '</h2><div class="target-grid"><label class="target-field"><span>' +
                escape(text('erp')) +
                '</span><select data-target-erp><option value=""' +
                (target ? '' : ' selected') +
                '>—</option>' +
                targetOptions +
                '</select></label>' +
                rootHtml +
                '<label class="target-field"><span>' +
                escape(text('accountSet')) +
                '</span><span class="target-select-control"><select data-target-account-set' +
                (loading && loadingField === 'account' ? ' disabled aria-busy="true"' : '') +
                '><option value=""' +
                (selectedRow ? '' : ' selected') +
                '>—</option>' +
                (optionsHtml ||
                    '<option value="" disabled>' + escape(text('noAccountSet')) + '</option>') +
                '</select>' +
                (loading && loadingField === 'account'
                    ? '<span class="target-load-state" role="status" aria-live="polite"><span class="target-spinner" aria-hidden="true"></span>' +
                      escape(loadingText) +
                      '</span>'
                    : '') +
                '</span>' +
                (loadFailed && loadingField === 'account'
                    ? '<span class="target-load-error" role="status" aria-live="polite">' +
                      escape(text('loadAccountsFailed')) +
                      '</span>'
                    : '') +
                '</label><label class="target-field"><span>' +
                escape(text('direction')) +
                '</span><select data-target-selection="direction"' +
                (options.lockDirection ? ' disabled' : '') +
                '><option value="">—</option><option value="purchase"' +
                (selection().direction === 'purchase' ? ' selected' : '') +
                '>' +
                escape(text('purchase')) +
                '</option><option value="sales"' +
                (selection().direction === 'sales' ? ' selected' : '') +
                '>' +
                escape(text('sales')) +
                '</option></select></label>' +
                modeField(target) +
                '</div><div class="checks">' +
                (target ? status(target) : '') +
                '</div>' +
                (target && blocked(target)
                    ? '<p class="target-block-note">' + escape(text('blocked')) + '</p>'
                    : '') +
                '</section>'
            );
        }

        function applyAccount(row) {
            var target = row.target;
            var choice = row.choice;
            var currentSelection = selection();
            var sameConnection =
                endpointId(target) === String(currentSelection.endpoint_id || '') &&
                String(connectionWorkspaceId(target)) ===
                    String(connectionWorkspaceId(currentSelection));
            Object.assign(selection(), {
                endpoint_id: target.endpoint_id || target.id,
                connection_workspace_client_id: connectionWorkspaceId(target),
                workspace_client_id:
                    sameConnection && currentSelection.workspace_client_id != null
                        ? currentSelection.workspace_client_id
                        : target.workspace_client_id,
                adapter: target.adapter,
                target_label: selectedTargetLabel(target, choice),
                account_root: choice.root_key || null,
                account_set: choice.key || choice.account_set,
            });
        }

        function chooseTarget(value) {
            var target = targets().find(function (candidate) {
                return key(candidate) === value;
            });
            if (!target || blocked(target)) return;
            clearCatalogProof();
            Object.assign(selection(), {
                endpoint_id: target.endpoint_id || target.id,
                connection_workspace_client_id: connectionWorkspaceId(target),
                workspace_client_id: target.workspace_client_id,
                adapter: target.adapter,
                target_label: target.label || targetOptionLabel(target),
                account_root: null,
                account_set: null,
                posting_kind: null,
                payment: null,
            });
            var wanted = String(target.selected_account_key || '');
            var fallback = accountRows(target).find(function (row) {
                return String(row.choice.key || row.choice.account_set || '') === wanted;
            });
            if (fallback && fallback.choice.writable !== false) applyAccount(fallback);
        }

        function choose(value) {
            var row = accountRows(selected()).find(function (candidate) {
                return accountKey(candidate) === value;
            });
            if (!row || blocked(row.target) || row.choice.writable === false) return;
            applyAccount(row);
        }

        function valid() {
            var target = selected();
            var loadState = target ? catalogState(target) : null;
            if (loadState && (loadState.state === 'loading' || loadState.state === 'failed')) {
                return false;
            }
            var adapter = String((target || {}).adapter || '').toLowerCase();
            var workspaceReady =
                selection().workspace_client_id != null ||
                (target && target.setup_action === 'auto_create_workspace');
            var modeReady =
                adapter === 'express'
                    ? /^(stock|service)$/.test(selection().posting_kind || '')
                    : selection().direction === 'purchase'
                      ? selection().payment === 'credit'
                      : /^(cash|credit)$/.test(selection().payment || '');
            return Boolean(
                target &&
                selectedAccount() &&
                (adapter !== 'express' || Boolean(currentRoot(target))) &&
                !blocked(target) &&
                workspaceReady &&
                /^(purchase|sales)$/.test(selection().direction || '') &&
                modeReady
            );
        }

        function bind(root, render) {
            function bindCatalogLoad(element, field) {
                if (!element) return;
                function begin(event) {
                    var target = selected();
                    if (!target) return;
                    var sessionKey = fieldKey(target, field);
                    if (event && event.type === 'focus' && skipFocus[sessionKey]) {
                        delete skipFocus[sessionKey];
                        return;
                    }
                    if (catalogArmed[sessionKey]) {
                        delete catalogArmed[sessionKey];
                        if (event && event.type === 'pointerdown') skipFocus[sessionKey] = true;
                        return;
                    }
                    if (event && event.type === 'pointerdown') event.preventDefault();
                    loadCatalog(target, render, field);
                }
                element.onpointerdown = begin;
                element.onfocus = begin;
                element.onblur = function () {
                    var target = selected();
                    if (!target) return;
                    var sessionKey = fieldKey(target, field);
                    delete catalogArmed[sessionKey];
                    delete skipFocus[sessionKey];
                };
            }
            var erp = root.querySelector('[data-target-erp]');
            if (erp) {
                erp.onchange = function () {
                    chooseTarget(erp.value);
                    if (options.onChange) options.onChange('target', selected());
                    render();
                };
            }
            var rootSelect = root.querySelector('[data-target-root]');
            if (rootSelect) {
                bindCatalogLoad(rootSelect, 'root');
                rootSelect.onchange = function () {
                    delete catalogArmed[fieldKey(selected(), 'root')];
                    selection().account_root = rootSelect.value || null;
                    selection().account_set = null;
                    var target = selected();
                    selection().target_label = target ? targetOptionLabel(target) : null;
                    if (options.onChange)
                        options.onChange('account_root', rootSelect.value || null);
                    render();
                };
            }
            var accountSet = root.querySelector('[data-target-account-set]');
            if (accountSet) {
                bindCatalogLoad(accountSet, 'account');
                accountSet.onchange = function () {
                    delete catalogArmed[fieldKey(selected(), 'account')];
                    if (accountSet.value) {
                        choose(accountSet.value);
                    } else {
                        selection().account_set = null;
                        var target = selected();
                        selection().target_label = target ? targetOptionLabel(target) : null;
                    }
                    if (options.onChange) options.onChange('target', selected());
                    render();
                };
            }
            root.querySelectorAll('[data-target-selection]').forEach(function (element) {
                element.onchange = function () {
                    var field = element.dataset.targetSelection;
                    selection()[field] = element.value || null;
                    if (field === 'direction') selection().payment = null;
                    if (options.onChange) options.onChange(field, element.value || null);
                    render();
                };
            });
        }

        return {
            adapter: function () {
                return adapter();
            },
            bind: bind,
            html: html,
            selected: selected,
            selection: selection,
            valid: valid,
        };
    }

    window.lineIntakeTargetSelect = { create: create, refreshTarget: refreshTarget };
})();
