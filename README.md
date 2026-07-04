# HostPay SDKs

Official client libraries for the HostPay API.

| Language | Status | Path |
| --- | --- | --- |
| Python | ✅ available — sync + async clients | [`python/`](python/) |
| TypeScript | ✅ available | [`typescript/`](typescript/) |

The SDKs are **hybrid**: a hand-written ergonomic client over the money surface
(users, wallets, deposits, transfers, payouts, escrow) plus webhook verification,
with strict response types generated from `openapi.json`.

Python 3.8–3.14 · Node 18+.

## Source of truth

[`openapi.json`](openapi.json) is the committed OpenAPI 3.1 spec both SDKs track.
It is **vendored** from the (private) HostPay API repo — regenerate it there and
copy it in; see [`PUBLISHING.md`](PUBLISHING.md).

## Releasing

See [`PUBLISHING.md`](PUBLISHING.md) — tag `python-vX.Y.Z` or `ts-vX.Y.Z` to
publish to PyPI / npm via GitHub Actions.
