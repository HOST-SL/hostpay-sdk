#!/usr/bin/env python3
"""Minimal AsyncHostPay walkthrough against a Test Mode instance.

Usage:
  HOSTPAY_BASE_URL=http://localhost:8082 \
  HOSTPAY_API_KEY=... HOSTPAY_SECRET_KEY=... \
  python examples/async_quickstart.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

from hostpay import AsyncHostPay  # noqa: E402


async def main() -> None:
    async with AsyncHostPay(
        api_key=os.environ["HOSTPAY_API_KEY"],
        secret_key=os.environ["HOSTPAY_SECRET_KEY"],
        base_url=os.environ.get("HOSTPAY_BASE_URL", "http://localhost:8082"),
    ) as client:
        user = await client.users.create(
            app_user_id=f"async-demo-{uuid.uuid4().hex[:8]}",
            name="Async Demo",
            phone_number="+23299000001",  # Test Mode: deposits auto-complete
        )
        wallet = await client.wallets.create(user.id)
        await client.deposits.mobile_money(wallet_id=wallet.id, amount=100)
        bal = await client.wallets.balance(wallet.id)
        print(f"user={user.id} wallet={wallet.id} balance={bal.balance}")


if __name__ == "__main__":
    asyncio.run(main())
