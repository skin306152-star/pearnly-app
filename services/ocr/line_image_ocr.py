"""
services/ocr/line_image_ocr.py · LINE Bot 图片/文件 OCR 后台任务

LINE 收图 → OCR 识别 → 落「采购/进项 · 待归类」(route_line_image),让老板在采购 inbox 一点入账。
2026-06-15(Zihao 拍板):LINE 图片识别的智能分流只保留「→ 采购进项」一条;不再写「识别记录」
(ocr_history)、不再走识别中心的缓存命中 / 异常栏 hook。采购进项 / 录入工作台自己的上传 OCR
识别是网页另一套代码,一字不动。计费仍按 credits 口径扣(与历史脱钩 · history_id=None)。
"""

import logging
import os

from core import db
from core import workspace_context as wc
from services.ocr.entrypoints import (
    all_pages_not_invoice as _ocr_all_pages_not_invoice,
    billing_quote as _ocr_billing_quote,
    charge_successful_ocr as _ocr_charge_success,
    is_supported_ocr_file as _ocr_is_supported_file,
    run_pipeline_for_file as _ocr_run_pipeline_file,
)

try:
    from services.line_binding import line_client
except ImportError:
    line_client = None  # line_client.py 不在仓库 · 单独部署到服务器

logger = logging.getLogger("mr-pilot")


async def _handle_line_image_ocr(
    bound_user: dict,
    line_user_id: str,
    message_id: str,
    lang: str,
    filename: str = None,
):
    """LINE 图片/文件 → OCR → 落采购待归类(不写识别记录)。

    步骤:① 下载 ② credits 检查 ③ OCR pipeline ④ 智能分流落采购进项 ⑤ 扣费 ⑥ 回执。
    """
    try:
        file_bytes = line_client.download_message_content(message_id)
        filename = filename or f"line_{message_id}.jpg"
        if not file_bytes:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_download"))
            return
        if not _ocr_is_supported_file(filename):
            line_client.push_text(line_user_id, line_client.t_line(lang, "unsupported"))
            return

        user_fresh = db.find_user_by_id(bound_user["id"])
        if not user_fresh:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        # LINE 无顶栏套账切换器 → 归 LINE 用户租户的默认套账(绑定店)。缺则 None(不拦)。
        _ws_client_id = wc.default_workspace_for_write(user_fresh.get("tenant_id"))

        quote = _ocr_billing_quote(user_fresh, file_bytes, filename, max_pages=50)
        if not quote.get("allowed"):
            code = quote.get("error_code")
            key = "err_quota" if code == "insufficient_balance" else "err_ocr"
            line_client.push_text(line_user_id, line_client.t_ocr(lang, key))
            return

        own_key = (
            user_fresh.get("gemini_api_key") or user_fresh.get("custom_gemini_api_key") or ""
        ).strip()
        api_key = own_key or None
        if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        try:
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

            _pipe_res = _ocr_run_pipeline_file(file_bytes, filename, api_key=api_key, max_pages=50)
            result = pipeline_result_to_legacy_dict(_pipe_res)
            _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
            logger.info(
                f"🆕 [line_ocr] pipeline_v1 · pages={_pipe_res.page_count} "
                f"· cost=฿{_pipeline_cost_thb:.4f}"
            )
        except Exception as _pipe_err:
            logger.error(f"[line_ocr] pipeline 识别失败: {type(_pipe_err).__name__}: {_pipe_err}")
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        pages = result.get("pages") or []
        if not pages or _ocr_all_pages_not_invoice(pages):
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 智能分流:LINE 票 → 采购进项待归类(唯一去向 · 不再进识别记录)。
        # 事务所 firm / 未开 expense / 无默认套账 / 异常 → route_line_image 内部早退,不影响回执。
        try:
            from services.purchase.intake import fields_from_invoice, route_line_image

            _pages_struct = getattr(_pipe_res, "pages", None) or []
            if _pages_struct and _ws_client_id:
                route_line_image(
                    tenant_id=user_fresh.get("tenant_id"),
                    workspace_client_id=_ws_client_id,
                    fields=fields_from_invoice(_pages_struct[0].invoice),
                    confidence=result.get("confidence"),
                )
        except Exception as _route_err:
            logger.warning(f"[line_ocr] 采购分流跳过: {_route_err}")

        # 扣费(credits 口径 · 不写识别记录 → history_id=None)。
        try:
            import asyncio as _acharge

            _acharge.create_task(
                _acharge.to_thread(
                    _ocr_charge_success, user_fresh, quote, None, f"LINE OCR · {filename}"
                )
            )
        except Exception as _chg_e:
            logger.warning(f"[line_ocr] credits charge dispatch failed: {_chg_e}")

        # cost 埋点(history_id=None)。
        try:
            _line_in = sum(int(p.get("input_tokens") or 0) for p in pages)
            _line_out = sum(int(p.get("output_tokens") or 0) for p in pages)
            db.log_ocr_cost(
                user_id=str(user_fresh["id"]),
                tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                history_id=None,
                engine="pipeline_v1",
                pages=len(pages),
                input_tokens=_line_in,
                output_tokens=_line_out,
                cost_thb=_pipeline_cost_thb,
                elapsed_ms=int(result.get("elapsed_ms") or 0),
            )
        except Exception as _ce:
            logger.warning(f"[line_ocr] cost log failed (non-blocking): {_ce}")

        # 回执:把识别到的字段回给用户(确认已收票 · 已进采购待归类)。
        reply_txt = line_client.format_ocr_result_for_line(lang, pages, invoice_count=len(pages))
        line_client.push_text(line_user_id, reply_txt)
        logger.info(f"[line_ocr] 完成 · user={user_fresh['id']} · → 采购待归类")

    except Exception as e:
        logger.exception(f"[line_ocr] 未知异常: {e}")
        try:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
        except Exception as _pe:
            logger.warning(f"[line_ocr] err 通知 push_text 失败: {_pe}")
