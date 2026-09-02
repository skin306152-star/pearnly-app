(function () {
    'use strict';

    var FIELD_ALIASES = {
        invoice_number: ['invoice_number', 'invoice_no'],
        date: ['date', 'invoice_date'],
        seller_name: ['seller_name', 'vendor'],
        total_amount: ['total_amount', 'grand_total'],
        name: ['name', 'description'],
        qty: ['qty', 'quantity'],
        price: ['price', 'unit_price'],
        subtotal: ['subtotal', 'amount', 'line_total'],
    };

    function clean(value) {
        return String(value == null ? '' : value).trim();
    }

    function fields(page) {
        var value = page && page.fields;
        return value && typeof value === 'object' ? value : {};
    }

    function valueFor(source, key) {
        var names = FIELD_ALIASES[key] || [key];
        for (var index = 0; index < names.length; index += 1) {
            var value = source[names[index]];
            if (clean(value)) return value;
        }
        return '';
    }

    function sameValue(left, right) {
        if (left && typeof left === 'object') return false;
        return clean(left) !== '' && clean(left) === clean(right);
    }

    function itemMatches(candidate, expected) {
        if (!candidate || !expected) return false;
        var keys = ['name', 'qty', 'price', 'subtotal'];
        var compared = 0;
        for (var index = 0; index < keys.length; index += 1) {
            var left = valueFor(candidate, keys[index]);
            var right = valueFor(expected, keys[index]);
            if (!clean(right)) continue;
            compared += 1;
            if (!sameValue(left, right)) return false;
        }
        return compared > 0;
    }

    function fieldPage(record, key, itemIndex) {
        var pages = Array.isArray(record && record.pages) ? record.pages : [];
        if (pages.length < 2) return 0;
        var canonical = fields(pages[0]);
        if (itemIndex != null) {
            var expected = (Array.isArray(canonical.items) ? canonical.items : [])[itemIndex];
            if (!expected) return 0;
            for (var itemPage = 1; itemPage < pages.length; itemPage += 1) {
                var pageItems = fields(pages[itemPage]).items;
                if (
                    Array.isArray(pageItems) &&
                    pageItems.some(function (candidate) {
                        return itemMatches(candidate, expected);
                    })
                ) {
                    return itemPage;
                }
            }
            return 0;
        }
        var expectedValue = valueFor(canonical, key);
        if (!clean(expectedValue)) return 0;
        for (var pageIndex = 1; pageIndex < pages.length; pageIndex += 1) {
            if (sameValue(valueFor(fields(pages[pageIndex]), key), expectedValue)) {
                return pageIndex;
            }
        }
        return 0;
    }

    function originalsHtml(record, text) {
        var review = window.lineIntakeBatchReview;
        var urls = review.previewUrls(record);
        if (!urls.length) return '<p class="review-empty">—</p>';
        var viewer = window.lineIntakeDocumentViewer;
        if (viewer && viewer.isPdf(record)) return viewer.html(record, text);
        var pages = Array.isArray(record.pages) ? record.pages : [];
        return (
            '<div class="review-originals" data-review-originals>' +
            urls
                .map(function (url, index) {
                    var page = pages[index] || {};
                    var number = page.page_number || page.page || index + 1;
                    return (
                        '<figure class="review-original' +
                        (index === 0 ? ' is-source' : '') +
                        '" data-review-page="' +
                        index +
                        '"><figcaption>' +
                        review.escape(text('pages')) +
                        ' ' +
                        review.escape(number) +
                        '</figcaption><div class="review-original__image" data-review-preview="' +
                        review.escape(url) +
                        '">' +
                        review.escape(text('loadingPreview')) +
                        '</div></figure>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function showPage(root, rawPage) {
        var page = Number(rawPage || 0);
        if (
            window.lineIntakeDocumentViewer &&
            window.lineIntakeDocumentViewer.selectPage(root, page)
        ) {
            return;
        }
        var container = root.querySelector('[data-review-originals]');
        var target = root.querySelector('[data-review-page="' + page + '"]');
        if (!container || !target) return;
        root.querySelectorAll('[data-review-page]').forEach(function (element) {
            element.classList.toggle('is-source', element === target);
        });
        container.scrollTo({ top: target.offsetTop - container.offsetTop, behavior: 'smooth' });
    }

    function bind(root) {
        if (window.lineIntakeDocumentViewer) window.lineIntakeDocumentViewer.bind(root);
        root.querySelectorAll('[data-source-page]').forEach(function (control) {
            var follow = function () {
                showPage(root, control.dataset.sourcePage);
            };
            control.addEventListener('focus', follow);
            control.addEventListener('click', follow);
        });
    }

    window.lineIntakeSourcePage = {
        bind: bind,
        fieldPage: fieldPage,
        originalsHtml: originalsHtml,
        showPage: showPage,
    };
})();
