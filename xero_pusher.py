# -*- coding: utf-8 -*-
"""
v118.27.4 · Xero 适配器(OAuth 2.0 · Web app · ACCREC 销售)
=========================================================
铁律:
  - server-side OAuth 2.0(Web app · 有 Client Secret)
  - access_token 30 分钟过期 · refresh_token 60 天过期
  - 1 个 user 可授权多个 organisation · Pearnly 让用户选 1 个默认
  - 推 Invoice 时 Contact 必须存在(Pearnly 不自动建 · 让用户先在 Xero 建)
  - erp_client_mappings.erp_code(用户配)= 当 Xero Contact Name(精确匹配)

环境变量:
  - XERO_CLIENT_ID(在 .env)
  - XERO_CLIENT_SECRET(在 .env)
  - PEARNLY_BASE_URL(默认 https://pearnly.com · 用于 redirect_uri)
"""

import os
import time
import logging
import secrets as _secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# ============================================================
# 配置(从 .env 读)
# ============================================================
XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
XERO_CONNECTIONS_URL = "https://api.xero.com/connections"

XERO_SCOPES = (
    # v118.27.4.1 · 2026-03-02 后新建的 app 必须用 granular scope · broad 已废
    "openid profile email "
    "accounting.contacts accounting.invoices "
    "offline_access"
)

DEFAULT_BASE_URL = "https://pearnly.com"
HTTP_TIMEOUT = 20  # 秒


def _client_id() -> str:
    return (os.environ.get("XERO_CLIENT_ID") or "").strip()


def _client_secret() -> str:
    return (os.environ.get("XERO_CLIENT_SECRET") or "").strip()


def _redirect_uri() -> str:
    base = (os.environ.get("PEARNLY_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return f"{base}/api/erp/xero/auth/callback"


def is_configured() -> bool:
    return bool(_client_id() and _client_secret())


# ============================================================
# OAuth flow
# ============================================================
def build_auth_url(state: str) -> str:
    """生成把用户重定向到 Xero 授权页的 URL"""
    params = {
        "response_type": "code",
        "client_id": _client_id(),
        "redirect_uri": _redirect_uri(),
        "scope": XERO_SCOPES,
        "state": state,
    }
    return XERO_AUTH_URL + "?" + urlencode(params)


def gen_state() -> str:
    return _secrets.token_urlsafe(32)


def exchange_code_for_token(code: str) -> Optional[Dict[str, Any]]:
    """code 换 access_token + refresh_token + id_token"""
    if not code:
        return None
    try:
        r = requests.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _redirect_uri(),
            },
            auth=(_client_id(), _client_secret()),
            headers={"Accept": "application/json"},
            timeout=HTTP_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"exchange_code_for_token failed: {r.status_code} {r.text[:300]}")
            return None
        return r.json()  # {access_token, refresh_token, expires_in, id_token, scope, token_type}
    except Exception as e:
        logger.error(f"exchange_code_for_token exception: {e}")
        return None


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """用 refresh_token 拿新 access_token + 新 refresh_token(rolling)"""
    if not refresh_token:
        return None
    try:
        r = requests.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(_client_id(), _client_secret()),
            headers={"Accept": "application/json"},
            timeout=HTTP_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"refresh_access_token failed: {r.status_code} {r.text[:300]}")
            return None
        return r.json()
    except Exception as e:
        logger.error(f"refresh_access_token exception: {e}")
        return None


def list_organisations(access_token: str) -> List[Dict[str, Any]]:
    """拿用户授权的 Xero organisations 列表"""
    if not access_token:
        return []
    try:
        r = requests.get(
            XERO_CONNECTIONS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
            timeout=HTTP_TIMEOUT,
        )
        if not r.ok:
            logger.error(f"list_organisations failed: {r.status_code} {r.text[:300]}")
            return []
        # [{id, tenantId, tenantType, tenantName, createdDateUtc, updatedDateUtc}]
        return r.json() or []
    except Exception as e:
        logger.error(f"list_organisations exception: {e}")
        return []


def compute_expires_at(expires_in_seconds: int) -> datetime:
    """Xero expires_in 通常 1800 秒 · 留 60 秒安全边"""
    safe = max(60, int(expires_in_seconds or 1800) - 60)
    return datetime.now(timezone.utc) + timedelta(seconds=safe)


