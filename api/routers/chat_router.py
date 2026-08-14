from fastapi import APIRouter, HTTPException

from api.schemas.roleplay_schemas import RoleplayChatRequest, RoleplayChatResponse
from api.services.cache.roleplay_cache import (
    RoleplayLockBusyError,
    RoleplayNotFoundError,
)
from api.services.roleplay_service import RoleplayEndedError, get_roleplay_service

chat_router = APIRouter(prefix="/roleplays", tags=["chat"])


@chat_router.post("/chat", response_model=RoleplayChatResponse)
def chat(request: RoleplayChatRequest) -> RoleplayChatResponse:
    try:
        return get_roleplay_service().generate_response(request)
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        ) from None
    except RoleplayNotFoundError:
        raise HTTPException(status_code=404, detail="Roleplay not found.") from None
    except RoleplayEndedError:
        raise HTTPException(
            status_code=409,
            detail="This roleplay has already ended.",
        ) from None
    except RoleplayLockBusyError:
        raise HTTPException(
            status_code=409,
            detail="Roleplay is busy. Try again.",
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate roleplay response: {exc}",
        ) from exc
