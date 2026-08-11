# -*- coding: utf-8 -*-
"""DMS 员工表取数(顾问匹配的精确层)· 被测模块 services/erp/dms_employees.py。

真机探针(测试站 2026-08-12):特意建了编号与登录名不同的员工 337 / WKC99 / wkuser99,
证明顾问下拉的 code 列是员工编号而非登录名。本测锁三件事:解析把编号与登录名分成两列
(别再拿编号当登录名);「取不到」与「员工表没人」分得开;销售账号没员工页权限时借
admin 凭据组重试,再失败才退化并留痕。
"""

import unittest
from contextlib import contextmanager

from services.erp import dms_employees


def _row_html(emp_id: str, code: str, login: str, name: str) -> str:
    """真机片段结构:data-val=员工id,块内 <p> 依次为 编号 / 登录名 / 姓名。"""
    return (
        f'<div data-val="{emp_id}" class="showdatalist">'
        '<div class="detaildata"><div>'
        f"<div><p>{code}</p><p>{login}</p></div>"
        f"<div><p>{name}</p></div>"
        "</div></div></div>"
    )


_PROBE = _row_html("337", "WKC99", "wkuser99", "WalkProbe แยกรหัส")
_BODY = "dt::" + _PROBE + _row_html("297", "SALE01", "sale01", "สมชาย")

_EMPLOYEES = [
    {"id": "337", "code": "WKC99", "login": "wkuser99", "name": "WalkProbe"},
    {"id": "297", "code": "SALE01", "login": "sale01", "name": "สมชาย"},
]


class _FakeClient:
    """鸭子类型的 DMSClient:_post_text + 懒切 admin 会话(_admin_transport/_writer_session)。

    body 为 Exception 实例即抛出(模拟 HTTP 非 200 / 会话失效);mode 记录这一发打在哪个
    会话上,好断言 admin 重试真的换了会话。
    """

    def __init__(self, user_body, *, admin_body=None, has_admin=False, admin_raises=None):
        self.user_body = user_body
        self.admin_body = admin_body
        self.admin_raises = admin_raises
        self._admin_transport = object() if (has_admin or admin_body is not None) else None
        self.mode = "user"
        self.calls = []

    def _post_text(self, path, data):
        self.calls.append((path, data, self.mode))
        body = self.admin_body if self.mode == "admin" else self.user_body
        if isinstance(body, Exception):
            raise body
        return body

    @contextmanager
    def _writer_session(self):
        if self.admin_raises is not None:
            raise self.admin_raises
        self.mode = "admin"
        try:
            yield
        finally:
            self.mode = "user"


class ParseEmployeeRowsTests(unittest.TestCase):
    def test_parses_id_code_login_name(self):
        rows = dms_employees.parse_employee_rows(_BODY)
        self.assertEqual(
            rows[0],
            {"id": "337", "code": "WKC99", "login": "wkuser99", "name": "WalkProbe แยกรหัส"},
        )
        self.assertEqual([r["id"] for r in rows], ["337", "297"])

    def test_code_and_login_stay_separate_columns(self):
        # 精确层存在的理由:这两列可以不同,混为一谈就会匹配到别人。
        row = dms_employees.parse_employee_rows("dt::" + _PROBE)[0]
        self.assertNotEqual(row["code"], row["login"])

    def test_missing_trailing_cells_are_blank_not_shifted(self):
        rows = dms_employees.parse_employee_rows(
            'dt::<div data-val="9"><div><p>C9</p><p>u9</p></div></div>'
        )
        self.assertEqual(rows[0], {"id": "9", "code": "C9", "login": "u9", "name": ""})

    def test_dash_placeholder_becomes_empty(self):
        rows = dms_employees.parse_employee_rows(_row_html("5", "C5", "u5", "-"))
        self.assertEqual(rows[0]["name"], "")

    def test_empty_body_is_empty_list_not_failure(self):
        self.assertEqual(dms_employees.parse_employee_rows(""), [])
        self.assertEqual(dms_employees.parse_employee_rows("   "), [])

    def test_listing_without_rows_is_empty_list(self):
        # 搜索无结果 / 员工表真的没人 —— 可以照常判「不在员工表」。
        self.assertEqual(dms_employees.parse_employee_rows("dt::<div>ไม่พบข้อมูล</div>"), [])

    def test_empty_result_marker_ndt_is_empty_list(self):
        # showdata 的空结果体前缀是 ndt:: 不是 dt::(见 _parse_customer_rows);
        # 认不出就会把「员工表没人」误判成「取数挂了」。
        self.assertEqual(dms_employees.parse_employee_rows("ndt::"), [])
        self.assertEqual(dms_employees.parse_employee_rows("ndt::<div>ไม่พบข้อมูล</div>"), [])

    def test_cellless_control_blocks_are_not_rows(self):
        # 结果体里并非每个 data-val 都是行(分页/表头控件也带),别把它们当员工。
        body = 'dt::<div data-val="page2" class="pagectl"></div>' + _PROBE
        rows = dms_employees.parse_employee_rows(body)
        self.assertEqual([r["id"] for r in rows], ["337"])

    def test_error_page_is_none_not_empty(self):
        # 被踢回登录页 / 500:当成 [] 会把「拿不到」误判成「这个人不存在」。
        self.assertIsNone(dms_employees.parse_employee_rows("<html><body>login</body></html>"))
        self.assertIsNone(dms_employees.parse_employee_rows("Fatal error: permission denied"))


