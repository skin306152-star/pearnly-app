# -*- coding: utf-8 -*-
"""别名 DAL 单测(services/workspace/client_alias_store.py · B2-c 污染闸主线)。

覆盖污染闸(方案 §4.6):闸1 同租户重复 norm 拒、闸2 泛词/过短拒、闸3 resolve 只吐
human_confirmed(ai_suggested 不进锚) + CRUD 归一/软删/幂等。用假游标,零 DB 依赖。
"""

import unittest

from services.workspace import client_alias_store as store
from services.workspace.client_alias_store import AliasError

TENANT = "t-1"
WC_A = 94
WC_B = 77


class _FakeCur:
    """client_name_aliases 内存表 + workspace_clients name 映射的假游标(逐句判 SQL 分支)。"""

    def __init__(self, names=None):
        self.rows: list[dict] = []
        self.names = dict(names or {})
        self._seq = 0
        self._res: list = []
        self.rowcount = 0

    def execute(self, sql, params):
        s = " ".join(sql.split())
        if s.startswith("SELECT workspace_client_id FROM client_name_aliases"):
            tenant, norm = params
            self._res = [
                {"workspace_client_id": r["workspace_client_id"]}
                for r in self.rows
                if r["tenant_id"] == tenant and r["alias_norm"] == norm and r["is_active"]
            ][:1]
        elif s.startswith("SELECT id FROM client_name_aliases"):
            tenant, ws, norm = params
            self._res = [
                {"id": r["id"]}
                for r in self.rows
                if r["tenant_id"] == tenant
                and r["workspace_client_id"] == ws
                and r["alias_norm"] == norm
                and r["is_active"]
            ][:1]
        elif s.startswith("INSERT INTO client_name_aliases"):
            tenant, ws, raw, norm, kind, mode, source, conf = params
            self._seq += 1
            self.rows.append(
                {
                    "id": self._seq,
                    "tenant_id": tenant,
                    "workspace_client_id": ws,
                    "alias_raw": raw,
                    "alias_norm": norm,
                    "alias_kind": kind,
                    "match_mode": mode,
                    "source": source,
                    "confidence": conf,
                    "is_active": True,
                }
            )
            self._res = [{"id": self._seq}]
        elif s.startswith("UPDATE client_name_aliases SET is_active = FALSE"):
            tenant, alias_id = params
            self.rowcount = 0
            for r in self.rows:
                if r["tenant_id"] == tenant and r["id"] == alias_id and r["is_active"]:
                    r["is_active"] = False
                    self.rowcount = 1
        elif s.startswith("SELECT id, alias_raw, alias_norm"):
            tenant, ws = params
            active_only = "AND is_active = TRUE" in s
            self._res = [
                dict(r)
                for r in self.rows
                if r["tenant_id"] == tenant
                and r["workspace_client_id"] == ws
                and (r["is_active"] or not active_only)
            ]
        elif s.startswith("SELECT name FROM workspace_clients"):
            ws, tenant = params
            name = self.names.get((tenant, ws))
            self._res = [{"name": name}] if name is not None else []
        elif s.startswith("SELECT alias_raw, match_mode FROM client_name_aliases"):
            tenant, ws, sources = params
            self._res = [
                {"alias_raw": r["alias_raw"], "match_mode": r["match_mode"]}
                for r in self.rows
                if r["tenant_id"] == tenant
                and r["workspace_client_id"] == ws
                and r["is_active"]
                and r["source"] in sources
            ]
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchone(self):
        return self._res[0] if self._res else None

    def fetchall(self):
        return list(self._res)


