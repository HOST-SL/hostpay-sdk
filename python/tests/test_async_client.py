"""Async client tests — mirrors test_client.py through AsyncHostPay.

Runs each case with asyncio.run() inside a plain sync test, so no
pytest-asyncio dependency (works unchanged on Python 3.8–3.14).
"""
import asyncio
import inspect
import json

import httpx
import pytest

from hostpay import AsyncHostPay, AuthenticationError, InvalidRequestError
from hostpay import _async_resources, resources


def _client(handler):
    """An AsyncHostPay client whose HTTP layer is a MockTransport running `handler`."""
    mock = httpx.MockTransport(handler)
    http = httpx.AsyncClient(base_url="https://api.test", transport=mock)
    return AsyncHostPay(api_key="ak-x", secret_key="sk-y", http_client=http)


def test_auth_headers_and_path_and_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["api-key"] = request.headers.get("api-key")
        seen["secret-key"] = request.headers.get("secret-key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": "usr_1", "name": "Alice"})

    async def case():
        async with _client(handler) as client:
            return await client.users.create(
                app_user_id="u1", name="Alice", phone_number="+23279000000"
            )

    user = asyncio.run(case())
    assert seen["path"] == "/api/v1/users/create/"
    assert seen["api-key"] == "ak-x" and seen["secret-key"] == "sk-y"
    assert seen["body"]["app_user_id"] == "u1"
    assert user.id == "usr_1"  # attribute access on the response


def test_idempotency_key_forwarded():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["idem"] = request.headers.get("Idempotency-Key")
        return httpx.Response(200, json={"transaction_id": "txn_1"})

    async def case():
        async with _client(handler) as client:
            await client.deposits.mobile_money(
                wallet_id="w1", amount=100, idempotency_key="abc-123"
            )

    asyncio.run(case())
    assert seen["idem"] == "abc-123"


def test_error_mapping():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "Invalid credentials"})

    async def case():
        async with _client(handler) as client:
            await client.wallets.balance("w1")

    with pytest.raises(AuthenticationError) as exc:
        asyncio.run(case())
    assert exc.value.status_code == 403
    assert "Invalid credentials" in str(exc.value)


def test_validation_error_is_invalid_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "bad amount"})

    async def case():
        async with _client(handler) as client:
            await client.payouts.mobile_money(
                wallet_id="w1", amount=-5, phone_number="+232"
            )

    with pytest.raises(InvalidRequestError):
        asyncio.run(case())


def test_query_params_and_list_response():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json=[{"id": "usr_1"}])

    async def case():
        async with _client(handler) as client:
            return await client.users.list(is_active=True)

    users = asyncio.run(case())
    assert seen["path"] == "/api/v1/users/"
    assert seen["query"] == {"is_active": "true"}
    assert users[0]["id"] == "usr_1"


def test_retries_5xx_then_succeeds():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(502, json={"detail": "bad gateway"})
        return httpx.Response(200, json={"balance": "5.00"})

    async def case():
        async with _client(handler) as client:
            return await client.wallets.balance("w1")

    bal = asyncio.run(case())
    assert len(calls) == 2
    assert bal["balance"] == "5.00"


def test_async_resources_mirror_sync():
    """The async module must expose the same classes, methods, and signatures
    as the sync one — this is the guard that keeps the two copies in step."""
    sync_classes = {
        n: c
        for n, c in vars(resources).items()
        if inspect.isclass(c) and not n.startswith("_") and c.__module__ == resources.__name__
    }
    assert sync_classes, "no sync resource classes found"
    for name, sync_cls in sync_classes.items():
        async_cls = getattr(_async_resources, name, None)
        assert async_cls is not None, f"missing async twin for {name}"
        sync_methods = {
            n: f for n, f in inspect.getmembers(sync_cls, inspect.isfunction)
            if not n.startswith("_")
        }
        async_methods = {
            n: f for n, f in inspect.getmembers(async_cls, inspect.isfunction)
            if not n.startswith("_")
        }
        assert sync_methods.keys() == async_methods.keys(), name
        for meth, sync_fn in sync_methods.items():
            assert inspect.iscoroutinefunction(async_methods[meth]), f"{name}.{meth} not async"
            assert inspect.signature(sync_fn) == inspect.signature(async_methods[meth]), (
                f"{name}.{meth} signature drifted"
            )
