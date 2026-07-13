# -*- coding: utf-8 -*-
"""N1 P1-6(交付文件名=内部名,不带客户/账期)守门:GET /api/workorder/orders/{id}/
deliverables/{kind} 下载文件名从落盘内部名(如 pp30_draft.md)换成
"{客户名}_{账期}_{报表名}"(RFC 5987)。锁定:①命中时文件名带客户名+账期+泰文报表短名
②取不到客户名(边缘态)诚实退回落盘原名,不拼假名字③Content-Disposition 走
core.route_helpers.content_disposition(同 fileconv/payroll/vat_excel 既有惯例,不新起
第二套编码)。

端点定义在 routes/workorder_financials_routes.py(2026-07 交付物组并入,与月度报表下载
同文件);鉴权/归属校验(_load_order → check_workspace_scope)仍是 routes/workorder_routes.py
的原判定,故同时引入 wr 用于打那两个共享 helper 的桩。
"""

from __future__ import annotations

import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import route_helpers
from routes import workorder_financials_routes as wfr
from routes import workorder_routes as wr
from tests.unit._route_contract_fakes import FakeDB

_USER = {"id": "u1", "tenant_id": "t-1"}
_WO = {"workspace_client_id": 7, "period": "2569-06"}


class _FakeDB(FakeDB):
    """共享 FakeDB 之上补 _client_name_for_order 要的 get_workspace_client 桩。"""

    def __init__(self, client=None):
        super().__init__()
        self._client = client

    def get_workspace_client(self, workspace_client_id, user_id, tenant_id=None):
        return self._client


def _common_patches(*, db, artifact_path):
    # db 有两处独立引用需要同一个桩:wfr.db(download_deliverable 自己的 get_cursor)+
    # wr.db(_client_name_for_order 仍定义在 workorder_routes.py,拆分后各自持有独立的
    # `from core import db` 名字绑定,不是同一个可变对象)。
    return [
        mock.patch.object(route_helpers, "get_current_user_from_request", return_value=_USER),
        mock.patch.object(route_helpers, "pearnly_ai_m1_enabled_for", return_value=True),
        mock.patch.object(route_helpers, "require_perm", return_value=_USER),
        mock.patch.object(wr, "check_workspace_scope", return_value=None),
        mock.patch.object(route_helpers, "check_workspace_scope", return_value=None),
        mock.patch.object(wfr, "db", db),
        mock.patch.object(wr, "db", db),
        mock.patch.object(wr.store, "get_work_order", return_value=dict(_WO)),
        mock.patch.object(wfr.api, "deliverable_artifact_path", return_value=artifact_path),
    ]


class DownloadDeliverableFilenameTests(unittest.IsolatedAsyncioTestCase):
    async def test_filename_has_client_name_period_and_report_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pp30_draft.md"
            path.write_text("x", encoding="utf-8")
            patches = _common_patches(
                db=_FakeDB(client={"name": "Sister Makeup"}), artifact_path="pp30_draft.md"
            )
            with contextlib.ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                stack.enter_context(
                    mock.patch.object(wfr.storage, "resolve_within_order", return_value=path)
                )
                resp = await wfr.download_deliverable("wo-1", "pp30_draft", mock.Mock())
        disp = resp.headers["content-disposition"]
        self.assertIn("2569-06", disp)
        self.assertIn("filename*=UTF-8''", disp)
        # Thai report label for pp30_draft(ภ.พ.30 draft) is present, percent-encoded.
        from urllib.parse import quote

        self.assertIn(quote("แบบร่าง ภ.พ.30".encode("utf-8")), disp)

    async def test_missing_client_name_falls_back_to_original_disk_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pp30_draft.md"
            path.write_text("x", encoding="utf-8")
            patches = _common_patches(db=_FakeDB(client=None), artifact_path="pp30_draft.md")
            with contextlib.ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                stack.enter_context(
                    mock.patch.object(wfr.storage, "resolve_within_order", return_value=path)
                )
                resp = await wfr.download_deliverable("wo-1", "pp30_draft", mock.Mock())
        disp = resp.headers["content-disposition"]
        self.assertIn("pp30_draft.md", disp)
        self.assertNotIn("2569-06", disp)


if __name__ == "__main__":
    unittest.main()
