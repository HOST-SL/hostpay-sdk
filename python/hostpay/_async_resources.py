"""Async twins of the resource groups in resources.py.

Kept as an explicit mirror (rather than sharing the sync classes) so that
`await client.users.create(...)` type-checks: an async def returning UserRead
is awaitable, a sync method annotated UserRead is not. A parity test asserts
the two modules expose identical classes, methods, and signatures.
"""
from __future__ import annotations

from typing import Any, Optional

from .models import EscrowResponse, TransactionResponse, UserRead, WalletRead
from .resources import PROVIDER_AFRICELL, PROVIDER_ORANGE  # noqa: F401 (re-export)


class _Resource:
    def __init__(self, transport: Any) -> None:
        self._t = transport


class Users(_Resource):
    async def create(
        self,
        app_user_id: str,
        name: str,
        phone_number: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> UserRead:
        return await self._t.request("POST", "/api/v1/users/create/", json={
            "app_user_id": app_user_id,
            "name": name,
            "phone_number": phone_number,
            "email": email,
            "username": username,
        })

    async def get(self, user_id: str) -> UserRead:
        return await self._t.request("GET", f"/api/v1/users/{user_id}/")

    async def list(self, is_active: Optional[bool] = None) -> list[UserRead]:
        params = {} if is_active is None else {"is_active": is_active}
        return await self._t.request("GET", "/api/v1/users/", params=params)

    async def update(
        self,
        user_id: str,
        app_user_id: str,
        name: str,
        phone_number: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> UserRead:
        """Full update — the API expects the complete user body; app_user_id
        must match the existing value (it is immutable)."""
        return await self._t.request("PUT", f"/api/v1/users/{user_id}/", json={
            "app_user_id": app_user_id,
            "name": name,
            "phone_number": phone_number,
            "email": email,
            "username": username,
        })

    async def delete(self, user_id: str) -> Any:
        return await self._t.request("DELETE", f"/api/v1/users/{user_id}/")

    async def disable(self, user_id: str) -> Any:
        return await self._t.request("POST", f"/api/v1/users/{user_id}/disable")

    async def enable(self, user_id: str) -> Any:
        return await self._t.request("POST", f"/api/v1/users/{user_id}/enable")


class Wallets(_Resource):
    async def create(self, user_id: str) -> WalletRead:
        return await self._t.request("POST", f"/api/v1/wallets/create/{user_id}/")

    async def get(self, user_id: str) -> WalletRead:
        return await self._t.request("GET", f"/api/v1/wallets/{user_id}/")

    async def balance(self, wallet_id: str) -> Any:
        return await self._t.request("GET", f"/api/v1/wallets/{wallet_id}/balance")

    async def list(self, is_active: Optional[bool] = None) -> list[WalletRead]:
        params = {} if is_active is None else {"is_active": is_active}
        return await self._t.request("GET", "/api/v1/wallets/", params=params)

    async def disable(self, wallet_id: str) -> Any:
        return await self._t.request("POST", f"/api/v1/wallets/{wallet_id}/disable")

    async def enable(self, wallet_id: str) -> Any:
        return await self._t.request("POST", f"/api/v1/wallets/{wallet_id}/enable")


class Transactions(_Resource):
    async def get(self, transaction_id: str) -> TransactionResponse:
        return await self._t.request("GET", f"/api/v1/transactions/{transaction_id}")

    async def list(
        self,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TransactionResponse]:
        params = {
            "status": status,
            "transaction_type": transaction_type,
            "start_date": start_date,
            "end_date": end_date,
            "search": search,
            "limit": limit,
            "offset": offset,
        }
        return await self._t.request(
            "GET",
            "/api/v1/transactions/",
            params={k: v for k, v in params.items() if v is not None},
        )

    async def for_wallet(self, wallet_id: str) -> list[TransactionResponse]:
        """All transactions for a wallet, incoming and outgoing."""
        return await self._t.request("GET", f"/api/v1/transactions/wallet/{wallet_id}")

    async def sync(self, reference_id: str) -> Any:
        """Trigger an immediate reconciliation sync for one of your
        transactions by its provider reference id — useful right after a
        payment completes."""
        return await self._t.request("POST", f"/api/v1/transactions/sync/{reference_id}")


class Deposits(_Resource):
    async def mobile_money(
        self, wallet_id: str, amount: int, idempotency_key: Optional[str] = None
    ) -> Any:
        return await self._t.request(
            "POST",
            "/api/v1/transactions/wallet/mobile-money-deposit",
            json={"wallet_id": wallet_id, "amount": amount},
            idempotency_key=idempotency_key,
        )

    async def card(
        self,
        wallet_id: str,
        amount: float,
        payment_method_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        return await self._t.request(
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
    async def create(
        self,
        sender_wallet_id: str,
        recipient_identifier: str,
        amount: float,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return await self._t.request(
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
    async def mobile_money(
        self,
        wallet_id: str,
        amount: float,
        phone_number: str,
        provider: str = PROVIDER_ORANGE,
        currency: str = "SLE",
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return await self._t.request(
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

    async def bank(
        self,
        wallet_id: str,
        amount: float,
        currency: str = "usd",
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TransactionResponse:
        return await self._t.request(
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
    async def hold(
        self,
        wallet_id: str,
        amount: float,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return await self._t.request(
            "POST",
            "/api/v1/escrow/hold",
            json={
                "wallet_id": wallet_id,
                "amount": amount,
                "description": description,
            },
            idempotency_key=idempotency_key,
        )

    async def release(
        self,
        transaction_id: str,
        recipient_wallet_id: str,
        amount: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return await self._t.request(
            "POST",
            f"/api/v1/escrow/{transaction_id}/release",
            json={"recipient_wallet_id": recipient_wallet_id, "amount": amount},
            idempotency_key=idempotency_key,
        )

    async def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return await self._t.request(
            "POST",
            f"/api/v1/escrow/{transaction_id}/refund",
            json={"amount": amount},
            idempotency_key=idempotency_key,
        )


class Fees(_Resource):
    async def summary(self) -> Any:
        return await self._t.request("GET", "/api/v1/fees/summary")

    async def configuration(self) -> Any:
        return await self._t.request("GET", "/api/v1/fees/configuration")

    async def estimate_deposit(
        self, amount: float, payment_method: str, is_international: bool = False
    ) -> Any:
        """payment_method: 'mobile_money' | 'card' | 'bank' | 'wallet'."""
        return await self._t.request("POST", "/api/v1/fees/estimate/deposit", json={
            "amount": amount,
            "payment_method": payment_method,
            "is_international": is_international,
        })

    async def estimate_withdrawal(self, amount: float, payment_method: str) -> Any:
        return await self._t.request("POST", "/api/v1/fees/estimate/withdrawal", json={
            "amount": amount,
            "payment_method": payment_method,
        })

    async def estimate_transfer(self, amount: float) -> Any:
        return await self._t.request("POST", "/api/v1/fees/estimate/transfer", json={
            "amount": amount,
        })

    async def estimate_card_metadata(self, payment_method_id: str, amount: float) -> Any:
        """Card-aware deposit estimate using the actual card's country/brand."""
        return await self._t.request(
            "POST", "/api/v1/fees/estimate/deposit/card-metadata", json={
                "payment_method_id": payment_method_id,
                "amount": amount,
            }
        )


class Testing(_Resource):
    async def simulate_monime_webhook(
        self, transaction_id: str, status: str = "successful"
    ) -> Any:
        """Complete or fail a pending Test Mode mobile-money deposit.
        Test keys only — the API rejects this in Live Mode. status:
        'successful' | 'failed'."""
        return await self._t.request(
            "POST", "/api/v1/testing/simulate-monime-webhook", json={
                "transaction_id": transaction_id,
                "status": status,
            }
        )


class WebhookSubscriptions(_Resource):
    async def create(
        self,
        target_url: str,
        events: list[str],
        description: Optional[str] = None,
        ip_allowlist: Optional[list[str]] = None,
        payload_version: Optional[str] = None,
    ) -> Any:
        """Create a subscription. The response includes the signing secret
        ONCE — store it; it cannot be retrieved again (only rotated)."""
        body: dict = {"target_url": target_url, "events": list(events)}
        if description is not None:
            body["description"] = description
        if ip_allowlist is not None:
            body["ip_allowlist"] = list(ip_allowlist)
        if payload_version is not None:
            body["payload_version"] = payload_version
        return await self._t.request("POST", "/api/v1/webhooks/subscriptions", json=body)

    async def list(self) -> Any:
        return await self._t.request("GET", "/api/v1/webhooks/subscriptions")

    async def update(
        self,
        subscription_id: str,
        target_url: Optional[str] = None,
        events: Optional[list[str]] = None,
        active: Optional[bool] = None,
        ip_allowlist: Optional[list[str]] = None,
        payload_version: Optional[str] = None,
    ) -> Any:
        body = {
            k: v
            for k, v in {
                "target_url": target_url,
                "events": events,
                "active": active,
                "ip_allowlist": ip_allowlist,
                "payload_version": payload_version,
            }.items()
            if v is not None
        }
        return await self._t.request(
            "PATCH", f"/api/v1/webhooks/subscriptions/{subscription_id}", json=body
        )

    async def delete(self, subscription_id: str) -> Any:
        return await self._t.request(
            "DELETE", f"/api/v1/webhooks/subscriptions/{subscription_id}"
        )

    async def rotate_secret(self, subscription_id: str) -> Any:
        """Returns the new signing secret once."""
        return await self._t.request(
            "POST", f"/api/v1/webhooks/subscriptions/{subscription_id}/rotate-secret"
        )
