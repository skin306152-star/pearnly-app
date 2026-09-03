#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建品表单发出去的那份载荷,跟接它的两层对不对得上(P0-① 零元卖货 / P1-⑪ 条码删不掉)。

链路上的每一段都用真件跑,不拿桩验桩:
  载荷  ← src/home/sales-products.ts 真表单(node · tests.unit._sales_products_dom)
  下发  ← services.pos.catalog._row_to_item 真整形(products 行 → POS 目录条目)
  收银  ← static/pos/pos-cashier.js 真加货 + static/pos/pos-i18n.js 真词典(node)
  改档  ← routes.products_routes._patch_fields + services.sales.products.update_product 真 SQL 拼装

钉死的两条,都是"两种状态被揉成一种"的同一类病:
  P0-① 招牌流程(扫到未建档 → 去建这个商品 → 只填名字)把价格写成 0,零元闸只拦得住 null,
       于是它在最该管的那条路上恒不生效 —— ฿0 进车、฿0 出门,小票/日结/报表全看着正常。
  P1-⑪ 清空条码发 null 被当成"这次没改",绿 toast 说已保存而条码原封不动,撞码成死胡同。
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from routes.products_routes import ProductUpdate, _patch_fields
from services.pos.catalog import _row_to_item
from services.sales.products import NULLABLE_FIELDS, update_product
from tests.unit._sales_products_dom import run

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POS_DIR = PROJECT_ROOT / "static" / "pos"
HOME_SRC = PROJECT_ROOT / "src" / "home"
CODE13 = "8850999320014"

# 扫到未建档的码 → 点「去建这个商品」→ 只填名字就保存。这个流程的场景就是抱着货快速建档,
# 价格框留空是它最常见的样子,不是边角情形。
QUICK_CREATE = """
window.PearnlyScanWedge = { register: () => () => {} };
loadProducts();
(async () => {
    window.openProductFormWithBarcode('%s', { overlay: true });
    await tick();
    document.getElementById('sx-pf-th').value = 'น้ำเปล่า';
    %s
    calls.length = 0;
    await document.getElementById('sx-p-save').onclick();
    await tick();
    const wrote = calls.filter((c) => c.method === 'POST')[0] || null;
    out({ body: wrote && wrote.body });
})();
"""

# 撞码 → 「去编辑那个商品」→ 换成那件货的编辑态(产品自己那条路,不是测试自己捏一个表单)
EDIT_THEN_CLEAR = """
window.PearnlyScanWedge = { register: () => () => {} };
loadProducts();
(async () => {
    answer = () => reply({ product: %s, matched_by: 'product', matched_unit: null });
    window.openProductFormWithBarcode('%s', { overlay: true });
    await tick();
    document.getElementById('sx-bc-goedit').onclick();
    await tick();
    const before = {
        barcode: document.getElementById('sx-pf-barcode').value,
        price: document.getElementById('sx-pf-price').value,
    };
    %s
    calls.length = 0;
    await document.getElementById('sx-p-save').onclick();
    await tick();
    const wrote = calls.filter((c) => c.method === 'PATCH')[0] || null;
    out({ before, body: wrote && wrote.body });
})();
"""

