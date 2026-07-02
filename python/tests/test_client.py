import json

import httpx
import pytest

from hostpay import AuthenticationError, HostPay, InvalidRequestError


def _client(handler):
    """A HostPay client whose HTTP layer is a MockTransport running `handler`."""
    mock = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://api.test", transport=mock)
    return HostPay(api_key="ak-x", secret_key="sk-y", http_client=http)


def test_auth_headers_and_path_and_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["api-key"] = request.headers.get("api-key")
        seen["secret-key"] = request.headers.get("secret-key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": "usr_1", "name": "Alice"})

    client = _client(handler)
    user = client.users.create(app_user_id="u1", name="Alice", phone_number="+23279000000")

    assert seen["path"] == "/api/v1/users/create/"
    assert seen["api-key"] == "ak-x" and seen["secret-key"] == "sk-y"
    assert seen["body"]["app_user_id"] == "u1"
    assert user.id == "usr_1"  # attribute access on the response


def test_idempotency_key_forwarded():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["idem"] = request.headers.get("Idempotency-Key")
        return httpx.Response(200, json={"transaction_id": "txn_1"})

    client = _client(handler)
    client.deposits.mobile_money(wallet_id="w1", amount=100, idempotency_key="abc-123")
    assert seen["idem"] == "abc-123"


def test_error_mapping():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"detail": "Invalid credentials"})

    client = _client(handler)
    with pytest.raises(AuthenticationError) as exc:
        client.wallets.balance("w1")
    assert exc.value.status_code == 403
    assert "Invalid credentials" in str(exc.value)


def test_validation_error_is_invalid_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "bad amount"})

    client = _client(handler)
    with pytest.raises(InvalidRequestError):
        client.payouts.mobile_money(wallet_id="w1", amount=-5, phone_number="+232")
