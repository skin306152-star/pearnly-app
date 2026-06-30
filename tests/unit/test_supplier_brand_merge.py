# -*- coding: utf-8 -*-
"""供应商建档:已知大连锁无税号也按归一品牌键并档(治 7-Eleven/711 各建一个)。

回归锚:LINE 随手记账常无税号,"7-Eleven" 与 "711" 此前各建一个供应商。修法 = 税号没
命中时,若属已知连锁则按 canonical_merchant 复用既有;通用小店名不并(防误并不同同名店)。
"""

import unittest

from services.purchase import suppliers as sup


class _FakeCur:
    """够用的假游标:认 find_by_tax_id 的 SELECT、品牌扫描 SELECT、INSERT。"""

    def __init__(self, existing):
        self.rows = [dict(r) for r in existing]
        self._res: list = []
        self.insert_count = 0

    def execute(self, sql, params):
        s = " ".join(sql.split())
        if s.startswith("INSERT INTO suppliers"):
            row = {
                "id": "new%d" % (self.insert_count + 1),
                "name": params[2],
                "tax_id": params[3],
            }
            self.rows.append(row)
            self.insert_count += 1
            self._res = [row]
        elif "tax_id = %s" in s:  # find_by_tax_id
            tax = params[2]
            self._res = [r for r in self.rows if (r.get("tax_id") or "") == (tax or "")]
        else:  # 品牌扫描:本套账全部
            self._res = list(self.rows)

    def fetchone(self):
        return self._res[0] if self._res else None

    def fetchall(self):
        return list(self._res)


def _create(cur, name, tax_id=None):
    return sup.create_supplier(cur, tenant_id="t", workspace_client_id=1, name=name, tax_id=tax_id)


class BrandMergeTests(unittest.TestCase):
    def test_known_brand_merges_without_taxid(self):
        cur = _FakeCur([{"id": "s1", "name": "7-Eleven", "tax_id": None}])
        got = _create(cur, "711")  # 无税号、同连锁不同写法
        self.assertEqual(got["id"], "s1")  # 复用既有
        self.assertEqual(cur.insert_count, 0)  # 没新建

    def test_known_brand_no_existing_creates(self):
        cur = _FakeCur([])
        got = _create(cur, "711")
        self.assertEqual(got["id"], "new1")
        self.assertEqual(cur.insert_count, 1)

    def test_generic_name_not_merged(self):
        # 通用小店名(非已知连锁)→ 不按名并,维持各自建档(防误并两个不同的同名店)。
        cur = _FakeCur([{"id": "s1", "name": "ABC ร้านค้า", "tax_id": None}])
        got = _create(cur, "ABC ร้านค้า")
        self.assertEqual(got["id"], "new1")
        self.assertEqual(cur.insert_count, 1)

    def test_taxid_match_still_wins(self):
        cur = _FakeCur([{"id": "s1", "name": "Whatever Co", "tax_id": "0105546015062"}])
        got = _create(cur, "别的名字", tax_id="0105546015062")
        self.assertEqual(got["id"], "s1")
        self.assertEqual(cur.insert_count, 0)


if __name__ == "__main__":
    unittest.main()
