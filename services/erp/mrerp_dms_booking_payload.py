# -*- coding: utf-8 -*-
"""订车载荷解析:主档行 → DMSMasterRef → DMSBookingPayload(纯函数,零 IO)。

为什么单独一层:订车提交前的权威只读复核(readonly_preflight)已经抓过一份完整主档与
选中车型的颜色。载荷解析若还按字段各拉一次 bshsd,就会(1)把「DMS 里明明存在」的车/
店/顾问/颜色在解析层重新判成不存在或已变更 —— 核心契约被绕过;(2)多出六七次远程取数,
销售账号下还多一轮不完整视图。所以取数归调用方(权威只读块),本模块只吃行。

两条路径共用同一份严格判据:
  · DMSClient.resolve_booking_payload —— 按需实时取数(单凭据/兼容路径,建单自检);
  · build_booking_payload —— 吃权威快照(订车提交路径:一次全主档 + 一次选中车颜色)。

pinned id 一旦存在就不许回落首行或钉死标量:主档读不到/已变更时提交旧值,月底对账才会
暴露填错。取数失败(rows None)→ ERR_DMS_MASTER_UNAVAILABLE(可重试);主档真空或找不到
pinned → ERR_DMS_MASTER_UNMATCHED(重试无意义,必须让操作员重新选择)。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional

from services.erp.mrerp_dms_booking_org import BookingOrganization
from services.erp.mrerp_dms_client_base import DMSClientError, to_be_date
from services.erp.mrerp_dms_master_rows import ref_from_row, row_by_id
from services.erp.mrerp_dms_models import (
    BookingDefaults,
    DMSBookingPayload,
    DMSMasterRef,
)


def advisor_ref_strict(
    fetch_rows: Callable[[], Optional[List[list]]], defaults: BookingDefaults
) -> DMSMasterRef:
    """顾问栏(ที่ปรึกษาการขาย)= 销售提成归属,只认调用方钉死的 id,绝不回落名册首行。

    逐问开局已按操作员的 DMS 账号匹配好归属(services/erp/dms_advisor.py),到这里必有
    id;落错人只有月底对账才看得出来,所以宁可当场报错也不猜。

    fetch_rows 是零参取行回调:没有 pin 就不该白拉一次名册(取数归调用方,这里只管判)。
    """
    if not defaults.advisor_id:
        raise DMSClientError("booking advisor not pinned for operator", "ERR_DMS_ADVISOR_REQUIRED")
    rows = fetch_rows()
    row = row_by_id(rows, defaults.advisor_id)
    if row is not None:
        return ref_from_row(row)
    if rows is None:
        raise DMSClientError(
            "DMS advisor master unavailable while validating the selected advisor",
            "ERR_DMS_MASTER_UNAVAILABLE",
        )
    raise DMSClientError(
        f"booking advisor id {defaults.advisor_id!r} not in DMS advisor master",
        "ERR_DMS_ADVISOR_UNMATCHED",
    )


def ref_from_rows(
    elemname: str,
    rows: Optional[List[list]],
    pinned_id: str,
    pinned_code: str = "",
    pinned_name: str = "",
) -> DMSMasterRef:
    """把用户的显式选择解析到一份**已取全**的主档行上(第 2 页的 id 也算数)。

    只用第 1 页会漏掉第 2 页的 pinned id,然后悄悄回落首行 —— 建单就填错车/店。
    """
    if pinned_id:
        if rows is None:
            raise DMSClientError(
                f"DMS master {elemname} unavailable while resolving pinned id {pinned_id!r}",
                "ERR_DMS_MASTER_UNAVAILABLE",
            )
        chosen = row_by_id(rows, pinned_id)
        if chosen is None:
            raise DMSClientError(
                f"pinned id {pinned_id!r} not in DMS master {elemname}",
                "ERR_DMS_MASTER_UNMATCHED",
            )
        return ref_from_row(chosen)
    if rows is None:
        raise DMSClientError(f"DMS master {elemname} unavailable", "ERR_DMS_MASTER_UNAVAILABLE")
    chosen = [
        row
        for row in rows
        if (pinned_code and len(row) > 1 and str(row[1]) == str(pinned_code))
        or (not pinned_code and pinned_name and len(row) > 2 and str(row[2]) == str(pinned_name))
    ]
    if len(chosen) != 1:
        raise DMSClientError(
            f"DMS master {elemname} requires an explicit unambiguous selection",
            "ERR_DMS_MASTER_UNMATCHED",
        )
    return ref_from_row(chosen[0])


def payload_from_refs(
    defaults: BookingDefaults,
    *,
    advisor: DMSMasterRef,
    car: DMSMasterRef,
    paint: DMSMasterRef,
    place: DMSMasterRef,
    term: DMSMasterRef,
    org: BookingOrganization,
    regis: DMSMasterRef,
    today: Optional[date] = None,
) -> DMSBookingPayload:
    """唯一装配点:各主档引用 + 顾问组织 → DMSBookingPayload。

    交车日用端点默认推算基线,逐问值由调用方 dataclasses.replace 覆盖(身份/地址由建单层
    create_booking_via_form 的 card 参数回显,不进载荷)。
    """
    today = today or date.today()
    delivery = today + timedelta(days=defaults.delivery_days)
    return DMSBookingPayload(
        doc_date_be=to_be_date(today),
        delivery_date_be=to_be_date(delivery),
        advisor=advisor,
        car=car,
        paint=paint,
        place_book=place,
        term_sale=term,
        branch=org.branch,
        team=org.team,
        organization_fields=org.form_fields,
        regis_behalf=regis,
    )


def build_booking_payload(
    defaults: BookingDefaults,
    *,
    masters: Dict[str, Any],
    paints: Optional[List[list]],
    org: BookingOrganization,
    today: Optional[date] = None,
) -> DMSBookingPayload:
    """吃**已取得的权威快照**装配载荷:零远程取数(颜色吃选中车型那一份)。

    masters 必须是同一次权威会话抓的全量主档(含 advisors);paints 是选中车型的颜色。
    """
    advisor = advisor_ref_strict(lambda: masters.get("advisors"), defaults)
    car = ref_from_rows("txtcar", masters.get("cars"), defaults.car_id, defaults.car_code, "")
    paint = ref_from_rows("txtcarpaint", paints, defaults.paint_id, defaults.paint_code, "")
    place = ref_from_rows(
        "txtplacebook", masters.get("place_books"), defaults.place_book_id, "", ""
    )
    term = ref_from_rows("txttermsale", masters.get("term_sales"), defaults.term_sale_id, "", "")
    regis = ref_from_rows(
        "txtregisbehalf", masters.get("regis_behalfs"), defaults.regis_behalf_id, "", ""
    )
    return payload_from_refs(
        defaults,
        advisor=advisor,
        car=car,
        paint=paint,
        place=place,
        term=term,
        org=org,
        regis=regis,
        today=today,
    )
