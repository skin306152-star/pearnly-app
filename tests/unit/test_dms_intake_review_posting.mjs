import assert from 'node:assert/strict';
import test from 'node:test';

import {
    applyPostingDefault,
    editablePostingItems,
    missingPostingKind,
    selectedPostingDefault,
} from '../../src/home/dms-intake-review-posting.ts';

function result(items) {
    return { invoices: [{ fields: { items } }] };
}

test('batch default changes only unconfirmed documents and mixed overrides stay visible', () => {
    const confirmedItems = [{ name: 'Done', qty: '1', posting_kind: 'service' }];
    const editableItems = [
        { name: 'Stock', qty: '1' },
        { name: 'Install', qty: '1' },
    ];
    const items = editablePostingItems(
        [result(confirmedItems), result(editableItems)],
        new Set([0])
    );

    applyPostingDefault(items, 'stock');
    assert.deepEqual(
        editableItems.map((item) => item.posting_kind),
        ['stock', 'stock']
    );
    assert.equal(confirmedItems[0].posting_kind, 'service');
    assert.equal(selectedPostingDefault(items), 'stock');

    editableItems[1].posting_kind = 'service';
    assert.equal(selectedPostingDefault(items), '');
});

test('valid per-line types pass even when a different field needs review', () => {
    assert.equal(
        missingPostingKind(
            result([
                { name: '', qty: '1', posting_kind: 'stock' },
                { name: 'Install', qty: '', posting_kind: 'service' },
            ])
        ),
        false
    );
    assert.equal(missingPostingKind(result([{ name: 'Missing', qty: '1' }])), true);
});