class MatchByLoginTests(unittest.TestCase):
    def test_exact_login_hit(self):
        self.assertEqual(dms_employees.match_by_login(_EMPLOYEES, "wkuser99")["id"], "337")

    def test_case_insensitive_and_trimmed(self):
        self.assertEqual(dms_employees.match_by_login(_EMPLOYEES, "  SALE01 ")["id"], "297")

    def test_code_column_never_matches(self):
        # 拿编号当登录名匹配正是这一层要修的错配。
        self.assertIsNone(dms_employees.match_by_login(_EMPLOYEES, "WKC99"))

    def test_no_hit(self):
        self.assertIsNone(dms_employees.match_by_login(_EMPLOYEES, "nobody"))

    def test_duplicate_logins_give_up(self):
        dupes = [
            {"id": "1", "login": "same"},
            {"id": "2", "login": "SAME"},
        ]
        self.assertIsNone(dms_employees.match_by_login(dupes, "same"))

    def test_empty_inputs(self):
        self.assertIsNone(dms_employees.match_by_login(_EMPLOYEES, ""))
        self.assertIsNone(dms_employees.match_by_login(_EMPLOYEES, "   "))
        self.assertIsNone(dms_employees.match_by_login([], "sale01"))
        self.assertIsNone(dms_employees.match_by_login(None, "sale01"))


class FetchEmployeesTests(unittest.TestCase):
    def test_pulls_full_list_from_current_session(self):
        cl = _FakeClient(_BODY)
        rows = dms_employees.fetch_employees(cl)
        self.assertEqual([r["login"] for r in rows], ["wkuser99", "sale01"])
        path, body, mode = cl.calls[0]
        self.assertEqual((path, mode), ("users/component/showdata.php", "user"))
        self.assertEqual(body["sd"], "")  # 空关键词 = 取全量
        self.assertEqual(body["sdtamt"], "500")

    def test_http_failure_without_admin_degrades_with_one_warning(self):
        cl = _FakeClient(RuntimeError("users/ http=500"))
        with self.assertLogs(dms_employees.logger, "WARNING") as logs:
            self.assertIsNone(dms_employees.fetch_employees(cl))
        self.assertEqual(len(logs.output), 1)
        self.assertEqual(len(cl.calls), 1)  # 没配 admin 就别白跑第二发

    def test_admin_retry_recovers_when_sales_session_is_blocked(self):
        cl = _FakeClient(RuntimeError("users/ http=500"), admin_body=_BODY)
        rows = dms_employees.fetch_employees(cl)
        self.assertEqual([r["id"] for r in rows], ["337", "297"])
        self.assertEqual([c[2] for c in cl.calls], ["user", "admin"])
        self.assertEqual(cl.mode, "user")  # 会话必须换回来

    def test_admin_retry_also_covers_unparseable_body(self):
        # 权限不足常见形态是 200 + 登录页 HTML,不是 500。
        cl = _FakeClient("<html>login</html>", admin_body=_BODY)
        self.assertEqual(len(dms_employees.fetch_employees(cl) or []), 2)

    def test_both_sessions_failing_returns_none_with_one_warning(self):
        cl = _FakeClient(RuntimeError("boom"), admin_body=RuntimeError("boom"))
        with self.assertLogs(dms_employees.logger, "WARNING") as logs:
            self.assertIsNone(dms_employees.fetch_employees(cl))
        self.assertEqual(len(logs.output), 1)
        self.assertEqual([c[2] for c in cl.calls], ["user", "admin"])

    def test_admin_login_failure_degrades_instead_of_raising(self):
        cl = _FakeClient(RuntimeError("boom"), has_admin=True, admin_raises=RuntimeError("bad pwd"))
        with self.assertLogs(dms_employees.logger, "WARNING"):
            self.assertIsNone(dms_employees.fetch_employees(cl))

    def test_empty_roster_is_not_retried_on_admin(self):
        # [] 是确定的答案(员工表没人),不是取数失败 —— 别为它多开一个 admin 会话。
        cl = _FakeClient("dt::", admin_body=_BODY)
        self.assertEqual(dms_employees.fetch_employees(cl), [])
        self.assertEqual([c[2] for c in cl.calls], ["user"])


if __name__ == "__main__":
    unittest.main()
