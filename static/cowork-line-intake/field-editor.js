(function () {
    'use strict';

    var ORDER = [
        'document_type',
        'is_not_invoice',
        'is_copy_or_duplicate',
        'invoice_number',
        'date_raw',
        'date',
        'seller_name',
        'seller_tax',
        'seller_branch',
        'seller_addr',
        'buyer_name',
        'buyer_tax',
        'buyer_branch',
        'buyer_addr',
        'subtotal',
        'vat',
        'wht_rate',
        'wht_amount',
        'discount',
        'total_amount',
        'cash_amount',
        'change_amount',
        'payment_method',
        'currency',
        'category',
        'notes',
    ];
    var META = new Set(['items', 'additional_invoices', 'source_refs', 'direction']);

    function esc(value) {
        var node = document.createElement('div');
        node.textContent = value == null ? '' : String(value);
        return node.innerHTML;
    }

    function scalarControl(value, path, lang, label) {
        if (typeof value === 'boolean') {
            return (
                '<select data-field="' +
                esc(path) +
                '"><option value="true"' +
                (value ? ' selected' : '') +
                '>' +
                esc(label(lang, 'true')) +
                '</option><option value="false"' +
                (!value ? ' selected' : '') +
                '>' +
                esc(label(lang, 'false')) +
                '</option></select>'
            );
        }
        var multiline = /addr|notes/i.test(path);
        return multiline
            ? '<textarea rows="3" data-field="' + esc(path) + '">' + esc(value) + '</textarea>'
            : '<input data-field="' + esc(path) + '" value="' + esc(value) + '">';
    }

    function renderFields(fields, recordIndex, lang, label) {
        var keys = ORDER.filter(function (key) {
            return Object.prototype.hasOwnProperty.call(fields, key);
        });
        Object.keys(fields).forEach(function (key) {
            if (!META.has(key) && keys.indexOf(key) < 0 && fields[key] == null) return;
            if (!META.has(key) && keys.indexOf(key) < 0) keys.push(key);
        });
        return (
            '<div class="field-grid">' +
            keys
                .map(function (key) {
                    var value = fields[key];
                    if (value && typeof value === 'object') return '';
                    return (
                        '<label class="field"><span>' +
                        esc(label(lang, key)) +
                        '</span>' +
                        scalarControl(value, recordIndex + ':' + key, lang, label) +
                        '</label>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function renderItems(fields, recordIndex, lang, label) {
        var items = Array.isArray(fields.items) ? fields.items : [];
        if (!items.length) items.push({ name: '', qty: '', price: '', subtotal: '' });
        return (
            '<div class="items">' +
            items
                .map(function (item, itemIndex) {
                    var keys = ['name', 'qty', 'price', 'subtotal'];
                    Object.keys(item).forEach(function (key) {
                        if (keys.indexOf(key) < 0 && key !== 'posting_kind') keys.push(key);
                    });
                    return (
                        '<div class="item-row">' +
                        keys
                            .map(function (key) {
                                return (
                                    '<label class="field"><span>' +
                                    esc(label(lang, key)) +
                                    '</span>' +
                                    scalarControl(
                                        item[key],
                                        recordIndex + ':items:' + itemIndex + ':' + key,
                                        lang,
                                        label
                                    ) +
                                    '</label>'
                                );
                            })
                            .join('') +
                        '</div>'
                    );
                })
                .join('') +
            '</div>'
        );
    }

    function apply(records, element) {
        var parts = element.dataset.field.split(':');
        var fields = records[Number(parts[0])].pages[0].fields;
        var current =
            parts[1] === 'items' ? fields.items[Number(parts[2])][parts[3]] : fields[parts[1]];
        var value = element.value;
        if (typeof current === 'boolean') value = value === 'true';
        if (parts[1] === 'items') fields.items[Number(parts[2])][parts[3]] = value;
        else fields[parts[1]] = value;
    }

    window.coworkFieldEditor = {
        esc: esc,
        renderFields: renderFields,
        renderItems: renderItems,
        apply: apply,
    };
})();
