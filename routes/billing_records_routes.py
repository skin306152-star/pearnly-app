# -*- coding: utf-8 -*-
"""Pearnly · 账单记录路由 · 预览列表(可按天/月/年筛选)+ 全量明细导出。

GET /api/credits/records       · 扣费/充值/识别 三类按 tab 取最近 N 条,可按 period
                                 (day/month/year/all)筛选;all=最新在前。数据实时(无缓存)。
GET /api/credits/billing-export· 三类全量明细 → 一个 xlsx(三 sheet · 表头随 lang)。

扣费=credit_transactions(usage+subscription)· 充值=topup_requests(仅 owner)·
识别=ocr_history(派生三态 成功/待复核/失败)。owner 看全租户,员工只看自己。
billing_routes 顶部 include_router 聚合 · 本模块仅 HTTP handler + 取数。
"""

from __future__ import annotations

import datetime as _dt
import logging

from fastapi import APIRouter, HTTPException, Request, Response

from core import db
from core.auth import get_current_user_from_request
from services.authz.deps import is_owner_role
from services.ocr_history import list_status as _ls

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_ROW_CAP = 5000  # 导出单 sheet 上限 · 命中则告警(不静默截断)
_PREVIEW_MAX = 50  # 预览单页上限
_BKK = _dt.timezone(_dt.timedelta(hours=7))


