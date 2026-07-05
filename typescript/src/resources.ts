/** Resource groups mapped to the HostPay money surface. See ../openapi.json. */
import type { Escrow as EscrowModel, HostPayObject, Transaction, User, Wallet } from "./models.js";

export interface Transport {
  request(
    method: string,
    path: string,
    init?: {
      body?: unknown;
      idempotencyKey?: string;
      query?: Record<string, unknown>;
      headers?: Record<string, string>;
      formData?: FormData;
    },
  ): Promise<any>;
}

/** Mobile-money providers (wire values the API expects). */
export const Provider = {
  orange: "m17",
  africell: "m18",
} as const;
export type ProviderCode = (typeof Provider)[keyof typeof Provider];

abstract class Resource {
  constructor(protected t: Transport) {}
}

export class Users extends Resource {
  create(params: {
    appUserId: string;
    name: string;
    phoneNumber: string;
    email?: string;
    username?: string;
  }): Promise<User> {
    return this.t.request("POST", "/api/v1/users/create/", {
      body: {
        app_user_id: params.appUserId,
        name: params.name,
        phone_number: params.phoneNumber,
        email: params.email,
        username: params.username,
      },
    });
  }

  get(userId: string): Promise<User> {
    return this.t.request("GET", `/api/v1/users/${userId}/`);
  }

  list(params: { isActive?: boolean } = {}): Promise<User[]> {
    return this.t.request("GET", "/api/v1/users/", {
      query: { is_active: params.isActive },
    });
  }

  /** Full update — the API expects the complete user body; appUserId must
   * match the existing value (it is immutable). */
  update(
    userId: string,
    params: {
      appUserId: string;
      name: string;
      phoneNumber: string;
      email?: string;
      username?: string;
    },
  ): Promise<User> {
    return this.t.request("PUT", `/api/v1/users/${userId}/`, {
      body: {
        app_user_id: params.appUserId,
        name: params.name,
        phone_number: params.phoneNumber,
        email: params.email,
        username: params.username,
      },
    });
  }

  /** Partial update — only the fields you pass are changed (appUserId is immutable). */
  patch(
    userId: string,
    params: {
      name?: string;
      email?: string;
      username?: string;
      phoneNumber?: string;
      isActive?: boolean;
    },
  ): Promise<User> {
    const body: Record<string, unknown> = {};
    if (params.name !== undefined) body.name = params.name;
    if (params.email !== undefined) body.email = params.email;
    if (params.username !== undefined) body.username = params.username;
    if (params.phoneNumber !== undefined) body.phone_number = params.phoneNumber;
    if (params.isActive !== undefined) body.is_active = params.isActive;
    return this.t.request("PATCH", `/api/v1/users/${userId}/`, { body });
  }

  delete(userId: string): Promise<any> {
    return this.t.request("DELETE", `/api/v1/users/${userId}/`);
  }

  disable(userId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/users/${userId}/disable`);
  }

  enable(userId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/users/${userId}/enable`);
  }
}

export class Wallets extends Resource {
  create(userId: string): Promise<Wallet> {
    return this.t.request("POST", `/api/v1/wallets/create/${userId}/`);
  }

  get(userId: string): Promise<Wallet> {
    return this.t.request("GET", `/api/v1/wallets/${userId}/`);
  }

  balance(walletId: string): Promise<HostPayObject> {
    return this.t.request("GET", `/api/v1/wallets/${walletId}/balance`);
  }

  list(params: { isActive?: boolean } = {}): Promise<Wallet[]> {
    return this.t.request("GET", "/api/v1/wallets/", {
      query: { is_active: params.isActive },
    });
  }

  disable(walletId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/wallets/${walletId}/disable`);
  }

  enable(walletId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/wallets/${walletId}/enable`);
  }
}

export class Transactions extends Resource {
  get(transactionId: string): Promise<Transaction> {
    return this.t.request("GET", `/api/v1/transactions/${transactionId}`);
  }

  list(
    params: {
      status?: string;
      transactionType?: string;
      startDate?: string;
      endDate?: string;
      search?: string;
      limit?: number;
      offset?: number;
    } = {},
  ): Promise<Transaction[]> {
    return this.t.request("GET", "/api/v1/transactions/", {
      query: {
        status: params.status,
        transaction_type: params.transactionType,
        start_date: params.startDate,
        end_date: params.endDate,
        search: params.search,
        limit: params.limit,
        offset: params.offset,
      },
    });
  }

