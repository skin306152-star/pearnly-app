"""Knowledge document API: upload, list, fetch, ingest status, delete.

Every handler resolves the caller's identity first, then constrains every query
to that tenant and the workspace clients the caller may see. Writes are
authorised before they touch the database: a member cannot attach a document to
an account set outside their visibility, and cannot delete one either. SQL lives
in services/knowledge/dal.py; this layer only does request shaping and
authorisation, mirroring the main project's thin *_routes.py convention.

Ingest runs inline here for the sandbox: upload parses, chunks, embeds and stores
the file so the document reaches READY (or FAILED) before the response returns. A
real deployment would hand this to a worker; the DAL and status vocabulary
already model that (queued job -> terminal job).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel

from core import db
from services.billing.charge import thb_to_satang
from services.knowledge import contract
from routes.knowledge_common import authorize_write, resolve_caller
from services.knowledge import dal, embedding, search
from services.knowledge.ocr_ingest import process_uploaded_any
from services.knowledge.processing import ProcessOutcome
from services.knowledge.schema import (
    DOC_FAILED,
    DOC_READY,
    ERROR_EMBEDDING,
    ERROR_PROCESSING,
    JOB_FAILED,
    JOB_SUCCESS,
    PROGRESS_COMPLETE,
    IngestJob,
    KnowledgeBase,
    KnowledgeDocument,
    SearchHit,
)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)


def _base_out(base: KnowledgeBase) -> dict[str, Any]:
    return {
        "id": base.id,
        "scope": base.scope,
        "workspace_client_id": base.workspace_client_id,
        "name": base.name,
        "status": base.status,
    }


def _doc_out(doc: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": doc.id,
        "knowledge_base_id": doc.knowledge_base_id,
        "workspace_client_id": doc.workspace_client_id,
        "filename": doc.filename,
        "source_type": doc.source_type,
        "mime_type": doc.mime_type,
        "status": doc.status,
        "error_code": doc.error_code,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


def _job_out(job: Optional[IngestJob]) -> Optional[dict[str, Any]]:
    if job is None:
        return None
    return {
        "id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "progress": job.progress,
        "error_code": job.error_code,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@router.get("/bases")
def list_bases(request: Request) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        bases = dal.list_bases(cur, tenant_id=identity.tenant_id, accessible_ids=accessible)
    return {"bases": [_base_out(b) for b in bases]}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    workspace_client_id: Optional[int] = Form(None),
    knowledge_base_id: Optional[int] = Form(None),
) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    authorize_write(accessible, workspace_client_id)

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")

    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    checksum = hashlib.sha256(data).hexdigest()
    storage_key = f"{identity.tenant_id}/{checksum}{suffix}"
    storage_path = contract.storage_put(storage_key, data)

    # OCR(图片/扫描件)联网较慢 · 放线程池避免阻塞 async 事件循环。
    # 入库失败必须落 failed 行 + 错误码,绝不让异常逃逸成 500(报告 P1a)。
    try:
        outcome = await asyncio.to_thread(process_uploaded_any, filename, data)
    except Exception:
        logger.exception("knowledge ingest failed: %s", filename)
        outcome = ProcessOutcome(status=DOC_FAILED, error_code=ERROR_PROCESSING)
    tenant_id = identity.tenant_id

    # Embed parsed chunks before opening the transaction — the network call stays
    # out of the DB transaction, and an embedding failure makes the document
    # FAILED rather than a silent, unsearchable READY.
    final_status, error_code = outcome.status, outcome.error_code
    vectors: list[list[float]] = []
    if outcome.status == DOC_READY:
        try:
            vectors = embedding.embed_texts([c.text for c in outcome.chunks], is_query=False)
        except embedding.EmbeddingError:
            final_status, error_code = DOC_FAILED, ERROR_EMBEDDING
    ready = final_status == DOC_READY

    with db.get_cursor_rls(tenant_id, commit=True) as cur:
        if knowledge_base_id is None:
            base = dal.get_or_create_default_base(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
            )
        else:
            base = dal.get_base(
                cur,
                tenant_id=tenant_id,
                base_id=knowledge_base_id,
                accessible_ids=accessible,
            )
            if base is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "knowledge base not found")

        doc = dal.create_document(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            knowledge_base_id=base.id,
            source_type=suffix.lstrip(".") or "unknown",
            filename=filename,
            mime_type=file.content_type,
            storage_path=storage_path,
            checksum=checksum,
            uploaded_by=identity.user_id,
        )
        job = dal.create_ingest_job(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            document_id=doc.id,
        )
        if ready:
            chunk_ids = search.store_chunks(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                document_id=doc.id,
                chunks=outcome.chunks,
            )
            search.store_embeddings(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                chunk_ids=chunk_ids,
                vectors=vectors,
                model=embedding.MODEL,
            )
        doc = dal.update_document_status(
            cur,
            tenant_id=tenant_id,
            document_id=doc.id,
            status=final_status,
            error_code=error_code,
        )
        job = dal.complete_ingest_job(
            cur,
            tenant_id=tenant_id,
            job_id=job.id,
            status=JOB_SUCCESS if ready else JOB_FAILED,
            progress=PROGRESS_COMPLETE if ready else 0,
            error_code=error_code,
        )

    # 入库计费(成功才扣):图片/扫描件按页(estimate_pdf),文本按字符(estimate_excel)。
    # 扣 tenant_credits.balance_thb · 统一走 contract.charge_credits(amount=satang)。
    if ready:
        try:
            if outcome.ocr_pages > 0:
                cost_thb = db.estimate_pdf_cost_thb(0, outcome.ocr_pages)
            else:
                cost_thb = db.estimate_excel_cost_thb(outcome.char_count)
            satang = thb_to_satang(cost_thb)
            if satang > 0:
                contract.charge_credits(
                    tenant_id,
                    "kb_ingest",
                    satang,
                    {
                        "document_id": doc.id,
                        "user_id": identity.user_id,
                        "ocr_pages": outcome.ocr_pages,
                        "chars": outcome.char_count,
                    },
                )
        except Exception:
            pass  # 计费失败不阻断已完成的入库

    return {
        "document": _doc_out(doc),
        "ingest_job": _job_out(job),
        "chunk_count": outcome.chunk_count if ready else 0,
    }


@router.get("/documents")
def list_documents(
    request: Request,
    knowledge_base_id: Optional[int] = None,
    include_deleted: bool = False,
) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        docs = dal.list_documents(
            cur,
            tenant_id=identity.tenant_id,
            accessible_ids=accessible,
            knowledge_base_id=knowledge_base_id,
            include_deleted=include_deleted,
        )
    return {"documents": [_doc_out(d) for d in docs]}


@router.get("/documents/{document_id}")
def get_document(request: Request, document_id: int) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        doc = dal.get_document(
            cur,
            tenant_id=identity.tenant_id,
            document_id=document_id,
            accessible_ids=accessible,
        )
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    return _doc_out(doc)


@router.get("/documents/{document_id}/ingest-status")
def get_ingest_status(request: Request, document_id: int) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        doc = dal.get_document(
            cur,
            tenant_id=identity.tenant_id,
            document_id=document_id,
            accessible_ids=accessible,
        )
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
        job = dal.get_latest_ingest_job(cur, tenant_id=identity.tenant_id, document_id=doc.id)
    return {
        "document_id": doc.id,
        "document_status": doc.status,
        "ingest_job": _job_out(job),
    }


@router.delete("/documents/{document_id}")
def delete_document(request: Request, document_id: int) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
        deleted = dal.soft_delete_document(
            cur,
            tenant_id=identity.tenant_id,
            document_id=document_id,
            accessible_ids=accessible,
        )
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    return {"status": "deleted", "document_id": document_id}


class SearchRequest(BaseModel):
    query: str
    limit: int = search.DEFAULT_TOP_K


def _hit_out(hit: SearchHit) -> dict[str, Any]:
    return {
        "chunk_id": hit.chunk_id,
        "document_id": hit.document_id,
        "filename": hit.filename,
        "text": hit.text,
        "score": round(hit.score, 4),
    }


@router.post("/search")
def search_documents(request: Request, body: SearchRequest) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    query = body.query.strip()
    if not query:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty query")
    try:
        query_vector = embedding.embed_texts([query], is_query=True)[0]
    except embedding.EmbeddingError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "embedding unavailable") from exc
    limit = max(1, min(body.limit, 50))
    with db.get_cursor_rls(identity.tenant_id) as cur:
        hits = search.search_chunks(
            cur,
            tenant_id=identity.tenant_id,
            accessible_ids=accessible,
            query_vector=query_vector,
            limit=limit,
        )
    return {"query": query, "hits": [_hit_out(h) for h in hits]}
