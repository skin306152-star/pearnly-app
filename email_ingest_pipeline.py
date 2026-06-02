# -*- coding: utf-8 -*-
"""email_ingest · 抓取管道(单附件 OCR 摄取 + 自动推送 + 账号抓取编排 + 连接测试)leaf。"""

import os
import time
import imaplib
import logging
from typing import Any, Dict, Optional

from services.ocr.entrypoints import (
    all_pages_not_invoice,
    billing_quote,
    charge_successful_ocr,
    content_hash,
    get_cached_history,
    run_pipeline_for_file,
)
from email_ingest_crypto import is_available
from email_ingest_imap import (
    MAX_EMAILS_PER_RUN,
    INITIAL_DAYS_BACK,
    _SUPPORTED_EXTS,
    _decode_mime,
    _extract_attachments,
    _connect_imap,
    _search_unread_with_attachments,
    _fetch_email,
    _mark_seen,
)

logger = logging.getLogger(__name__)


def _ingest_one_attachment(
    user_id: str,
    account_id: str,
    uid: str,
    filename: str,
    content: bytes,
    subject: str,
    sender: str,
) -> Optional[str]:
    """
    单个附件 → 走 Gemini OCR → 写 ocr_history
    返回 history_id(第一条)· 失败返回 None
    """
    import db

    ext = os.path.splitext(filename.lower())[1]
    if ext not in _SUPPORTED_EXTS:
        logger.info(f"[email_ingest] 跳过不支持附件 · {filename}")
        return None

    user = db.find_user_by_id(user_id)
    if not user:
        logger.warning(f"[email_ingest] user_id={user_id} 不存在")
        return None

    # 文件缓存命中:直接复用历史,不扣费(全入口统一契约)
    file_hash = content_hash(content)
    cached = get_cached_history(user, file_hash)
    if cached:
        logger.info(
            f"[email_ingest] 命中文件缓存 · {filename} · "
            f"hash={file_hash[:12]} hid={cached.get('id')}"
        )
        return str(cached.get("id"))

    quote = billing_quote(user, content, filename, max_pages=50)
    if not quote.get("allowed"):
        logger.warning(
            f"[email_ingest] billing/file gate blocked · {filename} · " f"{quote.get('error_code')}"
        )
        return None

    # Gemini API key · 优先用户自带 · 否则系统 key
    user_key = db.get_user_gemini_key(user_id)
    api_key = user_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("[email_ingest] 没有可用的 Gemini API key")
        return None

    try:
        from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

        _pipe_res = run_pipeline_for_file(content, filename, api_key=api_key, max_pages=50)
        result = pipeline_result_to_legacy_dict(_pipe_res)
        _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
        logger.info(
            f"🆕 [email_ingest] pipeline_v1 · {filename} · pages={_pipe_res.page_count} "
            f"· cost=฿{_pipeline_cost_thb:.4f}"
        )
    except Exception as _pipe_err:
        logger.error(
            f"[email_ingest] pipeline 识别失败 · {filename}: "
            f"{type(_pipe_err).__name__}: {_pipe_err}"
        )
        return None

    if not result or not result.get("pages"):
        logger.warning(f"[email_ingest] 识别结果为空 · {filename}")
        return None

    pages = result["pages"]
    if all_pages_not_invoice(pages):
        logger.warning(f"[email_ingest] 判定非发票 · 不入库不扣费 · {filename}")
        return None

    # 算置信度(简化 · 关键字段齐全=high · 否则 medium)
    confidence = "medium"
    try:
        f0 = (pages[0].get("fields") or {}) if pages else {}
        if f0.get("invoice_number") and f0.get("total_amount") and f0.get("seller_name"):
            confidence = "high"
    except Exception:
        pass

    # 归档名(若用户配了模板)
    archive_name = None
    category_tag = None
    try:
        import archive as archive_mod

        first_main = next(
            (p for p in pages if not p.get("is_duplicate") and not p.get("is_copy")), None
        )
        if first_main:
            merged = first_main.get("fields") or {}
            tpl = db.get_archive_template(user_id) or archive_mod.DEFAULT_TEMPLATE
            archive_name = archive_mod.preview_name(merged, tpl)
            category_tag = (merged.get("category") or "").strip() or None
    except Exception as e:
        logger.warning(f"[email_ingest] 归档名生成失败: {e}")

    # 写 ocr_history(带 source='email')
    source_ref = f"{account_id}:{uid}"
    history_id = db.insert_ocr_history(
        user_id=user_id,
        tenant_id=str(user.get("tenant_id")) if user.get("tenant_id") else None,
        filename=filename,
        page_count=int(quote.get("page_count") or result.get("page_count") or len(pages)),
        pages=pages,
        confidence=confidence,
        elapsed_ms=int(result.get("elapsed_ms") or 0),
        file_size_kb=len(content) // 1024,
        file_hash=file_hash,
        archive_name=archive_name,
        category_tag=category_tag,
        source="email",
        source_ref=source_ref,
    )

    charge_successful_ocr(
        user,
        quote,
        history_id,
        f"Email OCR · {filename} · {str(history_id or '')[:8]}",
    )

    # email_ingest cost 埋点(pipeline 唯一路径,100% 记录)
    try:
        _em_in = sum(int(p.get("input_tokens") or 0) for p in pages)
        _em_out = sum(int(p.get("output_tokens") or 0) for p in pages)
        _tenant_id = str(user.get("tenant_id")) if user.get("tenant_id") else None
        db.log_ocr_cost(
            user_id=user_id,
            tenant_id=_tenant_id,
            history_id=history_id,
            engine="pipeline_v1",
            pages=len(pages),
            input_tokens=_em_in,
            output_tokens=_em_out,
            cost_thb=_pipeline_cost_thb,
            elapsed_ms=int(result.get("elapsed_ms") or 0),
        )
        logger.info(f"💰 [email_ingest] cost log · {filename} · ฿{_pipeline_cost_thb:.4f}")
    except Exception as _ce:
        logger.warning(f"[email_ingest] cost log failed (non-blocking): {_ce}")

    return history_id


