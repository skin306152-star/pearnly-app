# -*- coding: utf-8 -*-
"""ภ.ง.ด.3/53 RD Prep 交付物装配(D1-3 · 税表D1-ภงด3-53-方案.md §5.3)。

package 步的附加交付物:把当期(posted)采购 WHT 行按收款人聚合,走
services/tax/rdprep.py(纯格式装配,零 I/O)拼成官方 RD Prep .txt。钱只从
services/tax/aggregate.pnd() 取(与主产品同一函数同一口径),本模块不重算——
只多查一次 doc_date(aggregate.pnd 的返回行没带,且不得改 services/tax/ 补它)。

生成条件(方案 §5.3):当期有对应 payee 类型 WHT 行才出该 kind。ภ.ง.ด.53(法人)
只要 payee 税号是合法 13 位就出;ภ.ง.ด.3(个人)官方 RD Prep txt 要求 AMPHUR/PROVINCE/
POSTAL 必填(§1.5 field 36-38),但 suppliers 表只有一个自由文本 address 列、无结构化
地址字段(schema 现状,方案 G5/U7)——本 M1 无法可靠拆分,故官方件恒不出、在备忘录点名
家数,不臆造拆地址。两 kind 都无数据 → 不出,备忘录记「本期无 WHT」。

键入底稿(D1-6,services/tax/pnd_keying_sheet.py):事务所真实工作流是在 RD e-Filing
网页逐条键入、从不用 RD Prep 程序,故另出一份会计照抄用的 xlsx——它是辅助件非官方申报
文件,不受地址必填约束,PND3 个人 payee 照样出、地址栏诚实留空标注,不因缺地址剔除。
"""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional

from services.sales.wht import WHT_PRESETS
from services.tax import pnd_keying_sheet, rdprep
from services.tax.aggregate import PND3 as _TABLE_PND3
from services.tax.aggregate import PND53 as _TABLE_PND53
from services.tax.aggregate import pnd as aggregate_pnd
from services.workorder import obligation_engine

logger = logging.getLogger(__name__)

KIND_PND3 = "pnd3_prep_txt"
KIND_PND53 = "pnd53_prep_txt"
KIND_PND3_KEYING = "pnd3_keying_xlsx"
KIND_PND53_KEYING = "pnd53_keying_xlsx"

# G1:WHT 档率 → 泰文收入类型文字,复用 sales/wht.py 的档位表(单一事实源,不另起一份)。
# 档率不落在预设表(自定义档)时兜底成 3% 服务档文案——官方 PDF 未给收入类型编码表
# (方案 U3),自由文字满足格式契约即可。
_INCOME_TYPE_BY_RATE = {rate: label.split(" / ")[0] for rate, label in WHT_PRESETS if rate != "0"}
_DEFAULT_INCOME_TYPE = _INCOME_TYPE_BY_RATE["3"]

_HEADQUARTERS_BRANCH_TEXT = "สำนักงานใหญ่"
_HEADQUARTERS_BRANCH_CODE = "000000"
_MAX_INCOME_GROUPS = 3  # 官方 §16:一 SEQ_NO 下最多 3 组收入类型,超出另起 SEQ_NO
_THAI_TAX_ID_LEN = 13
_USER_ID_PLACEHOLDER = "PLACEHOLDER"  # G7:RD e-filing 登记参考号,M1 无落点,诚实占位
_CONDITION_LABEL = {"1": "หัก ณ ที่จ่าย (代扣)"}  # 键入底稿เงื่อนไข列文案,与 PAY_CON="1" 同义


def _valid_tax_id(raw) -> bool:
    tid = (raw or "").strip()
    return len(tid) == _THAI_TAX_ID_LEN and tid.isdigit()


def _rate_key(rate: Optional[Decimal]) -> str:
    d = rate if isinstance(rate, Decimal) else Decimal(str(rate or 0))
    return format(d.normalize(), "f")