def _fmt_dt(value) -> str:
    """datetime / ISO str → 'YYYY-MM-DD HH:MM'(空→'')。"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("T", " ")[:16]
    try:
        return value.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)[:16]


def _period_range(period: str, date_str: str | None):
    """period(day/month/year)+ 锚点日期 → [start, end) 两个 date;all/非法 → (None, None)。"""
    p = (period or "all").lower()
    if p not in ("day", "month", "year"):
        return None, None
    try:
        anchor = _dt.date.fromisoformat(date_str) if date_str else _dt.datetime.now(_BKK).date()
    except Exception:
        anchor = _dt.datetime.now(_BKK).date()
    if p == "day":
        return anchor, anchor + _dt.timedelta(days=1)
    if p == "month":
        start = anchor.replace(day=1)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        return start, end
    start = anchor.replace(month=1, day=1)
    return start, start.replace(year=start.year + 1)


def _one_month_ago(d: "_dt.date") -> "_dt.date":
    """同日上个月(短月夹到月末)· 月初跨年回退。"""
    import calendar

    y, m = (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)
    return d.replace(year=y, month=m, day=min(d.day, calendar.monthrange(y, m)[1]))


def _export_range(period: str, date_str: str | None):
    """导出区间:period=day/month/year → 该区间;all/缺省 → 默认近一个月(截止今天)。
    返回 [start, end) 两个 date(始终有界,导出不再全量)。"""
    start, end = _period_range(period, date_str)
    if start and end:
        return start, end
    today = _dt.datetime.now(_BKK).date()
    return _one_month_ago(today), today + _dt.timedelta(days=1)


def _range_sql(col: str, start, end, params: list) -> str:
    if not start or not end:
        return ""
    params.extend([start, end])
    return f"AND {col} >= %s AND {col} < %s"


# ── 取数(三类 · date 范围可选 · 用于预览 limit 小 / 导出 limit=_ROW_CAP)─────


def _q_usage(cur, tid, uid, start, end, limit, offset=0):
    uid_sql = "AND ct.user_id = %s::uuid" if uid else ""
    base = [tid] + ([uid] if uid else [])
    rng: list = []
    rsql = _range_sql("ct.created_at", start, end, rng)
    cur.execute(
        f"""SELECT COUNT(*) AS n FROM credit_transactions ct
            WHERE ct.tenant_id = %s::uuid AND ct.type IN ('usage','subscription') {uid_sql} {rsql}""",
        base + rng,
    )
    total = int(cur.fetchone()["n"])
    cur.execute(
        f"""
        SELECT ct.created_at, ct.type, ct.description, ct.pages,
               ct.amount_thb AS cost_thb, ct.balance_after, oh.filename
        FROM credit_transactions ct
        LEFT JOIN ocr_history oh
            ON oh.user_id = ct.user_id::uuid
            AND ct.description LIKE '%% · ' || LEFT(oh.id::text, 8)
        WHERE ct.tenant_id = %s::uuid AND ct.type IN ('usage','subscription') {uid_sql} {rsql}
        ORDER BY ct.created_at DESC
        LIMIT %s OFFSET %s
    """,
        base + rng + [limit, offset],
    )
    rows = [
        {
            "date": _fmt_dt(r["created_at"]),
            "type": r["type"],
            "description": r["description"] or "",
            "filename": r["filename"] or "",
            "pages": int(r["pages"] or 0),
            "cost_thb": float(r["cost_thb"] or 0),
            "balance_after": (
                float(r["balance_after"]) if r["balance_after"] is not None else None
            ),
        }
        for r in cur.fetchall()
    ]
    return rows, total


def _q_topup(cur, tid, start, end, limit, offset=0):
    rng: list = []
    rsql = _range_sql("created_at", start, end, rng)
    cur.execute(
        f"SELECT COUNT(*) AS n FROM topup_requests WHERE tenant_id = %s {rsql}", [tid] + rng
    )
    total = int(cur.fetchone()["n"])
    cur.execute(
        f"""
        SELECT id, created_at, amount_thb, payer_name, status, review_note, reviewed_at, note
        FROM topup_requests WHERE tenant_id = %s {rsql}
        ORDER BY created_at DESC LIMIT %s OFFSET %s
    """,
        [tid] + rng + [limit, offset],
    )
    rows = [
        {
            "id": r["id"],
            "created_at": _fmt_dt(r["created_at"]),
            "amount_thb": float(r["amount_thb"] or 0),
            "payer_name": r["payer_name"] or "",
            "status": r["status"] or "",
            "reviewed_at": _fmt_dt(r["reviewed_at"]),
            "note": r["note"] or r["review_note"] or "",
        }
        for r in cur.fetchall()
    ]
    return rows, total


def _q_ocr(cur, tid, uid, start, end, limit, offset=0):
    """识别记录:ocr_history.tenant_id 多为 NULL → 按 user 归属过滤(owner 看本租户全员)。"""
    if uid:
        scope = "user_id = %s::uuid"
        sp = [uid]
    else:
        scope = "user_id IN (SELECT id FROM users WHERE tenant_id = %s::uuid)"
        sp = [tid]
    rng: list = []
    rsql = _range_sql("created_at", start, end, rng)
    cur.execute(f"SELECT COUNT(*) AS n FROM ocr_history WHERE {scope} {rsql}", sp + rng)
    total = int(cur.fetchone()["n"])
    cur.execute(
        f"""
        SELECT created_at, filename, invoice_no, seller_name, total_amount, page_count, source,
               {_ls.STATUS_CASE_SQL} AS status
        FROM ocr_history WHERE {scope} {rsql}
        ORDER BY created_at DESC LIMIT %s OFFSET %s
    """,
        sp + rng + [limit, offset],
    )
    rows = [
        {
            "created_at": _fmt_dt(r["created_at"]),
            "filename": r["filename"] or "",
            "invoice_no": r["invoice_no"] or "",
            "seller_name": r["seller_name"] or "",
            "total_amount": (float(r["total_amount"]) if r["total_amount"] is not None else None),
            "page_count": int(r["page_count"] or 0),
            "source": r["source"] or "manual",
            "status": r["status"] or "pending",
        }
        for r in cur.fetchall()
    ]
    return rows, total


@router.get("/api/credits/records")
async def list_records(
    request: Request,
    tab: str = "usage",
    period: str = "all",
    date: str = None,
    limit: int = 10,
    offset: int = 0,
):
    """三类记录预览(按 tab)· period=day/month/year/all · all=最新在前 · offset 翻页。"""
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        return {"rows": [], "total": 0, "tab": tab, "period": period}
    if tab not in ("usage", "topup", "ocr"):
        raise HTTPException(status_code=400, detail="bad_tab")
    limit = min(_PREVIEW_MAX, max(1, int(limit)))
    offset = max(0, int(offset))
    is_owner = is_owner_role(request, user)
    uid = None if is_owner else str(user["id"])
    start, end = _period_range(period, date)
    try:
        with db.get_cursor_rls(tenant_id=tid, user_id=uid) as cur:
            if tab == "usage":
                rows, total = _q_usage(cur, tid, uid, start, end, limit, offset)
            elif tab == "topup":
                if not is_owner:  # 充值是租户级(含余额信息)· 员工不可见
                    rows, total = [], 0
                else:
                    rows, total = _q_topup(cur, tid, start, end, limit, offset)
            else:
                rows, total = _q_ocr(cur, tid, uid, start, end, limit, offset)
    except Exception as e:
        logger.warning(f"list_records tab={tab} tenant={tid[:8]}: {e}")
        return {"rows": [], "total": 0, "tab": tab, "period": period}
    return {"rows": rows, "total": total, "tab": tab, "period": period}


@router.get("/api/credits/billing-export")
async def billing_export(request: Request, lang: str = "zh", period: str = "all", date: str = None):
    """扣费/充值/识别 三类明细 → xlsx(三 sheet · 表头随 lang)。
    按区间导出:period=day/month/year 用该区间;all/缺省 → 默认近一个月(截止今天)。"""
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        raise HTTPException(status_code=400, detail="no_tenant")
    if lang not in ("zh", "en", "th", "ja"):
        lang = "zh"
    is_owner = is_owner_role(request, user)
    uid = None if is_owner else str(user["id"])
    start, end = _export_range(period, date)

    company = ""
    usage_rows: list[dict] = []
    topup_rows: list[dict] = []
    ocr_rows: list[dict] = []
    try:
        with db.get_cursor_rls(tenant_id=tid, user_id=uid) as cur:
            cur.execute("SELECT name FROM tenants WHERE id = %s::uuid", (tid,))
            trow = cur.fetchone()
            company = (trow.get("name") if trow else "") or ""
            usage_rows, u_total = _q_usage(cur, tid, uid, start, end, _ROW_CAP)
            if is_owner:
                topup_rows, _ = _q_topup(cur, tid, start, end, _ROW_CAP)
            ocr_rows, o_total = _q_ocr(cur, tid, uid, start, end, _ROW_CAP)
            if u_total > _ROW_CAP or o_total > _ROW_CAP:
                logger.warning(f"billing-export capped {_ROW_CAP} tenant={tid[:8]}")
    except Exception as e:
        logger.error(f"billing_export gather tenant={tid}: {e}")
        raise HTTPException(status_code=500, detail="query_failed")

    from services.usage.billing_export import build_billing_xlsx

    try:
        data = build_billing_xlsx(
            lang=lang,
            company=company or "—",
            usage_rows=usage_rows,
            topup_rows=topup_rows,
            ocr_rows=ocr_rows,
        )
    except Exception as e:
        logger.error(f"billing_export build tenant={tid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="build_failed")

    safe = (
        "".join(ch for ch in (company or "tenant") if ch.isalnum() or ch in "-_")[:24] or "tenant"
    )
    last = end - _dt.timedelta(days=1)  # end 为排他上界 · 文件名用闭区间末日
    stem = f"pearnly_billing_{safe}_{start.strftime('%Y%m%d')}_{last.strftime('%Y%m%d')}"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{stem}.xlsx"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/api/credits/topup/{topup_id}/receipt.pdf")
async def topup_receipt(topup_id: int, request: Request, lang: str = "zh"):
    """单笔充值凭证 PDF。owner-only + tenant 归属双闸(防越权下载别家收据)。"""
    user = get_current_user_from_request(request)
    tid = str(user.get("tenant_id") or "")
    if not tid:
        raise HTTPException(status_code=400, detail="no_tenant")
    if not is_owner_role(request, user):
        raise HTTPException(status_code=403, detail="credits.owner_only")
    if lang not in ("zh", "en", "th", "ja"):
        lang = "zh"

    try:
        with db.get_cursor_rls(tenant_id=tid, user_id=None) as cur:
            cur.execute(
                """
                SELECT tr.id, tr.tenant_id, tr.amount_thb, tr.payer_name, tr.note,
                       tr.status, tr.created_at, tr.reviewed_at, t.name AS tenant_name
                FROM topup_requests tr
                LEFT JOIN tenants t ON t.id = tr.tenant_id
                WHERE tr.id = %s AND tr.tenant_id = %s::uuid
            """,
                (topup_id, tid),
            )
            row = cur.fetchone()
    except Exception as e:
        logger.error(f"topup_receipt query id={topup_id} tenant={tid}: {e}")
        raise HTTPException(status_code=500, detail="query_failed")
    if not row:
        raise HTTPException(status_code=404, detail="topup.not_found")

    receipt = {
        "id": row["id"],
        "amount_thb": float(row["amount_thb"] or 0),
        "payer_name": row["payer_name"] or "",
        "note": row["note"] or "",
        "status": row["status"] or "",
        "created_at": _fmt_dt(row["created_at"]),
        "reviewed_at": _fmt_dt(row["reviewed_at"]),
    }
    from services.billing.topup_receipt import build_topup_receipt_pdf

    try:
        data = build_topup_receipt_pdf(
            lang=lang, tenant_name=row["tenant_name"] or "—", receipt=receipt
        )
    except Exception as e:
        logger.error(f"topup_receipt build id={topup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="build_failed")

    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="pearnly_topup_{topup_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )
