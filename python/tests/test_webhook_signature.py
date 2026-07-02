import hashlib
import hmac
import json
import time

import pytest

from hostpay.errors import SignatureVerificationError
from hostpay.webhooks import Webhooks

SECRET = "whsec_test_secret"


def _sign(secret, ts, body):
    return hmac.new(
        secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256
    ).hexdigest()


def _headers(ts, body, secret=SECRET, prefix="v1="):
    return {
        "X-Webhook-Timestamp": ts,
        "X-HostPay-Signature": prefix + _sign(secret, ts, body),
    }


def test_valid_signature_parses_event():
    body = json.dumps({"event": "deposit.completed", "data": {"id": "txn_1"}})
    ts = str(int(time.time()))
    evt = Webhooks.construct_event(body, _headers(ts, body), SECRET)
    assert evt.event == "deposit.completed"
    assert evt.data.id == "txn_1"


def test_tampered_body_rejected():
    ts = str(int(time.time()))
    signed = json.dumps({"amount": 1})
    headers = _headers(ts, signed)
    with pytest.raises(SignatureVerificationError):
        Webhooks.construct_event(json.dumps({"amount": 1000000}), headers, SECRET)


def test_wrong_secret_rejected():
    body = json.dumps({"a": 1})
    ts = str(int(time.time()))
    with pytest.raises(SignatureVerificationError):
        Webhooks.construct_event(body, _headers(ts, body), "whsec_other")


def test_expired_timestamp_rejected():
    body = json.dumps({"a": 1})
    ts = str(int(time.time()) - 10_000)
    with pytest.raises(SignatureVerificationError):
        Webhooks.construct_event(body, _headers(ts, body), SECRET, tolerance=300)


def test_missing_headers_rejected():
    with pytest.raises(SignatureVerificationError):
        Webhooks.construct_event("{}", {}, SECRET)


def test_bytes_payload_and_no_prefix_and_lowercase_headers():
    body = json.dumps({"ok": True})
    ts = str(int(time.time()))
    headers = {
        "x-webhook-timestamp": ts,
        "x-hostpay-signature": _sign(SECRET, ts, body),  # no "v1=" prefix
    }
    evt = Webhooks.construct_event(body.encode("utf-8"), headers, SECRET)
    assert evt.ok is True
