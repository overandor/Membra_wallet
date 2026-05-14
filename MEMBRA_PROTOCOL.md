# MEMBRA Protocol

Membra_api is the system of record.

This repo follows the shared Membra protocol for reward accounting, payout eligibility, owner balance views, payout preparation, and non-custodial wallet handoff flows.

Core rule: payout eligibility is not payout release. Eligibility comes from approved campaign proof. Release requires payout rail approval, risk checks, and audit logging.

Shared IDs: own_, adv_, ast_, cmp_, plc_, proof_, pay_, pout_, aud_, snap_.

Wallet boundary: this repo must not store seed phrases, private keys, or fake custodial BTC balances. It records reward state and handoff state only.
