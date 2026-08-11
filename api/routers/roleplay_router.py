from fastapi import APIRouter, HTTPException

from api.schemas.roleplay_schemas import (
    CreateRoleplayRequest,
    CreateRoleplayResponse,
    RoleplayChatRequest,
    RoleplayChatResponse,
)
from api.services.cache.roleplay_cache import (
    RoleplayLockBusyError,
    RoleplayNotFoundError,
)
from api.services.roleplay_service import (
    RoleplayEndedError,
    get_roleplay_service,
)

roleplay_router = APIRouter(prefix="/roleplay", tags=["roleplay"])


@roleplay_router.post("", response_model=CreateRoleplayResponse)
def create_roleplay(request: CreateRoleplayRequest) -> CreateRoleplayResponse:
    return get_roleplay_service().create_roleplay(request)

@roleplay_router.post("/chat", response_model=RoleplayChatResponse)
def chat(request: RoleplayChatRequest) -> RoleplayChatResponse:
    try:
        return get_roleplay_service().generate_response(request)
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        ) from None
    except RoleplayNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Roleplay session not found: {request.roleplay_id}",
        ) from None
    except RoleplayEndedError:
        raise HTTPException(
            status_code=409,
            detail=f"Roleplay session has already ended: {request.roleplay_id}",
        ) from None
    except RoleplayLockBusyError:
        raise HTTPException(
            status_code=429,
            detail="Roleplay session is busy. Please retry.",
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate roleplay response: {exc}",
        ) from exc
