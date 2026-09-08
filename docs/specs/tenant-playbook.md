# Tenant Playbook — Tenant-Layer Schema (v1)

**Spec version**: v1 · Authored 2026-06-10 at the three-layer model codification (System / Tenant / Campaign — see [`docs/workflow.md`](../workflow.md) §The three layers).

The **Tenant Playbook** is the durable per-tenant record of **tactical learnings** — what we have learned *works* for this tenant, accumulated across campaigns. It is the inheritance vehicle that makes campaign #2 for a tenant faster and cheaper than campaign #1.

**Not to be confused with**:

| Artifact | Holds | This playbook's relation |
|---|---|---|
| **Brand Context** (`tenant-brand/<tenant>.md`) | Voice / visual identity / positioning | Playbook holds *tactics*, not brand |
| **Practitioner frameworks** (`craft/frameworks/`) | The practitioner discipline / principles that apply across ALL tenants | This playbook is tenant-specific |
| **Recommendations queue** (`tenant-brand/_recommendations-queue.md`) | Brand Manager's *proposed* Brand Context changes awaiting verdict | Playbook entries are already operator-approved |
| **`tenant/library/`** | Reference pieces / gold standards (whole artifacts) | Playbook holds *learnings about* what works, not the artifacts themselves |

**Stored**: `tenant-brand/<tenant-slug>-playbook.md` (+ rendered `.html`). CM is the only writer.

**Written**: ONLY at gated graduation moments (campaign wrap, retros). Nothing lands here silently — every entry is operator-approved. Per the **graduate-then-cite** rule, a learning must land here BEFORE a later campaign can use it; sibling campaign folders are never read directly.

---

## Schema

```markdown
# <Tenant> — Tenant Playbook

**Tenant**: <slug>     **Status**: Live     **Last graduation**: <YYYY-MM-DD>     **Source campaigns**: <list or "(none graduated yet)">

## §0 Value proposition + positioning (DURABLE — every campaign inherits; never re-asked at brief)
The strategic positioning layer (voice/visual stay in Brand Context). Contents:
- **The value proposition** — one sentence + the buyer triad it serves
- **Gate-survived positioning lines** — operator-approved lines from live assets, reusable across campaigns
- **Competitive claim map** — wallpaper / contested / open-territory buckets + nearest named threat. Refresh: PER-CAMPAIGN at brief time (Phase 1 freshness scan — operator ruling 2026-06-12); quarterly battle-card review as backstop
- **Only-we lines** — claims no named competitor can copy without breaking their model
- **Segment-map pointer** — link to the tenant segment map, the evidence base for all targeting + audience-insight work. Home (2026-06-12 ruling): the segment map is a TENANT-LAYER artifact (`tenant-brand/<tenant>-segments.md`) that campaigns cite; battle cards are its sales-facing rendering. Pre-ruling pointers into campaign assets stay until that tenant's next graduation moment — no retrofit.
- **Fit evidence base** — per-segment product-market-fit status (proven / promising / unproven) with evidence (what's selling, to whom, why · VoC · pricing posture), FINDING/HYPOTHESIS-tagged. Informs the Brief's objective fit-check (challenge, not block).
Cited as FIXED INPUT by every campaign Brief and every CD concept dispatch. The CD dramatises §0 toward the Brief's primary objective; it never re-invents it.

## §0a Disqualifiers / hard-nos (DURABLE, ALWAYS-LOADED — the inverse of §0; never re-asked at brief)
The sharp, quotable statement of who we explicitly do NOT target and what we will NOT say. The inverse of the audience-truths: where §1/audience-truths say what holds for the people we serve, this says who we walk away from and which angles are off the table — so no campaign re-derives a no the tenant has already settled. Always-loaded alongside §0 (FIXED INPUT to every Brief + sliced into every Per-Step Brief). Four required fields:
- **(a) Audiences / segments we do NOT address** — the buyer types, verticals, deal sizes, or geographies this tenant explicitly walks away from (with the one-line *why* — wrong economics, wrong fit, out of scope).
- **(b) Angles / claims we will NOT make** — positioning lines, hooks, and framings that are off-limits even when they'd "work" (with the *why* — dishonest, off-brand, invites the wrong buyer).
- **(c) Off-limits competitor framings / topics** — named-competitor knocks, contested categories, or subject areas we don't engage in published copy.
- **(d) Hard brand / legal nos** — the bright lines. **For prohibited *claims*, this field POINTS to the Governance Compliance Profile §2 (prohibited & restricted claims) by reference — it does NOT copy them** (graduate-then-cite: `tenant-brand/<tenant>-compliance.md` §2 is the single source of truth; duplicating it here would let the two drift). List only the brand-level nos that are NOT compliance claims (e.g. internal-shorthand never used in public), plus the one-line cite to §2.

## §1 Audience learnings
What we know about THIS tenant's audience that future briefs should inherit.
| Learning | Evidence | Source campaign | Date |

## §2 Channel + timing learnings
Send windows, platform performance, cadence patterns.
| Learning | Evidence | Source campaign | Date |

## §3 Format + asset learnings
Which forms / structures / review shapes perform for this tenant.
| Learning | Evidence | Source campaign | Date |

## §4 Messaging learnings
Hooks, angles, framings that landed or flopped — tactical, beyond brand voice.
| Learning | Evidence | Source campaign | Date |

## §5 Operational learnings
Approval workflows, stakeholder quirks, compliance constraints, publishing logistics.
| Learning | Evidence | Source campaign | Date |

## §6 Graduation log (append-only, most recent first)
| Date | Entry | Source | Approved by |
```

