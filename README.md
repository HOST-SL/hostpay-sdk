# HostPay SDKs

Official client libraries for the HostPay API.

| Language | Status | Path |
| --- | --- | --- |
| Python | ✅ available | [`python/`](python/) |
| TypeScript | ✅ available | [`typescript/`](typescript/) |

## Source of truth

[`openapi.json`](openapi.json) is the committed OpenAPI 3.1 spec both SDKs track.
Regenerate it after API changes:

```bash
python wallet-system/scripts/dump_openapi.py
```

The SDKs are **hybrid**: a hand-written ergonomic client over the money surface
(users, wallets, deposits, transfers, payouts, escrow) plus webhook verification,
with strict response types generated from `openapi.json`.

## Releasing

See [`PUBLISHING.md`](PUBLISHING.md) — tag `sdk-python-vX.Y.Z` or `sdk-ts-vX.Y.Z`
to publish to PyPI / npm via GitHub Actions.
