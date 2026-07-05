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


def test_users_list_passes_query_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json=[{"id": "usr_1"}])

    client = _client(handler)
    users = client.users.list(is_active=True)
    assert seen["path"] == "/api/v1/users/"
    assert seen["query"] == {"is_active": "true"}
    assert users[0]["id"] == "usr_1"


def test_users_update_sends_full_body():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "usr_1"})

    client = _client(handler)
    client.users.update(
        "usr_1", app_user_id="u1", name="New Name", phone_number="+232"
    )
    assert (seen["method"], seen["path"]) == ("PUT", "/api/v1/users/usr_1/")
    assert seen["body"]["name"] == "New Name"


def test_lifecycle_and_transactions_paths():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, dict(request.url.params)))
        return httpx.Response(200, json={})

    client = _client(handler)
    client.users.delete("u1")
    client.users.disable("u1")
    client.users.enable("u1")
    client.wallets.disable("w1")
    client.wallets.enable("w1")
    client.transactions.get("t1")
    client.transactions.for_wallet("w1")
    client.transactions.list(status="completed", limit=10)

    assert calls == [
        ("DELETE", "/api/v1/users/u1/", {}),
        ("POST", "/api/v1/users/u1/disable", {}),
        ("POST", "/api/v1/users/u1/enable", {}),
        ("POST", "/api/v1/wallets/w1/disable", {}),
        ("POST", "/api/v1/wallets/w1/enable", {}),
        ("GET", "/api/v1/transactions/t1", {}),
        ("GET", "/api/v1/transactions/wallet/w1", {}),
        ("GET", "/api/v1/transactions/", {"status": "completed", "limit": "10", "offset": "0"}),
    ]


def test_wallets_list_passes_query_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = dict(request.url.params)
        return httpx.Response(200, json=[{"id": "w1", "balance": "5.00"}])

    client = _client(handler)
    wallets = client.wallets.list(is_active=True)
    assert seen["path"] == "/api/v1/wallets/"
    assert seen["query"] == {"is_active": "true"}
    assert wallets[0]["id"] == "w1"


