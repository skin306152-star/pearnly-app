(function () {
    'use strict';

    function render(key, value, required, path, label, escapeHtml) {
        var objectValue = value && typeof value === 'object';
        var fieldValue = objectValue ? JSON.stringify(value, null, 2) : value;
        var control =
            typeof value === 'boolean'
                ? '<select data-field="' +
                  escapeHtml(path) +
                  '"><option value="true"' +
                  (value ? ' selected' : '') +
                  '>true</option><option value="false"' +
                  (!value ? ' selected' : '') +
                  '>false</option></select>'
                : objectValue
                  ? '<textarea data-field="' +
                    escapeHtml(path) +
                    '"' +
                    (required ? ' required' : '') +
                    '>' +
                    escapeHtml(fieldValue) +
                    '</textarea>'
                  : '<input data-field="' +
                    escapeHtml(path) +
                    '" value="' +
                    escapeHtml(fieldValue == null ? '' : fieldValue) +
                    '"' +
                    (required ? ' required' : '') +
                    '>';
        return (
            '<div class="field"><label>' +
            escapeHtml(label(key)) +
            (required ? ' *' : '') +
            '</label>' +
            control +
            '</div>'
        );
    }

    window.erpLineFieldRenderer = { render: render };
})();