def _income_type_text(rate: Optional[Decimal]) -> str:
    return _INCOME_TYPE_BY_RATE.get(_rate_key(rate), _DEFAULT_INCOME_TYPE)


def _title_name(form: str, payee_name: Optional[str]) -> str:
    """G3:法人抬头,含「หจก./ห้างหุ้นส่วน」字样归合伙,否则默认公司;个人官方要求无填 "-"。"""
    if form == rdprep.PND3:
        return "-"
    name = payee_name or ""
    if "หจก" in name or "ห้างหุ้นส่วน" in name:
        return "ห้างหุ้นส่วน"
    return "บริษัท"


def _derive_branch_code(branch: Optional[str]) -> str:
    """workspace_clients.branch 是自由文本(方案 U5 结论,默认 'สำนักงานใหญ่'),非结构化
    6 位码。总公司/空 → '000000';文本含数字 → 取数字左零填 6 位;其余无法可靠派生
    → 保守落 '000000'(不臆造分支号)。"""
    text = (branch or "").strip()
    if not text or text == _HEADQUARTERS_BRANCH_TEXT:
        return _HEADQUARTERS_BRANCH_CODE
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.zfill(6)[-6:] if digits else _HEADQUARTERS_BRANCH_CODE


def _filter_valid_lines(lines: list[dict]) -> list[dict]:
    return [ln for ln in lines if _valid_tax_id(ln.get("payee_tax_id"))]


def _fetch_doc_dates(cur, *, tenant_id: str, doc_ids: list[str]) -> dict[str, object]:
    """批量补 doc_date(aggregate.pnd 的行没带这列)。一次 IN 查询,不逐票查(防 N+1)。"""
    if not doc_ids:
        return {}
    cur.execute(
        "SELECT id, doc_date FROM purchase_docs WHERE tenant_id = %s AND id = ANY(%s::uuid[])",
        (tenant_id, doc_ids),
    )
    return {str(r["id"]): r["doc_date"] for r in cur.fetchall()}


def _group_by_payee(lines: list[dict], doc_dates: dict) -> dict[str, dict]:
    """payee_tax_id → {"name", "groups": {rate_key: {rate, base, wht, first_date}}}。
    同 payee 同税率的多张单合一组(base/wht 相加,PAID_DATE 取最早一笔·官方"首笔支付日")。"""
    payees: dict[str, dict] = {}
    for ln in lines:
        tax_id = ln["payee_tax_id"].strip()
        payee = payees.setdefault(tax_id, {"name": ln.get("payee_name"), "groups": {}})
        rate = ln.get("wht_rate") or Decimal("0")
        key = _rate_key(rate)
        group = payee["groups"].setdefault(
            key, {"rate": rate, "base": Decimal("0"), "wht": Decimal("0"), "first_date": None}
        )
        group["base"] += ln["base_amount"]
        group["wht"] += ln["wht_amount"]
        doc_date = doc_dates.get(ln["source_purchase_id"])
        if doc_date and (group["first_date"] is None or doc_date < group["first_date"]):
            group["first_date"] = doc_date
    return payees


def _detail_rows_for_payee(form: str, tax_id: str, payee: dict, branch_no: str) -> list[dict]:
    """一 payee 的税率组 → ≤3 组一行、超出另起行(官方 §16),行内字段序占位交给 rdprep。"""
    keys = sorted(payee["groups"], key=lambda k: payee["groups"][k]["rate"])
    id_field = "NID" if form == rdprep.PND53 else "PIN"
    rows = []
    for start in range(0, len(keys), _MAX_INCOME_GROUPS):
        chunk = keys[start : start + _MAX_INCOME_GROUPS]
        values = {
            "BRANCH_NO": branch_no,
            id_field: tax_id,
            "TIN": "0000000000",
            "TITLE_NAME": _title_name(form, payee["name"]),
            "FNAME": payee["name"],
            "SNAME": "",
        }
        for slot, key in enumerate(chunk, start=1):
            g = payee["groups"][key]
            values[f"PAID_DATE{slot}"] = (
                rdprep.to_buddhist_paid_date(g["first_date"]) if g["first_date"] else None
            )
            values[f"TAX_RATE{slot}"] = g["rate"]
            values[f"PAID_AMT{slot}"] = g["base"]
            values[f"TAX_AMT{slot}"] = g["wht"]
            values[f"INC_TYPE_PND{slot}"] = _income_type_text(g["rate"])
            values[f"PAY_CON{slot}"] = "1"  # G2:绝大多数=หัก ณ ที่จ่าย,M1 无逐行覆盖列,默认
        rows.append(values)
    return rows


