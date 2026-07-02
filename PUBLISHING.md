# Publishing the SDKs

This is the standalone SDK repo (`HOST-SL/hostpay-sdk`). Releases are automated
by GitHub Actions, triggered by pushing a version tag:

| Package | Registry | Tag pattern | Workflow |
| --- | --- | --- | --- |
| `hostpay` (Python) | PyPI | `python-vX.Y.Z` | `.github/workflows/publish-python.yml` |
| `@hostpay/sdk` (TS) | npm | `ts-vX.Y.Z` | `.github/workflows/publish-npm.yml` |

Each workflow verifies the tag matches the package version, runs the tests, then
publishes. **Nothing publishes until you push a tag** and complete the one-time
setup below.

## One-time setup

### 0. Claim the names

- PyPI: confirm **`hostpay`** is available (https://pypi.org/project/hostpay/).
- npm: create the **`@hostpay`** org (free for public packages) at
  https://www.npmjs.com/org/create, or change the name in
  `typescript/package.json`.

### 1. PyPI — Trusted Publishing (no token)

On PyPI → your project → *Publishing*, add a **pending trusted publisher**:

- Owner: `HOST-SL` · Repository: `hostpay-sdk`
- Workflow: `publish-python.yml`
- Environment: `pypi`

Then in GitHub → *Settings → Environments*, create an environment named
**`pypi`** (optionally add required reviewers to gate releases).

### 2. npm — automation token

1. npm → *Access Tokens* → **Generate → Automation** token.
2. GitHub → *Settings → Secrets and variables → Actions* → add secret
   **`NPM_TOKEN`**.

## Cutting a release

1. Bump the version in the package you're releasing:
   - Python: `python/pyproject.toml` → `version`
   - TS: `typescript/package.json` → `version`
2. Commit, then tag and push:
   ```bash
   git tag python-v0.1.0 && git push origin python-v0.1.0   # Python
   git tag ts-v0.1.0     && git push origin ts-v0.1.0       # TypeScript
   ```
3. Watch the Actions run. Versions are independent per package.

## The OpenAPI spec

`openapi.json` is **vendored** — the private API lives in another repo. When the
API changes, regenerate it there and copy it in:

```bash
# in the API repo
python wallet-system/scripts/dump_openapi.py
# then copy wallet-system/../sdk/openapi.json -> this repo's openapi.json
(cd typescript && npm run generate)   # refresh TS types
```

## Manual publish (fallback)

```bash
# Python
cd python && python -m pip install build twine
python -m build && twine upload dist/*

# TypeScript
cd typescript && npm login && npm publish
```
