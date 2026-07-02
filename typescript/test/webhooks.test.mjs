import { test } from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { Webhooks, SignatureVerificationError } from "../dist/index.js";

const SECRET = "whsec_test_secret";
const wh = new Webhooks();

const sign = (secret, ts, body) =>
  createHmac("sha256", secret).update(`${ts}.${body}`).digest("hex");

const headers = (ts, body, { secret = SECRET, prefix = "v1=" } = {}) => ({
  "X-Webhook-Timestamp": ts,
  "X-HostPay-Signature": prefix + sign(secret, ts, body),
});

const now = () => String(Math.floor(Date.now() / 1000));

test("valid signature parses event", () => {
  const body = JSON.stringify({ event: "deposit.completed", data: { id: "txn_1" } });
  const ts = now();
  const evt = wh.constructEvent(body, headers(ts, body), SECRET);
  assert.equal(evt.event, "deposit.completed");
  assert.equal(evt.data.id, "txn_1");
});

test("tampered body rejected", () => {
  const ts = now();
  const signed = JSON.stringify({ amount: 1 });
  assert.throws(
    () => wh.constructEvent(JSON.stringify({ amount: 1000000 }), headers(ts, signed), SECRET),
    SignatureVerificationError,
  );
});

test("wrong secret rejected", () => {
  const body = JSON.stringify({ a: 1 });
  const ts = now();
  assert.throws(
    () => wh.constructEvent(body, headers(ts, body), "whsec_other"),
    SignatureVerificationError,
  );
});

test("expired timestamp rejected", () => {
  const body = JSON.stringify({ a: 1 });
  const ts = String(Math.floor(Date.now() / 1000) - 10000);
  assert.throws(
    () => wh.constructEvent(body, headers(ts, body), SECRET, 300),
    SignatureVerificationError,
  );
});

test("missing headers rejected", () => {
  assert.throws(() => wh.constructEvent("{}", {}, SECRET), SignatureVerificationError);
});

test("bytes payload, no v1= prefix, lowercase + Headers instance", () => {
  const body = JSON.stringify({ ok: true });
  const ts = now();
  const h = new Headers({
    "x-webhook-timestamp": ts,
    "x-hostpay-signature": sign(SECRET, ts, body),
  });
  const evt = wh.constructEvent(new TextEncoder().encode(body), h, SECRET);
  assert.equal(evt.ok, true);
});
