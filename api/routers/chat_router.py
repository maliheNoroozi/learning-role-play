import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas.roleplay_schemas import RoleplayChatRequest
from api.services.roleplay.roleplay_cache import (
    RoleplayLockBusyError,
    RoleplayNotFoundError,
)
from api.services.roleplay.roleplay_service import (
    RoleplayEndedError,
    get_roleplay_service,
)

chat_router = APIRouter(prefix="/roleplays", tags=["chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _http_error_detail(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, KeyError) and str(exc) == "'OPENAI_API_KEY'":
        return 500, "OPENAI_API_KEY environment variable is not set."
    if isinstance(exc, RoleplayNotFoundError):
        return 404, "Roleplay not found."
    if isinstance(exc, RoleplayEndedError):
        return 409, "This roleplay has already ended."
    if isinstance(exc, RoleplayLockBusyError):
        return 409, "Roleplay is busy. Try again."
    return 502, f"Failed to generate roleplay response: {exc}"


@chat_router.post("/chat/stream")
def chat_stream(request: RoleplayChatRequest) -> StreamingResponse:
    """Stream the AI reply as SSE (`token` events, then a final `done` event)."""
    try:
        service = get_roleplay_service()
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        ) from None

    def event_stream() -> Iterator[str]:
        try:
            for event, payload in service.generate_response_stream(request):
                yield _sse(event, payload)
        except Exception as exc:
            _, detail = _http_error_detail(exc)
            yield _sse("error", {"detail": detail})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
