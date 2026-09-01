(function () {
    'use strict';

    function create(options) {
        var model = options.model;
        var text = options.text;
        var escape = options.escape;
        var lockedAdapter = '';

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

        function key(target) {
            return (
                endpointId(target) +
                ':' +
                String(target.workspace_client_id == null ? 'none' : target.workspace_client_id)
            );
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

        function accountRows() {
            var rows = [];
            accountTargets().forEach(function (target) {
                choicesFor(target).forEach(function (choice) {
                    rows.push({ target: target, choice: choice });
                });
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
                    String(target.workspace_client_id == null ? '' : target.workspace_client_id) ===
                        String(
                            selection().workspace_client_id == null
                                ? ''
                                : selection().workspace_client_id
                        )
                );
            });
        }

        function selectedAccount() {
            var target = selected();
            if (!target) return null;
            var wanted = String(selection().account_set || target.selected_account_key || '');
            var targetRows = accountRows().filter(function (candidate) {
                return candidate.target === target;
            });
            var row = targetRows.find(function (candidate) {
                return (
                    String(candidate.choice.key || candidate.choice.account_set || '') === wanted
                );
            });
            if (!row && targetRows.length === 1) row = targetRows[0];
            if (!row) return null;
            if (!selection().account_set) applyAccount(row);
            return row;
        }

        function adapter() {
            if (lockedAdapter) return lockedAdapter;
            lockedAdapter = adapterOf(selected()) || adapterOf(selection());
            return lockedAdapter;
        }

        function accountTargets() {
            var value = adapter();
            return value
                ? targets().filter(function (target) {
                      return adapterOf(target) === value;
                  })
                : [];
        }

        function adapterLabel(value) {
            return value === 'mrerp' ? 'MR.ERP' : value === 'express' ? 'Express' : value || 'ERP';
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

        function rootRows() {
            var seen = {};
            return accountRows().reduce(function (rows, row) {
                var rootKey = String(row.choice.root_key || '');
                if (!rootKey || seen[rootKey]) return rows;
                seen[rootKey] = true;
                rows.push({
                    key: rootKey,
                    label: row.choice.root_label || rootKey,
                });
                return rows;
            }, []);
        }

        function currentRoot() {
            var selectedRow = selectedAccount();
            return String(
                selection().account_root ||
                    (selectedRow && selectedRow.choice.root_key) ||
                    '' ||
                    (rootRows()[0] || {}).key ||
                    ''
            );
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
            var roots = rootRows();
            var root = currentRoot();
            var rows = accountRows().filter(function (row) {
                return (
                    adapter() !== 'express' || !root || String(row.choice.root_key || '') === root
                );
            });
            var selectedRow = selectedAccount();
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
            var target = selected();
            var rootHtml = '';
            if (adapter() === 'express' && roots.length) {
                rootHtml =
                    '<label class="target-field"><span>' +
                    escape(text('dataRoot')) +
                    '</span><select data-target-root>' +
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
                    '</select></label>';
            }
            return (
                '<section class="target-panel"><h2>' +
                escape(text('target')) +
                '</h2><div class="target-grid"><div class="target-field"><span>' +
                escape(text('erp')) +
                '</span><strong class="target-locked">' +
                escape(adapterLabel(adapter())) +
                '</strong></div>' +
                rootHtml +
                '<label class="target-field"><span>' +
                escape(text('accountSet')) +
                '</span><select data-target-account-set>' +
                (optionsHtml || '<option value="">' + escape(text('noAccountSet')) + '</option>') +
                '</select></label><label class="target-field"><span>' +
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
            Object.assign(selection(), {
                endpoint_id: target.endpoint_id || target.id,
                workspace_client_id: target.workspace_client_id,
                adapter: target.adapter,
                target_label: target.label || target.target_label,
                account_root: choice.root_key || null,
                account_set: choice.key || choice.account_set,
            });
        }

        function choose(value) {
            var row = accountRows().find(function (candidate) {
                return accountKey(candidate) === value;
            });
            if (!row || blocked(row.target) || row.choice.writable === false) return;
            applyAccount(row);
        }

        function valid() {
            var target = selected();
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
                !blocked(target) &&
                workspaceReady &&
                /^(purchase|sales)$/.test(selection().direction || '') &&
                modeReady
            );
        }

        function bind(root, render) {
            var rootSelect = root.querySelector('[data-target-root]');
            if (rootSelect) {
                rootSelect.onchange = function () {
                    selection().account_root = rootSelect.value || null;
                    selection().account_set = null;
                    var first = accountRows().find(function (row) {
                        return String(row.choice.root_key || '') === String(rootSelect.value || '');
                    });
                    if (first) applyAccount(first);
                    if (options.onChange)
                        options.onChange('account_root', rootSelect.value || null);
                    render();
                };
            }
            var accountSet = root.querySelector('[data-target-account-set]');
            if (accountSet) {
                accountSet.onchange = function () {
                    choose(accountSet.value);
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

    window.lineIntakeTargetSelect = { create: create };
})();
