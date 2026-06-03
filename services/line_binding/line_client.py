# -*- coding: utf-8 -*-
"""
Mr.Pilot · LINE Messaging API 客户端
T1 轮 2 · v0.19.0 · 2026-04-23

不依赖 line-bot-sdk · 只用 stdlib(hmac / base64 / urllib)
原因:
- 依赖少 · 不污染 requirements.txt
- LINE 官方 API 简单 · 手写更可控
- 将来迁 VPS 也一致
"""

import os
import hmac
import hashlib
import base64
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================
# 文案字典 · 根据用户偏好语言回复(T1 · 2026-04-23)
# ============================================================

from services.line_binding.line_i18n import (  # noqa: F401 · re-export(外部 line_client.X 契约 · format 用 t_ocr)
    LINE_I18N,
    OCR_RESULT_I18N,
    t_line,
    t_ocr,
)


def pick_lang_from_line_event(ev: dict) -> str:
    """
    从 LINE 事件里猜测用户语言(follow 时还没绑定 · 只能靠 LINE 提供的 language)。
    LINE 在 source 或 event 顶层可能带 language 字段(如 'zh-Hant', 'th', 'en', 'ja')
    """
    lang = (ev.get("language") or "").lower()
    if not lang:
        src = ev.get("source") or {}
        lang = (src.get("language") or "").lower()
    if not lang:
        return "zh"
    # 归一化
    if lang.startswith("th"):
        return "th"
    if lang.startswith("ja"):
        return "ja"
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return "zh"


def _get_channel_secret() -> str:
    s = os.environ.get("LINE_CHANNEL_SECRET", "").strip()
    if not s:
        logger.warning("LINE_CHANNEL_SECRET 未设置")
    return s


def _get_channel_token() -> str:
    s = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not s:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN 未设置")
    return s


# ============================================================
# 签名校验
# ============================================================


def verify_signature(body: bytes, signature: str) -> bool:
    """
    校验 LINE webhook 请求合法性。
    算法:HMAC-SHA256(body, channel_secret) → base64 → 对比 X-Line-Signature
    """
    secret = _get_channel_secret()
    if not secret or not signature:
        return False
    try:
        mac = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(mac).decode("utf-8")
        # 用 hmac.compare_digest 防时序攻击
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"verify_signature failed: {e}")
        return False


# ============================================================
# 回复消息(reply · 用 replyToken · 免费)
# ============================================================


def reply_text(reply_token: str, text: str) -> bool:
    """用 replyToken 回复纯文字(replyToken 一次性 · 60 秒内用)"""
    return _reply_messages(reply_token, [{"type": "text", "text": text[:5000]}])


def reply_messages(reply_token: str, messages: List[Dict[str, Any]]) -> bool:
    """回复多条消息(最多 5 条)"""
    return _reply_messages(reply_token, messages[:5])


