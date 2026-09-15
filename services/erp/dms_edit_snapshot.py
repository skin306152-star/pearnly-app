# -*- coding: utf-8 -*-
"""订车编辑器(load / save / paints)的**一份请求级权威快照** —— 一次登录取齐。

生产实测(2026-09-13):编辑页 load 一个请求分别独立登录 DMS 两次(全量主档一次、选中车型
颜色又一次),save 三次(主档 + 颜色 + 客户四级地址标签),editor GET 6–10 秒、POST save
9.8 秒 —— 每次登录都是完整的 Playwright 会话 + 管理员只读闸。这里把「一个请求真正要读的
权威数据」收进**同一次** `_run_logged_in(authoritative_read=True)` 会话:

  · 主档 + 银行类目录(同一次 fetch_masters / fetch_payment_bank_masters);
  · 本次请求指定的车型颜色(load 是 qa 已选车型,save 是提交上来的车型);
  · 客户四级地址标签(save 才有:provinces → districts → subdistricts → zipcodes)。

契约:
  · 只在**当前请求/当前订车会话**内复用 —— 不读 12h 缓存、不把上次请求的结论当这次的事实;
    调用方每个请求都要重新取一份。
  · 只读:走 _run_logged_in 的管理员只读闸,写路径一律不经过本模块。
  · 失败(登录/抓取/半份主档)fail closed:回 None,调用方必须如实报错,不许拿旧缓存或
    销售裁剪视图顶上;某车型颜色这次没读到 → 该车型在 paints 里落 None(读失败 ≠ 没颜色),
    由调用方按 fail closed 处理该车型,而不把整次请求判成主档不可用。
  · 成功后把这份**本次权威快照**落 dms_masters_cache(与旧 force_refresh 同效:主档按 DMS
    现状,本次读到的车型颜色进 paints_by_car)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


def geo_levels(customer: Optional[Dict[str, Any]]) -> Tuple[Tuple[str, str], ...]:
    """客户四级地址标签要读的级联层级(缺上一级 id 的层级不读:读了也是空表)。"""
    if not customer:
        return ()
    province = str(customer.get("province_id") or "")
    district = str(customer.get("district_id") or "")
    subdistrict = str(customer.get("subdistrict_id") or "")
    levels: List[Tuple[str, str]] = [("provinces", "")]
    if province:
        levels.append(("districts", province))
    if district:
        levels.append(("subdistricts", district))
    if subdistrict:
        levels.append(("zipcodes", subdistrict))
    return tuple(levels)


def _plain_car_ids(car_ids: Iterable[Any]) -> Tuple[str, ...]:
    """车型 id 归一成字符串、去空值去重(同一个车型在一次请求里只读一次颜色)。"""
    out: List[str] = []
    for car in car_ids or ():
        value = str(car or "")
        if value and value not in out:
            out.append(value)
    return tuple(out)


def _merge_customer_defaults(
    draft: Optional[Dict[str, Any]], live: Optional[Dict[str, Any]]
) -> Dict[str, str]:
    """只用 DMS 当前客户资料补草稿空值；用户已有值永远优先。"""
    out = {str(key): str(value or "") for key, value in (draft or {}).items()}
    for key, value in (live or {}).items():
        target = "zipcode" if key == "zipcode_name" else str(key)
        if not str(out.get(target) or "").strip():
            out[target] = str(value or "")
    return out


def _read(
    endpoint: Dict[str, Any],
    cars: Tuple[str, ...],
    customer: Optional[Dict[str, Any]],
    customer_id: str,
):
    """一次登录读主档、客户现值、颜色和地址级联；任何权威读取失败都 fail closed。"""

    def _fetch(client, adapter):
        from services.erp.mrerp_dms_company_banks import fetch_payment_bank_masters

        masters = {
            **client.fetch_masters(strict=True),
            **fetch_payment_bank_masters(adapter, client=client),
        }
        paints: Dict[str, Optional[List[list]]] = {}
        for car_id in cars:
            rows = client._bshsd_all("txtcarpaint", idcar=car_id)
            # None = 这一车型的颜色这次没读到(读失败 ≠ 空表)。留 None 交给调用方 fail
            # closed:别因为一个不该出现的车型 id 把整次请求判成主档不可用,也别把
            # 「没读到」当成「这车没颜色」。
            paints[car_id] = list(rows) if rows is not None else None
        live_customer: Dict[str, Any] = {}
        if customer_id:
            live_customer = dict(client.read_customer(customer_id) or {})
            from services.erp.dms_id_validate import normalize_thai_id
            from services.erp.mrerp_dms_client_base import DMSClientError

            expected = normalize_thai_id(str((customer or {}).get("people_id") or ""))
            actual = normalize_thai_id(str(live_customer.get("people_id") or ""))
            if expected and actual != expected:
                raise DMSClientError(
                    "booking editor customer identity mismatch", "ERR_DMS_CUSTOMER_LOOKUP"
                )
        resolved_customer = _merge_customer_defaults(customer, live_customer)
        geo = {
            level: list(client.list_geo(level, parent) or [])
            for level, parent in geo_levels(resolved_customer)
        }
        return {
            "masters": masters,
            "paints": paints,
            "geo": geo,
            "customer": live_customer,
            "resolved_customer": resolved_customer,
        }

    from services.erp.erp_dms_intake import _run_logged_in

    return _run_logged_in(endpoint, _fetch, authoritative_read=True)


def _store(endpoint: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
    """本次权威快照落主档缓存(写库失败只在缓存层记账,不推翻已取得的快照)。"""
    from services.erp.dms_masters_cache import write_authoritative_snapshot

    paints = snapshot["paints"]
    car_id = next(iter(paints), "")
    try:
        write_authoritative_snapshot(
            endpoint,
            snapshot["masters"],
            car_id=car_id,
            paints=paints.get(car_id) if car_id else None,
        )
    except Exception:
        logger.warning("[dms edit snapshot] master cache write failed", exc_info=True)


def read_edit_snapshot(
    endpoint: Dict[str, Any],
    *,
    car_ids: Iterable[Any] = (),
    customer: Optional[Dict[str, Any]] = None,
    customer_id: Any = "",
) -> Optional[Dict[str, Any]]:
    """一次权威登录取齐编辑器要用的主档/银行/颜色/地址级联;失败回 None(fail closed)。

    返回 {"masters", "paints": {car_id: rows}, "prefixes", "geo": {level: rows}}。
    """
    cars = _plain_car_ids(car_ids)
    result = _read(endpoint, cars, customer, str(customer_id or ""))
    if not isinstance(result, dict) or result.get("ok") is False:
        # _run_logged_in 的 _err dict(dict 但 ok=False)与异常回退路径都算失败。
        return None
    snapshot = {
        "masters": result["masters"],
        "paints": result["paints"],
        "prefixes": list((result["masters"] or {}).get("prefixes") or []),
        "geo": result["geo"],
        "customer": result.get("customer") or {},
        "resolved_customer": result.get("resolved_customer") or {},
    }
    _store(endpoint, snapshot)
    return snapshot


__all__ = ["geo_levels", "read_edit_snapshot"]
