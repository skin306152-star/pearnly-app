"""Large files keep their bytes, range semantics and cache validators when streamed."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock

from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles

from services.cloud_runtime.downloads import LargeResponseStreaming, MAX_BUFFERED_RESPONSE


class LargeDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def read_response(self, app, *, method="GET", headers=()):
        start, digest, size, chunks = {}, hashlib.sha256(), 0, 0

        async def send(message):
            nonlocal start, size, chunks
            if message["type"] == "http.response.start":
                start = message
            else:
                body = message.get("body", b"")
                digest.update(body)
                size += len(body)
                chunks += bool(body)

        scope = {
            "type": "http",
            "method": method,
            "path": "/installer.exe",
            "root_path": "",
            "headers": list(headers),
            "extensions": {},
        }
        await LargeResponseStreaming(app)(scope, AsyncMock(), send)
        return start, digest.hexdigest(), size, chunks

    async def test_real_static_file_is_chunked_with_unchanged_bytes_and_validators(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "installer.exe"
            block = b"installer-content" * 4096
            expected = hashlib.sha256()
            with path.open("wb") as stream:
                for _ in range(MAX_BUFFERED_RESPONSE // len(block) + 1):
                    stream.write(block)
                    expected.update(block)
            result, digest, size, chunks = await self.read_response(
                StaticFiles(directory=directory)
            )
            headers = dict(result["headers"])
            self.assertEqual(result["status"], 200)
            self.assertNotIn(b"content-length", headers)
            self.assertIn(b"etag", headers)
            self.assertIn(b"last-modified", headers)
            self.assertEqual((digest, size), (expected.hexdigest(), path.stat().st_size))
            self.assertGreater(chunks, 1)

            head, _, size, _ = await self.read_response(
                StaticFiles(directory=directory), method="HEAD"
            )
            self.assertEqual(int(dict(head["headers"])[b"content-length"]), path.stat().st_size)
            self.assertEqual(size, 0)

            partial, _, size, _ = await self.read_response(
                FileResponse(path), headers=[(b"range", b"bytes=10-19")]
            )
            self.assertEqual(partial["status"], 206)
            self.assertEqual(
                dict(partial["headers"])[b"content-range"],
                f"bytes 10-19/{path.stat().st_size}".encode(),
            )
            self.assertEqual((dict(partial["headers"])[b"content-length"], size), (b"10", 10))

    async def test_small_error_and_existing_stream_headers_are_preserved(self):
        for status in (200, 401, 403, 404):
            with self.subTest(status=status):
                response = Response(b"response", status_code=status, headers={"etag": "original"})
                start, _, size, _ = await self.read_response(response)
                self.assertEqual(start["status"], status)
                self.assertEqual(start["headers"], response.raw_headers)
                self.assertEqual(size, 8)

    async def test_non_http_protocol_passes_through(self):
        app, receive, send = AsyncMock(), AsyncMock(), AsyncMock()
        scope = {"type": "lifespan"}
        await LargeResponseStreaming(app)(scope, receive, send)
        app.assert_awaited_once_with(scope, receive, send)


if __name__ == "__main__":
    unittest.main()
