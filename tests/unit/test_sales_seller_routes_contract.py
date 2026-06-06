# -*- coding: utf-8 -*-
"""销项 PO-6 · 开票方资料路由契约 + DAL 租户隔离守门。"""

import unittest

from routes.sales_seller_routes import router
from services.sales import seller_profile

EXPECTED = {
    ("GET", "/api/sales/sellers"),
    ("GET", "/api/sales/sellers/{workspace_client_id}"),
    ("PUT", "/api/sales/sellers/{workspace_client_id}"),
}

ROW = {
    "id": 1,
    "name": "บริษัท",
    "tax_id": "0105551234567",
    "address": "addr",
    "branch": "สำนักงานใหญ่",
    "phone": "02",
    "vat_registered": True,
}


class FakeCursor:
    def __init__(self, fetchone=None, fetchall=None):
        self.calls = []
        self._one = fetchone
        self._all = fetchall or []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all

    @property
    def last(self):
        return self.calls[-1]


class SellerRoutesContractTests(unittest.TestCase):
    def test_router_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for _m, p in EXPECTED:
            self.assertIn(p, paths)


class SellerDalTests(unittest.TestCase):
    def test_get_and_list_scope_tenant(self):
        for fn in (
            lambda c: seller_profile.get_seller(c, tenant_id="t", workspace_client_id=1),
            lambda c: seller_profile.list_sellers(c, tenant_id="t"),
            lambda c: seller_profile.get_buyer(c, tenant_id="t", client_id=1),
        ):
            cur = FakeCursor(fetchone=ROW, fetchall=[ROW])
            fn(cur)
            self.assertIn(
                "tenant_id=%s", cur.last[0].replace(" ", "").replace("tenant_id =", "tenant_id=")
            )
            self.assertIn("t", cur.last[1])

    def test_set_seller_updates_whitelisted_only(self):
        cur = FakeCursor(fetchone=ROW)
        seller_profile.set_seller(
            cur,
            tenant_id="t",
            workspace_client_id=1,
            fields={"address": "X", "branch": "สาขา 1", "evil": "DROP"},
        )
        sql = cur.last[0]
        self.assertIn("UPDATE workspace_clients", sql)
        self.assertIn("address=%s", sql)
        self.assertNotIn("evil", sql)


if __name__ == "__main__":
    unittest.main()
