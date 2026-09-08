---
name: agent-io
description: |
  Validates the agent I/O contract (SYS-004) — the structured envelope that now rides
  ALONGSIDE each agent's prose return. CM runs `validate_envelope.py` on every return
  before acting on it: checks dispatch_id pairing, a valid status, the per-agent required
  fields on `delivered` (Producer artifacts + self-QA + content-subedit; Governance/Brand
  verdict + audit_ref; CD/Insights/Forensic artifacts), and that every ship:true artifact
  EXISTS on disk (reusing the SYS-003 gallery ship-file check). Additive + non-breaking:
  prose is still read during rollout; this never parses or retires prose.

  TRIGGER when: a subagent returns and CM needs to gate on the envelope before acting;
  "validate the envelope", "check the agent return"; inside a smoke test / hook that
  wants to confirm dispatch↔return integrity.

  DO NOT TRIGGER for: cost capture (use cost-ledger), gallery ship-existence on its own
  (use asset-gallery --check), or asset-status drift (use check-state).
---

# agent-io — the agent I/O contract validator (SYS-004)

Spec: [`docs/specs/agent-io-contract.md`](../../../docs/specs/agent-io-contract.md). This skill
implements **Steps 2-3 of §6** — agents EMIT a structured `return:` envelope alongside their
existing prose, and CM VALIDATES it at the boundary before acting. It is **additive and
non-breaking**: the asset content, the Per-Step Brief body, and the agents' prose returns are
all unchanged; nothing breaks if an envelope is missing. Retiring prose-parsing is the spec's
future gated Step 4 — not this skill.

## What it validates (agent-io-contract.md §5)

1. **`dispatch_id`** present — and matches the dispatch's `id` when a dispatch is supplied.
2. **`status`** present and in `{delivered, blocked, needs-rescope, refused}`.
3. On **`delivered`**, the per-agent required fields (§4 table):

   | Agent | Required on `delivered` |
   |---|---|
   | **producer** | `artifacts` (≥1 `ship: true`) + `self_qa.copy` + `self_qa.visual` + `self_qa.content_subedit` |
   | **governance** | `gate.verdict` ∈ {clear, clear-with-disclaimers, hold, block} + `gate.audit_ref` |
   | **brand** | `gate.verdict` ∈ {pass, pass-with-notes, send-back, kill} + `gate.audit_ref` |
   | **creative-director / insights / forensic** | `artifacts` (≥1) |

4. On **`delivered`** with artifacts — every `ship: true` artifact **path exists on disk**
   (resolved against `--asset-dir`, else the return file's own dir). Reuses the SYS-003 /
   `gallery-qa` ship-file-existence discipline so a claimed deliverable that isn't there
   fails loudly.
5. **Gate agents** must carry an explicit verdict — never inferred from prose (the
   "verdicts must be explicit" rule).

A non-delivered status (`blocked` / `needs-rescope` / `refused`) only needs `dispatch_id`
+ `status` + a `notes` explaining why; the delivered-state fields are not required.

Agent names are matched flexibly: the dispatch vocabulary (`governance`, `brand`, `cd`,
`insights`, `forensic`) and the self-declared / agent-dir names
(`governance-manager`, `brand-manager`, `marketing-forensic-analyst`, …) both resolve.

## Run it

```bash
# Validate a return (ship paths resolve to the return file's dir by default)
python .claude/skills/agent-io/validate_envelope.py --return <return.yaml>

# With the matching dispatch (also checks id pairing) + an explicit asset dir
python .claude/skills/agent-io/validate_envelope.py \
  --return <return.yaml> --dispatch <dispatch.yaml> \
  --asset-dir campaigns/<slug>/assets/<asset-slug>

# Built-in good + bad fixtures — verifiable with no live data
python .claude/skills/agent-io/validate_envelope.py --selftest
```

The envelope file may be a wrapper (`return:` / `dispatch:` top-level key, as the agents
emit it) or the bare inner mapping — both load.

## Exit code

`0` = GREEN (envelope satisfies the contract). Non-zero = RED (the report names each gap) —
so CM, a hook, or `system-smoke-test` can gate on it. CM never silently accepts a RED return:
it re-dispatches with the gap named, or surfaces it to the operator (§5).

## How CM uses it (the dispatch ledger)

On each return, CM runs this validator **before acting**, then appends the dispatch↔return
pair to the dispatch ledger (`.claude/state/dispatch-ledger.jsonl`, mirroring the
cost-ledger pattern) so orchestration is auditable. See the campaign-manager skill,
"Agent I/O contract (SYS-004)".

## Cross-references
- [`agent-io-contract.md`](../../../docs/specs/agent-io-contract.md) — the contract this enforces.
- [`gallery-qa.md`](../../../docs/specs/gallery-qa.md) + `asset-gallery/build-gallery.py --check` — the ship-file-existence check reused here.
- [`cost-ledger`](../cost-ledger/SKILL.md) — the ledger pattern the dispatch ledger mirrors.
- [`per-step-brief.md`](../../../docs/specs/per-step-brief.md) — the dispatch body the envelope rides alongside.
