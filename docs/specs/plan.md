# Plan — Phase 3 Schema (v3)

**Spec version**: v3 · 2026-07 — the asset list gains **Type** (marketing asset vs setup/deploy task), **Channel**, and **Description** columns, and renders as **one table with a channel ⇄ wave group-by toggle**, split Launch / Ongoing. Waves are *derived* from the Depends column (no hand-authored tiers). Legacy v2 plans (no Type column) keep rendering as the phase-grouped cards until migrated. · v2 · 2026-06-03 added §N "Phase 5 + 6 readiness" end-of-Phase-4 gate per Rollout Architecture v2 (`docs/specs/rollout-architecture.md` §4).

The **Plan** is the operational map for the campaign. CM authors it after the operator picks a Concept. It's the asset list + agent assignments + sequencing the operator approves before Phase 4 fires. **v2 extension**: at end of Phase 4 (asset production), CM updates the Plan with a new §N "Phase 5 + 6 readiness" section that summarises what setup + training + cadence-runbook the campaign needs based on what was actually built. This is the end-of-Phase-3 gate before Phase 6 (Day 1 Rollout) work fires.

**Length target: 1-2 pages** (table-led for asset list; §N adds ~half page for ongoing campaigns, less for one-offs).

**Stored**: `campaigns/<slug>/plan.md` (markdown authoritative) + rendered `plan.html`.

**Locked**: at end of Phase 3 operator approval for the strategic core (Phasing / Asset list / Roster / Budget / Fast-lane rules). The §N "Phase 5 + 6 readiness" section is appended/updated at **end of Phase 4** (after asset development completes); operator approves §N as the Phase 5 → Phase 6 gate.

Material scope changes (asset added / removed / major sequence change / §N readiness changes ownership_model or platform) require vN+1 + re-approval. Minor tweaks (date shift, dependency reshuffle, §N detail updates) don't.

---

## Schema

```markdown
# <Campaign Name> — Plan v<N>

**Concept selected**: <link to chosen Concept>     **Approved**: <date>     **Status**: Draft / Approved / Locked

## Phasing
Brief paragraph naming the campaign's phases (pre-launch / launch / sustain / wrap or equivalent). Each phase has a goal one-liner and a date range.

## Asset list

The asset list is **one table** — every marketing asset AND every setup/deploy task, as rows. It renders as a single grouped table with a **Group by: Channel | Wave** toggle (see "The two views" below), split Launch / Ongoing. Keep `# | Asset` as the first two columns — the gallery + `check-state` contract keys on them.

| # | Asset | Description | Type | Channel | Review shape | Form | Ships | Copy file | Owner agent | Phase | Target date | Depends on | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Visual identity kit | The masthead + templates every other asset is built from | asset | Brand foundation | `output` | Brand mini-guide (HTML) + masthead + templates | Masthead (SVG) + tile template + edition template | `none` | Producer | Pre-launch | YYYY-MM-DD | — | The dependency for every visual below |
| S1 | Create the Substack + lock handle | Stand up the publication so every asset can link to it | setup | Substack | — | Operator action (account) | — | `none` | Operator | Pre-launch | YYYY-MM-DD | — | CM can't create accounts |
| 2 | Publication setup | The about page + welcome email a new subscriber first meets | asset | Substack | `output` | Substack config + about + welcome (Mode C) | About-page copy + welcome-email copy | `md` | Producer | Launch | YYYY-MM-DD | #1, S1 | — |
| S2 | Deploy site placements | Push the placements live — the HTML itself going public | setup | Website | — | Publish → Netlify | — | `none` | Operator | Launch | YYYY-MM-DD | #7 | Operator's Netlify push |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Type values (v3):**
- `asset` — a **marketing deliverable** (web page, post, tile, video, email). Gets an asset folder, a per-asset gate, and a gallery tile — everything the old asset list held.
- `setup` — a **setup / deploy / config task** (create the Substack, deploy the HTML, drop GA4 tags, compliance fills). **Plan-only**: `Ships` is `—`, and it gets NO asset folder and NO gallery tile. It sits beside the assets it belongs to so a channel reads as a complete unit ("here's the page AND what it takes to get it live"). Give it an `S<n>` id in the `#` column so other rows can depend on it.