def _auto_push_if_configured(user_id: str, history_id: str):
    """抓到的发票 · 如果用户配了 auto_push endpoint · 自动推送 ERP"""
    if not history_id:
        return
    try:
        import db
        import erp_push

        auto_eps = db.list_erp_endpoints(user_id, auto_push_only=True)
        if not auto_eps:
            return
        detail = db.get_ocr_history_detail(user_id, history_id)
        if not detail:
            return
        for ep in auto_eps:
            if not ep.get("enabled"):
                continue
            push_result = erp_push.push_to_endpoint(ep, detail)
            db.insert_push_log(
                user_id=user_id,
                endpoint_id=ep.get("id"),
                history_id=history_id,
                invoice_no=detail.get("invoice_no"),
                seller_name=detail.get("seller_name"),
                total_amount=detail.get("total_amount"),
                status="success" if push_result.get("success") else "failed",
                http_status=push_result.get("http_status"),
                request_body=push_result.get("request_body"),
                response_body=push_result.get("response_body"),
                error_msg=push_result.get("error_msg"),
                attempt=1,
                elapsed_ms=push_result.get("elapsed_ms") or 0,
                trigger="auto",
            )
            if push_result.get("success"):
                db.update_endpoint_stats(ep["id"], True)
                db.update_history_push_status(history_id, "success")
            else:
                db.update_endpoint_stats(ep["id"], False)
                db.update_history_push_status(history_id, "failed")
    except Exception as e:
        logger.warning(f"[email_ingest] 自动推送失败 (非致命): {e}")


