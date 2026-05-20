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

LINE_I18N = {
    "zh": {
        "welcome": (
            "👋 欢迎使用 Mr.Pilot!\n\n"
            "请先到网站绑定账号:\n"
            "1. 登录 https://mr-cloud-mr-cloud.hf.space\n"
            "2. 打开「自动化 → LINE Bot」\n"
            "3. 把那里显示的 6 位数字发给我\n\n"
            "绑定完成后 · 把发票照片发给我 · 我帮你自动识别 ✨"
        ),
        "bind_invalid": "❌ 绑定码无效或已过期。\n请回网站重新获取。",
        "bind_conflict": (
            "❌ 绑定失败 · 此 LINE 账号可能已绑到其他 Mr.Pilot 用户。\n"
            "请先在原账号解绑再试。"
        ),
        "bind_success": (
            "✅ 绑定成功!\n\n"
            "Mr.Pilot 账号:{username}\n"
            "LINE:{display_name}\n\n"
            "接下来把发票照片发给我 · 自动识别入账 📸\n"
            "(图片识别功能即将上线)"
        ),
        "already_bound_hint": (
            "Hi {username} · 已绑定。\n"
            "把发票照片发给我 · 即可自动识别(功能即将上线)。"
        ),
        "need_bind": (
            "👋 请先绑定账号:\n"
            "1. 登录 Mr.Pilot 网站\n"
            "2. 打开「自动化 → LINE Bot」\n"
            "3. 把 6 位数字绑定码发给我"
        ),
        "image_not_bound": (
            "⚠️ 您还没绑定 Mr.Pilot 账号。\n"
            "请到网站「自动化 → LINE Bot」获取绑定码 · 发给我即可。"
        ),
        "image_soon": "📷 收到图片 · 图片识别功能即将上线 · 敬请期待!",
        "unsupported": "暂只支持文字(绑定码)和图片(即将上线)· 谢谢!",
    },
    "en": {
        "welcome": (
            "👋 Welcome to Mr.Pilot!\n\n"
            "Please bind your account first:\n"
            "1. Log in at https://mr-cloud-mr-cloud.hf.space\n"
            "2. Open 'Automation → LINE Bot'\n"
            "3. Send me the 6-digit code shown there\n\n"
            "Once bound, send invoice photos to me and I'll recognize them automatically ✨"
        ),
        "bind_invalid": "❌ Invalid or expired code.\nPlease get a new one from the website.",
        "bind_conflict": (
            "❌ Binding failed · this LINE account may already be bound to another Mr.Pilot user.\n"
            "Please unbind from the original account first."
        ),
        "bind_success": (
            "✅ Bound successfully!\n\n"
            "Mr.Pilot account: {username}\n"
            "LINE: {display_name}\n\n"
            "Now send me invoice photos · I'll auto-recognize and file them 📸\n"
            "(Image recognition coming soon)"
        ),
        "already_bound_hint": (
            "Hi {username} · already bound.\n"
            "Send me invoice photos for auto-recognition (coming soon)."
        ),
        "need_bind": (
            "👋 Please bind first:\n"
            "1. Log in to Mr.Pilot website\n"
            "2. Open 'Automation → LINE Bot'\n"
            "3. Send me the 6-digit binding code"
        ),
        "image_not_bound": (
            "⚠️ You haven't bound a Mr.Pilot account yet.\n"
            "Go to 'Automation → LINE Bot' on the website to get a binding code."
        ),
        "image_soon": "📷 Image received · recognition feature coming soon!",
        "unsupported": "Only text (binding codes) and images (coming soon) are supported · thanks!",
    },
    "th": {
        "welcome": (
            "👋 ยินดีต้อนรับสู่ Mr.Pilot!\n\n"
            "กรุณาผูกบัญชีก่อน:\n"
            "1. เข้าสู่ระบบที่ https://mr-cloud-mr-cloud.hf.space\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot'\n"
            "3. ส่งรหัส 6 หลักที่แสดงไว้มาให้เรา\n\n"
            "หลังผูกบัญชี · ส่งรูปใบกำกับมา · จะอ่านให้อัตโนมัติ ✨"
        ),
        "bind_invalid": "❌ รหัสไม่ถูกต้องหรือหมดอายุ\nกรุณารับรหัสใหม่จากเว็บไซต์",
        "bind_conflict": (
            "❌ ผูกบัญชีไม่สำเร็จ · LINE นี้อาจถูกผูกกับ Mr.Pilot บัญชีอื่นแล้ว\n"
            "กรุณายกเลิกที่บัญชีเดิมก่อน"
        ),
        "bind_success": (
            "✅ ผูกบัญชีสำเร็จ!\n\n"
            "บัญชี Mr.Pilot: {username}\n"
            "LINE: {display_name}\n\n"
            "ส่งรูปใบกำกับมาได้เลย · จะอ่านและบันทึกอัตโนมัติ 📸\n"
            "(ฟีเจอร์อ่านรูปกำลังมา)"
        ),
        "already_bound_hint": (
            "สวัสดี {username} · ผูกบัญชีเรียบร้อย\n"
            "ส่งรูปใบกำกับมา · จะอ่านให้อัตโนมัติ (กำลังมา)"
        ),
        "need_bind": (
            "👋 กรุณาผูกบัญชีก่อน:\n"
            "1. เข้าสู่เว็บ Mr.Pilot\n"
            "2. เปิด 'ระบบอัตโนมัติ → LINE Bot'\n"
            "3. ส่งรหัส 6 หลักมาให้เรา"
        ),
        "image_not_bound": (
            "⚠️ ยังไม่ได้ผูกบัญชี Mr.Pilot\n"
            "ไปที่ 'ระบบอัตโนมัติ → LINE Bot' บนเว็บไซต์เพื่อรับรหัสผูกบัญชี"
        ),
        "image_soon": "📷 รับรูปแล้ว · ฟีเจอร์อ่านรูปกำลังมา · โปรดรอ!",
        "unsupported": "รองรับเฉพาะข้อความ (รหัสผูกบัญชี) และรูป (กำลังมา) · ขอบคุณ!",
    },
    "ja": {
        "welcome": (
            "👋 Mr.Pilot へようこそ!\n\n"
            "まずアカウントを紐付けてください:\n"
            "1. https://mr-cloud-mr-cloud.hf.space にログイン\n"
            "2. 「自動化 → LINE Bot」を開く\n"
            "3. そこに表示される 6 桁の数字を送信\n\n"
            "紐付け完了後 · 請求書の写真を送ると自動認識します ✨"
        ),
        "bind_invalid": "❌ コードが無効または期限切れです。\nウェブサイトから新しいコードを取得してください。",
        "bind_conflict": (
            "❌ 紐付け失敗 · この LINE は別の Mr.Pilot アカウントに紐付け済みの可能性があります。\n"
            "元のアカウントで先に解除してください。"
        ),
        "bind_success": (
            "✅ 紐付け成功!\n\n"
            "Mr.Pilot アカウント: {username}\n"
            "LINE: {display_name}\n\n"
            "請求書の写真を送ってください · 自動で認識して記録します 📸\n"
            "(画像認識は近日公開)"
        ),
        "already_bound_hint": (
            "こんにちは {username} · 紐付け済みです。\n"
            "請求書の写真を送ると自動認識します(近日公開)。"
        ),
        "need_bind": (
            "👋 まず紐付けしてください:\n"
            "1. Mr.Pilot サイトにログイン\n"
            "2. 「自動化 → LINE Bot」を開く\n"
            "3. 6 桁のコードを送信"
        ),
        "image_not_bound": (
            "⚠️ Mr.Pilot アカウントがまだ紐付けされていません。\n"
            "サイトの「自動化 → LINE Bot」でコードを取得してください。"
        ),
        "image_soon": "📷 画像を受信しました · 画像認識機能は近日公開!",
        "unsupported": "テキスト(紐付けコード)と画像(近日公開)のみ対応しています · ありがとうございます!",
    },
}