**Channel values (v3):** the surface the work lives on — `Brand foundation` · `Substack` · `Website` · `LinkedIn + social` · `Email — <list>` · `Video` · `Ads & paid` · `Measurement` · etc. Drives the default grouping. If omitted, the renderer falls back to the keyword heuristic (`_plan_asset_type`).

**Name + Description (v3) — write for a human with ZERO context.** Both the `Asset` name and the `Description` are the operator's decision surface: a smart operator who has never seen this campaign must read them and know *exactly* what the thing is and what it's for — **no interpretation**. This is a hard bar, not a nicety (operator directive 2026-07-06 — the first v3 draft failed it). Rules:

- **No internal jargon.** Ban words like *tile · masthead · cadence · fast-lane · build-diary · flagship · cross-promo · unit · per-tenant · editorial backlog · lock the pattern*. Say the plain thing: *social share-image · logo · the weekly-issue tool · auto-approved · launch issue · promo block*.
- **Spell out every acronym on first use** — *business number (ABN) · Google Analytics · tagged links (UTM) · the goal (KPI) · button (CTA)*. Never a bare acronym.
- **No cross-references** — never `§3`, `A2`, `#1–#3`, a raw file path, or "the X unit / kit / surface". Name the actual thing.
- **No cryptic codes** — an issue's description says what it is *about* ("how the AI system went from a dozen agents to seven"), never "learning A2".
- **The test:** could someone *outside* marketing read the Name + Description and act with zero interpretation? If not, rewrite. The Description is the *purpose / what distinguishes it* — the deliverable format lives in `Form` / `Ships`.
- **Plain language everywhere** — including the collapsed `Notes` and the change log, not just the name + description. `Notes` may carry finer production detail (status, file paths, gate state) but stays interpretable: no cryptic codes (say what an issue is *about*, never "A2"), acronyms spelled out. The bar relaxes on *depth* in Notes, never on *clarity*.

**Review shape values:**
- `output` — the specific deliverable; operator approves it as-is
- `template [+N exemplars]` — parametric template is the approval target; N populated exemplars show how it works but inherit approval from the template
- `variant-comp [N variants × M sizes]` — one representative comp is the approval target; all production instances (other sizes, resizes, derivatives) inherit approval automatically — no individual review

**Copy file values:**
- `md` — editable Markdown companion alongside the visual (web pages, emails, articles, outreach, social copy)
- `csv` — spreadsheet for multi-variant copy (banner ad matrices, subject-line batches, variant copy tables)
- `pptx` — PowerPoint IS the deliverable; no separate copy file
- `docx` — Word document IS the deliverable
- `none` — no copy companion (pure visual, cookbooks, runbooks, trackers, or deliverable is already the copy)

**Form values** (be specific — include production mode): HTML/CSS landing page (Mode C) · HTML email templates (Mode C) · LinkedIn post + 1:1 PNG tile · Substack long-form article + HTML · Print PDF/SVG (CMYK, 3mm bleed) · HTML/CSS display banners (Mode C) · Markdown pitch template + HTML render · 1:1 PNG tile (Mode B) · etc.

**Ships values — the output manifest (added 2026-06-15; "the plan dictates the assets"):**
The `Ships` column is the **authoritative contract for exactly what each asset produces** — one entry per *distinct output*. An **output** is any discrete artifact the operator reviews or receives, **intermediate OR final** — not just the last file. `Form` describes the asset in prose; `Ships` enumerates the concrete outputs. They are different jobs:
- A sales deck whose `Form` is "Slide deck + presenter notes" → `Ships` **two formats**: `HTML deck (index.html) + PowerPoint (deck.pptx)`.
- A video whose `Form` is "Remotion silent videos" → `Ships` **two gated outputs**: `4 storyboards (HTML) + 8 × MP4`. The storyboard is a real output (it gets its own approval gate before expensive rendering), so it is named in `Ships` and it tiles.

