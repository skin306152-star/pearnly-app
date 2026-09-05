"""The internal proxy must preserve user auth and streamed upload/download bytes."""

import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from services.cloud_runtime.proxy import WorkerProxy


class ProxyStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_proxy_preserves_auth_body_query_and_response_cookies(self):
        observed = {}

        async def transport(request):
            observed["url"] = str(request.url)
            observed["auth"] = request.headers["authorization"]
            observed["iam"] = request.headers["x-serverless-authorization"]
            observed["host"] = request.headers.get_list("x-forwarded-host")
            observed["proto"] = request.headers.get_list("x-forwarded-proto")
            observed["body"] = await request.aread()
            return httpx.Response(
                201,
                headers=[("set-cookie", "first=1"), ("set-cookie", "second=2")],
                stream=httpx.ByteStream(b"download-content"),
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        scope = {
            "type": "http",
            "asgi": {"spec_version": "2.4"},
            "method": "POST",
            "path": "/api/ocr/recognize",
            "raw_path": b"/api/ocr/recognize",
            "query_string": b"lang=th",
            "headers": [
                (b"host", b"evil.example"),
                (b"x-forwarded-host", b"evil.example"),
                (b"x-forwarded-host", b"second-evil.example"),
                (b"x-forwarded-proto", b"http"),
                (b"authorization", b"Bearer user-session"),
                (b"x-serverless-authorization", b"forged-client-token"),
            ],
        }
        receive = AsyncMock(
            side_effect=[
                {"type": "http.request", "body": b"part-one", "more_body": True},
                {"type": "http.request", "body": b"-part-two", "more_body": False},
            ]
        )
        send = AsyncMock()
        with (
            patch.dict(os.environ, {"PEARNLY_WORKER_URL": "https://worker.example"}),
            patch("services.cloud_runtime.proxy.identity_token", return_value="real-iam-token"),
            patch("services.cloud_runtime.proxy.httpx.AsyncClient", return_value=client),
        ):
            await WorkerProxy(AsyncMock(), "web")(scope, receive, send)
        self.assertEqual(observed["url"], "https://worker.example/api/ocr/recognize?lang=th")
        self.assertEqual(observed["auth"], "Bearer user-session")
        self.assertEqual(observed["iam"], "Bearer real-iam-token")
        self.assertEqual(observed["host"], ["pearnly.com"])
        self.assertEqual(observed["proto"], ["https"])
        self.assertEqual(observed["body"], b"part-one-part-two")
        messages = [call.args[0] for call in send.call_args_list]
        self.assertEqual(messages[0]["status"], 201)
        cookies = [value for key, value in messages[0]["headers"] if key == b"set-cookie"]
        self.assertEqual(cookies, [b"first=1", b"second=2"])
        self.assertEqual(b"".join(m.get("body", b"") for m in messages[1:]), b"download-content")

    async def test_token_failure_returns_503_without_contacting_worker(self):
        scope = {"type": "http", "path": "/api/uploads/image", "headers": []}
        send = AsyncMock()
        with (
            patch.dict(os.environ, {"PEARNLY_WORKER_URL": "https://worker.example"}),
            patch("services.cloud_runtime.proxy.identity_token", side_effect=RuntimeError("token")),
            patch("services.cloud_runtime.proxy.httpx.AsyncClient") as client,
        ):
            await WorkerProxy(AsyncMock(), "web")(scope, AsyncMock(), send)
        client.assert_not_called()
        self.assertEqual(send.call_args_list[0].args[0]["status"], 503)

    async def test_worker_error_before_headers_returns_503(self):
        async def transport(request):
            raise httpx.ConnectError("unreachable", request=request)

        messages = await self._run_failure(transport, expected_error=False)
        self.assertEqual(
            [m["status"] for m in messages if m["type"] == "http.response.start"], [503]
        )

    async def test_stream_failure_never_sends_second_response_start(self):
        class BrokenStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"partial"
                raise httpx.ReadError("stream interrupted")

        async def transport(request):
            return httpx.Response(200, stream=BrokenStream())

        messages = await self._run_failure(transport, expected_error=True)
        self.assertEqual(
            [m["status"] for m in messages if m["type"] == "http.response.start"], [200]
        )
        self.assertIn(b"partial", [m.get("body") for m in messages])

    async def _run_failure(self, transport, *, expected_error):
        client = httpx.AsyncClient(transport=httpx.MockTransport(transport))
        scope = {
            "type": "http",
            "asgi": {"spec_version": "2.4"},
            "method": "POST",
            "path": "/api/uploads/image",
            "headers": [],
        }
        receive = AsyncMock(return_value={"type": "http.request", "body": b"", "more_body": False})
        send = AsyncMock()
        with (
            patch.dict(os.environ, {"PEARNLY_WORKER_URL": "https://worker.example"}),
            patch("services.cloud_runtime.proxy.identity_token", return_value="token"),
            patch("services.cloud_runtime.proxy.httpx.AsyncClient", return_value=client),
        ):
            if expected_error:
                with self.assertRaises(httpx.ReadError):
                    await WorkerProxy(AsyncMock(), "web")(scope, receive, send)
            else:
                await WorkerProxy(AsyncMock(), "web")(scope, receive, send)
        return [call.args[0] for call in send.call_args_list]


if __name__ == "__main__":
    unittest.main()