# ============================================================
# 推 Invoice(销售 ACCREC)
# ============================================================
def find_contact_by_name(access_token: str, xero_tenant_id: str, name: str) -> Optional[Dict[str, Any]]:
    """精确名匹配查 Xero Contact · 找不到返回 None"""
    if not access_token or not xero_tenant_id or not name:
        return None
    try:
        # Xero Contacts API · WHERE 子句精确匹配(URL 编码)
        params = {"where": f'Name=="{name}"'}
        r = requests.get(
            XERO_API_BASE + "/Contacts",
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Xero-Tenant-Id": xero_tenant_id,
                "Accept": "application/json",
            },
            timeout=HTTP_TIMEOUT,
        )
        if not r.ok:
            logger.warning(f"find_contact_by_name {r.status_code}: {r.text[:200]}")
            return None
        data = r.json() or {}
        contacts = data.get("Contacts") or []
        if not contacts:
            return None
        return contacts[0]
    except Exception as e:
        logger.error(f"find_contact_by_name exception: {e}")
        return None


def _lookup_mapping(mappings: Dict[str, Any], kind: str, key_field: str, key_value: Any) -> Optional[str]:
    items = (mappings or {}).get(kind) or []
    for m in items:
        if m.get('erp_type') == 'xero' and str(m.get(key_field) or '') == str(key_value or ''):
            return (m.get('erp_code') or '').strip() or None
    return None


def _derive_tax_kind(history: Dict[str, Any]) -> str:
    rate = history.get('tax_rate_pct') or history.get('vat_rate')
    try:
        if rate is not None:
            r = float(rate)
            if r == 7:  return 'vat_7'
            if r == 0:  return 'vat_0'
            if r < 0:   return 'vat_exempt'
    except Exception:
        pass
    return 'vat_7'


def build_invoice_payload(history: Dict[str, Any], mappings: Dict[str, Any],
                          contact: Dict[str, Any]) -> Dict[str, Any]:
    """从 OCR history + 映射 + Xero contact 拼 Invoice 推送 body
    Xero Invoice ACCREC(销售 / 应收)
    """
    cid = history.get('client_id') or 0
    inv_no = (history.get('invoice_no') or history.get('invoice_number') or '')[:255]
    inv_date = (history.get('invoice_date') or '')[:10]
    due_date = (history.get('due_date') or inv_date)[:10]

    # 税种 · 取 erp_tax_mappings 的 erp_code 当 Xero TaxType 名(用户配)
    tax_kind = _derive_tax_kind(history)
    tax_type = _lookup_mapping(mappings, 'taxes', 'pearnly_tax_kind', tax_kind) or 'OUTPUT'  # OUTPUT = Xero 默认 7% sales tax

    # 默认科目代码 · 取 revenue_sales 映射(若有)
    account_code = _lookup_mapping(mappings, 'accounts', 'pearnly_category', 'revenue_sales') or '200'

    # 金额(铁律 29 上限)
    def _f(v):
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0

    subtotal = _f(history.get('subtotal') or history.get('amount_before_tax'))
    total    = _f(history.get('total_amount'))
    if subtotal == 0 and total > 0:
        # 用税率反推
        try:
            rate = float(history.get('tax_rate_pct') or 7)
            subtotal = round(total / (1 + rate / 100), 2)
        except Exception:
            subtotal = total
    line_amount = round(subtotal, 2)

    # Xero Invoice ACCREC 标准结构
    return {
        "Type": "ACCREC",
        "Contact": {"ContactID": contact.get("ContactID")},
        "Date": inv_date or None,
        "DueDate": due_date or None,
        "InvoiceNumber": inv_no or None,
        "Reference": f"Pearnly · OCR · {history.get('id', '')[:8]}",
        "LineAmountTypes": "Exclusive",
        "Status": "DRAFT",  # DRAFT 默认 · 老板进 Xero 自己审批改 AUTHORISED
        "LineItems": [{
            "Description": (history.get('description') or 'OCR Invoice')[:400],
            "Quantity": 1,
            "UnitAmount": line_amount,
            "AccountCode": account_code,
            "TaxType": tax_type,
        }],
    }


def push_invoice(access_token: str, xero_tenant_id: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """POST 一张 Invoice · 返回 (ok, response_body 或 error)"""
    if not access_token or not xero_tenant_id:
        return False, {"error": "missing_token"}
    try:
        r = requests.post(
            XERO_API_BASE + "/Invoices",
            json={"Invoices": [payload]},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Xero-Tenant-Id": xero_tenant_id,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=HTTP_TIMEOUT,
        )
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:500]}
        if not r.ok:
            return False, {"http_status": r.status_code, "body": body}
        # 成功返回 {Invoices: [{InvoiceID, ...}]}
        return True, body
    except Exception as e:
        logger.error(f"push_invoice exception: {e}")
        return False, {"error": str(e)[:200]}


