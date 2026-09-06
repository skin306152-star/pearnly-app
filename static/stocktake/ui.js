/* Cowork stocktake views shared by the web shell and its LINE mobile entry. */
(function () {
    'use strict';
    window.PearnlyStocktake = function (host, options) {
        const t = (key) => options.t('st-' + key);
        const quantity = (value) => {
            const text = String(value ?? '').replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1');
            return text === '-0' ? '0' : text;
        };
        const esc = (s) =>
            String(s == null ? '' : s).replace(
                /[&<>"']/g,
                (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
            );
        const button = (action, label) =>
            `<button type="button" class="pu-btn pu-btn--secondary" data-action="${action}">${esc(t(label))}</button>`;
        const api = options.api;
        let task = null,
            tasks = [],
            keyword = '',
            filter = 'all',
            selected = null;
        let cameraTicket = 0,
            counter = null;
        let warehouse = '',
            location = '',
            camera = null,
            generation = 0,
            busy = false,
            page = 0;
        const $ = (selector) => host.querySelector(selector);
        host.classList.add('stocktake');
        function message(text) {
            const node = $('[data-message]');
            if (node) node.textContent = text;
        }
        function error(err) {
            const raw = String(err.code || '');
            const [code, row] = raw.replace(/^stocktake\./, '').split(':');
            const translated = t('error-' + code);
            message(
                (translated === 'st-error-' + code ? t('failed') : translated) +
                    (row ? ' · ' + row : '')
            );
        }
        async function stopCamera() {
            counter?.destroy();
            counter = null;
            cameraTicket++;
            if (camera) {
                camera.destroy();
                camera = null;
            }
            const stage = $('[data-camera]');
            if (stage) stage.innerHTML = '';
            const stop = $('[data-action="stop"]');
            if (stop) stop.hidden = true;
        }
        function base() {
            host.innerHTML = `<div class="st-toolbar"><h1>${esc(t('title'))}</h1>${task ? button('back', 'back') : ''}</div><p data-message role="status" aria-live="polite"></p><div data-body></div>`;
        }
        function listView() {
            task = null;
            selected = null;
            base();
            $('[data-body]').innerHTML =
                `${options.mobile ? '' : `<div class="st-toolbar">${button('template', 'template')}${button('new', 'new')}</div><p>${esc(t('intro'))}</p>`}
                <div class="st-list">${tasks.length ? tasks.map((r) => `<button class="st-card" data-task="${esc(r.id)}"><strong>${esc(r.name)}</strong><span>${esc(t(r.status))} · ${r.counted}/${r.total} ${esc(t('counted'))}</span><progress value="${r.counted}" max="${r.total || 1}"></progress><span>${esc(t('differences'))}: ${r.differences}</span></button>`).join('') : `<p>${esc(t('empty'))}</p>`}</div>`;
        }
        async function load() {
            const seq = ++generation;
            await stopCamera();
            base();
            message(t('loading'));
            try {
                const data = await api('');
                if (seq !== generation) return;
                tasks = data.tasks;
                listView();
            } catch (err) {
                if (seq === generation) error(err);
            }
        }
        async function open(id) {
            const seq = ++generation;
            await stopCamera();
            message(t('loading'));
            try {
                const data = await api('/' + id);
                if (seq !== generation) return;
                task = data;
                selected = null;
                keyword = '';
                filter = 'all';
                page = 0;
                detailView();
            } catch (err) {
                if (seq === generation) error(err);
            }
        }
        function detailView() {
            void stopCamera();
            base();
            const counted = task.items.filter((r) => r.actual_qty !== null).length;
            if (task.count_mode === 'scan') {
                const overview = () =>
                    `${t(task.status)} · ${task.items.filter((r) => r.actual_qty !== null).length}/${task.items.length} ${t('counted')}`;
                $('[data-body]').innerHTML =
                    `<h2>${esc(task.name)}</h2><p data-overview>${esc(overview())}</p><progress data-overview-progress value="${counted}" max="${task.items.length || 1}"></progress>
                    <div class="st-toolbar">${options.mobile ? '' : button('export', 'export')}${task.status === 'active' && !options.mobile ? button('close', 'close') : ''}${button('refresh', 'refresh')}</div><div data-scan-session></div>`;
                counter = window.PearnlyStocktakeCounter($('[data-scan-session]'), {
                    task,
                    api,
                    t,
                    esc,
                    quantity,
                    mobile: options.mobile,
                    onChanged(next) {
                        task = next;
                        $('[data-overview]').textContent = overview();
                        $('[data-overview-progress]').value = task.items.filter(
                            (r) => r.actual_qty !== null
                        ).length;
                    },
                });
                return;
            }
            $('[data-body]').innerHTML =
                `<h2>${esc(task.name)}</h2><p>${esc(t('legacy-task'))}</p><p>${esc(t(task.status))} · ${counted}/${task.items.length} ${esc(t('counted'))}</p><progress value="${counted}" max="${task.items.length || 1}"></progress>
                <div class="st-toolbar">${options.mobile ? '' : button('export', 'export')}${task.status === 'active' && !options.mobile ? button('close', 'close') : ''}${button('refresh', 'refresh')}</div>
                ${task.status === 'active' ? `<div class="st-toolbar">${button('scan', 'scan')}${button('stop', 'stop')}</div><div data-camera class="st-camera"></div>` : ''}
                <form data-search class="st-toolbar"><input data-query aria-label="${esc(t('search'))}" placeholder="${esc(t('search'))}" value="${esc(keyword)}"><button class="pu-btn pu-btn--primary">${esc(t('search-button'))}</button><select data-filter aria-label="${esc(t('filter'))}">${['all', 'uncounted', 'differences'].map((k) => `<option value="${k}" ${filter === k ? 'selected' : ''}>${esc(t(k))}</option>`).join('')}</select></form>
                <div data-count></div><div data-rows></div>`;
            $('[data-search]').onsubmit = (event) => {
                event.preventDefault();
                keyword = $('[data-query]').value.trim();
                page = 0;
                rows();
            };
            $('[data-query]').oninput = () => {
                keyword = $('[data-query]').value.trim();
                page = 0;
                rows();
            };
            $('[data-filter]').onchange = () => {
                filter = $('[data-filter]').value;
                page = 0;
                rows();
            };
            rows();
            const stop = $('[data-action="stop"]');
            if (stop) stop.hidden = true;
        }
        function rows(exact = false) {
            const q = keyword.toLowerCase();
            const matches = task.items.filter(
                (r) =>
                    (!q ||
                        (exact
                            ? [r.product_code, r.barcode].includes(keyword)
                            : [
                                  r.product_code,
                                  r.product_name,
                                  r.barcode,
                                  r.warehouse,
                                  r.location,
                              ].some((v) => v.toLowerCase().includes(q)))) &&
                    (filter === 'all' ||
                        (filter === 'uncounted'
                            ? r.actual_qty === null
                            : r.difference !== null && Number(r.difference) !== 0))
            );
            const visible = matches.slice(page * 50, (page + 1) * 50);
            const headers = [
                'product_code',
                'product_name',
                'barcode',
                'warehouse',
                'location',
                'unit',
                'book_qty',
                'actual_qty',
                'difference',
            ];
            $('[data-rows]').innerHTML = matches.length
                ? `<div class="st-table"><table><thead><tr>${headers.map((k) => `<th>${esc(t(k))}</th>`).join('')}<th></th></tr></thead><tbody>${visible.map((r) => `<tr>${headers.map((k) => `<td data-label="${esc(t(k))}">${esc(r[k] === null ? t('uncounted') : ['book_qty', 'actual_qty', 'difference'].includes(k) ? quantity(r[k]) : r[k])}</td>`).join('')}<td>${task.status === 'active' ? `<button class="pu-btn pu-btn--secondary" data-item="${esc(r.id)}">${esc(t(r.actual_qty === null ? 'count' : 'recount'))}</button>` : ''}</td></tr>`).join('')}</tbody></table></div><div class="st-toolbar">${page ? button('prev', 'prev') : ''}<span>${page * 50 + 1}–${page * 50 + visible.length} / ${matches.length}</span>${(page + 1) * 50 < matches.length ? button('next', 'next') : ''}</div>`
                : `<p>${esc(t('no-matches'))}</p>`;
            if (exact && matches.length) {
                const preferred = matches.filter(
                    (r) => r.warehouse === warehouse && r.location === location
                );
                if (matches.length === 1) select(matches[0].id);
                else if (preferred.length === 1) select(preferred[0].id);
                else message(t('choose-location'));
            }
        }
        function select(id) {
            void stopCamera();
            selected = task.items.find((r) => r.id === id);
            const variants = task.items.filter((r) => r.product_code === selected.product_code);
            $('[data-count]').innerHTML =
                `<form class="st-card st-count"><h3>${esc(selected.product_name)}</h3><p>${esc(selected.product_code)} · ${esc(selected.unit)}</p><label>${esc(t('choose-location'))}<select data-variant>${variants.map((r) => `<option value="${esc(r.id)}" ${r.id === id ? 'selected' : ''}>${esc(r.warehouse)} / ${esc(r.location || '—')}</option>`).join('')}</select></label><label>${esc(t('actual_qty'))}<input data-qty type="number" inputmode="decimal" min="0" step="0.000001" required value="${esc(quantity(selected.actual_qty))}"></label><p>${esc(t('book_qty'))}: ${esc(quantity(selected.book_qty))} · ${esc(t('actual_qty'))}: ${esc(selected.actual_qty === null ? t('uncounted') : quantity(selected.actual_qty))}</p><div class="st-toolbar"><button class="pu-btn pu-btn--primary">${esc(t('save-next'))}</button>${button('cancel-count', 'cancel')}</div></form>`;
            if (options.mobile) {
                $('[data-rows]').hidden = true;
                $('[data-search]').hidden = true;
            }
            $('[data-variant]').onchange = () => select($('[data-variant]').value);
            $('[data-count] form').onsubmit = save;
            $('[data-qty]').focus();
            $('[data-count]').scrollIntoView({ block: 'nearest' });
        }
        async function save(event) {
            event.preventDefault();
            if (busy) return;
            const qty = $('[data-qty]').value;
            if (!qty.trim()) return;
            busy = true;
            const row = selected;
            const seq = generation;
            const id = task.id;
            $('[data-count] button:not([type])').disabled = true;
            try {
                await api('/' + id + '/items/' + row.id, {
                    method: 'PUT',
                    body: JSON.stringify({ quantity: qty, version: row.version }),
                });
                if (seq !== generation) return;
                warehouse = row.warehouse;
                location = row.location;
                const refreshed = await api('/' + id);
                if (seq !== generation) return;
                task = refreshed;
                selected = null;
                keyword = '';
                detailView();
                message(t('saved'));
                $('[data-query]').focus();
            } catch (err) {
                if (seq === generation) {
                    error(err);
                    const b = $('[data-count] button:not([type])');
                    if (b) b.disabled = false;
                }
            } finally {
                busy = false;
            }
        }
        async function scan() {
            const seq = generation;
            await stopCamera();
            const ticket = cameraTicket;
            const stop = $('[data-action="stop"]');
            if (stop) stop.hidden = false;
            message(t('camera-loading'));
            try {
                const engine = await window.PearnlyScanCamera.ensureLoaded();
                if (seq !== generation || ticket !== cameraTicket) return;
                camera = engine.create({
                    container: $('[data-camera]'),
                    onScan(code) {
                        void stopCamera();
                        keyword = String(code).trim();
                        filter = 'all';
                        page = 0;
                        $('[data-query]').value = keyword;
                        $('[data-filter]').value = 'all';
                        message('');
                        rows(true);
                    },
                    onError() {
                        message(t('camera-failed'));
                    },
                });
                const handle = camera;
                const started = await handle.start();
                if (seq === generation && ticket === cameraTicket && started)
                    message(t('camera-aim'));
            } catch {
                if (seq === generation) message(t('camera-failed'));
            }
        }
        function dialog(html, submit) {
            const modal = document.createElement('dialog');
            modal.className = 'modal st-dialog';
            modal.innerHTML = `<form><div>${html}</div><p data-dialog-message role="alert"></p><div class="st-toolbar"><button type="button" class="pu-btn pu-btn--secondary" data-cancel>${esc(t('cancel'))}</button><button class="pu-btn pu-btn--primary">${esc(t('confirm'))}</button></div></form>`;
            host.appendChild(modal);
            modal.querySelector('[data-cancel]').onclick = () => modal.close();
            modal.onclose = () => modal.remove();
            modal.querySelector('form').onsubmit = async (event) => {
                event.preventDefault();
                const submitButton = modal.querySelector('button:not([type])');
                submitButton.disabled = true;
                try {
                    await submit(modal);
                    modal.close();
                } catch (err) {
                    const raw = String(err.code || '')
                        .replace(/^stocktake\./, '')
                        .split(':');
                    const text = t('error-' + raw[0]);
                    modal.querySelector('[data-dialog-message]').textContent =
                        (text.startsWith('st-error-') ? t('failed') : text) +
                        (raw[1] ? ' · ' + raw[1] : '');
                    submitButton.disabled = false;
                }
            };
            const heading = modal.querySelector('h2');
            if (heading) {
                heading.id = 'st-dialog-title';
                modal.setAttribute('aria-labelledby', heading.id);
            }
            modal.showModal();
        }
        function newTask() {
            const requestId = crypto.randomUUID();
            const seq = generation;
            dialog(
                `<input type="hidden" name="request_id" value="${requestId}"><h2>${esc(t('new'))}</h2><p>${esc(t('template-help'))}</p><label>${esc(t('name'))}<input name="name" maxlength="120" required></label><label>Excel (.xlsx)<input name="file" type="file" accept=".xlsx" required></label><p>${esc(t('freeze'))}</p>`,
                async (modal) => {
                    const data = new FormData(modal.querySelector('form'));
                    const result = await api('', { method: 'POST', body: data });
                    if (seq === generation) await open(result.id);
                }
            );
        }
        host.onclick = async (event) => {
            const target = event.target.closest('button');
            if (!target) return;
            if (target.dataset.task) {
                await open(target.dataset.task);
                return;
            }
            if (target.dataset.item) {
                select(target.dataset.item);
                return;
            }
            const action = target.dataset.action;
            if (!action) return;
            try {
                if (action === 'cancel-count') {
                    selected = null;
                    detailView();
                }
                if (action === 'back') await load();
                if (action === 'refresh') await open(task.id);
                if (action === 'new') newTask();
                if (action === 'template')
                    await options.download('/template', 'stocktake-template.xlsx');
                if (action === 'export')
                    await options.download(
                        '/' + task.id + '/export',
                        'stocktake-' + task.id + '.xlsx'
                    );
                if (action === 'scan') await scan();
                if (action === 'stop') await stopCamera();
                if (action === 'prev' || action === 'next') {
                    page += action === 'next' ? 1 : -1;
                    rows();
                }
                if (action === 'close') {
                    const id = task.id;
                    const seq = generation;
                    dialog(
                        `<h2>${esc(t('close'))}</h2><p>${esc(t('close-confirm'))}</p><p>${task.items.filter((r) => r.actual_qty === null).length} ${esc(t('uncounted'))}</p>`,
                        async () => {
                            await api('/' + id + '/close', { method: 'POST' });
                            if (seq === generation) await open(id);
                        }
                    );
                }
            } catch (err) {
                error(err);
            }
        };
        return {
            load,
            refreshLanguage() {
                if (counter) {
                    host.querySelector('h1').textContent = t('title');
                    for (const action of ['back', 'export', 'close', 'refresh']) {
                        const node = $(`[data-action="${action}"]`);
                        if (node) node.textContent = t(action);
                    }
                    $('[data-overview]').textContent =
                        `${t(task.status)} · ${task.items.filter((r) => r.actual_qty !== null).length}/${task.items.length} ${t('counted')}`;
                    counter.refreshLanguage();
                } else if (task) detailView();
                else listView();
            },
            destroy() {
                generation++;
                void stopCamera();
                host.onclick = null;
                host.querySelectorAll('dialog').forEach((d) => d.close());
            },
        };
    };
})();
