"""Keep browser and document processing on the IAM-protected Worker service."""

import asyncio
import logging
import os
import time

import httpx
from starlette.responses import JSONResponse, StreamingResponse

HEAVY_PREFIXES = (
    "/api/uploads/",
    "/api/ocr/",
    "/api/v1/ocr/",
    "/api/erp/",
    "/api/dms/",
    "/api/recon/",
    "/api/vat_excel/",
    "/api/vat_report_checks/",
    "/api/workorder/",
    "/api/fileconv/",
    "/api/bank-recon/",
    "/api/line/dms-booking/",
    "/api/line/erp/draft/",
    "/api/cowork-line/intake/draft/",
)
HEAVY_EXACT = {
    "/api/purchase/intake",
    "/api/uploads",
    "/api/accounting/bank/import",
    "/api/workspace/clients/import/parse",
    "/api/email-ingest/trigger",
    "/api/email-ingest/test",
    "/api/line/webhook",
    "/api/line/erp/webhook",
    "/api/line/dms/webhook",
}
LIGHT_EXACT = {"/api/dms/session", "/api/line/dms-booking/config", "/api/line/dms-booking/auth"}


def needs_worker(path):
    if path in LIGHT_EXACT:
        return False
    return (
        path.startswith(HEAVY_PREFIXES)
        or path in HEAVY_EXACT
        or path.endswith(("/receipt-pdf", "/full-invoice-pdf", "/document.pdf"))
        or (
            path.startswith(("/api/sales/documents/", "/api/history/"))
            and path.endswith(("/pdf", ".png"))
        )
        or path.startswith("/api/purchase/proof-pdf/")
        or (path.startswith("/api/ai/steward/") and path.endswith("/attachments"))
    )


_HOP_HEADERS = {
    b"host",
    b"connection",
    b"transfer-encoding",
    b"content-length",
    b"x-serverless-authorization",
    b"x-forwarded-for",
    b"x-forwarded-host",
    b"x-forwarded-proto",
    b"forwarded",
}
logger = logging.getLogger(__name__)
_token_cache: tuple[float, str] = (0, "")


def identity_token(audience: str) -> str:
    global _token_cache
    if _token_cache[0] > time.monotonic():
        return _token_cache[1]
    from google.auth.transport.requests import Request
    from google.oauth2.id_token import fetch_id_token

    token = fetch_id_token(Request(), audience)
    _token_cache = (time.monotonic() + 2400, token)
    return token


class WorkerProxy:
    def __init__(self, app, role: str):
        self.app = app
        self.role = role

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        if path.startswith(("/internal/deploy", "/internal/install-playwright")):
            return await JSONResponse({"detail": "VM deployment is retired"}, 410)(
                scope, receive, send
            )
        if self.role == "web" and path.startswith("/internal/cloud-tasks"):
            return await JSONResponse({"detail": "Not found"}, 404)(scope, receive, send)
        if self.role != "web" or not needs_worker(path):
            return await self.app(scope, receive, send)
        origin = os.environ["PEARNLY_WORKER_URL"].rstrip("/")
        query = scope.get("query_string", b"").decode("ascii")
        url = origin + scope.get("raw_path", path.encode()).decode("ascii")
        if query:
            url += "?" + query
        try:
            token = await asyncio.to_thread(identity_token, origin)
        except Exception:
            logger.warning("Worker identity token unavailable")
            return await JSONResponse({"detail": "Worker unavailable"}, 503)(scope, receive, send)
        headers = [(k, v) for k, v in scope["headers"] if k.lower() not in _HOP_HEADERS]
        headers.append(
            (
                b"x-serverless-authorization",
                ("Bearer " + token).encode(),
            )
        )
        headers.append(
            (b"x-forwarded-host", os.environ.get("PEARNLY_PUBLIC_HOST", "pearnly.com").encode())
        )
        headers.append((b"x-forwarded-proto", b"https"))

        async def body():
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    raise asyncio.CancelledError()
                yield message.get("body", b"")
                if not message.get("more_body"):
                    break

        started = False

        async def forward_response(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(1800, connect=30), follow_redirects=False
        ) as client:
            request = client.build_request(scope["method"], url, headers=headers, content=body())
            try:
                response = await client.send(request, stream=True)
                outgoing = StreamingResponse(response.aiter_raw(), status_code=response.status_code)
                outgoing.raw_headers = [
                    (k, v) for k, v in response.headers.raw if k.lower() not in _HOP_HEADERS
                ]
                try:
                    await outgoing(scope, receive, forward_response)
                finally:
                    await response.aclose()
            except httpx.RequestError:
                if started:
                    raise
                await JSONResponse({"detail": "Worker unavailable"}, 503)(scope, receive, send)
