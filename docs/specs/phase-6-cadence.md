# Phase 6 Ongoing Cadence — Spec

> **Plain-language standard (SYS-118).** The cadence runbook is the operating manual whoever runs the weekly/fortnightly cycle follows — often not the campaign's author. The **main prose must be plain language a non-technical operator can act on**: no code identifiers (script names, exit codes, slash-command internals), no internal jargon (dogfood, multi-tenant, content-subedit, UTM, au-sender-id, nav-crop), no unexplained acronyms. The execution "how" lives in the collapsible `<details>` blocks and code spans, for whoever runs it — never the lead prose. CM runs the [`review-ready`](../../.claude/skills/review-ready/SKILL.md) gate on the rendered runbook before surfacing it.

**Spec version**: v4 · 2026-07-23 — **§3 cycle-history + §4 KPI tables removed** (operator decision): they can't be auto-maintained from external tools (Substack / LinkedIn / Mailchimp aren't auto-read), so a hand-kept table goes stale and erodes trust in every surface. Cycle count lives on the **data-driven dashboard**; KPI reads come **on demand from the marketing-forensic-analyst** (in §3 close, or any time), reading real exported data. NEW: the **"the system IS the martech stack" principle** + the maintenance mechanism (which session, how it stays current), both below and surfaced to the operator in Step 5. (v3 2026-07-23 defined-layout; v2 2026-06-15 shared-spine; v1 2026-06-03 per Rollout Architecture v2 §6.)

**The canonical section order** (every Phase-6 cadence page follows this): **§0** overview → **✋ sign-off** → **§1** the cycle (plain-language steps) → **§2** escalation paths → **§3** what close looks like → *for the record* (links). No other top-level sections — **no cycle-history table, no KPI table**, no "procedural refinements", no standalone "who runs it" (fold into §0). Tracking + reporting are handled by the system + the analyst, never a hand-kept page table (see the principle below).

---

## The system IS the martech stack (the load-bearing principle)

A Phase-6 cadence page is **not a passive doc the operator maintains in a separate tool** — the AI system (**claude.ai + the AI Studio workspace + the render pipeline**) *is* the campaign-management layer. Three consequences the spec must always get right, and the page must make obvious to the operator:

1. **State lives in the files, not the chat.** The campaign's memory is `campaign.yaml` (phase, cadence entries, operator actions) + the campaign folder — never a chat session. So **any** workspace session recognises the ongoing campaign: CM / the cadence skill read that data on startup and know exactly where things stand. A brand-new fortnightly asset-production session picks up the thread with no hand-off.
2. **The operator never hand-edits the surface.** At the end of a cycle, the *same* session that produced the edition updates the DATA (the cadence entry) and RE-RENDERS the surfaces (dashboard + cadence page). Surfaces are a projection of the data ("operator surfaces are generated from data"). **Step 5 (Track) states this to the operator in plain words.**
3. **The system maintains what it can see; the analyst reads what it can't.** Cycle count / editions shipped / phase status live in `campaign.yaml` → auto-rendered (the dashboard). KPI numbers (subscribers, opens, engagement) live in EXTERNAL tools the system doesn't auto-read → so they are NOT put in a hand-kept table (it would go stale); they're read **on demand by the marketing-forensic-analyst** from real exported data. **This is why the §3 cycle-history and §4 KPI tables were removed.**

**Surface it, don't bury it**: §0 and Step 5 must make clear to the operator that claude.ai + the AI Studio ARE the martech stack — the same chat that writes the edition also keeps the campaign's records and surfaces current, in one loop, in the workspace.

**What this is**: the per-campaign **operator runbook for steady state** — what the operator opens on cadence day and executes top to bottom. **Authored by CM at the END of Phase 4, alongside `phase-5-rollout.md`** (both seed from Plan §N) — only for cadenced campaigns (`cadence_shape.type` != "one-off").

**Stored**: `campaigns/<slug>/phase-6-cadence.md` (markdown authoritative) + rendered `phase-6-cadence.html`. **Canonical filename** — not `cadence-playbook.md` (a legacy drift; retrofits rename to this).

