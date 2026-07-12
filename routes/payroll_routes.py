# -*- coding: utf-8 -*-
"""H1b · 工资表 ภ.ง.ด.1 工具卡 HTTP 端点(照 fileconv_routes.py 范式)。

引擎(services/payroll/、services/tax/pnd1_attach.py、services/tax/rdprep_pnd1.py)一行不改——
本文件只编排:parse 猜列/套模板(纯读) → commit 校验+落库+点亮义务 → output 从库读回
装配三产出下载。落库按 (tenant, client, period) 整体替换,供 ภ.ง.ด.1ก 年度聚合复用同一份
月度数据(方案 §2.3)。

全组挂 feature flag pearnly_ai_m1(闸关 → 404 fail-closed,同 fileconv_routes 先例)。
权限复用 tax.filing.view——工资进料是会计工作台工具,权限边界与查看申报工单一致。
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
from decimal import Decimal
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core import db
from core.route_helpers import authorize_pearnly_ai
from services.payroll import guess, intake, keying_sheet, model, obligations, store, validate
from services.payroll.model import PayrollRow
from services.tax import pnd1_attach, rdprep_pnd1

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payroll", tags=["payroll"])

_PERM = "tax.filing.view"
_MAX_BYTES = 20 * 1024 * 1024
_PREVIEW_ROWS = 20
_OUTPUT_KINDS = ("keying", "attach", "central")
_KEYING_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_TEXT_MEDIA = "text/plain; charset=utf-8"


def _issue_out(issue: model.Issue) -> dict:
    return {
        "kind": issue.kind,
        "field": issue.field,
        "message": issue.message,
        "row_no": issue.row_no,
        "value": issue.value,
    }


def _header_hash(header: list) -> str:
    """表头形态指纹(同表头再上传 → 命中模板)。列名文本 + 顺序即身份,不掺数据行。"""
    raw = json.dumps([str(h) for h in header], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cell_out(value):
    """原始单元格 → JSON 安全值(预览用,只读展示不进计算)。"""
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    return str(value)


def _content_disposition(filename: str) -> str:
    """泰文原名走 RFC 5987 filename*(HTTP 头只认 latin-1),同 fileconv_routes 先例。"""
    encoded = quote(filename.encode("utf-8"))
    return f"attachment; filename=\"payroll.txt\"; filename*=UTF-8''{encoded}"


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, detail="payroll.file_too_large")
    if not data:
        raise HTTPException(400, detail="payroll.empty_file")
    return data


def _load_client(cur, tenant_id: str, workspace_client_id: int) -> dict:
    """越权/不存在的账套主体一律 404(不泄漏存在性),同 client_pool_routes 先例。"""
    cur.execute(
        "SELECT id, name, tax_id FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(404, detail="payroll.client_not_found")
    return dict(row)


def _parse_json_field(raw: str, default):
    try:
        return json.loads(raw) if raw else default
    except (ValueError, TypeError):
        raise HTTPException(400, detail="payroll.bad_request")


def _default_paid_date(rows: list, fixed: dict):
    """手工加行未收支付日输入(方案 §手工加行:仅称谓/名/姓/身份证/实付/预扣六字段)——
    同批次导入行已定的支付日(整表同值场景最常见)拿来当手工行默认值,免得输出阶段
    因缺支付日报错(pnd1_attach/rdprep_pnd1 硬要求 row.paid_date)。fixed 已给整列值时
    不需要(rows_from_manual 会自己套用 fixed)。"""
    if model.F_PAID_DATE in fixed:
        return None
    for row in rows:
        if row.paid_date is not None:
            return row.paid_date
    return None


def _row_from_db(r: dict) -> PayrollRow:
    """load_period_rows 的 dict 行 → PayrollRow(与三产出装配函数要求的类型一致)。"""
    return PayrollRow(
        seq=r["seq"],
        employee_id=r["employee_id"],
        title=r["title"],
        first_name=r["first_name"],
        last_name=r["last_name"],
        paid_amount=r["paid_amount"],
        wht_amount=r["wht_amount"],
        paid_date=r["paid_date"],
        income_code=r["income_code"],
        condition=r["condition"],
    )


def _year_month(period: str) -> tuple:
    if not period or "-" not in period:
        return "", ""
    year, month = period.split("-", 1)
    return year, month


@router.post("/parse")
async def parse_endpoint(
    request: Request,
    file: UploadFile = File(...),
    workspace_client_id: int = Form(...),
    period: str = Form(...),
):
    """上传工资 Excel → 有模板(header_hash 命中)直接回模板映射,否则跑猜列。纯读不落库。"""
    _user, tenant_id = authorize_pearnly_ai(request, _PERM, not_found="payroll.not_found")
    data = await _read_upload(file)

    header, raw_rows = intake.read_workbook(data)
    if not header:
        raise HTTPException(400, detail="payroll.empty_workbook")
    header_hash = _header_hash(header)

    with db.get_cursor() as cur:
        _load_client(cur, tenant_id, workspace_client_id)
        template = store.get_template(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )

    template_hit = bool(template and template["header_hash"] == header_hash)
    if template_hit:
        column_map = {k: int(v) for k, v in template["column_map"].items()}
        guessed = {
            field_key: {"column": col, "confidence": guess.CONF_HIGH, "reason": "template_hit"}
            for field_key, col in column_map.items()
        }
        income_code = template["income_code"]
        fixed_values = template["fixed_values"]
    else:
        candidates = guess.guess_columns(header, raw_rows)
        guessed = {
            field_key: {"column": c.column, "confidence": c.confidence, "reason": c.reason}
            for field_key, c in candidates.items()
        }
        income_code = model.DEFAULT_INCOME_CODE
        fixed_values = {}

    payer_col = guess.find_constant_id_column(header, raw_rows)
    payer_id_candidate = None
    if payer_col is not None:
        for raw in raw_rows:
            if payer_col < len(raw) and raw[payer_col] is not None:
                payer_id_candidate = intake.coerce_id(raw[payer_col])
                break

    return {
        "header": [_cell_out(h) for h in header],
        "preview_rows": [[_cell_out(c) for c in r] for r in raw_rows[:_PREVIEW_ROWS]],
        "guessed": guessed,
        "template_hit": template_hit,
        "payer_id_candidate": payer_id_candidate,
        "required_fields": list(model.REQUIRED_FIELDS),
        "guessable_fields": list(model.GUESSABLE_FIELDS),
        "income_code": income_code,
        "fixed_values": fixed_values,
    }


@router.post("/commit")
async def commit_endpoint(
    request: Request,
    file: UploadFile = File(...),
    workspace_client_id: int = Form(...),
    period: str = Form(...),
    column_map: str = Form(...),
    fixed_values: str = Form("{}"),
    income_code: str = Form(model.DEFAULT_INCOME_CODE),
    manual_entries: str = Form("[]"),
):
    """确认过的列映射 → 结构化行 → 校验 → 落库(整体替换)+ 套模板 + 点亮义务。

    issues 有货不阻断落库(只验不算·诚实点名);仅全过校验(issues 为空)才点亮 pnd1
    (obligations.light_pnd1_obligation 的诚实边界:半成品数据不冒充"已申报有据")。
    """
    user, tenant_id = authorize_pearnly_ai(request, _PERM, not_found="payroll.not_found")
    data = await _read_upload(file)
    header, raw_rows = intake.read_workbook(data)
    if not header:
        raise HTTPException(400, detail="payroll.empty_workbook")

    cmap = {k: int(v) for k, v in _parse_json_field(column_map, {}).items()}
    fixed = _parse_json_field(fixed_values, {})
    manual = _parse_json_field(manual_entries, [])
    if model.F_INCOME_CODE not in cmap and model.F_INCOME_CODE not in fixed:
        fixed[model.F_INCOME_CODE] = income_code or model.DEFAULT_INCOME_CODE

    all_rows = intake.build_rows(header, raw_rows, cmap, fixed_values=fixed)

    manual_rows = []
    if manual:
        manual_fixed = dict(fixed)
        default_date = _default_paid_date(all_rows, fixed)
        if default_date is not None:
            manual_fixed[model.F_PAID_DATE] = default_date
        manual_rows = intake.rows_from_manual(manual, fixed_values=manual_fixed)
        start_seq = max((r.seq for r in all_rows), default=0) + 1
        for i, row in enumerate(manual_rows):
            row.seq = start_seq + i

    combined = all_rows + manual_rows
    rows, declared_total = intake.partition_rows(combined)
    issues = validate.validate_rows(rows, period=period, declared_total=declared_total)
    total_paid = validate.total_paid(rows)
    total_wht = sum((r.wht_amount or Decimal("0") for r in rows), Decimal("0"))
    header_hash = _header_hash(header)

    with db.get_cursor(commit=True) as cur:
        _load_client(cur, tenant_id, workspace_client_id)
        store.upsert_template(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            column_map=cmap,
            income_code=income_code or model.DEFAULT_INCOME_CODE,
            fixed_values=fixed,
            header_hash=header_hash,
        )
        row_count = store.save_period_rows(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=period,
            rows=rows,
        )
        if not issues:
            obligations.light_pnd1_obligation(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
            )

    logger.info(
        f"[payroll] commit user={user['id']} client={workspace_client_id} period={period} "
        f"rows={row_count} issues={len(issues)}"
    )
    return {
        "row_count": row_count,
        "totals": {"paid_amount": str(total_paid), "wht_amount": str(total_wht)},
        "declared_total": str(declared_total) if declared_total is not None else None,
        "issues": [_issue_out(i) for i in issues],
        "template_saved": True,
    }


@router.get("/output")
async def output_endpoint(
    request: Request,
    workspace_client_id: int = Query(...),
    period: str = Query(...),
    kind: str = Query(...),
):
    """从库读回已落库的月度进料行,装配三产出之一并回附件——响应字节走
    `.encode("utf-8")` 直进 BytesIO,零文本模式二次转换(引擎字节精确契约)。"""
    _user, tenant_id = authorize_pearnly_ai(request, _PERM, not_found="payroll.not_found")
    if kind not in _OUTPUT_KINDS:
        raise HTTPException(400, detail="payroll.bad_kind")

    with db.get_cursor() as cur:
        client = _load_client(cur, tenant_id, workspace_client_id)
        raw_rows = store.load_period_rows(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
        )

    if not raw_rows:
        raise HTTPException(
            404,
            detail={
                "code": "payroll.no_period_data",
                "message": f"No payroll rows for workspace_client_id={workspace_client_id} "
                f"period={period}",
            },
        )

    rows = [_row_from_db(r) for r in raw_rows]
    nid = client.get("tax_id") or ""
    tax_year, tax_month = _year_month(period)

    if kind == "keying":
        content = keying_sheet.build_workbook(rows)
        filename = keying_sheet.build_filename(nid=nid, tax_year_be=tax_year, tax_month=tax_month)
        return StreamingResponse(
            io.BytesIO(content),
            media_type=_KEYING_MEDIA,
            headers={"Content-Disposition": _content_disposition(filename)},
        )

    if kind == "attach":
        text = pnd1_attach.build_attachment(rows)
        filename = f"PND1_{nid}_{tax_year}_{tax_month}_attach.txt"
        return StreamingResponse(
            io.BytesIO(text.encode("utf-8")),
            media_type=_TEXT_MEDIA,
            headers={"Content-Disposition": _content_disposition(filename)},
        )

    text = _build_central(nid, tax_year, tax_month, rows)
    filename = rdprep_pnd1.build_filename(
        nid=nid, branch_no="000000", tax_year_be=tax_year, tax_month=tax_month
    )
    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type=_TEXT_MEDIA,
        headers={"Content-Disposition": _content_disposition(filename)},
    )


def _build_central(nid: str, tax_year: str, tax_month: str, rows: list) -> str:
    """官方 FORMAT กลาง header_dict 键序照 services/payroll/cli.py:88-101(单一事实源),
    无源字段(地址项)诚实留空,不臆造。"""
    return rdprep_pnd1.build_file(
        {
            "SENDER_NID": nid,
            "NID": nid,
            "SENDER_ROLE": "1",
            "BRANCH_NO": "000000",
            "DEPT_NAME": "สำนักงานใหญ่",
            "LTO": "0",
            "TAX_MONTH": tax_month,
            "TAX_YEAR": tax_year,
            "FORM_TYPE": "00",
            "USER_ID": "",
            "FORM_FLAG": "2",
        },
        rows,
        branch_no="000000",
    )
