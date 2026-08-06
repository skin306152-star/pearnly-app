# -*- coding: utf-8 -*-
"""客户税务画像 DAL 单测(services/workspace/tax_profile_store.py · B2-b)。

钉死:①跨租户隔离(A 读不到 B 的画像) ②upsert 幂等(同客户不建两行) ③部分更新
不清空其它字段 ④vat_credit_carry Decimal 往返精度不丢 ⑤画像不存在时的默认形状
与表 DEFAULT 一致 ⑥非法枚举值拒绝(不吞不猜)。FakeCursor 只录 INSERT 的列/参数 +
模拟 workspace_clients/client_tax_profiles 两张内存表,不连真库(CI 无 DB)。
"""

import unittest
from decimal import Decimal

from services.workspace import tax_profile_store as store

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"


class FakeCursor:
    """够用的假游标:workspace_clients + client_tax_profiles 两张内存表。"""

    def __init__(self):
        self.clients: dict = {}  # (tenant_id, ws_id) -> {"vat_registered": bool, "branch": str}
        self.profiles: dict = {}  # (tenant_id, ws_id) -> {field: value}
        self.calls: list = []
        self._one = None

    def add_client(self, tenant_id, ws_id, *, vat_registered=True, branch="สำนักงานใหญ่"):
        self.clients[(tenant_id, ws_id)] = {"vat_registered": vat_registered, "branch": branch}

    def execute(self, sql, params):
        self.calls.append((sql, params))
        s = " ".join(sql.split())
        if s.startswith("SELECT wc.vat_registered"):
            tenant_id, ws_id = params
            client = self.clients.get((tenant_id, ws_id))
            if client is None:
                self._one = None
                return
            profile = self.profiles.get((tenant_id, ws_id), {})
            row = {"vat_registered": client["vat_registered"], "ws_branch": client["branch"]}
            row["field_meta"] = profile.get("field_meta")
            row.update({f: profile.get(f) for f in store._MUTABLE_FIELDS})
            self._one = row
        elif s.startswith("INSERT INTO client_tax_profiles"):
            columns = sql.split("(", 1)[1].split(")", 1)[0]
            columns = [c.strip() for c in columns.split(",")]
            values = dict(zip(columns, params))
            key = (values["tenant_id"], values["workspace_client_id"])
            row = self.profiles.setdefault(key, {})
            # field_meta 走 SQL `||` 合并(逐字段替换顶层键),不是整列覆盖——假游标须
            # 真的模拟这一步,否则测不出"没被这次改动碰到的字段原样留着"这条契约。
            field_meta_delta = values.pop("field_meta", None)
            row.update(
                {k: v for k, v in values.items() if k not in ("tenant_id", "workspace_client_id")}
            )
            if field_meta_delta is not None:
                delta = getattr(field_meta_delta, "adapted", field_meta_delta)
                merged = dict(row.get("field_meta") or {})
                merged.update(delta)
                row["field_meta"] = merged
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchone(self):
        return self._one


class GetProfileTests(unittest.TestCase):
    def test_missing_client_for_tenant_returns_none(self):
        cur = FakeCursor()
        cur.add_client(TENANT_B, 94)
        self.assertIsNone(store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=94))

    def test_cross_tenant_isolation_a_cannot_read_b_profile(self):
        cur = FakeCursor()
        cur.add_client(TENANT_B, 94)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_B,
            workspace_client_id=94,
            updated_by="acct-b",
            has_employees="yes",
        )
        self.assertIsNone(store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=94))
        got_b = store.get_profile(cur, tenant_id=TENANT_B, workspace_client_id=94)
        self.assertEqual(got_b["has_employees"], "yes")

    def test_default_profile_shape_matches_table_default(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 1, vat_registered=True, branch="สำนักงานใหญ่")
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=1)
        self.assertEqual(got["vat_status"], "registered")
        self.assertEqual(got["branch"], "สำนักงานใหญ่")
        for field, default in store._ROW_DEFAULTS.items():
            self.assertEqual(got[field], default, f"field {field} default mismatch")

    def test_vat_status_derives_from_workspace_clients_vat_registered(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 2, vat_registered=False, branch="สาขา 1")
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=2)
        self.assertEqual(got["vat_status"], "unregistered")
        self.assertEqual(got["branch"], "สาขา 1")


