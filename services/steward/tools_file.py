# -*- coding: utf-8 -*-
"""吃附件的两个只读工具(万能口 F1):文件转换 · 销项报告三查。

薄封装,零业务逻辑重写:
  file_convert      services.fileconv.{convert,excel_in,xlsx_out}  (= /api/fileconv/convert)
  vat_report_check  services.vat.{vat_report_parser,vat_report_checks} (= /api/vat_report_checks/run)

取件(single_attachment)与产物落库(save_xlsx)在 tool_scope —— doc_read_qa/table_generate
共用同一套三锚与防穿越,不在这里各写一份。哪个文件由代码定,不由模型定:执行侧只认
ctx.attachment_ids(请求侧已按 kind 过滤/追问过),到这里必须恰好一件 —— 多了少了都是编排
出了问题,如实返错误码而不是自己挑一个跑。

产物落回同一张附件表(status=artifact):加密/防穿越/租户隔离/到期清理白拿,而且转出来的
xlsx 下一轮还能当料继续用。工具只出数据,人话在 copy_file 按数据渲染(模型碰不到数字)。
"""

from __future__ import annotations

from typing import Any

from services.steward.contracts import ToolResult
from services.steward import tool_scope
from services.steward.registry import ToolContext
from services.cost.usage_context import usage_context
from services.steward.tool_scope import (  # 入口仍在 tools_file:调用方按 tools_file.ERR_* 认错误码
    ERR_MANY_ATTACHMENTS,  # noqa: F401
    ERR_NO_ATTACHMENT,  # noqa: F401
    ERR_UNREADABLE,  # noqa: F401
)

ERR_CONVERT_REJECTED = "steward.convert_rejected"
ERR_REPORT_UNPARSED = "steward.report_unparsed"
ERR_REPORT_NEEDS_MODEL = "steward.report_needs_model"

_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
# excel_in.convert_excel 的 _ALL_EXTS 早已收 tsv/txt(表格族的三种分隔文本变体);这里漏抄
# 过一次 —— 漏掉的两个后果不是「拒收」而是悄悄落进下面的 else 分支当 PDF 解,一份 .tsv 的
# 字节喂给 convert_pdf 必然读不出页,白跑一趟且报错文案会说「转不出来」而不是格式不支持。
_EXCEL_EXTS = (".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".txt")
_ISSUES_PREVIEW = 20
_ROWS_PREVIEW = 20


def file_convert(ctx: ToolContext, args: dict) -> ToolResult:
    """PDF/图片/Excel → 结构化表 + 守恒校验,产物 xlsx 落回附件表供下载。"""
    from services.fileconv.convert import convert_image, convert_pdf
    from services.fileconv.excel_in import convert_excel
    from services.fileconv.model import REJECT_STATUSES
    from services.fileconv.xlsx_out import build_xlsx

    row, err = tool_scope.single_attachment(ctx)
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
    produced = tool_scope.save_xlsx(ctx, build_xlsx(result), name)
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


def vat_report_check(ctx: ToolContext, args: dict) -> ToolResult:
    """销项 VAT 报告三查:连号 / 买家分组 / 期间一致性。钱全程 Decimal,出线转定点字符串。

    args.model_ok 是「人在卡上点过『会过一次模型』」的凭据(attach_turn.decide 落的)。
    没有这张凭据就绝不让 parse_vat_report 走它的模型回退分支 —— 那条路上会计既没被告知
    也没点过头,而回执卡上的按钮明写着 cost.model_call=false。"""
    from services.steward import attach_kinds
    from services.vat.vat_report_checks import run_report_checks, to_jsonable
    from services.vat.vat_report_parser import parse_vat_report

    row, err = tool_scope.single_attachment(ctx)
    if err:
        return err
    name = row.get("original_name") or "report.pdf"
    if not args.get("model_ok") and attach_kinds.vat_check_needs_model(row["content"], name):
        return ToolResult(ok=False, error_code=ERR_REPORT_NEEDS_MODEL, data={"filename": name})
    api_key = (
        (ctx.user or {}).get("gemini_api_key")
        or (ctx.user or {}).get("custom_gemini_api_key")
        or ""
    ).strip() or None
    with usage_context("steward", doc_type="vat_report"):
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
