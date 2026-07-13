# -*- coding: utf-8 -*-
"""H1b 路由契约 · ภ.ง.ด.1 工资预扣工具卡端点(routes/payroll_routes.py)。

锁定:①三端点按 path+method 注册且挂进 app;②pearnly_ai_m1 闸关/未登录 → 404/401
(fail-closed);③超 20MB → 413·空文件 → 400;④越权客户 → 404;⑤parse 纯读:无模板走
guess_columns,同表头命中模板直接回模板映射(不再要求人工确认);⑥commit issues 不阻断
落库,仅全过校验才点亮 pnd1 义务;⑦手工加行合并进同批校验+落库;⑧output 无数据 →
404 结构化;attach 字节与引擎 build_attachment(rows).encode('utf-8') 逐字节一致。
"""

from __future__ import annotations

import datetime as dt
import io
import unittest
from decimal import Decimal
from unittest import mock

from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from core import route_helpers
from routes import payroll_routes as pr
from routes.payroll_routes import router as payroll_router
from services.payroll import model
from services.tax import pnd1_attach

_USER = {"id": "u1", "tenant_id": "t-1"}
_CLIENT_ROW = {"id": 7, "name": "Sister Makeup", "tax_id": "0105548082417"}


def _valid_id(prefix12: str) -> str:
    total = sum(int(prefix12[i]) * (13 - i) for i in range(12))
    return prefix12 + str((11 - total % 11) % 10)


_EMP = [_valid_id(p) for p in ("365010069742", "110420000252")]


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "รหัสเงินได้",
            "ลำดับ",
            "เลข 13 หลัก",
            "คำนำหน้า",
            "ชื่อ",
            "นามสกุล",
            "วันที่จ่าย",
            "จำนวนเงิน",
            "ภาษีหัก",
            "เงื่อนไข",
        ]
    )
    ws.append(["40(1)", 1, _EMP[0], "นางสาว", "สมหญิง", "ใจดี", 31052569, 13000, 0, 1])
    ws.append(["40(1)", 2, _EMP[1], "นาย", "สมชาย", "รักงาน", 31052569, 12040, 0, 1])
    ws.append([None, None, None, None, None, None, None, 25040, None, None])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload(name="payroll.xlsx", data=None) -> UploadFile:
    return UploadFile(filename=name, file=io.BytesIO(data if data is not None else _xlsx_bytes()))


class _Cur:
    """假游标:fetchone_seq 按调用顺序弹出,fetchall 固定返回。"""

    def __init__(self, fetchone_seq=None, fetchall_return=None):
        self._fetchone_seq = list(fetchone_seq or [])
        self._fetchall_return = fetchall_return if fetchall_return is not None else []
        self.queries = []

    def execute(self, sql, params=None):
        self.queries.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._fetchone_seq.pop(0) if self._fetchone_seq else None

    def fetchall(self):
        return self._fetchall_return


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _FakeDB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return _CM(self._cur)


def _row_set(router):
    out = set()
    for r in router.routes:
        for m in getattr(r, "methods", set()) or set():
            if m in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                out.add((m, r.path))
    return out


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        self.assertEqual(
            _row_set(payroll_router),
            {
                ("POST", "/api/payroll/parse"),
                ("POST", "/api/payroll/commit"),
                ("GET", "/api/payroll/output"),
                ("GET", "/api/payroll/annual/summary"),
                ("GET", "/api/payroll/annual/output"),
            },
        )

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/payroll/parse", paths)
        self.assertIn("/api/payroll/commit", paths)
        self.assertIn("/api/payroll/output", paths)
        self.assertIn("/api/payroll/annual/summary", paths)
        self.assertIn("/api/payroll/annual/output", paths)


class _GatedCase(unittest.IsolatedAsyncioTestCase):
    def _wire(self, *, m1=True, cur=None):
        patches = [
            mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=m1),
            mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        ]
        if cur is not None:
            patches.append(mock.patch.object(pr, "db", _FakeDB(cur)))
        for p in patches:
            self.enterContext(p)


