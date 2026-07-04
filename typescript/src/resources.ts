/** Resource groups mapped to the HostPay money surface. See ../openapi.json. */
import type { Escrow as EscrowModel, HostPayObject, Transaction, User, Wallet } from "./models.js";

export interface Transport {
  request(
    method: string,
    path: string,
    init?: { body?: unknown; idempotencyKey?: string; query?: Record<string, unknown> },
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
