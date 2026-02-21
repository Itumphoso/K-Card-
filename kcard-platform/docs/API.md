# K-Card API (Current Milestone)

Base path: `/api/v1`

## Auth Service
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /health`

### Sample register payload
```json
{
  "full_name": "Test User",
  "email": "user@example.com",
  "phone": "+263700000000",
  "password": "Secret123!"
}
```

### Sample login payload
```json
{
  "email": "admin@kcard.local",
  "password": "Admin123!"
}
```
