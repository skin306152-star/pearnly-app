import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const storage = new Map();
const events = [];
const pill = { style: {}, classList: { add() {}, remove() {}, toggle() {} }, title: '' };
const text = { textContent: '' };
const context = {
    console,
    Date,
    Math,
    JSON,
    Number,
    String,
    Promise,
    setInterval: () => 1,
    clearInterval() {},
    localStorage: {
        getItem: (key) => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value),
    },
    document: {
        getElementById: (id) => (id === 'sync-pill' ? pill : id === 'sync-txt' ? text : null),
    },
    CustomEvent: class {
        constructor(type, init) {
            this.type = type;
            this.detail = init.detail;
        }
    },
};
context.window = context;
context.window.addEventListener = () => {};
context.window.dispatchEvent = (event) => events.push(event);
let uuid = 0;
context.POS = {
    state: { terminalId: 4, online: false, token: null },
    uuid: () => `12345678-0000-4000-8000-${String(++uuid).padStart(12, '0')}`,
    PosErr: class extends Error {
        constructor(code) {
            super(code);
            this.code = code;
        }
    },
    totals: { localTotals: () => ({ grand_total: '10.00', vat_amount: '0.65' }) },
    t: (key) => key,
    tf: (key, vars) => `${key}:${vars.n}`,
    data: {},
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('static/pos/pos-offline.js', 'utf8'), context);

const payload = {
    client_uuid: 'sale-1',
    sold_at: '2026-01-01T00:00:00Z',
    lines: [{ product_id: 'p1', sell_unit: 'each', qty: 4, unit_price: 10 }],
    payments: [{ amount: 10 }],
};
await assert.rejects(
    context.POS.offline.enqueueSale(payload),
    (error) => error.code === 'pos.out_of_stock'
);
assert.equal(await context.POS.offline.pendingCount(), 0);

context.POS.offline.cacheCatalog([
    { id: 'p1', stock: { qty_base: '5' }, units: [{ unit_name: 'each', factor: '1' }] },
]);
const pending = await context.POS.offline.enqueueSale(payload);
assert.equal(pending.sale.status, 'pending');
assert.equal(pending.sale.temporary_receipt, true);
assert.match(pending.sale.receipt_no, /^OFF-[A-Z0-9]{8}-T04-/);

await assert.rejects(
    context.POS.offline.enqueueSale({ ...payload, client_uuid: 'sale-2' }),
    (error) => error.code === 'pos.out_of_stock'
);

context.POS.state.online = true;
context.POS.state.token = 'token-1';
context.POS.data.syncSales = async () => ({
    results: [{ client_uuid: 'sale-1', ok: true, sale_id: 'server-1', receipt_no: 'RCP-1' }],
});
await context.POS.offline.sync();
const mapped = await context.POS.offline.findReceipt(pending.sale.receipt_no);
assert.equal(mapped.receipt_no, 'RCP-1');
assert.equal(mapped.status, 'synced');
assert.equal(await context.POS.offline.pendingCount(), 0);
assert.equal(events[0].detail.receipt_no, 'RCP-1');

console.log('POS offline runtime contracts passed');
