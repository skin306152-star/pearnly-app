"""
services/ocr/line_image_ocr.py · LINE Bot 图片/文件 OCR 后台任务

从 app.py 抽出(REFACTOR-WB-app · 2026-06-01 · 纯搬家 0 逻辑改)。
line_webhook_routes._handle_line_event 里 lazy import 调到;依赖的 _ocr_* helpers
直接 from services.ocr.entrypoints import,不经 app.py → 解循环 import。
"""

import asyncio
import os
import logging
import threading

from core import db
from core import workspace_context as wc
from core.db import insert_ocr_history
from services.exceptions.exception_checks import _async_run_exception_checks
from services.ocr import line_image_route
from services.ocr.line_multi_page import select_bookable_pages
from services.ocr.entrypoints import (
    all_pages_not_invoice as _ocr_all_pages_not_invoice,
    billing_quote as _ocr_billing_quote,
    charge_successful_ocr as _ocr_charge_success,
    content_hash as _ocr_content_hash,
    is_supported_ocr_file as _ocr_is_supported_file,
    run_pipeline_for_file as _ocr_run_pipeline_file,
)

try:
    from services.line_binding import line_client, line_imagemap, line_reply
except ImportError:
    line_client = None  # line_client.py 不在仓库 · 单独部署到服务器
    line_reply = None

logger = logging.getLogger("mr-pilot")
_LOADING_SECONDS = 60
_LOADING_REFRESH_INTERVAL = 50

# 多图排队:同一用户 FIFO 串行,避免多张图卡片乱序。
_user_img_locks: dict[str, asyncio.Lock] = {}
_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif")


def _user_img_lock(line_user_id: str) -> asyncio.Lock:
    lock = _user_img_locks.get(line_user_id)
    if lock is None:
        lock = asyncio.Lock()
        _user_img_locks[line_user_id] = lock
    return lock


def _keep_loading(line_user_id: str, stop: threading.Event) -> None:
    """Keep LINE's loading indicator alive until the OCR task sends a result."""
    if not line_client:
        return
    while not stop.is_set():
        try:
            line_client.start_loading(line_user_id, _LOADING_SECONDS)
        except Exception as e:
            logger.warning(f"[line_ocr] start_loading 失败(不阻断): {e}")
        stop.wait(_LOADING_REFRESH_INTERVAL)


