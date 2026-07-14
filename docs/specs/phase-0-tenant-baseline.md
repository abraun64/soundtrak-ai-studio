# Phase 0 — Tenant Baseline (the per-business foundation)

**Spec version**: v1 · 2026-06-15 · Foundation of the three-evolutions build. Pairs with `compliance-profile.md` + `governance-manager/AGENT.md`.

Phase 0 is the **pre-campaign step that builds the durable tenant compound** — the per-business context every future campaign inherits as FIXED INPUT. It is the workflow that **fills the Governance Manager's shell** (authors the Compliance Profile) and gives the Creative Director its market + segment inputs.

> **🔒 FUTURE-ONLY / OPT-IN.** Phase 0 runs **once per tenant, on explicit request**. It **never auto-runs on existing tenants** (Acme Co · Acme Co · Soundtrak · the-signal), and it never reaches into a live campaign. Existing tenants migrate only if the operator chooses — no retrofit pressure.

## What Phase 0 is — and is NOT (reconciling the 2026-06-12 "no Phase 0 machinery" ruling)

That ruling rejected machinery that **builds strategy** ahead of campaigns. Phase 0 does **not** build strategy — it **ingests what already exists** and normalizes it. The line is **ingest-vs-create**:

| Phase 0 INGESTS (what exists) | Campaigns still CREATE (judgement/validation) |
|---|---|
| Existing brand guide / voice / visual identity | New value-prop *validation*, positioning *judgement* |
| Known compliance rules + approved disclaimers | — |
| Observable competitors + market structure | Creative concepts, campaign ideas |
| Known segments (descriptive + any prior data) | Segment *insight* mined per campaign by CD |
| Best-practice past assets | New assets |

Foundation-shaped campaigns still build absent/contested strategy through the gates (see `workflow.md` §Foundation campaigns). Phase 0 is the factual groundwork beneath them.

## The durable tenant compound (Phase 0 output)