  /**
   * Trigger an immediate reconciliation sync for one of your transactions by
   * its provider reference id — useful right after a payment completes.
   */
  sync(referenceId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/transactions/sync/${referenceId}`);
  }

  /** All transactions for a wallet, incoming and outgoing. */
  forWallet(walletId: string): Promise<Transaction[]> {
    return this.t.request("GET", `/api/v1/transactions/wallet/${walletId}`);
  }
}

export class Deposits extends Resource {
  mobileMoney(params: {
    walletId: string;
    amount: number;
    idempotencyKey?: string;
  }): Promise<HostPayObject> {
    return this.t.request(
      "POST",
      "/api/v1/transactions/wallet/mobile-money-deposit",
      {
        body: { wallet_id: params.walletId, amount: params.amount },
        idempotencyKey: params.idempotencyKey,
      },
    );
  }

  card(params: {
    walletId: string;
    amount: number;
    paymentMethodId?: string;
    idempotencyKey?: string;
  }): Promise<HostPayObject> {
    return this.t.request(
      "POST",
      "/api/v1/transactions/wallet/card-deposit/create",
      {
        body: {
          wallet_id: params.walletId,
          amount: params.amount,
          payment_method_id: params.paymentMethodId,
        },
        idempotencyKey: params.idempotencyKey,
      },
    );
  }
}

export class Transfers extends Resource {
  create(params: {
    senderWalletId: string;
    recipientIdentifier: string;
    amount: number;
    description?: string;
    idempotencyKey?: string;
  }): Promise<Transaction> {
    return this.t.request("POST", "/api/v1/transactions/wallet/transfer/", {
      body: {
        sender_wallet_id: params.senderWalletId,
        recipient_identifier: params.recipientIdentifier,
        amount: params.amount,
        description: params.description,
      },
      idempotencyKey: params.idempotencyKey,
    });
  }
}

export class Payouts extends Resource {
  mobileMoney(params: {
    walletId: string;
    amount: number;
    phoneNumber: string;
    provider?: ProviderCode;
    currency?: string;
    idempotencyKey?: string;
  }): Promise<Transaction> {
    return this.t.request(
      "POST",
      "/api/v1/transactions/wallet/mobile-money-cashout/",
      {
        body: {
          wallet_id: params.walletId,
          amount: params.amount,
          phone_number: params.phoneNumber,
          provider: params.provider ?? Provider.orange,
          currency: params.currency ?? "SLE",
        },
        idempotencyKey: params.idempotencyKey,
      },
    );
  }

  bank(params: {
    walletId: string;
    amount: number;
    currency?: string;
    description?: string;
    idempotencyKey?: string;
  }): Promise<Transaction> {
    return this.t.request("POST", "/api/v1/transactions/wallet/payout/", {
      body: {
        wallet_id: params.walletId,
        amount: params.amount,
        currency: params.currency ?? "usd",
        description: params.description,
      },
      idempotencyKey: params.idempotencyKey,
    });
  }
}

export class Escrow extends Resource {
  hold(params: {
    walletId: string;
    amount: number;
    description?: string;
    idempotencyKey?: string;
  }): Promise<EscrowModel> {
    return this.t.request("POST", "/api/v1/escrow/hold", {
      body: {
        wallet_id: params.walletId,
        amount: params.amount,
        description: params.description,
      },
      idempotencyKey: params.idempotencyKey,
    });
  }

  release(
    transactionId: string,
    params: { recipientWalletId: string; amount?: number; idempotencyKey?: string },
  ): Promise<EscrowModel> {
    return this.t.request("POST", `/api/v1/escrow/${transactionId}/release`, {
      body: {
        recipient_wallet_id: params.recipientWalletId,
        amount: params.amount,
      },
      idempotencyKey: params.idempotencyKey,
    });
  }

  refund(
    transactionId: string,
    params: { amount?: number; idempotencyKey?: string } = {},
  ): Promise<EscrowModel> {
    return this.t.request("POST", `/api/v1/escrow/${transactionId}/refund`, {
      body: { amount: params.amount },
      idempotencyKey: params.idempotencyKey,
    });
  }
}

export class Fees extends Resource {
  summary(): Promise<any> {
    return this.t.request("GET", "/api/v1/fees/summary");
  }

  configuration(): Promise<any> {
    return this.t.request("GET", "/api/v1/fees/configuration");
  }

  /** paymentMethod: "mobile_money" | "card" | "bank" | "wallet". */
  estimateDeposit(params: {
    amount: number;
    paymentMethod: string;
    isInternational?: boolean;
  }): Promise<any> {
    return this.t.request("POST", "/api/v1/fees/estimate/deposit", {
      body: {
        amount: params.amount,
        payment_method: params.paymentMethod,
        is_international: params.isInternational ?? false,
      },
    });
  }

  estimateWithdrawal(params: { amount: number; paymentMethod: string }): Promise<any> {
    return this.t.request("POST", "/api/v1/fees/estimate/withdrawal", {
      body: { amount: params.amount, payment_method: params.paymentMethod },
    });
  }

  estimateTransfer(params: { amount: number }): Promise<any> {
    return this.t.request("POST", "/api/v1/fees/estimate/transfer", {
      body: { amount: params.amount },
    });
  }

  /** Card-aware deposit estimate using the actual card's country/brand. */
  estimateCardMetadata(params: { paymentMethodId: string; amount: number }): Promise<any> {
    return this.t.request("POST", "/api/v1/fees/estimate/deposit/card-metadata", {
      body: { payment_method_id: params.paymentMethodId, amount: params.amount },
    });
  }
}

export class Testing extends Resource {
  /**
   * Complete or fail a pending Test Mode mobile-money deposit. Test keys
   * only — the API rejects this in Live Mode.
   */
  simulateMonimeWebhook(params: {
    transactionId: string;
    status?: "successful" | "failed";
  }): Promise<any> {
    return this.t.request("POST", "/api/v1/testing/simulate-monime-webhook", {
      body: {
        transaction_id: params.transactionId,
        status: params.status ?? "successful",
      },
    });
  }
}

export class WebhookSubscriptions extends Resource {
  /**
   * Create a subscription. The response includes the signing secret ONCE —
   * store it; it cannot be retrieved again (only rotated).
   */
  create(params: {
    targetUrl: string;
    events: string[];
    description?: string;
    ipAllowlist?: string[];
    payloadVersion?: string;
  }): Promise<any> {
    const body: Record<string, unknown> = {
      target_url: params.targetUrl,
      events: params.events,
    };
    if (params.description !== undefined) body.description = params.description;
    if (params.ipAllowlist !== undefined) body.ip_allowlist = params.ipAllowlist;
    if (params.payloadVersion !== undefined) body.payload_version = params.payloadVersion;
    return this.t.request("POST", "/api/v1/webhooks/subscriptions", { body });
  }

  list(): Promise<any> {
    return this.t.request("GET", "/api/v1/webhooks/subscriptions");
  }

  update(
    subscriptionId: string,
    params: {
      targetUrl?: string;
      events?: string[];
      active?: boolean;
      ipAllowlist?: string[];
      payloadVersion?: string;
    },
  ): Promise<any> {
    const body: Record<string, unknown> = {};
    if (params.targetUrl !== undefined) body.target_url = params.targetUrl;
    if (params.events !== undefined) body.events = params.events;
    if (params.active !== undefined) body.active = params.active;
    if (params.ipAllowlist !== undefined) body.ip_allowlist = params.ipAllowlist;
    if (params.payloadVersion !== undefined) body.payload_version = params.payloadVersion;
    return this.t.request("PATCH", `/api/v1/webhooks/subscriptions/${subscriptionId}`, { body });
  }

  delete(subscriptionId: string): Promise<void> {
    return this.t.request("DELETE", `/api/v1/webhooks/subscriptions/${subscriptionId}`);
  }

  /** Returns the new signing secret once. */
  rotateSecret(subscriptionId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/webhooks/subscriptions/${subscriptionId}/rotate-secret`);
  }
}