class GateTests(_GatedCase):
    async def test_m1_gate_closed_hides_parse_as_404(self):
        self._wire(m1=False)
        with self.assertRaises(HTTPException) as ctx:
            await pr.parse_endpoint(
                mock.Mock(), file=_upload(), workspace_client_id=7, period="2569-05"
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "payroll.not_found")

    async def test_m1_gate_closed_hides_output_as_404(self):
        self._wire(m1=False)
        with self.assertRaises(HTTPException) as ctx:
            await pr.output_endpoint(
                mock.Mock(), workspace_client_id=7, period="2569-05", kind="attach"
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_m1_gate_closed_hides_annual_summary_as_404(self):
        self._wire(m1=False)
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_summary_endpoint(mock.Mock(), workspace_client_id=7, tax_year="2569")
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_m1_gate_closed_hides_annual_output_as_404(self):
        self._wire(m1=False)
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_output_endpoint(
                mock.Mock(), workspace_client_id=7, tax_year="2569", kind="keying"
            )
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_unauthenticated_is_401(self):
        self.enterContext(
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                side_effect=HTTPException(401, detail="auth.missing_token"),
            )
        )
        with self.assertRaises(HTTPException) as ctx:
            await pr.parse_endpoint(
                mock.Mock(), file=_upload(), workspace_client_id=7, period="2569-05"
            )
        self.assertEqual(ctx.exception.status_code, 401)


class SizeLimitTests(_GatedCase):
    async def test_oversize_upload_is_413(self):
        self._wire(cur=_Cur())
        big = _upload(data=b"x" * (pr._MAX_BYTES + 1))
        with self.assertRaises(HTTPException) as ctx:
            await pr.parse_endpoint(mock.Mock(), file=big, workspace_client_id=7, period="2569-05")
        self.assertEqual(ctx.exception.status_code, 413)

    async def test_empty_upload_is_400(self):
        self._wire(cur=_Cur())
        with self.assertRaises(HTTPException) as ctx:
            await pr.parse_endpoint(
                mock.Mock(), file=_upload(data=b""), workspace_client_id=7, period="2569-05"
            )
        self.assertEqual(ctx.exception.status_code, 400)


class OwnershipTests(_GatedCase):
    async def test_client_not_owned_is_404(self):
        self._wire(cur=_Cur(fetchone_seq=[None]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.parse_endpoint(
                mock.Mock(), file=_upload(), workspace_client_id=9, period="2569-05"
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "payroll.client_not_found")


class ParseTests(_GatedCase):
    async def test_no_template_runs_guess(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW, None]))
        out = await pr.parse_endpoint(
            mock.Mock(), file=_upload(), workspace_client_id=7, period="2569-05"
        )
        self.assertFalse(out["template_hit"])
        self.assertEqual(out["guessed"][model.F_EMPLOYEE_ID]["column"], 2)
        self.assertEqual(out["guessed"][model.F_EMPLOYEE_ID]["confidence"], "high")
        self.assertEqual(out["guessed"][model.F_PAID_AMOUNT]["column"], 7)
        self.assertEqual(out["payer_id_candidate"], None)
        self.assertEqual(len(out["preview_rows"]), 3)
        self.assertEqual(list(model.REQUIRED_FIELDS), out["required_fields"])

    async def test_template_hit_skips_guess(self):
        template_row = {
            "column_map": {model.F_EMPLOYEE_ID: 2, model.F_PAID_AMOUNT: 7},
            "income_code": "40(1)",
            "fixed_values": {},
            "header_hash": pr._header_hash(
                [
                    "รหัสเงินได้",
                    "ลำดับ",
                    "เลข 13 หลัก",
                    "คำนำหน้า",
                    "ชื่อ",
                    "นามสกุล",
                    "วันที่จ่าย",
                    "จำนวนเงิน",
                    "ภาษีหัก",
                    "เงื่อนไข",
                ]
            ),
        }
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW, template_row]))
        out = await pr.parse_endpoint(
            mock.Mock(), file=_upload(), workspace_client_id=7, period="2569-05"
        )
        self.assertTrue(out["template_hit"])
        self.assertEqual(out["guessed"][model.F_EMPLOYEE_ID]["column"], 2)


