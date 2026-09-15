# -*- coding: utf-8 -*-
"""DMS 身份证「识别→可编辑面板→确认推送」两步流的服务封装。

dms_routes 的三个新端点调这里:
- recognize_lookup_mrerp_dms:登录一次 → 查 DMS 客户 + 解析 OCR 地址为级联 ids +
  府/县/区/邮编选项 + 称谓 → 一次性喂面板。
- geo_mrerp_dms:面板改地址时的级联代理。直接走 _run_logged_in 的真实 Playwright
  会话——adapter 退出时会显式访问 logout 页注销浏览器会话,复用它的 cookie 只会拿到
  已注销会话(HTTP 200 空壳正文或静默空级联),故不复用。
- push_idcard_fields_mrerp_dms:用面板编辑后的字段建/改客户(save_customer)。
  只写客户库(ลูกค้า · cus/new.php·cus/edit.php),不建订车单。

读级联与写操作统一走 Playwright 登录会话(_run_logged_in),会话随 adapter 上下文退出
注销,不落 cookie 缓存(铁律#7)。
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


def _err(code: str, raw: str = "") -> Dict[str, Any]:
    return {
        "ok": False,
        "error_code": code,
        "error_friendly": _dms_friendly(code),
        "raw_error": (raw or "")[:300],
        # 进 erp_push_logs.response_body:光有 error_code 分不清「DMS 拒」还是「复核没查到」
        "response_body": {"raw_error": (raw or "")[:300]},
    }


def _run_logged_in(endpoint: Dict[str, Any], fn, *, authoritative_read: bool = False):
    """Build adapter → login → fn(client, adapter). Maps DMS errors to friendly
    dicts. NEVER raises. 会话随 adapter 退出即注销,不缓存 cookie 复用。

    authoritative_read=True:整块 DMS 读取借管理员会话(配了独立管理员凭据组时),
    销售的挑选/匹配因此看到的是权威映射而不是自己的不完整视图。整块只解析一次管理员
    transport;未配管理员照样走销售;配了但管理员登录失败 → ERR_DMS_ADMIN_AUTH 明确
    失败关闭,不静默降级。写操作(upload/提交)不走这个入口。"""
    from services.line_dms.binding_guard import BindingChanged, require_current

    require_current()
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
                try:
                    adapter.login()
                except (MrerpDmsAuthError, MrerpDmsTechnicalError) as e:
                    if getattr(adapter, "concurrent_login_detected", False):
                        return _err(
                            "ERR_DMS_CONCURRENT_LOGIN",
                            getattr(adapter, "last_dialog", ""),
                        )
                    raise
                try:
                    require_current()
                    client = adapter._client()
                    if authoritative_read:
                        from services.erp.dms_admin_read import authoritative_read_session

                        with authoritative_read_session(client):
                            out = fn(client, adapter)
                    else:
                        out = fn(client, adapter)
                except DMSClientError as e:
                    if getattr(adapter, "concurrent_login_detected", False) and not getattr(
                        e, "response_body", {}
                    ).get("submitted"):
                        return _err(
                            "ERR_DMS_CONCURRENT_LOGIN",
                            getattr(adapter, "last_dialog", ""),
                        )
                    raise
                if getattr(adapter, "concurrent_login_detected", False) and not (
                    isinstance(out, dict) and out.get("booking_id")
                ):
                    return _err(
                        "ERR_DMS_CONCURRENT_LOGIN",
                        getattr(adapter, "last_dialog", ""),
                    )
                return out
        except MrerpDmsAdminAuthError as e:
            # admin 凭据组登录失败(≠ 用户会话)— 子类必须先于基类捕获。
            return _err("ERR_DMS_ADMIN_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsAuthError as e:
            return _err("ERR_DMS_AUTH", f"{type(e).__name__}: {e}")
        except MrerpDmsTechnicalError as e:
            return _err("ERR_DMS_TECHNICAL", f"{type(e).__name__}: {e}")
        except DMSClientError as e:
            result = _err(e.error_code or "ERR_DMS_TECHNICAL", str(e))
            evidence = getattr(e, "response_body", None)
            if isinstance(evidence, dict):
                result["response_body"].update(evidence)
            if getattr(e, "booking_no", None):
                result["booking_no"] = e.booking_no
            return result
    except BindingChanged:
        raise
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
    scenario:exact(身份证号命中)/ similar(按姓名找到候选)/ none(都没有)。

    客户匹配必须用权威视图:销售账号看不到的客户在销售搜索里就是「不存在」,会被误判成
    新客户。整块读取借管理员会话一次(未配管理员则照旧用销售)。"""

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
        prefixes = cl.list_prefixes()
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
            "prefixes": prefixes,
        }

    return _run_logged_in(endpoint, _do, authoritative_read=True)


def customer_fields_mrerp_dms(endpoint: Dict[str, Any], *, customer_id: str) -> Dict[str, Any]:
    """载入指定 DMS 客户的全字段(供相似场景选定候选后填充全字段表单)。
    返回 current_fields(含三套地址+下拉选中标签)+ 府选项 + 称谓。

    按客户号直读属于权威读:销售账号读不到时不能把「读不到」当成「这个客户没有资料」。"""

    def _do(cl, adapter):
        page = cl._post_text("cus/form.php", {"status": "e", "id": customer_id})
        data = cl._parse_form_defaults(page)
        return {
            "ok": True,
            "customer_id": customer_id,
            "current_fields": cl._extract_customer_fields(data, page),
            "provinces": cl._select_options(page, "selprovinces"),
            "prefixes": cl.list_prefixes(),
        }

    return _run_logged_in(endpoint, _do, authoritative_read=True)


def geo_mrerp_dms(endpoint: Dict[str, Any], *, level: str, parent_id: str = "") -> Dict[str, Any]:
    """地址级联选项。直接走 _run_logged_in 的真实 Playwright 会话(不复用已注销 cookie)。

    级联是建档表单的选项来源,同样按权威视图读;面板改地址时不额外多登一次 ——
    管理员 transport 由适配器复用,未配管理员即销售会话。"""

    def _do(cl, adapter):
        return {"ok": True, "options": cl.list_geo(level, parent_id)}

    return _run_logged_in(endpoint, _do, authoritative_read=True)


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
    update 与 overwrite 在写库层一致(载现表单 + 键存在即写),差异在前端给的字段集;
    update 只传选了「新值」的字段 → 其余保留 DMS 现值(传空串=显式清空)。返回写日志/响应用 dict。"""
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
