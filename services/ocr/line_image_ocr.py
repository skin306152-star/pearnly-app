"""
services/ocr/line_image_ocr.py · LINE Bot 图片/文件 OCR 后台任务

从 app.py 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
line_webhook_routes._handle_line_event 里 lazy import 调到;依赖的 _ocr_* helpers
直接 from services.ocr.entrypoints import,不经 app.py → 解循环 import。
"""

import os
import logging

from core import db
from core import workspace_context as wc
from core.db import insert_ocr_history
from services.exceptions.exception_checks import _async_run_exception_checks
from services.ocr.entrypoints import (
    all_pages_not_invoice as _ocr_all_pages_not_invoice,
    billing_quote as _ocr_billing_quote,
    charge_successful_ocr as _ocr_charge_success,
    content_hash as _ocr_content_hash,
    get_cached_history as _ocr_get_cached,
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
    quote_token: str = None,
):
    """
    异步处理 LINE 图片/文件消息:
      1. 下载内容
      2. 按网页上传同一支持清单喂 OCR pipeline
      3. 插入 ocr_history(source='line_bot')
      4. 非缓存成功识别后按 credits 定价扣费
      5. push 结果给用户
    """
    try:
        # 1. 下载
        file_bytes = line_client.download_message_content(message_id)
        filename = filename or f"line_{message_id}.jpg"
        if not file_bytes:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_download"))
            return
        if not _ocr_is_supported_file(filename):
            line_client.push_text(line_user_id, line_client.t_line(lang, "unsupported"))
            return

        # 2. 用户 / credits 检查(复用网页入口的 credits 逻辑)
        user_fresh = db.find_user_by_id(bound_user["id"])
        if not user_fresh:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        # PO-4 · LINE 上传套账分流(product-vision §三-bis):LINE 无顶栏切换器,
        # 归 LINE 用户租户的默认套账(绑定店)。缺则 None(insert 内 NULL · 不拦上传)。
        _ws_client_id = wc.default_workspace_for_write(user_fresh.get("tenant_id"))

        # 3. 文件指纹缓存查找:命中则跳 OCR + 跳扣费(缓存按套账隔离)
        file_hash = _ocr_content_hash(file_bytes)
        cached = _ocr_get_cached(user_fresh, file_hash, workspace_client_id=_ws_client_id)
        if cached:
            logger.info(f"[line_ocr] 命中文件缓存 (hash={file_hash[:12]}...) hid={cached['id']}")
            # 跑异常 hook(同网页缓存命中分支 · 不重复扣配额)
            try:
                import asyncio as _asyncio_exc_lc

                _cached_pages = cached.get("pages") or []
                _primary = next(
                    (
                        p
                        for p in _cached_pages
                        if not p.get("is_duplicate") and not p.get("is_copy")
                    ),
                    None,
                )
                _primary = _primary or (_cached_pages[0] if _cached_pages else None)
                _cf = (_primary or {}).get("fields") or {}
                _exc_total_c = None
                _raw_t_c = _cf.get("total_amount")
                if _raw_t_c:
                    try:
                        _exc_total_c = float(str(_raw_t_c).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[line_cache] total_amount 解析失败: {e}")
                _asyncio_exc_lc.create_task(
                    _async_run_exception_checks(
                        history_id=str(cached["id"]),
                        user_id=str(user_fresh["id"]),
                        tenant_id=(
                            str(user_fresh.get("tenant_id"))
                            if user_fresh.get("tenant_id")
                            else None
                        ),
                        seller_name=_cf.get("seller_name"),
                        invoice_no=_cf.get("invoice_number"),
                        total_amount=_exc_total_c,
                        confidence=cached.get("confidence"),
                        duplicate=None,
                        fields=_cf,
                    )
                )
                logger.info(f"  🛡  [LINE Cache] 异常检测已入队 · hid={cached['id']}")
            except Exception as _e_lc:
                logger.warning(f"[line_ocr] 缓存异常检测入队失败: {_e_lc}")
            # 推 cached 结果给用户(模拟 OCR 完成)
            reply_txt = line_client.format_ocr_result_for_line(
                lang, cached.get("pages") or [], invoice_count=len(cached.get("pages") or [])
            )
            line_client.push_text(line_user_id, reply_txt)
            return

        quote = _ocr_billing_quote(user_fresh, file_bytes, filename, max_pages=50)
        if not quote.get("allowed"):
            code = quote.get("error_code")
            if code == "insufficient_balance":
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_quota"))
            else:
                line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 4. OCR · 新 pipeline 唯一路径
        own_key = (
            user_fresh.get("gemini_api_key") or user_fresh.get("custom_gemini_api_key") or ""
        ).strip()
        api_key = own_key or None
        # 检查 API key 可用性(用户自带或系统默认)
        if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_plan"))
            return

        try:
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

            _pipe_res = _ocr_run_pipeline_file(
                file_bytes,
                filename,
                api_key=api_key,
                max_pages=50,
            )
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
        if not pages:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return
        if _ocr_all_pages_not_invoice(pages):
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
            return

        # 统一智能通道(docs/smart-intake/15):图片 → 置信驱动入账(建草稿/高置信直接入账)+ 数据卡。
        #   expense 开 → ingest_line_image(高置信直接入正式账,其余草稿/待归类);回执发数据卡。
        #   expense 关 → 不入账,走下方识别记录原路(事务所等),一字不动。异常 → 同样回落识别记录。
        ingest = None
        tid_str = str(user_fresh["tenant_id"]) if user_fresh.get("tenant_id") else None
        try:
            from services.purchase.intake import (
                fields_from_invoice,
                line_expense_gate_open,
            )
            from services.purchase.line_ingest import ingest_line_image

            _pages_struct = getattr(_pipe_res, "pages", None) or []
            if _pages_struct and _ws_client_id and tid_str:
                with db.get_cursor_rls(tid_str, commit=True) as cur:
                    if line_expense_gate_open(cur, tenant_id=tid_str):
                        # 票图闭环:LINE 图持久化到 pdf_storage(同网页上传留底)→ image_ref 挂进单据,
                        # 详情页才看得到原票。此前没传 image_ref → LINE 进来的单据票图恒空。
                        from services.ocr import pdf_storage as _pstore

                        _suffix = os.path.splitext(filename or "")[1] or ".jpg"
                        _img_ref, _ = _pstore.save_bytes(str(user_fresh["id"]), file_bytes, _suffix)
                        from services.expense import line_l2

                        ingest = ingest_line_image(
                            cur,
                            tenant_id=tid_str,
                            workspace_client_id=_ws_client_id,
                            fields=fields_from_invoice(_pages_struct[0].invoice),
                            confidence=result.get("confidence"),
                            field_confidence=getattr(_pages_struct[0], "field_confidence", None),
                            image_ref=_img_ref,
                            created_by=str(user_fresh["id"]),
                            api_key=line_l2.resolve_api_key(user_fresh),
                        )
        except Exception as _route_err:
            logger.warning(f"[line_ocr] 采购入账分流跳过(回落识别记录): {_route_err}")
            ingest = None

        if ingest:
            # 已入账/草稿/待归类 → 不写识别记录;计费与历史脱钩(history_id=None);回执发数据卡。
            try:
                import asyncio as _acharge

                _acharge.create_task(
                    _acharge.to_thread(
                        _ocr_charge_success, user_fresh, quote, None, f"LINE OCR · {filename}"
                    )
                )
            except Exception as _chg_e:
                logger.warning(f"[line_ocr] credits charge dispatch failed: {_chg_e}")
            try:
                db.log_ocr_cost(
                    user_id=str(user_fresh["id"]),
                    tenant_id=tid_str,
                    history_id=None,
                    engine="pipeline_v1",
                    pages=len(pages),
                    input_tokens=sum(int(p.get("input_tokens") or 0) for p in pages),
                    output_tokens=sum(int(p.get("output_tokens") or 0) for p in pages),
                    cost_thb=_pipeline_cost_thb,
                    elapsed_ms=int(result.get("elapsed_ms") or 0),
                )
            except Exception as _ce:
                logger.warning(f"[line_ocr] cost log failed (non-blocking): {_ce}")
            _push_result_card(line_user_id, lang, ingest, quote_token, _ws_client_id)
            # 对话记忆(PO-15):记图片轮的结果,让下一句文本问「为什么/需补啥」时大脑接得住。
            from services.line_binding import line_chat_memory

            line_chat_memory.note(
                line_user_id=line_user_id, tenant_id=tid_str, role="user", content="[ส่งรูปใบเสร็จ]"
            )
            line_chat_memory.note(
                line_user_id=line_user_id,
                tenant_id=tid_str,
                role="bot",
                content=f"票据识别:{ingest.get('state', '')} {ingest.get('amount') or ''}".strip(),
            )
            logger.info(f"[line_ocr] 完成 · state={ingest['state']} · user={user_fresh['id']}")
            return

        # 5. 写 history(source='line_bot')· 事务所/未开 expense 走识别记录
        # file_hash 已在 3.5 计算(v118.22.0.3)
        try:
            hid = insert_ocr_history(
                user_id=str(user_fresh["id"]),
                tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                filename=filename,
                page_count=int(quote.get("page_count") or result.get("page_count") or len(pages)),
                pages=pages,
                confidence=result.get("confidence") or "unknown",
                elapsed_ms=result.get("elapsed_ms") or 0,
                file_size_kb=len(file_bytes) // 1024,
                file_hash=file_hash,
                source="line_bot",
                source_ref=line_user_id,
                workspace_client_id=_ws_client_id,  # PO-4 · 归 LINE 绑定店套账
            )
        except Exception as e:
            logger.warning(f"[line_ocr] 写 history 失败(不影响回复): {e}")
            hid = None
        if hid:
            try:
                import asyncio as _asyncio_charge_l

                _asyncio_charge_l.create_task(
                    _asyncio_charge_l.to_thread(
                        _ocr_charge_success,
                        user_fresh,
                        quote,
                        str(hid),
                        f"LINE OCR · {filename} · {str(hid)[:8]}",
                    )
                )
            except Exception as _chg_e:
                logger.warning(f"[line_ocr] credits charge dispatch failed: {_chg_e}")

        # LINE 入口 cost 埋点(pipeline 唯一路径,100% 记录)
        try:
            _line_in = sum(int(p.get("input_tokens") or 0) for p in pages)
            _line_out = sum(int(p.get("output_tokens") or 0) for p in pages)
            db.log_ocr_cost(
                user_id=str(user_fresh["id"]),
                tenant_id=str(user_fresh.get("tenant_id")) if user_fresh.get("tenant_id") else None,
                history_id=hid,
                engine="pipeline_v1",
                pages=len(pages),
                input_tokens=_line_in,
                output_tokens=_line_out,
                cost_thb=_pipeline_cost_thb,
                elapsed_ms=int(result.get("elapsed_ms") or 0),
            )
            logger.info(f"💰 [line_ocr] cost log · ฿{_pipeline_cost_thb:.4f}")
        except Exception as _ce:
            logger.warning(f"[line_ocr] cost log failed (non-blocking): {_ce}")

        # 5.5 · 异常栏 hook(v118.22.0.2 修复 · LINE 入口此前漏挂 · 致 LINE 票据从不进 5 类规则)
        # v118.22.0.3 · 增加 duplicate 预检 · 让 LINE 票据也享有「重复发票拦截」防护
        if hid:
            try:
                import asyncio as _asyncio_exc_l

                _primary = pages[0] if pages else {}
                _f = _primary.get("fields") or {}
                _exc_total = None
                _raw_t = _f.get("total_amount")
                if _raw_t:
                    try:
                        _exc_total = float(str(_raw_t).replace(",", "").strip())
                    except Exception as e:
                        logger.warning(f"[line_ocr_exc] total_amount 解析失败: {e}")
                # duplicate 检测(同网页入口)
                _dup = None
                try:
                    _dup_raw = db.check_duplicate_invoice(
                        user_id=str(user_fresh["id"]),
                        invoice_no=_f.get("invoice_number"),
                        invoice_date=_f.get("invoice_date"),
                        seller_name=_f.get("seller_name"),
                        total_amount=_exc_total,
                        exclude_id=str(hid),
                        workspace_client_id=_ws_client_id,  # PO-4 · 重复检测限本套账
                    )
                    if _dup_raw:
                        _dup = {
                            "level": _dup_raw.get("level"),
                            "matched_fields": _dup_raw.get("matched_fields"),
                            "match": _dup_raw.get("match"),
                        }
                except Exception as _e_dup:
                    logger.warning(f"[line_ocr] duplicate 检测失败(不影响 hook): {_e_dup}")
                _asyncio_exc_l.create_task(
                    _async_run_exception_checks(
                        history_id=str(hid),
                        user_id=str(user_fresh["id"]),
                        tenant_id=(
                            str(user_fresh.get("tenant_id"))
                            if user_fresh.get("tenant_id")
                            else None
                        ),
                        seller_name=_f.get("seller_name"),
                        invoice_no=_f.get("invoice_number"),
                        total_amount=_exc_total,
                        confidence=result.get("confidence"),
                        duplicate=_dup,
                        fields=_f,
                    )
                )
                logger.info(
                    f"  🛡  [LINE] 异常检测已入队 · hid={hid} · dup={'有' if _dup else '无'}"
                )
            except Exception as _e:
                logger.warning(f"[line_ocr] 异常检测入队失败(不影响推送): {_e}")

        # 6. 推送识别结果
        reply_txt = line_client.format_ocr_result_for_line(lang, pages, invoice_count=len(pages))
        line_client.push_text(line_user_id, reply_txt)
        logger.info(f"[line_ocr] 完成 · user={user_fresh['id']} · hid={hid}")

    except Exception as e:
        logger.exception(f"[line_ocr] 未知异常: {e}")
        try:
            line_client.push_text(line_user_id, line_client.t_ocr(lang, "err_ocr"))
        except Exception as _pe:
            logger.warning(f"[line_ocr] err 通知 push_text 失败: {_pe}")


def _push_result_card(
    line_user_id: str, lang: str, ingest: dict, quote_token: str = None, ws_client_id=""
) -> None:
    """识别结果数据卡 push:【引用照片的一行回执】+【Flex 数据卡】。失败回落纯文字(不静默)。"""
    state = ingest.get("state", "confirm")
    ack_key = {
        "posted": "exp_ack_posted",
        "dup": "exp_ack_dup",
    }.get(state, "exp_ack_confirm")
    try:
        from services.line_binding import line_card

        ack = {
            "type": "text",
            "text": line_client.t_line(lang, ack_key, amount=ingest.get("amount") or "—"),
        }
        if quote_token:
            ack["quoteToken"] = quote_token
        card = line_card.result_card(
            state=state,
            amount=ingest.get("amount"),
            fields=ingest.get("card_fields") or {},
            field_confidence=ingest.get("field_confidence") or {},
            doc_id=ingest.get("ref") or ingest.get("doc_id") or "",
            lang=lang,
            web_url="https://pearnly.com/home",
            workspace_name=ingest.get("workspace_name") or "",
            token=ingest.get("token") or "",
            warn_total=bool(ingest.get("warn_total")),
            liff_id=os.getenv("LINE_LIFF_ID", "").strip(),
            workspace_client_id=str(ws_client_id or ""),
        )
        line_client.push_messages(line_user_id, [ack, card])
    except Exception as e:
        logger.warning(f"[line_ocr] 数据卡 push 失败,回落纯文字: {e}")
        line_client.push_text(line_user_id, line_client.t_ocr(lang, "routed_to_purchase"))