# 收银台真件:pos-i18n(真词典)+ pos-data(POS 命名空间)+ pos-cashier(零元闸就在里头)。
# DOM 只是宿主 —— 加不加得进车由 addToCart 的返回值说了算,那正是网格点选那条路吃的东西。
POS_HARNESS = r"""
const fs = require('fs');
const dir = process.argv[1];
const item = JSON.parse(process.argv[2]);
function mkEl() {
    const el = {
        tagName: 'DIV', children: [], style: {}, dataset: {}, value: '',
        className: '', innerHTML: '', disabled: false, _text: '', _cls: new Set(), _on: {},
        appendChild(c) { this.children.push(c); return c; },
        removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); return c; },
        set textContent(v) { this._text = String(v); this.children = []; },
        get textContent() { return this.children.length ? this.children.map((c) => c.textContent).join('') : this._text; },
        addEventListener(t, f) { (this._on[t] = this._on[t] || []).push(f); },
        setAttribute(n, v) { this[n] = v; },
        querySelector: () => null, querySelectorAll: () => [], closest: () => null,
    };
    el.classList = {
        add: (c) => el._cls.add(c), remove: (c) => el._cls.delete(c),
        contains: (c) => el._cls.has(c),
        toggle: (c, on) => { const want = on === undefined ? !el._cls.has(c) : !!on;
            if (want) el._cls.add(c); else el._cls.delete(c); return want; },
    };
    return el;
}
const byId = {};
global.document = {
    readyState: 'complete',
    getElementById: (id) => (byId[id] = byId[id] || mkEl()),
    createElement: () => mkEl(),
    createTextNode: (t) => ({ textContent: String(t) }),
    querySelector: () => null, querySelectorAll: () => [], addEventListener: () => {},
    body: mkEl(),
};
const win = { addEventListener: () => {} };
global.window = win;
global.fetch = () => Promise.reject(new Error('本测不打网络'));
const load = (name) => (0, eval)(fs.readFileSync(dir + '/' + name, 'utf8'));
load('pos-i18n.js');
load('pos-data.js');
load('pos-product-names.js');
load('pos-cost.js');
const POS = win.POS;
POS.state.lang = 'zh';
POS.toast = () => {};
load('pos-totals.js');
POS.totals = global.POS.totals;
load('pos-cart-math.js');
load('pos-cashier.js');
const refused = POS.cashier.addToCart(item);
const hints = {};
['th', 'en', 'zh', 'ja'].forEach((lang) => {
    POS.state.lang = lang;
    hints[lang] = POS.t('posui.cart.fix_in_backoffice');
});
POS.state.lang = 'zh';
process.stdout.write(JSON.stringify({
    refused: refused,
    // 拒收卡念出来的那句话(pos-scan.js::onRefused 就是这么拼的)
    said: refused ? POS.tf(refused.key, { name: POS.nm(item.name), unit: refused.unit }) : '',
    hints: hints,
}));
"""


def _js(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _payload(scenario: str) -> dict:
    body = run(scenario)["body"]
    assert body is not None, "表单一次都没写出去 · 场景没跑通"
    return body


def _catalog_price(unit_price):
    """products 行 → POS 目录条目的价格字段(真整形:None 保持 None,数值补两位小数)。"""
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "name_th": "น้ำเปล่า",
        "name_en": None,
        "name_zh": None,
        "category_id": None,
        "barcode": CODE13,
        "base_unit": "ขวด",
        "image_url": None,
        "vat_applicable": True,
        "track_batch": False,
        "is_weighed": False,
        "unit_price": unit_price,
    }
    return _row_to_item(row, {}, {"qty": {}, "near": set()})


def _till(item: dict) -> dict:
    proc = subprocess.run(
        ["node", "-e", POS_HARNESS, "--", str(POS_DIR), json.dumps(item, ensure_ascii=False)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise AssertionError("收银台 harness 跑挂了:\n" + proc.stderr.decode("utf-8", "replace"))
    return json.loads(proc.stdout.decode("utf-8"))


def _sets_of(sql: str, params: list) -> dict:
    """UPDATE ... SET a = %s, b = %s ... → {列: 参数}(now() 那种没有占位符,自然不进来)。"""
    body = sql.split(" SET ", 1)[1].split(" WHERE ", 1)[0]
    return dict(zip(re.findall(r"(\w+) = %s", body), params))


class _Cursor:
    """只记 SQL 的游标桩:被测的是 update_product 拼出来的那条 UPDATE,不是 psycopg2。"""

    def __init__(self):
        self.calls: list = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params or [])))

    def fetchone(self):
        return {"id": "p1"}

    def fetchall(self):
        return []