def run_account_ingest(account: Dict[str, Any], trigger: str = "auto") -> Dict[str, Any]:
    """
    对一个账号执行一次抓取
    参数:
      account: 从 email_ingest_accounts 表读出的一行 dict
      trigger: "auto" | "manual"
    返回:统计 dict(用于写 email_ingest_logs)
        {
            "status": "success" | "partial" | "failed" | "skipped",
            "emails_scanned": int,
            "attachments_found": int,
            "ocr_succeeded": int,
            "ocr_failed": int,
            "error_message": str | None,
            "error_details": list | None,
            "elapsed_ms": int,
            "new_history_ids": [uuid, ...]  · 供后续自动推 ERP 调用
        }
    本轮 skeleton · 真 OCR 调用放到下一轮(避免一次改太多联动 ocr_history 的东西)
    """
    t0 = time.time()
    result = {
        "status": "skipped",
        "emails_scanned": 0,
        "attachments_found": 0,
        "ocr_succeeded": 0,
        "ocr_failed": 0,
        "error_message": None,
        "error_details": [],
        "elapsed_ms": 0,
        "new_history_ids": [],
    }

    # 可用性检查
    if not is_available():
        result["status"] = "failed"
        result["error_message"] = "encryption_not_configured"
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        return result

    conn = _connect_imap(account)
    if conn is None:
        result["status"] = "failed"
        result["error_message"] = "imap_connect_failed"
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        return result

    try:
        folder = account.get("folder") or "INBOX"
        # 首次抓取往前 7 天 · 之后每次只抓 1 天内(定时 15min · 完全够)
        since_days = INITIAL_DAYS_BACK if not account.get("last_fetched_at") else 1

        uids = _search_unread_with_attachments(conn, folder, since_days)
        result["emails_scanned"] = len(uids)

        # 限幅
        if len(uids) > MAX_EMAILS_PER_RUN:
            logger.info(
                f"[email_ingest] 未读 {len(uids)} 封 · 本次只处理前 {MAX_EMAILS_PER_RUN} 封"
            )
            uids = uids[:MAX_EMAILS_PER_RUN]

        for uid in uids:
            try:
                msg = _fetch_email(conn, uid)
                if msg is None:
                    continue
                subject = _decode_mime(msg.get("Subject"))
                sender = _decode_mime(msg.get("From"))

                # v95 · 应用过滤器:发件人白名单 + 主题关键词(任一为空则跳过该层过滤)
                filter_sender_str = (account.get("filter_sender") or "").strip()
                filter_subject_str = (account.get("filter_subject") or "").strip()
                # 发件人白名单:逗号 / 换行 / 分号 分隔 · 任意 substring 匹配
                if filter_sender_str:
                    senders = [
                        s.strip().lower()
                        for s in filter_sender_str.replace(";", ",").replace("\n", ",").split(",")
                        if s.strip()
                    ]
                    sender_lower = (sender or "").lower()
                    if senders and not any(s in sender_lower for s in senders):
                        logger.info(f"[email_ingest] 跳过 · 发件人不在白名单: {sender[:60]}")
                        if account.get("mark_as_read", True):
                            _mark_seen(conn, uid)
                        continue
                # 主题关键词:任一关键词在主题里出现即通过
                if filter_subject_str:
                    keywords = [
                        k.strip().lower()
                        for k in filter_subject_str.replace(";", ",").replace("\n", ",").split(",")
                        if k.strip()
                    ]
                    subject_lower = (subject or "").lower()
                    if keywords and not any(k in subject_lower for k in keywords):
                        logger.info(f"[email_ingest] 跳过 · 主题不含关键词: {subject[:60]}")
                        if account.get("mark_as_read", True):
                            _mark_seen(conn, uid)
                        continue

                attachments = _extract_attachments(msg)
                if not attachments:
                    # 这封邮件没支持的附件 · 也标已读避免下次再扫
                    if account.get("mark_as_read", True):
                        _mark_seen(conn, uid)
                    continue

                result["attachments_found"] += len(attachments)

                import db

                for filename, content in attachments:
                    try:
                        # 幂等:如果这封邮件 UID 之前已经处理过 · 跳过
                        if db.is_email_uid_seen(account["id"], uid.decode()):
                            continue

                        history_id = _ingest_one_attachment(
                            user_id=account["user_id"],
                            account_id=account["id"],
                            uid=uid.decode(),
                            filename=filename,
                            content=content,
                            subject=subject,
                            sender=sender,
                        )
                        # 无论 OCR 是否成功 · 都记一条 seen_uids · 防重复
                        db.mark_email_uid_seen(
                            account_id=account["id"],
                            uid=uid.decode(),
                            history_id=history_id,
                            subject=subject,
                            sender=sender,
                        )
                        if history_id:
                            result["ocr_succeeded"] += 1
                            result["new_history_ids"].append(history_id)
                            # 自动推 ERP(如果用户配了)
                            _auto_push_if_configured(account["user_id"], history_id)
                        else:
                            result["ocr_failed"] += 1
                            result["error_details"].append(
                                {
                                    "uid": uid.decode(),
                                    "subject": subject[:80] if subject else "",
                                    "filename": filename,
                                    "error": "ocr_failed_or_skipped",
                                }
                            )
                    except Exception as e:
                        result["ocr_failed"] += 1
                        result["error_details"].append(
                            {
                                "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                                "subject": (subject or "")[:80],
                                "filename": filename,
                                "error": f"{type(e).__name__}: {str(e)[:200]}",
                            }
                        )

                if account.get("mark_as_read", True):
                    _mark_seen(conn, uid)

            except Exception as e:
                result["error_details"].append(
                    {
                        "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                        "error": f"{type(e).__name__}: {str(e)[:200]}",
                    }
                )

        # 粗略判决 status
        if result["ocr_failed"] > 0 and result["ocr_succeeded"] > 0:
            result["status"] = "partial"
        elif result["ocr_failed"] > 0 and result["ocr_succeeded"] == 0:
            result["status"] = "failed"
            result["error_message"] = "all_ocr_failed"
        else:
            result["status"] = "success"

    except Exception as e:
        logger.exception(f"[email_ingest] account={account.get('id')} 抓取异常")
        result["status"] = "failed"
        result["error_message"] = f"{type(e).__name__}: {str(e)[:200]}"
    finally:
        try:
            conn.logout()
        except Exception:
            pass

    result["elapsed_ms"] = int((time.time() - t0) * 1000)
    logger.info(
        f"[email_ingest] account={account.get('id')} trigger={trigger} "
        f"scanned={result['emails_scanned']} attachments={result['attachments_found']} "
        f"ok={result['ocr_succeeded']} fail={result['ocr_failed']} status={result['status']} "
        f"elapsed={result['elapsed_ms']}ms"
    )
    return result


def test_connection(
    email_addr: str,
    password: str,
    imap_host: str,
    imap_port: int = 993,
    imap_use_ssl: bool = True,
    folder: str = "INBOX",
) -> Dict[str, Any]:
    t0 = time.time()
    result = {"success": False, "error_msg": None, "elapsed_ms": 0, "folder_count": None}
    try:
        if imap_use_ssl:
            conn = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=15)
        else:
            conn = imaplib.IMAP4(imap_host, imap_port, timeout=15)
        conn.login(email_addr, password)
        status, data = conn.select(folder, readonly=True)
        if status == "OK" and data and data[0]:
            try:
                result["folder_count"] = int(data[0])
            except Exception:
                pass
        conn.logout()
        result["success"] = True
    except imaplib.IMAP4.error as e:
        msg = str(e)
        if "AUTHENTICATIONFAILED" in msg.upper() or "Invalid credentials" in msg:
            result["error_msg"] = "auth_failed"
        else:
            result["error_msg"] = f"imap_error: {msg[:200]}"
    except Exception as e:
        result["error_msg"] = f"{type(e).__name__}: {str(e)[:200]}"
    result["elapsed_ms"] = int((time.time() - t0) * 1000)
    return result
