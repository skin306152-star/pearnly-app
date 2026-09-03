import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POS_DIR = ROOT / "static" / "pos"


def test_cashier_renders_vat_modes_and_blocks_zero_total():
    script = r"""
const fs = require('fs');
const dir = process.argv[1];
const nodes = {};
const listeners = {};
function node() {
  const el = {
    children: [], style: {}, dataset: {}, value: '', innerHTML: '', hidden: false,
    disabled: false, title: '', _text: '', _classes: new Set(),
    appendChild(child) { this.children.push(child); return child; },
    addEventListener() {}, querySelectorAll() { return []; }, closest() { return null; },
    set textContent(value) { this._text = String(value); }, get textContent() { return this._text; },
  };
  el.classList = {
    add: (name) => el._classes.add(name), remove: (name) => el._classes.delete(name),
    contains: (name) => el._classes.has(name),
    toggle: (name, on) => { if (on) el._classes.add(name); else el._classes.delete(name); },
  };
  return el;
}
global.document = {
  readyState: 'loading',
  getElementById: (id) => (nodes[id] = nodes[id] || node()),
  querySelector: () => null, querySelectorAll: () => [], addEventListener() {},
  createElement: () => node(), body: node(),
};
const win = {
  addEventListener: (type, cb) => { (listeners[type] = listeners[type] || []).push(cb); },
  dispatchEvent: (event) => (listeners[event.type] || []).forEach((cb) => cb(event)),
};
global.window = win;
global.fetch = () => Promise.reject(new Error('offline'));
const load = (name) => (0, eval)(fs.readFileSync(dir + '/' + name, 'utf8'));
load('pos-i18n.js');
load('pos-totals.js');
load('pos-data.js');
load('pos-cost.js');
load('pos-cart-math.js');
const POS = win.POS;
POS.totals = global.POS.totals;
POS.state.lang = 'zh';
POS.toast = () => {};
load('pos-cashier.js');
POS.cashier.init();
function product(id, price) {
  return {
    id, name: {zh: id}, base_unit: '件', matched_unit: '件', vat_applicable: true,
    units: [{unit_name: '件', factor: '1', price: String(price)}],
    stock: {qty_base: '9'},
  };
}
POS.state.payment = {vat_registered: false, vat_rate: '0', price_includes_vat: false};
POS.cashier.addToCart(product('赠品', 0));
const zero = {
  grand: nodes['cart-grand'].textContent,
  payDisabled: nodes['cart-pay-btn'].disabled,
  noteHidden: nodes['cart-zero-note'].hidden,
};
POS.cashier.addToCart(product('商品', 100));
const unregistered = {
  grand: nodes['cart-grand'].textContent,
  label: nodes['cart-vat-label'].textContent,
  vatHidden: nodes['cart-vat-value'].style.display,
};
POS.state.payment = {vat_registered: true, vat_rate: '7', price_includes_vat: false};
win.dispatchEvent({type: 'pos:payment-settings'});
const exclusive = {
  grand: nodes['cart-grand'].textContent,
  vat: nodes['cart-vat-amt'].textContent,
  label: nodes['cart-vat-label'].textContent,
};
POS.state.payment.price_includes_vat = true;
win.dispatchEvent({type: 'pos:payment-settings'});
const inclusive = {
  grand: nodes['cart-grand'].textContent,
  vat: nodes['cart-vat-amt'].textContent,
  label: nodes['cart-vat-label'].textContent,
};
const mockSale = POS.cartMath.mockSale({
  lines: [{qty: 1, unit_price: 100, line_discount: 10, vat_applicable: true}],
  header_discount: {type: 'amount', value: 10},
  payments: [{method: 'cash', amount: 80}],
}).sale;
process.stdout.write(JSON.stringify({zero, unregistered, exclusive, inclusive, mockSale}));
"""
    proc = subprocess.run(
        ["node", "-e", script, "--", str(POS_DIR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    assert out["zero"] == {"grand": "0.00", "payDisabled": True, "noteHidden": False}
    assert out["unregistered"] == {
        "grand": "100.00",
        "label": "未登记 VAT · 本单不计税",
        "vatHidden": "none",
    }
    assert out["exclusive"] == {
        "grand": "107.00",
        "vat": "7.00",
        "label": "VAT 7%（另加）",
    }
    assert out["inclusive"] == {
        "grand": "100.00",
        "vat": "6.54",
        "label": "其中 VAT 7%（已含）",
    }
    assert out["mockSale"]["subtotal"] == "90.00"
    assert out["mockSale"]["discount_total"] == "20.00"
    assert out["mockSale"]["vat_amount"] == "5.23"
    assert out["mockSale"]["grand_total"] == "80.00"
