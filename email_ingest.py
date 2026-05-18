# -*- coding: utf-8 -*-
"""
Mr.Pilot · v0.17 · M6 邮箱附件抓取
职责:
  - 从用户邮箱(IMAP)拉取未读邮件 · 提取 PDF/图片附件
  - 喂给 Gemini OCR → 写 ocr_history · 触发自动 ERP 推送
  - 记录抓取日志到 email_ingest_logs
  - 单账号账号 + 应用密码(不走 OAuth · MVP 简化)

安全:
  - 密码用 Fernet 对称加密 · 密钥从环境变量 EMAIL_ENCRYPTION_KEY 读
  - 首次运行如无密钥会生成一个 · 打印到日志 · 部署者必须保存到环境变量

本模块本轮只做骨架 + 加密工具 · 真实抓取逻辑放到 _fetch_imap_attachments
下一轮再接到 FastAPI 定时任务和前端接口
"""
import os
import time
import base64
import logging
import email
import imaplib
from email.header import decode_header
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================
# 加密:Fernet(cryptography 库 · 如未装则回退到 base64 警告模式)
# ============================================================
_FERNET = None
_FERNET_INIT_DONE = False


def _get_fernet():
    """懒加载 Fernet · 失败不炸 · 降级 base64 + 警告"""
    global _FERNET, _FERNET_INIT_DONE
    if _FERNET_INIT_DONE:
        return _FERNET
    _FERNET_INIT_DONE = True
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.error("[email_ingest] cryptography 未安装 · 密码将降级 base64 明文存储(不安全 · 仅开发用)")
        return None

    key = os.environ.get("EMAIL_ENCRYPTION_KEY", "").strip()
    if not key:
        # 首次生成一个提示给部署者
        generated = Fernet.generate_key().decode()
        logger.error("=" * 60)
        logger.error("[email_ingest] EMAIL_ENCRYPTION_KEY 未配置!")
        logger.error(f"请在 HF Space Secrets 中添加:")
        logger.error(f"  EMAIL_ENCRYPTION_KEY = {generated}")
        logger.error("未配置前邮箱抓取功能将禁用")
        logger.error("=" * 60)
        return None

    try:
        _FERNET = Fernet(key.encode() if isinstance(key, str) else key)
        logger.info("[email_ingest] Fernet 加密已就绪")
        return _FERNET
    except Exception as e:
        logger.error(f"[email_ingest] Fernet 初始化失败: {e}")
        return None


def encrypt_password(plaintext: str) -> bytes:
    """加密密码 · 返回 bytes(存 bytea 字段)"""
    f = _get_fernet()
    if not plaintext:
        return b""
    if f is None:
        # 降级模式 · 至少不是明文(但不是真的加密)
        return base64.b64encode(plaintext.encode("utf-8"))
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_password(cipher: bytes) -> Optional[str]:
    """解密密码 · 返回明文或 None"""
    if not cipher:
        return None
    f = _get_fernet()
    if f is None:
        try:
            return base64.b64decode(cipher).decode("utf-8")
        except Exception:
            return None
    try:
        return f.decrypt(bytes(cipher)).decode("utf-8")
    except Exception as e:
        logger.error(f"[email_ingest] 解密失败: {e}")
        return None


def is_available() -> bool:
    """外部判断邮箱抓取是否可用"""
    return _get_fernet() is not None


# ============================================================
# IMAP 预设(主流服务的默认配置 · 前端下拉选)
# ============================================================
IMAP_PRESETS = {
    "gmail":   {"host": "imap.gmail.com",         "port": 993, "ssl": True},
    "outlook": {"host": "outlook.office365.com",  "port": 993, "ssl": True},
    "yahoo":   {"host": "imap.mail.yahoo.com",    "port": 993, "ssl": True},
    "icloud":  {"host": "imap.mail.me.com",       "port": 993, "ssl": True},
    "qq":      {"host": "imap.qq.com",            "port": 993, "ssl": True},
    "163":     {"host": "imap.163.com",           "port": 993, "ssl": True},
    # 通用 · 用户自填
    "custom":  {"host": "",                       "port": 993, "ssl": True},
}


# ============================================================
# IMAP 抓取主函数(骨架 · 真正的抓取逻辑)
# ============================================================

# 支持的附件扩展名(OCR 能处理的)
_SUPPORTED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

# 首次抓取时向前追溯多少天
INITIAL_DAYS_BACK = 7

# 单次最多处理多少封邮件
MAX_EMAILS_PER_RUN = 20


