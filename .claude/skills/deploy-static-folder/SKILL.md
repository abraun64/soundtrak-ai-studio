---
name: deploy-static-folder
description: |
  Static-folder deploy adapter — deploys an asset's self-contained HTML deployment package
  (the folder holding index.html) to a local static-hosting folder by filesystem copy, then
  verifies index.html landed. Offline, no credentials. The REFERENCE implementation of the
  deploy-adapter contract (.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md).

  TRIGGER when: CM dispatches an Approved static-site asset with deployment.platform ==
  "static-folder" AND deployment.publish_method in [api, hybrid] AND tenant integrations.yaml
  has has_adapter: true for static-folder (deploy_root set in defaults).

  DO NOT TRIGGER when: publish_method == "cookbook" (use deploy-cookbook), has_adapter: false,
  or the asset is not an HTML deployment package (no index.html).
---

# Static-Folder Adapter (reference implementation)

Deploys an asset's HTML deployment package into a static-hosting folder. This is the worked
example proving the [deploy-adapter contract](../deploy-cookbook/ADAPTER-CONTRACT.md) end-to-end:
real deploy, real verification, offline smoke test. Copy its patterns when building the next
adapter.

## Declared INPUTS

- **Asset path** (from invoker prompt) — the deployment-package folder containing `index.html`
  (per `docs/specs/asset.md` §84-107). May also hold `asset.yaml`.
- Sibling **`asset.yaml` `deployment:` block** — `location`, `verification`, `deployment_notes`.
- Tenant **`integrations.yaml#platforms.static-folder`** — `defaults.deploy_root` (the target
  folder). Passed here as `--dest`. No credentials (offline target).

## Declared OUTPUTS — the adapter envelope

```json
{
  "status": "deployed | dry_run | aborted | failed",
  "platform": "static-folder",
  "target": "<destination folder>",
  "verification": {
    "automated": [ { "check": "index.html present at destination", "passed": true } ],
    "manual":    [ { "check": "Public URL returns 200", "operator_action": "…" } ]
  },
  "operator_action": "Static package deployed to <dest>. Point the host at this folder.",
  "notes": "<deployment_notes>"
}
```

## deploy step

Copy every entry of the package folder into `deploy_root` (`shutil.copy2` for files,
`shutil.copytree(dirs_exist_ok=True)` for subfolders). Idempotent; overwrites in place.

## verify step

Automated: assert `index.html` exists at the destination — drives envelope `status`. Manual: any
`deployment.verification` entry (e.g. public-URL-200) is returned for the operator.

## What this adapter does NOT do

- Perform any copy under `--smoke-test` / `--dry-run` (plan + verify only; status `dry_run`).
- Prune stale files at the destination on redeploy (documented in investigation-reference.md).
- Publish the folder to the internet — it copies to a folder; a host/CDN serves it.

## Failure modes

- Asset path missing → ABORT (exit 2).
- No `--dest` and no `deployment.location` → ABORT (exit 2).
- Package has no `index.html` on a real deploy → ABORT (exit 4) — not a deployable package.
- (Credentialled adapters: unset required env-var → ABORT + fall back to deploy-cookbook. This
  adapter has no required env-vars but keeps the check for parity.)

## How to run

```bash
# Offline smoke test (no args, no creds):
python smoke_test.py

# Dry-run against a real asset package (plan + verify, no copy):
python adapter.py --asset <package-folder> --smoke-test

# Real deploy:
python adapter.py --asset <package-folder> --dest <deploy_root>
```

## Cross-references

- `.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md` — the contract this proves.
- `.claude/skills/integration-scaffolder/` — scaffolds new adapters to that contract.
- `docs/specs/asset.md` §deployment · §84-107 (HTML package) · `docs/specs/integrations.md`.
- `investigation-reference.md` (sibling) — how the target works.