| Deliverable | Artifact (current flat structure) | Powered by | New? |
|---|---|---|---|
| Brand Context (voice / visual / style) | `tenant-brand/<tenant>.md` | `brand-voice:discover-brand` + `generate-guidelines` (+ CD authoring if absent) | exists |
| Value prop + claim map + only-we + segment pointer | `tenant-brand/<tenant>-playbook.md` §0 | `company-intelligence` competitive scan | exists (seed) |
| Segment map | `tenant-brand/<tenant>-segments.md` | `segmentation-strategy` | exists (ingest known) |
| **Market landscape + competitor list** | `tenant-brand/<tenant>-market.md` | `company-intelligence` | **NEW** (schema below) |
| **Compliance Profile** | `tenant-brand/<tenant>-compliance.md` | `governance-manager` (Phase 0 authoring role) | **NEW** (`compliance-profile.md`) |
| **Audience truths** (durable per-segment tensions) | `tenant-brand/<tenant>-audience-truths.md` | `insights-manager` (Phase 0 authoring role) | **NEW** (`audience-truths.md`) |
| **Research library** (SHARED, faceted — public market/audience papers) | `tenant/research-library/` (+ `INDEX.md`) — shared across tenants, like the creative library | `insights-manager` / `insight-scan` (Phase 0 *contributes* the tenant's vertical research) | **NEW** (`research-library.md`) |
| Best-practice asset library | `tenant/library/` (+ later `<business>/baseline/library/`) | `library-add` + `b2b-audit` of existing marketing | exists (seed) |
| Tech stack | `tenant/<slug>/integrations.yaml` | onboard interview | exists |
| **Tenant Dashboard** (operator home) | `tenant-brand/<tenant>-home.html` (flat) | generated from `tenant.yaml` + campaigns tagged `tenant: <slug>` | **NEW** (flat — no restructure) |

(Post-W4 business-rooted: all of the above move to `<business>/baseline/…`. W4 keeps the flat paths working — no retrofit.)

## The skill-step map (the wiring)

| Step | Skill / agent | Output → captured into |
|---|---|---|
| Industry + regime research → Compliance Profile | **`governance-manager`** (authoring role) | `<tenant>-compliance.md` (operator/counsel approve) |
| Market + competitive scan | **`company-intelligence`** | `<tenant>-market.md` + playbook §0 claim map |
| Needs-based segmentation (2×2 · independent axis · personas · channels · TAM/SAM/SOM) | **`segmentation-strategy`** | `<tenant>-segments.md` |
| Find existing brand materials across platforms | **`brand-voice:discover-brand`** | feeds Brand Context |
| Voice synthesis from discovered docs | **`brand-voice:generate-guidelines`** | Brand Context §2 |
| (Optional) foundation strategy generation | **`marketing-strategies`** | playbook notes (only if strategy is absent/contested) |
| Audience-truths (tenant) + research-library (shared) seed | **`insights-manager`** / **`insight-scan`** (multi-source sweep) | `<tenant>-audience-truths.md` + `tenant/research-library/` (faceted by vertical) |
| Gold-standard seeding | **`library-add`** | `tenant/library/` |
| **Tenant identity + home** (last step) | operator/CM: hand-create `tenant-brand/<tenant>.yaml` → run `build-tenant-home.py --tenant <slug>` | `tenant-brand/<tenant>.yaml` + `<tenant>-home.html` (then auto-refreshed by the stop hook) |

**Brand Context authoring (when no existing brand materials exist).** Primary path: `brand-voice:discover-brand` + `generate-guidelines` synthesize voice from what's found. Where there's genuinely nothing to ingest, the Creative Director authors the Brand Context as a **Phase 0 task** — voice (tonal calibration + writing principles + words-we-use/avoid) + visual identity (palette + type + register + composition rules) + positioning, extracted structurally per [`brand-context.md`](brand-context.md), inferences marked "operator to confirm", Canva brand kit set up. **This authoring lives in Phase 0** — it moved out of the CD agent's old Stage-1a role (2026-06-15). The CD agent now only authors concept trios at Phase 2 and *consumes* the Brand Context.

## Capture-to-markdown rule (load-bearing)

`company-intelligence` / `segmentation-strategy` / `marketing-strategies` each emit a **self-contained HTML in their own house style** (Ink / Signal-Red / Cream). The system is markdown-authoritative → `render-html`. **So Phase 0 captures the markdown *substance* of each skill's analysis into the tenant artifact** (segment map, market landscape) and keeps the skill's standalone HTML as a companion under `tenant/<slug>/_discovery/`. The skill HTML is never the authoritative source.

## Gates

- **ONE batched approval per artifact class** (operator-trio style): "here's the tenant baseline — Brand Context · Segments · Market · Compliance — approve / edit each." Compliance Profile additionally carries the counsel-review flag (§8 of its spec).
- **"No baseline needed for X" is a valid explicit outcome** — never skipped silently.
- The Compliance Profile is **operator-approved** (and counsel where §8 requires); never auto-activated.
- **The same gate governs re-runs and section-scoped updates** — a re-run diffs proposed changes against approved content and asks the operator to confirm; it **never silently overwrites** an approved baseline (see *Idempotent re-run + section-scoped update*).

## Run-once + refresh

- Phase 0 **completes once per tenant**, but is **safe to re-run any time** as material accumulates (see *Idempotent re-run* below) — the first run establishes the baseline; later runs top up gaps or update one section, never redo the whole thing. Tenant-baseline readiness surfaces on `campaigns/index`.
- Refresh cadence: claim map per-campaign (existing rule); market + segments quarterly; **Compliance Profile on regime change + periodic** (its §10).
- Owner: CM orchestrates; later extractable to an `/establish-tenant` skill after 2–3 manual runs (per the existing skill-extraction discipline).

## Idempotent re-run + section-scoped update (SYS-065)

"Set yourself up" / "onboard `<tenant>`" / **"update my brand"** is **one idempotent workflow**, not a one-shot. Re-running it as new material arrives — or to change a single part — is a first-class path, and it is **safe**: it keeps what's still right, only interviews for what's missing or changed, and **never silently overwrites operator-approved baseline content** (see *Gates*). This mirrors the promise the operator FAQ makes (`docs/playbooks/faq.md` → "Do I have to redo my whole setup…").

### Auto-detect — what already exists

Before interviewing, CM **detects the current baseline state per section** so it can skip what's present. Detection is mechanical (don't eyeball it):

```
python .claude/skills/campaign-manager/phase0_detect.py --tenant <slug>
```

It reads two signals per section — the **file** (`tenant-brand/<slug>*` / `tenant/<slug>/integrations.yaml`) and the **`baseline:` declaration** in `tenant-brand/<slug>.yaml` — and reports each section as `present` (both agree), `missing` (interview it), or `partial` (file/declaration mismatch — reconcile with the operator, never silently). This is the read-only companion to `phase0_gate.py`: the **gate** answers "may a campaign start?"; the **detector** answers "what does this tenant already have, section by section?".

- **First run** (all `missing`): the full baseline pass, exactly as today.
- **Re-run** (some `present`): CM lists what's already established, confirms it in one line ("your voice, segments and market are set — leave them?"), and only interviews the `missing`/`partial` sections plus anything the operator names for update.

### Section vocabulary + operator update verbs

The baseline is addressable in six sections. Each maps to an artifact and an operator-facing verb — updating one section **must not** redo the others:

