import { APIConnectionError, errorFromStatus } from "./errors.js";
import {
  Deposits,
  Escrow,
  Payouts,
  Transactions,
  Transfers,
  Users,
  Wallets,
  type Transport,
} from "./resources.js";
import { Webhooks } from "./webhooks.js";

const DEFAULT_BASE_URL = "https://hpay-api.host-sl.com";

export interface HostPayOptions {
  apiKey: string;
  secretKey: string;
  baseUrl?: string;
  /** Per-request timeout in ms (default 30000). */
  timeout?: number;
  /** Retries for connection errors / 5xx (default 2). */
  maxRetries?: number;
  /** Override fetch (for tests or custom agents). Defaults to global fetch. */
  fetch?: typeof fetch;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

class HttpTransport implements Transport {
  private baseUrl: string;
  private timeout: number;
  private maxRetries: number;
  private fetchImpl: typeof fetch;
  private auth: Record<string, string>;

  constructor(opts: HostPayOptions) {
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.timeout = opts.timeout ?? 30_000;
    this.maxRetries = opts.maxRetries ?? 2;
    this.fetchImpl = opts.fetch ?? globalThis.fetch;
    this.auth = {
      "api-key": opts.apiKey,
      "secret-key": opts.secretKey,
      "User-Agent": "hostpay-node/0.2.1",
    };
  }

  async request(
    method: string,
    path: string,
    init: { body?: unknown; idempotencyKey?: string; query?: Record<string, unknown> } = {},
  ): Promise<any> {
    if (init.query) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(init.query)) {
        if (v !== undefined && v !== null) qs.set(k, String(v));
      }
      const q = qs.toString();
      if (q) path += (path.includes("?") ? "&" : "?") + q;
    }
    const headers: Record<string, string> = {
      ...this.auth,
      "Content-Type": "application/json",
    };
    if (init.idempotencyKey) headers["Idempotency-Key"] = init.idempotencyKey;
    const payload =
      init.body !== undefined ? JSON.stringify(init.body) : undefined;

    let lastErr: unknown;
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeout);
      let res: Response;
      try {
        res = await this.fetchImpl(this.baseUrl + path, {
          method,
          headers,
          body: payload,
          signal: controller.signal,
        });
      } catch (err) {
        lastErr = err;
        if (attempt < this.maxRetries) {
          await sleep(500 * 2 ** attempt);
          continue;
        }
        throw new APIConnectionError(`Could not reach HostPay: ${String(err)}`);
      } finally {
        clearTimeout(timer);
      }

      if (res.status >= 500 && attempt < this.maxRetries) {
        await sleep(500 * 2 ** attempt);
        continue;
      }
      return handleResponse(res);
    }
    throw new APIConnectionError(`Could not reach HostPay: ${String(lastErr)}`);
  }
}

async function handleResponse(res: Response): Promise<any> {
  const text = await res.text();
  if (res.ok) return text ? JSON.parse(text) : null;

  let detail: unknown = text;
  try {
    const parsed = JSON.parse(text);
    detail =
      parsed && typeof parsed === "object" && "detail" in parsed
        ? (parsed as any).detail
        : parsed;
  } catch {
    /* keep raw text */
  }
  const message = typeof detail === "string" ? detail : `HTTP ${res.status}`;
  throw errorFromStatus(res.status, message, detail);
}

export class HostPay {
  readonly users: Users;
  readonly wallets: Wallets;
  readonly deposits: Deposits;
  readonly transfers: Transfers;
  readonly transactions: Transactions;
  readonly payouts: Payouts;
  readonly escrow: Escrow;
  readonly webhooks: Webhooks;

  constructor(opts: HostPayOptions) {
    if (!opts.apiKey || !opts.secretKey) {
      throw new Error("apiKey and secretKey are required");
    }
    const t = new HttpTransport(opts);
    this.users = new Users(t);
    this.wallets = new Wallets(t);
    this.deposits = new Deposits(t);
    this.transfers = new Transfers(t);
    this.transactions = new Transactions(t);
    this.payouts = new Payouts(t);
    this.escrow = new Escrow(t);
    this.webhooks = new Webhooks();
  }
}