export class Connect extends Resource {
  /**
   * Submit identity + business details for the wallet owner's Stripe Connect
   * account. `clientIp` must be the END CUSTOMER's IP address — Stripe records
   * it as evidence of Terms-of-Service acceptance, so the SDK refuses to guess it.
   */
  completeOnboarding(params: {
    walletId: string;
    individual: Record<string, unknown>;
    businessProfile: Record<string, unknown>;
    clientIp: string;
    cardToken?: string;
  }): Promise<any> {
    if (!params.clientIp) {
      throw new Error(
        "clientIp is required: Stripe records it for TOS acceptance and it must be the end customer's IP, not your server's",
      );
    }
    return this.t.request("POST", "/api/v1/transactions/wallet/complete-onboarding/", {
      body: {
        wallet_id: params.walletId,
        individual: params.individual,
        business_profile: params.businessProfile,
        card_token: params.cardToken,
      },
      headers: { "X-Forwarded-For": params.clientIp },
    });
  }

  /** Upload an identity document (JPEG/PNG/PDF, max 10 MB). */
  uploadVerificationDocument(params: {
    walletId: string;
    document: Blob | Uint8Array;
    documentSide: "front" | "back";
    filename?: string;
    mimeType?: string;
  }): Promise<any> {
    const blob =
      params.document instanceof Blob
        ? params.document
        : new Blob([params.document as Uint8Array<ArrayBuffer>], { type: params.mimeType ?? "image/jpeg" });
    const formData = new FormData();
    formData.set("document_side", params.documentSide);
    formData.set("file", blob, params.filename ?? "document.jpg");
    return this.t.request(
      "POST",
      `/api/v1/transactions/wallet/${params.walletId}/connect/verification-document`,
      { formData },
    );
  }

  /** Sync and return the Connect account's verification status. */
  status(walletId: string): Promise<any> {
    return this.t.request("GET", `/api/v1/transactions/wallet/${walletId}/connect/status`);
  }

  delete(walletId: string): Promise<any> {
    return this.t.request("POST", "/api/v1/transactions/wallet/connect/delete", {
      query: { wallet_id: walletId },
    });
  }
}
