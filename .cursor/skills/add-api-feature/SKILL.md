---
name: add-api-feature
description: >
  Use when creating or modifying a FastAPI endpoint, request schema,
  response schema, service method, or API-related backend functionality.
---

# Add FastAPI Feature

## 1. Inspect existing architecture

Before writing code:

- Find similar endpoints.
- Inspect the relevant router.
- Inspect existing Pydantic schemas.
- Inspect the service layer.
- Follow existing dependency injection and error handling patterns.

Do not invent a new architecture when an existing pattern can be reused.

## 2. Maintain separation of responsibilities

Routers should handle HTTP concerns:

- request parsing
- status codes
- HTTP errors
- response construction

Business logic should live in services.

Pydantic models should define API contracts.

Do not place significant business logic directly inside route handlers.

## 3. Types and schemas

Reuse existing schemas when appropriate.

Prefer explicit Python type hints.

Avoid returning arbitrary dictionaries when a response schema exists.

## 4. Errors

Use the repository's existing domain exceptions.

Translate domain errors to HTTP errors at the API boundary.

Do not make lower-level service code depend unnecessarily on FastAPI.

## 5. API contract

If request or response schemas change:

```bash
make generate_openapi
```

Then check affected frontend code. Do not manually duplicate backend schemas in TypeScript.

## 6. Verification

```bash
make backend_lint
```

Run relevant tests if they exist for the changed area.
