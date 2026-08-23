---
name: create-nextjs-feature
description: >
  Use when creating or modifying frontend functionality in the Next.js
  application, including pages, React components, hooks, forms,
  frontend API integration, state management, and UI behavior.
---

# Create a Next.js Feature

## 1. Understand the feature

Before changing code:

- Inspect the relevant existing files.
- Search for similar functionality.
- Understand the existing architecture.
- Do not introduce a new pattern when the repository already has one.

## 2. Decide the server/client boundary

Prefer Server Components.

Use Client Components only when necessary for:

- React state
- effects
- event handlers
- browser APIs
- client-only libraries

Do not add `"use client"` to an entire page when only a small child component needs client behavior.

## 3. Reuse existing code

Before creating something new, search for:

- components
- utilities
- hooks
- API functions
- schemas
- TypeScript types

Avoid duplicate abstractions.

## 4. API integration

Keep API communication in the existing API layer.

Reuse generated OpenAPI types when available (`frontend/lib/openapi.generated.ts`).

Handle:

- loading
- errors
- empty states
- cancellation when appropriate

## 5. React code

Prefer:

- small focused components
- explicit TypeScript types
- composition over large components

Avoid:

- unnecessary useEffect
- unnecessary state
- premature memoization
- duplicated derived state

## 6. Accessibility

Follow the project frontend accessibility rule (`.cursor/rules/frontend.mdc`).

Before finishing, review changed UI for accessibility issues introduced by how
library components are configured, composed, or customized.

## 7. Verification

```bash
make frontend_lint
```

Then review the changed files for unnecessary client components and duplicated code.
