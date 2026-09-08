---
name: integration-scaffolder
description: |
  Stamp out a new DEPLOY ADAPTER skeleton conforming to the deploy-adapter contract
  (.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md). Given an adapter name + a target,
  generates a new .claude/skills/deploy-<name>/ dir with the four required contract files
  (interface SKILL.md + adapter.py + investigation-reference.md + smoke_test.py) as fill-in
  stubs. Template-driven; deploy adapters only (SYS-066 scope).

  TRIGGER when: the operator wants to add a new coded deploy adapter / publishing target /
  deploy surface and needs the standard skeleton — "scaffold a deploy adapter for X",
  "add an integration for X", "new deploy adapter", "/integration-scaffolder".

  DO NOT TRIGGER for: cookbook (paste-instruction) deploys — use deploy-cookbook; non-deploy
  integrations; editing an existing adapter's logic.
---

# Integration Scaffolder (deploy adapters)

Stamps a new deploy adapter conforming to
[`ADAPTER-CONTRACT.md`](../deploy-cookbook/ADAPTER-CONTRACT.md).

## What it does

Runs `scaffold.py`, which reads the templates in `templates/` and writes a new
`.claude/skills/deploy-<name>/` directory containing the four contract files as stubs:

| File | Purpose |
|---|---|
| `SKILL.md` | interface — declared INPUTS/OUTPUTS(envelope)/deploy/verify/boundaries |
| `adapter.py` | implementation stub with an offline `--smoke-test` path + envelope |
| `investigation-reference.md` | captured-reference stub (how the target works) |
| `smoke_test.py` | offline smoke test asserting a well-formed envelope + no real deploy |

## How to run

```bash
cd ".claude/skills/integration-scaffolder"
python scaffold.py --name <adapter-name> --target "<human target description>"
```

Example:

```bash
python scaffold.py --name sharepoint --target "SharePoint Pages library"
```

Flags: `--dest <skills-dir>` (default: the skills dir this skill lives in) · `--force`
(overwrite an existing adapter dir). On success prints each created file path then `SCAFFOLD OK`.

## After scaffolding — fill in the stubs

The stub is not a working adapter. Fill, in order:
1. `investigation-reference.md` — investigate the target FIRST (mechanism, auth, verification).
2. `adapter.py` — real deploy logic + env-vars in `REQUIRED_ENV`.
3. `SKILL.md` — the TODO boundaries / steps.
4. Run `python smoke_test.py` until it passes.

Then register the platform in the tenant `integrations.yaml` (`has_adapter: true`).

## Reference implementation

`.claude/skills/deploy-static-folder/` is a COMPLETE adapter built to this contract (offline,
smoke-test-passing) — the worked example to copy patterns from.

## Cross-references

- `.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md` — the contract.
- `.claude/skills/deploy-static-folder/` — the reference adapter.
- `docs/specs/integrations.md` · `docs/specs/asset.md` §deployment.
