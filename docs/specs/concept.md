# Concept — Phase 2 Schema

A **Concept** is one creative option in the Phase 2 trio. CD authors three (Safe / Smart / Wild) for the operator to pick from.

**A concept is a CAMPAIGN IDEA, not a value proposition** (Phase 2 redesign retro R2, 2026-06-12). The tenant value proposition lives at tenant playbook §0 and reaches CD as **FIXED INPUT** in the dispatch — CD cites it and dramatises it toward the Brief's declared primary objective; CD never authors or re-invents it per campaign. A campaign idea = a mechanic + a hook + a calendar.

**Litmus test — the trio answers the question the Brief's objective asks (apply to every big idea before it enters the trio)**:
- **Market-facing campaigns** (the default — the objective is a market outcome): if the big idea answers *"why buy us"* it is a proposition — **reject and re-roll**; if it answers *"what will we do in market for N weeks"* it is a campaign idea — **accept**.
- **Foundation-shaped campaigns** (the objective is to establish strategy — value proposition, positioning, segments): the test FLIPS — *"why buy us"* answers ARE the deliverable. The trio = three **positioning / value-proposition routes** (Safe / Smart / Wild territories), claim-map-grounded and segment-evidenced, one Recommended. Campaign-idea answers are the reject case here.

CM's dispatch states which deliverable type is expected — CD never infers it. (Evidence: the 2026-06 Soundtrak re-run returned three propositions when the proposition was left open — a bug under a launch objective, the exact deliverable under a `foundation` objective.)

**Length target: 1 page per Concept** (3 pages for the full trio).

**Stored**: `campaigns/<slug>/concepts/<safe|smart|wild>.md` (markdown authoritative) + rendered side-by-side `concept-trio.html`. *(Notion storage reference removed 2026-06-12 — Notion retired in v3 architecture.)*

---

## Schema (one Concept)

