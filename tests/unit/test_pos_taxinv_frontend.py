# -*- coding: utf-8 -*-
"""POS 补开全式税票前端守门(G2 · 静态断言源文件,同 test_pos_caps_frontend 先例)。

锁定:新逻辑文件进拼包清单且顺序合法 · 视图/弹窗 DOM 落点 · 弹窗搬出 view-main
作用域(别的视图开弹窗不被 display:none 吞)· 前端 Mod-11 镜像存在 · 四语键齐。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "static/pos/pos.html").read_text("utf-8")
CSS = (ROOT / "static/pos/pos.css").read_text("utf-8")
TAXCSS = (ROOT / "static/pos/pos-taxinv.css").read_text("utf-8")
TAXINV = (ROOT / "static/pos/pos-taxinv.js").read_text("utf-8")
BUILD = (ROOT / "scripts/build-home-js.mjs").read_text("utf-8")
BUILD_CSS = (ROOT / "scripts/build-home-css.mjs").read_text("utf-8")
POSJS = (ROOT / "static/pos/pos.js").read_text("utf-8")
I18N = (ROOT / "static/pos/pos-i18n.js").read_text("utf-8")


class BundleRegistrationTests(unittest.TestCase):
    def test_taxinv_registered_between_data_and_cashier(self):
        """不进 files 数组 = 根本不进 bundle;须在 pos-data 之后、pos-cashier 之前。"""
        i_data = BUILD.index("pos/pos-data.js")
        i_taxinv = BUILD.index("pos/pos-taxinv.js")
        i_cashier = BUILD.index("pos/pos-cashier.js")
        self.assertLess(i_data, i_taxinv)
        self.assertLess(i_taxinv, i_cashier)

    def test_taxinv_css_registered_after_tokens(self):
        """pos-taxinv.css 吃 pos.css 的 :root 令牌 → 必须登记且排它之后。"""
        i_base = BUILD_CSS.index("pos/pos.css")
        i_tax = BUILD_CSS.index("pos/pos-taxinv.css")
        self.assertLess(i_base, i_tax)


class DomLayoutTests(unittest.TestCase):
    def test_view_and_entries_present(self):
        for needle in (
            'id="view-taxinv"',
            'id="cart-taxinv-btn"',
            'id="taxinv-receipt"',
            'id="taxinv-find-btn"',
            'id="taxinv-body"',
        ):
            self.assertIn(needle, HTML, needle)

    def test_tax_mask_is_js_injected_not_in_html(self):
        """弹窗由 pos-taxinv.js 注入 body(任何视图都能开):留在 view-main 里会被
        .pos-view{display:none} 吞掉(视觉上「点了没反应」)。"""
        self.assertNotIn('id="tax-mask"', HTML)
        self.assertIn("mask.id = 'tax-mask'", TAXINV)
        self.assertIn("document.body.appendChild(mask)", TAXINV)
        for mid in ("tax-lookup-btn", "tax-save-buyer", "tax-lookup-hint", "tax-taxid-bad"):
            self.assertIn(mid, TAXINV, mid)

    def test_view_registered_in_router(self):
        # VIEWS 从 DOM 派生(新增屏只写 pos.html 不用登记);taxinv 的进入钩子仍显式。
        self.assertIn("querySelectorAll('section.pos-view')", POSJS)
        self.assertIn("POS.taxinv.resetView()", POSJS)
        self.assertIn("POS.taxinv.init()", POSJS)


class CssScopeTests(unittest.TestCase):
    def test_tax_styles_scoped_to_mask_id_in_own_file(self):
        self.assertNotIn(".pos-view--main .tax-", CSS)
        self.assertNotIn("#tax-mask", CSS)  # 税票样式单一归属 pos-taxinv.css
        self.assertIn("#tax-mask.show", TAXCSS)
        self.assertIn("#tax-mask .tax-modal", TAXCSS)

    def test_taxinv_view_reuses_refund_visuals(self):
        m = re.search(r'<section class="([^"]*)" id="view-taxinv"', HTML)
        self.assertIsNotNone(m)
        self.assertIn("pos-view--refund", m.group(1))
        self.assertIn("pos-view--taxinv", m.group(1))


class ChecksumMirrorTests(unittest.TestCase):
    def test_mod11_mirror_present(self):
        """前端镜像后端 buyer.th13_checksum_ok:权重 13-i、(11-sum%11)%10。"""
        self.assertIn("function th13Ok", TAXINV)
        self.assertIn("(13 - i)", TAXINV)
        self.assertIn("(11 - (sum % 11)) % 10", TAXINV)

    def test_lookup_and_save_buyer_wired(self):
        self.assertIn("POS.data.taxLookup", TAXINV)
        self.assertIn("full-invoice-pdf", TAXINV)
        self.assertIn("tax-save-buyer", TAXINV)


class MainSiteRowActionTests(unittest.TestCase):
    """主站交易明细行内动作(工单 G2 第二入口):列 + 弹窗 + Mod-11 镜像 + 四语键。"""

    MODAL = (ROOT / "src/home/pos-taxinv-modal.ts").read_text("utf-8")
    LOG = (ROOT / "src/home/pos-sales-log.ts").read_text("utf-8")
    I18N_MAIN = (ROOT / "static/i18n-data.js").read_text("utf-8")

    def test_log_wires_taxinv_column_and_modal(self):
        self.assertIn("poslog.col_taxinv", self.LOG)
        self.assertIn("openPosTaxinvModal", self.LOG)
        self.assertIn("data-tiv-make", self.LOG)
        self.assertIn("data-tiv-open", self.LOG)
        self.assertIn("full_invoice_no", self.LOG)

    def test_modal_has_mod11_mirror_and_pos_endpoints(self):
        self.assertIn("function th13Ok", self.MODAL)
        self.assertIn("(11 - (sum % 11)) % 10", self.MODAL)
        self.assertIn("/api/pos/tax-lookup", self.MODAL)
        self.assertIn("full-tax-invoice", self.MODAL)
        self.assertIn("full-invoice-pdf", self.MODAL)
        self.assertIn("save_buyer", self.MODAL)

    def test_main_i18n_keys_four_langs(self):
        for key in (
            "poslog.col_taxinv",
            "poslog.tiv_make",
            "postax.title",
            "postax.lookup_miss",
            "postax.checksum_bad",
            "postax.save_buyer",
        ):
            self.assertEqual(self.I18N_MAIN.count(f"'{key}'"), 4, f"{key} 应四语各一份")


class I18nKeysTests(unittest.TestCase):
    def test_new_keys_exist_in_all_four_langs(self):
        keys = (
            "posui.cart.taxinv",
            "posui.taxinv.title",
            "posui.taxinv.hint",
            "posui.taxinv.issued.title",
            "posui.taxinv.reprint",
            "posui.tax.lookup",
            "posui.tax.lookup.miss",
            "posui.tax.invalid",
            "posui.tax.save_buyer",
        )
        for key in keys:
            self.assertEqual(I18N.count(f"'{key}'"), 4, f"{key} 应四语各一份")


if __name__ == "__main__":
    unittest.main()
