import { createHmac, timingSafeEqual } from "node:crypto";
import { SignatureVerificationError } from "./errors.js";

/**
 * Verify inbound HostPay webhooks.
 *
 * HostPay signs each delivery with:
 *   X-Webhook-Timestamp: <unix seconds>
 *   X-HostPay-Signature: v1=<hex HMAC-SHA256( secret, "<timestamp>.<raw body>" )>
 *
 * Pass the **raw** request body (string or bytes) exactly as received — not a
 * re-serialized object — or the signature will not match.
 */
const SIG_HEADER = "x-hostpay-signature";
const TS_HEADER = "x-webhook-timestamp";

type HeaderBag = Record<string, string> | Headers;

function getHeader(headers: HeaderBag, name: string): string | undefined {
  if (typeof (headers as Headers).get === "function") {
    return (headers as Headers).get(name) ?? undefined;
  }
  for (const key of Object.keys(headers as Record<string, string>)) {
    if (key.toLowerCase() === name) return (headers as Record<string, string>)[key];
  }
  return undefined;
}

export class Webhooks {
  /** Subscription CRUD (client.webhooks.subscriptions.*) — injected by the
   * client so this module stays transport-free for bare constructEvent use. */
  readonly subscriptions: any;

  constructor(subscriptions?: any) {
    this.subscriptions = subscriptions;
  }

  /**
   * Verify the signature and return the parsed event. Throws
   * SignatureVerificationError on any mismatch, or if the timestamp is older
   * than `tolerance` seconds (replay protection; pass 0 to disable).
   */
  constructEvent(
    payload: string | Uint8Array,
    headers: HeaderBag,
    secret: string,
    tolerance = 300,
  ): any {
    const body =
      typeof payload === "string"
        ? payload
        : Buffer.from(payload).toString("utf8");

    const timestamp = getHeader(headers, TS_HEADER);
    const sigHeader = getHeader(headers, SIG_HEADER);
    if (!timestamp || !sigHeader) {
      throw new SignatureVerificationError(
        "Missing X-Webhook-Timestamp or X-HostPay-Signature header",
      );
    }
    const signature = sigHeader.startsWith("v1=") ? sigHeader.slice(3) : sigHeader;

    const expected = createHmac("sha256", secret)
      .update(`${timestamp}.${body}`)
      .digest("hex");
    const a = Buffer.from(expected);
    const b = Buffer.from(signature);
    if (a.length !== b.length || !timingSafeEqual(a, b)) {
      throw new SignatureVerificationError("Signature mismatch");
    }

    if (tolerance) {
      const ts = Number(timestamp);
      if (!Number.isFinite(ts)) {
        throw new SignatureVerificationError("Invalid timestamp");
      }
      const age = Math.abs(Date.now() / 1000 - ts);
      if (age > tolerance) {
        throw new SignatureVerificationError(
          `Timestamp outside tolerance (${Math.round(age)}s > ${tolerance}s)`,
        );
      }
    }

    return JSON.parse(body);
  }
}
