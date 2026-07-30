# Agent I/O Contract spec

**Version**: v0.2 · 2026-06-30 (**IMPLEMENTED — Steps 2-3 of §6**: validator built + agents emit the return envelope + CM validates at the boundary, all ADDITIVE / non-breaking. Step 4 — CM consumes the envelope as the SOLE source of truth + retires prose-parsing + a check-state dispatch↔return pairing layer — remains the future gated step.)
**Status**: Wired (additive). Ticket SYS-004. Validator: [`.claude/skills/agent-io/validate_envelope.py`](../../.claude/skills/agent-io/validate_envelope.py) (+ `dispatch_ledger.py`); CM emits the dispatch envelope + validates each return (see campaign-manager SKILL.md "Agent I/O contract (SYS-004)"); all six agents emit the `return:` block (their prose returns are unchanged). Nothing breaks if an envelope is missing.
**Owner**: Campaign Manager (orchestration); reviewed by the operator. Step 4 is gated by operator review before any prose-parsing is retired.

## 1. Why

Today CM dispatches to the seven agents with a **Per-Step Brief** (a one-page markdown envelope — see [`per-step-brief.md`](per-step-brief.md)) and each agent hands back **prose**: the finished asset, a self-QA, and a status line, as free text. CM reads that prose to decide what happens next.

That handoff is the system's least machine-checkable seam:
- a return can silently omit `status`, the content-subedit report, or the `asset.yaml`, and nothing notices until the gallery/dashboard breaks downstream;
- CM can't *programmatically* confirm an agent did its job (Producer ran content-subedit; Governance returned a verdict) — it parses sentences;
- fan-out aggregation (cost, status, dashboard) rides on fragile prose-parsing.

The fix is a **structured envelope on both sides of the dispatch**. The asset *content* stays prose + visual; only the *envelope* — the metadata of the handoff — becomes a schema CM can validate.

## 2. Scope (and non-goals)

**In scope:** a machine-checkable **dispatch envelope** (CM → agent) and **return envelope** (agent → CM), plus the validation CM runs at the boundary.

**Non-goals:**
- Not a rewrite of the Per-Step Brief — its human-readable body (§1–§9) stays exactly as is; the dispatch envelope is a small structured header *alongside* it.
- Not a change to what agents *produce* — the deliverable (copy, visuals, `asset.yaml`) is unchanged.
- Not a new artifact store — the return references the artifacts already written (`asset.yaml`, asset record), it doesn't duplicate them.

## 3. Dispatch envelope — CM → agent

A small YAML header CM emits with each dispatch. The Per-Step Brief rides alongside as the human-readable task.

```yaml
dispatch:
  id: <campaign>/<asset>/<agent>/<n>      # unique; pairs with the return
  campaign: <slug>
  agent: producer | governance | brand | creative-director | insights | forensic
  asset_ref: <asset-slug>                 # Plan # / asset folder; omit for non-asset agents
  review_shape: output | template[+N] | variant-comp[NxM]   # mirrors the Plan
  expects:                                # what the return MUST contain (drives validation)
    - artifacts
    - self_qa
    - status
  budget: { model: <id>, max_tokens: <n> }   # optional; feeds metered cost
```

The brief body (strategy / voice / visual / mandatories / KPIs / output-expected) is unchanged — it stays the Per-Step Brief.

## 4. Return envelope — agent → CM

The agent emits this as a single fenced ```yaml `return:` block at the end of its response (CM parses it). Prose around it is fine during rollout; once Step 4 lands, the envelope is authoritative.

```yaml
return:
  dispatch_id: <matches dispatch.id>
  agent: producer
  status: delivered | blocked | needs-rescope | refused
  artifacts:                              # mirrors asset.yaml files; the deliverables
    - path: <rel-to-asset>
      type: Template | Instance | Foundation
      ship: true | false
      role: <asset_record | primary_doc | ...>
  self_qa:                                # producer + any authoring agent
    copy:    { ran: true, layers: 3, pass: true, report: <ref> }
    visual:  { ran: true, layers: 3, pass: true, report: <ref> }
    content_subedit: { ran: true, violations: 0, report: <ref> }   # every copy asset
  gate:                                   # GATE agents only (governance / brand)
    verdict: clear | clear-with-disclaimers | hold | block        # governance
             | pass | pass-with-notes | send-back | kill          # brand
    audit_ref: <path to the audit block>
  flags:                                  # CM routes these
    - { to: operator | brand | governance, kind: open-question | decision | risk, text: <one line> }
  cost: { tokens_in: <n>, tokens_out: <n> }    # feeds the cost-ledger
  notes: <short prose, optional>
