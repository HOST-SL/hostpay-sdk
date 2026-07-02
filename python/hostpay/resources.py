"""Resource groups mapped to the HostPay money surface.

Each method mirrors a real endpoint; see ../openapi.json for the full API.
"""
from __future__ import annotations

from typing import Any, Optional

from .models import EscrowResponse, TransactionResponse, UserRead, WalletRead

# Mobile-money providers (wire values expected by the API).
PROVIDER_ORANGE = "m17"
PROVIDER_AFRICELL = "m18"


class _Resource:
    def __init__(self, transport: Any) -> None:
        self._t = transport


class Users(_Resource):
    def create(
        self,
        app_user_id: str,
        name: str,
        phone_number: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> UserRead:
        return self._t.request("POST", "/api/v1/users/create/", json={
            "app_user_id": app_user_id,
            "name": name,
            "phone_number": phone_number,
            "email": email,
            "username": username,
        })

    def get(self, user_id: str) -> UserRead:
        return self._t.request("GET", f"/api/v1/users/{user_id}/")


class Wallets(_Resource):
    def create(self, user_id: str) -> WalletRead:
        return self._t.request("POST", f"/api/v1/wallets/create/{user_id}/")

    def get(self, user_id: str) -> WalletRead:
        return self._t.request("GET", f"/api/v1/wallets/{user_id}/")

    def balance(self, wallet_id: str) -> Any:
        return self._t.request("GET", f"/api/v1/wallets/{wallet_id}/balance")


class Deposits(_Resource):
    def mobile_money(
        self, wallet_id: str, amount: int, idempotency_key: Optional[str] = None
    ) -> Any:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/mobile-money-deposit",
            json={"wallet_id": wallet_id, "amount": amount},
            idempotency_key=idempotency_key,
        )

    def card(
        self,
        wallet_id: str,
        amount: float,
        payment_method_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/card-deposit/create",
            json={
                "wallet_id": wallet_id,
                "amount": amount,
                "payment_method_id": payment_method_id,
            },
            idempotency_key=idempotency_key,
        )


class Transfers(_Resource):
    def create(
        self,
        sender_wallet_id: str,
        recipient_identifier: str,
        amount: float,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/transfer/",
            json={
                "sender_wallet_id": sender_wallet_id,
                "recipient_identifier": recipient_identifier,
                "amount": amount,
                "description": description,
            },
            idempotency_key=idempotency_key,
        )


class Payouts(_Resource):
    def mobile_money(
        self,
        wallet_id: str,
        amount: float,
        phone_number: str,
        provider: str = PROVIDER_ORANGE,
        currency: str = "SLE",
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/mobile-money-cashout/",
            json={
                "wallet_id": wallet_id,
                "amount": amount,
                "phone_number": phone_number,
                "provider": provider,
                "currency": currency,
            },
            idempotency_key=idempotency_key,
        )

    def bank(
        self,
        wallet_id: str,
        amount: float,
        currency: str = "usd",
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/payout/",
            json={
                "wallet_id": wallet_id,
                "amount": amount,
                "currency": currency,
                "description": description,
            },
            idempotency_key=idempotency_key,
        )


class Escrow(_Resource):
    def hold(
        self, wallet_id: str, amount: float, description: Optional[str] = None
    ) -> EscrowResponse:
        return self._t.request("POST", "/api/v1/escrow/hold", json={
            "wallet_id": wallet_id,
            "amount": amount,
            "description": description,
        })

    def release(
        self, transaction_id: str, recipient_wallet_id: str, amount: Optional[float] = None
    ) -> EscrowResponse:
        return self._t.request(
            "POST",
            f"/api/v1/escrow/{transaction_id}/release",
            json={"recipient_wallet_id": recipient_wallet_id, "amount": amount},
        )

    def refund(self, transaction_id: str, amount: Optional[float] = None) -> EscrowResponse:
        return self._t.request(
            "POST", f"/api/v1/escrow/{transaction_id}/refund", json={"amount": amount}
        )
