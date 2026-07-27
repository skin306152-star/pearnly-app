# -*- coding: utf-8 -*-
"""吃附件的两个只读工具(万能口 F1):文件转换 · 销项报告三查。

薄封装,零业务逻辑重写:
  file_convert      services.fileconv.{convert,excel_in,xlsx_out}  (= /api/fileconv/convert)
  vat_report_check  services.vat.{vat_report_parser,vat_report_checks} (= /api/vat_report_checks/run)

哪个文件由代码定,不由模型定:执行侧只认 ctx.attachment_ids(请求侧已按 kind 过滤/追问过),
到这里必须恰好一件 —— 多了少了都是编排出了问题,如实返错误码而不是自己挑一个跑。

产物落回同一张附件表(status=artifact):加密/防穿越/租户隔离/到期清理白拿,而且转出来的
xlsx 下一轮还能当料继续用。工具只出数据,人话在 copy_file 按数据渲染(模型碰不到数字)。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from services.agent.contracts import ToolResult
from services.steward import attachments
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

ERR_NO_ATTACHMENT = "steward.attachment_missing"
ERR_MANY_ATTACHMENTS = "steward.attachment_ambiguous"
ERR_UNREADABLE = "steward.attachment_unreadable"
ERR_CONVERT_REJECTED = "steward.convert_rejected"
ERR_REPORT_UNPARSED = "steward.report_unparsed"

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
_EXCEL_EXTS = (".xlsx", ".xlsm", ".xls", ".csv")
_ISSUES_PREVIEW = 20
_ROWS_PREVIEW = 20


def _single(ctx: ToolContext) -> tuple[Optional[dict], Optional[ToolResult]]:
    """取本轮唯一那件料 + 明文字节。租户/会话/上传人三锚再验一次(worker 没有请求可依附,
    身份闸在这里补);盘上路径再过一次防穿越 —— 库里存的字符串不当可信输入。"""
    from core import db

    ids = [str(i) for i in (ctx.attachment_ids or ())]
    if not ids:
        return None, ToolResult(ok=False, error_code=ERR_NO_ATTACHMENT)
    if len(ids) > 1:
        return None, ToolResult(ok=False, error_code=ERR_MANY_ATTACHMENTS, data={"n": len(ids)})
    with db.get_cursor() as cur:
        rows = attachments.list_by_ids(
            cur, tenant_id=ctx.tenant_id, session_id=ctx.session_id, ids=ids
        )
    row = rows[0] if rows else None
    if not row or str(row.get("user_id") or "") != str(ctx.user_id):
        return None, ToolResult(ok=False, error_code=ERR_NO_ATTACHMENT)
    path = attachments.resolve_within_session(
        ctx.tenant_id, ctx.session_id, row.get("file_ref") or ""
    )
    if not path:
        return None, ToolResult(ok=False, error_code=ERR_UNREADABLE, data=_named(row))
    try:
        row = {**row, "content": attachments.read_content(str(path))}
    except OSError:
        return None, ToolResult(ok=False, error_code=ERR_UNREADABLE, data=_named(row))
    return row, None


def _named(row: dict) -> dict[str, Any]:
    return {"filename": row.get("original_name") or ""}


def file_convert(ctx: ToolContext, args: dict) -> ToolResult:
    """PDF/图片/Excel → 结构化表 + 守恒校验,产物 xlsx 落回附件表供下载。"""
    from services.fileconv.convert import convert_image, convert_pdf
    from services.fileconv.excel_in import convert_excel
    from services.fileconv.model import REJECT_STATUSES
    from services.fileconv.xlsx_out import build_xlsx

    row, err = _single(ctx)
    if err:
        return err
    name = row.get("original_name") or "upload.pdf"
    low = name.lower()
    if low.endswith(_IMAGE_EXTS):
        result = convert_image(row["content"], source_name=name, tenant_id=ctx.tenant_id)
    elif low.endswith(_EXCEL_EXTS):
        result = convert_excel(row["content"], source_name=name)
    else:
        result = convert_pdf(row["content"], source_name=name, tenant_id=ctx.tenant_id)

    if result.status in REJECT_STATUSES:
        # 拒绝态绝不出数据表:截断的行集会让余额链假自洽,比诚实拒绝更危险(model.py 顶注)。
        return ToolResult(
            ok=False,
            error_code=ERR_CONVERT_REJECTED,
            data={"filename": name, "status": result.status},
        )
    produced = _save_xlsx(ctx, build_xlsx(result), name)
    return ToolResult(
        ok=True,
        data={
            "filename": name,
            "doc_type": result.doc_type,
            "status": result.status,
            "conserved": result.conserved,
            # 行数自己数,不读 stats["row_count"]:Excel 网格路的 stats 里根本没有这个键
            # (excel_in 落的是 engine/sheet_count),读它会在半数入口上印出 0 行。
            "row_count": sum(len(t.rows or []) for t in result.tables or []),
            "stats": result.stats,
            "issue_count": len(result.issues),
            "issues": [
                {
                    "kind": i.kind,
                    "line_no": i.line_no,
                    "account": i.account,
                    "message": i.message,
                    "expected": i.expected,
                    "actual": i.actual,
                }
                for i in result.issues[:_ISSUES_PREVIEW]
            ],
            "download": produced,
        },
    )


def _save_xlsx(ctx: ToolContext, content: bytes, source_name: str) -> dict[str, Any]:
    """产物落回附件表。落不下(盘满/库炸)不翻已经跑成的转换 —— 如实回空,答复少一个下载链,
    不把一次成功的转换报成失败。"""
    from core import db

    out_name = f"{Path(source_name).stem or 'convert'}.xlsx"
    try:
        path = attachments.save(
            content,
            tenant_id=ctx.tenant_id,
            session_id=ctx.session_id,
            original_name=out_name,
        )
        with db.get_cursor(commit=True) as cur:
            row = attachments.insert(
                cur,
                tenant_id=ctx.tenant_id,
                session_id=ctx.session_id,
                user_id=ctx.user_id,
                original_name=out_name,
                file_ref=str(path),
                size_bytes=len(content),
                sha256=attachments.sha256_of(content),
                mime=attachments.guess_mime(out_name),
                kind="converted",
                kind_source=attachments.SOURCE_RULE,
                kind_reason="file_convert_output",
                status=attachments.STATUS_ARTIFACT,
            )
    except Exception:  # noqa: BLE001
        logger.warning("[steward.file_convert] artifact save failed", exc_info=True)
        return {}
    return {"attachment_id": str(row["id"]), "name": out_name, "size_bytes": len(content)}


def vat_report_check(ctx: ToolContext, args: dict) -> ToolResult:
    """销项 VAT 报告三查:连号 / 买家分组 / 期间一致性。钱全程 Decimal,出线转定点字符串。"""
    from services.vat.vat_report_checks import run_report_checks, to_jsonable
    from services.vat.vat_report_parser import parse_vat_report

    row, err = _single(ctx)
    if err:
        return err
    name = row.get("original_name") or "report.pdf"
    api_key = (
        (ctx.user or {}).get("gemini_api_key")
        or (ctx.user or {}).get("custom_gemini_api_key")
        or ""
    ).strip() or None
    parsed = parse_vat_report(row["content"], name, api_key=api_key)
    rows = parsed.get("rows") or []
    if not parsed.get("ok") or not rows:
        return ToolResult(
            ok=False,
            error_code=ERR_REPORT_UNPARSED,
            data={"filename": name, "reason": str(parsed.get("error") or "")[:200]},
        )

    checks = to_jsonable(run_report_checks(rows))
    sequence = checks["sequence"]
    families = sequence.get("families") or []
    missing = _missing_rows(families)
    return ToolResult(
        ok=True,
        data={
            "filename": name,
            "row_count": len(rows),
            "period": _period_text(checks["period"]),
            "family_count": len(families),
            "missing_count": len(missing),
            "missing": missing[:_ROWS_PREVIEW],
            "duplicate": (sequence.get("duplicate_invoices") or [])[:_ROWS_PREVIEW],
            "duplicate_count": len(sequence.get("duplicate_invoices") or []),
            "void_count": len(sequence.get("void_invoices") or []),
            "format_anomaly_count": len(sequence.get("format_anomalies") or []),
            "out_of_period": (checks["period"].get("out_of_period") or [])[:_ROWS_PREVIEW],
            "out_of_period_count": len(checks["period"].get("out_of_period") or []),
            "buyer_count": len(checks["buyer_summary"].get("buyers") or []),
            "buyers": (checks["buyer_summary"].get("buyers") or [])[:_ROWS_PREVIEW],
            "grand_total": checks["buyer_summary"].get("grand_total") or {},
        },
    )


def _period_text(period: dict) -> str:
    year, month = period.get("period_year"), period.get("period_month")
    return f"{int(year):04d}-{int(month):02d}" if year and month else ""


def _missing_rows(families: list) -> list[dict[str, Any]]:
    """两种号型的「缺」不是一回事,不许合成一列:传统连号缺的是【号】(IV69/00512),
    日期编码号缺的是【天】(那天一张票都没开)。type 随行走,让文案各说各的。"""
    out: list[dict[str, Any]] = []
    for family in families:
        kind = family.get("type") or ""
        values = family.get("missing") if kind == "numeric" else family.get("missing_days")
        out.extend(
            {"family": family.get("label") or "", "type": kind, "missing": str(v)}
            for v in (values or [])
        )
    return out
