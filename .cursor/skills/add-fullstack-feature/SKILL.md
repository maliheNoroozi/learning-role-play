---
name: add-fullstack-feature
description: >
  Use when implementing a feature that requires coordinated changes across
  the Next.js frontend and FastAPI backend.
---

# Implement Full-Stack Feature

## 1. Trace the complete flow

Before changing code, determine the end-to-end path:

Next.js UI
→ frontend API layer
→ HTTP request
→ FastAPI router
→ Pydantic schema
→ service
→ LangGraph if applicable
→ response schema
→ generated TypeScript type
→ frontend state
→ UI

Identify which layers actually need modification.

Do not change unrelated layers.

## 2. Plan the contract

Determine whether the API contract needs to change.

Identify:

- request changes
- response changes
- error behavior
- streaming events if applicable

## 3. Implement backend

Read and follow the `add-api-feature` skill.

## 4. Regenerate API types

If the FastAPI API contract changed:

```bash
make generate_openapi
```

Do not manually duplicate the backend schema in TypeScript.

## 5. Implement frontend

Read and follow the `create-nextjs-feature` skill.

Use the generated API contract.

## 6. Verify end-to-end behavior

Check:

UI → request → backend → response → UI

```bash
make backend_lint
make frontend_lint
```
