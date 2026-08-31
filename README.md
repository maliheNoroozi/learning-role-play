# Learning Roleplay

Practice real conversations with an AI character. Set a scenario, your role, and goals — then chat until you achieve them or the session ends.

## Stack

- **Backend:** FastAPI, LangChain / LangGraph, OpenAI (`gpt-4o-mini`), Redis, MongoDB
- **Frontend:** Next.js (App Router), React, Tailwind CSS, Zod
- **Tooling:** `uv` (Python), `pnpm` (frontend), Docker Compose (Redis + MongoDB)

## How it works

1. The learner submits roleplay setup (scenario, roles, goals, AI character).
2. `POST /roleplays` creates a session, persists it (MongoDB + Redis), and returns a `roleplay_id`.
3. Each chat turn streams `roleplay_id` + `learner_message` to `POST /roleplays/chat/stream` (SSE).
4. A LangGraph pipeline evaluates goals and ending conditions in parallel, then streams either a normal in-character reply or a closing message (`token` events, then a final `done` event).
5. Session state (history, irrelevant-message count, ended flag) is written through MongoDB and refreshed in Redis under a per-session lock.

**Session storage:** Redis is the hot cache and lock layer; MongoDB is the durable store (cache-aside reads, write-through saves).

**Ending conditions:** `goals_achieved`, `profanity`, `conversation_exhausted`, `irrelevant` (after repeated off-topic messages), or `none`.

## Project structure

```
.
├── api/
│   ├── main.py                      # FastAPI app, CORS, /health
│   ├── routers/
│   │   ├── roleplay_router.py       # POST /roleplays
│   │   └── chat_router.py           # POST /roleplays/chat/stream (SSE)
│   ├── schemas/
│   │   └── roleplay_schemas.py      # Request / response / session models
│   └── services/
│       ├── config.py                # Model + roleplay constants
│       ├── prompts.py
│       ├── cache/                   # Redis client + config
│       ├── database/                # MongoDB client + config
│       └── roleplay/
│           ├── roleplay_service.py  # LangGraph roleplay + evaluation
│           ├── roleplay_store.py    # Cache-aside + write-through facade
│           ├── roleplay_cache.py    # Redis session + locks
│           └── roleplay_repository.py  # MongoDB persistence
├── frontend/
│   ├── app/                         # App Router pages + server actions
│   ├── components/                  # Chat, Roleplay form, UI primitives
│   ├── hooks/                       # useChat, useSSE, form defaults
│   └── lib/                         # API client, schemas, OpenAPI types
├── notebook/                        # Research / experiments
├── docker-compose.yml               # Redis + MongoDB
├── Makefile
└── pyproject.toml
```

## Prerequisites

- Python 3.13+ and [uv](https://docs.astral.sh/uv/)
- Node.js and [pnpm](https://pnpm.io/)
- Docker (for Redis and MongoDB)
- An OpenAI API key

## Setup

**Backend env** — copy and fill `.env` at the repo root:

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=your-key-here

# Optional LangSmith tracing
LANGSMITH_TRACING=
LANGSMITH_ENDPOINT=
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# Optional; defaults to localhost Redis if unset
REDIS_URL=
REDIS_DB=

# Optional; defaults to localhost MongoDB / roleplay DB if unset
MONGODB_HOST=
MONGODB_PORT=
MONGODB_DB=
MONGODB_USER=
MONGODB_PASSWORD=
```

**Frontend env** — in `frontend/`:

```bash
cp env.example .env.local
```

```env
NEXT_PUBLIC_API_URL=http://localhost:9000
```

Install dependencies (or use `make install`):

```bash
uv sync
cd frontend && pnpm install
```

## Run

Start infrastructure (Redis + MongoDB):

```bash
make docker-up
```

Start the API (port **9000**):

```bash
make backend
```

Or manually:

```bash
docker compose up -d --wait
set -a && source .env && set +a
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 9000
```

Start the frontend (port **3000**):

```bash
make frontend
```

- App: [http://localhost:3000](http://localhost:3000)
- API docs: [http://127.0.0.1:9000/docs](http://127.0.0.1:9000/docs)
- Health: `GET /health` → `{"status":"ok"}`

Stop infrastructure:

```bash
make docker-down
```

## API

### Create a roleplay

`POST /roleplays` → `201`

```bash
curl -X POST http://127.0.0.1:9000/roleplays \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "You are at a car dealership negotiating the price of a used sedan.",
    "learner_goals": ["Negotiate a fair price", "Ask about warranty options"],
    "learner_role": "A first-time car buyer",
    "ai_character_name": "Alex",
    "ai_character_role": "Experienced car salesperson",
    "ai_character_personality": "Friendly but persuasive, focused on closing the deal."
  }'
```

Response:

```json
{ "roleplay_id": "<uuid>" }
```

### Stream a chat message

`POST /roleplays/chat/stream` → Server-Sent Events

```bash
curl -N -X POST http://127.0.0.1:9000/roleplays/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "roleplay_id": "<uuid>",
    "learner_message": "Hi, I am interested in this car. What is your best price?"
  }'
```

SSE events:

| Event | Payload |
|-------|---------|
| `token` | `{ "text": "<chunk>" }` — streamed AI text |
| `done` | Full turn result: `ai_response`, `should_end`, `ending_condition`, optional `ending_rationale` |
| `error` | `{ "detail": "..." }` — failure during the stream |

| Status / case | Meaning |
|---------------|---------|
| 404 | Unknown `roleplay_id` |
| 409 | Session already ended, or lock busy |
| 500 | Missing `OPENAI_API_KEY` |
| 502 / `error` event | Upstream / generation failure |

## Frontend flow

1. Home (`/`) — set up scenario, goals, and AI character.
2. On create, the app calls `POST /roleplays` and navigates to `/roleplays/[id]/chat`.
3. Chat streams each learner message to `POST /roleplays/chat/stream`, renders tokens as they arrive, and ends the session when `should_end` is true.

## Useful Make targets

| Target | Description |
|--------|-------------|
| `make install` | `uv sync` + frontend `pnpm install` |
| `make docker-up` | Start Redis + MongoDB |
| `make docker-down` | Stop Docker Compose services |
| `make backend` | Start API on port 9000 (loads `.env`) |
| `make frontend` | Start Next.js dev server |
| `make generate_openapi` | Regenerate `frontend/lib/openapi.generated.ts` from the FastAPI schema |
| `make lint` | Frontend lint/typecheck + backend Ruff |
| `make backend_lint` | Ruff import fix, format, and lint under `api/` |
| `make frontend_lint` | ESLint + `tsc --noEmit` in `frontend/` |
| `make clean` | Remove caches, checkpoints, and temp OpenAPI JSON |