async def process_line_image_serial(
    bound_user: dict,
    line_user_id: str,
    message_id: str,
    lang: str,
    filename: str = None,
    quote_token: str = None,
):
    """多图排队入口:抢 per-user 锁 → 轮到这张才转圈 → 处理 → 发卡。下一张等本张发完卡再开始。"""
    lock = _user_img_lock(line_user_id)
    async with lock:
        stop_loading = threading.Event()
        loading_thread = threading.Thread(
            target=_keep_loading,
            args=(line_user_id, stop_loading),
            name=f"line-loading-{line_user_id[-6:]}",
            daemon=True,
        )
        loading_thread.start()
        try:
            return await _handle_line_image_ocr(
                bound_user=bound_user,
                line_user_id=line_user_id,
                message_id=message_id,
                lang=lang,
                filename=filename,
                quote_token=quote_token,
            )
        finally:
            stop_loading.set()
            loading_thread.join(timeout=1)


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

    def _notify(body: str) -> None:
        # 图片异步通知统一引用原图片(quoteToken·P1C),失败/成功都让用户知道在回应哪张图。
        line_reply.push_text_context(
            line_user_id,
            body,
            quote_token=quote_token,
            tenant_id=(bound_user.get("tenant_id") if bound_user else None),
        )

    def _notify_card(card_key: str, fallback_body: str) -> None:
        # 有设计图卡就发图卡(Zihao 定:只发图卡不发文字);无卡回落文字。
        msg = line_imagemap.card_message(card_key)
        if msg:
            line_reply.push_messages_context(
                line_user_id,
                [msg],
                tenant_id=(bound_user.get("tenant_id") if bound_user else None),
            )
            return
        _notify(fallback_body)

    try:
        # 1. 下载
        file_bytes = line_client.download_message_content(message_id)
        filename = filename or f"line_{message_id}.jpg"
        if not file_bytes:
            _notify(line_client.t_ocr(lang, "err_download"))
            return False
        if not _ocr_is_supported_file(filename):
            _notify_card("unsupported", line_client.t_line(lang, "unsupported"))
            return False

        # 2. 用户 / credits 检查(复用网页入口的 credits 逻辑)
        user_fresh = db.find_user_by_id(bound_user["id"])
        if not user_fresh:
            _notify(line_client.t_ocr(lang, "err_plan"))
            return False

        # PO-4 · LINE 上传套账分流(product-vision §三-bis):LINE 无顶栏切换器,
        # 归 LINE 用户租户的默认套账(绑定店)。缺则 None(insert 内 NULL · 不拦上传)。
        _ws_client_id = wc.default_workspace_for_write(user_fresh.get("tenant_id"))

        # 3+3.5 费用 OCR 前快路(line_image_route.pre_ocr_shortcut):①意图=dms →
        # 专用身份证路接管;②缓存快路(dup/指纹·有待决意图时让位)。None=继续现状。
        file_hash = _ocr_content_hash(file_bytes)
        _pre = await line_image_route.pre_ocr_shortcut(
            user_fresh,
            line_user_id,
            file_hash,
            _ws_client_id,
            lang,
            quote_token,
            file_bytes=file_bytes,
            filename=filename,
        )
        if _pre is not None:
            return _pre

        quote = _ocr_billing_quote(user_fresh, file_bytes, filename, max_pages=50)
        if not quote.get("allowed"):
            code = quote.get("error_code")
            if code == "insufficient_balance":
                _notify_card("no_credit", line_client.t_ocr(lang, "err_quota"))
            else:
                _notify(line_client.t_ocr(lang, "err_ocr"))
            return False

        # 4. OCR · 新 pipeline 唯一路径
        own_key = (
            user_fresh.get("gemini_api_key") or user_fresh.get("custom_gemini_api_key") or ""
        ).strip()
        api_key = own_key or None
        # 检查 API key 可用性(用户自带或系统默认)
        if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
            _notify(line_client.t_ocr(lang, "err_plan"))
            return False

        try:
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
            from services.ocr.feedback.context import ocr_request_context

            _ctx_tid = str(user_fresh["tenant_id"]) if user_fresh.get("tenant_id") else None
            # 反馈闭环 ② · 设请求级上下文(L2 few-shot 按租户取例;flag 关时无副作用)
            with ocr_request_context(str(user_fresh["id"]), _ctx_tid):
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
            _notify_card("ocr_failed", line_client.t_line(lang, "line_ocr_failed_recovery"))
            return False

        pages = result.get("pages") or []
        if not pages:
            _notify_card("ocr_failed", line_client.t_line(lang, "line_ocr_failed_recovery"))
            return False
        if _ocr_all_pages_not_invoice(pages):
            # 非票据靶向引导(银行对账单→指去对账·认不出回落通用文案)
            _guide = line_image_route.not_invoice_guidance(pages, lang)
            _notify(_guide or line_client.t_line(lang, "line_not_receipt_recovery"))
            return True

        tid_str = str(user_fresh["tenant_id"]) if user_fresh.get("tenant_id") else None
        # LI-2 意图分流(闸默认关):决策/落地/兜底全在 route 层,指令默认值=现状代码逐字节不变。
        _idir = await line_image_route.intercept(
            user_fresh,
            _ws_client_id,
            tid_str,
            line_user_id,
            lang,
            quote,
            result,
            pages,
            _pipeline_cost_thb,
            filename,
            file_bytes,
            file_hash,
            quote_token,
        )
        if _idir.handled is not None:
            return _idir.handled
        _ws_client_id = _idir.ws if _idir.ws is not None else _ws_client_id

        # 统一智能通道(docs/smart-intake/15):图片 → 置信驱动入账(建草稿/高置信直接入账)+ 数据卡。
        #   expense 开 → ingest_line_image(高置信直接入正式账,其余草稿/待归类);回执发数据卡。
        #   expense 关 → 不入账,走下方识别记录原路(事务所等),一字不动。异常 → 同样回落识别记录。
        ingests = []
        try:
            from services.purchase.intake import (
                fields_from_invoice,
                line_expense_gate_open,
            )
            from services.purchase.line_ingest import ingest_line_image

            _pages_struct = getattr(_pipe_res, "pages", None) or []
            if _pages_struct and _ws_client_id and tid_str and not _idir.skip_ingest:
                with db.get_cursor_rls(tid_str, commit=True) as cur:
                    if line_expense_gate_open(cur, tenant_id=tid_str):
                        # 票图闭环:LINE 图持久化到 pdf_storage → image_ref 挂进单据。
                        from services.ocr import pdf_storage as _pstore

                        _suffix = os.path.splitext(filename or "")[1] or ".jpg"
                        _img_ref, _ = _pstore.save_bytes(str(user_fresh["id"]), file_bytes, _suffix)
                        from services.expense import line_l2

                        _api_key = line_l2.resolve_api_key(user_fresh)
                        # 多页单据逐页入账:此前只取 page[0],2..N 张被静默丢弃(伤账)。
                        # select_bookable_pages 防长单跨页重复记账;不同票各自建单/发卡。
                        for _fields, _fc, _sha in select_bookable_pages(
                            _pages_struct, file_hash, flatten=fields_from_invoice
                        ):
                            _one = ingest_line_image(
                                cur,
                                tenant_id=tid_str,
                                workspace_client_id=_ws_client_id,
                                fields=_fields,
                                confidence=result.get("confidence"),
                                field_confidence=_fc,
                                image_ref=_img_ref,
                                created_by=str(user_fresh["id"]),
                                api_key=_api_key,
                                image_sha256=_sha,
                            )
                            if _one:
                                ingests.append(_one)
        except Exception as _route_err:
            logger.warning(f"[line_ocr] 采购入账分流跳过(回落识别记录): {_route_err}")
            ingests = []

        if ingests:
            _is_img = os.path.splitext(filename or "")[1].lower() in _IMAGE_EXTS
            for _one in ingests:
                _one["source"] = "image" if _is_img else "file"  # 来自图片 / 来自文件
            # 已入账/草稿/待归类 → 不写识别记录;计费与历史脱钩(history_id=None);回执发数据卡。
            try:
                asyncio.create_task(
                    asyncio.to_thread(
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
            # 多张票各自发一张卡(只第一张引用用户原图,避免 N 条都带引用)。
            for _i, _one in enumerate(ingests):
                _push_result_card(
                    line_user_id,
                    lang,
                    _one,
                    quote_token if _i == 0 else None,
                    _ws_client_id,
                    tenant_id=tid_str,
                )
            # 跨轮锚点:锚定这张单,让下一句「把刚才那张推进ERP」命中它(闸关 no-op)。
            from services.agent import anchors as agent_anchors

            agent_anchors.record_image_docs(
                user_fresh, tid_str, line_user_id, ingests, _ws_client_id
            )
            # 对话记忆(PO-15):记图片轮的结果,让下一句文本问「为什么/需补啥」时大脑接得住。
            from services.line_binding import line_chat_memory

            line_chat_memory.note(
                line_user_id=line_user_id, tenant_id=tid_str, role="user", content="[ส่งรูปใบเสร็จ]"
            )
            _summary = "; ".join(
                s for o in ingests if (s := f"{o.get('state', '')} {o.get('amount') or ''}".strip())
            )
            _bot_note = (
                f"票据识别:{_summary}"
                if len(ingests) == 1
                else f"票据识别 {len(ingests)} 张:{_summary}"
            )
            line_chat_memory.note(
                line_user_id=line_user_id, tenant_id=tid_str, role="bot", content=_bot_note
            )
            logger.info(f"[line_ocr] 完成 · docs={len(ingests)} · user={user_fresh['id']}")
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
                asyncio.create_task(
                    asyncio.to_thread(
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
                        tenant_id=tid_str,
                    )
                    if _dup_raw:
                        _dup = {
                            "level": _dup_raw.get("level"),
                            "matched_fields": _dup_raw.get("matched_fields"),
                            "match": _dup_raw.get("match"),
                        }
                except Exception as _e_dup:
                    logger.warning(f"[line_ocr] duplicate 检测失败(不影响 hook): {_e_dup}")
                asyncio.create_task(
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

        # 6. 推送识别结果:删老式字段 dump(Zihao 指明清掉)· 改干净一行(已识别 + 引导网页)。
        # 到这里票已识别(认不出的在上方 all_pages_not_invoice 已拦);未开记账模块/入账分流失败
        # 的兜底统一走此 —— 已写识别记录,网页可查,不再回显整段原始字段。
        _notify(
            line_client.t_ocr(lang, "success_head") + " · " + line_client.t_ocr(lang, "view_on_web")
        )
        logger.info(f"[line_ocr] 完成 · user={user_fresh['id']} · hid={hid}")

    except Exception as e:
        logger.exception(f"[line_ocr] 未知异常: {e}")
        try:
            _notify_card("ocr_failed", line_client.t_line(lang, "line_ocr_failed_recovery"))
        except Exception as _pe:
            logger.warning(f"[line_ocr] err 通知 push_text 失败: {_pe}")
        return False


def _push_result_card(
    line_user_id: str,
    lang: str,
    ingest: dict,
    quote_token: str = None,
    ws_client_id="",
    tenant_id=None,
) -> None:
    """识别结果数据卡 push(共用发卡口 line_booker.push_result_card · 发完绑消息 id 供引用改/删)。"""
    from services.line_binding import line_booker

    line_booker.push_result_card(
        line_user_id,
        lang,
        ingest,
        quote_token=quote_token,
        ws_client_id=ws_client_id,
        tenant_id=tenant_id,
    )
