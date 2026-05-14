# Membra Wallet

Membra Wallet is the payment boundary for the MEMBRA ecosystem.

It coordinates campaign funding, owner reward eligibility, payment state, wallet handoff links, audit logs, and payout rail integrations for Membra Ads, Membra Relay, Membra Wear, Membra KPI, and future MEMBRA modules.

## One-line thesis

Membra Wallet coordinates payments and payouts while keeping final fund movement inside approved external payment rails and user-authorized wallet flows.

## Product scope

- advertiser campaign funding state
- owner reward eligibility
- payout release workflow
- payment and reward audit logs
- wallet handoff links
- SMS alias relay experiments
- Stripe Connect style account onboarding
- proof-linked payout rules
- payment reconciliation reports

## Core invariant

Membra records payment state and proof eligibility. It must not silently move value outside an approved payment rail or user-authorized flow.

## Membra Ads payment flow

1. Advertiser funds a campaign.
2. Membra records the funding state.
3. Media kit workflow starts.
4. Owner submits placement proof.
5. Proof review determines eligibility.
6. Wallet module records reward state.
7. Approved rewards are released through the configured payout rail.
8. Audit event is written.
9. ProofBook can hash the funding and reward records.

## Reward states

- pending
- eligible
- held
- released
- failed
- reversed

## SMS Bitcoin Relay submodule concept

The SMS relay concept remains non-custodial:

- phone number is an alias
- SMS is a command or notification channel
- backend coordinates requests and handoff links
- user wallet or payment provider completes settlement
- audit trail records state changes

## Required guardrails

- no reward release without approved proof
- no campaign funding without reconciliation
- no unauthenticated webhook state changes
- no manual state change without audit record
- no public leak of sensitive payment metadata
- no hidden balance mutation

## Integration points

Membra Ads calls Wallet for:

- campaign funding status
- owner payout readiness
- reward release request
- payment audit export

Membra KPI reads Wallet data for:

- funded campaigns
- eligible rewards
- released rewards
- failed rewards
- payment reconciliation metrics

Membra ProofBook records:

- funding proof hash
- proof-approved reward hash
- release audit hash

## Current stage

Payment boundary module with SMS relay doctrine and Membra Ads payout integration documentation.
