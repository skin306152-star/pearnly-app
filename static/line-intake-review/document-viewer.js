(function () {
    'use strict';

    var active = null;
    var frame = null;

    function clean(value) {
        return String(value == null ? '' : value).trim();
    }

    function isPdf(record) {
        var contentType = clean(
            record && (record.source_mime_type || record.mime_type || record.content_type)
        ).toLowerCase();
        if (contentType.split(';')[0] === 'application/pdf') return true;
        return /\.pdf$/i.test(clean(record && record.filename));
    }

    function fileIcon() {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><path d="M14 2v6h6"></path><path d="M8 13h8M8 17h5"></path></svg>';
    }

    function closeIcon() {
        return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"></path></svg>';
    }

    function html(record, text) {
        var review = window.lineIntakeBatchReview;
        var urls = review.previewUrls(record);
        var pages = Array.isArray(record.pages) ? record.pages : [];
        var filename = clean(record.filename) || text('pdfDocument');
        var total = urls.length;
        var pageLabel = text('pages');
        return (
            '<div class="review-document-file"><button type="button" class="review-document-file__open" data-review-document-open aria-haspopup="dialog"><span class="review-document-file__icon">' +
            fileIcon() +
            '</span><span class="review-document-file__body"><strong>' +
            review.escape(filename) +
            '</strong><span>' +
            review.escape(total) +
            ' ' +
            review.escape(pageLabel) +
            ' · ' +
            review.escape(text('openOriginal')) +
            '</span></span><span class="review-document-file__type">PDF</span></button></div>' +
            '<section class="review-document-viewer" data-review-document-viewer data-pages-label="' +
            review.escape(pageLabel) +
            '" data-selected-page="0" role="dialog" aria-modal="true" aria-label="' +
            review.escape(filename) +
            '" aria-hidden="true" hidden><header class="review-document-viewer__header"><button type="button" class="review-document-viewer__close" data-review-document-close aria-label="' +
            review.escape(text('closeOriginal')) +
            '">' +
            closeIcon() +
            '</button><div class="review-document-viewer__title"><strong>' +
            review.escape(filename) +
            '</strong><span data-review-document-status aria-live="polite">1 / ' +
            review.escape(total) +
            ' ' +
            review.escape(pageLabel) +
            '</span></div><span aria-hidden="true"></span></header><div class="review-document-viewer__pages" data-review-document-pages>' +
            urls
                .map(function (url, index) {
                    var page = pages[index] || {};
                    var number = page.page_number || page.page || index + 1;
                    return (
                        '<figure class="review-document-page' +
                        (index === 0 ? ' is-source' : '') +
                        '" data-review-page="' +
                        index +
                        '"><figcaption>' +
                        review.escape(pageLabel) +
                        ' ' +
                        review.escape(number) +
                        '</figcaption><div class="review-document-page__image" data-review-preview="' +
                        review.escape(url) +
                        '">' +
                        review.escape(text('loadingPreview')) +
                        '</div></figure>'
                    );
                })
                .join('') +
            '</div></section>'
        );
    }

    function pages(viewer) {
        return Array.from(viewer.querySelectorAll('[data-review-page]'));
    }

    function updateStatus(viewer, index) {
        var values = pages(viewer);
        var selected = Math.max(0, Math.min(Number(index) || 0, values.length - 1));
        viewer.dataset.selectedPage = String(selected);
        values.forEach(function (page, pageIndex) {
            page.classList.toggle('is-source', pageIndex === selected);
        });
        var status = viewer.querySelector('[data-review-document-status]');
        if (status) {
            status.textContent =
                selected + 1 + ' / ' + values.length + ' ' + viewer.dataset.pagesLabel;
        }
        return selected;
    }

    function showPage(viewer, rawPage, behavior) {
        var values = pages(viewer);
        if (!values.length) return;
        var selected = updateStatus(viewer, rawPage);
        var scroller = viewer.querySelector('[data-review-document-pages]');
        if (!scroller || viewer.hidden) return;
        scroller.scrollTo({ top: values[selected].offsetTop, behavior: behavior || 'smooth' });
    }

    function currentPage(viewer) {
        var scroller = viewer.querySelector('[data-review-document-pages]');
        if (!scroller) return;
        var scrollerTop = scroller.getBoundingClientRect().top;
        var nearest = pages(viewer).reduce(
            function (best, page, index) {
                var distance = Math.abs(page.getBoundingClientRect().top - scrollerTop);
                return distance < best.distance ? { distance: distance, index: index } : best;
            },
            { distance: Infinity, index: 0 }
        );
        updateStatus(viewer, nearest.index);
    }

    function closeViewer(restoreFocus) {
        if (!active) return;
        var closing = active;
        active = null;
        closing.viewer.hidden = true;
        closing.viewer.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('review-document-viewer-open');
        document.removeEventListener('keydown', onKeydown);
        window.scrollTo({ left: closing.scrollX, top: closing.scrollY, behavior: 'auto' });
        if (restoreFocus && closing.opener && closing.opener.isConnected) closing.opener.focus();
    }

    function onKeydown(event) {
        if (event.key === 'Escape') closeViewer(true);
        if (event.key === 'Tab' && active) {
            event.preventDefault();
            active.viewer.querySelector('[data-review-document-close]').focus();
        }
    }

    function openViewer(viewer, opener) {
        if (active) closeViewer(false);
        active = {
            viewer: viewer,
            opener: opener,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
        };
        document.body.classList.add('review-document-viewer-open');
        viewer.hidden = false;
        viewer.setAttribute('aria-hidden', 'false');
        document.addEventListener('keydown', onKeydown);
        requestAnimationFrame(function () {
            showPage(viewer, viewer.dataset.requestedPage || viewer.dataset.selectedPage, 'auto');
            viewer.querySelector('[data-review-document-close]').focus();
        });
    }

    function bind(root) {
        root.querySelectorAll('[data-review-document-viewer]').forEach(function (viewer) {
            var opener = viewer.previousElementSibling.querySelector('[data-review-document-open]');
            var close = viewer.querySelector('[data-review-document-close]');
            var scroller = viewer.querySelector('[data-review-document-pages]');
            opener.onclick = function () {
                openViewer(viewer, opener);
            };
            close.onclick = function () {
                closeViewer(true);
            };
            scroller.onscroll = function () {
                if (frame) cancelAnimationFrame(frame);
                frame = requestAnimationFrame(function () {
                    currentPage(viewer);
                });
            };
            ['pointerdown', 'touchstart', 'wheel'].forEach(function (eventName) {
                scroller.addEventListener(eventName, function () {
                    delete viewer.dataset.requestedPage;
                });
            });
            viewer.addEventListener('review-preview-loaded', function () {
                if (viewer.hidden || viewer.dataset.requestedPage == null) return;
                requestAnimationFrame(function () {
                    showPage(viewer, viewer.dataset.requestedPage, 'auto');
                });
            });
        });
    }

    function selectPage(root, rawPage) {
        var viewer = root.querySelector('[data-review-document-viewer]');
        if (!viewer) return false;
        viewer.dataset.requestedPage = String(Number(rawPage) || 0);
        showPage(viewer, rawPage);
        return true;
    }

    function cleanup(root) {
        if (active && root.contains(active.viewer)) closeViewer(false);
    }

    window.lineIntakeDocumentViewer = {
        bind: bind,
        cleanup: cleanup,
        html: html,
        isPdf: isPdf,
        selectPage: selectPage,
    };
})();
