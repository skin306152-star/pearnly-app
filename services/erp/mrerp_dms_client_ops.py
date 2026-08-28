# -*- coding: utf-8 -*-
"""DMS 订车单业务操作(建单/编号/查询/主档解析/客户查找)mixin.

从 mrerp_dms_client.py 抽出 · self.* 经 MRO 解析回 DMSClient。
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from services.erp import dms_employees, mrerp_dms_docno
from services.erp.mrerp_dms_models import (
    BookingDefaults,
    DMSBookingPayload,
    DMSMasterRef,
    ThaiIdCardPayload,
)
from services.erp.mrerp_dms_client_base import DMSClientError, to_be_date
from services.erp.mrerp_dms_payments import payment_form_fields

logger = logging.getLogger(__name__)

# DMS 订车单(drfcbc)菜单 id/层级 —— autonum 自动编号的键(MR.ERP DMS 标准实例)。
# 走原生表单建单时带上,让 new.php 推进对应 BK 流水计数器。
_DRFCBC_IDMENU = "25"
_DRFCBC_MENULV = "2"

# DMS autonum 计数器是按分店分段的,跟全局唯一约束会失步:它回的「下一个号」
# 可能已被其它分店/历史单占用,提交即 err::"เลขที่ใบจอง" ซ้ำ(单号重复)。
# 撞重复时往后顺号重试,跳过所有已占用号。
_BOOKING_DOCNO_MAX_TRIES = mrerp_dms_docno.BOOKING_DOCNO_MAX_TRIES

# 顾问名册翻页页大小(真机 probe:服务端尊重 bshsdamt,200 行一页覆盖单店全部销售)。
_ADVISOR_PAGE_SIZE = 200


def _is_duplicate_docno_error(body: str) -> bool:
    """DMS 单号重复报错(err::"เลขที่ใบจอง" ซ้ำ)· ซ้ำ=泰语「重复」。"""
    return mrerp_dms_docno.is_duplicate_docno_error(body)


def _bump_docno(docno: str) -> str:
    """末尾连续数字段 +1 并保持位宽:BK2606000001 → BK2606000002。无数字尾则补 1。"""
    return mrerp_dms_docno.bump_docno(docno)


def row_by_id(rows: Optional[List[list]], rid: str) -> Optional[list]:
    """bshsd 主档行按 id 命中(首列即 id),取首个;没有 → None。"""
    for row in rows or []:
        if row and str(row[0]) == str(rid):
            return row
    return None


def _memo(client: Any) -> Dict[tuple, Any]:
    """会话级取数备忘。client 实例活在一次 DMS 登录会话里(_run_logged_in),期间主档不变;
    惰性挂在实例上,mixin 因此不依赖 DMSClient.__init__。"""
    return client.__dict__.setdefault("_bshsd_memo", {})


def _parse_bshsd_rows(elemname: str, text: str) -> Optional[List[List[Any]]]:
    """bshsd 响应 → 行表。空 body / 合法空数组 → [];非空但不可解析 → None。

    「取数失败」与「名册真的一个人都没有」必须分得开:前者可以降级重试,后者只能诚实报错。
    """
    if not text.strip():
        return []
    try:
        rows = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        rows = None
    if not isinstance(rows, list):
        logger.warning(
            "[dms] bshsd %s: body is not a JSON array; treated as fetch failure", elemname
        )
        return None
    return rows


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
                "txtregisname": booking.regis_name or card.full_name,
            }
        )
        # 有订金渠道时覆盖上面的 0.00 默认与新增渠道字段;空 payments 则保持现状。
        data.update(payment_form_fields(booking.payments))
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

        docno = self._next_booking_docno(booking.branch.id)
        if not docno:
            raise DMSClientError("booking auto number unavailable", "ERR_DMS_IMPORT")
        digits = getattr(self, "_booking_docno_digits", 6)
        docno = mrerp_dms_docno.next_unoccupied_docno(docno, digits, self._post_text)
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
        """取 DMS 订车单下一个自动编号(BK+期间+流水)。autonum 关/异常时返回空。"""
        try:
            cfg = json.loads(
                self._post_text(
                    "component/php/autonum.php",
                    {"menulv": _DRFCBC_MENULV, "idmenu": _DRFCBC_IDMENU},
                )
            )
            if not cfg or cfg[0] is None or str(cfg[1]) != "1":
                return ""
            digits = int(cfg[3])
            if digits <= 0:
                return ""
            self._booking_docno_digits = digits
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

    def attach_booking_files(self, *, booking_id: str, files: list) -> dict:
        """给已存在订车单挂附件 —— 逐文件独立一轮 edit.php POST,失败不中断。

        DMS 上传契约(_dms_probe/fupload_probe/CONTRACT.md):上传 = POST
        drfcbc/edit.php 提交【完整编辑表单】的 FormData,不是独立小接口;只发
        新文件字段会把订车单既有字段冲空。所以先加载编辑表单解析全部现值,再
        逐件追加 fulnew[]/fulnewname[];全部跑完回读校验(HTTP 200 不算数)。

        files 元素:{"display_name", "filename", "content_type", "content"}。
        返回 {"ok", "attached", "failed": [{"display_name", "error"}]}。
        """
        if not files:
            return {"ok": True, "attached": 0, "failed": []}

        # 编辑表单加载参数名以真机抓包为准(probe 用 {status:"e", id:..})。
        form_html = self._post_text("drfcbc/form.php", {"status": "e", "id": str(booking_id)})
        base = self._parse_form_defaults(form_html)
        if base.get("stsel") != "e" or base.get("idsel") != str(booking_id):
            raise DMSClientError(
                f"booking attach form mismatch: stsel={base.get('stsel')!r} "
                f"idsel={base.get('idsel')!r} vs booking_id={booking_id!r}",
                "ERR_DMS_IMPORT",
            )
        docno_before = base.get("txtdocno")

        attached = 0
        failed: List[Dict[str, str]] = []
        uploaded: List[str] = []  # POST 判绿的件,留待回读校验
        for item in files:
            display = str(item.get("display_name") or "")[:150]
            data = dict(base)
            data["fulnewname[]"] = display
            resp = self.transport.post(
                self._url("drfcbc/edit.php"),
                data=data,
                files={"fulnew[]": (item["filename"], item["content"], item["content_type"])},
                timeout_ms=120000,
            )
            body = (resp.text or "").strip()
            if resp.status_code == 200 and not body.startswith("err::"):
                uploaded.append(display)
            else:
                failed.append(
                    {
                        "display_name": display,
                        "error": f"edit.php http={resp.status_code} {body[:200]}",
                    }
                )

        # 回读校验:HTTP 200 不算数,附件必须真渲染在表单上且没冲坏单据。
        if uploaded:
            verify = self._parse_form_defaults(
                self._post_text("drfcbc/form.php", {"status": "e", "id": str(booking_id)})
            )
            current_names = {v for k, v in verify.items() if k.startswith("fulcurrname")}
            docno_ok = verify.get("txtdocno") == docno_before
            for display in uploaded:
                if not docno_ok:
                    failed.append({"display_name": display, "error": "readback docno changed"})
                elif display not in current_names:
                    failed.append(
                        {"display_name": display, "error": "readback missing display name"}
                    )
                else:
                    attached += 1

        return {"ok": not failed, "attached": attached, "failed": failed}

    def fetch_masters(self) -> Dict[str, List[List[Any]]]:
        """Pull the dropdown lists the connect wizard needs. Best-effort:
        a missing/unreadable list comes back as []. 普通主档与顾问名册一样翻页取全 ——
        只取第一页会让第 2 页起的选项在 LINE 逐问里静默消失。"""
        out: Dict[str, List[List[Any]]] = {}
        for key, elem in (
            ("cars", "txtcar"),
            ("place_books", "txtplacebook"),
            ("term_sales", "txttermsale"),
            ("branches", "txtbranch_book"),
            ("regis_behalfs", "txtregisbehalf"),
        ):
            try:
                out[key] = self._bshsd_all(elem) or []
            except Exception:
                out[key] = []
        try:
            # 顾问名册单独翻页取全:操作员账号按 code 列匹配,被分页截断就永远匹配不上。
            out["advisors"] = self._advisor_rows() or []
        except Exception:
            out["advisors"] = []
        try:
            out["prefixes"] = self.list_prefixes() or []
        except Exception:
            out["prefixes"] = []
        # 员工表带登录名,是顾问归属的精确层(顾问下拉的 code 列只是员工编号)。
        # 销售账号未必有员工页权限 → 取不到就落 [],调用方回落启发式匹配。
        out["employees"] = dms_employees.fetch_employees(self) or []
        return out

    def resolve_booking_payload(
        self, defaults: BookingDefaults, card: ThaiIdCardPayload, *, today: Optional[date] = None
    ) -> DMSBookingPayload:
        """Build a DMSBookingPayload from endpoint defaults, resolving any
        master ref the user did not pin from live DMS master data."""
        today = today or date.today()
        delivery = today + timedelta(days=defaults.delivery_days)

        advisor = self._advisor_ref_strict(defaults)
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

        return DMSBookingPayload(
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

    def _advisor_rows(self) -> Optional[List[List[Any]]]:
        """顾问名册(翻页取全)· 建单严格解析与 fetch_masters 共用同一次取数。"""
        return self._bshsd_all("txtusers", page_size=_ADVISOR_PAGE_SIZE)

    def _advisor_ref_strict(self, defaults: BookingDefaults) -> DMSMasterRef:
        """顾问栏(ที่ปรึกษาการขาย)= 销售提成归属,只认调用方钉死的 id,绝不回落名册首行。

        逐问开局已按操作员的 DMS 账号匹配好归属(services/erp/dms_advisor.py),到这里必有
        id;落错人只有月底对账才看得出来,所以宁可当场报错也不猜。
        """
        if not defaults.advisor_id:
            raise DMSClientError(
                "booking advisor not pinned for operator", "ERR_DMS_ADVISOR_REQUIRED"
            )
        rows = self._advisor_rows()
        row = row_by_id(rows, defaults.advisor_id)
        if row is not None:
            return self._ref_from_row(row)
        if rows is None and defaults.advisor_name:
            # 名册取数失败(接口抖 / 200 里塞了不可解析的 body):有名字才敢放行,按钉死标量
            # 提交,DMS 侧仍按 id 认人。名册真空(rows == [])不走这条 —— 那种单 DMS 必拒,
            # 降级只会把「建不了单」拖到更晚才暴露。
            return DMSMasterRef(
                id=defaults.advisor_id, code=defaults.advisor_code, name=defaults.advisor_name
            )
        raise DMSClientError(
            f"booking advisor id {defaults.advisor_id!r} not in DMS advisor master",
            "ERR_DMS_ADVISOR_UNMATCHED",
        )

    def _ref_from_default(
        self, elemname: str, pinned_id: str, pinned_code: str, pinned_name: str, **extra
    ) -> DMSMasterRef:
        """Resolve a master ref: if the user pinned an id, fetch that exact
        row from the full (paged) live master; else take the first available row.

        只在第 1 页里找 pinned id,id 在第 2 页会被误判成「不存在」然后悄悄回落首行,
        建单就填错车/店。故最终解析与 fetch_masters 一样走 _bshsd_all 全量翻页。

        pinned id 一旦存在就不许回落首行或钉死标量:主档读不到/已变更时提交旧值,
        月底对账才会暴露填错。取数失败(rows None)→ ERR_DMS_MASTER_UNAVAILABLE
        (可重试);主档真空或找不到 pinned → ERR_DMS_MASTER_UNMATCHED(重试无意义,
        必须让操作员重新选择)。
        """
        rows = self._bshsd_all(elemname, **extra)
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
            return self._ref_from_row(chosen)
        chosen = rows[0] if rows else None
        if chosen is None:
            # No live rows and no pin — fall back to the pinned scalars so the
            # caller still gets a usable (if unverified) ref.
            return DMSMasterRef(id=pinned_id, code=pinned_code, name=pinned_name)
        return self._ref_from_row(chosen)

    @staticmethod
    def _ref_from_row(row: list) -> DMSMasterRef:
        """bshsd 行 [id, code, name, ...] → DMSMasterRef(尾列进 extra 供表单原样回显)。"""
        return DMSMasterRef(
            id=str(row[0]),
            code=str(row[1]) if len(row) > 1 else str(row[0]),
            name=str(row[2]) if len(row) > 2 else (str(row[1]) if len(row) > 1 else ""),
            extra=tuple(row[3:]),
        )

    def _bshsd(self, elemname: str, **extra) -> Optional[List[List[Any]]]:
        """DMS 主档单页取数(取数失败 → None,见 _parse_bshsd_rows)。

        同一会话内同参只打一次:一次建单要解六七个主档、还会在成功后就地刷缓存,
        而主档在这一次登录期间不会变。失败不进备忘,允许下次重试。
        """
        key = (elemname, tuple(sorted(extra.items())))
        memo = _memo(self)
        if key not in memo:
            data = {"bshsdamt": "10", "bshsdcurrpage": "1", "elemname": elemname, "sdt": ""}
            data.update({k: str(v) for k, v in extra.items()})
            rows = _parse_bshsd_rows(elemname, self._post_text("drfcbc/component/bshsd.php", data))
            if rows is None:
                return None
            memo[key] = rows
        return memo[key]

    def _bshsd_all(
        self, elemname: str, *, page_size: int = 200, max_pages: int = 20, **extra
    ) -> Optional[List[List[Any]]]:
        """翻页拉全某主档:不满一页即最后一页。任一页取数失败 → 整体 None。

        半份名册比取不到更危险 ——「这个人不在名册」的判断会变成瞎话。撞 max_pages 说明
        主档比预期大一个量级,截断必须点名留痕(静默截断 = 又一个分页黑洞)。
        """
        key = (elemname, tuple(sorted(extra.items())), "all")
        memo = _memo(self)
        if key in memo:
            return memo[key]
        rows: List[List[Any]] = []
        for page in range(1, max_pages + 1):
            got = self._bshsd(elemname, bshsdamt=page_size, bshsdcurrpage=page, **extra)
            if got is None:
                return None
            rows.extend(got)
            if len(got) < page_size:
                break
        else:
            logger.warning(
                "[dms] master %s truncated at %d pages / %d rows", elemname, max_pages, len(rows)
            )
        memo[key] = rows
        return rows