**Authored from**: Plan §N.2 + Brief §Tech/Human/Cadence + `tenant/<name>/integrations.yaml` + Phase 5 closure learnings.

**Living document**: updated after each cycle — current §1 always reflects current best practice; history accretes in §3/§5. NOT versioned; current state is canonical.

---

## Same spine as Phase 5

Phase 6 IS the Phase 5 runbook with the one-time bits swapped for recurring ones, so the operator learns **one shape**:

| Section | Phase 5 | Phase 6 (this spec, v3) |
|---|---|---|
| Cold-start context | §0 At a glance | §0 At a glance (fold "who runs it" in here) |
| **The cycle's steps** (plain-language numbered steps) | §2 setup & deploy (once) | **§1 the cycle (repeats)** |
| Failure / escalation | §5 failure modes | §2 escalation paths |
| Wrap / close | — | **§3 what close looks like** |
| Tracking / reporting | §6 gate banner | dashboard (auto, data-driven) + analyst on demand — **NOT a page table** |
| One-time module | §3 training & handoff | — |

Both phases share the **numbered-step format** (§1 here = §2 there): each step leads with a plain-language "What this is" a non-technical reader can act on, carries its own check, and pushes any command/path detail into a collapsible (SYS-118). Phase 6 cycle steps are lighter than Phase 5 deploy steps — *Rollback* is usually n/a for a repeating step — but the discipline (atomic, honest times, plain language, data-driven status) is the same. **The §1 format is the operator-preferred prose steps, NOT a 7-column table** (the v2 table shape is retired).

---

## Schema

