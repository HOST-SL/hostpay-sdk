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

    def list(self, is_active: Optional[bool] = None) -> list[UserRead]:
        params = {} if is_active is None else {"is_active": is_active}
        return self._t.request("GET", "/api/v1/users/", params=params)

    def update(
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
        return self._t.request("PUT", f"/api/v1/users/{user_id}/", json={
            "app_user_id": app_user_id,
            "name": name,
            "phone_number": phone_number,
            "email": email,
            "username": username,
        })


    def patch(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> UserRead:
        """Partial update — only the fields you pass are changed
        (app_user_id is immutable)."""
        body = {
            k: v
            for k, v in {
                "name": name,
                "email": email,
                "username": username,
                "phone_number": phone_number,
                "is_active": is_active,
            }.items()
            if v is not None
        }
        return self._t.request("PATCH", f"/api/v1/users/{user_id}/", json=body)

    def delete(self, user_id: str) -> Any:
        return self._t.request("DELETE", f"/api/v1/users/{user_id}/")

    def disable(self, user_id: str) -> Any:
        return self._t.request("POST", f"/api/v1/users/{user_id}/disable")

    def enable(self, user_id: str) -> Any:
        return self._t.request("POST", f"/api/v1/users/{user_id}/enable")


class Wallets(_Resource):
    def create(self, user_id: str) -> WalletRead:
        return self._t.request("POST", f"/api/v1/wallets/create/{user_id}/")

    def get(self, user_id: str) -> WalletRead:
        return self._t.request("GET", f"/api/v1/wallets/{user_id}/")

    def balance(self, wallet_id: str) -> Any:
        return self._t.request("GET", f"/api/v1/wallets/{wallet_id}/balance")

    def list(self, is_active: Optional[bool] = None) -> list[WalletRead]:
        params = {} if is_active is None else {"is_active": is_active}
        return self._t.request("GET", "/api/v1/wallets/", params=params)

    def disable(self, wallet_id: str) -> Any:
        return self._t.request("POST", f"/api/v1/wallets/{wallet_id}/disable")

    def enable(self, wallet_id: str) -> Any:
        return self._t.request("POST", f"/api/v1/wallets/{wallet_id}/enable")


class Transactions(_Resource):
    def get(self, transaction_id: str) -> TransactionResponse:
        return self._t.request("GET", f"/api/v1/transactions/{transaction_id}")

    def list(
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
        return self._t.request(
            "GET",
            "/api/v1/transactions/",
            params={k: v for k, v in params.items() if v is not None},
        )

    def for_wallet(self, wallet_id: str) -> list[TransactionResponse]:
        """All transactions for a wallet, incoming and outgoing."""
        return self._t.request("GET", f"/api/v1/transactions/wallet/{wallet_id}")

    def sync(self, reference_id: str) -> Any:
        """Trigger an immediate reconciliation sync for one of your
        transactions by its provider reference id — useful right after a
        payment completes."""
        return self._t.request("POST", f"/api/v1/transactions/sync/{reference_id}")


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
        self,
        wallet_id: str,
        amount: float,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return self._t.request(
            "POST",
            "/api/v1/escrow/hold",
            json={
                "wallet_id": wallet_id,
                "amount": amount,
                "description": description,
            },
            idempotency_key=idempotency_key,
        )

    def release(
        self,
        transaction_id: str,
        recipient_wallet_id: str,
        amount: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return self._t.request(
            "POST",
            f"/api/v1/escrow/{transaction_id}/release",
            json={"recipient_wallet_id": recipient_wallet_id, "amount": amount},
            idempotency_key=idempotency_key,
        )

    def refund(
        self,
        transaction_id: str,
        amount: Optional[float] = None,
        idempotency_key: Optional[str] = None,
    ) -> EscrowResponse:
        return self._t.request(
            "POST",
            f"/api/v1/escrow/{transaction_id}/refund",
            json={"amount": amount},
            idempotency_key=idempotency_key,
        )


class Fees(_Resource):
    def summary(self) -> Any:
        return self._t.request("GET", "/api/v1/fees/summary")

    def configuration(self) -> Any:
        return self._t.request("GET", "/api/v1/fees/configuration")

    def estimate_deposit(
        self, amount: float, payment_method: str, is_international: bool = False
    ) -> Any:
        """payment_method: 'mobile_money' | 'card' | 'bank' | 'wallet'."""
        return self._t.request("POST", "/api/v1/fees/estimate/deposit", json={
            "amount": amount,
            "payment_method": payment_method,
            "is_international": is_international,
        })

    def estimate_withdrawal(self, amount: float, payment_method: str) -> Any:
        return self._t.request("POST", "/api/v1/fees/estimate/withdrawal", json={
            "amount": amount,
            "payment_method": payment_method,
        })

    def estimate_transfer(self, amount: float) -> Any:
        return self._t.request("POST", "/api/v1/fees/estimate/transfer", json={
            "amount": amount,
        })

    def estimate_card_metadata(self, payment_method_id: str, amount: float) -> Any:
        """Card-aware deposit estimate using the actual card's country/brand."""
        return self._t.request(
            "POST", "/api/v1/fees/estimate/deposit/card-metadata", json={
                "payment_method_id": payment_method_id,
                "amount": amount,
            }
        )


class Testing(_Resource):
    def simulate_monime_webhook(
        self, transaction_id: str, status: str = "successful"
    ) -> Any:
        """Complete or fail a pending Test Mode mobile-money deposit.
        Test keys only — the API rejects this in Live Mode. status:
        'successful' | 'failed'."""
        return self._t.request(
            "POST", "/api/v1/testing/simulate-monime-webhook", json={
                "transaction_id": transaction_id,
                "status": status,
            }
        )


class WebhookSubscriptions(_Resource):
    def create(
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
        return self._t.request("POST", "/api/v1/webhooks/subscriptions", json=body)

    def list(self) -> Any:
        return self._t.request("GET", "/api/v1/webhooks/subscriptions")

    def update(
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
        return self._t.request(
            "PATCH", f"/api/v1/webhooks/subscriptions/{subscription_id}", json=body
        )

    def delete(self, subscription_id: str) -> Any:
        return self._t.request(
            "DELETE", f"/api/v1/webhooks/subscriptions/{subscription_id}"
        )

    def rotate_secret(self, subscription_id: str) -> Any:
        """Returns the new signing secret once."""
        return self._t.request(
            "POST", f"/api/v1/webhooks/subscriptions/{subscription_id}/rotate-secret"
        )


class Connect(_Resource):
    """Stripe Connect onboarding for user payout accounts."""

    def complete_onboarding(
        self,
        wallet_id: str,
        individual: dict,
        business_profile: dict,
        client_ip: str,
        card_token: Optional[str] = None,
    ) -> Any:
        """Submit identity + business details for the wallet owner's Connect
        account.

        client_ip must be the END CUSTOMER's IP address — Stripe records it
        as evidence of Terms-of-Service acceptance. Passing your server's IP
        is a compliance violation, so the SDK refuses to guess it.
        """
        if not client_ip:
            raise ValueError(
                "client_ip is required: Stripe records it for TOS acceptance "
                "and it must be the end customer's IP, not your server's"
            )
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/complete-onboarding/",
            json={
                "wallet_id": wallet_id,
                "individual": individual,
                "business_profile": business_profile,
                "card_token": card_token,
            },
            headers={"X-Forwarded-For": client_ip},
        )

    def upload_verification_document(
        self,
        wallet_id: str,
        document: Any,
        document_side: str,
        filename: str = "document.jpg",
        mime_type: str = "image/jpeg",
    ) -> Any:
        """Upload an identity document (JPEG/PNG/PDF, max 10 MB).

        document: bytes or a file-like object. document_side: 'front' | 'back'.
        """
        return self._t.request(
            "POST",
            f"/api/v1/transactions/wallet/{wallet_id}/connect/verification-document",
            data={"document_side": document_side},
            files={"file": (filename, document, mime_type)},
        )

    def status(self, wallet_id: str) -> Any:
        """Sync and return the Connect account's verification status."""
        return self._t.request(
            "GET", f"/api/v1/transactions/wallet/{wallet_id}/connect/status"
        )

    def delete(self, wallet_id: str) -> Any:
        return self._t.request(
            "POST",
            "/api/v1/transactions/wallet/connect/delete",
            params={"wallet_id": wallet_id},
        )
