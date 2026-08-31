# -*- coding: utf-8 -*-
"""Shared LINE Messaging API transport for Cowork, DMS, and ERP."""

import os
import hmac
import hashlib
import base64
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


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
        return "th"  # 事件不带 language(图片/普通消息)· 主市场泰国兜底
    # 归一化
    if lang.startswith("th"):
        return "th"
    if lang.startswith("ja"):
        return "ja"
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return "th"


# 三个产品共用 LINE 传输，凭据按产品隔离。
_CHANNEL_ENV = {
    "cowork": ("LINE_CHANNEL_SECRET", "LINE_CHANNEL_ACCESS_TOKEN"),
    "dms": ("LINE_DMS_CHANNEL_SECRET", "LINE_DMS_CHANNEL_ACCESS_TOKEN"),
    "erp": ("LINE_ERP_CHANNEL_SECRET", "LINE_ERP_CHANNEL_ACCESS_TOKEN"),
}


def _channel_env_names(channel: str) -> tuple[str, str]:
    names = _CHANNEL_ENV.get(channel)
    if names:
        return names
    logger.warning("未知 LINE channel profile: %s", channel)
    return "", ""


def _get_channel_secret(channel: str = "cowork") -> str:
    name = _channel_env_names(channel)[0]
    s = os.environ.get(name, "").strip()
    if not s:
        logger.warning(f"{name} 未设置")
    return s


def _get_channel_token(channel: str = "cowork") -> str:
    name = _channel_env_names(channel)[1]
    s = os.environ.get(name, "").strip()
    if not s:
        logger.warning(f"{name} 未设置")
    return s


# ============================================================
# 签名校验
# ============================================================


def verify_signature(body: bytes, signature: str, *, channel: str = "cowork") -> bool:
    """
    校验 LINE webhook 请求合法性。
    算法:HMAC-SHA256(body, channel_secret) → base64 → 对比 X-Line-Signature
    channel:凭据 profile（cowork / dms / erp）。
    """
    secret = _get_channel_secret(channel)
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


def reply_text(reply_token: str, text: str, *, channel: str = "cowork") -> bool:
    """用 replyToken 回复纯文字(replyToken 一次性 · 60 秒内用)"""
    return _reply_messages(reply_token, [{"type": "text", "text": text[:5000]}], channel=channel)


def reply_messages(
    reply_token: str, messages: List[Dict[str, Any]], *, channel: str = "cowork"
) -> bool:
    """回复多条消息(最多 5 条)"""
    return _reply_messages(reply_token, messages[:5], channel=channel)


def _reply_messages(
    reply_token: str, messages: List[Dict[str, Any]], *, channel: str = "cowork"
) -> bool:
    token = _get_channel_token(channel)
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


def push_text(to_line_user_id: str, text: str, *, channel: str = "cowork") -> bool:
    """用 userId 主动推送文字(绑定完成通知 / 异常提醒用)"""
    token = _get_channel_token(channel)
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


def start_loading(
    to_line_user_id: str, loading_seconds: int = 20, *, channel: str = "cowork"
) -> bool:
    """显示「正在输入…」转圈动画(1:1 聊天 · ≤60s · docs/smart-intake/15 §2)。

    收图/调 L2 前立即调,识别完发结果即自动消失。loadingSeconds 取 5 的倍数(API 约束)。
    尽力而为,失败不抛(不得阻塞主流程)。
    """
    token = _get_channel_token(channel)
    if not token or not to_line_user_id:
        return False
    secs = max(5, min(60, (int(loading_seconds) // 5) * 5 or 5))
    payload = json.dumps({"chatId": to_line_user_id, "loadingSeconds": secs}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/chat/loading/start",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 202)
    except Exception as e:
        logger.warning(f"LINE start_loading 失败(不阻塞): {e}")
        return False


def create_rich_menu(payload: Dict[str, Any], channel: str = "cowork") -> Optional[str]:
    """建 Rich Menu(返 richMenuId · 整合用 · 需再 setDefault + 上传背景图)。失败 None。

    payload 由 line_intake.rich_menu_payload 出。真生效还要传背景图 + setDefaultRichMenu,
    属用户验收范围(需真 channel)。
    """
    token = _get_channel_token(channel)
    if not token:
        return None
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/richmenu",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")).get("richMenuId")
    except Exception as e:
        logger.error(f"LINE createRichMenu 失败: {e}")
        return None


def push_messages(
    to_line_user_id: str, messages: List[Dict[str, Any]], *, channel: str = "cowork"
) -> bool:
    """用 userId 主动推送消息列表(Flex 卡 / 多消息)· OCR 异步结果用(镜像 push_text)。"""
    token = _get_channel_token(channel)
    if not token or not to_line_user_id or not messages:
        return False
    url = "https://api.line.me/v2/bot/message/push"
    payload = json.dumps({"to": to_line_user_id, "messages": messages[:5]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        logger.error(f"LINE push_messages 失败: {e}")
        return False


# ============================================================
# 获取用户资料(拿昵称 / 头像)
# ============================================================


def get_user_profile(line_user_id: str, *, channel: str = "cowork") -> Optional[Dict[str, Any]]:
    """
    获取 LINE 用户资料。
    返回:{displayName, userId, pictureUrl, statusMessage} 或 None
    只有 Bot 的好友才能查到 · 其他返回 404
    """
    token = _get_channel_token(channel)
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


def download_message_content(message_id: str, *, channel: str = "cowork") -> Optional[bytes]:
    """下载图片 / 视频 / 音频消息的原始字节"""
    token = _get_channel_token(channel)
    if not token or not message_id:
        return None
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
        # 分段耗时打点(自带 request_id):图片下载段。只记毫秒/大小,不记内容(防票据泄露)。
        logger.info(
            "line: download mid=%s %dms %dKB",
            message_id,
            int((time.monotonic() - t0) * 1000),
            len(data) // 1024,
        )
        return data
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
