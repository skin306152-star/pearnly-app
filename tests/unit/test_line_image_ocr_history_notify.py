# -*- coding: utf-8 -*-
"""LINE 图片 OCR 第 5 步写 history 失败时的推送诚实性(services/ocr/line_image_ocr.py)。

修复前:insert_ocr_history 抛异常 → hid=None,但照样推「✅ 识别完成 · 网页历史查看详情」,
网页历史其实没有这条记录(假成功)。修复后:hid 为空改推 save_failed 文案 + return False;
正常写库成功仍推 success_head + view_on_web(回归保护)。

真调用 _handle_line_image_ocr,只 mock 该函数的外部依赖(下载/用户查找/计费/OCR pipeline/
路由分流/推送出口),不 mock 被测的分支判断本身;断言基于真实执行后落到 push_text_context
的调用参数。"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest import mock

from services.line_binding import line_client
from services.ocr import line_image_ocr as mod
from services.ocr.line_image_route import Directive

_LANG = "th"
_BOUND_USER = {"id": "U1", "tenant_id": "T1"}
_USER_FRESH = {
    "id": "U1",
    "tenant_id": "T1",
    "gemini_api_key": "test-key",  # 走自带 key 分支,免碰 GEMINI_API_KEY 环境变量
    "custom_gemini_api_key": None,
}
_PAGES = [{"fields": {"seller_name": "ACME", "total_amount": "100"}}]
_RESULT = {"pages": _PAGES, "confidence": "high", "elapsed_ms": 100, "page_count": 1}
_QUOTE = {"allowed": True, "page_count": 1}


def _pipe_res():
    # pages=None → 下游 _pages_struct 塌成 [],连带 skip_ingest 一起确保走不进采购入账分流,
    # 直落第 5 步 insert_ocr_history(本测试要覆盖的分支)。
    return SimpleNamespace(estimated_cost_thb=0.5, page_count=1, pages=None)


def _run(insert_history_mock: mock.Mock):
    """真跑 _handle_line_image_ocr 到第 5/6 步,只桩掉外部依赖,返回 (返回值, notify mock)。"""

    async def _call():
        with (
            mock.patch.object(mod.line_client, "download_message_content", return_value=b"bytes"),
            mock.patch.object(mod, "_ocr_is_supported_file", return_value=True),
            mock.patch.object(mod.db, "find_user_by_id", return_value=_USER_FRESH),
            mock.patch.object(mod.wc, "default_workspace_for_write", return_value=1),
            mock.patch.object(mod, "_ocr_content_hash", return_value="HASH"),
            mock.patch.object(
                mod.line_image_route, "pre_ocr_shortcut", new=mock.AsyncMock(return_value=None)
            ),
            mock.patch.object(mod, "_ocr_billing_quote", return_value=_QUOTE),
            mock.patch.object(mod, "_ocr_run_pipeline_file", return_value=_pipe_res()),
            mock.patch(
                "services.ocr.legacy_adapter.pipeline_result_to_legacy_dict",
                return_value=_RESULT,
            ),
            mock.patch.object(mod, "_ocr_all_pages_not_invoice", return_value=False),
            mock.patch.object(
                mod.line_image_route,
                "intercept",
                new=mock.AsyncMock(return_value=Directive(handled=None, ws=None, skip_ingest=True)),
            ),
            mock.patch.object(mod, "insert_ocr_history", insert_history_mock),
            mock.patch.object(mod.db, "log_ocr_cost"),
            mock.patch.object(mod.db, "check_duplicate_invoice", return_value=None),
            mock.patch.object(mod, "_ocr_charge_success"),
            mock.patch.object(mod, "_async_run_exception_checks", new=mock.AsyncMock()),
            mock.patch.object(mod.line_reply, "push_text_context", return_value=True) as notify,
        ):
            ret = await mod._handle_line_image_ocr(
                bound_user=_BOUND_USER,
                line_user_id="LU1",
                message_id="M1",
                lang=_LANG,
                filename="test.jpg",
                quote_token="QT",
            )
            await asyncio.sleep(0)  # 让 fire-and-forget 的 create_task(charge/exception hook)走一步
            return ret, notify

    return asyncio.run(_call())


class HistoryWriteFailureNotifyTests(unittest.TestCase):
    def test_history_insert_failure_sends_save_failed_and_returns_false(self):
        ins = mock.Mock(side_effect=RuntimeError("db down"))
        ret, notify = _run(ins)

        ins.assert_called_once()
        self.assertFalse(ret)
        notify.assert_called_once()
        body = notify.call_args.args[1]
        self.assertEqual(body, line_client.t_ocr(_LANG, "save_failed"))
        self.assertNotIn(line_client.t_ocr(_LANG, "success_head"), body)

    def test_history_insert_success_sends_success_head_and_view_on_web(self):
        ins = mock.Mock(return_value="HID-1")
        ret, notify = _run(ins)

        ins.assert_called_once()
        notify.assert_called_once()
        body = notify.call_args.args[1]
        expected = (
            line_client.t_ocr(_LANG, "success_head")
            + " · "
            + line_client.t_ocr(_LANG, "view_on_web")
        )
        self.assertEqual(body, expected)
        self.assertNotEqual(ret, False)  # 正常路未提前 return False(回归保护)


if __name__ == "__main__":
    unittest.main()
