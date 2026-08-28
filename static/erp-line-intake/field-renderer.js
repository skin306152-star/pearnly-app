(function () {
    'use strict';

    function render(key, value, required, recordIndex, label, escapeHtml) {
        var objectValue = value && typeof value === 'object';
        var fieldValue = objectValue ? JSON.stringify(value, null, 2) : value;
        var dataKey = recordIndex + ':' + escapeHtml(key);
        var control = objectValue
            ? '<textarea data-field="' +
              dataKey +
              '"' +
              (required ? ' required' : '') +
              '>' +
              escapeHtml(fieldValue) +
              '</textarea>'
            : '<input data-field="' +
              dataKey +
              '" value="' +
              escapeHtml(fieldValue == null ? '' : fieldValue) +
              '"' +
              (required ? ' required' : '') +
              '>';
        return (
            '<div class="field"><label>' +
            escapeHtml(key.indexOf('item.') === 0 ? key.split('.').pop() : label(key)) +
            (required ? ' *' : '') +
            '</label>' +
            control +
            '</div>'
        );
    }

    window.erpLineFieldRenderer = { render: render };
})();
