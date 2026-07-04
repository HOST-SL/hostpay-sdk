import { test } from "node:test";
import assert from "node:assert/strict";
import { HostPay, AuthenticationError, InvalidRequestError } from "../dist/index.js";

function makeClient(handler) {
  return new HostPay({
    apiKey: "ak-x",
    secretKey: "sk-y",
    baseUrl: "https://api.test",
    fetch: async (url, init) => handler(url, init),
  });
}

test("auth headers, path, and body", async () => {
  let seen;
  const client = makeClient((url, init) => {
    seen = { url, headers: init.headers, body: JSON.parse(init.body) };
    return new Response(JSON.stringify({ id: "usr_1", name: "Alice" }), { status: 201 });
  });

  const user = await client.users.create({
    appUserId: "u1",
    name: "Alice",
    phoneNumber: "+23279000000",
  });

  assert.equal(seen.url, "https://api.test/api/v1/users/create/");
  assert.equal(seen.headers["api-key"], "ak-x");
  assert.equal(seen.headers["secret-key"], "sk-y");
  assert.equal(seen.body.app_user_id, "u1");
  assert.equal(user.id, "usr_1");
});

test("idempotency key forwarded", async () => {
  let idem;
  const client = makeClient((url, init) => {
    idem = init.headers["Idempotency-Key"];
    return new Response(JSON.stringify({ transaction_id: "txn_1" }), { status: 200 });
  });
  await client.deposits.mobileMoney({ walletId: "w1", amount: 100, idempotencyKey: "abc-123" });
  assert.equal(idem, "abc-123");
});

test("403 maps to AuthenticationError", async () => {
  const client = makeClient(
    () => new Response(JSON.stringify({ detail: "Invalid credentials" }), { status: 403 }),
  );
  await assert.rejects(() => client.wallets.balance("w1"), (err) => {
    assert.ok(err instanceof AuthenticationError);
    assert.equal(err.status, 403);
    assert.match(err.message, /Invalid credentials/);
    return true;
  });
});

test("422 maps to InvalidRequestError", async () => {
  const client = makeClient(
    () => new Response(JSON.stringify({ detail: "bad amount" }), { status: 422 }),
  );
  await assert.rejects(
    () => client.payouts.mobileMoney({ walletId: "w1", amount: -5, phoneNumber: "+232" }),
    InvalidRequestError,
  );
});

test("users.list passes query params", async () => {
  let seen;
  const client = makeClient((url) => {
    seen = url;
    return new Response(JSON.stringify([{ id: "usr_1" }]), { status: 200 });
  });
  const users = await client.users.list({ isActive: true });
  assert.equal(seen, "https://api.test/api/v1/users/?is_active=true");
  assert.equal(users[0].id, "usr_1");
});

test("users.update sends PUT with full body", async () => {
  let seen;
  const client = makeClient((url, init) => {
    seen = { url, method: init.method, body: JSON.parse(init.body) };
    return new Response(JSON.stringify({ id: "usr_1" }), { status: 200 });
  });
  await client.users.update("usr_1", {
    appUserId: "u1",
    name: "New Name",
    phoneNumber: "+232",
  });
  assert.equal(seen.url, "https://api.test/api/v1/users/usr_1/");
  assert.equal(seen.method, "PUT");
  assert.equal(seen.body.name, "New Name");
});

test("lifecycle and transactions paths", async () => {
  const calls = [];
  const client = makeClient((url, init) => {
    calls.push(`${init.method} ${url.replace("https://api.test", "")}`);
    return new Response("{}", { status: 200 });
  });
  await client.users.delete("u1");
  await client.users.disable("u1");
  await client.users.enable("u1");
  await client.wallets.disable("w1");
  await client.wallets.enable("w1");
  await client.transactions.get("t1");
  await client.transactions.forWallet("w1");
  await client.transactions.list({ status: "completed", limit: 10 });

  assert.deepEqual(calls, [
    "DELETE /api/v1/users/u1/",
    "POST /api/v1/users/u1/disable",
    "POST /api/v1/users/u1/enable",
    "POST /api/v1/wallets/w1/disable",
    "POST /api/v1/wallets/w1/enable",
    "GET /api/v1/transactions/t1",
    "GET /api/v1/transactions/wallet/w1",
    "GET /api/v1/transactions/?status=completed&limit=10",
  ]);
});

