"""Response models (TypedDict) mirroring the OpenAPI schemas.

Compile-time only: responses are returned as dict-like ``HostPayObject`` at
runtime, which is structurally these types. Access typed fields with
``resp["field"]`` (attribute access ``resp.field`` also works at runtime).

Fields mirror ../../openapi.json — the source of truth. Regenerate/refresh when
the API changes.
"""
from __future__ import annotations

from typing import Optional, TypedDict


class _UserRequired(TypedDict):
    id: str
    app_user_id: str
    name: str
    phone_number: str
    created_at: str


class UserRead(_UserRequired, total=False):
    email: Optional[str]
    username: Optional[str]
    is_active: bool
    stripe_connect_account_id: Optional[str]
    stripe_connect_verified: Optional[bool]


class _WalletRequired(TypedDict):
    id: str
    user_id: str
    balance: str
    currency: str
    created_at: str
    updated_at: str


class WalletRead(_WalletRequired, total=False):
    is_active: bool


class _TransactionRequired(TypedDict):
    id: str
    amount: str
    transaction_type: str
    payment_method: str
    status: str
    live_mode: bool
    timestamp: str
    created_at: str
    updated_at: str


class TransactionResponse(_TransactionRequired, total=False):
    currency: Optional[str]
    description: Optional[str]
    reference_id: Optional[str]
    wallet_id: Optional[str]
    recipient_wallet_id: Optional[str]
    amount_in_base_currency: Optional[str]
    application_fee: Optional[str]
    platform_fee: Optional[str]
    monime_fee: Optional[str]
    stripe_fee: Optional[str]
    estimated_monime_fee: Optional[str]
    estimated_stripe_fee: Optional[str]
    total_amount_paid: Optional[str]
    escrow_amount: Optional[str]
    escrow_wallet_id: Optional[str]
    order_id: Optional[str]


class _EscrowRequired(TypedDict):
    id: str
    wallet_id: str
    escrow_wallet_id: str
    amount: float
    escrow_amount: float
    status: str
    transaction_type: str
    created_at: str
    updated_at: str


class EscrowResponse(_EscrowRequired, total=False):
    recipient_wallet_id: Optional[str]
    application_wallet_id: Optional[str]
    application_fee: Optional[float]
    description: Optional[str]
