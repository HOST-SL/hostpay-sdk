"""Verify inbound HostPay webhooks.

HostPay signs each delivery with:
    X-Webhook-Timestamp: <unix seconds>
    X-HostPay-Signature: v1=<hex HMAC-SHA256( secret, "<timestamp>.<raw body>" )>

Pass the **raw** request body (bytes or str) exactly as received — not a
re-serialized dict — or the signature will not match.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Mapping, Union

from ._object import HostPayObject
from .errors import SignatureVerificationError

_SIG_HEADER = "x-hostpay-signature"
_TS_HEADER = "x-webhook-timestamp"


class Webhooks:
    def __init__(self, subscriptions: Any = None) -> None:
        # Subscription CRUD (client.webhooks.subscriptions.*) — injected by the
        # client so this module stays transport-free for bare construct_event use.
        self.subscriptions = subscriptions

    @staticmethod
    def construct_event(
        payload: Union[str, bytes],
        headers: Mapping[str, str],
        secret: str,
        tolerance: int = 300,
    ) -> Any:
        """Verify the signature and return the parsed event.

        Raises SignatureVerificationError on any mismatch or if the timestamp is
        older than `tolerance` seconds (replay protection; set 0 to disable).
        """
        body = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        lower = {k.lower(): v for k, v in headers.items()}

        timestamp = lower.get(_TS_HEADER)
        sig_header = lower.get(_SIG_HEADER)
        if not timestamp or not sig_header:
            raise SignatureVerificationError(
                "Missing X-Webhook-Timestamp or X-HostPay-Signature header"
            )

        signature = sig_header[3:] if sig_header.startswith("v1=") else sig_header

        expected = hmac.new(
            secret.encode("utf-8"),
            f"{timestamp}.{body}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise SignatureVerificationError("Signature mismatch")

        if tolerance:
            try:
                age = abs(time.time() - int(timestamp))
            except ValueError as exc:
                raise SignatureVerificationError("Invalid timestamp") from exc
            if age > tolerance:
                raise SignatureVerificationError(
                    f"Timestamp outside tolerance ({age:.0f}s > {tolerance}s)"
                )

        return HostPayObject(json.loads(body))
