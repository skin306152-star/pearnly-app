/* Scan-first counts use independent, idempotent entries instead of replacing totals. */
(function () {
    'use strict';
    window.PearnlyStocktakeCounter = function (host, options) {
        const { t, esc, api, quantity } = options;
        let task = options.task,
            camera = null,
            cameraMode = !!options.mobile,
            disposed = false;
        let selected = null,
            editing = null,
            pending = null,
            busy = false,
            draft = null;
        let warehouse = '',
            location = '',
            reportPage = 0,
            reportQuery = '',
            reportFilter = 'all';
        let entryPage = 0,
            displayedEntries = task.entries.slice(0, 50),
            entryTotal = task.entry_total;
        const $ = (q) => host.querySelector(q);
        const action = (key, label = key) =>
            `<button type="button" class="pu-btn pu-btn--secondary" data-scan-action="${key}">${esc(t(label))}</button>`;
        const message = (value) => {
            const node = $('[data-scan-message]');
            if (node) node.textContent = value;
        };
        function error(err) {
            const key =
                'error-' +
                String(err.code || '')
                    .replace(/^stocktake\./, '')
                    .split(':')[0];
            const text = t(key);
            message(text.startsWith('st-error-') ? t('failed') : text);
        }
        function stop() {
            camera?.destroy();
            camera = null;
            $('[data-scan-camera]')?.replaceChildren();
        }
        function places() {
            return [...task.items, ...(task.places || [])];
        }
        function warehouseOptions() {
            return [
                ...new Set(
                    places()
                        .map((r) => r.warehouse)
                        .filter(Boolean)
                ),
            ];
        }
        function updateLocations() {
            const wh = $('[data-entry-warehouse]').value;
            const values = [
                ...new Set(
                    places()
                        .filter((r) => r.warehouse === wh)
                        .map((r) => r.location)
                        .filter(Boolean)
                ),
            ];
            $('[data-location-options]').innerHTML = values
                .map((value) => `<option value="${esc(value)}"></option>`)
                .join('');
        }
        function keepDraft() {
            if (!$('[data-entry-form]')) return;
            draft = {
                warehouse: $('[data-entry-warehouse]').value,
                location: $('[data-entry-location]').value,
                quantity: $('[data-entry-quantity]').value,
            };
        }
        function render() {
            stop();
            host.innerHTML = `<p data-scan-message role="status" aria-live="polite"></p>
                ${
                    task.status === 'active'
                        ? `<section data-reader ${selected ? 'hidden' : ''}>
                <p>${esc(t('scan-first'))}</p><div class="st-toolbar">${action('camera', 'scan')}${action('manual', 'manual-code')}${action('stop', 'stop')}</div>
                <div data-scan-camera class="st-camera"></div>
                <form data-code-form class="st-toolbar"><input data-code maxlength="300" autocomplete="off" aria-label="${esc(t('manual-code'))}" placeholder="${esc(t('manual-code'))}"><button class="pu-btn pu-btn--primary">${esc(t('find-product'))}</button></form></section>`
                        : ''
                }
                <section data-entry-editor></section>
                <details data-history><summary>${esc(t('entry-history'))}</summary><p>${esc(t('entry-history-help'))}</p><div data-entries></div></details>
                <details data-report ${options.mobile ? '' : 'open'}><summary>${esc(t('product-summary'))}</summary>
                <div class="st-toolbar"><input data-report-query value="${esc(reportQuery)}" aria-label="${esc(t('search'))}" placeholder="${esc(t('search'))}">
                <select data-report-filter aria-label="${esc(t('filter'))}">${['all', 'uncounted', 'differences'].map((k) => `<option value="${k}" ${reportFilter === k ? 'selected' : ''}>${esc(t(k))}</option>`).join('')}</select></div><div data-product-summary></div></details>`;
            const codeForm = $('[data-code-form]');
            if (codeForm)
                codeForm.onsubmit = (event) => {
                    event.preventDefault();
                    cameraMode = false;
                    stop();
                    match($('[data-code]').value.trim());
                };
            $('[data-report-query]').oninput = () => {
                reportQuery = $('[data-report-query]').value;
                reportPage = 0;
                summary();
            };
            $('[data-report-filter]').onchange = () => {
                reportFilter = $('[data-report-filter]').value;
                reportPage = 0;
                summary();
            };
            history();
            summary();
            if (selected) editor();
        }
        function match(code) {
            if (selected || busy || disposed) return false;
            const item = task.items.find((r) => r.barcode === code || r.product_code === code);
            if (!code || !item) {
                message(t('no-matches'));
                return false;
            }
            stop();
            selected = item;
            editing = null;
            pending = null;
            draft = {
                warehouse: warehouse || item.warehouse || '',
                location: warehouse ? location : item.location || '',
                quantity: '',
            };
            $('[data-reader]').hidden = true;
            editor();
            message('');
            return true;
        }
        function editor() {
            const values = draft;
            $('[data-entry-editor]').innerHTML = `<form data-entry-form class="st-card st-count">
                <h3>${esc(selected.product_name)}</h3><p>${esc(selected.product_code)} · ${esc(selected.unit)}</p>
                <p>${esc(t('book_qty'))}: ${esc(quantity(selected.book_qty))} · ${esc(t('actual-total'))}: ${esc(selected.actual_qty === null ? t('uncounted') : quantity(selected.actual_qty))}</p>
                <label>${esc(t('warehouse'))}<input data-entry-warehouse list="st-warehouses" maxlength="300" required placeholder="${esc(t('choose-or-type'))}" value="${esc(values.warehouse)}"></label>
                <datalist id="st-warehouses">${warehouseOptions()
                    .map((v) => `<option value="${esc(v)}"></option>`)
                    .join('')}</datalist>
                <label>${esc(t('location-optional'))}<input data-entry-location list="st-locations" maxlength="300" placeholder="${esc(t('choose-or-type'))}" value="${esc(values.location)}"></label><datalist id="st-locations" data-location-options></datalist>
                <label>${esc(t('quantity-this-entry'))}<input data-entry-quantity type="number" min="0" step="0.000001" inputmode="decimal" required value="${esc(values.quantity)}"></label>
                <p>${esc(t(editing ? 'edit-entry-help' : 'add-entry-help'))}</p><div class="st-toolbar"><button class="pu-btn pu-btn--primary" data-entry-submit>${esc(t(editing ? 'save-correction' : 'save-next'))}</button>${action('cancel', 'cancel')}</div></form>`;
            updateLocations();
            $('[data-entry-warehouse]').oninput = updateLocations;
            $('[data-entry-form]').onsubmit = (event) => {
                event.preventDefault();
                void save();
            };
            if (pending && !pending.confirmed)
                $('[data-entry-form]')
                    .querySelectorAll('input')
                    .forEach((node) => {
                        node.disabled = true;
                    });
            if (!options.mobile || !pending) $('[data-entry-quantity]').focus();
            $('[data-entry-editor]').scrollIntoView({ block: 'nearest' });
        }
        async function refresh() {
            const latest = await api('/' + task.id);
            if (disposed) return false;
            task = latest;
            displayedEntries = task.entries.slice(0, 50);
            entryTotal = task.entry_total;
            entryPage = 0;
            options.onChanged(task);
            return true;
        }
        async function save(voided = false) {
            if (busy || disposed) return;
            keepDraft();
            if (!pending) {
                const body = {
                    request_id: crypto.randomUUID(),
                    quantity: draft.quantity,
                    warehouse: draft.warehouse.trim(),
                    location: draft.location.trim(),
                };
                if (editing) Object.assign(body, { version: editing.version, voided });
                pending = {
                    body,
                    path:
                        '/' +
                        task.id +
                        (editing ? '/entries/' + editing.id : '/items/' + selected.id + '/entries'),
                    method: editing ? 'PATCH' : 'POST',
                    confirmed: false,
                };
            }
            busy = true;
            host.querySelectorAll('button,input,select').forEach((node) => {
                node.disabled = true;
            });
            try {
                if (!pending.confirmed) {
                    await api(pending.path, {
                        method: pending.method,
                        body: JSON.stringify(pending.body),
                    });
                    pending.confirmed = true;
                }
                if (disposed) return;
                const savedWarehouse = pending.body.warehouse,
                    savedLocation = pending.body.location;
                if (!(await refresh())) return;
                warehouse = savedWarehouse;
                location = savedLocation;
                selected = null;
                editing = null;
                draft = null;
                pending = null;
                render();
                message(t('entry-saved'));
                if (cameraMode) void scan();
                else if (!options.mobile) $('[data-code]')?.focus();
            } catch (err) {
                if (disposed) return;
                if (err.status >= 400 && err.status < 500 && !pending?.confirmed) pending = null;
                error(err);
                if (pending) message(t('retry-same-entry'));
                host.querySelectorAll('button,input,select').forEach((node) => {
                    node.disabled = false;
                });
                if (pending)
                    $('[data-entry-form]')
                        ?.querySelectorAll('input')
                        .forEach((node) => {
                            node.disabled = true;
                        });
            } finally {
                busy = false;
            }
        }
        async function scan() {
            if (task.status !== 'active' || selected || disposed) return;
            cameraMode = true;
            stop();
            message(t('camera-loading'));
            const handle = window.PearnlyStocktakeCamera({
                container: $('[data-scan-camera]'),
                onScan: match,
                onError() {
                    if (disposed || camera !== handle) return;
                    stop();
                    message(t('camera-failed'));
                },
            });
            camera = handle;
            const started = await handle.start();
            if (!disposed && camera === handle && started) message(t('camera-aim'));
        }
        function summary() {
            const q = reportQuery.toLowerCase();
            const items = task.items.filter(
                (r) =>
                    [r.product_code, r.product_name, r.barcode].some((v) =>
                        v.toLowerCase().includes(q)
                    ) &&
                    (reportFilter === 'all' ||
                        (reportFilter === 'uncounted'
                            ? r.actual_qty === null
                            : r.difference !== null && Number(r.difference) !== 0))
            );
            const visible = items.slice(reportPage * 50, (reportPage + 1) * 50);
            const fields = [
                'product_code',
                'product_name',
                'barcode',
                'unit',
                'book_qty',
                'actual_qty',
                'difference',
            ];
            $('[data-product-summary]').innerHTML =
                `<div class="st-table"><table><thead><tr>${fields.map((k) => `<th>${esc(t(k === 'actual_qty' ? 'actual-total' : k))}</th>`).join('')}</tr></thead><tbody>${visible.map((r) => `<tr>${fields.map((k) => `<td data-label="${esc(t(k === 'actual_qty' ? 'actual-total' : k))}">${esc(r[k] === null ? t('uncounted') : ['book_qty', 'actual_qty', 'difference'].includes(k) ? quantity(r[k]) : r[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div><div class="st-toolbar">${reportPage ? action('report-prev', 'prev') : ''}<span>${items.length ? reportPage * 50 + 1 : 0}–${reportPage * 50 + visible.length} / ${items.length}</span>${(reportPage + 1) * 50 < items.length ? action('report-next', 'next') : ''}</div>`;
        }
        function history() {
            $('[data-entries]').innerHTML =
                `<div class="st-list">${displayedEntries.map((e) => `<article class="st-card"><strong>${esc(e.product_name)}</strong><span>${esc(e.product_code)} · ${esc(e.warehouse)} / ${esc(e.location || '—')}</span><span>${esc(quantity(e.quantity))} ${esc(e.unit)} · ${esc(e.voided ? t('entry-voided') : t('entry-included'))}</span><small>${esc(e.counted_by_name)} · ${esc(new Date(e.counted_at).toLocaleString())}</small>${task.status === 'active' && !e.voided ? `<div class="st-toolbar"><button type="button" class="pu-btn pu-btn--secondary" data-edit-entry="${esc(e.id)}">${esc(t('edit-entry'))}</button><button type="button" class="pu-btn pu-btn--secondary" data-void-entry="${esc(e.id)}">${esc(t('void-entry'))}</button></div>` : ''}</article>`).join('') || `<p>${esc(t('no-entries'))}</p>`}</div><div class="st-toolbar">${entryPage ? action('entries-prev', 'prev') : ''}<span>${entryTotal ? entryPage * 50 + 1 : 0}–${entryPage * 50 + displayedEntries.length} / ${entryTotal}</span>${(entryPage + 1) * 50 < entryTotal ? action('entries-next', 'next') : ''}</div>`;
        }
        async function pageEntries(delta) {
            const target = entryPage + delta;
            const data = await api('/' + task.id + '/entries?offset=' + target * 50 + '&limit=50');
            if (disposed) return;
            entryPage = target;
            displayedEntries = data.entries;
            entryTotal = data.total;
            history();
        }
        host.onclick = async (event) => {
            const target = event.target.closest('button');
            if (!target || busy) return;
            event.stopPropagation();
            try {
                if (target.dataset.editEntry || target.dataset.voidEntry) {
                    if (pending) {
                        message(t('retry-same-entry'));
                        return;
                    }
                    stop();
                    editing = displayedEntries.find(
                        (e) => e.id === (target.dataset.editEntry || target.dataset.voidEntry)
                    );
                    selected = task.items.find((r) => r.id === editing.item_id);
                    draft = {
                        quantity: quantity(editing.quantity),
                        warehouse: editing.warehouse,
                        location: editing.location,
                    };
                    render();
                    if (target.dataset.voidEntry) {
                        if (window.confirm(t('void-confirm'))) await save(true);
                    }
                    return;
                }
                const key = target.dataset.scanAction;
                if (key === 'camera') await scan();
                if (key === 'manual' || key === 'stop') {
                    cameraMode = false;
                    stop();
                    message('');
                    if (key === 'manual') $('[data-code]').focus();
                }
                if (key === 'cancel') {
                    if (pending) {
                        message(t('retry-same-entry'));
                        return;
                    }
                    selected = null;
                    editing = null;
                    draft = null;
                    render();
                    if (cameraMode) void scan();
                }
                if (key === 'report-prev' || key === 'report-next') {
                    reportPage += key === 'report-prev' ? -1 : 1;
                    summary();
                }
                if (key === 'entries-prev' || key === 'entries-next')
                    await pageEntries(key === 'entries-prev' ? -1 : 1);
            } catch (err) {
                if (!disposed) error(err);
            }
        };
        render();
        if (cameraMode && task.status === 'active') void scan();
        return {
            refreshLanguage() {
                keepDraft();
                render();
                if (!selected && cameraMode) void scan();
            },
            destroy() {
                disposed = true;
                stop();
                host.onclick = null;
            },
        };
    };
})();
