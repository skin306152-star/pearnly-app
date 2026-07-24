# -*- coding: utf-8 -*-
"""ERP 推送失败码 → 4 语友好文案(从 push_log_queries 抽出 · 纯数据 + 查表)。

发票推送 catalog(mrerp_business_friendly.friendly_for_ui)只覆盖 ERR_* 发票推送码;
身份证→订车单(adapter=mrerp_dms)有独立一组 ERR_DMS_* 码,friendly_for_ui 不覆盖 →
不补就在日志/详情/异常里裸露 ERR_*(Zihao 2026-06-01 指出)。friendly_any 统一入口:
发票优先 → 身份证订车兜底。push 日志/详情/异常三处共用。
"""

from typing import Optional, Dict

from services.erp.mrerp_business_friendly import friendly_for_ui

# 身份证→订车单推送/识别错误码的 4 语友好文案(zh/th/en/ja)。
_DMS_PUSH_FRIENDLY: Dict[str, Dict[str, str]] = {
    "ERR_ID_CARD_REQUIRED_FIELDS": {
        "zh": "身份证关键字段未识别完整(身份证号或姓名)· 已暂停建单 · 请用清晰的正面照重新识别",
        "en": "Key ID-card fields (ID number or name) were not fully recognized; booking was paused. Please rescan a clear front image.",
        "th": "อ่านข้อมูลบัตรประชาชนหลัก (เลขบัตร/ชื่อ) ไม่ครบ จึงหยุดสร้างใบจอง กรุณาสแกนภาพด้านหน้าที่ชัดเจนอีกครั้ง",
        "ja": "身分証の主要項目(番号・氏名)を完全に読み取れず、予約作成を停止しました。鮮明な表面の画像で再読み取りしてください。",
    },
    "ERR_DMS_CUSTOMER_CREATE": {
        "zh": "在 DMS 建客户失败 · 请检查身份证上的地址信息后重试",
        "en": "Failed to create the customer in DMS. Please check the address on the ID card and retry.",
        "th": "สร้างลูกค้าใน DMS ไม่สำเร็จ กรุณาตรวจสอบที่อยู่บนบัตรประชาชนแล้วลองใหม่",
        "ja": "DMS での顧客作成に失敗しました。身分証の住所をご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT_REPORT": {
        "zh": "订车单导入 DMS 时被退回(数据校验未过)· 请核对身份证信息后重试",
        "en": "DMS rejected the booking import (data validation failed). Please verify the ID-card data and retry.",
        "th": "DMS ปฏิเสธการนำเข้าใบจอง (ตรวจสอบข้อมูลไม่ผ่าน) กรุณาตรวจสอบข้อมูลบัตรแล้วลองใหม่",
        "ja": "DMS が予約の取り込みを拒否しました(データ検証エラー)。身分証データをご確認のうえ再試行してください。",
    },
    "ERR_DMS_IMPORT": {
        "zh": "订车单导入 DMS 失败 · 请稍后重试",
        "en": "Failed to import the booking into DMS. Please retry shortly.",
        "th": "นำเข้าใบจองรถไปยัง DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "予約データの DMS への取り込みに失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_BOOKING_PATCH": {
        "zh": "订车单已建但补充资料失败 · 请到 DMS 后台核对该单",
        "en": "The booking was created but updating its details failed. Please verify it in the DMS console.",
        "th": "สร้างใบจองแล้วแต่บันทึกรายละเอียดเพิ่มเติมไม่สำเร็จ กรุณาตรวจสอบใบจองในระบบ DMS",
        "ja": "予約は作成されましたが詳細の更新に失敗しました。DMS 管理画面でご確認ください。",
    },
    "ERR_DMS_TEMPLATE": {
        "zh": "获取 DMS 订车单模板失败 · 请稍后重试",
        "en": "Failed to fetch the DMS booking template. Please retry shortly.",
        "th": "ดึงแม่แบบใบจองของ DMS ไม่สำเร็จ กรุณาลองใหม่ภายหลัง",
        "ja": "DMS の予約テンプレート取得に失敗しました。しばらくしてから再試行してください。",
    },
    "ERR_DMS_AUTH": {
        "zh": "DMS 登录失败 · 请到连接向导检查账号和密码",
        "en": "DMS login failed. Please check the username and password in the connection wizard.",
        "th": "เข้าสู่ระบบ DMS ไม่สำเร็จ กรุณาตรวจสอบชื่อผู้ใช้และรหัสผ่านในตัวช่วยเชื่อมต่อ",
        "ja": "DMS へのログインに失敗しました。連携ウィザードでユーザー名とパスワードをご確認ください。",
    },
    "ERR_DMS_NOT_INVOICE_ENDPOINT": {
        "zh": "该连接是身份证订车专用 · 不能用于推送发票",
        "en": "This connection is for ID-card vehicle booking only and cannot push invoices.",
        "th": "การเชื่อมต่อนี้ใช้สำหรับการจองรถด้วยบัตรประชาชนเท่านั้น ไม่สามารถส่งใบกำกับได้",
        "ja": "この連携は身分証による車両予約専用で、請求書の送信には使用できません。",
    },
    "ERR_DMS_TECHNICAL": {
        "zh": "连接 DMS 超时或网络异常 · 请稍后重试",
        "en": "DMS connection timed out or a network error occurred. Please retry shortly.",
        "th": "การเชื่อมต่อ DMS หมดเวลาหรือเครือข่ายขัดข้อง กรุณาลองใหม่ภายหลัง",
        "ja": "DMS への接続がタイムアウトまたはネットワーク異常です。しばらくしてから再試行してください。",
    },
    "ERR_DMS_UNEXPECTED": {
        "zh": "推送 DMS 时发生未知错误 · 请稍后重试或联系客服",
        "en": "An unexpected error occurred while pushing to DMS. Please retry or contact support.",
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิดขณะส่งไป DMS กรุณาลองใหม่หรือติดต่อฝ่ายสนับสนุน",
        "ja": "DMS への送信中に予期しないエラーが発生しました。再試行するかサポートにお問い合わせください。",
    },
}


def dms_push_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中身份证订车错误码 → 返回 {zh,th,en,ja} dict;否则 None。
    按码长度降序匹配(长码先于其前缀短码,如 ERR_DMS_IMPORT_REPORT 先于 ERR_DMS_IMPORT)
    防子串误命中 · 新增码进 _DMS_PUSH_FRIENDLY 即自动生效,无需再维护一份顺序列表。"""
    if not error_msg:
        return None
    for code in sorted(_DMS_PUSH_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _DMS_PUSH_FRIENDLY[code]
    return None


# Express 本地小助手「库存过账」回执码 —— 不带 ERR_ 前缀,作为 error_msg 子串出现
# (DBF_WRITE_FAILED 账套无库存品主档/泰文写盘崩 · STOCK_ITEM_NOT_FOUND 零负库存)。
# 未收录时原始码直接裸露给泰国会计看(2026-07-23 真料排障 F1)。
_EXPRESS_STOCK_FRIENDLY: Dict[str, Dict[str, str]] = {
    "DBF_WRITE_FAILED": {
        "zh": "写入 Express 账套失败 · 常见于该账套还没有库存商品主档 · 请先在 Express 建好库存商品,或本批改用「销售·服务」模式推送",
        "en": "Failed to write into the Express account set — commonly because the set has no stock-item master yet. Please create a stock item in Express first, or push this batch in the “Sales · Service” mode.",
        "th": "เขียนข้อมูลลงชุดบัญชี Express ไม่สำเร็จ มักเป็นเพราะชุดบัญชียังไม่มีสินค้าคงคลังตั้งต้น กรุณาสร้างสินค้าคงคลังใน Express ก่อน หรือส่งชุดนี้ด้วยโหมด «ขาย•บริการ»",
        "ja": "Express の帳簿セットへの書き込みに失敗しました。多くは在庫品マスタが未作成のためです。先に Express で在庫品を作成するか、本バッチを「販売・サービス」モードで送信してください。",
    },
    "STOCK_ITEM_NOT_FOUND": {
        "zh": "该商品在 Express 里库存为零或不足 · 请先在 Express 录入进货或期初库存,再推送",
        "en": "This item has zero or insufficient stock in Express. Please record a purchase or opening balance in Express first, then push again.",
        "th": "สินค้านี้มีสต๊อกใน Express เป็นศูนย์หรือไม่เพียงพอ กรุณาบันทึกการซื้อหรือยอดยกมาใน Express ก่อน แล้วจึงส่งอีกครั้ง",
        "ja": "この商品は Express の在庫がゼロまたは不足しています。先に Express で仕入または期首在庫を登録してから再送信してください。",
    },
}


def express_stock_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """命中 Express 库存过账回执码 → 4 语 dict;否则 None。与 dms_push_friendly 同款:
    按码长度降序子串匹配,新增码进表即生效。"""
    if not error_msg:
        return None
    for code in sorted(_EXPRESS_STOCK_FRIENDLY, key=len, reverse=True):
        if code in error_msg:
            return _EXPRESS_STOCK_FRIENDLY[code]
    return None


def _doc_sanity_friendly(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """单据防呆码(date_implausible/currency_not_thb 等)四语化 · 复用 routing 唯一目录。
    此前只翻 ERR_*,doc_sanity 码在 LINE 失败消息里裸奔(真机 2026-07-02 截图抓到)。"""
    msg = str(error_msg or "")
    if not msg:
        return None
    try:
        from services.erp.mrerp_http.routing import _DOC_SANITY_FRIENDLY

        return next((tr for pfx, tr in _DOC_SANITY_FRIENDLY.items() if pfx in msg), None)
    except Exception:
        return None


def friendly_any(error_msg: Optional[str]) -> Optional[Dict[str, str]]:
    """发票推送 catalog 优先(friendly_for_ui)→ 单据防呆码 → 身份证订车 → Express 库存码。
    给 push 日志/详情/异常/LINE 失败消息统一用 · 任一命中即不裸露内部码。"""
    return (
        friendly_for_ui(error_msg)
        or _doc_sanity_friendly(error_msg)
        or dms_push_friendly(error_msg)
        or express_stock_friendly(error_msg)
    )


def friendly_text(error_msg: Optional[str], lang: str, fallback: str = "") -> str:
    """friendly_any 的取词版:命中给 lang(回落 en),未命中给 fallback。
    LINE 侧三处各写一遍"hit.get(lang) or hit['en']"收敛到这(/simplify 2026-07-03)。"""
    hit = friendly_any(error_msg) or {}
    return hit.get(lang) or hit.get("en") or fallback
