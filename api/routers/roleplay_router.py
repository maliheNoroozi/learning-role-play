from fastapi import APIRouter

from api.schemas.roleplay_schemas import CreateRoleplayRequest, CreateRoleplayResponse
from api.services.roleplay.roleplay_service import get_roleplay_service

roleplay_router = APIRouter(prefix="/roleplays", tags=["roleplays"])


@roleplay_router.post("", response_model=CreateRoleplayResponse, status_code=201)
def create_roleplay(request: CreateRoleplayRequest) -> CreateRoleplayResponse:
    return get_roleplay_service().create_roleplay(request)
