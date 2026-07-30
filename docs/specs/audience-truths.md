# Audience Truths — schema (durable tenant artifact)

**Spec version**: v1 · 2026-06-20. The **durable, slow-moving** per-segment audience truths for a tenant — distinct from the campaign-timely Insight Brief. Authored/refreshed by the **Insights Manager**; lives at `tenant-brand/<tenant>-audience-truths.md` (+ `.html`).

## What it is — and how it differs from the Insight Brief

| | Audience Truths (this) | Insight Brief (campaign) |
|---|---|---|
| Layer | **Tenant** (durable) | **Campaign** (per-campaign) |
| Time horizon | Enduring tensions that hold across campaigns | What's impacting the market *right now* |
| Built | Phase 0; refreshed each campaign | Phase 1, every campaign |

The Insight Brief's timely insights are **checked against** these enduring truths; validated/new truths **graduate UP** here at campaign wrap (graduate-then-cite). So campaign #2 starts from accumulated audience understanding, and the insight-scan doesn't re-derive what's already established.

## Where it lives + cadence
- `tenant-brand/<tenant>-audience-truths.md`. Seeded in Phase 0; **refreshed per-campaign** from the Insight Brief §4 (operator-gated at wrap). No separate quarterly clock.

## Schema

```markdown
# Audience Truths — <Tenant>
**Last refreshed**: <date>     **Source**: Phase 0 seed + campaigns <list>

## <Segment A>
- **Truth** — one sentence: the enduring tension/belief that holds for this segment.
  **Evidence** — named source(s) + date(s). **Since** — when first established. **Held across** — campaigns that confirmed it.
- … (2–5 enduring truths per segment)

## <Segment B>
…

## Retired / shifted
- Truths that no longer hold (with the date + why) — kept as audit, not active.
```

## Discipline (inherits the insight bar)
Same bar as the Insight Brief: a truth is a **non-obvious, evidenced audience tension**, not a demographic platitude. Each carries a named source + date. A truth that stops holding is **moved to "Retired / shifted"** with the reason — never silently deleted.

## How it's used
- The **insight-scan** reads it first (refresh-against, don't re-derive).
- The **Insights Manager** proposes additions in the Insight Brief §4; CM gates them at wrap → they graduate here.
- Feeds, indirectly, the CD (via the campaign Insight Brief) — the enduring truths give the timely insights their depth.

## Cross-references
`insight-brief.md` · `insights-manager/AGENT.md` · `phase-0-tenant-baseline.md` (the compound) · `segments` (who the audience is — complementary) · `research-library.md` (the evidence corpus).
