"""Internal ERP records never leave Pearnly, regardless of the invoking portal."""

from fastapi import HTTPException

INTERNAL_SOURCES = frozenset({"erp_web", "line_erp"})


def require_external_history(history):
    if str((history or {}).get("source") or "") in INTERNAL_SOURCES:
        raise HTTPException(403, detail="erp.internal_only")


def require_external_user(user):
    if user.get("entry") == "erp":
        raise HTTPException(403, detail="erp.internal_only")
