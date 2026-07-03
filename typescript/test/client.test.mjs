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