---

## Entry discipline

- **Evidence-tagged** — every learning's Evidence cell leads with **FINDING** (strong, consistent evidence — you'd defend it) or **HYPOTHESIS** (directional; n small or confounded), per the forensic-analyst convention. HYPOTHESIS entries graduate to FINDING when later campaigns confirm them; they get culled when they don't.
- **Source-cited** — name the campaign + the artifact/data that produced the learning.
- **One line per learning** — the playbook is a slicing source, not an essay. Detail lives in the source campaign's retro/analysis (frozen history).
- **Culled, not hoarded** — at each graduation gate, CM proposes removals for stale or contradicted entries alongside additions. A playbook full of dead learnings is worse than an empty one.

## How it's used

- **Per-Step Brief slicing** (Phase 4a): CM pulls the 1–3 most-relevant entries into the brief's Strategy slice (see [`per-step-brief.md`](per-step-brief.md) §2), quoted verbatim with evidence tag + `Playbook §N` citation. Producer reads the slice; never loads this file.
- **Phase 1 Fact-Find**: for any tenant with prior campaigns, CM reads the playbook at brief intake — pre-fills brief fields and cites entries instead of re-asking the operator.
- **Phase 2**: CM passes relevant entries to CD in the trio invocation as tactical priors — and §0 in full as FIXED INPUT (proposition + claim map + only-we lines + segment pointer) + **§0a Disqualifiers / hard-nos** as a convergence filter (the trio can't surface a concept that targets a walked-away segment or makes an off-limits claim).
- **§0a is always-loaded** (like §0): CM inherits it with the baseline at Phase 1 brief intake and slices it into every Per-Step Brief alongside the audience-for-this-asset, so Producer always knows the bright lines. For prohibited *claims* it carries only the POINTER to the Compliance Profile §2 (graduate-then-cite); Governance §2 remains the single source of truth.
- **New-tenant onboarding**: §0 is seeded by a competitive scan before first concepts (see `docs/playbooks/onboard-tenant.md` §1.2); campaign-wrap graduations populate the rest.
- **Foundation-shaped campaigns** (the Brief's objective is strategy development): when the foundation is absent or contested, the campaign engine builds it — strategy artifacts as the asset list, positioning routes as the trio, wrap graduation as the foundation approval. See `docs/workflow.md` §Foundation campaigns + `plan.md` §Asset list discipline.
- **Tenant kit** (productization): this file ships in the tenant kit — it is part of the compounding value a client tenant accumulates.

## Graduation workflow (campaign wrap)

1. CM assembles graduation candidates from the closing campaign across all four destinations: tactical learnings (HERE) · winning assets (`tenant/library/` via `/library-add`) · brand drift (`_recommendations-queue.md`) · system lessons (memory rules / specs via retro §4).
2. **ONE operator decision moment**: a graduation table — candidate · destination · evidence · proposed verdict. "No candidates" is a valid outcome but must be stated explicitly, never skipped.
3. On approval: CM writes the entries, appends §6 log rows, re-renders HTML.
4. Rejected candidates are logged in the campaign retro (frozen history), not here.

## Cross-references

- [`docs/workflow.md`](../workflow.md) §The three layers — the constitutional model
- [`per-step-brief.md`](per-step-brief.md) §2 — playbook slice injection + graduate-then-cite authoring rule
- [`retro.md`](retro.md) §4 — tenant-layer graduation as a retro output class
- CM SKILL.md §Campaign wrap — graduation gate
- Memory: `project-system-tenant-campaign-layering.md`
