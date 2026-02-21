# K-Card Architecture

K-Card is organized as a microservice-style MVP on a shared PostgreSQL database.

## Runtime services
- `auth-service` (JWT auth, user/role bootstrap)
- `wallet-service` (wallet balances, append-only ledger, QR generation, payments)
- `payments-service` (mock provider confirmations + payment intent status)
- `transport-service` (merchant + vehicle onboarding, rides, cab location updates)
- `payout-service` (merchant withdrawal flow with admin approval)
- `credit-service` (controlled credit eligibility, draw, repay)
- `api-gateway` (single `/api/v1` entrypoint proxying to all services)
- `postgres`

## Core data model
- Users/Roles + `user_roles`
- Merchant domain (`merchants`, `merchant_users`, `vehicles`, `cab_locations`, `rides`)
- Wallet domain (`wallets`, `ledger_entries`, `payment_intents`, `payouts`)
- Credit domain (`credit_lines`, `credit_events`)
- Global `audit_logs`

## Business rules enforced
1. Users can top up and pay; there is no user cash-out endpoint.
2. Merchant payout endpoint only allows `MERCHANT` role and destinations `mpesa/ecocash/bank`.
3. Ride lifecycle supports request -> assign -> status changes with latest location lookup.
4. Credit draws and repayments are audited and mirrored in wallet ledger entries.

## Security and controls
- JWT access/refresh token flow from auth-service.
- Shared RBAC dependency for service endpoints (`USER`, `MERCHANT`, `ADMIN`).
- Append-only ledger table: new entries are inserted, never edited.
- Audit logs inserted for payout/credit/top-up operations.
