"""Bound Academy write-request bodies before FastAPI parses or buffers them."""

from starlette.responses import JSONResponse

ACADEMY_MAX_REQUEST_BODY_BYTES = 64 * 1024
_ACADEMY_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class AcademyRequestBodyLimitMiddleware:
    def __init__(self, app, max_body_bytes: int = ACADEMY_MAX_REQUEST_BODY_BYTES):
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not self._is_academy_write(scope):
            await self.app(scope, receive, send)
            return

        content_length = self._content_length(scope)
        if content_length == -1:
            await self._respond(scope, receive, send, 400, "Invalid Content-Length")
            return
        if content_length is not None and content_length > self.max_body_bytes:
            await self._respond(scope, receive, send, 413, "Request body too large")
            return

        body = bytearray()
        disconnected = False
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                disconnected = True
                break
            if message["type"] != "http.request":
                await self._respond(scope, receive, send, 400, "Invalid request body")
                return

            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_body_bytes:
                await self._respond(scope, receive, send, 413, "Request body too large")
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        body_bytes = bytes(body)
        replayed_body = False
        disconnect_pending = disconnected

        async def replay_receive():
            nonlocal replayed_body, disconnect_pending
            if not replayed_body:
                replayed_body = True
                return {
                    "type": "http.request",
                    "body": body_bytes,
                    "more_body": disconnect_pending,
                }
            if disconnect_pending:
                disconnect_pending = False
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    @staticmethod
    def _is_academy_write(scope) -> bool:
        path = scope.get("path", "")
        return scope.get("method") in _ACADEMY_WRITE_METHODS and (
            path == "/api/v1/academy" or path.startswith("/api/v1/academy/")
        )

    @staticmethod
    def _content_length(scope) -> int | None:
        values = [
            value
            for name, value in scope.get("headers", ())
            if name.lower() == b"content-length"
        ]
        if not values:
            return None
        if len(values) != 1:
            return -1
        try:
            length = int(values[0])
        except (TypeError, ValueError):
            return -1
        return length if length >= 0 else -1

    @staticmethod
    async def _respond(scope, receive, send, status_code: int, detail: str) -> None:
        response = JSONResponse(status_code=status_code, content={"detail": detail})
        await response(scope, receive, send)