# Architecture

Membra Wallet is a non-custodial SMS relay for Bitcoin and Lightning actions.

## Components

1. SMS relay

Receives inbound user commands and sends notifications. SMS is an interface, not custody.

2. Alias registry

Maps a user's contact alias to a Membra user record. The alias is not a private key and does not control funds.

3. Wallet connections

Stores public, watch-only, or user-authorized wallet references. The backend must never store seed phrases, private keys, signing keys, or spend authority.

4. Payment requests

A request is an intent record. It does not move funds.

5. Payment intents

An intent creates a secure action page or wallet deep link that the user completes from their own wallet.

6. Balance lookup

Balance is read from linked wallet references or external read-only providers. Membra does not maintain a custodial BTC balance.

7. Audit trail

Every registration, request, payment intent, lock, and wallet connection event should be logged.

## Flow

Bob requests sats from Alice.

Alice receives an SMS.

Alice approves by SMS.

Membra creates a payment intent.

Alice opens the wallet action page.

Alice's own wallet signs or pays.

Membra records settlement proof.

## Non-custodial invariant

The backend coordinates requests and notifications. It does not spend.
