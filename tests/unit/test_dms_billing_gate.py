# -*- coding: utf-8 -*-
"""DMS 身份证 OCR 余额闸契约(铁律 #26)。

锁:_ocr_id_card 在做 OCR/扣费之前必须过 get_billing_status_combined —— 余额不足且
非豁免 → 402 拦下,绝不先识别再扣成负;放行/豁免才继续。回归防护此前缺闸的洞。
"""

import asyncio
import unittest
from unittest import mock

import routes.dms_routes as dms


class _FakeUpload:
    def __init__(self, content=b"\x89PNG\r\n", content_type="image/png", filename="id.png"):
        self._content = content
        self.content_type = content_type
        self.filename = filename

    async def read(self):
        return self._content


_USER = {"id": "u-1", "tenant_id": "11111111-1111-1111-1111-111111111111"}
_EP = {"id": "ep-1", "adapter": "mrerp_dms", "enabled": True}


def _run(coro):
    # 自带事件循环 · 不依赖全局 loop(全量发现时别的测试可能已关闭它)。
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class DmsBillingGateTest(unittest.TestCase):
    def setUp(self):
        self._ep_patch = mock.patch.object(dms, "_resolve_dms_endpoint", return_value=_EP)
        self._ep_patch.start()
        self.addCleanup(self._ep_patch.stop)

    def test_insufficient_balance_blocks_before_ocr(self):
        """余额不足且非豁免 → 402 · 不调 OCR、不扣费。"""
        bill = {
            "allowed": False,
            "is_exempt": False,
            "balance_thb": 0.0,
            "pages_used_this_month": 5,
        }
        with (
            mock.patch.object(dms.db, "get_billing_status_combined", return_value=bill),
            mock.patch.object(dms.db, "estimate_pdf_cost_thb", return_value=1.5),
            mock.patch.object(dms.db, "charge_ocr_async") as charge,
            mock.patch("services.ocr.id_card_extract.extract_thai_id_card") as extract,
        ):
            with self.assertRaises(dms.HTTPException) as ctx:
                _run(dms._ocr_id_card(object(), _FakeUpload(), None, _USER))
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(ctx.exception.detail["code"], "insufficient_balance")
        extract.assert_not_called()  # 没有识别
        charge.assert_not_called()  # 没有扣费

    def test_exempt_passes_even_when_not_allowed(self):
        """豁免账号 → 即便 allowed=False 也放行(不被闸挡)。"""
        bill = {"allowed": False, "is_exempt": True, "balance_thb": 0.0, "pages_used_this_month": 0}
        ocr_out = {"needs_review": False, "missing_fields": [], "id_card": {"first_name": "a"}}
        with (
            mock.patch.object(dms.db, "get_billing_status_combined", return_value=bill),
            mock.patch.object(dms.db, "charge_ocr_async"),
            mock.patch("services.ocr.id_card_extract.extract_thai_id_card", return_value=ocr_out),
        ):
            ep, ocr, _ms = _run(dms._ocr_id_card(object(), _FakeUpload(), None, _USER))
        self.assertEqual(ep, _EP)
        self.assertEqual(ocr, ocr_out)

    def test_allowed_passes_to_ocr(self):
        """余额充足 → 过闸继续 OCR。"""
        bill = {
            "allowed": True,
            "is_exempt": False,
            "balance_thb": 99.0,
            "pages_used_this_month": 1,
        }
        ocr_out = {"needs_review": False, "missing_fields": [], "id_card": {"first_name": "b"}}
        with (
            mock.patch.object(dms.db, "get_billing_status_combined", return_value=bill),
            mock.patch.object(dms.db, "charge_ocr_async"),
            mock.patch("services.ocr.id_card_extract.extract_thai_id_card", return_value=ocr_out),
        ):
            ep, ocr, _ms = _run(dms._ocr_id_card(object(), _FakeUpload(), None, _USER))
        self.assertEqual(ocr, ocr_out)


if __name__ == "__main__":
    unittest.main()
