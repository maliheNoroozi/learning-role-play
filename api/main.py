from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.chat_router import chat_router
from api.routers.roleplay_router import roleplay_router

app = FastAPI(
    title="Learning Roleplay API",
    description="Conversation-style learning roleplay powered by ChatGPT.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roleplay_router)
app.include_router(chat_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
