"""Explicit-only, IAM-private protocol probe; never mounted in the application."""

import hashlib
import json
import os

from services.cloud_runtime.downloads import LargeResponseStreaming
from services.cloud_runtime.proxy import WorkerProxy

MAX_BODY_BYTES = 128 * 1024 * 1024


async def _json(send, status, payload):
    body = json.dumps(payload, separators=(",", ":")).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")],
        }
    )
    await send({"type": "http.response.body", "body": body})


class TransportProbe:
    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] != "http":
            return
        if scope["path"] == "/api/health" and scope["method"] == "GET":
            return await _json(send, 200, {"ok": True, "http_version": scope["http_version"]})
        if scope["path"] != "/api/ocr/transport-probe" or scope["method"] != "POST":
            return await _json(send, 404, {"detail": "Not found"})
        size, sha = 0, hashlib.sha256()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                raise RuntimeError("Unexpected probe request event")
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > MAX_BODY_BYTES:
                return await _json(send, 413, {"detail": "Probe body limit exceeded"})
            sha.update(chunk)
            if not message.get("more_body", False):
                break
        await _json(
            send,
            200,
            {"size": size, "sha256": sha.hexdigest(), "http_version": scope["http_version"]},
        )


def create_app():
    role = os.environ.get("PEARNLY_PROBE_ROLE", "worker")
    if role not in {"web", "worker"}:
        raise ValueError("PEARNLY_PROBE_ROLE must be web or worker")
    if role == "web" and not os.environ.get("PEARNLY_WORKER_URL"):
        raise ValueError("Web probe requires PEARNLY_WORKER_URL")
    return LargeResponseStreaming(WorkerProxy(TransportProbe(), role))


def main():
    from services.cloud_runtime.server import run

    run(create_app())


if __name__ == "__main__":
    main()