The operator's framing: *"the plan dictates the assets, so the plan needs to be explicit — sales deck >> output = HTML, PPT; video >> output = storyboard, MP4."* If the plan is vague about outputs, that is the root cause of any downstream what-do-I-ship confusion — fix the plan, not the symptom.

This column is **load-bearing**, not documentation:
- **Gallery tiles = Ships, 1:1.** Every entry in `Ships` becomes exactly one gallery tile; nothing else does. A non-web-renderable output (`.pptx`/`.pdf`/`.docx`/`.xlsx`) still ships and still tiles — the gallery renders it as a format-card with a download action.
- **asset.yaml `ship: true` = Ships, 1:1.** The Producer sets `ship: true` on exactly the files named in `Ships` and `ship: false` (or omits/declares as Foundation) on everything else — render-pipeline sources (`slide.html`, `build-pptx.py`), embedded component images (`images/*`), deployment wrappers (`modal-embed.html`), and the asset record (`asset.html`) are **never** ships.
- **`check-state` validates the chain** Plan `Ships` ↔ asset.yaml `ship:true` ↔ gallery tiles; a mismatch is drift.

Write `Ships` concretely and tersely: name the format + the file kind, e.g. `Case study (HTML) + deck slide (PNG)` · `3-touch email sequence (HTML + copy)` · `8 × MP4 (4 videos × 4:5 + 9:16)` · `Landing page (HTML)`. If an asset ships nothing reviewable (a process checkpoint, a CUT row), use `—`. **If you can't fill `Ships` cleanly, the asset isn't specified yet — that is the signal to tighten the Form/scope before production, not to let the Producer improvise it.**

### The two views (rendered, v3) — channel ⇄ wave

One list, two group-bys. The operator flips a **Group by: Channel | Wave** toggle:
- **By channel** (default) — rows grouped by the surface they live on; the `Wave` column shows, per channel, what fires when.
- **By wave** — rows grouped by production wave; the `Channel` column shows, per wave, which surfaces are in play.

Both are the SAME rows with both columns present — no second table, nothing hand-synced. Above both sits the **Launch / Ongoing** split (classified from the Phase column): Launch = one-time stand-up; Ongoing = the recurring engine (cadence, weekly editions, paid boost, KPI monitoring). Every per-row detail is preserved — the key columns sit inline; Form / Review shape / Copy file / Target / Notes fold into a per-row **details** expander so nothing is dropped.

### Waves — derived, never authored (v3)

A **Wave** is a row's dependency tier, computed from the `Depends on` column:
- **Wave 1** = every row with no unmet dependency → the agents produce these **at once, in parallel**.
- **Wave N** = rows whose dependencies all sit in earlier waves.

The wave count auto-sizes to the graph: everything-needs-only-the-identity-kit → 2 waves; a chain (kit → Substack → edition → cadence) → more; nothing depends on anything → 1 wave (build it all at once). Waves are the ordering *within* Launch/Ongoing — a different axis from that lifecycle split. **Never hand-author a tier column** — it would drift from the dependencies; the renderer derives it. A dependency cycle is broken defensively (the offending node is treated as a root); a cycle means the Plan is malformed — fix the deps.

### CM dispatch — fire each wave as a parallel batch (v3)

The wave structure is executable, not decorative. In Phase 4, **CM dispatches all of a wave's `asset` rows as one parallel Producer batch** — multiple concurrent Producer dispatches (one Producer role, many simultaneous jobs; NOT different agent types, which would conflate *who does the work* with *when it can start*). The operator gate is at the **wave boundary**: approve Wave 1, and Wave 2's assets fire together the moment it clears — not asset-by-asset within a wave, except where a specific asset is flagged NOT fast-lane. `setup` rows the operator owns (create the account, provision keys, deploy) are the roots that gate the first asset wave — surface them as operator actions up front.

