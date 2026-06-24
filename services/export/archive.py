# -*- coding: utf-8 -*-
"""进项外流归档编排(Excel 同步 + Drive/Sheets 异步 handler · 契约 05 §2.2)。

Excel = 零授权同步(gather → rows → xlsx);Drive/Sheets = 异步 job(复用 recon_jobs 队列
worker · 进度态 · 失败可重试 · **幂等只补未成功**:export_archived_docs 台账已成功者跳过)。
套账隔离贯穿(每查 WHERE tenant_id + workspace_client_id);Google 凭据按套账取 → 不跨套账串。

gather/flatten 纯逻辑可单测;真 Drive/Sheets(DriveClient/SheetsClient)= 用户验收范围。
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from core import db
from services.export import drive as drive_svc
from services.export import entries as entries_svc
from services.export import excel as excel_svc
from services.export import google_oauth, google_store
from services.export import rows as rows_svc
from services.export import sheets as sheets_svc
from services.purchase import categories as cat_svc
from services.purchase import docs as docs_svc

logger = logging.getLogger("mr-pilot")


def flatten_categories(tree: list) -> dict:
    """两级科目树 → {id: name}(大类 + 子类全收)。纯函数。"""
    out = {}
    for top in tree or []:
        out[str(top.get("id"))] = top.get("name") or ""
        for child in top.get("children") or []:
            out[str(child.get("id"))] = child.get("name") or ""
    return out


def _subject_name(cur, *, tenant_id, workspace_client_id) -> str:
    cur.execute(
        "SELECT name FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    row = cur.fetchone()
    return (row and row.get("name")) or f"套账{workspace_client_id}"


def _posted_doc_ids(cur, *, tenant_id, workspace_client_id, date_from, date_to) -> list:
    """范围内已入账(posted)单据 id(草稿/作废不归 · 契约 04 §七B)。"""
    sql = (
        "SELECT id, doc_date FROM purchase_docs "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND status = 'posted'"
    )
    params = [tenant_id, workspace_client_id]
    if date_from:
        sql += " AND doc_date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND doc_date <= %s"
        params.append(date_to)
    sql += " ORDER BY doc_date"
    cur.execute(sql, tuple(params))
    return [str(r["id"]) for r in cur.fetchall()]


def gather_items(cur, *, tenant_id, workspace_client_id, doc_ids, evidence_mode="api") -> list:
    """doc_ids → 导出 item 列表 {doc,lines,supplier,posting,evidence_url,image_ref}。

    evidence_mode='api' → evidence_url 用 bill-image 鉴权端点(Excel 用);
    'drive' → 留空,归档后回填 Drive 夹链接。套账隔离由 get_doc/posting 查询自带。
    """
    items = []
    for did in doc_ids:
        full = docs_svc.get_doc(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        if not full:
            continue
        posting = entries_svc.get_posting_for_source(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            source_type="purchase",
            source_id=did,
        )
        image_ref = docs_svc.get_bill_image_ref(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, doc_id=did
        )
        ev_url = f"/api/purchase/docs/{did}/bill-image?idx=0" if evidence_mode == "api" else ""
        items.append(
            {
                "doc": full["doc"],
                "lines": full["lines"],
                "supplier": full.get("supplier"),
                "posting": posting,
                "evidence_url": ev_url,
                "image_ref": image_ref,
            }
        )
    return items


def _category_names(cur, *, tenant_id, workspace_client_id) -> dict:
    tree = cat_svc.get_tree(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    return flatten_categories(tree)


def excel_bytes(
    cur, *, tenant_id, workspace_client_id, date_from=None, date_to=None, lang="zh"
) -> bytes:
    """同步导出:范围内已入账明细 → xlsx 字节流(零授权兜底)· 列头/枚举值随 lang。"""
    doc_ids = _posted_doc_ids(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        date_from=date_from,
        date_to=date_to,
    )
    items = gather_items(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        doc_ids=doc_ids,
        evidence_mode="api",
    )
    cats = _category_names(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    rows = rows_svc.build_export_rows(items, category_names=cats, lang=lang)
    subject = _subject_name(cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id)
    return excel_svc.build_workbook(rows, sheet_title=subject or None, lang=lang)


def _read_image(image_ref: Optional[str]) -> Optional[bytes]:
    if not image_ref:
        return None
    try:
        from services.ocr import pdf_storage

        p = pdf_storage.get_pdf_abs_path(image_ref)
        return p.read_bytes() if p and p.exists() else None
    except Exception:  # noqa: BLE001
        return None


def _image_to_pdf(image_bytes: bytes) -> Optional[bytes]:
    """原图转单页 PDF(交会计)。失败返 None(不阻断归档)。"""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PDF")
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        return None


def run_export(job: dict) -> None:
    """异步归档 handler(recon_jobs worker 调度 · job_type='export')。

    凭据按套账取;逐单归档(已成功跳过=幂等);写 Sheet。进度/结果经 recon_jobs store
    回填(drive/sheet 链接进 progress)。无凭据/Google 故障 → 失败可重试,不污染主数据。
    """
    from services.recon_jobs import store as jobs

    jid = str(job.get("id"))
    tid = job.get("tenant_id")
    ws = job.get("workspace_client_id")
    params = job.get("params") or {}
    date_from, date_to = params.get("date_from"), params.get("date_to")
    lang = params.get("lang") or "zh"

    with db.get_cursor(commit=False) as cur:
        token = google_oauth.valid_access_token(cur, tenant_id=tid, workspace_client_id=ws)
        if not token:
            jobs.fail(jid, "google_not_connected")
            return
        doc_ids = _posted_doc_ids(
            cur, tenant_id=tid, workspace_client_id=ws, date_from=date_from, date_to=date_to
        )
        done_set = google_store.already_archived_ids(
            cur, tenant_id=tid, workspace_client_id=ws, doc_ids=doc_ids
        )
        subject = _subject_name(cur, tenant_id=tid, workspace_client_id=ws)
        cats = _category_names(cur, tenant_id=tid, workspace_client_id=ws)

    drive_client = drive_svc.DriveClient(token)
    pending = [d for d in doc_ids if d not in done_set]
    done_n, skip_n = 0, len(done_set)

    for did in pending:
        try:
            with db.get_cursor(commit=True) as cur:
                items = gather_items(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    doc_ids=[did],
                    evidence_mode="drive",
                )
                if not items:
                    skip_n += 1
                    continue
                it = items[0]
                doc = it["doc"]
                supplier = (it.get("supplier") or {}).get("name") or ""
                img = _read_image(it.get("image_ref"))
                res = drive_svc.archive_doc(
                    drive_client,
                    subject=subject,
                    doc_date=doc.get("doc_date"),
                    supplier=supplier,
                    doc_id=did,
                    image_bytes=img,
                    pdf_bytes=_image_to_pdf(img) if img else None,
                )
                google_store.mark_archived(
                    cur,
                    tenant_id=tid,
                    workspace_client_id=ws,
                    doc_id=did,
                    drive_folder_id=res.get("evidence_folder_id"),
                    drive_url=res.get("evidence_url"),
                )
            done_n += 1
            jobs.update_progress(jid, {"done_n": done_n, "skip_n": skip_n, "total": len(doc_ids)})
        except Exception as e:  # noqa: BLE001
            logger.warning("export archive doc %s failed: %s", did, e)

    links = _sync_sheet(tid, ws, token, subject, doc_ids, cats, date_from, date_to, lang)
    jobs.finish(
        jid,
        "export_archived_docs",
        ws,
        {
            "done_n": done_n,
            "skip_n": skip_n,
            "total": len(doc_ids),
            "sheet_url": links.get("sheet_url", ""),
            "drive_url": links.get("drive_url", ""),
        },
    )


def _sync_sheet(tid, ws, token, subject, doc_ids, cats, date_from, date_to, lang="zh") -> dict:
    """归档后写主体×年 Sheet(全量明细·证据列回链 Drive 夹)。失败返空不阻断。"""
    out = {"sheet_url": "", "drive_url": ""}
    try:
        with db.get_cursor(commit=False) as cur:
            items = gather_items(
                cur, tenant_id=tid, workspace_client_id=ws, doc_ids=doc_ids, evidence_mode="drive"
            )
            arch = {}
            cur.execute(
                "SELECT doc_id, drive_url FROM export_archived_docs "
                "WHERE tenant_id = %s AND workspace_client_id = %s",
                (tid, ws),
            )
            arch = {str(r["doc_id"]): r["drive_url"] for r in cur.fetchall()}
        for it in items:
            it["evidence_url"] = arch.get(str(it["doc"].get("id")), "")
        rows = rows_svc.build_export_rows(items, category_names=cats, lang=lang)
        if not rows:
            return out
        year = int(str(rows[0]["doc_date"])[:4])
        month = int(str(rows[0]["doc_date"])[5:7])
        sheets_client = sheets_svc.SheetsClient(token)
        from services.export import archive_tree

        folder = drive_svc.ensure_folder_path(
            drive_svc.DriveClient(token), archive_tree.subject_year_path(subject, year)
        )
        out["drive_url"] = drive_svc.folder_web_link(folder)
        ssid = sheets_svc.sync(
            sheets_client,
            folder_id=folder,
            subject=subject,
            year=year,
            month=month,
            rows=rows,
            lang=lang,
        )
        out["sheet_url"] = f"https://docs.google.com/spreadsheets/d/{ssid}"
    except Exception as e:  # noqa: BLE001
        logger.warning("export sheet sync failed: %s", e)
    return out


def register() -> None:
    """注册 export handler 到 recon_jobs worker(startup 调)。"""
    from services.recon_jobs import worker

    worker.register_handler("export", run_export)