def _assemble_form(
    form: str,
    payees: dict[str, dict],
    *,
    sender_nid: str,
    branch_no: str,
    tax_month: str,
    tax_year: str,
    branch_type: str,
) -> tuple[str, Decimal]:
    detail_rows = []
    for tax_id, payee in payees.items():
        detail_rows.extend(_detail_rows_for_payee(form, tax_id, payee, branch_no))

    tot_amt = Decimal("0")
    tot_tax = Decimal("0")
    detail_records = []
    for seq, values in enumerate(detail_rows, start=1):
        for slot in (1, 2, 3):
            tot_amt += values.get(f"PAID_AMT{slot}") or Decimal("0")
            tot_tax += values.get(f"TAX_AMT{slot}") or Decimal("0")
        detail_records.append(rdprep.build_detail(form, {**values, "SEQ_NO": seq}))

    header_values = {
        "SENDER_ID": "0000",
        "SENDER_NID": sender_nid,
        "SENDER_BRANCH": branch_no,
        "SENDER_ROLE": "1",
        "NID": sender_nid,
        "BRANCH_NO": branch_no,
        "DEPT_NAME": _HEADQUARTERS_BRANCH_TEXT,
        "SECTION3": "1",  # U4:Pearnly 常规商业 WHT 恒按 ม.3 เตรส 报
        "SECTION_B": "0",
        "SECTION_C": "0",
        "LTO": "0",
        "TAX_MONTH": tax_month,
        "TAX_YEAR": tax_year,
        "BRANCH_TYPE": branch_type,
        "FORM_TYPE": "00",
        "TOT_NUM": len(detail_records),
        "TOT_AMT": tot_amt,
        "TOT_TAX": tot_tax,
        "SUR_AMT": Decimal("0"),
        "GTOT_TAX": tot_tax,  # SUR_AMT 恒 0.00(逾期算法归 G3 未来项),GTOT=TOT_TAX
        "TRANS_AMT": Decimal("0"),
        "USER_ID": _USER_ID_PLACEHOLDER,
        "FORM_FLAG": "1",
    }
    header = rdprep.build_header(form, header_values)
    text = rdprep.assemble(header, detail_records)
    return text, tot_tax


def _client_row(ctx, client_id) -> Optional[dict]:
    ctx.cur.execute(
        "SELECT tax_id, name, address, branch, vat_registered FROM workspace_clients "
        "WHERE id = %s AND tenant_id = %s",
        (client_id, ctx.tenant_id),
    )
    row = ctx.cur.fetchone()
    return dict(row) if row else None