def _patched(payload: dict) -> dict:
    """前端载荷 → 路由整形 → update_product 真写的那几列(全程真件)。"""
    fields = _patch_fields(ProductUpdate(**payload), NULLABLE_FIELDS)
    cur = _Cursor()
    update_product(cur, tenant_id="t1", workspace_client_id=1, product_id="p1", fields=fields)
    sql, params = cur.calls[0]
    return _sets_of(sql, params)


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class QuickCreatePriceTests(unittest.TestCase):
    """P0-① · 只填名字建出来的货,不许在收银台按 ฿0 卖出去。"""

    @classmethod
    def setUpClass(cls):
        # 只填名字,价格框一个字没打 —— 招牌流程本来的样子
        cls.blank = _payload(QUICK_CREATE % (CODE13, ""))
        # 人自己打了个 0:那是人做的决定(小票上看得见),不该被前端悄悄改写成"没设价"
        cls.zero = _payload(
            QUICK_CREATE % (CODE13, "document.getElementById('sx-pf-price').value = '0';")
        )

    def test_blank_price_is_sent_as_null_not_zero(self):
        # 老行为:Number('') || 0 → 0,后端存 0.00,从此分不出"忘了填"和"真的免费"
        self.assertIsNone(self.blank["unit_price"], "价格框留空却发了个价出去")
        # 键必须发出去(PATCH 侧按 exclude_unset 分"没改"和"改成空",不发就是不改)
        self.assertIn("unit_price", self.blank)

    def test_typed_zero_stays_zero(self):
        self.assertEqual(self.zero["unit_price"], 0, "人自己打的 0 被前端改写了")

    def test_that_payload_is_refused_by_the_till(self):
        """载荷原样走真下发整形 → 真收银台:这件货必须加不进车,并且说清是哪个单位没价。"""
        item = _catalog_price(self.blank["unit_price"])
        self.assertIsNone(item["units"][0]["price"], "下发到收银台时又变回有价了")
        got = _till(item)
        self.assertEqual(
            got["refused"], {"key": "posui.cart.unit_no_price", "unit": "ขวด"}, "฿0 的货进车了"
        )
        self.assertIn("ขวด", got["said"])
        self.assertNotIn("posui.", got["said"], "拒收卡把 i18n key 念出来了")

    def test_zero_would_have_walked_straight_into_the_cart(self):
        """反面对照:同一条链路喂 0,零元闸完全不出声 —— 所以这条必须在表单那头就堵住。"""
        item = _catalog_price(0)
        self.assertEqual(item["units"][0]["price"], "0.00")
        self.assertIsNone(_till(item)["refused"], "闸居然拦住了 0?那前端这条修复的前提就变了")

    def test_price_column_says_no_price_instead_of_zero(self):
        """后台列表也不许把"没设价"画成 ฿0.00 —— 老板照着那一列定价就再也发现不了。"""
        res = run("""
        window.PearnlyScanWedge = { register: () => () => {} };
        loadProducts();
        (async () => {
            makeEl('page-sales-products');
            apiGet = async () => ({ products: [
                { id: 'p1', name_th: 'ไม่มีราคา', unit_price: null, vat_applicable: true },
                { id: 'p2', name_th: 'มีราคา', unit_price: 15, vat_applicable: true },
            ] });
            window.loadSalesProducts();
            await tick();
            out({ html: document.getElementById('sx-p-body').innerHTML });
        })();
        """)
        self.assertIn("sx-p-noprice", res["html"], "没设价被画成了金额")
        self.assertNotIn("0.00", res["html"])
        self.assertIn("15.00", res["html"], "有价的那件也被画成「没设价」了")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class ProductReferenceCostFormTests(unittest.TestCase):
    def _open_and_save(self, visible: bool) -> dict:
        return run(f"""
window.PearnlyScanWedge = {{ register: () => () => {{}} }};
apiGet = async () => ({{ products: [], cost_visible: {str(visible).lower()} }});
answer = (url, opts) => opts && opts.method === 'POST'
    ? reply({{ ok: true, product: {{}} }})
    : reply({{ detail: 'sales.product_not_found' }}, 404);
loadProducts();
(async () => {{
    window.openProductFormWithBarcode('{CODE13}', {{ overlay: true }});
    await tick(); await tick();
    const cost = document.getElementById('sx-pf-cost');
    document.getElementById('sx-pf-th').value = 'น้ำ';
    if (cost) cost.value = '9.75';
    await document.getElementById('sx-p-save').onclick();
    await tick();
    const wrote = calls.filter((c) => c.method === 'POST')[0] || null;
    out({{ costField: !!cost, body: wrote && wrote.body }});
}})();
""")

    def test_authorized_form_sends_reference_cost(self):
        got = self._open_and_save(True)
        self.assertTrue(got["costField"])
        self.assertEqual(got["body"]["default_cost"], 9.75)

    def test_unauthorized_form_neither_shows_nor_sends_cost(self):
        got = self._open_and_save(False)
        self.assertFalse(got["costField"])
        self.assertNotIn("default_cost", got["body"])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端链路测试")
