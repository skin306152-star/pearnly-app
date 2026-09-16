"""ERP-only native stock receipts/issues."""

from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Request, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import ValidationError
import json
from pydantic import BaseModel, Field
from routes.erp_intake_routes import _authorize
from services.erp import stock_documents

router = APIRouter(prefix="/api/erp/stock-documents")


class StockRequest(BaseModel):
    document_id: UUID
    workspace_client_id: int = Field(gt=0)
    direction: Literal["in", "out"]
    fields: dict


@router.post("")
def save_stock(req: StockRequest, request: Request):
    user = _authorize(request)
    return {
        "ok": True,
        "document": stock_documents.save(
            user,
            workspace_id=req.workspace_client_id,
            direction=req.direction,
            document_id=req.document_id,
            fields=req.fields,
        ),
    }


@router.get("")
def list_stock(request: Request, workspace_client_id: int, direction: Literal["in", "out"]):
    user = _authorize(request)
    return {
        "ok": True,
        "documents": stock_documents.list_documents(
            user, request, workspace_id=workspace_client_id, direction=direction
        ),
    }


@router.post("/with-attachment")
def save_stock_attachment(request: Request, payload: str = Form(...), file: UploadFile = File(...)):
    user = _authorize(request)
    try:
        req = StockRequest.model_validate(json.loads(payload))
    except (ValidationError, ValueError):
        raise HTTPException(422, "erp.invalid_document") from None
    content = file.file.read(10 * 1024 * 1024 + 1)
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "erp.attachment_too_large")
    if not (
        content.startswith(b"%PDF-")
        or content.startswith(b"\x89PNG\r\n\x1a\n")
        or content.startswith(b"\xff\xd8\xff")
    ):
        raise HTTPException(422, "erp.attachment_type")
    return {
        "ok": True,
        "document": stock_documents.save(
            user,
            workspace_id=req.workspace_client_id,
            direction=req.direction,
            document_id=req.document_id,
            fields=req.fields,
            attachment=(file.filename or "attachment", content),
        ),
    }


@router.get("/{document_id}/attachment")
def get_attachment(
    document_id: UUID, request: Request, workspace_client_id: int, direction: Literal["in", "out"]
):
    user = _authorize(request)
    content = stock_documents.attachment_bytes(
        user,
        request,
        workspace_id=workspace_client_id,
        direction=direction,
        document_id=document_id,
    )
    return Response(
        content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="attachment"'},
    )
