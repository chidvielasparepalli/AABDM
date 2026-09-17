# AABDM

**Autonomous AI Business Development Manager**

AABDM is an AI-powered business development platform designed to support prospect research, client management, sales calls, negotiation, follow-ups, analytics, and learning workflows from a unified application.

## Architecture

- `apps/api` — FastAPI backend and business logic
- `apps/dashboard` — application dashboard
- Authentication — Clerk-compatible authenticated API flow
- Database — SQLAlchemy-backed persistence
- AI/business workflows — research, calls, negotiation, follow-ups, memory, learning, and analytics

## Backend

The API exposes a health endpoint at `/health` and an authenticated `/me` endpoint. Core feature routers are registered from the FastAPI application entry point.

## Development

Keep secrets and local environment files outside version control. Use `.env.example` for documented environment variables.

## Status

AABDM is under active development. APIs and product workflows may evolve as features are implemented.
