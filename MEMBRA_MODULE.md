# MEMBRA Module Contract — Wallet

## Role

Ledger and payout-eligibility boundary for MEMBRA. Records holds, Stripe checkout/webhook events, payout eligibility, and settlement-safe wallet status.

## System inputs

- account records
- proof approval events
- listing visibility events
- Stripe events
- admin payout decisions

## System outputs

- ledger events
- payout eligibility records
- hold states
- Stripe event records

## Health

```text
GET /api/health
```

## Replit role

`service`

Runs as the settlement-boundary service behind MEMBRA KPI or the MEMBRA OS website.

## Production boundary

Does not custody funds, move money, request private keys, or request seed phrases. External regulated rails settle money.
