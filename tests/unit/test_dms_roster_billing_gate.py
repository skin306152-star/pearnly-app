# -*- coding: utf-8 -*-
"""操作员计费守门契约(波3 · DL-8 · C7)。

架构拍板核心:操作员 = 老板租户下的 member 用户,身份证 OCR 的计费/余额闸命中的必须是
【租户级】余额(老板钱包),不因 role='member' 走别的口径。本测证 recognize_id_card 对 member
操作员用户仍以 _tid(user)=其租户(=老板租户)查 get_billing_status_combined + charge_ocr_async。
照 test_dms_billing_gate.py 范式(patch 落服务模块)。
"""

import asyncio
import unittest
from unittest import mock

import routes.dms_routes as dms
from services.erp import dms_id_ocr as svc

OWNER_TENANT = "11111111-1111-1111-1111-111111111111"
# 操作员:member 角色 · tenant_id 指向老板租户(erp_endpoints/billing 全按 user_id/tenant_id)。
_OPERATOR = {"id": "op-1", "tenant_id": OWNER_TENANT, "role": "member"}
_EP = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": True}


class _FakeUpload:
    def __init__(self, content=b"\x89PNG\r\n", content_type="image/png", filename="id.png"):
        self._content = content
        self.content_type = content_type
        self.filename = filename

    async def read(self):
        return self._content


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class OperatorBillingTenantScopedTest(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(svc, "resolve_dms_endpoint", return_value=_EP)
        p.start()
        self.addCleanup(p.stop)

    def test_member_operator_bills_tenant_wallet(self):
        ocr_out = {"needs_review": False, "missing_fields": [], "id_card": {"first_name": "a"}}
        bill = {"allowed": True, "is_exempt": False, "balance_thb": 99.0, "pages_used_this_month": 1}
        with (
            mock.patch.object(svc.db, "get_billing_status_combined", return_value=bill) as gate,
            mock.patch.object(svc.db, "charge_ocr_async") as charge,
            mock.patch("services.ocr.id_card_extract.extract_thai_id_card", return_value=ocr_out),
        ):
            _run(dms._ocr_id_card(object(), _FakeUpload(), None, _OPERATOR))

        # 余额闸按 (user_id, tenant_id) 查 —— tenant_id 必须是操作员租户(=老板钱包),与 role 无关。
        gate.assert_called_once()
        self.assertEqual(gate.call_args.args[0], "op-1")
        self.assertEqual(gate.call_args.args[1], OWNER_TENANT)
        # 扣费同样落租户维度(charge_ocr_async 第 2 位参数 = tenant_id)。
        charge.assert_called_once()
        self.assertEqual(charge.call_args.args[1], OWNER_TENANT)


if __name__ == "__main__":
    unittest.main()
