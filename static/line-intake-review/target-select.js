(function () {
    'use strict';

    function create(options) {
        var model = options.model;
        var text = options.text;
        var escape = options.escape;

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

        function key(target) {
            return (
                endpointId(target) +
                ':' +
                String(target.workspace_client_id == null ? 'none' : target.workspace_client_id)
            );
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
            var cards = targets()
                .map(function (target) {
                    var workspace =
                        target.workspace_label ||
                        target.workspace_name ||
                        (target.workspace_client_id == null
                            ? text('autoWorkspace')
                            : text('workspace') + ' #' + target.workspace_client_id);
                    return (
                        '<button type="button" class="target-card' +
                        (selected() === target ? ' active' : '') +
                        (blocked(target) ? ' blocked' : '') +
                        '" data-target-option="' +
                        escape(key(target)) +
                        '"' +
                        (blocked(target) ? ' aria-disabled="true"' : '') +
                        '><strong>' +
                        escape(workspace) +
                        '</strong><span>' +
                        escape(
                            target.label || target.target_label || target.adapter || text('erp')
                        ) +
                        '</span><div class="checks">' +
                        status(target) +
                        '</div></button>'
                    );
                })
                .join('');
            var target = selected();
            return (
                '<section class="target-panel"><h2>' +
                escape(text('target')) +
                '</h2><div class="target-list">' +
                (cards || '<p class="target-empty">' + escape(text('noTarget')) + '</p>') +
                '</div><div class="target-grid"><label class="target-field"><span>' +
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
                '</div>' +
                (target && blocked(target)
                    ? '<p class="target-block-note">' + escape(text('blocked')) + '</p>'
                    : '') +
                '</section>'
            );
        }

        function choose(value) {
            var target = targets().find(function (row) {
                return key(row) === value;
            });
            if (!target || blocked(target)) return;
            Object.assign(selection(), {
                endpoint_id: target.endpoint_id || target.id,
                workspace_client_id: target.workspace_client_id,
                adapter: target.adapter,
                target_label: target.label || target.target_label,
                posting_kind: null,
                payment: null,
            });
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
                !blocked(target) &&
                workspaceReady &&
                /^(purchase|sales)$/.test(selection().direction || '') &&
                modeReady
            );
        }

        function bind(root, render) {
            root.querySelectorAll('[data-target-option]').forEach(function (button) {
                button.onclick = function () {
                    choose(button.dataset.targetOption);
                    if (options.onChange) options.onChange('target', selected());
                    render();
                };
            });
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
                return String((selected() || {}).adapter || '').toLowerCase();
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