def t_line(lang: Optional[str], key: str, **kwargs) -> str:
    """
    取 LINE 场景文案。
    lang:zh/en/th/ja · 其他/None 默认用 zh
    key:文案 key
    kwargs:格式化变量(如 username / display_name)
    """
    if lang not in LINE_I18N:
        lang = "zh"
    tmpl = LINE_I18N[lang].get(key) or LINE_I18N["zh"].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl


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
    payload = json.dumps({
        "replyToken": reply_token,
        "messages": messages,
    }).encode("utf-8")
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
# 推送消息(push · LINE 官方计费限制按账号配置)
# ============================================================

def push_text(to_line_user_id: str, text: str) -> bool:
    """用 userId 主动推送文字(绑定完成通知 / 异常提醒用)"""
    token = _get_channel_token()
    if not token or not to_line_user_id:
        return False
    url = "https://api.line.me/v2/bot/message/push"
    payload = json.dumps({
        "to": to_line_user_id,
        "messages": [{"type": "text", "text": text[:5000]}],
    }).encode("utf-8")
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

OCR_RESULT_I18N = {
    "zh": {
        "processing": "📸 收到图片 · 正在识别...",
        "success_head": "✅ 识别完成",
        "field_vendor": "供应商",
        "field_no": "发票号",
        "field_date": "日期",
        "field_amount": "金额",
        "no_data": "(未识别出)",
        "multi_invoices": "📦 识别出 {n} 张发票(仅显示第 1 张 · 完整结果请查网页历史)",
        "err_download": "❌ 图片下载失败 · 请重发",
        "err_ocr": "❌ 识别失败 · 请换张清晰点的照片再试",
        "err_quota": "⚠️ 余额不足或额度暂不可用 · 请充值或联系管理员",
        "err_service": "⚠️ 识别服务暂不可用 · 请联系管理员",
        "err_account": "⚠️ 账号暂不可用 · 请联系管理员",
        "view_on_web": "网页历史记录查看详情 👉 https://mr-cloud-mr-cloud.hf.space",
    },
    "en": {
        "processing": "📸 Image received · recognizing...",
        "success_head": "✅ Recognition complete",
        "field_vendor": "Vendor",
        "field_no": "Invoice No",
        "field_date": "Date",
        "field_amount": "Amount",
        "no_data": "(not detected)",
        "multi_invoices": "📦 {n} invoices detected (showing #1 only · see web history for all)",
        "err_download": "❌ Image download failed · please resend",
        "err_ocr": "❌ Recognition failed · try a clearer photo",
        "err_quota": "⚠️ Balance is insufficient or usage is unavailable · please top up or contact admin",
        "err_service": "⚠️ Recognition service is unavailable · please contact admin",
        "err_account": "⚠️ Account unavailable · please contact admin",
        "view_on_web": "View details in web history 👉 https://mr-cloud-mr-cloud.hf.space",
    },
    "th": {
        "processing": "📸 รับรูปแล้ว · กำลังอ่าน...",
        "success_head": "✅ อ่านเสร็จแล้ว",
        "field_vendor": "ผู้ขาย",
        "field_no": "เลขที่ใบกำกับ",
        "field_date": "วันที่",
        "field_amount": "ยอดเงิน",
        "no_data": "(ไม่พบ)",
        "multi_invoices": "📦 พบ {n} ใบ (แสดงเฉพาะใบแรก · ดูทั้งหมดในเว็บ)",
        "err_download": "❌ ดาวน์โหลดรูปไม่สำเร็จ · กรุณาส่งใหม่",
        "err_ocr": "❌ อ่านไม่สำเร็จ · ลองถ่ายให้ชัดขึ้น",
        "err_quota": "⚠️ ยอดไม่พอหรือการใช้งานยังไม่พร้อม · กรุณาเติมเงินหรือติดต่อผู้ดูแล",
        "err_service": "⚠️ บริการอ่านเอกสารยังไม่พร้อม · กรุณาติดต่อผู้ดูแล",
        "err_account": "⚠️ บัญชีไม่พร้อมใช้งาน · กรุณาติดต่อผู้ดูแล",
        "view_on_web": "ดูรายละเอียดบนเว็บ 👉 https://mr-cloud-mr-cloud.hf.space",
    },
    "ja": {
        "processing": "📸 画像を受信 · 認識中...",
        "success_head": "✅ 認識完了",
        "field_vendor": "取引先",
        "field_no": "請求書番号",
        "field_date": "日付",
        "field_amount": "金額",
        "no_data": "(検出されず)",
        "multi_invoices": "📦 {n} 枚検出(1 枚目のみ表示 · 全件は Web で確認)",
        "err_download": "❌ 画像ダウンロード失敗 · 再送信してください",
        "err_ocr": "❌ 認識失敗 · より鮮明な写真でお試しください",
        "err_quota": "⚠️ 残高不足、または利用できません · チャージまたは管理者にお問い合わせください",
        "err_service": "⚠️ 認識サービスは現在利用できません · 管理者にお問い合わせください",
        "err_account": "⚠️ アカウント利用不可 · 管理者にお問い合わせください",
        "view_on_web": "Web で履歴を確認 👉 https://mr-cloud-mr-cloud.hf.space",
    },
}


def t_ocr(lang: Optional[str], key: str, **kwargs) -> str:
    """OCR 场景文案"""
    if lang not in OCR_RESULT_I18N:
        lang = "zh"
    tmpl = OCR_RESULT_I18N[lang].get(key) or OCR_RESULT_I18N["zh"].get(key) or key
    if kwargs:
        try:
            return tmpl.format(**kwargs)
        except Exception:
            return tmpl
    return tmpl


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
    date   = _pick("invoice_date", "date") or t_ocr(lang, "no_data")
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