class CommitTests(_GatedCase):
    def _column_map(self):
        return (
            '{"employee_id": 2, "title": 3, "first_name": 4, "last_name": 5, '
            '"paid_date": 6, "paid_amount": 7, "wht_amount": 8, "income_code": 0}'
        )

    async def test_clean_commit_lights_obligation(self):
        cur = _Cur(fetchone_seq=[_CLIENT_ROW])
        self._wire(cur=cur)
        self.enterContext(
            mock.patch.object(pr.obligations, "light_pnd1_obligation", return_value=True)
        )
        out = await pr.commit_endpoint(
            mock.Mock(),
            file=_upload(),
            workspace_client_id=7,
            period="2569-05",
            column_map=self._column_map(),
            fixed_values="{}",
            income_code="40(1)",
            manual_entries="[]",
        )
        self.assertEqual(out["row_count"], 2)
        self.assertEqual(out["totals"]["paid_amount"], "25040")
        self.assertEqual(out["declared_total"], "25040")
        self.assertEqual(out["issues"], [])
        pr.obligations.light_pnd1_obligation.assert_called_once()

    async def test_issues_do_not_block_persist_or_light(self):
        cur = _Cur(fetchone_seq=[_CLIENT_ROW])
        self._wire(cur=cur)
        self.enterContext(
            mock.patch.object(pr.obligations, "light_pnd1_obligation", return_value=True)
        )
        out = await pr.commit_endpoint(
            mock.Mock(),
            file=_upload(),
            workspace_client_id=7,
            period="2569-06",  # 表内支付日是 2569-05 · 触发 V2 出期 issue
            column_map=self._column_map(),
            fixed_values="{}",
            income_code="40(1)",
            manual_entries="[]",
        )
        self.assertEqual(out["row_count"], 2)  # 落库不受 issue 阻断
        self.assertTrue(out["issues"])
        pr.obligations.light_pnd1_obligation.assert_not_called()

    async def test_manual_entry_appends_row(self):
        cur = _Cur(fetchone_seq=[_CLIENT_ROW])
        self._wire(cur=cur)
        self.enterContext(
            mock.patch.object(pr.obligations, "light_pnd1_obligation", return_value=True)
        )
        manual = (
            '[{"employee_id": "%s", "title": "นาย", "first_name": "ใหม่", '
            '"last_name": "คนที่สาม", "paid_amount": "5000", "wht_amount": "0"}]'
            % _valid_id("110100234561")
        )
        out = await pr.commit_endpoint(
            mock.Mock(),
            file=_upload(),
            workspace_client_id=7,
            period="2569-05",
            column_map=self._column_map(),
            fixed_values="{}",
            income_code="40(1)",
            manual_entries=manual,
        )
        self.assertEqual(out["row_count"], 3)
        self.assertEqual(out["totals"]["paid_amount"], "30040")


class OutputTests(_GatedCase):
    async def test_no_data_is_404_structured(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=[]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.output_endpoint(
                mock.Mock(), workspace_client_id=7, period="2569-05", kind="attach"
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail["code"], "payroll.no_period_data")

    async def test_bad_kind_is_400(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.output_endpoint(
                mock.Mock(), workspace_client_id=7, period="2569-05", kind="csv"
            )
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_attach_bytes_match_engine_output_exactly(self):
        db_rows = [
            {
                "seq": 1,
                "employee_id": _EMP[0],
                "title": "นางสาว",
                "first_name": "สมหญิง",
                "last_name": "ใจดี",
                "income_code": "40(1)",
                "paid_date": dt.date(2026, 5, 31),
                "paid_amount": Decimal("13000"),
                "wht_amount": Decimal("0"),
                "condition": "1",
            }
        ]
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=db_rows))
        out = await pr.output_endpoint(
            mock.Mock(), workspace_client_id=7, period="2569-05", kind="attach"
        )
        self.assertIsInstance(out, StreamingResponse)
        body = b"".join([chunk async for chunk in out.body_iterator])
        rows = [pr._row_from_db(r) for r in db_rows]
        self.assertEqual(body, pnd1_attach.build_attachment(rows).encode("utf-8"))
        disp = out.headers["Content-Disposition"]
        self.assertIn("filename*=UTF-8''", disp)


