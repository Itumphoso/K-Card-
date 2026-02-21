# K-Card Runbook

## Start platform services
```bash
cd kcard-platform
cp .env.example .env
docker compose -f infra/compose.yml up --build
```

## Run auth service locally
```bash
cd kcard-platform/services/auth-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8001
```

## Seed credentials
- Admin: `admin@kcard.local` / `Admin123!`
- User: `user@kcard.local` / `User123!`
- Merchant user: `merchant@kcard.local` / `Merchant123!`
