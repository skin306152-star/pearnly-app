"""Invoice issuing is unavailable in the internal ERP portal."""

from fastapi import HTTPException, Request
from core.auth import get_current_user_from_request


def require_invoice_feature(request: Request):
    user = get_current_user_from_request(request)
    if user.get("entry") == "erp":
        raise HTTPException(403, detail="erp.feature_unavailable")