def _reply_messages(reply_token: str, messages: List[Dict[str, Any]]) -> bool:
    token = _get_channel_token()
    if not token or not reply_token:
        return False
    url = "https://api.line.me/v2/bot/message/reply"
    payload = json.dumps(
        {
            "replyToken": reply_token,
            "messages": messages,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass  # body 读不到就保持空串,下行 logger.error 仍会记 HTTP code
        logger.error(f"LINE reply 失败 {e.code}: {body}")
        return False
    except Exception as e:
        logger.error(f"LINE reply 异常: {e}")
        return False


# ============================================================
# 推送消息(push · 要收费 · 免费套餐每月 500 条)
# ============================================================


def push_text(to_line_user_id: str, text: str) -> bool:
    """用 userId 主动推送文字(绑定完成通知 / 异常提醒用)"""
    token = _get_channel_token()
    if not token or not to_line_user_id:
        return False
    url = "https://api.line.me/v2/bot/message/push"
    payload = json.dumps(
        {
            "to": to_line_user_id,
            "messages": [{"type": "text", "text": text[:5000]}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"LINE push 失败: {e}")
        return False


# ============================================================
# 获取用户资料(拿昵称 / 头像)
# ============================================================


def get_user_profile(line_user_id: str) -> Optional[Dict[str, Any]]:
    """
    获取 LINE 用户资料。
    返回:{displayName, userId, pictureUrl, statusMessage} 或 None
    只有 Bot 的好友才能查到 · 其他返回 404
    """
    token = _get_channel_token()
    if not token or not line_user_id:
        return None
    url = f"https://api.line.me/v2/bot/profile/{line_user_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except urllib.error.HTTPError as e:
        logger.warning(f"LINE get_user_profile {line_user_id} {e.code}")
        return None
    except Exception as e:
        logger.error(f"LINE get_user_profile 异常: {e}")
        return None


# ============================================================
# 下载图片消息内容(T1 轮 3 OCR 用 · 本轮未用)
# ============================================================


def download_message_content(message_id: str) -> Optional[bytes]:
    """下载图片 / 视频 / 音频消息的原始字节"""
    token = _get_channel_token()
    if not token or not message_id:
        return None
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                return None
            return resp.read()
    except Exception as e:
        logger.error(f"LINE download_message_content 异常: {e}")
        return None


# ============================================================
# T1 轮 3 · 图片 → PDF 转换(复用网页 OCR 流程)
# ============================================================


def image_to_pdf_bytes(img_bytes: bytes) -> Optional[bytes]:
    """
    把 LINE 传来的图片 bytes 包成单页 PDF bytes · 直接喂给现有 OCR 引擎。
    依赖 pymupdf(requirements.txt 已有)
    """
    try:
        import fitz  # pymupdf

        # 打开图片
        img_doc = fitz.open(stream=img_bytes, filetype=None)
        # 先把图片转 pixmap 拿尺寸 · 再创建 PDF 页
        page = img_doc[0]
        rect = page.rect
        pdf = fitz.open()
        pdf_page = pdf.new_page(width=rect.width, height=rect.height)
        pdf_page.insert_image(rect, stream=img_bytes)
        pdf_bytes = pdf.tobytes()
        pdf.close()
        img_doc.close()
        return pdf_bytes
    except Exception as e:
        logger.error(f"image_to_pdf_bytes 失败: {e}")
        return None


# ============================================================
# T1 轮 3 · 识别结果文案(4 语)
# ============================================================


def format_ocr_result_for_line(lang: str, pages: list, invoice_count: int = 1) -> str:
    """把 OCR 结果格式化为 LINE 消息文本"""
    if not pages:
        return t_ocr(lang, "err_ocr")

    # 取第一页第一张发票的结构化数据
    first = pages[0] if isinstance(pages, list) else {}
    fields = first.get("fields") or {}

    # 字段名兼容(不同引擎返回可能不一样)
    def _pick(*keys):
        for k in keys:
            v = fields.get(k) or first.get(k)
            if v:
                return str(v)
        return None

    vendor = _pick("seller_name", "vendor", "supplier") or t_ocr(lang, "no_data")
    inv_no = _pick("invoice_no", "invoice_number") or t_ocr(lang, "no_data")
    date = _pick("invoice_date", "date") or t_ocr(lang, "no_data")
    amount = _pick("total_amount", "amount", "total") or t_ocr(lang, "no_data")

    lines = [
        t_ocr(lang, "success_head"),
        "",
        f"{t_ocr(lang, 'field_vendor')}:{vendor}",
        f"{t_ocr(lang, 'field_no')}:{inv_no}",
        f"{t_ocr(lang, 'field_date')}:{date}",
        f"{t_ocr(lang, 'field_amount')}:{amount}",
    ]
    if invoice_count > 1:
        lines.append("")
        lines.append(t_ocr(lang, "multi_invoices", n=invoice_count))
    lines.append("")
    lines.append(t_ocr(lang, "view_on_web"))
    return "\n".join(lines)
