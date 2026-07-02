# Publishing the SDKs

Releases are automated by GitHub Actions, triggered by pushing a version tag:

| Package | Registry | Tag pattern | Workflow |
| --- | --- | --- | --- |
| `hostpay` (Python) | PyPI | `sdk-python-vX.Y.Z` | `.github/workflows/publish-python.yml` |
| `@hostpay/sdk` (TS) | npm | `sdk-ts-vX.Y.Z` | `.github/workflows/publish-npm.yml` |

Each workflow verifies the tag matches the package version, runs the tests, then
publishes. **Nothing publishes until you push a tag** and complete the one-time
setup below.

## One-time setup

### 0. Claim the names

- PyPI: confirm **`hostpay`** is available (https://pypi.org/project/hostpay/).
- npm: create the **`@hostpay`** org (free for public packages) at
  https://www.npmjs.com/org/create, or change the name in
  `sdk/typescript/package.json`.

### 1. PyPI — Trusted Publishing (no token)

On PyPI → your project → *Publishing*, add a **pending trusted publisher**:

- Owner: `HOST-SL` · Repository: `host_pay`
- Workflow: `publish-python.yml`
- Environment: `pypi`

Then in GitHub → *Settings → Environments*, create an environment named
**`pypi`** (optionally add required reviewers to gate releases).

### 2. npm — automation token

1. npm → *Access Tokens* → **Generate → Automation** token.
2. GitHub → *Settings → Secrets and variables → Actions* → add secret
   **`NPM_TOKEN`** with that value.

(Publishing uses `--provenance`; the workflow already requests the needed
`id-token` permission.)

## Cutting a release

1. If the API changed, regenerate the spec and TS types:
   ```bash
   python wallet-system/scripts/dump_openapi.py
   (cd sdk/typescript && npm run generate)
   ```
2. Bump the version in the package you're releasing:
   - Python: `sdk/python/pyproject.toml` → `version`
   - TS: `sdk/typescript/package.json` → `version`
3. Commit, then tag and push:
   ```bash
   # Python
   git tag sdk-python-v0.1.0 && git push origin sdk-python-v0.1.0
   # TypeScript
   git tag sdk-ts-v0.1.0 && git push origin sdk-ts-v0.1.0
   ```
4. Watch the Actions run. Versions are independent per package.

## Manual publish (fallback)

```bash
# Python
cd sdk/python && python -m pip install build twine
python -m build && twine upload dist/*

# TypeScript
cd sdk/typescript && npm login && npm publish
```

## First release note

For PyPI Trusted Publishing you may need to create the project with one manual
`twine upload` before the pending publisher activates — or use PyPI's
"pending publisher" flow, which creates the project on the first CI publish.
