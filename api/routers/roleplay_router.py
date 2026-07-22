from fastapi import APIRouter, HTTPException

from api.schemas.roleplay_schemas import RoleplayRequest, RoleplayResponse
from api.services.roleplay_service import get_roleplay_service

roleplay_router = APIRouter(prefix="/roleplay", tags=["roleplay"])


@roleplay_router.post("/chat", response_model=RoleplayResponse)
def chat(request: RoleplayRequest) -> RoleplayResponse:
    try:
        return get_roleplay_service().generate_response(request)
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable is not set.",
        ) from None
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate roleplay response: {exc}",
        ) from exc
