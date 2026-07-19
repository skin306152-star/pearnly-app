# -*- coding: utf-8 -*-
"""DMS 身份证「识别→可编辑面板→确认推送」两步流的服务封装。

dms_routes 的三个新端点调这里:
- recognize_lookup_mrerp_dms:登录一次 → 查 DMS 客户 + 解析 OCR 地址为级联 ids +
  府/县/区/邮编选项 + 称谓 → 一次性喂面板。
- geo_mrerp_dms:面板改地址时的级联代理。优先用缓存 cookie + httpx(只读·快),
  失效再 Playwright 重登录并刷新缓存。
- push_idcard_fields_mrerp_dms:用面板编辑后的字段建/改客户(save_customer)。
  只写客户库(ลูกค้า · cus/new.php·cus/edit.php),不建订车单。

会话 cookie 缓存(进程级·短 TTL):登录成本高,级联只读复用 cookie 避免每次重登录。
写操作(建/改客户)仍走 Playwright(铁律#7);cookie 只用于只读级联。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from services.erp.dms_customer_diff import diff_customer_fields
from services.erp.dms_id_validate import normalize_thai_id
from services.erp.erp_dms_push import (
    _build_mrerp_dms_adapter,
    _dms_friendly,
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
        # 进 erp_push_logs.response_body:光有 error_code 分不清「DMS 拒」还是「复核没查到」
        "response_body": {"raw_error": (raw or "")[:300]},
    }


def _run_logged_in(endpoint: Dict[str, Any], fn):
    """Build adapter → login → fn(client, adapter) → cache cookies. Maps DMS
    errors to friendly dicts. NEVER raises."""
    cfg = endpoint.get("config") or {}
    adapter, build_err = _build_mrerp_dms_adapter(cfg)
    if build_err:
        return _err(build_err["error_code"], build_err["raw"])
    try:
        from services.erp.mrerp_dms_adapter import (
            MrerpDmsAdminAuthError,
            MrerpDmsAuthError,
            MrerpDmsTechnicalError,
        )
        from services.erp.mrerp_dms_client_base import DMSClientError

        try:
            with adapter:
                adapter.login()
                out = fn(adapter._client(), adapter)
                _cookies_put(endpoint, adapter.session_cookies(), adapter.base_url)
                return out
        except MrerpDmsAdminAuthError as e:
            # admin 凭据组登录失败(≠ 用户会话)— 子类必须先于基类捕获。
            return _err("ERR_DMS_ADMIN_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsAuthError as e:
            return _err("ERR_DMS_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsTechnicalError as e:
            return _err("ERR_DMS_TECHNICAL", f"{type(e).__name__}: {e}")
        except DMSClientError as e:
            return _err(e.error_code or "ERR_DMS_TECHNICAL", str(e))
    except Exception as e:
        logger.exception("dms intake op failed")
        return _err("ERR_UNEXPECTED", f"{type(e).__name__}: {e}")


def _score_candidates(
    rows: List[Dict[str, str]], *, people_id: str, name: str
) -> List[Dict[str, Any]]:
    """给相似候选打分(0-100):身份证号完全一致=100;否则姓名相似为主、
    身份证号相似为辅。按分降序。"""
    import difflib

    out: List[Dict[str, Any]] = []
    for r in rows:
        rname = r.get("name", "")
        rpid = r.get("people_id", "")
        name_ratio = difflib.SequenceMatcher(None, name or "", rname).ratio()
        score = name_ratio
        if people_id and rpid:
            if people_id == rpid:
                score = 1.0
            else:
                id_ratio = difflib.SequenceMatcher(None, people_id, rpid).ratio()
                score = max(score, 0.6 * name_ratio + 0.4 * id_ratio)
        out.append({**r, "score": round(score * 100)})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def _incoming_for_diff(name: str, addr, resolved, phone: str = "") -> Dict[str, str]:
    """身份证识别侧的「新值」侧,喂 diff_customer_fields。地址取解析后的 master id
    (与 DMS current_fields 同口径,可比);phone 是操作员手输的(身份证上没有),
    非空才参与 diff——否则改了电话也测不出差异,更新时被静默丢弃;prefix/birthday
    此入口无信息,缺键即不参与 diff。"""
    out = {
        "name": name,
        "house_no": addr.house_no,
        "moo": addr.moo,
        "soi": addr.soi,
        "road": addr.road,
        "province_id": resolved.province_id,
        "district_id": resolved.district_id,
        "subdistrict_id": resolved.subdistrict_id,
        "zipcode_id": resolved.zipcode_id,
    }
    if (phone or "").strip():
        out["phone"] = str(phone).strip()
    return out


def recognize_lookup_mrerp_dms(
    endpoint: Dict[str, Any],
    *,
    people_id: str,
    name: str = "",
    ocr_address: Dict[str, Any],
    phone: str = "",
    fallback_customer_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """OCR 后:查 DMS 客户 + 解析 OCR 地址级联 + 选项 + 称谓 + 相似候选。
    scenario:exact(身份证号命中)/ similar(按姓名找到候选)/ none(都没有)。"""

    def _do(cl, adapter):
        from services.erp.mrerp_dms_models import ThaiAddress

        look = cl.lookup_customer(people_id)
        if not look["found"]:
            # 台账兜底先行:本租户最近推过的同尾号客户,按客户号【直读】核对全证号——
            # 直读不经搜索缓存,权威零等待;「新客隐身期」(2026-07-19 四案实锤:刚建/
            # 刚改的客户对新会话隐身数分钟)案例全在台账里,先直读省下退避重试。
            pid_norm = normalize_thai_id(str(people_id))
            for cid in fallback_customer_ids or []:
                f = cl.read_customer(str(cid))
                if pid_norm and normalize_thai_id(str(f.get("people_id") or "")) == pid_norm:
                    look = {"found": True, "customer_id": str(cid), "fields": f}
                    break
        # 台账也没有才退避重试:只剩「DMS 原生老客户 + 搜索偶发空返」这个窄场景,
        # 真新客户为它多付 ~3s(误标新客的代价更高,保守保留两试)。
        for _ in range(2):
            if look["found"] or not (people_id or "").strip():
                break
            time.sleep(1.5)
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
        if look["found"]:
            scenario = "exact"
            fields = look["fields"]
            field_diffs = diff_customer_fields(
                fields, _incoming_for_diff(name, addr, resolved, phone)
            )
            candidates = [
                {
                    "customer_id": look["customer_id"],
                    "cuscode": fields.get("cuscode", ""),
                    "name": fields.get("name", ""),
                    "people_id": fields.get("people_id", "") or people_id,
                    "score": 100,
                }
            ]
        else:
            field_diffs = []
            rows = cl.search_customers_detailed(name) if (name or "").strip() else []
            candidates = _score_candidates(rows, people_id=people_id, name=name or "")
            scenario = "similar" if candidates else "none"

        return {
            "ok": True,
            "scenario": scenario,
            "match": {
                "found": look["found"],
                "customer_id": look["customer_id"],
                "current_fields": look["fields"],
            },
            "field_diffs": field_diffs,
            "candidates": candidates,
            "geo": geo,
            "prefixes": cl._select_options(form_html, "selprefix"),
        }

    return _run_logged_in(endpoint, _do)


def customer_fields_mrerp_dms(endpoint: Dict[str, Any], *, customer_id: str) -> Dict[str, Any]:
    """载入指定 DMS 客户的全字段(供相似场景选定候选后填充全字段表单)。
    返回 current_fields(含三套地址+下拉选中标签)+ 府选项 + 称谓。"""

    def _do(cl, adapter):
        page = cl._post_text("cus/form.php", {"status": "e", "id": customer_id})
        data = cl._parse_form_defaults(page)
        return {
            "ok": True,
            "customer_id": customer_id,
            "current_fields": cl._extract_customer_fields(data, page),
            "provinces": cl._select_options(page, "selprovinces"),
            "prefixes": cl._select_options(page, "selprefix"),
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
    addresses: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """面板最终字段 → 建/改客户(只写 DMS 客户库 ลูกค้า,不建订车单)。
    mode:create(新建)/ overwrite(覆盖可映射)/ update(只写差异字段)。
    update 与 overwrite 在写库层一致(载现表单 + 空值跳过),差异在前端给的字段集;
    update 只传选了「新值」的字段 → 其余保留 DMS 现值。返回写日志/响应用 dict。"""
    t0 = time.time()
    save_mode = "create" if mode == "create" else "overwrite"

    def _do(cl, adapter):
        cid, converted = cl.save_customer(
            fields=fields, mode=save_mode, customer_id=customer_id, addresses=addresses
        )
        # create 被幂等/撞码转成 overwrite 时如实回 update——回执不谎称「新建」。
        actual = "update" if converted else mode
        return {
            "ok": True,
            "success": True,
            "customer_id": cid,
            "mode": actual,
            "elapsed_ms": int((time.time() - t0) * 1000),
            "response_body": {
                "adapter": "mrerp_dms",
                "customer_id": cid,
                "mode": actual,
            },
        }

    out = _run_logged_in(endpoint, _do)
    if not out.get("ok"):
        out["success"] = False
        out["elapsed_ms"] = int((time.time() - t0) * 1000)
    return out
