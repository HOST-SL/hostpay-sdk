# HostPay SDKs

Official client libraries for the HostPay API.

| Language | Status | Path |
| --- | --- | --- |
| Python | ✅ available | [`python/`](python/) |
| TypeScript | ⏳ planned | `typescript/` |

## Source of truth

[`openapi.json`](openapi.json) is the committed OpenAPI 3.1 spec both SDKs track.
Regenerate it after API changes:

```bash
python wallet-system/scripts/dump_openapi.py
```

The SDKs are **hybrid**: a hand-written ergonomic client over the money surface
(users, wallets, deposits, transfers, payouts, escrow) plus webhook verification.
Strict typed models can be generated from `openapi.json` when needed.
