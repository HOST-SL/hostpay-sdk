# HostPay TypeScript SDK

A small, typed client for the [HostPay](https://hpay.host-sl.com) payments API —
wallets, deposits, transfers, payouts, escrow, transaction queries, user/wallet lifecycle management, and webhook verification.

Server-side only (it uses your `secret-key`). Node 18+, zero runtime dependencies
(uses the built-in `fetch` and `node:crypto`).

## Install

```bash
npm install @hostpay/sdk
```

## Quickstart

```ts
import { HostPay } from "@hostpay/sdk";

const client = new HostPay({ apiKey: "ak-...", secretKey: "sk-..." });
// Test Mode? use your test keys — same code, no real money moves.

// 1. Create a user and their wallet
const user = await client.users.create({
  appUserId: "user_123",
  name: "Alice",
  phoneNumber: "+23279000000",
  email: "alice@example.com",
});
const wallet = await client.wallets.create(user.id);

// 2. Deposit via mobile money
await client.deposits.mobileMoney({ walletId: wallet.id, amount: 100 });

// 3. Check the balance
const bal = await client.wallets.balance(wallet.id);
console.log(bal.balance, bal.currency);

// 4. Transfer, pay out, escrow
await client.transfers.create({ senderWalletId: wallet.id, recipientIdentifier: "bob", amount: 20 });
await client.payouts.mobileMoney({ walletId: wallet.id, amount: 5, phoneNumber: "+23279000000" });
const hold = await client.escrow.hold({ walletId: wallet.id, amount: 10 });
await client.escrow.release(hold.id, { recipientWalletId: "..." });
```

## Authentication

Pass `apiKey` and `secretKey` once; they're sent on every request. `baseUrl`
defaults to production — point it at your staging host for testing.

## Idempotency

Money-moving calls accept `idempotencyKey` — reuse the same key to safely retry
without double-charging:

```ts
await client.payouts.mobileMoney({
  walletId, amount: 5, phoneNumber: "+232...", idempotencyKey: "order-42-payout",
});
```

## Verifying webhooks

Pass the **raw** request body and headers straight from your server:

```ts
import express from "express";
import { HostPay, SignatureVerificationError } from "@hostpay/sdk";

const client = new HostPay({ apiKey: "ak-...", secretKey: "sk-..." });

app.post("/webhooks/hostpay", express.raw({ type: "*/*" }), (req, res) => {
  try {
    const event = client.webhooks.constructEvent(req.body, req.headers, WEBHOOK_SIGNING_SECRET);
    if (event.event === "deposit.completed") { /* ... */ }
    res.sendStatus(200);
  } catch (err) {
    if (err instanceof SignatureVerificationError) return res.sendStatus(400);
    throw err;
  }
});
```

Signatures are HMAC-SHA256 over `"<timestamp>.<body>"`; deliveries older than
`tolerance` seconds (default 300) are rejected.

## Errors

All errors extend `HostPayError` and carry `.status` and `.detail`:
`AuthenticationError` (401/403), `InvalidRequestError` (400/404/422),
`RateLimitError` (429), `APIError` (5xx), `APIConnectionError`,
`SignatureVerificationError`.

## Sandbox testing

In Test Mode, a user's phone number drives deterministic outcomes (see the
[Testing guide](https://hpay.host-sl.com/docs/guides/testing)): `+23299000001`
completes, `+23299000002` fails, `+23299000009` stays pending. The same fail
number works for payout recipients.

## Typed responses

Core responses are strictly typed from the OpenAPI spec: `users.*` return
`User`, `wallets.create/get` return `Wallet`, `transfers`/`payouts` return
`Transaction`, and `escrow.*` returns `Escrow` — so you get autocomplete and
compile-time checks. Ad-hoc responses (wallet balance, the deposit envelope)
are typed loosely as `HostPayObject`.

Types are generated from the committed [`../openapi.json`](../openapi.json)
(`src/generated.ts`) — the source of truth for both SDKs. Regenerate after API
changes with `npm run generate`.