test("wallets.list passes query params", async () => {
  let seen;
  const client = makeClient((url) => {
    seen = url;
    return new Response(JSON.stringify([{ id: "w1" }]), { status: 200 });
  });
  const wallets = await client.wallets.list({ isActive: true });
  assert.equal(seen, "https://api.test/api/v1/wallets/?is_active=true");
  assert.equal(wallets[0].id, "w1");
});

test("escrow methods forward idempotency key", async () => {
  const seen = [];
  const client = makeClient((url, init) => {
    seen.push([new URL(url).pathname, init.headers["Idempotency-Key"]]);
    return new Response(JSON.stringify({ id: "esc_1" }), { status: 200 });
  });

  await client.escrow.hold({ walletId: "w1", amount: 10, idempotencyKey: "hold-1" });
  await client.escrow.release("esc_1", { recipientWalletId: "w2", idempotencyKey: "rel-1" });
  await client.escrow.refund("esc_1", { idempotencyKey: "ref-1" });

  assert.deepEqual(seen, [
    ["/api/v1/escrow/hold", "hold-1"],
    ["/api/v1/escrow/esc_1/release", "rel-1"],
    ["/api/v1/escrow/esc_1/refund", "ref-1"],
  ]);
});

test("fees, sync, testing, and subscription paths", async () => {
  const seen = [];
  const client = makeClient((url, init) => {
    seen.push([init.method ?? "GET", new URL(url).pathname, init.body ? JSON.parse(init.body) : null]);
    return new Response(JSON.stringify({}), { status: 200 });
  });

  await client.fees.summary();
  await client.fees.estimateDeposit({ amount: 100, paymentMethod: "card", isInternational: true });
  await client.transactions.sync("mnm_ref_1");
  await client.testing.simulateMonimeWebhook({ transactionId: "txn_1" });
  await client.webhooks.subscriptions.create({ targetUrl: "https://f.example/hook", events: ["payout.failed"] });
  await client.webhooks.subscriptions.update("sub_1", { active: false });
  await client.webhooks.subscriptions.rotateSecret("sub_1");

  assert.deepEqual(seen, [
    ["GET", "/api/v1/fees/summary", null],
    ["POST", "/api/v1/fees/estimate/deposit", { amount: 100, payment_method: "card", is_international: true }],
    ["POST", "/api/v1/transactions/sync/mnm_ref_1", null],
    ["POST", "/api/v1/testing/simulate-monime-webhook", { transaction_id: "txn_1", status: "successful" }],
    ["POST", "/api/v1/webhooks/subscriptions", { target_url: "https://f.example/hook", events: ["payout.failed"] }],
    ["PATCH", "/api/v1/webhooks/subscriptions/sub_1", { active: false }],
    ["POST", "/api/v1/webhooks/subscriptions/sub_1/rotate-secret", null],
  ]);
});

test("appInfo appended to User-Agent", async () => {
  let ua;
  const client = new HostPay({
    apiKey: "ak-x",
    secretKey: "sk-y",
    baseUrl: "https://api.test",
    appInfo: "Fataba-Platform/1.0",
    fetch: async (url, init) => {
      ua = init.headers["User-Agent"];
      return new Response(JSON.stringify({}), { status: 200 });
    },
  });
  await client.fees.summary();
  assert.match(ua, /^hostpay-node\/\d+\.\d+\.\d+ Fataba-Platform\/1\.0$/);
});