class UpsertProfileTests(unittest.TestCase):
    def test_idempotent_same_client_does_not_create_second_row(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 5)
        store.upsert_profile(
            cur, tenant_id=TENANT_A, workspace_client_id=5, updated_by="u1", has_employees="yes"
        )
        store.upsert_profile(
            cur, tenant_id=TENANT_A, workspace_client_id=5, updated_by="u1", has_employees="no"
        )
        self.assertEqual(len(cur.profiles), 1)
        self.assertEqual(cur.profiles[(TENANT_A, 5)]["has_employees"], "no")

    def test_partial_update_does_not_clear_other_fields(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 6)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=6,
            updated_by="u1",
            has_employees="yes",
            pays_juristic="yes",
        )
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=6,
            updated_by="u1",
            pays_juristic="no",
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=6)
        self.assertEqual(got["has_employees"], "yes")
        self.assertEqual(got["pays_juristic"], "no")

    def test_decimal_round_trip_preserves_precision(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 7)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=7,
            updated_by="u1",
            vat_credit_carry="1234.56",
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=7)
        self.assertIsInstance(got["vat_credit_carry"], Decimal)
        self.assertEqual(got["vat_credit_carry"], Decimal("1234.56"))

    def test_updated_by_required(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 8)
        with self.assertRaises(store.TaxProfileError) as ctx:
            store.upsert_profile(
                cur, tenant_id=TENANT_A, workspace_client_id=8, updated_by="", has_employees="yes"
            )
        self.assertEqual(ctx.exception.code, "updated_by_required")

    def test_invalid_enum_value_rejected(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 9)
        with self.assertRaises(store.TaxProfileError) as ctx:
            store.upsert_profile(
                cur,
                tenant_id=TENANT_A,
                workspace_client_id=9,
                updated_by="u1",
                has_employees="maybe",
            )
        self.assertEqual(ctx.exception.code, "invalid_enum_value")
        self.assertEqual(ctx.exception.field, "has_employees")
        self.assertEqual(cur.profiles, {})  # 拒绝时不落半条脏数据

    def test_invalid_decimal_rejected(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 10)
        with self.assertRaises(store.TaxProfileError) as ctx:
            store.upsert_profile(
                cur,
                tenant_id=TENANT_A,
                workspace_client_id=10,
                updated_by="u1",
                vat_credit_carry="not-a-number",
            )
        self.assertEqual(ctx.exception.code, "invalid_decimal")
        self.assertEqual(ctx.exception.field, "vat_credit_carry")

    def test_bool_and_int_fields_coerced(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 11)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=11,
            updated_by="u1",
            has_multi_branch=True,
            branch_count=3,
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=11)
        self.assertIs(got["has_multi_branch"], True)
        self.assertEqual(got["branch_count"], 3)


class FieldMetaManualStampTests(unittest.TestCase):
    """手填(upsert_profile)即时盖 field_meta 出处戳(画像卡智能判断批次)。"""

    def test_manual_write_stamps_source_and_confirmed_at(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 20)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=20,
            updated_by="acct-1",
            has_employees="yes",
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=20)
        meta = got["field_meta"]["has_employees"]
        self.assertEqual(meta["source"], "manual")
        self.assertEqual(meta["confirmed_by"], "acct-1")
        self.assertIsNotNone(meta["confirmed_at"])
        self.assertIsNone(meta["proposal"])

    def test_untouched_fields_keep_no_field_meta_entry(self):
        """只碰了 has_employees,field_meta 里不该无端多出 pays_individuals 这一条。"""
        cur = FakeCursor()
        cur.add_client(TENANT_A, 21)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=21,
            updated_by="acct-1",
            has_employees="yes",
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=21)
        self.assertNotIn("pays_individuals", got["field_meta"])

    def test_second_manual_write_does_not_erase_first_fields_meta(self):
        """两次各改一个不同字段,field_meta 须同时留着两条(JSONB `||` 只替换被点名的键)。"""
        cur = FakeCursor()
        cur.add_client(TENANT_A, 22)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=22,
            updated_by="acct-1",
            has_employees="yes",
        )
        store.upsert_profile(
            cur, tenant_id=TENANT_A, workspace_client_id=22, updated_by="acct-2", pays_juristic="no"
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=22)
        self.assertEqual(got["field_meta"]["has_employees"]["confirmed_by"], "acct-1")
        self.assertEqual(got["field_meta"]["pays_juristic"]["confirmed_by"], "acct-2")

    def test_non_tracked_kwargs_leave_no_field_meta(self):
        """source/confidence/profile_version 是画像整体的账本属性,不是某个字段的出处。"""
        cur = FakeCursor()
        cur.add_client(TENANT_A, 23)
        store.upsert_profile(
            cur, tenant_id=TENANT_A, workspace_client_id=23, updated_by="acct-1", confidence="0.9"
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=23)
        self.assertEqual(got["field_meta"], {})


