(function () {
    'use strict';

    var PAGE_SIZE = 20;

    function esc(value) {
        var node = document.createElement('div');
        node.textContent = value == null ? '' : String(value);
        return node.innerHTML;
    }

    function canonicalFields(record) {
        var pages = Array.isArray(record && record.pages) ? record.pages : [];
        var first = pages[0] && typeof pages[0] === 'object' ? pages[0] : {};
        return first.fields && typeof first.fields === 'object' ? first.fields : {};
    }

    function previewUrls(record) {
        if (Array.isArray(record.preview_urls) && record.preview_urls.length) {
            return record.preview_urls;
        }
        var fallback = record.preview_url || record.original_url || record.source_url || '';
        return fallback ? [fallback] : [];
    }

    function clean(value) {
        return String(value == null ? '' : value).trim();
    }

    function itemRows(fields) {
        return Array.isArray(fields.items) ? fields.items.filter(Boolean) : [];
    }

    function documentIssues(record, direction, options) {
        options = options || {};
        var fields = canonicalFields(record);
        var issues = [];
        var mode = direction || fields.direction || 'purchase';
        if (fields.is_not_invoice === true) issues.push('not_invoice');
        if (fields.is_copy_or_duplicate === true) issues.push('duplicate');
        if (!clean(fields.date || fields.invoice_date)) issues.push('date');
        if (mode === 'sales') {
            if (!clean(fields.invoice_number || fields.invoice_no)) issues.push('invoice_number');
        } else {
            if (!clean(fields.seller_name || fields.vendor)) issues.push('seller_name');
            if (!clean(fields.total_amount || fields.grand_total)) issues.push('total_amount');
        }
        var items = itemRows(fields);
        if (!items.length) issues.push('items');
        items.forEach(function (item, index) {
            if (!clean(item.name || item.description)) issues.push('item_name_' + index);
            if (!clean(item.qty || item.quantity)) issues.push('item_qty_' + index);
            if (
                options.requirePostingKind &&
                ['stock', 'service'].indexOf(clean(item.posting_kind).toLowerCase()) < 0
            ) {
                issues.push('posting_kind_' + index);
            }
        });
        return issues;
    }

    function summary(record, direction) {
        var fields = canonicalFields(record);
        var sales = direction === 'sales';
        var party = sales
            ? fields.buyer_name || fields.customer_name
            : fields.seller_name || fields.vendor;
        return {
            number: clean(fields.invoice_number || fields.invoice_no) || '—',
            date: clean(fields.date || fields.invoice_date) || '—',
            party: clean(party) || '—',
            total: clean(fields.total_amount || fields.grand_total) || '—',
            items: itemRows(fields).length,
            pages: Math.max(1, previewUrls(record).length),
        };
    }

    function create(options) {
        var root = options.root;
        var query = '';
        var filter = 'all';
        var limit = PAGE_SIZE;
        var selectedIndex = null;
        var busy = false;
        var objectUrls = new Map();

        function records() {
            var value = options.records();
            return Array.isArray(value) ? value : [];
        }

        function t(key, values) {
            return options.text(key, values);
        }

        function issues(record) {
            return options.issues(record);
        }

        function gate() {
            var review = records().filter(function (record) {
                return issues(record).length > 0;
            }).length;
            var globallyReady = options.globalReady ? options.globalReady() : true;
            return {
                review: review,
                ready: records().length - review,
                canConfirm: records().length > 0 && review === 0 && globallyReady,
                blockers: review + (globallyReady ? 0 : 1),
            };
        }

        function matches(record) {
            var hasIssues = issues(record).length > 0;
            if (filter === 'review' && !hasIssues) return false;
            if (filter === 'ready' && hasIssues) return false;
            if (!query) return true;
            var haystack = JSON.stringify({
                summary: summary(record, options.direction()),
                filename: record.filename,
                fields: canonicalFields(record),
            }).toLowerCase();
            return haystack.indexOf(query.toLowerCase()) >= 0;
        }

        function filtered() {
            return records()
                .map(function (record, index) {
                    return { record: record, index: index };
                })
                .filter(function (entry) {
                    return matches(entry.record);
                });
        }

        function badge(record) {
            var bad = issues(record).length > 0;
            return (
                '<span data-review-status class="review-status review-status--' +
                (bad ? 'issue' : 'ready') +
                '">' +
                esc(t(bad ? 'statusReview' : 'statusReady')) +
                '</span>'
            );
        }

        function listRow(entry) {
            var info = summary(entry.record, options.direction());
            var url = previewUrls(entry.record)[0] || '';
            return (
                '<button type="button" class="review-row" data-open-record="' +
                entry.index +
                '"><span class="review-thumb"' +
                (url ? ' data-review-preview="' + esc(url) + '"' : '') +
                '><span>' +
                esc(t('loadingPreview')) +
                '</span></span><span class="review-row__body"><span class="review-row__head"><strong>' +
                esc(info.number) +
                '</strong>' +
                badge(entry.record) +
                '</span><span class="review-row__party">' +
                esc(info.party) +
                '</span><span class="review-row__meta">' +
                esc(info.date) +
                ' · ' +
                esc(info.pages) +
                ' ' +
                esc(t('pages')) +
                ' · ' +
                esc(info.items) +
                ' ' +
                esc(t('itemCount')) +
                ' · ฿' +
                esc(info.total) +
                '</span><span class="review-row__link">' +
                esc(t('viewDetails')) +
                ' →</span></span></button>'
            );
        }

        function renderResults() {
            var container = root.querySelector('[data-review-results]');
            if (!container) return;
            var values = filtered();
            var shown = values.slice(0, limit);
            container.innerHTML = shown.length
                ? shown.map(listRow).join('')
                : '<p class="review-empty">' + esc(t('noMatches')) + '</p>';
            if (values.length > shown.length) {
                container.insertAdjacentHTML(
                    'beforeend',
                    '<button type="button" class="review-load" data-load-more>' +
                        esc(t('loadMore')) +
                        '</button>'
                );
            }
            bindList();
            hydratePreviews(container);
        }

        function filtersHtml() {
            return ['all', 'review', 'ready']
                .map(function (value) {
                    var key = 'filter' + value.charAt(0).toUpperCase() + value.slice(1);
                    return (
                        '<button type="button" class="review-filter' +
                        (filter === value ? ' is-active' : '') +
                        '" data-filter="' +
                        value +
                        '">' +
                        esc(t(key)) +
                        '</button>'
                    );
                })
                .join('');
        }

        function listHtml() {
            var report = gate();
            return (
                '<section class="review-toolbar"><label class="review-search"><span class="sr-only">' +
                esc(t('searchPlaceholder')) +
                '</span><input type="search" value="' +
                esc(query) +
                '" placeholder="' +
                esc(t('searchPlaceholder')) +
                '" data-review-search></label><div class="review-filters">' +
                filtersHtml() +
                '</div><p class="review-summary">' +
                esc(
                    t('batchSummary', {
                        total: records().length,
                        ready: report.ready,
                        review: report.review,
                    })
                ) +
                '</p></section><section class="review-results" data-review-results></section>'
            );
        }

        function detailHtml() {
            var record = records()[selectedIndex];
            if (!record) {
                selectedIndex = null;
                return listHtml();
            }
            var info = summary(record, options.direction());
            return (
                '<button type="button" class="review-back" data-review-back>← ' +
                esc(t('backToList')) +
                '</button><div class="review-detail__heading"><div><h2>' +
                esc(info.number) +
                '</h2><p>' +
                esc(info.party) +
                ' · ' +
                esc(info.date) +
                '</p></div>' +
                badge(record) +
                '</div>' +
                options.renderDetail(record, selectedIndex)
            );
        }

        function actionsHtml() {
            return (
                '<div class="review-gate" data-review-gate></div><div class="review-actions"><button class="pu-btn pu-btn--secondary" type="button" data-review-action="save">' +
                esc(t('save')) +
                '</button><button class="pu-btn pu-btn--primary" type="button" data-review-action="confirm">' +
                esc(t('confirmBatch')) +
                '</button><button class="pu-btn pu-btn--danger" type="button" data-review-action="discard">' +
                esc(t('discard')) +
                '</button></div>'
            );
        }

        function render() {
            if (window.lineIntakeDocumentViewer) window.lineIntakeDocumentViewer.cleanup(root);
            root.innerHTML =
                '<h1>' +
                esc(options.title()) +
                '</h1>' +
                (selectedIndex == null && options.renderPrefix ? options.renderPrefix() : '') +
                '<section class="review-workspace">' +
                (selectedIndex == null ? listHtml() : detailHtml()) +
                '</section>' +
                actionsHtml();
            root.hidden = false;
            bind();
            if (selectedIndex == null) renderResults();
            else {
                options.bindDetail(root, selectedIndex, refreshGate);
                if (window.lineIntakeSourcePage) window.lineIntakeSourcePage.bind(root);
                hydratePreviews(root);
            }
            refreshGate();
        }

        function bindList() {
            root.querySelectorAll('[data-open-record]').forEach(function (button) {
                button.onclick = function () {
                    selectedIndex = Number(button.dataset.openRecord);
                    render();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                };
            });
            var more = root.querySelector('[data-load-more]');
            if (more) {
                more.onclick = function () {
                    limit += PAGE_SIZE;
                    renderResults();
                };
                if ('IntersectionObserver' in window) {
                    var observer = new IntersectionObserver(function (entries) {
                        if (
                            entries.some(function (entry) {
                                return entry.isIntersecting;
                            })
                        ) {
                            observer.disconnect();
                            more.click();
                        }
                    });
                    observer.observe(more);
                }
            }
        }

        function bind() {
            var search = root.querySelector('[data-review-search]');
            if (search) {
                search.oninput = function () {
                    query = search.value.trim();
                    limit = PAGE_SIZE;
                    renderResults();
                };
            }
            root.querySelectorAll('[data-filter]').forEach(function (button) {
                button.onclick = function () {
                    filter = button.dataset.filter;
                    limit = PAGE_SIZE;
                    root.querySelectorAll('[data-filter]').forEach(function (candidate) {
                        candidate.classList.toggle('is-active', candidate === button);
                    });
                    renderResults();
                };
            });
            var back = root.querySelector('[data-review-back]');
            if (back)
                back.onclick = function () {
                    selectedIndex = null;
                    render();
                };
            root.querySelectorAll('[data-review-action]').forEach(function (button) {
                button.onclick = function () {
                    if (button.dataset.reviewAction === 'discard') openDiscard();
                    else options.onAction(button.dataset.reviewAction);
                };
            });
            if (options.bindPrefix) options.bindPrefix(root, render);
        }

        function refreshGate() {
            var report = gate();
            if (selectedIndex != null && records()[selectedIndex]) {
                var selectedHasIssues = issues(records()[selectedIndex]).length > 0;
                root.querySelectorAll('[data-review-status]').forEach(function (status) {
                    status.className =
                        'review-status review-status--' + (selectedHasIssues ? 'issue' : 'ready');
                    status.textContent = t(selectedHasIssues ? 'statusReview' : 'statusReady');
                });
            }
            var confirm = root.querySelector('[data-review-action="confirm"]');
            if (confirm) confirm.disabled = busy || !report.canConfirm;
            root.querySelectorAll('[data-review-action]').forEach(function (button) {
                if (button !== confirm) button.disabled = busy;
            });
            var note = root.querySelector('[data-review-gate]');
            if (note) {
                note.hidden = report.canConfirm;
                note.textContent = report.canConfirm
                    ? ''
                    : t('resolveBeforeConfirm', { count: report.blockers });
            }
        }

        function hydratePreviews(scope) {
            var elements = Array.from(scope.querySelectorAll('[data-review-preview]'));
            var load = function (element) {
                if (element.dataset.previewLoaded) return;
                element.dataset.previewLoaded = '1';
                var source = element.dataset.reviewPreview;
                var ready = objectUrls.has(source)
                    ? Promise.resolve(objectUrls.get(source))
                    : fetch(source, { headers: options.authHeaders() })
                          .then(function (response) {
                              if (!response.ok) throw Error('preview');
                              return response.blob();
                          })
                          .then(function (blob) {
                              var url = URL.createObjectURL(blob);
                              objectUrls.set(source, url);
                              return url;
                          });
                ready
                    .then(function (url) {
                        var image = '<img src="' + esc(url) + '" alt="' + esc(t('original')) + '">';
                        element.innerHTML = element.closest('[data-review-document-viewer]')
                            ? image
                            : '<a href="' +
                              esc(url) +
                              '" target="_blank" rel="noopener">' +
                              image +
                              '</a>';
                        element.dispatchEvent(
                            new CustomEvent('review-preview-loaded', { bubbles: true })
                        );
                    })
                    .catch(function () {
                        element.textContent = t('previewFailed');
                    });
            };
            if (!('IntersectionObserver' in window)) return elements.forEach(load);
            var observer = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            observer.unobserve(entry.target);
                            load(entry.target);
                        }
                    });
                },
                { rootMargin: '240px' }
            );
            elements.forEach(function (element) {
                observer.observe(element);
            });
        }

        function openDiscard() {
            var dialog = document.getElementById('discard-dialog');
            dialog.hidden = false;
            dialog.setAttribute('aria-hidden', 'false');
            dialog.querySelector('[data-dialog-title]').textContent = t('confirmDiscard');
            dialog.querySelector('[data-dialog-confirm]').textContent = t('discard');
            dialog.querySelector('[data-dialog-cancel-button]').textContent = t('cancel');
            dialog.querySelectorAll('[data-dialog-cancel]').forEach(function (element) {
                element.onclick = closeDiscard;
            });
            dialog.querySelector('[data-dialog-confirm]').onclick = function () {
                closeDiscard();
                options.onAction('discard');
            };
        }

        function closeDiscard() {
            var dialog = document.getElementById('discard-dialog');
            dialog.hidden = true;
            dialog.setAttribute('aria-hidden', 'true');
        }

        function setBusy(value) {
            busy = Boolean(value);
            refreshGate();
        }

        return {
            render: render,
            refreshGate: refreshGate,
            setBusy: setBusy,
            canConfirm: function () {
                return gate().canConfirm;
            },
        };
    }

    window.lineIntakeBatchReview = {
        canonicalFields: canonicalFields,
        create: create,
        documentIssues: documentIssues,
        escape: esc,
        previewUrls: previewUrls,
    };
})();