class AddAliasGateTests(unittest.TestCase):
    def test_normalizes_raw_into_alias_norm(self):
        cur = _FakeCur()
        store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup")
        self.assertEqual(cur.rows[0]["alias_norm"], "sistermakeup")
        self.assertEqual(cur.rows[0]["alias_raw"], "Sister Makeup")

    def test_duplicate_active_norm_by_other_client_rejected(self):
        # 闸1:同租户一个 active norm 只能指一个客户,第二客户认领 → 结构化拒绝,不静默二选一。
        cur = _FakeCur()
        store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup")
        with self.assertRaises(AliasError) as ctx:
            store.add_alias(
                cur, tenant_id=TENANT, workspace_client_id=WC_B, alias_raw="sister  makeup"
            )
        self.assertEqual(ctx.exception.code, store.ERR_ALIAS_NORM_CONFLICT)

    def test_same_client_reclaim_is_idempotent(self):
        cur = _FakeCur()
        first = store.add_alias(
            cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup"
        )
        again = store.add_alias(
            cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="SISTER MAKEUP"
        )
        self.assertEqual(first, again)
        self.assertEqual(len(cur.rows), 1)

    def test_generic_stopword_rejected(self):
        # 闸2:归一后落到纯泛词 → 拒(会扫中无关票)。
        cur = _FakeCur()
        for word in ("shop", "Makeup", "ร้าน"):
            with self.assertRaises(AliasError) as ctx:
                store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw=word)
            self.assertEqual(ctx.exception.code, store.ERR_ALIAS_GENERIC_TERM)

    def test_too_short_norm_rejected(self):
        cur = _FakeCur()
        with self.assertRaises(AliasError) as ctx:
            store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="ab")
        self.assertEqual(ctx.exception.code, store.ERR_ALIAS_TOO_SHORT)

    def test_substring_mode_requires_min_six(self):
        cur = _FakeCur()
        with self.assertRaises(AliasError) as ctx:
            store.add_alias(
                cur,
                tenant_id=TENANT,
                workspace_client_id=WC_A,
                alias_raw="abcd",
                match_mode="substring",
            )
        self.assertEqual(ctx.exception.code, store.ERR_ALIAS_SUBSTRING_TOO_SHORT)
        # exact 模式同样 4 字 → 放行(substring 门槛更高才是差异点)。
        self.assertIsNotNone(
            store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="abcd")
        )

    def test_empty_after_normalization_is_noop(self):
        cur = _FakeCur()
        # 纯法人前后缀 → 归一后空 → no-op(不落库、不 raise)。
        self.assertIsNone(
            store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="บริษัท")
        )
        self.assertEqual(cur.rows, [])


class ResolveNamesTests(unittest.TestCase):
    def test_resolve_returns_legal_plus_human_confirmed_aliases(self):
        cur = _FakeCur(names={(TENANT, WC_A): "บริษัท ซิสเตอร์ เมคอัพ จำกัด"})
        store.add_alias(
            cur,
            tenant_id=TENANT,
            workspace_client_id=WC_A,
            alias_raw="Sister Makeup",
            match_mode="exact",
            source="human_confirmed",
        )
        entries = store.resolve_names(cur, tenant_id=TENANT, workspace_client_id=WC_A)
        self.assertEqual(entries[0], ("บริษัท ซิสเตอร์ เมคอัพ จำกัด", "legal"))
        self.assertIn(("Sister Makeup", "exact"), entries)

    def test_ai_suggested_alias_not_consumed_by_resolve(self):
        # 闸3:大脑/学习得来的别名走影子,resolve 不吐 → 方向锚不消费。
        cur = _FakeCur(names={(TENANT, WC_A): "บริษัท ซิสเตอร์ เมคอัพ จำกัด"})
        store.add_alias(
            cur,
            tenant_id=TENANT,
            workspace_client_id=WC_A,
            alias_raw="Sister Cosmetics",
            source="ai_suggested",
        )
        entries = store.resolve_names(cur, tenant_id=TENANT, workspace_client_id=WC_A)
        self.assertEqual(entries, [("บริษัท ซิสเตอร์ เมคอัพ จำกัด", "legal")])

    def test_resolve_without_legal_name_still_returns_aliases(self):
        cur = _FakeCur()  # 无 workspace_clients 名
        store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup")
        entries = store.resolve_names(cur, tenant_id=TENANT, workspace_client_id=WC_A)
        self.assertEqual(entries, [("Sister Makeup", "exact")])


class DeactivateAndListTests(unittest.TestCase):
    def test_deactivate_frees_norm_for_another_client(self):
        cur = _FakeCur()
        aid = store.add_alias(
            cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup"
        )
        self.assertTrue(store.deactivate_alias(cur, tenant_id=TENANT, alias_id=aid))
        # 软删后同 norm 可被别的客户认领(闸1 只约束 active)。
        self.assertIsNotNone(
            store.add_alias(
                cur, tenant_id=TENANT, workspace_client_id=WC_B, alias_raw="Sister Makeup"
            )
        )

    def test_list_active_only_hides_soft_deleted(self):
        cur = _FakeCur()
        aid = store.add_alias(
            cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="Sister Makeup"
        )
        store.add_alias(cur, tenant_id=TENANT, workspace_client_id=WC_A, alias_raw="ซิสเตอร์เมค")
        store.deactivate_alias(cur, tenant_id=TENANT, alias_id=aid)
        active = store.list_aliases(cur, tenant_id=TENANT, workspace_client_id=WC_A)
        self.assertEqual(len(active), 1)
        allrows = store.list_aliases(
            cur, tenant_id=TENANT, workspace_client_id=WC_A, active_only=False
        )
        self.assertEqual(len(allrows), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
