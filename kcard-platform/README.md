# K-Card Platform

Monorepo bootstrap for K-Card fintech platform.

## Included in this milestone
- Monorepo folder structure for services/apps/gateway/infra/docs.
- Docker Compose with Postgres, Redis, Auth Service, API Gateway.
- Shared Python package for JWT, password hashing, settings, and DB session.
- Auth service with JWT endpoints and Alembic migration + seed users.

## Quick start
```bash
cd kcard-platform
cp .env.example .env
docker compose -f infra/compose.yml up --build
```
