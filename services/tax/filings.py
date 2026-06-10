# -*- coding: utf-8 -*-
"""税表 DAL + 生成/提交状态机(docs/tax-filing/01+02)。

生成幂等:UNIQUE(tenant,ws,period,kind),重算覆盖 prepared,filed 的不动(已报不可改,
错了走更正申报);数据消失的 prepared 草稿直接删(filed 永不删)。提交不可逆 = 安全带:
mark_filed 前先按最新账本重算 + 重跑体检,硬异常拦(绝不让报错表),过了才置 filed。
调用方管事务。
"""

from __future__ import annotations

import calendar
import json
from datetime import date
from decimal import Decimal

from core.pos_api import PosError
from services.tax import aggregate, anomalies
from services.tax import settings as tax_settings

ZERO = Decimal("0")

_COLS = (
    "id, period, kind, status, net_amount, breakdown, anomalies, due_date, "
    "filed_method, receipt_no, filed_at, filed_by, created_at, updated_at"
)

_LINE_COLS = (
    "id, payee_name, payee_tax_id, payee_type, income_type, base_amount, wht_rate, "
    "wht_amount, source_purchase_id, cert_url, cert_status, sort"
)


def due_date(period: str) -> date:
    """纸质申报截止 = 次月 15 日(e-filing 有 +8 天延展,接通 RD 后再按提交方式算)。"""
    year, month = int(period[:4]), int(period[5:7])
    if month == 12:
        year, month = year + 1, 1
    else:
        month += 1
    return date(year, month, min(15, calendar.monthrange(year, month)[1]))


def _jsonb(v) -> str:
    return json.dumps(v, ensure_ascii=False, default=str)


def _as_obj(v, fallback):
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v) if v else fallback
    except (TypeError, ValueError):
        return fallback


def _row_out(row: dict) -> dict:
    out = dict(row)
    out["breakdown"] = _as_obj(out.get("breakdown"), {})
    out["anomalies"] = _as_obj(out.get("anomalies"), [])
    return out


def _upsert(cur, *, tenant_id, workspace_client_id, period, kind, net, breakdown, checked):
    """写一张草稿(filed 不覆盖)。返回行或 None(=已 filed 没动)。"""
    cur.execute(
        "INSERT INTO tax_filings "
        "(tenant_id, workspace_client_id, period, kind, status, net_amount, breakdown, "
        " anomalies, due_date) "
        "VALUES (%s, %s, %s, %s, 'prepared', %s, %s::jsonb, %s::jsonb, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id, period, kind) DO UPDATE SET "
        "status = 'prepared', net_amount = EXCLUDED.net_amount, "
        "breakdown = EXCLUDED.breakdown, anomalies = EXCLUDED.anomalies, "
        "due_date = EXCLUDED.due_date, updated_at = now() "
        "WHERE tax_filings.status != 'filed' "
        f"RETURNING {_COLS}",
        (
            tenant_id,
            workspace_client_id,
            period,
            kind,
            net,
            _jsonb(breakdown),
            _jsonb(checked),
            due_date(period),
        ),
    )
    return cur.fetchone()


def _replace_lines(cur, *, tenant_id, filing_id, lines) -> None:
    cur.execute(
        "DELETE FROM filing_lines WHERE tenant_id = %s AND filing_id = %s",
        (tenant_id, filing_id),
    )
    for i, ln in enumerate(lines):
        cur.execute(
            "INSERT INTO filing_lines "
            "(tenant_id, filing_id, payee_name, payee_tax_id, payee_type, income_type, "
            " base_amount, wht_rate, wht_amount, source_purchase_id, cert_url, cert_status, sort) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                tenant_id,
                filing_id,
                ln["payee_name"],
                ln["payee_tax_id"],
                ln["payee_type"],
                ln["income_type"],
                ln["base_amount"],
                ln["wht_rate"],
                ln["wht_amount"],
                ln["source_purchase_id"],
                ln["cert_url"],
                ln["cert_status"],
                i,
            ),
        )


def _drop_stale_draft(cur, *, tenant_id, workspace_client_id, period, kind) -> None:
    """该期该表已无数据 → 删草稿(filed 永不删,filing_lines 级联)。"""
    cur.execute(
        "DELETE FROM tax_filings "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s AND kind = %s "
        "AND status != 'filed'",
        (tenant_id, workspace_client_id, period, kind),
    )