```markdown
# Phase 6 Ongoing Cadence — <Campaign Name>

**Tenant**: <name>     **Cadence**: <frequency> · <day + time + timezone>
**Operator**: <designated role + name OR "tenant-managed internally">
**Operator mode**: Mode 1 (the operator/Code) | Mode 2 v1 (Code+OneDrive on tenant machine)
**Phase 6 start date**: <date>     **Cycles completed**: <count>
**Plan status**: 🟡 Draft — awaiting your sign-off  /  ✅ Approved — the cadence may run

## §0 Campaign overview
**Reuse the dashboard's 🧭 Campaign DNA block** — Big Idea · Key message · 15-sec pitch · KPI · Full concept — **REQUIRED, identical to Phase 5**. Phase 6 MUST carry the campaign overview, not only cadence-specific rows (this was missed on The Debrief 2026-07-23 and corrected). Then add a **"how the cadence runs" block** (how often · each edition · who produces it · why it matters) below it.
- **§0 carries a "Quick links" row** — **[Gallery] · [Plan] · [Dashboard]** (Phase 6 also the editorial calendar) — inside the campaign-overview table, so the operator jumps to the gallery and the plan from the TOP of the page, not only the footer. **This applies to BOTH the Phase-5 rollout and the Phase-6 cadence §0** (operator request 2026-07-23).
- **No separate key-asset thumbnail table** for Phase 6 — link the assets from the Quick-links row + "→ all assets in the Gallery".
- Close §0 with: who runs it (fold the standalone "who runs it" here) · "cycle complete when …" (in §1) · total operator time.
(Phase 5 keeps its key-asset visual table; Phase 6 swaps it for this cycle-workflow because the *flow* is what the operator needs to internalise, not a static asset grid.)

## ✋ Sign off this plan first   ← operator approval gate (added 2026-06-15)

Built at the end of Phase 4 alongside the Phase 5 doc — a **Draft you approve before the cadence runs**. Check: is the cycle complete + right, and does every step have its asset / cadence skill / cookbook? CM lists any gaps here at build time; gaps go back to Phase 4 before approval.

| Gap | What's needed | Owner / source |
|---|---|---|
| <missing asset / cadence skill / cookbook> | <what to produce> | Phase 4 (Producer / CM) — produce before approval |

*(or "✅ No gaps — every cycle step has what it needs.")*

**How it surfaces (data-driven)**: while the **Plan status** line says Draft, the cross-campaign **[Tasks queue](../tasks.html)** and the dashboard To Do show **one** row for this phase — *"Approve the Phase 6 plan — Manage & Report"* (🔴). The cycle steps in §1 are **not** re-listed there: they live in this doc, so the task list stays a decision queue, not a duplicate step list. `operator_actions.collapse_phase_plan_actions` reads this line.

**To approve**: reply `approve Phase 6 plan` → CM trims the **Plan status** line to `✅ **Approved** — the cadence may run (approved <date>)` and re-renders → the gate row drops and the cadence runs. Until then it's a proposal.

## §1 The cycle (numbered steps + one review)
*Plain-language numbered steps the operator works top to bottom each cycle. Each step = a "What this is" a non-technical reader can act on + a checkbox; any command/path detail lives in a collapsible, never the lead prose (SYS-118). Atomic (one action per step), honest on time. Fold the running order / "what to pick" INTO Step 1 — no separate running-order section.*

### Step 1 — <pick / trigger>
**What this is**: <plain explanation>. <If there's a running order or a backlog to pick from, it goes HERE — folded into the pick.>
**How — the exact words to type**: `<the literal prompt>` (the normal case) · `<variant>` (a specific pick).
<details><summary>Setup — do this first</summary> open a Claude session in the workspace; any path/option detail here, not above. </details>
| ✓ | Check |
|---|---|
| ☐ | <plain check for this step> |

### Step 2 … Step N — <same shape, one action each>
**What this is**: <plain explanation of what the system produces or what the operator does>.
**Where to find it** (on any "the system produced X" step): <the output folder + the gallery>, so the operator knows where to review.
**Review in the same chat** (on the review step): the operator reads the draft and replies in plain words in the SAME session that produced it ("approve it" / "change the headline to …"); it revises in place.
| ✓ | Check |
|---|---|
| ☐ | <plain check> |

**Cycle complete when**: <criterion>. Total operator time: ~<min>.

**The final step is always "Track" — and it's where the loop closes.** The operator tells the chat the cycle is done (+ any numbers worth noting); the SAME session records the cadence entry in `campaign.yaml` and re-renders the surfaces. The operator does NOT hand-edit the page. Because state is in the files, any session — even a fresh asset-production one — recognises the campaign.

**How the loop is wired (SYS-119).** The record + re-render is a numbered CLOSE step in each cadence engine (`debrief-weekly-engine`, `sb-podcast-weekly-assets`), not a thing to remember. It writes/updates a top-level **`cadence:` list** in `campaign.yaml` — one entry per cycle: `- cycle: <N>` · `edition`/`episode` · `ship_date: <YYYY-MM-DD>` · `status: done` (or `drafted` while held on a forward-flag). The campaign's **Phase-6 dashboard row uses `status_mode: derive_cadence`**, which reads that list and shows *"🔄 N of M cadence checkpoint(s) complete"* — computed, never hand-set, so it can't drift. (An empty/absent list reads *"⏳ Queued post-launch"*.) That is the whole loop: the engine records → the row derives → any fresh session reads the true position. KPI numbers are NOT tabled on the page; real reads come from the analyst on demand (§3). Say this to the operator in Step 5, plainly: *claude.ai + the AI Studio are your martech stack — the same chat that writes the edition keeps its records current.*
Status is data-driven (the cadence entry in `campaign.yaml` → dashboard Phase-6 row); the interactive checkboxes are a personal overlay, never the source of truth.

## §2 Escalation paths
| If this happens | Do this | Then (fallback) |
|---|---|---|
| <condition 1> | <first action> | <escalation if first fails> |
| ... | | |
(Sourced from `tenant/<name>/integrations.yaml#escalation`. Don't duplicate — cross-reference.)

