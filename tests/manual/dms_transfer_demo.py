"""Loopback simulation: real booking handlers; fake storage, bank masters and LINE transport."""

import asyncio
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.line_dms import binding_guard
from services.line_platform.channels import DMS_CHANNELS
from tests.unit.test_line_dms_booking_qa import Env, _qa, _seed, _TID, _LUID, qa

BANKS = [
    ["1", "SCB", "SCB", "ระยอง", "1234567890"],
    ["2", "BBL", "BBL", "00", "00"],
    ["3", "TTB", "TTB", "ระยอง", ""],
]
SESSIONS = {}


async def interact(channel, action, value="", session=None, banks=BANKS):
    with Env(company_banks=banks, source_banks=[]) as env:
        binding = {"channel_key": channel, "tenant_id": _TID, "user_id": "simulated"}
        with (
            binding_guard.scope(binding),
            mock.patch.object(binding_guard, "current", return_value=True),
        ):
            if action == "reset" or session is None:
                _seed(env, _qa("pay_channel"))
                await qa.handle_postback(_TID, _LUID, "qa:pay:transfer", {}, "simulated")
            else:
                env.store.data[(_TID, _LUID)] = session
                if action == "text":
                    await qa.handle_text(_TID, _LUID, value, "simulated")
                elif action == "postback":
                    await qa.handle_postback(_TID, _LUID, value, {}, "simulated")
                elif action == "image":
                    await qa.handle_image(_TID, _LUID, "simulated-slip", "simulated")
                else:
                    raise ValueError("Unknown simulation action")
        messages = []
        for call in env.reply.call_args_list:
            assert call.kwargs["channel"] == channel
            messages.extend(call.args[1])
        return {"session": env.session(), "messages": messages, "step": env.qa_payload()["step"]}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = Path(__file__).with_suffix(".html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            channel = data["channel"]
            if channel not in DMS_CHANNELS:
                raise ValueError("Unknown OA")
            result = asyncio.run(
                interact(channel, data["action"], data.get("value", ""), SESSIONS.get(channel))
            )
            SESSIONS[channel] = result.pop("session")
            body = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
        except (ValueError, KeyError) as exc:
            body = json.dumps({"error": str(exc)}).encode()
            self.send_response(400)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 18109), Handler).serve_forever()