```

### Per-agent return profiles (which fields are required)

| Agent | Required on `status: delivered` |
|---|---|
| **Producer** | `artifacts` (≥1 ship:true), `self_qa.copy` + `self_qa.visual` (where applicable), `content_subedit` on every copy asset |
| **Governance** | `gate.verdict` ∈ {clear, clear-with-disclaimers, hold, block} + `gate.audit_ref` |
| **Brand** | `gate.verdict` ∈ {pass, pass-with-notes, send-back, kill} + `gate.audit_ref` |
| **Creative Director** | `artifacts` (concept/brand-context files) |
| **Insights** | `artifacts` (insight brief) + optional `flags` (resonance read) |
| **Forensic** | `artifacts` (campaign report) |

Any agent may return `status: blocked / needs-rescope / refused` with `notes` explaining why instead of the delivered-state fields.

## 5. Validation — CM at the boundary

When a return comes back, CM validates **before** acting on it:
1. `dispatch_id` present and matches the dispatch.
2. `status` present and valid.
3. On `delivered`: the per-agent required fields (§4 table) are present.
4. On `delivered` with artifacts: every `ship: true` artifact **exists on disk** — this reuses the SYS-003 `build-gallery --check` logic, so a claimed deliverable that isn't there fails loudly.
5. Gate agents: a verdict is present (never infer approval from prose — see the "verdicts must be explicit" rule).

A failed return is **not** silently accepted: CM re-dispatches with the gap named, or surfaces it to the operator. Every dispatch↔return pair is appended to a dispatch ledger (same pattern as the cost-ledger) so the orchestration is auditable.

**This makes three existing disciplines machine-enforced rather than prose-trusted:** ship-file existence (SYS-003 / gallery-qa), explicit verdicts (governance/brand), and cost capture (cost-ledger).

## 6. Staged rollout (do it slowly)

Each step is its own ticket, gated by operator review. **No step touches a live agent until the prior one is proven.**

- **Step 1 — this spec.** Design the envelopes; change nothing. ✅ done (v0.1).
- **Step 2 — pilot on Producer.** Producer emits the return envelope *alongside* its existing prose; CM validates it but still reads the prose. ✅ **implemented** — the validator (`.claude/skills/agent-io/validate_envelope.py`) checks dispatch_id pairing, status, the Producer required fields, and ship-file existence; CM emits the §3 dispatch envelope + runs the validator before acting + appends to `.claude/state/dispatch-ledger.jsonl`. Producer's AGENT.md now carries the `return:` block instruction.
- **Step 3 — roll to the other agents** (Governance → Brand → CD → Insights → Forensic), each emitting + validated. ✅ **implemented** — all six agents' AGENT.md files carry the `return:` block; the validator covers every per-agent profile (gate verdicts for Governance/Brand, artifacts for CD/Insights/Forensic).
- **Step 4 — CM consumes the envelope** as the SOLE source of truth for dashboard / cost / status auto-update; retire prose-parsing. Add a smoke-test / check-state layer that validates dispatch↔return pairing across a campaign. ← *future gated step — not yet done; prose-parsing stays authoritative during rollout.*

> **Where we are (2026-06-30):** Steps 2-3 are wired and ADDITIVE — the structured envelope rides *alongside* the prose, the validator gates each return, but the prose is still read. Nothing breaks if an envelope is missing. Step 4 (envelope as sole source of truth) is the next ticket, gated by operator review.

## 7. Cross-references
- [`per-step-brief.md`](per-step-brief.md) — the dispatch body (human-readable); this contract adds the structured header + the return side.
- [`asset.md`](asset.md) — the `asset.yaml` schema the `artifacts` block mirrors.
- [`gallery-qa.md`](gallery-qa.md) — the ship-file-existence check reused in validation (§5.4).
- [`cost-ledger`](../../.claude/skills/cost-ledger/SKILL.md) — where `return.cost` lands.
- [`system-manager.md`](system-manager.md) — SYS-004 tracks this work.
