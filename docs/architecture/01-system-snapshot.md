# System Snapshot (Week 01)

## Purpose
Provide a stable foundation for a data → decision AI system.

## Current Components
- FastAPI service (health endpoint)
- PostgreSQL via Docker Compose
- Alembic migrations
- Local dev workflow via Make + uv

## What Exists vs What’s Planned
Exists:
- Infrastructure
- Tooling
- DB lifecycle

Planned (not built yet):
- Data ingestion
- Transformations
- Models
- Decision logic

## Key Constraints
- Local-first dev
- Reproducible installs
- No secrets in repo
- DB must be ready before app/migrations
