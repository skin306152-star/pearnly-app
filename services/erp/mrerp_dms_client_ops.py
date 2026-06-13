# -*- coding: utf-8 -*-
"""DMS 订车单业务操作(建单/编号/查询/主档解析/客户查找)mixin.

从 mrerp_dms_client.py 抽出 · self.* 经 MRO 解析回 DMSClient。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from services.erp.mrerp_dms_models import (
    BookingDefaults,
    DMSBookingPayload,
    DMSMasterRef,
    ThaiIdCardPayload,
)
from services.erp.mrerp_dms_client_base import DMSClientError, to_be_date

# DMS 订车单(drfcbc)菜单 id/层级 —— autonum 自动编号的键(MR.ERP DMS 标准实例)。
# 走原生表单建单时带上,让 new.php 推进对应 BK 流水计数器。
_DRFCBC_IDMENU = "25"
_DRFCBC_MENULV = "2"

# DMS autonum 计数器是按分店分段的,跟全局唯一约束会失步:它回的「下一个号」
# 可能已被其它分店/历史单占用,提交即 err::"เลขที่ใบจอง" ซ้ำ(单号重复)。
# 撞重复时往后顺号重试,跳过所有已占用号。
_BOOKING_DOCNO_MAX_TRIES = 25


def _is_duplicate_docno_error(body: str) -> bool:
    """DMS 单号重复报错(err::"เลขที่ใบจอง" ซ้ำ)· ซ้ำ=泰语「重复」。"""
    return body.startswith("err::") and "ซ้ำ" in body


def _bump_docno(docno: str) -> str:
    """末尾连续数字段 +1 并保持位宽:BK2606000001 → BK2606000002。无数字尾则补 1。"""
    i = len(docno)
    while i > 0 and docno[i - 1].isdigit():
        i -= 1
    head, tail = docno[:i], docno[i:]
    if not tail:
        return docno + "1"
    return head + str(int(tail) + 1).zfill(len(tail))


class DMSClientOpsMixin:
    def _apply_booking_form_fields(
        self,
        data: Dict[str, str],
        *,
        customer_id: str,
        booking: DMSBookingPayload,
        card: ThaiIdCardPayload,
    ) -> None:
        """填订车单业务字段(顾问/车/颜色/客户/身份/地址…)· 建(new)与改(edit)共用。
        不含 stsel/idsel/txtdocno —— 由调用方按建/改设置。"""
        data.update(
            {
                "usersval": booking.advisor.id,
                "txtusers": booking.advisor.name,
                "txtuserstel": booking.advisor.extra[0] if booking.advisor.extra else ".",
                "placebookval": booking.place_book.id,
                "txtplacebook": booking.place_book.name,
                "cusval": customer_id,
                "txtcus": card.full_name,
                "prefixval": card.prefix_id,
                "txtprefix": card.prefix_name,
                "txtpeopleid": card.people_id,
                "txtbirthday": card.birthday_be,
                "txttel": card.phone,
                "carval": booking.car.id,
                "txtcar": booking.car.code,
                "carbrandval": self._extra(booking.car, 0),
                "txtcarbrand": self._extra(booking.car, 1),
                "typecarval": self._extra(booking.car, 2),
                "txttypecar": self._extra(booking.car, 3),
                "typecardescval": self._extra(booking.car, 4),
                "txttypecardesc": self._extra(booking.car, 5),
                "gradeval": self._extra(booking.car, 6),
                "txtgrade": self._extra(booking.car, 7),
                "cargearval": self._extra(booking.car, 8),
                "txtcargear": self._extra(booking.car, 9),
                "txtmanuyear": self._extra(booking.car, 10),
                "enginepowerval": self._extra(booking.car, 11),
                "txtenginepower": self._extra(booking.car, 12),
                "carpaintval": booking.paint.id,
                "txtcarpaint": booking.paint.code,
                "carpaintname": booking.paint.name,
                "txtprice": self._extra(booking.car, 13),
                "txtcardeliverydate": booking.delivery_date_be,
                "termsaleval": booking.term_sale.id,
                "txttermsale": booking.term_sale.name,
                "branch_bookval": booking.branch.id,
                "txtbranch_book": booking.branch.name,
                "team_bookval": booking.team.id,
                "txtteam_book": booking.team.name,
                "branch_sellval": booking.branch.id,
                "txtbranch_sell": booking.branch.name,
                "team_sellval": booking.team.id,
                "txtteam_sell": booking.team.name,
                "txtearnestmoney": "0.00",
                "regisbehalfval": booking.regis_behalf.id,
                "txtregisbehalf": booking.regis_behalf.name,
                "txtregisname": card.full_name,
            }
        )
        self._apply_address_to_booking_form(data, card.address)

    def create_booking_via_form(
        self, *, customer_id: str, booking: DMSBookingPayload, card: ThaiIdCardPayload
    ) -> tuple:
        """A1:走 DMS 原生订车单表单建单 · DMS autonum 出 BK 号(符合公司规则·零手填)。
        取代 Excel 导入 + patch 两步。返回 (booking_id, booking_no)。

        autonum 计数器与全局唯一约束失步时会回已占用号 → 提交即「单号重复」。
        撞重复就往后顺号重试(_bump_docno),跳过被占用的号。"""
        form_html = self._post_text("drfcbc/form.php", {"status": "n"})
        base = self._parse_form_defaults(form_html)
        base["stsel"] = "n"
        base["idsel"] = ""
        base["idmenu"] = _DRFCBC_IDMENU
        base["menulv"] = _DRFCBC_MENULV
        self._apply_booking_form_fields(base, customer_id=customer_id, booking=booking, card=card)

        docno = self._next_booking_docno(booking.branch.id) or booking.booking_no
        last_body = ""
        for _ in range(_BOOKING_DOCNO_MAX_TRIES):
            data = dict(base)
            data["txtdocno"] = docno
            resp = self.transport.post(self._url("drfcbc/new.php"), data=data, timeout_ms=120000)
            last_body = (resp.text or "").strip()
            if resp.status_code == 200 and not last_body.startswith("err::"):
                booking_id = self.search_booking(docno)
                if not booking_id:
                    raise DMSClientError(
                        "booking create returned ok but search failed", "ERR_DMS_IMPORT"
                    )
                return booking_id, docno
            if resp.status_code == 200 and _is_duplicate_docno_error(last_body):
                docno = _bump_docno(docno)
                continue
            break
        raise DMSClientError(f"booking create failed: {last_body[:300]!r}", "ERR_DMS_IMPORT")

    def _next_booking_docno(self, branch_id: str) -> str:
        """取 DMS 订车单下一个自动编号(BK+期间+流水)。autonum 关/异常 → '' 让调用方兜底。"""
        try:
            cfg = json.loads(
                self._post_text(
                    "component/php/autonum.php",
                    {"menulv": _DRFCBC_MENULV, "idmenu": _DRFCBC_IDMENU},
                )
            )
            if not cfg or cfg[0] is None or str(cfg[1]) != "1":
                return ""
            det = json.loads(
                self._post_text(
                    "component/php/autonumdetail.php",
                    {
                        "idautonum": cfg[0],
                        "prefixautonum": cfg[2],
                        "digitautonum": cfg[3],
                        "idautonumformat": cfg[4],
                        "idbranch": branch_id or "",
                    },
                )
            )
            return str(det[2]) if len(det) > 2 and det[2] else ""
        except Exception:
            return ""

    def fetch_masters(self) -> Dict[str, List[List[Any]]]:
        """Pull the dropdown lists the connect wizard needs. Best-effort:
        a missing/empty list comes back as []."""
        out: Dict[str, List[List[Any]]] = {}
        for key, elem, extra in (
            ("advisors", "txtusers", {}),
            ("cars", "txtcar", {}),
            ("place_books", "txtplacebook", {}),
            ("term_sales", "txttermsale", {}),
            ("branches", "txtbranch_book", {}),
            ("regis_behalfs", "txtregisbehalf", {}),
        ):
            try:
                out[key] = self._bshsd(elem, **extra)
            except Exception:
                out[key] = []
        return out

    def resolve_booking_payload(
        self, defaults: BookingDefaults, card: ThaiIdCardPayload, *, today: Optional[date] = None
    ) -> DMSBookingPayload:
        """Build a DMSBookingPayload from endpoint defaults, resolving any
        master ref the user did not pin from live DMS master data."""
        today = today or date.today()
        delivery = today + timedelta(days=defaults.delivery_days)

        advisor = self._ref_from_default(
            "txtusers", defaults.advisor_id, defaults.advisor_code, defaults.advisor_name
        )
        car = self._ref_from_default("txtcar", defaults.car_id, defaults.car_code, "")
        paint = self._ref_from_default(
            "txtcarpaint", defaults.paint_id, defaults.paint_code, "", idcar=car.id
        )
        place = self._ref_from_default("txtplacebook", defaults.place_book_id, "", "")
        term = self._ref_from_default("txttermsale", defaults.term_sale_id, "", "")
        branch = self._ref_from_default("txtbranch_book", defaults.branch_id, "", "")
        team = self._ref_from_default(
            "txtteam_book", defaults.team_id, "", "", branch_book=branch.id
        )
        regis = self._ref_from_default("txtregisbehalf", defaults.regis_behalf_id, "", "")

        booking_no = f"{defaults.booking_prefix}{card.people_id[-6:]}{today.strftime('%m%d')}"
        return DMSBookingPayload(
            booking_no=booking_no,
            doc_date_be=to_be_date(today),
            delivery_date_be=to_be_date(delivery),
            advisor=advisor,
            car=car,
            paint=paint,
            place_book=place,
            term_sale=term,
            branch=branch,
            team=team,
            regis_behalf=regis,
        )

    def search_customer(self, text: str) -> Optional[str]:
        body = self._post_text(
            "cus/component/showdata.php",
            {
                "sdtamt": "10",
                "sdtpage": "1",
                "sd": text,
                "selcolsort": "1",
                "selcolsorttype": "1",
            },
        )
        return self._first_data_val(body)

    def search_booking(self, booking_no: str) -> Optional[str]:
        body = self._post_text(
            "drfcbc/component/showdata.php",
            {
                "sdtamt": "10",
                "sdtpage": "1",
                "sd": booking_no,
                "ftd": "1",
                "selcolsort": "1",
                "selcolsorttype": "1",
            },
        )
        return self._first_data_val(body)

    def _ref_from_default(
        self, elemname: str, pinned_id: str, pinned_code: str, pinned_name: str, **extra
    ) -> DMSMasterRef:
        """Resolve a master ref: if the user pinned an id, fetch that exact
        row; else take the first available row from live master data."""
        rows = self._bshsd(elemname, **extra)
        chosen = None
        if pinned_id:
            for row in rows:
                if str(row[0]) == str(pinned_id):
                    chosen = row
                    break
        if chosen is None and rows:
            chosen = rows[0]
        if chosen is None:
            # No live rows and no pin — fall back to the pinned scalars so the
            # caller still gets a usable (if unverified) ref.
            return DMSMasterRef(id=pinned_id, code=pinned_code, name=pinned_name)
        return DMSMasterRef(
            id=str(chosen[0]),
            code=str(chosen[1]) if len(chosen) > 1 else str(chosen[0]),
            name=str(chosen[2]) if len(chosen) > 2 else (str(chosen[1]) if len(chosen) > 1 else ""),
            extra=tuple(chosen[3:]),
        )

    def _bshsd(self, elemname: str, **extra) -> List[List[Any]]:
        data = {"bshsdamt": "10", "bshsdcurrpage": "1", "elemname": elemname, "sdt": ""}
        data.update({k: str(v) for k, v in extra.items()})
        text = self._post_text("drfcbc/component/bshsd.php", data)
        try:
            return json.loads(text) if text.strip() else []
        except (ValueError, json.JSONDecodeError):
            return []
