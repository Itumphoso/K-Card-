# Runbook

## Local startup
```bash
cd kcard-platform
cp .env.example .env
docker compose -f infra/compose.yml up --build
```

Gateway: `http://localhost:8000`

## Demo identities
- `admin@kcard.local` / `Admin123!`
- `user@kcard.local` / `User123!`
- `merchant@kcard.local` / `Merchant123!`

## Web admin
```bash
cd apps/web-admin
npm install
npm run dev
```

## Mobile app (Expo)
```bash
cd apps/mobile-app
npm install
npm start
```

## Troubleshooting
- If auth fails due to missing tables, restart stack so auth-service initializes first.
- If you see 401 from domain services, ensure the token is an access token from `/auth/login`.
- If gateway returns 404, ensure the first path segment maps to a configured service domain.
