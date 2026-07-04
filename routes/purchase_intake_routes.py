# -*- coding: utf-8 -*-
"""商户采购智能入口路由 · /intake 分流 + /expense 文字记费用(docs/purchasing/02 §0/§4)。

/intake:图 → OCR(复用 ocr/entrypoints·计费同网页/LINE)→ 判方向(有 VAT→进项·否则费用)→ 建
草稿落列表(待归类已下线·高置信齐全且 auto_book 开则直接过账);文字 → 费用归类草稿。OCR 在游标
外跑(不长持事务)。/expense:文字一句话 → 直接记一笔 posted 费用(LINE bot 复用此入口·替代收据
S2d 生成)。成员可用;套账隔离 + expense 门控。
"""

from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel

from core import db
from core.pos_api import PosError, ok
from routes.purchase_common import auth_member, gate, resolve_ws, uid as _uid
from services.ocr import entrypoints as ocr
from services.purchase import categories as cat_svc
from services.purchase import docs as docs_svc
from services.purchase import intake as intake_svc
from services.purchase import posting as posting_svc
from services.purchase import settings as settings_svc

router = APIRouter(prefix="/api/purchase", tags=["purchase-intake"])


def _run_ocr(user_fresh: dict, file_bytes: bytes, filename: str) -> tuple[dict, str, dict]:
    """计费 → OCR → (fields, confidence_band, field_confidence)。计费不过/无票 → PosError。"""
    if not ocr.is_supported_ocr_file(filename):
        raise PosError("purchase.line_invalid", 422, detail="unsupported_file")
    api_key = (
        user_fresh.get("gemini_api_key") or user_fresh.get("custom_gemini_api_key") or ""
    ).strip() or None
    if not api_key and not os.environ.get("GEMINI_API_KEY", "").strip():
        raise PosError("purchase.unexpected", 402, detail="no_api_key")
    quote = ocr.billing_quote(user_fresh, file_bytes, filename, max_pages=50)
    if not quote.get("allowed"):
        raise PosError("purchase.unexpected", 402, detail=quote.get("error_code") or "ocr_blocked")
    try:
        pipe_res = ocr.run_pipeline_for_file(
            file_bytes,
            filename,
            api_key=api_key,
            max_pages=50,
            **ocr.policy_context_from_billing(quote),
        )
    except Exception as e:
        raise PosError("purchase.unexpected", 422, detail="ocr_failed") from e
    pages = getattr(pipe_res, "pages", None) or []
    if not pages:
        raise PosError("purchase.unexpected", 422, detail="ocr_empty")
    _charge(user_fresh, quote)
    page = pages[0]
    return (
        intake_svc.fields_from_invoice(page.invoice),
        getattr(page, "confidence_band", ""),
        dict(getattr(page, "field_confidence", {}) or {}),
    )


def _charge(user_fresh: dict, quote: dict) -> None:
    """成功识别扣费(同网页/LINE 计费 · 合成引用号,不写识别中心 history)。"""
    try:
        ocr.charge_successful_ocr(
            user_fresh, quote, f"purchase_intake_{uuid.uuid4().hex[:12]}", "采购智能入口 OCR"
        )
    except Exception:
        pass


@router.post("/intake")
async def api_intake(
    request: Request,
    image: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    workspace_client_id: Optional[int] = Form(None),
):
    user, tid = auth_member(request, "intake.upload")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, workspace_client_id)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        cats = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)

    if image is not None:
        file_bytes = await image.read()
        if not file_bytes:
            raise PosError("purchase.line_invalid", 422, detail="empty_image")
        user_fresh = db.find_user_by_id(_uid(user)) or user
        fields, confidence, field_conf = _run_ocr(
            user_fresh, file_bytes, image.filename or "upload.jpg"
        )
        # 票图落盘留底 → ref 进草稿,确认入账时挂成 bill 附件(C · 表单/详情可回看原票)。
        from services.ocr import pdf_storage

        _suffix = os.path.splitext(image.filename or "")[1].lower() or ".jpg"
        bill_ref, _ = pdf_storage.save_bytes(_uid(user), file_bytes, _suffix)
        with db.get_cursor_rls(tid, commit=True) as cur:
            data = intake_svc.resolve_image_intake(
                cur,
                tenant_id=tid,
                workspace_client_id=ws,
                fields=fields,
                confidence=confidence,
                field_confidence=field_conf,
                settings=cfg,
                source="photo",
                image_url=bill_ref,
                created_by=_uid(user),
            )
        return ok(data)

    if text and text.strip():
        parsed = intake_svc.classify_expense_text(text, cats)
        draft = {
            "doc_kind": "expense",
            "supplier": None,
            "lines": [intake_svc.expense_line(parsed)],
            "category_id": parsed["category_id"],
        }
        return ok(
            {
                "kind": "expense",
                "confidence": "auto",
                "route": "expense",
                "draft": draft,
                "dedupe_hit": False,
            }
        )

    raise PosError("purchase.line_invalid", 422, detail="no_input")


class ExpenseIn(BaseModel):
    workspace_client_id: Optional[int] = None
    text: str = ""
    category_id: Optional[str] = None


@router.post("/expense")
async def api_quick_expense(req: ExpenseIn, request: Request):
    """文字一句话 → 直接记一笔 posted 费用(LINE bot 复用)。替代收据由 S2d 凭据接口补。"""
    user, tid = auth_member(request, "purchase.doc.create")
    if not req.text.strip():
        raise PosError("purchase.line_invalid", 422, detail="empty_text")
    with db.get_cursor_rls(tid, commit=True) as cur:
        gate(cur, tid)
        ws = resolve_ws(cur, request, tid, req.workspace_client_id)
        cfg = settings_svc.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
        cats = cat_svc.get_tree(cur, tenant_id=tid, workspace_client_id=ws)
        parsed = intake_svc.classify_expense_text(req.text, cats)
        category_id = req.category_id or parsed["category_id"]
        data = {
            "doc_kind": "expense",
            "source": "line",
            "category_id": category_id,
            "lines": [intake_svc.expense_line(parsed)],
        }
        created = docs_svc.create_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            created_by=_uid(user),
            data=data,
            settings=cfg,
            status="draft",
        )
        posted = posting_svc.post_doc(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            doc_id=created["doc"]["id"],
            auto_stock_in=False,
            created_by=_uid(user),
        )
        return ok({"doc": posted["doc"], "category": {"id": category_id}})
