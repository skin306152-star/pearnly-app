from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class PurchaseProductWiringTests(unittest.TestCase):
    def test_purchase_match_uses_live_product_catalog(self):
        text = (ROOT / "src/home/purchase-modals.ts").read_text(encoding="utf-8")
        self.assertIn("/api/sales/products?q=", text)
        self.assertNotIn("'/api/products?q=", text)


if __name__ == "__main__":
    unittest.main()
