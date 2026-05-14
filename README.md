# Membra SMS Bitcoin Relay

A non-custodial SMS-based Bitcoin and Lightning wallet relay.

Membra does **not** hold user funds, does **not** store seed phrases, does **not** spend from user wallets, and does **not** maintain custodial balances. A phone number is only an alias and notification/command channel. Actual funds stay in the user's own Bitcoin or Lightning wallet.

## Core thesis

Phone number = human-readable wallet alias.

SMS = command and notification relay.

Backend = alias registry, request coordinator, risk/consent layer, watch-only balance fetcher, audit trail.

Bitcoin/Lightning wallet = external user-controlled signer and custodian of funds.

## Core invariant

No backend custody.
No private keys on server.
No SMS-only withdrawal.
No internal BTC balance ledger.
No fake balance movement.
Every real payment must be settled by the user's own wallet or wallet provider.

## What this repository contains

- FastAPI backend scaffold
- SMS webhook command parser
- Phone alias registry
- Watch-only wallet connection records
- Payment request workflow
- Non-custodial payment-intent workflow
- Balance lookup abstraction
- Risk and limits scaffold
- Audit logging scaffold
- Tests for SMS command parsing
- Docker Compose for local Postgres

## Supported SMS commands

- `REGISTER`
- `VERIFY <code>`
- `BALANCE`
- `REQUEST <amount> SATS FROM <phone> FOR <memo>`
- `SEND <amount> SATS TO <phone> FOR <memo>`
- `APPROVE <request_id>`
- `DENY <request_id>`
- `LOCK`
- `HELP`

## Important product behavior

When a user sends `SEND` or `APPROVE`, Membra does not move internal sats. It creates a payment intent and returns a secure wallet action link. The user must complete payment from their own Bitcoin or Lightning wallet.

Example:

1. Bob requests 100,000 sats from Alice.
2. Alice receives an SMS notification.
3. Alice replies `APPROVE RQ123`.
4. Membra creates a payment intent.
5. Alice receives a secure link or Lightning invoice action.
6. Alice's own wallet signs/pays.
7. Membra records settlement proof after confirmation/callback.

## Local setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d postgres
uvicorn app.main:app --reload
```

Visit:

```text
http://localhost:8000/docs
```

Run tests:

```bash
pytest
```

## Environment

See `.env.example`.

## Safety notes

This project is intentionally non-custodial. Do not add server-side seed phrase handling, private key storage, automatic spending, or SMS-only withdrawal execution. If you integrate Lightning via NWC, LNURL, LND, Greenlight, Breez SDK, Alby Hub, or another wallet layer, keep user spend authorization explicit and do not silently spend from SMS alone.

## Compliance note

Even non-custodial relay products can trigger legal, privacy, sanctions, consumer protection, telecommunications, and financial compliance obligations depending on jurisdiction and implementation. This repository is a technical scaffold, not legal advice.
