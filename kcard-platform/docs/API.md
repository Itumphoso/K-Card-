# API Surface (`/api/v1`)

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

## Wallet
- `GET /wallets/me`
- `GET /wallets/{wallet_id}/ledger`
- `POST /wallets/topup-intent`
- `POST /wallets/pay`
- `POST /wallets/qr/generate`

## Payments
- `POST /payments/confirm`
- `GET /payments/{intent_id}`

## Transport
- `POST /merchants/register`
- `POST /vehicles/register`
- `POST /cabs/{vehicle_id}/location`
- `POST /rides/request`
- `POST /rides/{ride_id}/assign`
- `POST /rides/{ride_id}/status`
- `GET /rides/{ride_id}`

## Payouts
- `POST /payouts/request`
- `GET /payouts`
- `POST /payouts/{payout_id}/approve`
- `POST /payouts/{payout_id}/mark-paid`

## Credit
- `POST /credit/eligibility-check`
- `POST /credit/request`
- `POST /credit/{credit_line_id}/draw`
- `POST /credit/{credit_line_id}/repay`
- `GET /credit/me`

All services also expose `GET /api/v1/health`.