# ============================================================
# 错误码 → 4 语友好提示
# ============================================================
XERO_ERROR_FRIENDLY: Dict[str, Dict[str, str]] = {
    'ERR_NOT_CONNECTED': {
        'zh': '还未连接 Xero · 请先去自动化 → ERP 对接 连接 Xero',
        'en': 'Not connected to Xero. Connect first under Automation → ERP.',
        'th': 'ยังไม่ได้เชื่อม Xero · กรุณาเชื่อมที่ ระบบอัตโนมัติ → ERP ก่อน',
        'ja': 'Xero に未接続 · 先に「自動化 → ERP 連携」で接続してください',
    },
    'ERR_TOKEN_EXPIRED': {
        'zh': '连接已失效 · 请重新连接 Xero',
        'en': 'Connection expired. Please reconnect Xero.',
        'th': 'การเชื่อมต่อหมดอายุ · โปรดเชื่อม Xero ใหม่',
        'ja': '接続が失効しました · Xero を再接続してください',
    },
    'ERR_NO_DEFAULT_ORG': {
        'zh': '未选默认 organisation · 请去 Xero 连接卡片选 1 个',
        'en': 'No default organisation. Pick one in the Xero connection card.',
        'th': 'ยังไม่ได้เลือกองค์กรเริ่มต้น · ไปเลือกที่การ์ดเชื่อม Xero',
        'ja': 'デフォルト組織が未設定 · Xero 接続カードで選択してください',
    },
    'ERR_NO_CLIENT_MAPPING': {
        'zh': '该客户在字段映射里没配 Xero 客户名',
        'en': 'No Xero customer name configured for this client in field mapping.',
        'th': 'ลูกค้านี้ยังไม่ได้ตั้งชื่อลูกค้า Xero ในแมปฟิลด์',
        'ja': 'この取引先の Xero 取引先名がフィールドマッピングで未設定',
    },
    'ERR_CONTACT_NOT_FOUND': {
        'zh': 'Xero 里没找到这个客户 · 请先在 Xero 建好客户档案 / 或在字段映射里改成正确的 Xero 客户名',
        'en': 'Customer not found in Xero. Create the contact in Xero first, or fix the Xero customer name in field mapping.',
        'th': 'ไม่พบลูกค้านี้ใน Xero · สร้างผู้ติดต่อใน Xero ก่อน หรือแก้ชื่อใน แมปฟิลด์',
        'ja': 'Xero でこの取引先が見つかりません · Xero で先に作成するか、マッピングを修正',
    },
    'ERR_INVALID_INVOICE': {
        'zh': '发票字段不合法 · 请检查发票号 / 日期 / 金额',
        'en': 'Invoice fields invalid. Check invoice number / date / amount.',
        'th': 'ฟิลด์ใบกำกับไม่ถูกต้อง · ตรวจสอบเลขที่ / วันที่ / ยอดเงิน',
        'ja': '請求書フィールドが無効 · 番号/日付/金額を確認',
    },
    'ERR_RATE_LIMITED': {
        'zh': 'Xero API 限流 · 请等几分钟再推',
        'en': 'Xero API rate-limited. Wait a few minutes.',
        'th': 'Xero API ถูกจำกัด · รอสักครู่',
        'ja': 'Xero API レート制限 · 数分待ってください',
    },
}


def get_error_friendly(error_code: str, lang: str = 'zh') -> str:
    entry = XERO_ERROR_FRIENDLY.get(error_code or "", {})
    return entry.get(lang) or entry.get('en') or (error_code or "")


def parse_xero_error(http_status: int, body: Dict[str, Any]) -> str:
    """Xero 错误响应 → 我们的 ERR_xxx 错误码"""
    if http_status == 401:
        return 'ERR_TOKEN_EXPIRED'
    if http_status == 429:
        return 'ERR_RATE_LIMITED'
    # 400 错误 · Xero body 里可能有 ValidationErrors
    try:
        if isinstance(body, dict):
            elements = body.get('Elements') or []
            for el in elements:
                errs = el.get('ValidationErrors') or []
                for e in errs:
                    msg = (e.get('Message') or '').lower()
                    if 'contact' in msg and ('not' in msg or 'invalid' in msg):
                        return 'ERR_CONTACT_NOT_FOUND'
    except Exception:
        pass
    return 'ERR_INVALID_INVOICE'