### The plan is the living source of truth — the gallery mirrors it (v3)

The Phase-4 asset gallery **derives** its channels, names, descriptions, dependency waves, and Launch/Ongoing split from THIS plan (via the shared `plan_model`) — the gallery is a *view* of the plan, never a separate list. Two consequences:

- **Any change to the asset set, in ANY phase, updates this plan first — in the same turn.** A new asset surfaced during Phase-4 review, an asset dropped, or one re-scoped: CM adds/edits its row here (plain-language name + description, `Type`, `Channel`, `Depends on`) *before/as* it produces it, then re-renders `plan.html` and rebuilds the gallery. A material scope change bumps the plan version + re-approval; a like-for-like swap or dependency reshuffle doesn't.
- **Waves re-derive automatically.** Because `Wave` comes from `Depends on` and is recomputed on every render, adding or removing a row re-waves BOTH surfaces at once — no manual wave bookkeeping, and the two can't disagree.

`check-state` enforces the floor: any asset folder on disk with no plan row is flagged as drift (Layer E), and the gallery shows an unmatched tile in a visible "not in the plan yet" group rather than hiding it — so an unreconciled addition surfaces immediately instead of rotting the plan.

### Asset list discipline — cadence-skill rule (v2 addition)

**For campaigns where `cadence_shape.type` is `ongoing` or `hybrid`**, the Asset list MUST include a per-tenant cadence skill scaffold as a Phase 4 (Asset Production) deliverable:

| # | Asset | Form | Owner agent | Phase | Target date | Depends on | Notes |
|---|---|---|---|---|---|---|---|
| N | Per-tenant cadence skill — `.claude/skills/<tenant-slug>-<cadence-name>-assets/SKILL.md` | Skill definition (SKILL.md + trigger block + required inputs + AI-derived outputs + output folder structure + reference materials + execution flow) | CM + Producer | Phase 4 | Before end of asset-dev wave | Wave 0 templates | This is the operator's Phase 6 entry point. Without it, phase-6-cadence.md references a skill that doesn't exist. Per `feedback_cadence_skill_is_phase3_deliverable.md`. |

The cadence skill scaffold is **intentionally thin** at Phase 4 time (~250 lines of SKILL.md prose) — orchestration only, no novel logic. Producer + CM + Brand Manager + adapters do the heavy lifting. The scaffold is versioned after 2-3 real cycles per the deferred-extraction principle.

**Naming convention**: `.claude/skills/<tenant-slug>-<cadence-name>-assets/` — e.g.:
- `sb-podcast-weekly-assets/` (Acme Co Talks weekly)
- `sb-news-monthly-assets/` (Acme Co News monthly)
- `soundtrak-techpulse-weekly/` (Soundtrak TechPulse cadence)

Per `feedback_cadence_skill_is_phase3_deliverable.md` + `feedback_captured_rules_require_explicit_propagation.md`.

### Asset list discipline — foundation-shaped campaigns (v3 addition, 2026-06-12)

