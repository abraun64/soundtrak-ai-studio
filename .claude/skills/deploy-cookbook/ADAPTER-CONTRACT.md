# Deploy-Adapter Contract

**Spec version**: v1 · Authored 2026-07-14 (SYS-066).

The **standard shape every coded deploy adapter in this system must conform to.** A "deploy
adapter" is a `.claude/skills/deploy-<platform>/` skill that pushes an Approved asset to one
external publishing target (email, static site, intranet, social, print, drive, API).

Prior art this contract generalises: `.claude/skills/deploy-mailchimp/` (API adapter) and
`.claude/skills/publish-soundtrak-article-website/` (git-push adapter). The cookbook generator
(`.claude/skills/deploy-cookbook/SKILL.md`) is the **fallback** for any platform WITHOUT a
coded adapter; a coded adapter is what this contract standardises.

Anchoring principle: **prove the contract with ONE real adapter, don't build a framework ahead
of need.** New adapters are added one at a time, each conforming here, each with a passing smoke
test before it ships.

---

## What every deploy adapter MUST provide

A conforming adapter directory (`.claude/skills/deploy-<name>/`) contains **four required files**:

### 1. `SKILL.md` — the interface

The declared contract Claude reads. MUST contain, in frontmatter + body:

- **Frontmatter** `name` (= `deploy-<name>`) and a `description` with an explicit
  **TRIGGER when** clause and a **DO NOT TRIGGER when** clause (matching the deploy-mailchimp
  shape), so CM dispatches it correctly.
- **Declared INPUTS** — what the adapter reads:
  - the asset path (from the invoker prompt),
  - the sibling `asset.yaml` `deployment:` block (`platform`, `publish_method`, `location`,
    `format_requirements`, `verification`, `deployment_notes` — per `docs/specs/asset.md`),
  - the tenant `integrations.yaml#platforms[<platform>]` config (`has_adapter`, `credentials`
    as `${ENV_VAR}` refs, `defaults`) — per `docs/specs/integrations.md`.
- **Declared OUTPUTS** — the **adapter envelope** (see below) it returns to CM.
- **A `deploy` step** — the action that pushes the asset to the target.
- **A `verify` step** — runs the asset's `deployment.verification` checks (automated ones
  execute here; manual ones are returned for the operator).
- **A "does NOT do" section** — hard boundaries (e.g. "does not click Send", "does not
  perform the live production deploy without an explicit flag").
- **Failure modes** — at minimum: missing/unset credentials → ABORT + cookbook fallback;
  malformed asset → error, no partial deploy.
- **Cross-references** — the specs + the cookbook fallback.

### 2. `adapter.py` — the tested implementation

The actual push logic. MUST:

- Resolve credentials from env-vars at runtime (`os.environ.get`) — **never** literal secrets.
- ABORT cleanly (non-zero exit, diagnostic on stderr) if a required env-var is unset, and
  signal the caller to fall back to `deploy-cookbook`.
- Read the `deployment:` block + `integrations.yaml` platform config as declared in SKILL.md.
- Expose a `--dry-run` / `--smoke-test` path that exercises the full input→plan→verify flow
  WITHOUT performing a real external network deploy (so the smoke test is offline-verifiable).
- Print the **adapter envelope** (JSON, see below) to stdout on success.

### 3. `investigation-reference.md` — the captured reference

How the target actually works, captured once so the next person doesn't re-investigate. MUST
cover: the deploy mechanism (API endpoints / CLI / git-push / file-drop), auth model + the exact
env-vars, the request/response or file-layout shape, verification signals (how you know it
landed), known gotchas, and links to official docs. For an offline target, document the on-disk
contract instead of an API.

### 4. `smoke_test.py` — the smoke test

A self-contained, offline, zero-config test proving the adapter conforms. MUST:

- Run with no credentials and no network (`python smoke_test.py`), exit `0` on pass, non-zero
  on fail, and print a one-line PASS/FAIL summary.
- Build a throwaway fixture asset (asset.yaml `deployment:` block + a rendered file) in a temp
  dir, invoke the adapter in dry-run/smoke mode, and assert:
  1. the adapter reads the `deployment:` block + platform config without error,
  2. it emits a well-formed **adapter envelope** with the required keys,
  3. `verify` reports the asset's verification checks (splitting automated vs manual),
  4. no real external network deploy happened.
- Clean up its temp fixtures.

---

## The adapter envelope (standard OUTPUT)

Every adapter returns a JSON object to CM with **at least** these keys:

```json
{
  "status": "deployed | draft_created | dry_run | aborted | failed",
  "platform": "<platform key>",
  "target": "<where it went / would go — url, path, campaign id>",
  "verification": {
    "automated": [ { "check": "...", "passed": true } ],
    "manual":    [ { "check": "...", "operator_action": "..." } ]
  },
  "operator_action": "<the one next thing the operator must do, or ''>",
  "notes": "<deployment_notes echoed + any adapter remarks>"
}
```

`status: dry_run` is what a `--smoke-test`/`--dry-run` invocation returns — a real deploy was
NOT performed.

---

## Conformance checklist (what the scaffolder stamps + the smoke test proves)

- [ ] Four required files present: `SKILL.md`, `adapter.py`, `investigation-reference.md`, `smoke_test.py`.
- [ ] `SKILL.md` declares INPUTS, OUTPUTS (envelope), a `deploy` step + a `verify` step, boundaries, failure modes.
- [ ] `SKILL.md` frontmatter has TRIGGER / DO NOT TRIGGER clauses.
- [ ] `adapter.py` resolves creds from env-vars, has a `--smoke-test`/`--dry-run` offline path, prints the envelope.
- [ ] `investigation-reference.md` documents mechanism + auth + verification + gotchas.
- [ ] `smoke_test.py` runs offline with no creds, exits 0 on pass, and asserts a well-formed envelope + no real deploy.

---

## Cross-references

- `.claude/skills/deploy-cookbook/SKILL.md` — the cookbook FALLBACK for platforms with no coded adapter.
- `.claude/skills/deploy-mailchimp/` — prior-art API adapter (schema stage).
- `.claude/skills/publish-soundtrak-article-website/` — prior-art git-push adapter (working).
- `.claude/skills/deploy-static-folder/` — the reference adapter proving THIS contract end-to-end.
- `.claude/skills/integration-scaffolder/` — stamps a new adapter skeleton conforming to this contract.
- `docs/specs/integrations.md` — tenant `integrations.yaml` schema (platform config the adapter reads).
- `docs/specs/asset.md` §deployment — per-asset `deployment:` block the adapter consumes.
