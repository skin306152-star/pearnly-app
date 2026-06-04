"""Cited Q&A API: ask a question, fetch a past answer.

Retrieval is scoped to the caller's visibility (or one account set when given);
generation is grounded in the retrieved chunks. With no relevant chunk the
question is refused (no_answer) and not billed. Every answer is recorded so it
can be reviewed against its citations.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from core import db
from services.knowledge import contract
from routes.knowledge_common import authorize_write, resolve_caller
from services.knowledge import ask, dal, embedding, generation, search
from services.knowledge.schema import KnowledgeAnswer

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-ask"])

_CREDIT_KIND = "rag_answer"


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
    identity, accessible = resolve_caller(request)
    question = body.question.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty question")

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
        contract.charge_credits(identity.tenant_id, _CREDIT_KIND, 1, {"answer_id": answer.id})
    return _answer_out(answer)


@router.get("/answers/{answer_id}")
def get_answer(request: Request, answer_id: int) -> dict[str, Any]:
    identity, accessible = resolve_caller(request)
    with db.get_cursor_rls(identity.tenant_id) as cur:
        answer = dal.get_answer(
            cur, tenant_id=identity.tenant_id, answer_id=answer_id, accessible_ids=accessible
        )
    if answer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "answer not found")
    return _answer_out(answer)
