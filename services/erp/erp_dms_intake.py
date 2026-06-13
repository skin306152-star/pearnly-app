# -*- coding: utf-8 -*-
"""DMS 身份证「识别→可编辑面板→确认推送」两步流的服务封装。

dms_routes 的三个新端点调这里:
- recognize_lookup_mrerp_dms:登录一次 → 查 DMS 客户 + 解析 OCR 地址为级联 ids +
  府/县/区/邮编选项 + 称谓 + 订车主档 → 一次性喂面板。
- geo_mrerp_dms:面板改地址时的级联代理。优先用缓存 cookie + httpx(只读·快),
  失效再 Playwright 重登录并刷新缓存。
- push_idcard_fields_mrerp_dms:用面板编辑后的字段建/改客户(save_customer)+ 建订车单。

会话 cookie 缓存(进程级·短 TTL):登录成本高,级联只读复用 cookie 避免每次重登录。
写操作(建/改客户、订车单)仍走 Playwright(铁律#7);cookie 只用于只读级联。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from services.erp.erp_dms_push import (
    _build_mrerp_dms_adapter,
    _dms_friendly,
    _id_card_payload_from_dict,
)

logger = logging.getLogger(__name__)

_SESSION_TTL_S = 600
_session_cache: Dict[str, Dict[str, Any]] = {}


def _cache_key(endpoint: Dict[str, Any]) -> str:
    return str(endpoint.get("id") or endpoint.get("config", {}).get("system_url") or "dms")


def _cookies_put(endpoint: Dict[str, Any], cookies: List[dict], base_url: str) -> None:
    if cookies:
        _session_cache[_cache_key(endpoint)] = {
            "cookies": cookies,
            "base": base_url,
            "exp": time.time() + _SESSION_TTL_S,
        }


def _cookies_get(endpoint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ent = _session_cache.get(_cache_key(endpoint))
    if ent and ent["exp"] > time.time():
        return ent
    return None


class _CookieTransport:
    """httpx transport(带登录 cookie)· 鸭子类型同 PlaywrightTransport · 仅用于只读级联。
    若响应像登录页(会话过期)→ 抛错让调用方回退 Playwright 重登录。"""

    def __init__(self, base_url: str, cookies: List[dict]):
        import httpx

        jar = {c.get("name"): c.get("value") for c in (cookies or []) if c.get("name")}
        self._c = httpx.Client(cookies=jar, timeout=20.0, follow_redirects=True)

    def _wrap(self, r):
        from services.erp.mrerp_dms_adapter import _Resp

        body = r.content or b""
        text = body.decode("utf-8", "replace")
        if "txtpasswords" in text or "checklogin.php" in text:
            raise _StaleSession()
        return _Resp(r.status_code, text, body)

    def get(self, url: str, timeout_ms: Optional[int] = None):
        return self._wrap(self._c.get(url))

    def post(self, url: str, data=None, files=None, timeout_ms: Optional[int] = None):
        form = {k: str(v) for k, v in (data or {}).items()}
        return self._wrap(self._c.post(url, data=form))


class _StaleSession(Exception):
    pass


def _err(code: str, raw: str = "") -> Dict[str, Any]:
    return {
        "ok": False,
        "error_code": code,
        "error_friendly": _dms_friendly(code),
        "raw_error": (raw or "")[:300],
    }


def _run_logged_in(endpoint: Dict[str, Any], fn):
    """Build adapter → login → fn(client, adapter) → cache cookies. Maps DMS
    errors to friendly dicts. NEVER raises."""
    cfg = endpoint.get("config") or {}
    adapter, build_err = _build_mrerp_dms_adapter(cfg)
    if build_err:
        return _err(build_err["error_code"], build_err["raw"])
    try:
        from services.erp.mrerp_dms_adapter import MrerpDmsAuthError, MrerpDmsTechnicalError
        from services.erp.mrerp_dms_client_base import DMSClientError

        try:
            with adapter:
                adapter.login()
                out = fn(adapter._client(), adapter)
                _cookies_put(endpoint, adapter.session_cookies(), adapter.base_url)
                return out
        except MrerpDmsAuthError as e:
            return _err("ERR_DMS_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsTechnicalError as e:
            return _err("ERR_DMS_TECHNICAL", f"{type(e).__name__}: {e}")
        except DMSClientError as e:
            return _err(e.error_code or "ERR_DMS_TECHNICAL", str(e))
    except Exception as e:
        logger.exception("dms intake op failed")
        return _err("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")


def recognize_lookup_mrerp_dms(
    endpoint: Dict[str, Any], *, people_id: str, ocr_address: Dict[str, Any]
) -> Dict[str, Any]:
    """OCR 后:查 DMS 客户 + 解析 OCR 地址级联 + 选项 + 称谓 + 订车主档。"""

    def _do(cl, adapter):
        from services.erp.mrerp_dms_models import ThaiAddress

        look = cl.lookup_customer(people_id)
        form_html = cl._post_text("cus/form.php", {"status": "n"})
        a = ocr_address or {}
        addr = ThaiAddress(
            house_no=str(a.get("house_no") or ""),
            moo=str(a.get("moo") or ""),
            soi=str(a.get("soi") or ""),
            road=str(a.get("road") or ""),
            province_name=str(a.get("province") or a.get("province_name") or ""),
            district_name=str(a.get("district") or a.get("district_name") or ""),
            subdistrict_name=str(a.get("subdistrict") or a.get("subdistrict_name") or ""),
            zipcode=str(a.get("zipcode") or ""),
        )
        resolved = cl._resolve_address_geo(addr, form_html)
        geo = {
            "provinces": cl._select_options(form_html, "selprovinces"),
            "districts": (
                cl.list_geo("districts", resolved.province_id) if resolved.province_id else []
            ),
            "subdistricts": (
                cl.list_geo("subdistricts", resolved.district_id) if resolved.district_id else []
            ),
            "zipcodes": (
                cl.list_geo("zipcodes", resolved.subdistrict_id) if resolved.subdistrict_id else []
            ),
            "selected": {
                "province_id": resolved.province_id,
                "district_id": resolved.district_id,
                "subdistrict_id": resolved.subdistrict_id,
                "zipcode_id": resolved.zipcode_id,
            },
            "text": {
                "house_no": addr.house_no,
                "moo": addr.moo,
                "soi": addr.soi,
                "road": addr.road,
            },
        }
        masters = adapter.test_connection().get("masters", {})
        return {
            "ok": True,
            "match": {
                "found": look["found"],
                "customer_id": look["customer_id"],
                "current_fields": look["fields"],
            },
            "geo": geo,
            "prefixes": cl._select_options(form_html, "selprefix"),
            "masters": masters,
        }

    return _run_logged_in(endpoint, _do)


def geo_mrerp_dms(endpoint: Dict[str, Any], *, level: str, parent_id: str = "") -> Dict[str, Any]:
    """地址级联选项。优先缓存 cookie + httpx(快);失效回退 Playwright。"""
    cached = _cookies_get(endpoint)
    if cached:
        try:
            from services.erp.mrerp_dms_client import DMSClient

            cl = DMSClient(_CookieTransport(cached["base"], cached["cookies"]), cached["base"])
            return {"ok": True, "options": cl.list_geo(level, parent_id)}
        except _StaleSession:
            _session_cache.pop(_cache_key(endpoint), None)
        except Exception as e:
            logger.warning(f"[dms] geo httpx fallback: {type(e).__name__}: {e}")

    def _do(cl, adapter):
        return {"ok": True, "options": cl.list_geo(level, parent_id)}

    return _run_logged_in(endpoint, _do)


def push_idcard_fields_mrerp_dms(
    endpoint: Dict[str, Any],
    *,
    fields: Dict[str, Any],
    mode: str,
    customer_id: Optional[str],
    booking_overrides: Dict[str, Any],
) -> Dict[str, Any]:
    """面板编辑字段 → 建/改客户 + 建订车单。返回 dms_routes 写日志/响应用的 dict。"""
    t0 = time.time()

    def _do(cl, adapter):
        from datetime import date, timedelta
        from services.erp.mrerp_dms_client import excel_serial
        from services.erp.mrerp_dms_models import BookingDefaults

        cid = cl.save_customer(fields=fields, mode=mode, customer_id=customer_id)
        card = _id_card_payload_from_dict(_fields_to_idcard(fields))
        cfg = endpoint.get("config") or {}
        merged = dict(cfg.get("booking_defaults") or {})
        merged.update({k: v for k, v in (booking_overrides or {}).items() if v not in (None, "")})
        defaults = BookingDefaults.from_config({"booking_defaults": merged})

        template = cl.download_booking_template()
        booking = cl.resolve_booking_payload(defaults, card)
        today = date.today()
        booking_id = cl.import_booking_from_xlsx(
            template_bytes=template,
            booking=booking,
            card=card,
            doc_date_serial=excel_serial(today),
            delivery_date_serial=excel_serial(today + timedelta(days=defaults.delivery_days)),
        )
        cl.patch_booking_identity(
            booking_id=booking_id, customer_id=cid, booking=booking, card=card
        )
        return {
            "ok": True,
            "success": True,
            "customer_id": cid,
            "booking_id": booking_id,
            "booking_no": booking.booking_no,
            "mode": mode,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "response_body": {
                "adapter": "mrerp_dms",
                "booking_no": booking.booking_no,
                "booking_id": booking_id,
                "customer_id": cid,
                "mode": mode,
            },
        }

    out = _run_logged_in(endpoint, _do)
    if not out.get("ok"):
        out["success"] = False
        out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out


def _fields_to_idcard(f: Dict[str, Any]) -> Dict[str, Any]:
    name = (f.get("name") or "").strip()
    parts = name.split(" ", 1)
    return {
        "people_id": f.get("people_id"),
        "first_name": parts[0] if parts else "",
        "last_name": parts[1] if len(parts) > 1 else "",
        "birthday_be": f.get("birthday_be"),
        "prefix_id": f.get("prefix_id") or "17",
        "prefix_name": f.get("prefix_name") or "",
        "phone": f.get("phone") or "0800000000",
        "address": {
            "house_no": f.get("house_no"),
            "moo": f.get("moo"),
            "soi": f.get("soi"),
            "road": f.get("road"),
            "province_id": f.get("province_id"),
            "province": f.get("province_name"),
            "district_id": f.get("district_id"),
            "district": f.get("district_name"),
            "subdistrict_id": f.get("subdistrict_id"),
            "subdistrict": f.get("subdistrict_name"),
            "zipcode_id": f.get("zipcode_id"),
            "zipcode": f.get("zipcode"),
        },
    }
