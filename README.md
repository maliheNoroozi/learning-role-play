# Learning Roleplay

Conversation-style practice sessions powered by ChatGPT. Learners set up a scenario, role, goals, and AI character, then chat while the backend tracks progress, conversation state, and ending conditions.

## Stack

- **Backend:** FastAPI, LangChain / LangGraph, OpenAI (`gpt-4o-mini`), Redis, MongoDB
- **Frontend:** Next.js (App Router), React, Tailwind CSS, Zod
- **Tooling:** `uv` (Python), `pnpm` (frontend), Docker Compose (Redis, MongoDB)

## How it works

1. The learner submits roleplay setup (scenario, roles, goals, AI character).
2. `POST /roleplays` creates a session, persists it (MongoDB + Redis), and returns a `roleplay_id`.
3. Each chat turn sends only `roleplay_id` + `learner_message` to `POST /roleplays/chat`.
4. A LangGraph pipeline evaluates goals and ending conditions in parallel, then generates either a normal in-character reply or a closing message.
5. Session state is stored with Redis cache-aside + MongoDB write-through. Concurrent chat turns are serialized with a per-session Redis lock.

**Ending conditions:** `goals_achieved`, `profanity`, `conversation_exhausted`, `irrelevant` (after repeated off-topic messages), or `none`.

## Project structure

```
.
├── api/
│   ├── main.py                      # FastAPI app, CORS, /health
│   ├── routers/
│   │   ├── roleplay_router.py       # POST /roleplays
│   │   └── chat_router.py           # POST /roleplays/chat
│   ├── schemas/
│   │   └── roleplay_schemas.py
│   └── services/
│       ├── roleplay/                # LangGraph roleplay, cache, repository, store
│       ├── cache/                   # Redis client + config
│       ├── database/                # MongoDB client + config
│       ├── prompts.py
│       └── config.py
├── frontend/                        # Next.js UI (setup form + chat)
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

Install dependencies:

```bash
uv sync
cd frontend && pnpm install
```

## Run

Start Redis and MongoDB:

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
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 9000
```

Start the frontend (port **3000**):

```bash
make frontend
```

- App: [http://localhost:3000](http://localhost:3000)
- API docs: [http://127.0.0.1:9000/docs](http://127.0.0.1:9000/docs)
- Health: `GET /health` → `{"status":"ok"}`

Stop infrastructure when done:

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

### Send a chat message

`POST /roleplays/chat`

```bash
curl -X POST http://127.0.0.1:9000/roleplays/chat \
  -H "Content-Type: application/json" \
  -d '{
    "roleplay_id": "<uuid>",
    "learner_message": "Hi, I am interested in this car. What is your best price?"
  }'
```

Response includes `ai_response`, `should_end`, `ending_condition`, and optional `ending_rationale`.

| Status | Meaning                             |
| ------ | ----------------------------------- |
| 404    | Unknown `roleplay_id`               |
| 409    | Session already ended, or lock busy |
| 502    | Upstream / generation failure       |

## Frontend flow

1. Home (`/`) — set up scenario, goals, and AI character.
2. On create, the app calls `POST /roleplays` and navigates to `/roleplays/[id]/chat`.
3. Chat sends `roleplay_id` + each learner message to the API and shows the AI reply (and ends the session when `should_end` is true).

## Useful Make targets

| Target                  | Description                                                            |
| ----------------------- | ---------------------------------------------------------------------- |
| `make docker-up`        | Start Redis + MongoDB via Docker Compose                               |
| `make docker-down`      | Stop Redis + MongoDB                                                   |
| `make backend`          | Start API on port 9000 (loads `.env`)                                  |
| `make frontend`         | Start Next.js dev server                                               |
| `make generate_openapi` | Regenerate `frontend/lib/openapi.generated.ts` from the FastAPI schema |
| `make backend_lint`     | Format and lint Python under `api/` and `tests/`                       |
| `make frontend_lint`    | ESLint + TypeScript check (`tsc --noEmit`) in `frontend/`              |
