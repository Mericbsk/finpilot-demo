# Borsa Academy API Access Matrix

**Status:** Level B implementation pending human review. This documents the legacy `/api/v1/academy` router only; it does not approve a FinSense-to-Borsa content bridge or a production release.

| Method and path | Data class | Authentication | Authorization | Cost and side effects | Current boundary |
|---|---|---|---|---|---|
| `GET /api/v1/academy/status` | Aggregate operational counts | JWT | Admin role | Reads Academy status; no content generation | Admin-only; generic 503 on backend failure |
| `GET /api/v1/academy/dashboard/{user_id}` | Personal learning progress | JWT | Path ID must equal token `sub` | Reads user profile and progress | Cross-user access returns 404 |
| `GET /api/v1/academy/lesson/{lesson_id}` | Lesson content and components | None | Public API route, but source is not approved | Legacy SQLite read was previously possible | Returns 503 until a canonical release reader is integrated |
| `POST /api/v1/academy/onboard` | User answers and learning profile | JWT | Request `user_id` must equal token `sub` | Writes profile and learning path | Cross-user writes return 403 |
| `POST /api/v1/academy/generate` | Draft lesson content | JWT | Admin role | LLM/model cost and database writes | Admin-only; 60 requests/minute per client IP |
| `POST /api/v1/academy/seed` | Bulk starter content | JWT | Admin role | Multiple generation jobs and database writes | Admin-only; 60 requests/minute per client IP |
| `POST /api/v1/academy/run/daily` | Content jobs and quality results | JWT | Admin role | Runs job processing and may incur model/database work | Admin-only; 60 requests/minute per client IP |

## Shared API Controls

- Route-level limits on the three costly admin triggers reuse the existing SlowAPI limiter and its 60/minute per-IP policy.
- CORS uses an explicit default origin list (`localhost:3000`, `:3001`, `:8000`); `CORS_ORIGINS` can replace it. Methods and headers are wildcarded, while credentials are not enabled by the current middleware configuration.
- Request-validation responses no longer include the submitted body or Pydantic input values.
- Academy `POST`, `PUT`, `PATCH`, and `DELETE` requests are capped at 65,536 bytes. The middleware rejects an oversized `Content-Length` early and also counts streamed body chunks before forwarding a bounded body to FastAPI; oversized requests receive 413.
- The 64 KiB cap is a candidate engineering default for JSON-only Academy writes (onboarding answers are the widest input; generation uses metadata, while seed/daily triggers need no payload). This is a Level B behavior change pending human/operations review; it is not deployment or release approval.
- Borsa's web Academy consumes a static JSON artifact and has no caller for these API routes in the inspected frontend. The static producer/owner decision remains pending separately.