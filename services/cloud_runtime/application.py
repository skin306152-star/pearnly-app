"""Cloud Run application composition; the legacy VM entrypoint stays isolated."""

import os

from app import app
from services.cloud_runtime.downloads import LargeResponseStreaming
from services.cloud_runtime.proxy import WorkerProxy

role = os.environ["PEARNLY_RUNTIME_ROLE"]
if role == "worker":
    from services.cloud_tasks.routes import router

    app.include_router(router)
app.add_middleware(WorkerProxy, role=role)
app.add_middleware(LargeResponseStreaming)


@app.get("/internal/runtime-version")
async def runtime_version():
    return {
        "sha": os.environ.get("BUILD_SHA", ""),
        "revision": os.environ.get("K_REVISION", ""),
        "role": role,
    }
