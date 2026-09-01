(function () {
    'use strict';

    function enumControl(options, value, required, path, lang, escapeHtml, source) {
        var blank =
            '<option value=""' +
            (value == null || value === '' ? ' selected' : '') +
            '>' +
            escapeHtml(window.lineIntakeReviewI18n.text(lang, 'notSpecified')) +
            '</option>';
        return (
            '<select data-field="' +
            escapeHtml(path) +
            '"' +
            source +
            (required ? ' required' : '') +
            '>' +
            blank +
            options
                .map(function (option) {
                    return (
                        '<option value="' +
                        escapeHtml(option.value) +
                        '"' +
                        (option.selected ? ' selected' : '') +
                        '>' +
                        escapeHtml(option.label) +
                        '</option>'
                    );
                })
                .join('') +
            '</select>'
        );
    }

    function render(key, value, required, path, lang, label, escapeHtml, sourcePage) {
        var objectValue = value && typeof value === 'object';
        var itemField = /:item:\d+:/.test(path);
        var longItemName = /:item:\d+:name$/.test(path);
        var fieldValue = objectValue ? JSON.stringify(value, null, 2) : value;
        var source = ' data-source-page="' + Number(sourcePage || 0) + '"';
        var options = window.lineIntakeReviewI18n.options(lang, key, value);
        var control = options
            ? enumControl(options, value, required, path, lang, escapeHtml, source)
            : typeof value === 'boolean'
              ? '<select data-field="' +
                escapeHtml(path) +
                '"' +
                source +
                '><option value="true"' +
                (value ? ' selected' : '') +
                '>' +
                escapeHtml(window.lineIntakeReviewI18n.text(lang, 'true')) +
                '</option><option value="false"' +
                (!value ? ' selected' : '') +
                '>' +
                escapeHtml(window.lineIntakeReviewI18n.text(lang, 'false')) +
                '</option></select>'
              : objectValue || longItemName
                ? '<textarea data-field="' +
                  escapeHtml(path) +
                  '"' +
                  source +
                  (required ? ' required' : '') +
                  '>' +
                  escapeHtml(fieldValue) +
                  '</textarea>'
                : '<input data-field="' +
                  escapeHtml(path) +
                  '"' +
                  source +
                  ' value="' +
                  escapeHtml(fieldValue == null ? '' : fieldValue) +
                  '"' +
                  (required ? ' required' : '') +
                  '>';
        return (
            '<div class="field' +
            (itemField ? ' item-field item-field--' + escapeHtml(key) : '') +
            '"><label>' +
            escapeHtml(label(key)) +
            (required ? ' *' : '') +
            '</label>' +
            control +
            '</div>'
        );
    }

    window.erpLineFieldRenderer = { render: render };
})();
