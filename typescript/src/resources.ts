/** Resource groups mapped to the HostPay money surface. See ../openapi.json. */

export interface Transport {
  request(
    method: string,
    path: string,
    init?: { body?: unknown; idempotencyKey?: string },
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
  }): Promise<any> {
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

  get(userId: string): Promise<any> {
    return this.t.request("GET", `/api/v1/users/${userId}/`);
  }
}

export class Wallets extends Resource {
  create(userId: string): Promise<any> {
    return this.t.request("POST", `/api/v1/wallets/create/${userId}/`);
  }

  get(userId: string): Promise<any> {
    return this.t.request("GET", `/api/v1/wallets/${userId}/`);
  }

  balance(walletId: string): Promise<any> {
    return this.t.request("GET", `/api/v1/wallets/${walletId}/balance`);
  }
}

export class Deposits extends Resource {
  mobileMoney(params: {
    walletId: string;
    amount: number;
    idempotencyKey?: string;
  }): Promise<any> {
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
  }): Promise<any> {
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
  }): Promise<any> {
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
  }): Promise<any> {
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
  }): Promise<any> {
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
  }): Promise<any> {
    return this.t.request("POST", "/api/v1/escrow/hold", {
      body: {
        wallet_id: params.walletId,
        amount: params.amount,
        description: params.description,
      },
    });
  }

  release(
    transactionId: string,
    params: { recipientWalletId: string; amount?: number },
  ): Promise<any> {
    return this.t.request("POST", `/api/v1/escrow/${transactionId}/release`, {
      body: {
        recipient_wallet_id: params.recipientWalletId,
        amount: params.amount,
      },
    });
  }

  refund(transactionId: string, params: { amount?: number } = {}): Promise<any> {
    return this.t.request("POST", `/api/v1/escrow/${transactionId}/refund`, {
      body: { amount: params.amount },
    });
  }
}
