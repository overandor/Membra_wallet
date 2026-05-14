# Security Notes

This project is intentionally non-custodial.

## Prohibited backend behavior

The backend must not store seed phrases.

The backend must not store private keys.

The backend must not silently spend funds.

The backend must not treat SMS as sufficient authorization for high-value actions.

The backend must not maintain fake custodial balances.

## SMS threat model

SMS can be intercepted, SIM-swapped, delayed, spoofed by weak providers, or read by malware on a user's device.

SMS is acceptable for low-risk prompts, notifications, and intent creation.

Sensitive actions should require stronger verification through a secure wallet action page, wallet signature, passkey, hardware wallet, or explicit external wallet approval.

## Recommended controls

Use low default limits.

Rate-limit commands.

Lock accounts quickly.

Add device and session checks.

Require a secure link for payment completion.

Require explicit wallet authorization.

Log all actions.

Mask aliases in public responses.

Avoid storing unnecessary personal data.

## Settlement proof

A payment should only be marked settled after a trusted wallet callback, Lightning preimage/payment proof, transaction confirmation, or another verifiable settlement event.