**For foundation-shaped campaigns (the Brief's objective is strategy development)**, the asset list comprises **strategy artifacts**, not market-facing assets. Standard set (prune/extend per scope):

| Asset | What it is |
|---|---|
| Segment map | Tenant-layer targeting evidence base — segments · pains · triggers · landmines · per-segment fit status. Home: `tenant-brand/<tenant>-segments.md` at graduation |
| Competitive claim map | Wallpaper / contested / open-territory buckets + nearest named threat (per playbook §0 schema) |
| Value proposition one-pager | The approved route from the trio, with gate-survived lines + only-we lines |
| Brand platform | Brand Context authored/overhauled (voice · visual · positioning) |
| Fit evidence base | Per-segment PMF status with FINDING/HYPOTHESIS-tagged evidence |

Each is a normal asset (generic `asset.md` contract, `output` review shape, gallery tile, per-asset operator gate). **At wrap, these graduate to the tenant layer — the wrap graduation gate IS the foundation approval.** The frozen campaign folder remains the audit trail of how the strategy was made.

## Roster
Specialists in scope for this campaign:
- **Producer** — all production assets
- **Brand Manager** — every asset gate, automatic
- **Campaign Manager** — orchestration throughout
- **Creative Director** — on retainer for creative-integrity callbacks; primary work done in Phases 1–3
- **Operator (you)** — bylines + personal sign-offs + final approvals + publish actions where needed

(Wave 3+ agents added only if Producer escalates a specific asset beyond AI-tooling ceiling.)

## Budget allocation

| Line | Amount | Purpose |
|---|---|---|
| <paid line 1> | $<n> | <what> |
| Production tooling | $<n> | Replicate / AI gen costs |
| Contingency | $<n> | 5–15% reserve |
| **Total** | $<n> | (matches Brief budget total) |

## Fast-lane rules
What ships without per-asset operator approval (still subject to Brand verdict):
- <e.g. weekly recurring companion posts after first 3 establish pattern>
- <e.g. email signature drop-ins>

NOT fast-lane:
- <e.g. anchor posts, paid creative, any deviated tile, any net-new format>

## Open questions
Anything CM resolved or surfaced during planning that downstream production needs to know about. Includes pending dependencies (legal review windows, founder time blocks, etc.).

---

## §N — Phase 5 + 6 readiness *(v2 — populated at end of Phase 4)*

> **Authored**: <date> (end of asset development)
> **Status**: Draft / ✅ Approved (= Phase 5 → Phase 6 gate passed) / 🟥 Blocked
> **Approves**: operator

### N.1 Phase 6 — Day-1 Rollout requirements

**Source-of-truth references** (read these to fully populate this section):
- Brief §Tech Setup (`tech_stack`) — destination platforms per channel
- Brief §Human Roles (`human_roles`) — who runs what
- Brief §Cadence Shape (`cadence_shape`) — `ownership_model` + `phase_6_emphasis`
- Asset list above — what one-offs need to be deployed
- `tenant/<tenant>/integrations.yaml` (built in Phase 6 itself, but the **plan** for what goes in it is captured here)

**One-off assets to deploy at Day 1:**

| # | Asset (from Asset list above) | Destination (from Brief tech_stack) | Method (api / cookbook / hybrid) | Owner | Acceptance criterion |
|---|---|---|---|---|---|
| <#> | <asset name> | <platform> | <method> | <the operator / Tenant operator> | <how we know it landed> |
| ... | | | | | |

**Setup tasks** (Phase 5 work CM + the operator need to complete before Phase 5 can fire):
- Provision <platform> API key access (tenant-side action)
- Configure `tenant/<tenant>/integrations.yaml` with credentials + per-platform defaults + channel_defaults
- Install Claude Code on designated operator machine (if ownership_model = tenant-self-runs or the operator-runs-then-tenant)
- Scaffold tenant OneDrive folder structure per Rollout Architecture §8.2
- <other tenant-specific provisioning>

**Training plan** (only if ownership_model != the operator-runs):
- Pre-session materials: phase-6-cadence.html · operator-onboarding.html · Brand Context · tenant integrations.yaml walkthrough
- Day 1 live session: ~1-2 hrs (depth per ownership_model — tenant-self-runs needs heavier than handoff-period)
- First-N-weeks support: <the operator on Slack/email; N = duration; intensity = check-in frequency>

### N.2 Phase 6 — Ongoing Cadence requirements *(only if `cadence_shape.type` != "one-off")*

**Per-cycle runbook ownership**: <role + name OR "tenant-managed internally">
**Per-cycle estimated time**: <minutes operator + minutes adapter-handled>

**Cycle steps** (skeleton — full version becomes `campaigns/<slug>/phase-6-cadence.md`, authored at the end of Phase 4):
1. <trigger event — e.g. new podcast episode airs Wednesday>
2. <operator opens Claude Code on cadence day>
3. <runs slash command — e.g. /weekly-episode-pack>
4. <answers N structured questions>
5. <reviews approved assets in gallery>
6. <adapter-handled steps fire>
7. <operator manual steps — Send button, social posts, etc.>

**Escalation paths** (one-liner per category; full version in phase-6-cadence.md):
- <category 1>: <what to do> → <escalation contact>
- <category 2>: ...

### N.3 Retro milestones *(v2 — added 2026-06-04)*

Per `docs/specs/retro.md`, this campaign's planned retro touchpoints:

| Trigger | Scope | Timing | Output target |
|---|---|---|---|
| End of Phase 1 (Brief approval) | phase-1-boundary | ~10 min | `campaigns/<slug>/retros/<date>-phase-1-boundary.md` |
| End of Phase 2 (Concept selection) | phase-2-boundary | ~10 min | `campaigns/<slug>/retros/<date>-phase-2-boundary.md` |
| End of Phase 3 / each wave close | wave-N OR phase-3-boundary | ~30 min | `campaigns/<slug>/retros/<date>-wave-N.md` |
| End of Phase 4 (Plan §N approval) | phase-4-boundary | ~10 min | `campaigns/<slug>/retros/<date>-phase-4-boundary.md` |
| End of Phase 5 (Day-1 Rollout closure) | phase-5-boundary | ~15 min | `campaigns/<slug>/retros/<date>-phase-5-boundary.md` |
| Phase 6 cycle 4 close (= "is steady-state?") | wave-N or quarterly | ~30 min | `campaigns/<slug>/retros/<date>-phase-6-cycle-4.md` |
| Campaign-end (one-off) OR quarterly (ongoing) | campaign-end OR quarterly | ~45-60 min | `campaigns/<slug>/retros/<date>-quarterly-NN.md` |

**Skip rule**: light phase-boundary retros may be skipped if operator confirms "no friction this phase, nothing to capture" within a minute. Heavier retros (wave / campaign-end / quarterly) are MANDATORY — no skip.

### N.4 Phase 5 → Phase 6 gate criteria

Before §N is marked ✅ Approved and Phase 6 work fires, all of these must be true:

- [ ] Brief §Tech Setup fully resolved (no `TBD` in tech_stack)
- [ ] Brief §Human Roles fully resolved (no `TBD` in ai_trigger_person / approval_chain / manual_publisher / escalation_contact)
- [ ] Brief §Cadence Shape fully resolved (`ownership_model` confirmed; `phase_6_emphasis` set)
- [ ] All assets in Asset list above have `asset.yaml` with `deployment:` block populated (or marked explicit-TBD with reason)
- [ ] No outstanding Brand Manager verdicts (all assets ✅ Approved or kill-decision documented)
- [ ] Operator confirms credentials-side commitments (API key provisioning timeline, training availability, etc.)

If any criterion is unmet, §N status stays 🟥 Blocked + Phase 6 does NOT fire.
```

---

## Drafting discipline

- Asset list is the headline — table-led, scannable.
- Effort Tier from Brief sets expected asset count: XS=1–3 / S=3–6 / M=6–12 / L=12–25 / XL=25+. Above range = justify per asset; below = justify the restraint.
- Owner agent must match the agent roster. Only Producer + Brand + CM in default; escalations named explicitly.
- Fast-lane list is small and specific. "All social posts" is too broad. "Weekly Tuesday companion post after Brand confirms pattern on first 3" is right.
- Open questions limited to genuine pending items, not "what about everything else?"
- **v2 §N drafting**: §N is NOT in the initial Plan draft at Phase 3 approval — it's appended at end of Phase 4 (after asset development completes) and approved as a separate gate. The initial Plan locks the strategic core; §N locks the rollout-readiness.
- **v2 §N for one-off campaigns**: §N.2 (Phase 6) is omitted entirely. §N.1 + §N.3 only.
- **v2 §N for ongoing campaigns**: all three subsections required. §N.2 skeleton is intentionally brief — the full cycle runbook lives in `campaigns/<slug>/phase-6-cadence.md` (built in Phase 6 of the Rollout Architecture build sequence).
- **Revision discipline — change history goes to the FOOT, never the header (operator directive 2026-06-15).** A revised plan re-reads as a clean whole from the top; version-change prose ("v2.1 change", "Major v2 shifts from v1", etc.) does NOT sit between the header and the first section. Put a one-line pointer under the header — `> *(Full change history at the foot of this plan.)*` — and a single **`## Change log (vX → vY)`** section at the bottom. The render policy auto-moves history-classified `##` sections to the "📜 History & audit trail" tail (keywords: change log / changelog / version history / what changed / revision / freshness), but it CANNOT move header prose — so never author change history as header prose. Mirrors the concept-spec revision rule (`feedback_concept_revision_drift_taxonomy`).
- **"What's happening" (Channel workstreams) is never truncated (operator directive 2026-06-15).** The plan template's auto-generated channel summary shows every asset name at full length — more description, not less. (Enforced in `render.py _ws_desc`; the `.ws-row__desc` cell wraps and grows.)

---

## What this Plan does NOT contain

- Per-asset detail (lives in each Per-Step Brief, written by CM at dispatch time)
- Brand context (lives in Brand Context record; CM injects slices into each Per-Step Brief)
- Concept narrative (lives in the chosen Concept)
- Full Phase 5 rollout runbook (lives in `campaigns/<slug>/phase-5-rollout.md`, authored from §N.1 by CM **at the end of Phase 4**, together with the Phase 6 doc)
- Full Phase 6 cycle runbook (lives in `campaigns/<slug>/phase-6-cadence.md`, authored from §N.2 + Brief **at the end of Phase 4**, alongside the Phase 5 doc; cadenced campaigns only)
- Tenant credentials (live in `tenant/<tenant>/integrations.yaml`, never in Plan)

---

## v2 retrofit pattern (when applied to in-flight campaigns)

When a v1-era Plan needs v2 retrofit because the campaign is approaching Phase 6 (as Acme Co will need 2026-06-03):

1. CM appends §N "Phase 5 + 6 readiness" to the Plan markdown at end of Phase 4.
2. CM pre-populates §N.1 + §N.2 from Brief v2 sections + completed asset list (the assets' `deployment:` blocks once filled provide the destinations).
3. Anything genuinely unknown becomes a Plan OQ batch — blocks Phase 6 firing.
4. Plan version bumps to vN+1 (or v2.x for the retrofit batch); operator approves §N as a discrete gate.
5. Dashboard reflects: 🔵 "§N Phase 5 + 6 readiness in flight" → 🟡 "§N pending operator gate" → ✅ "§N approved · Phase 5 firing".

---

## Cross-references

- **Rollout Architecture v2 spec**: `docs/specs/rollout-architecture.md` — §4 defines the §N gate; §5 defines Phase 5 artifact (phase-5-rollout.md) that §N.1 expands into; §6 defines Phase 6 artifact (phase-6-cadence.md) that §N.2 expands into.
- **Brief spec v2**: `docs/specs/brief.md` — §Tech Setup + §Human Roles + §Cadence Shape are the upstream source of §N data.
- **Asset spec** (extended in Rollout Architecture build sequence Phase 4): asset.yaml `deployment:` block per-asset destinations feed §N.1's deployment matrix.
- **Phase 5 artifact spec**: `docs/specs/phase-5-rollout.md` (built in Rollout Architecture build sequence Phase 6) — §N.1 is the seed; phase-5-rollout.md is the expanded runbook.
- **Phase 6 artifact spec**: `docs/specs/phase-6-cadence.md` (built in Rollout Architecture build sequence Phase 6) — §N.2 is the seed; phase-6-cadence.md is the expanded per-cycle runbook.
