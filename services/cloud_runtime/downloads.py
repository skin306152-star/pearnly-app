"""Stream large responses through Cloud Run's HTTP/1 ingress."""

MAX_BUFFERED_RESPONSE = 32 * 1024 * 1024


class LargeResponseStreaming:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] == "HEAD":
            return await self.app(scope, receive, send)

        async def stream_response(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                if any(
                    name.lower() == b"content-length" and int(value) >= MAX_BUFFERED_RESPONSE
                    for name, value in headers
                ):
                    # FileResponse already emits chunks. Omitting the length lets
                    # Uvicorn use chunked encoding instead of Cloud Run buffering it.
                    message = {
                        **message,
                        "headers": [(k, v) for k, v in headers if k.lower() != b"content-length"],
                    }
            await send(message)

        await self.app(scope, receive, stream_response)