```markdown
# <Concept name> — <Safe / Smart / Wild> [⭐ Recommended]

## 1. Big idea
One sentence. Channel-flexible. On-strategy. Brand-permissible. The campaign hangs on this.
A CAMPAIGN IDEA that dramatises the tenant's §0 proposition toward the declared primary objective — passes the litmus test ("what will we do in market for N weeks", never "why buy us").

## 2. Audience insight
The pivotal "aha" that earns the right to land. Why this specific audience will respond to this specific framing right now.
**Evidence-cited (REQUIRED — retro R3)**: the insight names its sources — segment map / battle cards / customer interviews / forensic data / VoC. An insight without evidence must be labelled **HYPOTHESIS** (usable, but the operator sees its weight honestly). A self-authored insight presented as fact is a spec violation.

## 2c. Competitive frame (REQUIRED, every concept — retro R4)
Three lines, drawn from the tenant competitive claim map (playbook §0):
- **Claim territories this concept occupies**: which open / contested territories it plants a flag in
- **Wallpaper claims it avoids leading with**: which category-generic claims (e.g. "AI + human", "cheaper/faster") it deliberately does not hero
- **Only-we line**: the single claim in this concept no named competitor can copy without breaking their model

Requires the tenant claim map to exist and be fresh — refreshed **per-campaign at brief time** (operator ruling 2026-06-12; the freshness scan is a Phase 1 step).

## 3. Key message

§1 is the *strategic argument* (internal/operator-facing). §3 is the *audience-facing distillation* — what Renee/the buyer actually hears, reads, or sees in passing. Distinct outputs; don't conflate.

- **Primary key message**: <one short audience-facing line — the elevator. Ideally inherits the Brief's one-line elevator from §Mandatories.>
- **Supporting messages**: <2–3 contextual reinforcements, each labelled with which surface they live on>
- **Hook lines / opening salvos**: <3–5 seed sentences a writer can sharpen>

### 3a. 15-second radio ad (REQUIRED, every concept — operator-set discipline 2026-05-28)

Every concept must include a **15-second radio script** as a clarity discipline. We may or may not ever produce or air the ad — that's not the point. **The point is the forcing function**: 15 seconds = ~40 voiced words = brutal constraint that exposes message-clarity gaps invisible in prose.

If the proposition can't survive 15 seconds of constrained read-aloud, it isn't tight enough yet.

**Specs**:
- 15 seconds · ~40 voiced words at AU-natural pace (~2.5–3 wps)
- Voice per tenant Brand Context §2 (Acme Co-voice, etc.)
- Tenant language norms (AU English, etc.)
- All Brand Context mandatories apply (no banned words / framings)
- Sign-off on brand name + (where relevant) campaign signature line
- Structure: problem → mechanic → proposition → sign-off

**Format in concept doc**:

> *[15 seconds — voice direction]*
>
> *"...script..."*

Followed by:
- Word count
- "What this script forces clear" — bullets identifying which strategic elements the constraint sharpened
- "How this carries into other surfaces" — explicit statement that all other concept copy (Reels scripts, banner ads, email opens) must be testable against the radio ad's logic chain

## 4. Moodboard / creative treatment — **renders as a VISUAL board, not text** (changed 2026-06-23)
**The operator must SEE the look, not read a description of it.** §4 renders on the operator surface (concept page + trio) as a **Pinterest-style visual board** — a masonry/tile grid — authored as inline HTML in the concept md (the render pipeline passes inline HTML/SVG through). The prose below becomes captions/labels on the board, not the main event.

**The board tiles (use OWNED visuals as images; copyrighted refs as cards — fair-use internal, never reproduced in published assets):**
- **Hero / cover tile(s)** — screenshot(s) of the concept's cover/hero mockup(s) (`mockups/*.html` → PNG) — the strongest, most real tiles. The single biggest visual upgrade.
- **AI preview tile (REQUIRED at trio author time, not deferred)** — one generated sample tile per concept showing the concept's structural delta against the locked brand register. Via `/replicate-generate` at trio authoring (~$0.04/concept). Saved to `concepts/previews/<safe|smart|wild>-tile.png`. (If the brand kit is still pending, mark the tile slot "pending brand kit" — don't fake it.)
- **Mechanic tile** — the §4c SVG, shown inline as a board tile.
- **Palette chips** — the accent/heat/primary swatches as colour tiles (CSS), labelled.
- **Type specimen tile** — display + data-sans intent, set in the actual intended faces where possible.
- **Reference cards** — the 3–5 named visual references as styled **cards** (name + "what to steal — the move, not the surface"). Copyrighted refs are NOT reproduced as images on a published surface; the moodboard is internal/operator-facing, so a thumbnail is fair-use-permissible but a clean text card is the safe default.

**The prose (kept, as board captions / a sidebar):**
- **Aesthetic direction**: <one paragraph — mood, palette intent, typography intent, imagery direction>
- **Hero visual**: <one line describing the canonical expression — captions the hero tile>
- **"This not that"**: <3–4 sharpening contrasts>
- **Deep board**: link to `concept-moodboard.md`/`.html` (the full internal reference board — copyrighted refs under fair use).

**Visual-distinctness still holds**: the three concepts' boards must look *different at a glance* (different hero tile, palette, register) — three skins of one board is a fail.

## 4b. Tactical precedents (REQUIRED, every concept)

2–3 NAMED operators / brands / newsletters who ran the same *mechanic* (not just the same theme) at scale with public numbers where possible. Sourced via WebSearch / WebFetch at trio authoring — these are not optional creative inspiration; they are evidence the concept's mechanic works for similar-shape businesses.

**Layout discipline (CM when stitching the trio surface)**: §4b precedents live *inside each concept block*, immediately below that concept's §4a description — NOT aggregated into a separate "evidence stack" section above the three concepts. Operator reads top-to-bottom per concept; lifting evidence to a header section forces them to scroll and cross-reference. Evidence next to the mechanic = readable. Evidence above the concepts = friction.

Per precedent: operator name + asset · what they did (one sentence) · outcome with real numbers if available (otherwise "proxy evidence — no public number") · transferable principle (one sentence) · source URL.

Format as a table:

| Operator | What they did | Outcome | Transferable principle |
|---|---|---|---|
| ... | ... | ... | ... |

**Honest evidence meta-note** (one paragraph, end of §4b across all three concepts): which concept has the strongest evidence base, which is thinnest. If one concept's precedents are weak or B2C-only, say so. **Do not manufacture evidence.** Thin evidence is itself a strategic signal — Wild concepts often have thin evidence by definition (highest-upside / lowest-precedent) and the operator deserves to know that.

## 4c. Concept mechanic diagram (REQUIRED, every concept)

An inline SVG diagram (authored by CD, embedded in concept markdown) showing the **reader-flow / conversion mechanic** of this specific concept — how a reader moves from awareness surface through to conversion event, and where this concept's structural delta sits in that flow.

Saved to `campaigns/<slug>/concepts/diagrams/<safe|smart|wild>-mechanic.svg`. Referenced in the concept markdown as `![<concept> mechanic diagram](diagrams/<concept>-mechanic.svg)`.

Drawn in tenant brand palette (pull from Brand Context §3 — primary, accent, background colors). System-UI typography is fine; brand fonts not required at this resolution. ~600–800 wide × 300–360 tall viewBox is the right scale for trio side-by-side.

Purpose: prose is harder to compare than a diagram. Operator needs to *see* the mechanic next to the other two, not infer it from §1 prose.

## 5. Narrative architecture
The beats / movements the campaign progresses through. 3–6 beats. Each beat names: when, where (channel surface), what (the move).

## 6. Channel rollout (high-level)
Which surfaces the concept lives on, with a one-line narrative hook per surface. Detailed tactic list lives in the Plan, not here. **Draw on the Insight Brief §2 routes to market** (the budget- and time-filtered, evidenced map of how each segment is reachable — media + community + **partnership/co-GTM + intermediary [VCs/incubators/associations] + advocacy**) the CM injected: prefer routes the audience actually trusts over generic surfaces, and — especially on a low budget — consider whether the concept can be **built around a partnership/co-GTM play** (a route the §2 surfaced) rather than bought reach. The §2 routes are *intelligence that informs* this rollout — you still own the creative call (lean in, stretch, or deliberately depart, with reasoning); they are not a fixed media plan, and a route flagged slow-build won't serve a short-deadline campaign.

## 7. Pitch rationale (Recommended option only)
Why this concept earns the Recommended mark — tying the creative call to the Brief's KPI in 4–6 bullets.

## 8. Risks & trade-offs
The honest list. What this concept makes harder, what it sacrifices, what could go wrong. 2–3 risks with one-line mitigations each.

## 10. Divergence → convergence — the road not taken (EXPOSED on the operator surface, at the bottom)
**Changed 2026-06-23 (operator):** the divergent/convergent thinking is no longer buried audit — it is **shown to the operator at the bottom of the operator surface** (each concept page + the trio), as a clean *"Considered & dismissed — and why"* block. Seeing the ideas that were deliberately killed is what proves the three options are a *convergence*, not the first three ideas — it earns trust in the recommendation. Two parts:
- **Kill register (EXPOSED — the operator reads this)** — the top territories/ideas that did NOT make the trio, each with a one-line reason ("off-claim-map" · "not compliance-clearable" · "redesigned into Smart" · "off-budget"). The dismissed *ideas* are the point: name them plainly, lead with the idea, then the reason. A silent drop defeats the record. Render it as a visible section at the bottom (not a `<details>` the operator must open, and not a pointer to another file).
- **Lenses swept (deeper audit — may stay collapsed)** — the named creative lenses CD ran (format · emotional-register · protagonist · mechanic · cultural-borrow · channel-native · contrarian · tenant-specific) + the practitioner-framework principles applied (the playbook — `craft/frameworks/Soundtrak_Playbook.md`). This is the methodology trail; it can sit in a collapsed `<details>` below the kill register.

(§9 Revision freshness check sits above §10. The kill register half of §10 is now an **operator surface**; only the lenses-swept trail remains pure audit.)
```

---

## Trio discipline

- **Three options, genuinely distinct.** Safe = lowest risk to the proposition. Smart = the strategic sweet spot. Wild = highest-upside / highest-risk creative swing. Not three variations of the same idea.
- **One marked Recommended** with §7 pitch rationale. The other two get §1–§6 only.
- **Trio shares one audience insight** by default. Wild may test a competing insight only with explicit flag.
- **Big Idea test**: must pass channel-flexible + on-strategy + brand-permissible + **compliance-clearable** (won't be blocked at the Stage-2b governance gate, where a Compliance Profile exists) + the proposition litmus (campaign idea, not value proposition) before entering the trio. CD kills candidates before pitching.
- **Divergent→convergent method (REQUIRED)**: the trio is the *output* of a named-lens sweep + a visible kill register (CD AGENT.md step 4), recorded in §10. A trio presented with no sweep / kill register behind it is incomplete.
- **Proposition guard**: on a market-facing campaign, if more than one candidate keeps answering "why buy us", the dispatch was missing the §0 fixed input — CD flags back to CM rather than shipping propositions dressed as concepts.
- **Targeting guard**: the Brief's selected segment is FIXED INPUT — CD mines it for the §2 insight, never re-selects the target. If CD believes the segment is wrong for the declared objective, that's a flag back to CM with reasoning, not a quiet re-targeting.
- **Visual distinctness**: three concepts must produce visually distinct moodboards, not three variations of the same register.
- **Visuals are required, not optional — and §4 is a VISUAL BOARD, not text**: every concept ships with a §4 Pinterest-style board (hero/cover mockup tiles + AI preview tile + palette chips + type specimen + §4c mechanic SVG + reference cards), authored as inline HTML so the operator *sees* the look. Operator-set 2026-05-28 (*"I want visuals in every concept design."*) + 2026-06-23 (*"the moodboard should be more visual, like a Pinterest board"*). CD must not surface a concept with a text-only moodboard. CM (authoring integrated/Selected concepts) must not strip the board — tiles carry forward, and any new integrated hero is added as a tile inline.
- **Divergent→convergent is EXPOSED (2026-06-23)**: §10's kill register renders as a visible *"Considered & dismissed — and why"* block at the bottom of the operator surface (concept page + trio) — not buried, not a `<details>`, not a pointer to another file. The operator sees the road not taken.

## Revision discipline — no prose drift (REQUIRED — every concept revision, added 2026-06-12)

Concepts that are revised in place accumulate **sediment** — the document slowly becomes an edit-trail instead of a concept. A full review of all campaigns to date (2026-06-12) found five recurring drift forms; a revision MUST eliminate all five. **A revision RE-AUTHORS the concept clean to the §1–§8 structure; it does not annotate the previous version.**

| Drift form | What it looks like | The rule |
|---|---|---|
| **Changelog-in-header** | `Status: Approved v1.4` + `(v1.0 → v1.1 → v1.2 → v1.3 → v1.4 …)` / `v1.1 revision… v1.2 revision…` in the Status/Authored lines | Header carries ONE line: current status + (if chosen) Recommended/Selected. The full version history lives ONLY in the bottom audit block. |
| **Inline version stamps** | `(updated 2026-05-28 v1.3)`, `operator-added`, `(was 5d, renumbered 5e)`, `v2 bookmark mechanic` woven through prose | Zero version stamps in the body. The body reads as the current truth with no memory of prior drafts. |
| **Provenance seams** (integrated concepts) | `(inherited from Safe — load-bearing)`, `(Wild v2)`, a "Source concept" column | The integrated concept reads as ONE whole (per [[feedback_integrated_concept_reads_as_whole]]). Which-source-came-from-where goes ONLY in the bottom audit block. |
| **Strikethrough / deferral sediment** | `~~share-card feature~~ DEFERRED`, duplicate "Risks" sections (§6 + §8), "see §6 above" pointers | Deferred items are CUT from the body to `future-phases.md` + named in one "Deferred" line. No strikethroughs, no duplicate/pointer sections. |
| **Accreted sub-numbering** | §4.0 · §4.1a · §4.2a · §4.2b · §4.3a · §4b · §4c · §5b · §5c · §5d · §5e | Numbering stays canonical §1–§8 (+ the spec's defined sub-sections §3a/§4a/§4b/§4c). New content goes in its canonical section; if it truly needs a home, an appendix below the audit rule — never a new mid-document sub-number. |

**The audit block (below a horizontal rule, framed "for the record, not the cold reader")** is the ONE home for all revision history: the changelog, the source-concept list (for integrations), the §9 freshness-check table, and any process notes. A cold reader who never scrolls past the rule still gets a clean, current, whole concept.

**Test**: hand the concept (above the rule) to someone who has never seen the trio. If they can tell it was version 4, or that it was merged from Safe+Wild, or which lines were "added later" — it has drift. Re-author until they can't.

## Revision freshness discipline (REQUIRED — every concept revision)

**The pattern**: prose updates fast; embedded artifacts (AI tiles, SVG diagrams, ASCII architecture diagrams, asset rosters) update slow. Whenever a concept undergoes a substantive revision — mechanic pivot, channel-mix change, key-message change, new surface added — every embedded artifact must be either updated to match the new state OR explicitly marked "carried forward — still applies."

**The mechanic**: every concept doc ends with a `§9 Revision freshness check` table. One row per embedded artifact. Columns: artifact name · current state at this version · last touched · status (✅ fresh / ✅ carried forward — still applies / 🟡 TBD / ❌ drift).

**The discipline**: at revision time, CM walks the table top to bottom. For each row, ask:
1. Does this artifact still depict the campaign's current truth?
2. If yes — mark "carried forward" with the version it was last touched.
3. If no — update it before re-rendering. SVG diagrams regenerated. AI tiles flagged for regeneration via `/replicate-generate`. ASCII diagrams hand-updated. Asset rosters synced.
4. If TBD (operator pick pending) — mark explicitly.

**Why this matters**: visual artifacts are the operator's primary cognitive shortcut for "is this concept currently the one we're shipping?" If a diagram lags behind the prose, the operator gets confused — and that confusion correctly reads as "the system isn't keeping itself honest." Caught 2026-05-28 in Acme Co Phase 2 when CM updated Wild prose v1 → v2 but left the v1 event-mechanic SVG embedded for two revision cycles.

**Applies to**: Concept revisions (Phase 2 · all versions). Also: Brief revisions (Phase 1), Plan revisions (Phase 3), Per-Step Brief revisions (Phase 4a) — every artifact that embeds visuals or structured tables runs a parallel freshness check at its own §N.

**CM enforcement**: before re-rendering after any concept-revision write, CM walks §9 explicitly. The walk is logged in the concept history. If an artifact at "✅ fresh" status is later caught as stale, that's a P1 process failure — flagged in retro, root-caused, and the spec strengthened.

## Drafting discipline

- 1 page per concept. If you're writing more, ask why.
- Use the inspiration repository (`tenant/inspiration/`) — pull 3–7 relevant references per concept; cite in §4.
- Anti-clone: steal the move, not the surface. If a concept reads as a clone of a named reference, re-roll.
- Audience insight ≠ audience description. The insight is the pivotal pattern; the description belongs in the Brief.

## What this Concept does NOT contain

- Per-asset specs (lives in Per-Step Briefs)
- Tactic checklist with owners + dates (lives in Plan)
- Brand context (lives in Brand Context record)
- Detailed visual generation prompts (lives in Per-Step Briefs when an asset needs one)

## Anti-pattern: surfacing the trio without visual + evidence

If you find yourself writing the trio as prose-only with no AI preview tiles, no tactical precedent tables, and no SVG mechanic diagrams — stop. The operator can't pick blind. **Operator needing to ask "where's the visualisation?" or "where are the precedents?" is a CD output gap, not a creative-direction conversation.** §4 AI previews + §4b precedents + §4c mechanic SVGs are required at trio author time, every campaign, not on operator request.