def generate_filings(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> list:
    """本期全部税表草稿(close-period 挂点 / 手动重算共用)。返回生成/更新的行。

    PP30:VAT 登记才生成;0 税额默认也生成(file_zero·泰国月度强制),设置关了且
    全零(无任何销/进项行)才跳过。PND:有代扣明细才生成(无 0 申报义务)。
    """
    settings = tax_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    out = []

    if settings["vat_registered"]:
        agg = aggregate.pp30(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
        )
        b = agg["breakdown"]
        is_empty = b["output_count"] == 0 and b["input_count"] == 0
        if settings["file_zero"] or not is_empty:
            checked = anomalies.check(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                kind=aggregate.PP30,
                payload=b,
            )
            row = _upsert(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                kind=aggregate.PP30,
                net=agg["net"],
                breakdown=b,
                checked=checked,
            )
            if row is not None:
                out.append(_row_out(row))
        else:
            _drop_stale_draft(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                kind=aggregate.PP30,
            )

    pnd = aggregate.pnd(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    for kind in (aggregate.PND53, aggregate.PND3):
        table = pnd["tables"][kind]
        if not table["lines"]:
            _drop_stale_draft(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
                kind=kind,
            )
            continue
        breakdown = {
            "wht_total": table["total"],
            "line_count": len(table["lines"]),
            "missing_tax_id": table["missing_tax_id"],
        }
        checked = anomalies.check(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=period,
            kind=kind,
            payload=breakdown,
        )
        row = _upsert(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=period,
            kind=kind,
            net=table["total"],
            breakdown=breakdown,
            checked=checked,
        )
        if row is not None:
            _replace_lines(cur, tenant_id=tenant_id, filing_id=row["id"], lines=table["lines"])
            out.append(_row_out(row))
    return out


def list_filings(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    cur.execute(
        f"SELECT {_COLS} FROM tax_filings "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND period = %s "
        "ORDER BY kind",
        (tenant_id, workspace_client_id, period),
    )
    items = [_row_out(r) for r in cur.fetchall()]
    unfiled = [i for i in items if i["status"] != "filed"]
    total_due = sum(
        (Decimal(str(i["net_amount"])) for i in unfiled if Decimal(str(i["net_amount"])) > ZERO),
        ZERO,
    )
    return {
        "summary": {
            "period": period,
            "total_due": total_due,
            "next_due_date": min((i["due_date"] for i in unfiled), default=None),
            "filed_count": len(items) - len(unfiled),
            "pending_count": len(unfiled),
        },
        "items": items,
    }


def get_filing(cur, *, tenant_id: str, workspace_client_id: int, filing_id: str):
    cur.execute(
        f"SELECT {_COLS} FROM tax_filings "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, filing_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    out = _row_out(row)
    cur.execute(
        f"SELECT {_LINE_COLS} FROM filing_lines "
        "WHERE tenant_id = %s AND filing_id = %s ORDER BY sort",
        (tenant_id, filing_id),
    )
    out["lines"] = [dict(r) for r in cur.fetchall()]
    return out


def require_filing(cur, *, tenant_id: str, workspace_client_id: int, filing_id: str) -> dict:
    filing = get_filing(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, filing_id=filing_id
    )
    if filing is None:
        raise PosError("tax.unexpected", 404, detail="filing_not_found")
    return filing


def recompute(cur, *, tenant_id: str, workspace_client_id: int, filing_id: str) -> dict:
    """按最新账本重算本期(覆盖 prepared;filed 拒绝)。"""
    filing = require_filing(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, filing_id=filing_id
    )
    if filing["status"] == "filed":
        raise PosError("tax.already_filed", 409)
    generate_filings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=filing["period"]
    )
    fresh = get_filing(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, filing_id=filing_id
    )
    if fresh is None:
        # 数据已清空(如源单全作废)→ 草稿随之消失,诚实返回而非留旧数
        raise PosError("tax.unexpected", 404, detail="no_data_after_recompute")
    return fresh


def fresh_anomalies(cur, *, tenant_id: str, workspace_client_id: int, filing: dict) -> list:
    """按当下数据重跑体检(不信存的 anomalies 缓存)。/check 端点与提交安全带共用。"""
    if filing["kind"] == aggregate.PP30:
        payload = aggregate.pp30(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=filing["period"],
        )["breakdown"]
    else:
        table = aggregate.pnd(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=filing["period"],
        )["tables"][filing["kind"]]
        payload = {"missing_tax_id": table["missing_tax_id"]}
    return anomalies.check(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=filing["period"],
        kind=filing["kind"],
        payload=payload,
    )


def _raise_hard(checked: list) -> None:
    hard = anomalies.hard_codes(checked)
    if "period_not_closed" in hard:
        raise PosError("tax.period_not_closed", 409)
    if "wht_missing_tax_id" in hard:
        raise PosError("tax.missing_tax_id", 422)
    if hard:
        raise PosError("tax.has_anomaly", 422, detail=",".join(hard))


def assert_fileable(cur, *, tenant_id: str, workspace_client_id: int, filing: dict) -> list:
    """提交前安全带:体检硬异常拦(绝不让报错表)。返回最新 anomaly 列表。"""
    checked = fresh_anomalies(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, filing=filing
    )
    _raise_hard(checked)
    return checked


def mark_filed(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    filing_id: str,
    method: str,
    receipt_no=None,
    filed_by=None,
) -> dict:
    """置 filed(不可逆)。先重算锁最新数 + 体检过才放行;已报 → tax.already_filed。

    重算刚把按最新账本跑的体检落了库,直接拿它拦,不再重跑一遍 aggregate。
    """
    filing = recompute(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, filing_id=filing_id
    )
    _raise_hard(filing["anomalies"])
    cur.execute(
        "UPDATE tax_filings SET status = 'filed', filed_method = %s, receipt_no = %s, "
        "filed_at = now(), filed_by = %s, updated_at = now() "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status != 'filed' "
        f"RETURNING {_COLS}",
        (method, receipt_no, filed_by, tenant_id, workspace_client_id, filing_id),
    )
    row = cur.fetchone()
    if row is None:
        raise PosError("tax.already_filed", 409)
    return _row_out(row)


def require_line_source(cur, *, tenant_id: str, workspace_client_id: int, line_id: str) -> str:
    """PND 行 → 源进项单 id(扣缴凭证补开入口)。无行/无源单 → 404。"""
    cur.execute(
        "SELECT l.source_purchase_id FROM filing_lines l "
        "JOIN tax_filings f ON f.id = l.filing_id AND f.tenant_id = l.tenant_id "
        "WHERE l.tenant_id = %s AND f.workspace_client_id = %s AND l.id = %s",
        (tenant_id, workspace_client_id, line_id),
    )
    row = cur.fetchone()
    if row is None or not row["source_purchase_id"]:
        raise PosError("tax.unexpected", 404, detail="line_not_found")
    return str(row["source_purchase_id"])


def set_line_cert(
    cur, *, tenant_id: str, workspace_client_id: int, line_id: str, cert_url: str
) -> dict:
    """补登扣缴凭证 URL(issue 端点·凭证本体由进项模块生成)。已报的表不可改。"""
    cur.execute(
        "SELECT l.id, l.source_purchase_id, f.status FROM filing_lines l "
        "JOIN tax_filings f ON f.id = l.filing_id AND f.tenant_id = l.tenant_id "
        "WHERE l.tenant_id = %s AND f.workspace_client_id = %s AND l.id = %s",
        (tenant_id, workspace_client_id, line_id),
    )
    row = cur.fetchone()
    if row is None:
        raise PosError("tax.unexpected", 404, detail="line_not_found")
    if row["status"] == "filed":
        raise PosError("tax.already_filed", 409)
    if not row["source_purchase_id"]:
        raise PosError("tax.unexpected", 422, detail="line_has_no_source")
    cur.execute(
        "UPDATE filing_lines SET cert_url = %s, cert_status = 'generated' "
        "WHERE tenant_id = %s AND id = %s "
        f"RETURNING {_LINE_COLS}",
        (cert_url, tenant_id, line_id),
    )
    return dict(cur.fetchone())