| Section | Artifact | Operator says |
|---|---|---|
| **brand-context** | `tenant-brand/<tenant>.md` | "update my brand", "refresh my brand context" |
| **voice** | `tenant-brand/<tenant>.md` (voice/tone slice — same file, scoped edit) | "update my voice", "change how it writes" |
| **segments** | `tenant-brand/<tenant>-segments.md` | "update my segments", "update just my target segments" |
| **market** | `tenant-brand/<tenant>-market.md` | "refresh my market / competitors" |
| **compliance** | `tenant-brand/<tenant>-compliance.md` | "update my compliance rules / disclaimers" |
| **channels** | `tenant/<tenant>/integrations.yaml` | "update my channels", "I added a new tool" |

`voice` has no file of its own — it's the voice/tone slice of the Brand Context, reported and edited separately so "update just my voice" is a legible scoped verb that touches only that slice of `<tenant>.md`.

A section-scoped update (`--section <name>` on the detector) interviews **only** that section, diffs the proposed change against the current approved content, and gates just that artifact class. It does **not** re-open the other five.

### Gates preserved (hard — no silent overwrite)

The re-run/update path uses the **same batched approval per artifact class** as a first run (see *Gates*). A re-run or section update **NEVER** writes over operator-approved baseline content without confirmation:

1. **Detect** the current state (present / missing / partial).
2. For any section being changed, **draft the update and show the diff** against the current approved artifact — what's added, what's changed, what's removed.
3. **The operator approves the diff** (per artifact class, batched) before anything is written.
4. Only on explicit approval is the artifact rewritten and its `baseline:` entry / `Last updated` stamp refreshed; then re-render its HTML (per the render-on-every-state-change rule).

`partial` (file present but not declared, or declared but file missing) is surfaced for reconciliation, never auto-resolved. "No change needed for section X" is a valid **explicit** outcome, never a silent skip. This protects operator trust: an approved baseline is only ever changed by the operator saying yes to a specific diff.

## `<tenant>-market.md` — inline schema (NEW artifact)

The competitive + market-structure record (largely a `company-intelligence` capture). Durable per-tenant.

```markdown
# Market Landscape — <Tenant>
**Last updated**: <date>     **Source**: company-intelligence run <date> (HTML companion in tenant/<slug>/_discovery/)

## Market structure
TAM / segments / pools · where the tenant sits · growth dynamics. (FINDING/HYPOTHESIS tagged.)

## Competitor list (~10–15 named where the category supports it)
| Competitor | Position | Nearest-threat? | Notes |

## Competitive claim landscape (feeds playbook §0)
- Wallpaper claims (category-generic — avoid leading with)
- Contested claims (multiple players)
- Open territory (unclaimed)
- Only-we lines (no named competitor can copy without breaking their model)

## Refresh
Per-campaign claim-map freshness scan (existing rule) + quarterly market review.
```

## Tenant Dashboard + cross-linking (operator surface — flat structure, NO restructure)

Decided 2026-06-15: build this on the **current flat structure** — no folder move, no business-rooted restructure. Two small data additions power it:
- **`tenant.yaml`** (per tenant, `tenant-brand/<tenant>.yaml`) — display name + nickname + pointers to the tenant's baseline artifacts (brand-context · compliance · segments · market · playbook · integrations).
- **`tenant: <slug>`** field on each `campaign.yaml` — declares which tenant owns the campaign.

The **Tenant Dashboard** (`tenant-brand/<tenant>-home.html`) is generated from `tenant.yaml` + a scan of campaigns where `tenant == <slug>` (same operator-surfaces-from-data discipline as `campaign.yaml` → dashboard). It **lists the baseline compound** (links to each artifact) and **lists the tenant's campaigns** (links down to each campaign dashboard).

**Cross-link navigation hierarchy** (dashboards stop being islands):
- **Master index** (`campaigns/index.html`) → group campaign cards by tenant; each links to its Tenant Dashboard.
- **Campaign dashboard** → breadcrumb UP to its Tenant Dashboard (Tenant → Campaign → artifact).
- **Tenant Dashboard** → DOWN to campaigns + baseline artifacts.

**Build**: additive render-pipeline work — a new `tenant` render type + `tenant.yaml` schema + the `tenant:` field + breadcrumb/index grouping in `render.py` + `operator_actions.py`. **NOT business-rooted, NOT W4** — campaigns stay at `campaigns/<slug>/`, discovered exactly as today; the auto-fire hooks are untouched. (The dormant business-rooted dual-path in `tenant_paths.py` remains available if physical nesting is ever wanted.)

## Cross-references

- `docs/specs/compliance-profile.md` — the Compliance Profile Phase 0 authors
- `.claude/agents/governance-manager/AGENT.md` — authoring role
- `docs/playbooks/onboard-tenant.md` — the operator runbook that operationalizes this spec
- `docs/specs/tenant-playbook.md` — §0 seeded here; segment map cited here
- `docs/specs/brand-context.md` — authored/ingested here
- `docs/workflow.md` §Foundation campaigns — the create-side counterpart
- `docs/specs/_proposals/three-evolutions-implementation-plan.md` — build plan + NO-RETROFIT constraint