def build(ctx, out_dir: Path, period_be: Optional[str]) -> tuple[dict, list[str]]:
    """当期 WHT → {kind: (path, numbers)} + 备忘录附加行。取不到前置数据一律静默跳过
    (工单未绑客户等边界),读不出合法 WHT 数据则如实点名——不出交付物不等于崩流程。

    RD Prep 是整批出包里的附加交付物,不是主线(pp30/ledger/bank/memo/evidence 才是)——
    真查库这段失败(连接抖动等)只应折损这两个 kind,绝不能拖垮整个 package 步。与
    wht_signals.scan_period_wht_signals 同一诚实边界:只兜 DB 访问失败,不吞纯 Python
    分组/装配逻辑的 bug(那些错该在单测里现形,见 test_workorder_pnd_prep.py)。"""
    if not period_be:
        return {}, []

    wo = ctx.store.get_work_order(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    client_id = (wo or {}).get("workspace_client_id")
    if not client_id:
        return {}, []

    try:
        return _build_for_client(ctx, out_dir, period_be, client_id)
    except Exception:
        logger.exception(
            "pnd_prep failed (tenant=%s, work_order=%s, period=%s)",
            ctx.tenant_id,
            ctx.work_order_id,
            period_be,
        )
        return {}, []


def _build_for_client(ctx, out_dir: Path, period_be: str, client_id) -> tuple[dict, list[str]]:
    client = _client_row(ctx, client_id)
    if not client or not _valid_tax_id(client.get("tax_id")):
        return {}, [
            "ผู้เสียภาษี (客户) ขาดเลขผู้เสียภาษี 13 หลัก ไม่สามารถออก RD Prep ได้ "
            "(客户缺 13 位税号,ภ.ง.ด.3/53 RD Prep 均不产出)"
        ]

    try:
        ad_start = obligation_engine._period_to_ad_month_start(period_be)
    except obligation_engine.ObligationEngineError:
        return {}, []
    ad_period = f"{ad_start.year:04d}-{ad_start.month:02d}"
    pnd_result = aggregate_pnd(
        ctx.cur, tenant_id=ctx.tenant_id, workspace_client_id=client_id, period=ad_period
    )
    tables = pnd_result["tables"]
    valid = {
        kind: _filter_valid_lines(tables[kind]["lines"]) for kind in (_TABLE_PND53, _TABLE_PND3)
    }
    invalid_payee_count = sum(
        len(tables[kind]["lines"]) - len(valid[kind]) for kind in (_TABLE_PND53, _TABLE_PND3)
    )

    if not valid[_TABLE_PND53] and not valid[_TABLE_PND3]:
        memo = ["ไม่มีรายการหัก ณ ที่จ่ายในงวดนี้ (本期无 WHT,未产出 ภ.ง.ด.3/53 RD Prep)"]
        if invalid_payee_count:
            memo.append(
                f"ผู้รับเงิน {invalid_payee_count} รายขาดเลขผู้เสียภาษี 13 หลัก "
                f"(收款人缺 13 位税号 {invalid_payee_count} 家,已从两表剔除)"
            )
        return {}, memo

    # 键入底稿(辅助件)两表都出,doc_date 服务两表分组;一次 IN 查询覆盖两表,不逐票查。
    doc_ids = [ln["source_purchase_id"] for ln in valid[_TABLE_PND53] + valid[_TABLE_PND3]]
    doc_dates = _fetch_doc_dates(ctx.cur, tenant_id=ctx.tenant_id, doc_ids=doc_ids)

    tax_month, tax_year = period_be.split("-")[1], period_be.split("-")[0]
    branch_no = _derive_branch_code(client.get("branch"))
    branch_type = "V" if client.get("vat_registered") else ""

    kinds: dict[str, tuple[str, dict]] = {}
    memo_lines: list[str] = []

    if valid[_TABLE_PND53]:
        payees = _group_by_payee(valid[_TABLE_PND53], doc_dates)
        text, tot_tax = _assemble_form(
            rdprep.PND53,
            payees,
            sender_nid=client["tax_id"],
            branch_no=branch_no,
            tax_month=tax_month,
            tax_year=tax_year,
            branch_type=branch_type,
        )
        kinds[KIND_PND53] = _write_txt(
            out_dir,
            rdprep.build_filename(
                form=rdprep.PND53,
                nid=client["tax_id"],
                branch_no=branch_no,
                tax_year_be=tax_year,
                tax_month=tax_month,
            ),
            text,
            pnd_kind=KIND_PND53,
            payee_count=len(payees),
            wht_total=tot_tax,
            period=period_be,
        )
        kinds[KIND_PND53_KEYING] = _write_keying_xlsx(
            out_dir,
            rdprep.PND53,
            payees,
            client=client,
            tax_month=tax_month,
            tax_year=tax_year,
            period_be=period_be,
        )

    if valid[_TABLE_PND3]:
        excluded_payees = {ln["payee_tax_id"].strip() for ln in valid[_TABLE_PND3]}
        payees3 = _group_by_payee(valid[_TABLE_PND3], doc_dates)
        kinds[KIND_PND3_KEYING] = _write_keying_xlsx(
            out_dir,
            rdprep.PND3,
            payees3,
            client=client,
            tax_month=tax_month,
            tax_year=tax_year,
            period_be=period_be,
        )
        memo_lines.append(
            f"ผู้รับเงินบุคคลธรรมดา {len(excluded_payees)} รายขาดที่อยู่แบบโครงสร้าง "
            f"(AMPHUR/PROVINCE/POSTAL) จึงไม่รวมใน ภ.ง.ด.3 RD Prep งวดนี้ แต่มีไฟล์คีย์ข้อมูล "
            f"(keying sheet) สำหรับกรอก e-Filing ด้วยตนเองแทน "
            f"(个人预扣税收款人 {len(excluded_payees)} 家缺结构化地址,本期未随批产出 "
            f"ภ.ง.ด.3 RD Prep 官方件,但已产出键入底稿 xlsx 供人工照抄 e-Filing)"
        )

    if invalid_payee_count:
        memo_lines.append(
            f"ผู้รับเงิน {invalid_payee_count} รายขาดเลขผู้เสียภาษี 13 หลัก "
            f"(收款人缺 13 位税号 {invalid_payee_count} 家,已从两表剔除)"
        )

    return kinds, memo_lines


def _keying_rows(form: str, payees: dict[str, dict]) -> list[dict]:
    """payees(_group_by_payee 产出)→ 键入底稿逐行:一 payee 一税率一行,不受 RD Prep txt
    「一序 ≤3 组收入类型」拼行限制(那是官方格式契约,键入底稿是给人逐行照抄的清单)。"""
    rows = []
    for tax_id in sorted(payees):
        payee = payees[tax_id]
        for key in sorted(payee["groups"], key=lambda k: payee["groups"][k]["rate"]):
            g = payee["groups"][key]
            rows.append(
                {
                    "tax_id": tax_id,
                    "title_name": _title_name(form, payee["name"]),
                    "payee_name": payee["name"] or "",
                    "address": None,  # M1 数据源无结构化地址(见模块 docstring),诚实留空
                    "paid_date": g["first_date"],
                    "income_type": _income_type_text(g["rate"]),
                    "rate": g["rate"],
                    "paid_amount": g["base"],
                    "wht_amount": g["wht"],
                    "condition": _CONDITION_LABEL["1"],
                }
            )
    return rows


def _write_keying_xlsx(
    out_dir: Path,
    form: str,
    payees: dict[str, dict],
    *,
    client: dict,
    tax_month: str,
    tax_year: str,
    period_be: str,
) -> tuple[str, dict]:
    rows = _keying_rows(form, payees)
    payload = pnd_keying_sheet.build_workbook(form, rows)
    filename = pnd_keying_sheet.build_filename(
        form=form, nid=client["tax_id"], tax_year_be=tax_year, tax_month=tax_month
    )
    path = out_dir / filename
    path.write_bytes(payload)
    row_totals = pnd_keying_sheet.totals(rows)
    return str(path), {
        "payee_count": len(payees),
        "row_count": len(rows),
        "paid_amount_total": row_totals["paid_amount"],
        "wht_total": row_totals["wht_amount"],
        "period": period_be,
    }


def _write_txt(out_dir: Path, filename: str, text: str, **numbers) -> tuple[str, dict]:
    path = out_dir / filename
    payload = text.encode("utf-8")  # 官方 §7 CR/LF 定长契约:走字节写盘,避开文本模式换行翻译
    path.write_bytes(payload)
    numbers["txt_sha256"] = hashlib.sha256(payload).hexdigest()
    return str(path), numbers
