# -*- coding: utf-8 -*-
"""本地兜底小票须沿用成交快照里的折扣与税务身份。"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _render_receipt(*, doc_kind: str, cached_vat_registered: bool) -> str:
    script = f"""
const fs = require('fs');
let printed = '';
global.window = {{
  POS: {{
    state: {{ store: 'Shop', storeAddress: '', cashier: null }},
    fmt: (v) => Number(v || 0).toFixed(2),
    hm: () => '12:00',
    esc: (v) => String(v),
    nm: (v) => String(v),
    t: (v) => v,
    toast: () => {{}},
  }},
  open: () => ({{ document: {{ write: (html) => {{ printed = html; }}, close: () => {{}} }} }}),
}};
global.localStorage = {{
  getItem: () => JSON.stringify({{ vat_registered: {json.dumps(cached_vat_registered)}, tax_id: '123' }}),
  setItem: () => {{}},
}};
eval(fs.readFileSync({json.dumps(str(ROOT / "static/pos/pos-receipt.js"))}, 'utf8'));
window.POS.receipt.printLocal({{
  receipt_no: 'R-1',
  doc_kind: {json.dumps(doc_kind)},
  subtotal: '100.00',
  discount_total: '10.00',
  grand_total: '90.00',
  vat_amount: '0.00',
  lines: [{{ name: 'Item', qty: 1, price: 100 }}],
  payments: [{{ method: 'cash', amount: '90.00' }}],
}});
process.stdout.write(printed);
"""
    return subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_local_receipt_prints_discount_and_uses_sale_doc_kind():
    out = _render_receipt(doc_kind="receipt", cached_vat_registered=True)

    assert "ยอดรวม (Subtotal)" in out
    assert "ส่วนลด (Discount)" in out
    assert "-฿10.00" in out
    assert "ใบเสร็จรับเงิน" in out
    assert "ใบกำกับภาษีอย่างย่อ" not in out


def test_local_receipt_uses_authoritative_vat_sale_over_stale_cache():
    out = _render_receipt(doc_kind="abbrev_tax_invoice", cached_vat_registered=False)

    assert "ใบกำกับภาษีอย่างย่อ" in out
    assert "ภาษีมูลค่าเพิ่ม 7%" in out