def _decode_mime(s) -> str:
    """解码 MIME 编码的邮件头(如 =?UTF-8?B?...?=)"""
    if s is None:
        return ""
    parts = decode_header(s)
    out = []
    for text, enc in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", errors="replace"))
            except Exception:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _extract_attachments(msg) -> List[Tuple[str, bytes]]:
    """
    从 email.Message 中抽取支持的附件 · 返回 [(filename, content_bytes)]
    跳过内联图片(Content-Disposition=inline)和不支持的扩展名
    """
    results = []
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        if not filename:
            continue
        filename = _decode_mime(filename)
        ext = os.path.splitext(filename.lower())[1]
        if ext not in _SUPPORTED_EXTS:
            continue
        disp = (part.get("Content-Disposition") or "").lower()
        if "inline" in disp and "attachment" not in disp:
            # 内联图片(如邮件签名)· 跳过
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        results.append((filename, payload))
    return results


def _connect_imap(account: Dict[str, Any]) -> Optional[imaplib.IMAP4]:
    """建 IMAP 连接 · 失败返回 None"""
    host = account["imap_host"]
    port = int(account.get("imap_port") or 993)
    use_ssl = bool(account.get("imap_use_ssl", True))
    try:
        if use_ssl:
            conn = imaplib.IMAP4_SSL(host, port, timeout=20)
        else:
            conn = imaplib.IMAP4(host, port, timeout=20)
        password = decrypt_password(account["password_enc"])
        if password is None:
            logger.error(f"[email_ingest] 账号密码解密失败 · account_id={account['id']}")
            return None
        conn.login(account["email_address"], password)
        return conn
    except Exception as e:
        logger.error(f"[email_ingest] IMAP 连接失败 {host}:{port} · {type(e).__name__}: {e}")
        return None


def _search_unread_with_attachments(conn: imaplib.IMAP4, folder: str, since_days: int) -> List[bytes]:
    """搜未读邮件 · 返回 UID 列表"""
    try:
        conn.select(folder, readonly=False)
        since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")
        # UNSEEN = 未读 · SINCE 是日期下限 · HAS ATTACHMENT 不是所有服务器都支持 · 所以下载后再过滤附件
        status, data = conn.uid("SEARCH", None, f'(UNSEEN SINCE "{since_date}")')
        if status != "OK" or not data or not data[0]:
            return []
        return data[0].split()
    except Exception as e:
        logger.error(f"[email_ingest] IMAP 搜索失败: {type(e).__name__}: {e}")
        return []


