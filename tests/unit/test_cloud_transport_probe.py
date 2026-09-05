"""Protocol probe boundaries without Hypercorn, credentials or business effects."""

import hashlib
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import AsyncMock, patch

from services.cloud_runtime import transport_probe as probe


class TransportProbeTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, chunks, *, path="/api/ocr/transport-probe", method="POST"):
        scope = {
            "type": "http",
            "http_version": "2",
            "path": path,
            "method": method,
            "headers": [(b"authorization", b"Bearer never-echo-this")],
        }
        events = [
            {"type": "http.request", "body": chunk, "more_body": index < len(chunks) - 1}
            for index, chunk in enumerate(chunks)
        ]
        send = AsyncMock()
        with patch.dict(os.environ, PEARNLY_PROBE_ROLE="worker"):
            await probe.create_app()(scope, AsyncMock(side_effect=events), send)
        messages = [call.args[0] for call in send.call_args_list]
        return messages[0]["status"], json.loads(messages[-1]["body"])

    async def test_streamed_bytes_hash_and_protocol_without_echoing_headers(self):
        status, payload = await self.request([b"first", b"\x00second", b""])
        self.assertEqual(status, 200)
        self.assertEqual(
            payload,
            {
                "size": 12,
                "sha256": hashlib.sha256(b"first\x00second").hexdigest(),
                "http_version": "2",
            },
        )
        self.assertNotIn("never-echo-this", json.dumps(payload))

    async def test_body_limit_uses_received_bytes_without_trusting_content_length(self):
        with patch.object(probe, "MAX_BODY_BYTES", 8):
            status, _ = await self.request([b"1234", b"5678"])
            self.assertEqual(status, 200)
            status, payload = await self.request([b"1234", b"56789"])
            self.assertEqual(status, 413)
            self.assertEqual(set(payload), {"detail"})

    async def test_health_never_reads_body(self):
        status, payload = await self.request([], path="/api/health", method="GET")
        self.assertEqual((status, payload), (200, {"ok": True, "http_version": "2"}))

    async def test_unknown_route_or_wrong_method_is_not_a_generic_upload_endpoint(self):
        for path, method in (("/api/other", "POST"), ("/api/ocr/transport-probe", "GET")):
            with self.subTest(path=path, method=method):
                status, _ = await self.request([], path=path, method=method)
                self.assertEqual(status, 404)

    async def test_disconnect_does_not_claim_a_complete_hash(self):
        send = AsyncMock()
        await probe.TransportProbe()(
            {"type": "http", "path": "/api/ocr/transport-probe", "method": "POST"},
            AsyncMock(return_value={"type": "http.disconnect"}),
            send,
        )
        send.assert_not_called()

    async def test_lifespan_completes_without_starting_business_services(self):
        send = AsyncMock()
        await probe.TransportProbe()(
            {"type": "lifespan"},
            AsyncMock(
                side_effect=[
                    {"type": "lifespan.startup"},
                    {"type": "lifespan.shutdown"},
                ]
            ),
            send,
        )
        self.assertEqual(
            [call.args[0] for call in send.call_args_list],
            [
                {"type": "lifespan.startup.complete"},
                {"type": "lifespan.shutdown.complete"},
            ],
        )

    def test_web_requires_target_and_unknown_role_is_rejected(self):
        with patch.dict(os.environ, {"PEARNLY_PROBE_ROLE": "web"}, clear=True):
            with self.assertRaisesRegex(ValueError, "PEARNLY_WORKER_URL"):
                probe.create_app()
        with patch.dict(os.environ, PEARNLY_PROBE_ROLE="schema"):
            with self.assertRaises(ValueError):
                probe.create_app()

    def test_probe_import_does_not_import_server_database_or_production_app(self):
        source = """
import sys
import services.cloud_runtime.transport_probe
for name in ('hypercorn', 'core.db', 'app', 'services.cloud_runtime.application'):
    assert name not in sys.modules, name
"""
        result = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