class ConfirmFieldProposalsTests(unittest.TestCase):
    """推断候选转正(confirm 端点消费的落库函数)——source='inferred',值同一时刻写进本值列。"""

    def test_confirm_writes_value_and_inferred_meta(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 30)
        store.confirm_field_proposals(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=30,
            updated_by="acct-1",
            proposals={
                "pays_individuals": {
                    "value": "yes",
                    "confidence": "high",
                    "evidence": "pays_individuals:hit:3:2569-07",
                }
            },
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=30)
        self.assertEqual(got["pays_individuals"], "yes")
        meta = got["field_meta"]["pays_individuals"]
        self.assertEqual(meta["source"], "inferred")
        self.assertEqual(meta["confidence"], "high")
        self.assertEqual(meta["evidence"], "pays_individuals:hit:3:2569-07")
        self.assertIsNone(meta["proposal"])

    def test_empty_proposals_is_noop(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 31)
        store.confirm_field_proposals(
            cur, tenant_id=TENANT_A, workspace_client_id=31, updated_by="acct-1", proposals={}
        )
        self.assertEqual(cur.calls, [])

    def test_missing_updated_by_rejected(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 32)
        with self.assertRaises(store.TaxProfileError) as ctx:
            store.confirm_field_proposals(
                cur,
                tenant_id=TENANT_A,
                workspace_client_id=32,
                updated_by="",
                proposals={"pays_individuals": {"value": "yes"}},
            )
        self.assertEqual(ctx.exception.code, "updated_by_required")

    def test_invalid_enum_value_rejected(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 33)
        with self.assertRaises(store.TaxProfileError):
            store.confirm_field_proposals(
                cur,
                tenant_id=TENANT_A,
                workspace_client_id=33,
                updated_by="acct-1",
                proposals={"pays_individuals": {"value": "maybe"}},
            )

    def test_confirm_does_not_clobber_other_confirmed_field(self):
        cur = FakeCursor()
        cur.add_client(TENANT_A, 34)
        store.upsert_profile(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=34,
            updated_by="acct-1",
            has_employees="yes",
        )
        store.confirm_field_proposals(
            cur,
            tenant_id=TENANT_A,
            workspace_client_id=34,
            updated_by="acct-1",
            proposals={"pays_individuals": {"value": "yes", "confidence": "high", "evidence": "e"}},
        )
        got = store.get_profile(cur, tenant_id=TENANT_A, workspace_client_id=34)
        self.assertEqual(got["field_meta"]["has_employees"]["source"], "manual")
        self.assertEqual(got["field_meta"]["pays_individuals"]["source"], "inferred")


class _DefsFakeCursor:
    """load_active_defs 只读一张全租户共享的参考表,不需要 workspace_clients 夹具。"""

    def __init__(self, rows):
        self._rows = rows
        self.calls: list = []

    def execute(self, sql, params=()):
        self.calls.append((" ".join(sql.split()), params))

    def fetchall(self):
        return self._rows


class LoadActiveDefsTests(unittest.TestCase):
    """义务生成引擎(B2-d)的 defs 读侧:tax_obligation_defs 无 tenant_id 列(方案 §5.4
    全租户共享法定常量),SQL 天生不带 tenant_id——不属于 services/workorder 的隔离机械闸
    (test_workorder_sql_isolation)管辖范围,故放画像域而非 obligation_engine.py。"""

    def test_maps_rows_by_obligation_code(self):
        cur = _DefsFakeCursor(
            [
                {
                    "obligation_code": "pnd1",
                    "trigger_kind": "has_employees",
                    "due_paper_day": 7,
                    "due_efiling_day": 15,
                    "sso_epayment_extra_workdays": 0,
                    "effective_from": "2024-02-01",
                    "effective_to": None,
                },
            ]
        )
        defs = store.load_active_defs(cur)
        self.assertEqual(set(defs), {"pnd1"})
        self.assertEqual(defs["pnd1"]["due_paper_day"], 7)
        self.assertEqual(defs["pnd1"]["trigger_kind"], "has_employees")

    def test_query_carries_no_tenant_filter_by_design(self):
        cur = _DefsFakeCursor([])
        store.load_active_defs(cur)
        sql, params = cur.calls[0]
        self.assertNotIn("tenant_id", sql.lower())
        self.assertEqual(params, ())

    def test_empty_table_returns_empty_dict(self):
        self.assertEqual(store.load_active_defs(_DefsFakeCursor([])), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
