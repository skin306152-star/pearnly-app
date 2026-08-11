"""Cited Q&A API: ask a question, fetch a past answer.

Retrieval is scoped to the caller's visibility (or one account set when given);
generation is grounded in the retrieved chunks. With no relevant chunk the
question is refused (no_answer) and not billed. Every answer is recorded so it
can be reviewed against its citations.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from core import db
from services.authz.deps import require_perm
from services.billing import account_status
from services.billing.charge import SATANG_PER_THB
from services.knowledge import contract
from routes.knowledge_common import authorize_write, resolve_caller
from services.knowledge import ask, dal, embedding, generation, search
from services.knowledge.schema import KnowledgeAnswer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-ask"])

_CREDIT_KIND = "rag_answer"
# 每答出一次扣 ฿0.50(50 satang · Zihao 2026-06-05 拍板 · 真实成本~฿0.07·≈OCR 毛利)。
_RAG_ANSWER_SATANG = 50


class AskRequest(BaseModel):
    question: str
    workspace_client_id: Optional[int] = None
    limit: int = search.DEFAULT_TOP_K


def _answer_out(answer: KnowledgeAnswer) -> dict[str, Any]:
    out = {
        "answer_id": answer.id,
        "question": answer.question,
        "answer": answer.answer,
        "no_answer": answer.no_answer,
        "citations": answer.citations,
        "model": answer.model,
    }
    if answer.no_answer:
        out["message_key"] = ask.NO_SOURCE_MESSAGE_KEY
    return out


@router.post("/ask")
def ask_question(request: Request, body: AskRequest) -> dict[str, Any]:
    require_perm(request, "kb.ask")
    identity, accessible = resolve_caller(request)
    question = body.question.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty question")

    # 余额前置检查:不足则在花 Gemini 钱之前拦下(豁免账号放行)。查不出余额同样不放行——
    # 钱闸 fail-closed(见 services/billing/account_status),但 503 与 402 分开:一个是我们
    # 的故障(稍后再试),一个是用户没钱(去充值)。
    try:
        _bill = db.get_billing_status_combined(identity.user_id, identity.tenant_id)
        if account_status.lookup_failed(_bill):
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": account_status.LOOKUP_ERROR},
            )
        if not _bill.get("is_exempt") and float(_bill.get("balance_thb", 0)) < (
            _RAG_ANSWER_SATANG / SATANG_PER_THB
        ):
            raise HTTPException(
                status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "insufficient_balance",
                    "balance": _bill.get("balance_thb", 0.0),
                    "estimated_cost": _RAG_ANSWER_SATANG / SATANG_PER_THB,
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[kb.ask] billing pre-check failed", exc_info=True)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": account_status.LOOKUP_ERROR}
        ) from exc

    scope = accessible
    if body.workspace_client_id is not None:
        authorize_write(accessible, body.workspace_client_id)
        scope = [body.workspace_client_id]

    limit = max(1, min(body.limit, 20))
    try:
        query_vector = embedding.embed_texts([question], is_query=True)[0]
        with db.get_cursor_rls(identity.tenant_id) as cur:
            hits = search.search_chunks(
                cur,
                tenant_id=identity.tenant_id,
                accessible_ids=scope,
                query_vector=query_vector,
                limit=limit,
            )
        result = ask.answer_question(question, hits)
    except (embedding.EmbeddingError, generation.GenerationError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "model unavailable") from exc

    with db.get_cursor_rls(identity.tenant_id, commit=True) as cur:
        answer = dal.create_answer(
            cur,
            tenant_id=identity.tenant_id,
            workspace_client_id=body.workspace_client_id,
            question=question,
            answer=result.answer,
            citations=result.citations,
            model=result.model,
            no_answer=result.no_answer,
            created_by=identity.user_id,
        )

    if not result.no_answer:
        contract.charge_credits(
            identity.tenant_id,
            _CREDIT_KIND,
            _RAG_ANSWER_SATANG,
            {"answer_id": answer.id, "user_id": identity.user_id},
        )
    return _answer_out(answer)


@router.get("/answers/{answer_id}")
def get_answer(request: Request, answer_id: int) -> dict[str, Any]:
    require_perm(request, "kb.doc.view")
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        answer = dal.get_answer(
            cur, tenant_id=identity.tenant_id, answer_id=answer_id, accessible_ids=accessible
        )
    if answer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "answer not found")
    return _answer_out(answer)


@router.get("/chunks/{chunk_id}")
def get_chunk(request: Request, chunk_id: int) -> dict[str, Any]:
    """出处原文:取被引用的 chunk + 相邻段落,供来源弹窗高亮命中片段。"""
    require_perm(request, "kb.doc.view")
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        ctx = search.get_chunk_context(
            cur, tenant_id=identity.tenant_id, accessible_ids=accessible, chunk_id=chunk_id
        )
    if ctx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chunk not found")
    return ctx
