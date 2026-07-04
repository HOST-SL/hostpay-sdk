"""HTTP transport + the top-level HostPay client."""
from __future__ import annotations

import time
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from typing import Any, Dict, Optional

import httpx

from ._object import HostPayObject, _wrap
from .errors import APIConnectionError, error_from_status
from .resources import (
    Deposits,
    Escrow,
    Payouts,
    Transactions,
    Transfers,
    Users,
    Wallets,
)
from .webhooks import Webhooks

DEFAULT_BASE_URL = "https://hpay-api.host-sl.com"

# Single-sourced from pyproject.toml via the installed package metadata, so it
# can never drift from the released version again.
try:
    _VERSION = _pkg_version("hostpay")
except PackageNotFoundError:  # uninstalled source checkout
    _VERSION = "0.0.0.dev0"


class _Transport:
    """Builds authenticated requests, retries transient failures, maps errors."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        http_client: Optional[httpx.Client],
    ) -> None:
        self._max_retries = max_retries
        # Auth is applied per-request so a caller-supplied http_client is still
        # authenticated.
        self._auth = {
            "api-key": api_key,
            "secret-key": secret_key,
            "User-Agent": f"hostpay-python/{_VERSION}",
        }
        self._client = http_client or httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout
        )

    def request(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        headers: Dict[str, str] = dict(self._auth)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        # Retry only idempotent-safe conditions: connection errors and 5xx. POSTs
        # are retried too — the API supports Idempotency-Key for money movements.
        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._client.request(
                    method, path, json=json, params=params, headers=headers
                )
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(0.5 * (2 ** attempt))
                    continue
                raise APIConnectionError(f"Could not reach HostPay: {exc}") from exc

            if resp.status_code >= 500 and attempt < self._max_retries:
                time.sleep(0.5 * (2 ** attempt))
                continue
            return _handle_response(resp)
        raise APIConnectionError(f"Could not reach HostPay: {last_exc}")

    def close(self) -> None:
        self._client.close()


def _handle_response(resp: "httpx.Response") -> Any:
    if 200 <= resp.status_code < 300:
        if not resp.content:
            return None
        return _wrap(resp.json())
    try:
        body = resp.json()
        detail = body.get("detail", body) if isinstance(body, dict) else body
    except ValueError:
        detail = resp.text
    message = detail if isinstance(detail, str) else f"HTTP {resp.status_code}"
    raise error_from_status(resp.status_code, message, detail)


class HostPay:
    """HostPay API client.

    >>> client = HostPay(api_key="ak-...", secret_key="sk-...")
    >>> user = client.users.create(app_user_id="u1", name="Alice", phone_number="+23279000000")
    >>> wallet = client.wallets.create(user.id)
    >>> client.deposits.mobile_money(wallet_id=wallet.id, amount=100)
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key or not secret_key:
            raise ValueError("api_key and secret_key are required")
        self._transport = _Transport(
            api_key, secret_key, base_url, timeout, max_retries, http_client
        )
        self.users = Users(self._transport)
        self.wallets = Wallets(self._transport)
        self.deposits = Deposits(self._transport)
        self.transfers = Transfers(self._transport)
        self.transactions = Transactions(self._transport)
        self.payouts = Payouts(self._transport)
        self.escrow = Escrow(self._transport)
        self.webhooks = Webhooks()

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "HostPay":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