def _annual_db_rows():
    return [
        {
            "period": "2569-05",
            "seq": 1,
            "employee_id": _EMP[0],
            "title": "นางสาว",
            "first_name": "สมหญิง",
            "last_name": "ใจดี",
            "income_code": "40(1)",
            "paid_date": dt.date(2026, 5, 31),
            "paid_amount": Decimal("13000"),
            "wht_amount": Decimal("0"),
            "condition": "1",
        },
        {
            "period": "2569-06",
            "seq": 1,
            "employee_id": _EMP[0],
            "title": "นางสาว",
            "first_name": "สมหญิง",
            "last_name": "ใจดี",
            "income_code": "40(1)",
            "paid_date": dt.date(2026, 6, 30),
            "paid_amount": Decimal("13000"),
            "wht_amount": Decimal("0"),
            "condition": "1",
        },
    ]


class AnnualSummaryTests(_GatedCase):
    async def test_no_data_is_404_structured(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=[]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_summary_endpoint(mock.Mock(), workspace_client_id=7, tax_year="2569")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail["code"], "payroll.no_year_data")

    async def test_bad_tax_year_is_400(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_summary_endpoint(mock.Mock(), workspace_client_id=7, tax_year="25a9")
        self.assertEqual(ctx.exception.status_code, 400)

    async def test_summary_aggregates_across_months(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=_annual_db_rows()))
        out = await pr.annual_summary_endpoint(mock.Mock(), workspace_client_id=7, tax_year="2569")
        self.assertEqual(out["employee_count"], 1)
        self.assertEqual(out["totals"]["paid_amount"], "26000")
        self.assertEqual(out["months_present"], ["2569-05", "2569-06"])
        self.assertEqual(out["issues"], [])
        self.assertEqual(out["upload_kinds_available"], ["keying"])


class AnnualOutputTests(_GatedCase):
    async def test_no_data_is_404_structured(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=[]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_output_endpoint(
                mock.Mock(), workspace_client_id=7, tax_year="2569", kind="keying"
            )
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail["code"], "payroll.no_year_data")

    async def test_bad_kind_is_400_honest_downgrade_message(self):
        # 有数据时 kind 非法才是 400 语义;鉴权/数据存在性检查在前(simplify 收口后
        # kind 检查挪到 _load_year_or_404 之后,无数据的 attach 请求走 404 不泄语义)。
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=_annual_db_rows()[:1]))
        with self.assertRaises(HTTPException) as ctx:
            await pr.annual_output_endpoint(
                mock.Mock(), workspace_client_id=7, tax_year="2569", kind="attach"
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail["code"], "payroll.annual_kind_not_available")

    async def test_keying_download_streams_xlsx(self):
        self._wire(cur=_Cur(fetchone_seq=[_CLIENT_ROW], fetchall_return=_annual_db_rows()[:1]))
        out = await pr.annual_output_endpoint(
            mock.Mock(), workspace_client_id=7, tax_year="2569", kind="keying"
        )
        self.assertIsInstance(out, StreamingResponse)
        self.assertEqual(out.media_type, pr._KEYING_MEDIA)
        disp = out.headers["Content-Disposition"]
        self.assertIn("filename*=UTF-8''", disp)


if __name__ == "__main__":
    unittest.main()
