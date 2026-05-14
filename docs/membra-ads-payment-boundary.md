# Membra Ads Payment Boundary

Membra Wallet defines the payment and reward state layer for Membra Ads.

## Role

Membra Ads manages campaigns, media kits, proof records, and tracking events.

Membra Wallet manages payment state, reward eligibility, release checks, and audit records.

## Flow

1. Advertiser funds a campaign through an approved payment rail.
2. Membra records the campaign as funded.
3. Owner completes the placement workflow.
4. Proof review determines eligibility.
5. Wallet module records the reward state.
6. Approved rewards are released through the configured payment rail.
7. Audit records are written for every state change.

## States

- pending
- eligible
- held
- released
- failed
- reversed

## Required controls

- no release without approved proof
- no release without campaign funding record
- no unauthenticated webhook state changes
- no manual state change without audit record
- no hidden balance mutation

## Integration points

Membra Ads should call Wallet for:

- campaign funding status
- owner account readiness
- reward eligibility
- release request
- payment audit export

Membra Wallet should call ProofBook for:

- reward proof hash
- funding proof hash
- release audit hash