class ClearFieldTests(unittest.TestCase):
    """P1-⑪ · 表单里清掉的东西,要真的清得掉(条码撞了才有出路;价格填错了才改得回)。"""

    OTHER = {"id": "p-cola", "name_th": "โค้ก", "barcode": CODE13, "unit_price": 15}

    @classmethod
    def setUpClass(cls):
        clear = (
            "document.getElementById('sx-pf-barcode').value = '';"
            "document.getElementById('sx-pf-price').value = '';"
        )
        cls.res = run(EDIT_THEN_CLEAR % (_js(cls.OTHER), CODE13, clear))
        assert cls.res["body"] is not None, "改档一次都没写出去 · 场景没跑通"
        # 只改名字、别的一个字没动:每次都发齐全部键的代价是"没动过的也会被写回",
        # 写回的值必须还是原值,不然改个错别字就把码和价一起冲了。
        rename = "document.getElementById('sx-pf-th').value = 'โค้ก ใหม่';"
        cls.renamed = run(EDIT_THEN_CLEAR % (_js(cls.OTHER), CODE13, rename))["body"]

    def test_editing_only_the_name_keeps_code_and_price(self):
        self.assertEqual(self.renamed["name_th"], "โค้ก ใหม่")
        self.assertEqual(self.renamed["barcode"], CODE13, "只改了名字,条码被冲掉了")
        self.assertEqual(self.renamed["unit_price"], 15, "只改了名字,售价被冲掉了")

    def test_the_form_really_opened_on_that_product(self):
        # 断言的前提得先立住:编辑态里确实有码有价,清空才有意义
        self.assertEqual(self.res["before"], {"barcode": CODE13, "price": "15"})

    def test_cleared_fields_are_sent_as_explicit_null(self):
        body = self.res["body"]
        for key in ("barcode", "unit_price"):
            self.assertIn(key, body, f"{key} 清空后干脆不发了 · 后端只会当成没改")
            self.assertIsNone(body[key], f"{key} 清空后发的不是 null")

    def test_that_payload_writes_null_into_the_columns(self):
        """载荷原样走真路由整形 + 真 SQL 拼装:UPDATE 必须真把这两列写成 NULL。"""
        sets = _patched(self.res["body"])
        # 老后端 `if v is not None` 把 null 滤掉 → 这两列根本不在 SET 里,却回 ok:true
        for key in ("barcode", "unit_price"):
            self.assertIn(key, sets, f"{key} 没进 UPDATE · 「已保存」是假的")
            self.assertIsNone(sets[key], f"{key} 没被写成 NULL")

    def test_untouched_fields_are_not_wiped(self):
        """名字还在框里,不许因为"发了全部键"就把没动过的东西一起冲掉。"""
        sets = _patched(self.res["body"])
        self.assertEqual(sets.get("name_th"), "โค้ก")


class RejectCardCopyTests(unittest.TestCase):
    """P1-⑩ · 拒收卡不许把店主指到一个不存在的菜单上。"""

    # 后台到底有没有维护单位(箱/瓶)的界面 —— 由"有没有人调过那个接口"这个事实定,
    # 不由测试自己的印象定;将来真做出来了,这条闸自己就松开。
    UNITS_PATHS = {"zh": "单位", "en": "Units", "th": "หน่วย", "ja": "単位"}

    @classmethod
    def setUpClass(cls):
        cls.calls_units_api = any(
            "/units" in p.read_text(encoding="utf-8") for p in HOME_SRC.glob("*.ts")
        )
        cls.hints = _till(_catalog_price(None))["hints"] if shutil.which("node") else {}

    @unittest.skipUnless(shutil.which("node"), "node 不可用")
    def test_hint_does_not_point_at_a_screen_that_does_not_exist(self):
        if self.calls_units_api:
            self.skipTest("后台已经有维护单位的界面了 · 这条闸不再适用")
        for lang, word in self.UNITS_PATHS.items():
            with self.subTest(lang=lang):
                self.assertTrue(self.hints.get(lang), f"{lang} 少了这条指路文案")
                # 「→ 单位」这种箭头路径 = 在教人点菜单;后台根本没有那一项
                self.assertNotRegex(
                    self.hints[lang],
                    rf"→\s*{re.escape(word)}",
                    f"{lang} 还在指向不存在的「…→ {word}」菜单",
                )


if __name__ == "__main__":
    unittest.main()