def _fetch_email(conn: imaplib.IMAP4, uid: bytes):
    """根据 UID 取整封邮件 · 返回 email.Message 或 None"""
    try:
        status, data = conn.uid("FETCH", uid, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            return None
        raw = data[0][1]
        return email.message_from_bytes(raw)
    except Exception as e:
        logger.error(f"[email_ingest] FETCH {uid} 失败: {type(e).__name__}: {e}")
        return None


def _mark_seen(conn: imaplib.IMAP4, uid: bytes):
    """标已读"""
    try:
        conn.uid("STORE", uid, "+FLAGS", "\\Seen")
    except Exception as e:
        logger.warning(f"[email_ingest] 标已读失败 uid={uid}: {e}")


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
    # PDF 或图片 · 图片需要先转 PDF(复用 jsPDF 方案不行 · 用 PIL + reportlab 简化:只支持 PDF)
    ext = os.path.splitext(filename.lower())[1]
    if ext != ".pdf":
        # v0.17 轮 2 暂只支持 PDF 附件 · 图片走下轮扩展
        logger.info(f"[email_ingest] 跳过非 PDF 附件 · {filename}")
        return None

    # 用户限额/quota 检查
    user = db.find_user_by_id(user_id)
    if not user:
        logger.warning(f"[email_ingest] user_id={user_id} 不存在")
        return None

    # 页数检查(复用 ocr_engine)
    try:
        from ocr_engine import count_pdf_pages
        page_count = count_pdf_pages(content)
        if page_count == 0:
            logger.warning(f"[email_ingest] 无法解析 PDF · {filename}")
            return None
        if page_count > 50:
            logger.warning(f"[email_ingest] PDF 页数超限 · {filename} ({page_count}页)")
            return None
    except Exception as e:
        logger.error(f"[email_ingest] 读取 PDF 页数失败: {e}")
        return None

    # Gemini API key · 优先用户自带 · 否则系统 key(若月付额度够)
    user_key = db.get_user_gemini_key(user_id)
    monthly_quota = user.get("monthly_quota")
    if not user_key:
        # 月付用户 · 检查配额
        if monthly_quota is None:
            logger.warning(f"[email_ingest] 用户 {user_id} 未配 API key 且非月付 · 跳过")
            return None
        used = db.get_user_monthly_usage(user_id)
        if used + page_count > monthly_quota:
            logger.warning(f"[email_ingest] 用户 {user_id} 额度不足 · 跳过 · used={used} quota={monthly_quota}")
            return None

    # 调 OCR
    # Round 2 · 新 pipeline 接入(feature-flag-gated)
    api_key = user_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("[email_ingest] 没有可用的 Gemini API key")
        return None

    result = None
    _pipeline_cost_thb = None

    if os.environ.get("OCR_USE_NEW_PIPELINE", "false").strip().lower() == "true":
        try:
            from services.ocr.pipeline import run_on_pdf_bytes as _pipeline_run
            from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
            _pipe_res = _pipeline_run(content, max_pages=50, api_key=api_key)
            result = pipeline_result_to_legacy_dict(_pipe_res)
            _pipeline_cost_thb = float(_pipe_res.estimated_cost_thb)
            logger.info(
                f"🆕 [email_ingest] pipeline_v1 · {filename} · pages={_pipe_res.page_count} "
                f"· cost=฿{_pipeline_cost_thb:.4f}"
            )
        except Exception as _pipe_err:
            logger.warning(
                f"[email_ingest] pipeline_v1 失败 · fallback Gemini · {filename} · "
                f"{type(_pipe_err).__name__}: {_pipe_err}"
            )
            result = None
            _pipeline_cost_thb = None

    if result is None:
        try:
            import gemini_engine
            result = gemini_engine.recognize_pdf(content, api_key=api_key, max_pages=50)
        except Exception as e:
            logger.error(f"[email_ingest] Gemini 识别失败 · {filename}: {e}")
            return None

    if not result or not result.get("pages"):
        logger.warning(f"[email_ingest] 识别结果为空 · {filename}")
        return None

    pages = result["pages"]

    # 扣配额(月付用户)
    if not user_key and monthly_quota is not None:
        try:
            db.increment_user_monthly_usage(user_id, page_count)
        except Exception as e:
            logger.warning(f"[email_ingest] 扣配额失败: {e}")

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
        first_main = next((p for p in pages if not p.get("is_duplicate") and not p.get("is_copy")), None)
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
        filename=filename,
        page_count=page_count,
        pages=pages,
        confidence=confidence,
        elapsed_ms=int(result.get("elapsed_ms") or 0),
        file_size_kb=len(content) // 1024,
        file_hash=None,  # 邮件附件不用文件 hash 缓存(防止用户重发同文件跳过)
        archive_name=archive_name,
        category_tag=category_tag,
        source="email",
        source_ref=source_ref,
    )

    # Round 2 · pipeline 路径强制 cost 埋点(email_ingest 此前完全漏记)
    # 旧 Gemini 路径维持原样(等全切后另行处理)
    if _pipeline_cost_thb is not None:
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
            logger.info(f"[email_ingest] 未读 {len(uids)} 封 · 本次只处理前 {MAX_EMAILS_PER_RUN} 封")
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
                    senders = [s.strip().lower() for s in filter_sender_str.replace(";", ",").replace("\n", ",").split(",") if s.strip()]
                    sender_lower = (sender or "").lower()
                    if senders and not any(s in sender_lower for s in senders):
                        logger.info(f"[email_ingest] 跳过 · 发件人不在白名单: {sender[:60]}")
                        if account.get("mark_as_read", True):
                            _mark_seen(conn, uid)
                        continue
                # 主题关键词:任一关键词在主题里出现即通过
                if filter_subject_str:
                    keywords = [k.strip().lower() for k in filter_subject_str.replace(";", ",").replace("\n", ",").split(",") if k.strip()]
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
                            result["error_details"].append({
                                "uid": uid.decode(),
                                "subject": subject[:80] if subject else "",
                                "filename": filename,
                                "error": "ocr_failed_or_skipped",
                            })
                    except Exception as e:
                        result["ocr_failed"] += 1
                        result["error_details"].append({
                            "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                            "subject": (subject or "")[:80],
                            "filename": filename,
                            "error": f"{type(e).__name__}: {str(e)[:200]}",
                        })

                if account.get("mark_as_read", True):
                    _mark_seen(conn, uid)

            except Exception as e:
                result["error_details"].append({
                    "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                    "error": f"{type(e).__name__}: {str(e)[:200]}",
                })

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


# ============================================================
# 测试连接(给前端"测试连接"按钮用 · 只登录不抓附件)
# ============================================================
def test_connection(email_addr: str, password: str, imap_host: str,
                    imap_port: int = 993, imap_use_ssl: bool = True,
                    folder: str = "INBOX") -> Dict[str, Any]:
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
