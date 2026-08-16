(function (root) {
    'use strict';

    function create(callbacks) {
        var core = root.DailyCore;
        var state = core.state;

        function sendToLogin() {
            core.clearToken();
            state.gate = 'login';
            root.DailyGate.renderGate();
        }

        function isAccessDenied(res) {
            return res.status === 401 || res.status === 404;
        }

        function loadMonth() {
            state.loading = true;
            callbacks.rerender();
            core.api('/api/daily/entries?month=' + encodeURIComponent(state.monthId)).then(
                function (res) {
                    if (res.status === 200) {
                        state.entries = (res.body && res.body.entries) || [];
                    } else if (isAccessDenied(res)) {
                        sendToLogin();
                        return;
                    } else {
                        state.entries = [];
                        callbacks.showToast('daily.err.load_failed');
                    }
                    state.loading = false;
                    callbacks.rerender();
                }
            );
        }

        function saveEntry(entry) {
            if (state.saving) return;
            state.saving = true;
            core.api('/api/daily/entries', { method: 'POST', json: entry }).then(function (res) {
                state.saving = false;
                if (res.status === 200 && res.body) {
                    state.entries.push(res.body);
                    state.entries.sort(function (a, b) {
                        return (
                            String(b.entry_date).localeCompare(String(a.entry_date)) ||
                            String(b.created_at).localeCompare(String(a.created_at))
                        );
                    });
                    state.showEntryForm = false;
                    callbacks.showToast('daily.toast.saved');
                } else if (isAccessDenied(res)) {
                    sendToLogin();
                    return;
                } else {
                    callbacks.showToast('daily.err.save_failed');
                }
                callbacks.rerender();
            });
        }

        function deleteEntry(id) {
            if (!root.confirm(core.t('daily.confirm.delete'))) return;
            core.api('/api/daily/entries/' + encodeURIComponent(id), { method: 'DELETE' }).then(
                function (res) {
                    if (res.status === 200) {
                        state.entries = state.entries.filter(function (entry) {
                            return entry.id !== id;
                        });
                        callbacks.showToast('daily.toast.deleted');
                    } else if (isAccessDenied(res)) {
                        sendToLogin();
                        return;
                    } else {
                        callbacks.showToast('daily.err.delete_failed');
                    }
                    callbacks.rerender();
                }
            );
        }

        function exportData() {
            core.api('/api/daily/export').then(function (res) {
                if (isAccessDenied(res)) {
                    sendToLogin();
                    return;
                }
                if (res.status !== 200) {
                    callbacks.showToast('daily.err.load_failed');
                    callbacks.rerender();
                    return;
                }
                var payload = {
                    version: 1,
                    exportedAt: new Date().toISOString(),
                    entries: (res.body && res.body.entries) || [],
                };
                var blob = new Blob([JSON.stringify(payload, null, 2)], {
                    type: 'application/json',
                });
                var link = root.document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'daily-finance-' + new Date().toISOString().slice(0, 10) + '.json';
                link.click();
                URL.revokeObjectURL(link.href);
                callbacks.showToast('daily.toast.exported');
                callbacks.rerender();
            });
        }

        function importFile(file) {
            var reader = new FileReader();
            reader.onload = function () {
                var parsed = null;
                try {
                    parsed = JSON.parse(String(reader.result));
                } catch (error) {
                    parsed = null;
                }
                var incoming = Array.isArray(parsed)
                    ? parsed
                    : parsed && Array.isArray(parsed.entries)
                      ? parsed.entries
                      : null;
                if (!incoming || !incoming.length) {
                    callbacks.showToast('daily.err.import_invalid');
                    callbacks.rerender();
                    return;
                }
                var valid = incoming.every(function (entry) {
                    return (
                        entry &&
                        typeof entry.id === 'string' &&
                        typeof entry.date === 'string' &&
                        (entry.type === 'income' || entry.type === 'expense') &&
                        typeof entry.title === 'string' &&
                        Number.isFinite(Number(entry.amount))
                    );
                });
                if (!valid) {
                    callbacks.showToast('daily.err.import_invalid');
                    callbacks.rerender();
                    return;
                }
                if (!root.confirm(core.t('daily.confirm.import', { n: incoming.length }))) return;
                var queue = incoming.slice();
                var done = 0;
                var next = function () {
                    if (!queue.length) {
                        callbacks.showToast('daily.toast.imported', { n: done });
                        loadMonth();
                        return;
                    }
                    var entry = queue.shift();
                    core.api('/api/daily/entries', {
                        method: 'POST',
                        json: {
                            date: entry.date,
                            kind: entry.type,
                            title: entry.title,
                            amount: Number(entry.amount),
                        },
                    }).then(function (res) {
                        if (isAccessDenied(res)) {
                            sendToLogin();
                            queue.length = 0;
                            return;
                        }
                        if (res.status === 200) done += 1;
                        next();
                    });
                };
                next();
            };
            reader.readAsText(file);
        }

        return {
            loadMonth: loadMonth,
            saveEntry: saveEntry,
            deleteEntry: deleteEntry,
            exportData: exportData,
            importFile: importFile,
        };
    }

    root.DailyActions = { create: create };
})(typeof window !== 'undefined' ? window : globalThis);