## §3 What close looks like (when the campaign wraps)
Even an always-on cadence has a defined wrap (the KPI window is read, or the tenant retires the engine). Closing is not "stop publishing" — it's a short set of concrete moves (per `campaign-report.md` → `retro.md` → graduate):
1. **Pull the numbers** — export the performance data into `reads/` (or hand over the paths).
2. **Get the results report** — hand the files to the **marketing-forensic-analyst** → a standalone HTML readout (KPIs vs target, biggest funnel leak, what actually drove growth; every claim tagged, never invented). This IS the results readout.
3. **Run the retro + graduate** — per `retro.md`, scope = campaign-end: what worked / didn't → system updates, PLUS the graduation pass (winning templates → `tenant/library/`; tactical learnings → the tenant playbook; brand drift → the recs queue).
4. **Write the wrap note** — in the tenant voice: lead with one striking number, honest about misses, specific learnings.

Then the campaign **freezes** (read-only history); future campaigns inherit from the tenant layer, not this folder.
```

---

## Drafting discipline

- **§1 is THE thing.** Operator opens this on cadence day, works the numbered steps top to bottom, done. Everything else is reference.
- **Steps are atomic + plain.** One operator action (or one automated step) per numbered step. Don't batch. Each step leads with a plain "What this is"; the review step says to review IN THE SAME CHAT that produced the draft; a produce step says WHERE the output lands (folder + gallery).
- **Jargon-free prose (SYS-118).** No code identifiers (`hero_scrub.py`, exit codes), internal jargon (dogfood, multi-tenant, receipts guardrail), or unexplained acronyms in the lead prose — plain language a non-technical operator can act on. Command/path detail goes in a `<details>` collapsible only.
- **Fold the running order into Step 1.** No separate "running order" section — the pick + its options live in Step 1.
- **Honest times.** If a step takes 10 min, write 10.
- **Data-driven status + checkbox overlay** — identical to Phase 5: the dashboard's Phase-6 row is the truth (cadence entries with `status: done`); checkboxes are personal tracking only.
- **Checkboxes must be real inputs, not glyphs.** Every check cell uses `<input type="checkbox" class="phase6-cb">` + the small persistence script (localStorage; see the reference implementation) so it is actually clickable and remembers across a visit. **NEVER a static `☐` / `☑` glyph** — it renders but can't be ticked (the 2026-07-23 bug). Include a "clear for a new cycle" reset, since the checklist repeats each cycle.
- **Escalation mirrors integrations.yaml** — cross-reference, don't duplicate.
- **The system maintains the surface, not the operator.** The cycle's own session records the cadence entry + re-renders; the operator never hand-edits. State is in the files, so any session recognises the campaign (the system IS the martech stack — see the principle above).
- **No hand-kept KPI or cycle-history tables.** Cycle count → the data-driven dashboard; KPI → the analyst on demand from real data. Don't put a KPI or cycle-history table on the page — it can't be auto-filled from external tools and will go stale.
- **§3 close is always present** — even an always-on cadence defines its wrap (pull numbers → results report → retro + graduate → wrap note → freeze).
- **No phase-number drift** — storage keys, classes, headers, history labels all say *Phase 6*.

---

## Mode-specific guidance

### Mode 1 (the operator/Code)
- All steps execute on the operator's machine; "open Claude Code" = the operator's existing project; gates resolve in chat with the operator.

### Mode 2 v1 (Code+OneDrive on tenant machine)
- Operator opens Claude Code on THEIR machine pointed at THEIR tenant OneDrive; same skills/agents/commands.
- Gates resolve in chat with the tenant operator (the operator not in the loop unless escalated).
- Escalation = Slack/email to the operator per `integrations.yaml#escalation`.

---

## Cross-references

- **Phase 5 spec**: `docs/specs/phase-5-rollout.md` — the shared spine + step unit + status rule; what Phase 6 follows from.
- **Rollout Architecture v2 spec**: `docs/specs/rollout-architecture.md` §6 (Phase 6) + §6.2 (Mode 1 vs Mode 2 v1).
- **Plan spec**: `docs/specs/plan.md` §N.2 — upstream skeleton.
- **integrations.yaml spec**: `docs/specs/integrations.md` — §escalation block sourced here.
- **Brief spec**: §Cadence Shape — frequency + ownership_model upstream of this file.
