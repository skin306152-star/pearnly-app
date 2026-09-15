"""Local-only LINE transport simulator. Install on an isolated development app."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel


class Event(BaseModel):
    text: str = ""
    postback: str = ""


def install(app, *, line_user_id: str):
    """Use real webhook/session/draft APIs; substitute LINE transport and ID verification."""
    from routes import line_erp_routes
    from services.line_erp import webhook
    from services.line_platform import client

    import asyncio

    from scripts import erp_internal_line_fixture

    erp_internal_line_fixture.install()
    messages = []
    downloads = {}
    pending = []
    original_download = client.download_message_content
    client.download_message_content = lambda message_id, **kwargs: (
        downloads[message_id]
        if message_id in downloads
        else original_download(message_id, **kwargs)
    )
    original_spawn = webhook.cloud_dispatch.spawn

    def spawn(name, function, *args, **kwargs):
        if name == "line_erp.document":
            pending.append(asyncio.create_task(function(*args)))
        else:
            return original_spawn(name, function, *args, **kwargs)

    webhook.cloud_dispatch.spawn = spawn
    id_token = secrets.token_urlsafe(32)
    original_verify = line_erp_routes.verify_id_token
    line_erp_routes.verify_id_token = lambda token, env: (
        {"sub": line_user_id}
        if secrets.compare_digest(str(token), id_token)
        else original_verify(token, env)
    )

    def emit(_recipient, values, **_kwargs):
        messages.extend(values)
        return True

    client.reply_messages = emit
    client.push_messages = emit
    client.reply_text = lambda to, text, **kwargs: emit(
        to, [{"type": "text", "text": text}], **kwargs
    )
    client.push_text = client.reply_text
    client.start_loading = lambda *args, **kwargs: None
    router = APIRouter()

    @router.get("/__line_sim")
    def simulator():
        return HTMLResponse(
            Path(__file__).with_name("erp_internal_line_simulator.html").read_text()
        )

    @router.get("/__line_sim/sdk.js")
    def sdk():
        import json

        return Response(
            "window.liff={init:async()=>{},isLoggedIn:()=>true,getIDToken:()=>"
            + json.dumps(id_token)
            + ",closeWindow:()=>{}};",
            media_type="application/javascript",
        )

    @router.get("/liff/erp")
    def editor():
        source = Path("static/dist/erp-line-intake.html").read_text()
        return HTMLResponse(
            source.replace("https://static.line-scdn.net/liff/edge/2/sdk.js", "/__line_sim/sdk.js")
        )

    @router.post("/__line_sim/event")
    async def event(body: Event):
        messages.clear()
        envelope = {"source": {"userId": line_user_id}, "replyToken": "local-reply"}
        if body.postback:
            envelope.update(type="postback", postback={"data": body.postback})
        else:
            envelope.update(type="message", message={"type": "text", "text": body.text})
        await webhook.handle_event(envelope)
        return {"messages": list(messages)}

    @router.post("/__line_sim/upload")
    async def upload(file: UploadFile = File(...), fixture: bool = Form(False)):
        messages.clear()
        message_id = secrets.token_urlsafe(16)
        downloads[message_id] = await file.read()
        from services.line_erp import store

        binding = store.get_binding(line_user_id)
        session = store.get_session(binding["tenant_id"], line_user_id) if binding else {}
        context = erp_internal_line_fixture.fixture_direction.set(
            ((session or {}).get("payload") or {}).get("mode") if fixture else None
        )
        try:
            await webhook.handle_event(
                {
                    "type": "message",
                    "source": {"userId": line_user_id},
                    "replyToken": "local-reply",
                    "message": {
                        "id": message_id,
                        "type": "file",
                        "fileName": file.filename,
                    },
                }
            )
            if pending:
                await asyncio.gather(*pending)
                pending.clear()
            return {"messages": list(messages)}
        finally:
            erp_internal_line_fixture.fixture_direction.reset(context)
            downloads.pop(message_id, None)

    # Prepend local routes so only this development process substitutes the LIFF page.
    app.router.routes[0:0] = router.routes
