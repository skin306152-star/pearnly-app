"""Serve HTTP/2 cleartext behind Cloud Run's TLS-terminating proxy."""

import asyncio
import os


def run(app):
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', '8080'))}"]
    config.accesslog = "-"
    config.graceful_timeout = 8
    config.shutdown_timeout = 2
    config.startup_timeout = 240
    # Preserve the previous Uvicorn entrypoint's proxy/IP handling. Cloudflare
    # and WorkerProxy sanitize forwarded headers before the trusted cloud hop.
    asyncio.run(serve(ProxyHeadersMiddleware(app, trusted_hosts="*"), config, mode="asgi"))
