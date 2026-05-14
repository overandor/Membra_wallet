# Membra Wallet

**Membra Wallet is the non-custodial payment boundary for MEMBRA Labs and the MEMBRA Proof Network.**

It coordinates campaign funding state, owner reward eligibility, wallet handoff links, audit logs, payout rail integrations, and optional SMS wallet relay workflows.

## Company Context

- Company: **MEMBRA Labs**
- Flagship product: **MEMBRA Proof Network**
- Commercial wedge supported: **Membra Ads**
- Module: **Membra Wallet**
- Category: non-custodial payment coordination, payout eligibility, wallet relay, audit boundary

## One-Line Thesis

Membra Wallet coordinates payment and payout state while keeping final fund movement inside approved external payment rails and explicit user-authorized wallet flows.

## Core Invariant

Membra records payment state and proof eligibility. It must not silently move value outside an approved payment rail or user-authorized flow.

Membra must not:

- hold private keys
- store seed phrases
- fake internal Bitcoin balances
- execute SMS-only withdrawals
- release rewards without approved proof
- mutate payment state without an audit record
- imply custody unless a regulated payment partner explicitly provides it

## Product Scope

- advertiser campaign funding state
- owner reward eligibility
- payout hold/release workflow
- payment and reward audit logs
- wallet handoff links
- SMS alias relay experiments
- Stripe Connect-style account onboarding
- proof-linked payout rules
- payment reconciliation reports

## Membra Ads Payment Flow

1. Advertiser funds a campaign through an approved rail.
2. Membra records the funding state.
3. Media kit workflow starts.
4. Owner submits placement proof.
5. Proof review determines payout eligibility.
6. Wallet module records reward state.
7. Approved rewards are released through the configured payout rail.
8. Audit event is written.
9. ProofBook can hash funding, eligibility, and release records.

## Reward States

- `pending`
- `eligible`
- `held`
- `released`
- `failed`
- `reversed`

## SMS Bitcoin Relay Submodule Concept

The SMS relay concept remains non-custodial:

- phone number is an alias
- SMS is a command or notification channel
- backend coordinates requests and handoff links
- user wallet or payment provider completes settlement
- audit trail records state changes

## Required Guardrails

- no reward release without approved proof
- no campaign funding without reconciliation
- no unauthenticated webhook state changes
- no manual state change without audit record
- no public leak of sensitive payment metadata
- no hidden balance mutation
- no unsupported financial, legal, or income claims

## Integration Points

| Module | Integration |
|---|---|
| `Membra_ads` | campaign funding status, payout readiness, reward release requests |
| `Membra_kpi` | funded campaigns, eligible rewards, released rewards, failed rewards, reconciliation metrics |
| `Membra_proofbook` | funding proof hash, reward eligibility hash, release audit hash |
| `Membra_admin-` | payout holds, release review, failed payout resolution |
| `membra` | company hub, buyer package, demo runtime |

## Local Setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d postgres
uvicorn app.main:app --reload
```

Docs:

```text
http://localhost:8000/docs
```

Tests:

```bash
pytest
```

## Current Stage

Payment boundary module with SMS relay doctrine and Membra Ads payout integration documentation. Suitable for prototype packaging, not production financial infrastructure until legal, compliance, provider, and security review are complete.