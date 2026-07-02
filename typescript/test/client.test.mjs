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
