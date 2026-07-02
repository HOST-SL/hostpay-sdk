# HostPay Python SDK

A small, typed client for the [HostPay](https://hpay.host-sl.com) payments API —
wallets, deposits, transfers, payouts, escrow, and webhook verification.

## Install

```bash
pip install hostpay          # once published
# or, from this repo:
pip install ./sdk/python
```

Requires Python 3.8+ and `httpx`.

## Quickstart

```python
from hostpay import HostPay

client = HostPay(api_key="ak-...", secret_key="sk-...")
# Test Mode? use your test keys — same code, no real money moves.

# 1. Create a user and their wallet
user = client.users.create(
    app_user_id="user_123",
    name="Alice",
    phone_number="+23279000000",
    email="alice@example.com",
)
wallet = client.wallets.create(user.id)

# 2. Deposit via mobile money
deposit = client.deposits.mobile_money(wallet_id=wallet.id, amount=100)

# 3. Check the balance (attribute or dict access)
bal = client.wallets.balance(wallet.id)
print(bal.balance, bal["currency"])

# 4. Transfer, pay out, escrow
client.transfers.create(sender_wallet_id=wallet.id, recipient_identifier="bob", amount=20)
client.payouts.mobile_money(wallet_id=wallet.id, amount=5, phone_number="+23279000000")
hold = client.escrow.hold(wallet_id=wallet.id, amount=10)
client.escrow.release(hold.id, recipient_wallet_id="...")
```

## Authentication

Pass your `api-key` and `secret-key` once at construction; they're sent on every
request. `base_url` defaults to production — point it at your staging host for
testing.

## Idempotency

Money-moving calls accept `idempotency_key` — reuse the same key to safely retry
without double-charging:

```python
client.payouts.mobile_money(
    wallet_id=w, amount=5, phone_number="+232...", idempotency_key="order-42-payout"
)
```

## Verifying webhooks

Pass the **raw** request body and headers straight from your web framework:

```python
from hostpay import HostPay, SignatureVerificationError

client = HostPay(api_key="ak-...", secret_key="sk-...")

# e.g. in Flask
@app.post("/webhooks/hostpay")
def hook():
    try:
        event = client.webhooks.construct_event(
            payload=request.get_data(),          # raw bytes, not request.json
            headers=request.headers,
            secret=WEBHOOK_SIGNING_SECRET,
        )
    except SignatureVerificationError:
        return "", 400
    if event.event == "deposit.completed":
        ...
    return "", 200
```

Signatures are HMAC-SHA256 over `"<timestamp>.<body>"`; deliveries older than
`tolerance` seconds (default 300) are rejected.

## Errors

All errors derive from `HostPayError` and carry `.status_code` and `.detail`:
`AuthenticationError` (401/403), `InvalidRequestError` (400/404/422),
`RateLimitError` (429), `APIError` (5xx), `APIConnectionError`,
`SignatureVerificationError`.

## Sandbox testing

In Test Mode, a user's phone number drives deterministic outcomes (see the
[Testing guide](https://hpay.host-sl.com/docs/guides/testing)): `+23299000001`
completes, `+23299000002` fails, `+23299000009` stays pending. The same fail
number works for payout recipients.

## Notes

Responses are `HostPayObject` (dict + attribute access), so new API fields work
without an SDK upgrade. Strict typed models can be generated from the committed
[`../openapi.json`](../openapi.json), the source of truth for both SDKs —
regenerate it with `python wallet-system/scripts/dump_openapi.py`.
