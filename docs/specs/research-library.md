# Research Library — schema (SHARED, faceted — like the gold-standard library)

**Spec version**: v2 · 2026-06-22 (was v1 per-tenant; **changed to shared** per operator ruling — most research, especially human-behaviour research, is cross-tenant). A **single shared** corpus of **public/external** market + audience research, faceted so any tenant's insight-scan pulls the relevant subset. Lives at `tenant/research-library/` — a sibling of the shared creative `tenant/library/` and `tenant/tactics/`. Read + grown by the **Insights Manager** / `insight-scan` skill.

## Shared, not per-tenant — and why it's safe
- **Shared** (operator-level, all tenants), exactly like the gold-standard **creative** library. A WEF / OECD / IPSOS / Gallup paper found for one tenant serves the next; **human-behaviour research is essentially universal** (behavioural science, generational values, "what professionals want from work" apply across tenants). Find once, cite forever, everywhere → it compounds harder than a per-tenant silo.
- **It does NOT break tenant data isolation.** The library holds only **published, external research** — never tenant-confidential data. The constitutional rule is unchanged:
  - **Public research → here** (shared).
  - **A tenant's own proprietary data** (e.g. ACME CO's placement dataset) → stays **tenant-scoped** (`tenant/<slug>/`), never shared.

## What it is — and is NOT
- **IS**: WEF / OECD / McKinsey / PwC / IPSOS / Gallup / Pew reports, government workforce data, **behavioural-science + psychographic/values studies**, academic/ethnographic papers, key trade features — the authoritative evidence base that grounds insights in named, dated sources.
- **NOT** the creative library (`tenant/library/` = gold-standard creative references). NOT a tenant's confidential first-party data.

## Structure
```
tenant/research-library/
  INDEX.md                  ← the faceted catalogue (below)
  <source-slug>.md          ← per-paper: faithful summary + key data + link + citation
```

## INDEX.md — faceted entry schema
| Source | Publisher | Date | **Vertical** | **Audience** | **Topic** | **Layer** | **Source type** | Key finding (one line) | Added by | Link |
|---|---|---|---|---|---|---|---|---|---|---|
| *Future of Jobs 2025* | WEF | 2025-01 | universal | all | workforce/skills | market | research-firm | … | campaign-X | url |
| *ATWD Career Intentions* | AITSL | 2025-10 | education-workforce | educators | attrition/motivation | human-behaviour | government | workload>pay drives exit | ACME CO Q2-26 | url |

Facets (so the scan filters precisely):
- **Vertical** — `universal` (behavioural science / values / demographics — applies to all tenants) · or a specific vertical (`education-workforce`, `fintech`, `pro-services`, …).
- **Audience** — the segment type the finding speaks to.
- **Topic** — workforce · demographics · values · behavioural-science · attrition · etc.
- **Layer** — **`market`** (what's happening) vs **`human-behaviour`** (what makes people tick) — the key facet for human-insight work; the scan pulls human-behaviour entries first for the human layer.
- **Source type** — consultancy · research-firm · government · academic · trade.

Each significant paper also gets `<source-slug>.md` (citation · faithful summary + the data points an insight can cite · relevance · link). Summarise + cite + link — don't reproduce copyrighted text wholesale.

## How the insight-scan uses it
**Cite-first, filtered.** Before any web call, the scan reads the INDEX filtered to **`vertical = <this tenant's vertical>` OR `vertical = universal`** (+ the relevant audience/topic/layer). It cites lodged papers rather than re-fetching, and prioritises **`layer = human-behaviour`** for the human-insight layer.

## Lifecycle
- **Seeded in Phase 0** — onboarding lodges the new tenant's vertical research + any universal gaps (tagged accordingly). Phase 0 *contributes to* the shared library; it isn't a per-tenant artifact.
- **Grows per-campaign** — the Insight Brief §4 proposes additions; CM gates them at wrap → they graduate into the shared INDEX (faceted).
- A **`/research-add`** skill can be extracted later (mirroring `/library-add`).

## Cross-references
`insight-scan` skill (reads this first, faceted) · `insights-manager/AGENT.md` · `insight-brief.md` (§3 cites it; §4 proposes additions) · `audience-truths.md` (tenant-scoped — the per-tenant truths these public papers help evidence) · `tenant/library/` (the parallel shared *creative* library) · `phase-0-tenant-baseline.md`.
