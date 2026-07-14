# Practitioner frameworks (`craft/frameworks/`)

The transferable strategic discipline that ships **with** Soundtrak AI Studio — the "AI configured on practitioner discipline" the product is built on. These are reusable **frameworks** (how to *think*), distinct from the tactical `craft/` lenses (how to *make* an asset) and from any tenant's own brand specifics (voice / positioning / proof), which live in the tenant Brand Context and are built at Phase 0.

## What's here

| File | What it is |
|---|---|
| [`Soundtrak_Playbook.md`](Soundtrak_Playbook.md) | **Strategic doctrine — the 53 principles.** Commercial strategy · brand & positioning · content / research / owned-media · GTM & sales · customer intelligence & UX · operations · technology & AI · the six Soundtrak Consulting principles. *How Soundtrak thinks* — the strategic backbone every campaign inherits. |
| [`applied-marketing-frameworks.md`](applied-marketing-frameworks.md) | **Generic applied toolkit — three reference catalogues in one** (section-anchored): **§1 Mental models** (~60 buyer-psychology / persuasion / pricing / growth models + challenge→models quick-ref) · **§2 Conversion audit (CRO)** (7-dimension page-audit + Quick-Wins/High-Impact/Test-Ideas shape) · **§3 Voice of customer** (VOC extraction + evidence-built personas). *How anyone executes.* Mined (re-expressed, tenant-agnostic) from [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT), 2026-07-14, per SYS-062. |

**Doctrine vs toolkit — the boundary that prevents overlap.** The Playbook owns the tenant's strategic *doctrine*; `applied-marketing-frameworks.md` owns the generic applied *toolkit*. Where a model appears in both (e.g. Jobs-to-Be-Done), the **Playbook owns the strategic principle and the applied file owns the execution toolkit — cross-link, don't duplicate.** Pull **by section**, not the whole file.

## How the agents use it

- **Campaign Manager** (Brief) and **Creative Director** (Concepts) read the playbook as **FIXED INPUT** — the strategic lenses to think *through*, not re-author. A concept cites the principle it applies or tests (e.g. *"this is principle 13 — challenger intellectual authority — in landing-page form"*).
- The playbook is the **generic discipline**. The **tenant's own** voice, positioning, segments, and proof come from the tenant Brand Context (`tenant-brand/<tenant>.md` + playbook §0), authored at Phase 0 — never from here. (So a tenant sounds like *themselves*, applying these frameworks.)
- **Producer** never reads this raw — CM slices the relevant principle into the Per-Step Brief.

**When to pull `applied-marketing-frameworks.md` (by section):**
- **CD** — pull **§1 Mental models** when shaping a concept's persuasion (name the model the concept applies/tests); pull **§2 Conversion audit** when the concept *is* a landing/pricing/feature page.
- **CM → Producer** — slice **§1** (copy/page psychology) and **§2** (page audit) into the Per-Step Brief for web / landing / pricing / ad assets.
- **Insights Manager + CM (Brief interview)** — pull **§3 Voice of customer** to ground the audience insight in verbatim customer language.

## Extending it

Add your own frameworks as `craft/frameworks/*.md` and cite them the same way. The system reads whatever is here.
