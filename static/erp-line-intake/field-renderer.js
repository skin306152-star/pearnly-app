(function () {
    'use strict';

    function render(key, value, required, path, label, escapeHtml, sourcePage) {
        var objectValue = value && typeof value === 'object';
        var itemField = /:item:\d+:/.test(path);
        var longItemName = /:item:\d+:name$/.test(path);
        var fieldValue = objectValue ? JSON.stringify(value, null, 2) : value;
        var source = ' data-source-page="' + Number(sourcePage || 0) + '"';
        var control =
            typeof value === 'boolean'
                ? '<select data-field="' +
                  escapeHtml(path) +
                  '"' +
                  source +
                  '><option value="true"' +
                  (value ? ' selected' : '') +
                  '>true</option><option value="false"' +
                  (!value ? ' selected' : '') +
                  '>false</option></select>'
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