def test_escrow_methods_forward_idempotency_key():
    """Fataba report: escrow is money-moving, so retried POSTs must carry the
    caller's Idempotency-Key like deposits/transfers/payouts do."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.headers.get("Idempotency-Key")))
        return httpx.Response(200, json={"id": "esc_1"})

    client = _client(handler)
    client.escrow.hold(wallet_id="w1", amount=10, idempotency_key="hold-1")
    client.escrow.release("esc_1", recipient_wallet_id="w2", idempotency_key="rel-1")
    client.escrow.refund("esc_1", idempotency_key="ref-1")

    assert seen == [
        ("/api/v1/escrow/hold", "hold-1"),
        ("/api/v1/escrow/esc_1/release", "rel-1"),
        ("/api/v1/escrow/esc_1/refund", "ref-1"),
    ]


def test_fees_resource_paths_and_bodies():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))
        return httpx.Response(200, json={})

    client = _client(handler)
    client.fees.summary()
    client.fees.configuration()
    client.fees.estimate_deposit(amount=100, payment_method="card", is_international=True)
    client.fees.estimate_withdrawal(amount=50, payment_method="mobile_money")
    client.fees.estimate_transfer(amount=25)
    client.fees.estimate_card_metadata(payment_method_id="pm_1", amount=75)

    assert calls == [
        ("GET", "/api/v1/fees/summary", None),
        ("GET", "/api/v1/fees/configuration", None),
        ("POST", "/api/v1/fees/estimate/deposit",
         {"amount": 100, "payment_method": "card", "is_international": True}),
        ("POST", "/api/v1/fees/estimate/withdrawal",
         {"amount": 50, "payment_method": "mobile_money"}),
        ("POST", "/api/v1/fees/estimate/transfer", {"amount": 25}),
        ("POST", "/api/v1/fees/estimate/deposit/card-metadata",
         {"payment_method_id": "pm_1", "amount": 75}),
    ]


def test_transactions_sync_and_testing_simulator():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))
        return httpx.Response(200, json={})

    client = _client(handler)
    client.transactions.sync("mnm_ref_123")
    client.testing.simulate_monime_webhook("txn_1")  # default: successful
    client.testing.simulate_monime_webhook("txn_2", status="failed")

    assert calls == [
        ("POST", "/api/v1/transactions/sync/mnm_ref_123", None),
        ("POST", "/api/v1/testing/simulate-monime-webhook",
         {"transaction_id": "txn_1", "status": "successful"}),
        ("POST", "/api/v1/testing/simulate-monime-webhook",
         {"transaction_id": "txn_2", "status": "failed"}),
    ]


def test_webhook_subscriptions_crud():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        calls.append((request.method, request.url.path, body))
        return httpx.Response(200, json={})

    client = _client(handler)
    subs = client.webhooks.subscriptions
    subs.create(target_url="https://f.example/hook", events=["payout.failed"])
    subs.list()
    subs.update("sub_1", active=False)  # only provided fields go on the wire
    subs.rotate_secret("sub_1")
    subs.delete("sub_1")

    assert calls == [
        ("POST", "/api/v1/webhooks/subscriptions",
         {"target_url": "https://f.example/hook", "events": ["payout.failed"]}),
        ("GET", "/api/v1/webhooks/subscriptions", None),
        ("PATCH", "/api/v1/webhooks/subscriptions/sub_1", {"active": False}),
        ("POST", "/api/v1/webhooks/subscriptions/sub_1/rotate-secret", None),
        ("DELETE", "/api/v1/webhooks/subscriptions/sub_1", None),
    ]
    # construct_event stays available on the same namespace.
    assert callable(client.webhooks.construct_event)


def test_app_info_appended_to_user_agent():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["ua"] = request.headers["User-Agent"]
        return httpx.Response(200, json={})

    mock = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://api.test", transport=mock)
    client = HostPay(
        api_key="ak-x", secret_key="sk-y", http_client=http,
        app_info="Fataba-Platform/1.0",
    )
    client.fees.summary()
    assert seen["ua"].startswith("hostpay-python/")
    assert seen["ua"].endswith(" Fataba-Platform/1.0")


def test_users_patch_sends_only_provided_fields():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "usr_1"})

    client = _client(handler)
    client.users.patch("usr_1", name="New Name", is_active=False)
    assert seen["method"] == "PATCH"
    assert seen["path"] == "/api/v1/users/usr_1/"
    assert seen["body"] == {"name": "New Name", "is_active": False}


def test_connect_onboarding_requires_and_forwards_client_ip():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["xff"] = request.headers.get("X-Forwarded-For")
        seen["body"] = json.loads(request.content)
        seen["path"] = request.url.path
        return httpx.Response(200, json={"account_id": "acct_1"})

    client = _client(handler)
    client.connect.complete_onboarding(
        wallet_id="w1",
        individual={"first_name": "Alice", "address": {"country": "SL"}},
        business_profile={"mcc": "5734"},
        client_ip="41.223.10.5",
    )
    assert seen["path"] == "/api/v1/transactions/wallet/complete-onboarding/"
    assert seen["xff"] == "41.223.10.5"
    assert seen["body"]["wallet_id"] == "w1"

    # the SDK must refuse to guess the TOS-acceptance IP
    with pytest.raises(ValueError):
        client.connect.complete_onboarding(
            wallet_id="w1", individual={}, business_profile={}, client_ip="",
        )


def test_connect_document_upload_is_multipart():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content_type"] = request.headers.get("Content-Type", "")
        seen["body"] = request.content
        seen["path"] = request.url.path
        return httpx.Response(200, json={"payouts_enabled": False})

    client = _client(handler)
    client.connect.upload_verification_document(
        wallet_id="w1",
        document=b"%PDF-1.4 fake",
        document_side="front",
        filename="passport.pdf",
        mime_type="application/pdf",
    )
    assert seen["path"] == "/api/v1/transactions/wallet/w1/connect/verification-document"
    assert seen["content_type"].startswith("multipart/form-data")
    assert b'name="document_side"' in seen["body"] and b"front" in seen["body"]
    assert b"passport.pdf" in seen["body"] and b"%PDF-1.4 fake" in seen["body"]


def test_connect_status_and_delete_paths():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path, dict(request.url.params)))
        return httpx.Response(200, json={})

    client = _client(handler)
    client.connect.status("w1")
    client.connect.delete("w1")
    assert calls == [
        ("GET", "/api/v1/transactions/wallet/w1/connect/status", {}),
        ("POST", "/api/v1/transactions/wallet/connect/delete", {"wallet_id": "w1"}),
    ]
