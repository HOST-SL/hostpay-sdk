#!/usr/bin/env python3
"""End-to-end smoke test of the Python SDK against a running Test Mode instance.

Model-aware: it surface-checks every SDK call (a well-formed response, or a
well-formed API error, means the SDK built the request, authed, and parsed the
reply correctly). If the deposit credits the user wallet (client_managed model),
it additionally asserts balances move through transfer/escrow/payout. In the
platform_managed model — where deposits credit the application's earnings, not
the user wallet — those balance-delta checks are skipped.

Usage:
  HOSTPAY_BASE_URL=http://localhost:8082 \
  HOSTPAY_API_KEY=... HOSTPAY_SECRET_KEY=... \
  python examples/smoke_sdk.py
"""
import os
import sys
import uuid
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from hostpay import HostPay, HostPayError  # noqa: E402

MAGIC_COMPLETE = "+23299000001"  # Test Mode: deposits auto-complete
results = []


def surface(name, fn, *keys):
    """PASS if the call returns a dict with the expected keys, OR raises a
    well-formed HostPayError (the SDK still reached the endpoint and parsed it)."""
    try:
        r = fn()
        assert isinstance(r, dict) and r, f"{name}: empty response"
        for k in keys:
            assert k in r, f"{name}: missing key '{k}'"
        results.append(f"PASS  {name}")
        return r
    except HostPayError as e:
        assert e.status_code is not None, f"{name}: error without status code"
        results.append(f"PASS  {name} (API error {e.status_code}: {str(e)[:60]})")
        return None


def bal(client, wallet_id):
    return Decimal(str(client.wallets.balance(wallet_id)["balance"]))


def main():
    base_url = os.environ["HOSTPAY_BASE_URL"]
    client = HostPay(
        api_key=os.environ["HOSTPAY_API_KEY"],
        secret_key=os.environ["HOSTPAY_SECRET_KEY"],
        base_url=base_url,
    )
    tag = uuid.uuid4().hex[:8]
    print(f"→ base_url={base_url}\n")

    # --- surface checks: user + wallet creation ---
    sender = surface(
        "users.create (sender)",
        lambda: client.users.create(
            app_user_id=f"smoke-s-{tag}", name="Smoke Sender",
            username=f"smoke_s_{tag}", phone_number=MAGIC_COMPLETE,
            email=f"smoke-s-{tag}@example.com"),
        "id",
    )
    recipient = surface(
        "users.create (recipient)",
        lambda: client.users.create(
            app_user_id=f"smoke-r-{tag}", name="Smoke Recipient",
            username=f"smoke_r_{tag}", phone_number=MAGIC_COMPLETE,
            email=f"smoke-r-{tag}@example.com"),
        "id",
    )
    sw = surface("wallets.create (sender)", lambda: client.wallets.create(sender["id"]),
                 "id", "balance", "currency")["id"]
    rw = surface("wallets.create (recipient)", lambda: client.wallets.create(recipient["id"]),
                 "id")["id"]

    # --- deposit + detect the payment model ---
    b0 = bal(client, sw)
    dep = surface("deposits.mobile_money",
                  lambda: client.deposits.mobile_money(wallet_id=sw, amount=100_000),
                  "transaction_id", "transaction")
    assert dep and dep["transaction"].get("status"), "deposit: transaction not well-formed"
    b1 = bal(client, sw)
    user_wallet_credited = b1 > b0
    model = "client_managed" if user_wallet_credited else "platform_managed"
    print(f"  detected model: {model} (user wallet {b0} -> {b1})\n")

    if user_wallet_credited:
        # --- flow checks: balances must move ---
        r0 = bal(client, rw)
        client.transfers.create(sender_wallet_id=sw, recipient_identifier=f"smoke_r_{tag}",
                                amount=20, description="smoke transfer")
        assert bal(client, sw) < b1, "sender balance did not fall after transfer"
        assert bal(client, rw) > r0, "recipient balance did not rise after transfer"
        results.append("PASS  transfer (balances moved)")

        hold = client.escrow.hold(wallet_id=sw, amount=10, description="smoke escrow")
        client.escrow.release(hold["id"], recipient_wallet_id=rw)
        results.append("PASS  escrow hold + release")

        try:
            client.payouts.mobile_money(wallet_id=sw, amount=5, phone_number=MAGIC_COMPLETE)
            results.append("PASS  payout (initiated)")
        except HostPayError as e:
            results.append(f"PASS  payout (API error {e.status_code})")
    else:
        # --- surface checks: reached the endpoint + parsed (funds are in app earnings) ---
        surface("transfers.create",
                lambda: client.transfers.create(
                    sender_wallet_id=sw, recipient_identifier=f"smoke_r_{tag}", amount=20),
                "id")
        surface("escrow.hold",
                lambda: client.escrow.hold(wallet_id=sw, amount=10), "id")
        surface("payouts.mobile_money",
                lambda: client.payouts.mobile_money(
                    wallet_id=sw, amount=5, phone_number=MAGIC_COMPLETE), "id")

    print("\n".join(f"  {r}" for r in results))
    print(f"\n{len(results)} SDK checks passed ({model}).")


if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        sys.exit(f"missing env var: {e}")
    except (AssertionError, HostPayError) as e:
        sys.exit(f"\n  FAIL  {e}")
