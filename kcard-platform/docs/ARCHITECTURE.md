# K-Card Architecture

## System map (MVP bootstrap)
- **API Gateway** routes versioned `/api/v1/*` traffic to backend services.
- **Auth Service** manages identities, passwords, JWT access/refresh tokens, and RBAC claims.
- **PostgreSQL** is the source of truth for transactional data.
- **Redis** is available for caching/session revocation queues.

## Initial implementation status
This bootstrap includes:
1. Monorepo structure for all required services and apps.
2. Docker Compose runtime with PostgreSQL, Redis, gateway placeholder, and auth service.
3. Shared Python package for configuration, DB session management, JWT helpers, and common schemas.
4. Auth service with Alembic migration and seed data (admin/user/merchant personas + roles).

## Auth flow
1. User registers with email/password.
2. Password is hashed with `bcrypt`.
3. Login validates credentials and issues access + refresh JWTs.
4. `/api/v1/auth/me` reads and validates bearer token and returns profile + roles.
5. Refresh endpoint rotates access token and emits a new refresh token.
