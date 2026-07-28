# Battle Cards — Asset spec

**Type**: Internal-only sales-kit reference. NEVER shipped to a prospect.
**Audience**: the tenant's operator (founder / sales-rep / practitioner) opening the card before discovery calls + scanning mid-call.
**Form factor**: prints clean on ~2 pages A4 single-sided. Markdown + rendered HTML.
**Canonical reference implementation**: `campaigns/soundtrak-ai-system-overview-2026q2/assets/17-battle-cards/`

## Why a dedicated spec

Battle Cards have specific quality criteria that don't apply to other sales-kit assets. They're deal-time scannable tools, not exhaustive product sheets. Producer drafting Battle Cards without this spec defaults to product-sheet shape (long-form prose, 10+ objections, dense feature comparisons) which fails at the moment of actual use. This spec encodes the Gong-aligned battle-card best practice as the system default.

## Four pillars (the Gong principles, codified)

### Pillar 1 — Scannability + Rule of Three

Reps reference Battle Cards in the heat of a live call. Layout must make critical information instantly discoverable.

- **Rule of Three**: every section maxes at 3 items. 3 differentiators · 3 main objections · 3 competitor scenarios · 3 pricing scenarios. Cognitive load above 3 collapses mid-call scannability.
- **No blocks of text**: bullets, short sentences, talking-point format. Paragraphs are banned in §1-§4. Reserved for the optional extended reference appendix only.
- **30-second top-of-card test**: §1 must be scannable in 30 seconds before a call. Operator opens it on phone, walks to coffee, opens the laptop, takes the call.

### Pillar 2 — Scenarios + Landmines + Fact-Impact-Act

Content is centred on real buyer conversations, not feature matrices.

- **Scenario-first** competitor analysis: each competitor card opens with *"Prospect says: '[verbatim what they say]'"*. Not a feature-comparison grid.
- **Landmines**: every competitor section carries one smart-question the operator asks that surfaces the competitor's hidden weakness. Example: *"How does your current system handle [X] without requiring custom coding?"* Each Landmine should expose a structural failure the competitor can't defend.
- **Fact-Impact-Act framework**: every kept objection AND every competitor scenario uses this three-label structure with the labels visible to the reader:
  - **Fact**: the factual competitive difference (1 line)
  - **Impact**: the consequence for the buyer's business (1 line)
  - **Act**: the verbatim response + the specific question the operator asks next (1 line)
- The three-label structure is non-negotiable. It's the discipline that prevents Battle Cards drifting back into prose.

### Pillar 3 — Frontline evidence

Credibility lives in real engagement data, not assumptions.

- **Win-loss interviews**: anchor "How to Win" sections in actual buyer feedback from lost deals (where the operator has it). When the operator is founder-only with no separate sales team to interview, use first-person practitioner experience explicitly framed as such.
- **Named engagements vs archetypal patterns**: where the operator has permission to name real clients, do. Where not, use archetypal-prospect language ("founders at this stage typically say…") and FLAG to the operator at production time so they can choose to upgrade.
- **No fabricated metrics**. Producer never invents win-loss numbers. Either real engagement data flagged for operator confirm, or archetypal framing transparently labelled as such.

### Pillar 4 — Fresh + accessible

Stale Battle Cards break credibility with the prospect.

- **Freshness stamp at top of card**: `Last reviewed: YYYY-MM-DD · Owner: <name> · Next review: YYYY-MM-DD`. Mandatory.
- **Default review cadence**: quarterly (90 days). Adjust per tenant if frequency of new objections / pricing changes warrants tighter.
- **Named owner**: not the AI agents. A human operator (typically the founder / sales lead / product marketing) is the named owner of the Battle Cards. Updates route through them.
- **Accessibility**: Battle Cards live in the campaign's `assets/` folder + render to HTML via `render-html` skill + surface in the per-campaign gallery. NOT buried in shared drives. Future enhancement: CRM-snippet export (Hubspot, Salesforce, Close).

## Required structure

The Battle Cards `asset.md` MUST contain these sections in this order:

### Header block

```
# Battle Cards <vN> — <Tenant> Sales Kit Reference

**Asset**: #<id> · **Status**: <status> · **Form**: Internal-only reference card
**Last reviewed**: YYYY-MM-DD · **Owner**: <name> · **Next review**: YYYY-MM-DD
**Audience**: <operator name> only. Open before discovery calls. Mid-call scannable.

> **Never send this to a prospect.** Internal scaffolding. No CTAs, no marketing copy.
```

### Honest audit table (only on revisions)

On v2+ versions, surface a pillar-by-pillar table showing what v1 failed on + what v2 fixed. This is the rationale the operator reads in 1 minute before approving the revision.

### §1 Quick reference (top of card)

Scannable in 30 seconds. Single page top.

- **3 winning differentiators** (Rule of Three): the 3 things that uniquely belong to this tenant vs. competitors
- **Pricing anchor**: one line (e.g. `$X-Y/m + ~$Z setup. Walk-away under $W total.`)
- **Screening question** (verbatim): the one-line qualifier the operator drops in every CTA

### §2 Competitor scenarios (3 only)

For each of 3 competitors:
- **Scenario** (Prospect says: "...")
- **The Landmine** (smart question operator asks)
- **Fact / Impact / Act** (three labels visible)
- **How to Win** (1-2 lines, anchored in real or archetypal pattern)

### §3 Top 3 objections (Fact-Impact-Act format)

Three highest-stakes, highest-frequency objections. Demote the rest to `objection-extended.md` (sibling file, declared as Foundation `type: rationale` in asset.yaml). The extended file preserves the full v1 / prior-version responses so nothing of substance is lost — just reorganised for mid-call use.

### §4 Pricing playbook

- **The anchor**: one line
- **3 pricing scenarios** (low-anchor pushback / high-anchor comparison / setup-fee justification — adjust per tenant): each as a 2-line verbatim operator response
- **Walk-away threshold**: one line

### §5 Screening-question routing

Tenant-specific. Map each reply pattern (typically 5-7 rows) to a route (Offer A / Offer B / Probe / Disqualify) + the verbatim operator reply. **Rule of Three doesn't apply** to a lookup table — operator can't lose pipeline patterns to fit the rule.

### Appendix — Pre-call cheat sheet (optional)

60-second print-ready summary. The top-of-card §1 collapsed further for offline glance.

## Required peer artifacts

In the asset folder:

- `asset.md` — the source (above structure)
- `index.html` — rendered via `render-html` skill, print-to-PDF capable
- `copy.md` — operator-editable surface per the web-deliverable contract
- `objection-extended.md` — demoted objections (Foundation, type: rationale)
- `asset.yaml` — declarative metadata. `default_channel: Sales Kit`, files block declares the 4 above

## Voice rules

Same as the tenant's brand voice but tighter:
- **Internal-prep register** allowed (fragments, mid-sentence directness, operator-talking-to-themselves). NOT the polished landing-page register.
- **Em-dashes**: zero in body prose. Use middle-dot `·` for inline separators (e.g. `Offer A · strong fit`), period for end-stops, hyphen-with-spaces ` - ` for parenthetical beats.
- **Banned-words**: enforced per tenant Brand Context.
- **Operator is the subject of every verb** (you / the operator / they-the-operator). NOT a generic "we" or "the company".

## Phase 6 maintenance discipline

Battle Cards are living documents. Phase 6 (post-launch maintenance) of every campaign that ships a Battle Cards asset MUST include a quarterly-review task.

**Operator workflow** (chat-driven, codified here):

1. Operator opens chat with CM: *"Battle cards quarterly review for <tenant>"*
2. CM:
   - Reads the current Battle Cards `asset.md`
   - Prompts operator with structured intake: *"Since the last review (`<date>`), what's changed?"*
     - New objections heard in discovery calls? (top 3 worth surfacing)
     - Pricing shifted? (range, setup fee, walk-away)
     - Competitor moves? (new pricing, new positioning, new players)
     - Win-loss patterns? (what's working in pitches, what's blocking)
     - Screening-question reply patterns drifted? (new reply types worth adding)
   - Synthesises operator answers into proposed revisions
   - Surfaces a diff vs current Battle Cards for operator approval
3. Operator approves → Producer fires for the revision pass
4. Battle Cards v(n+1) ships with updated freshness stamp + next-review date
5. CM updates the campaign dashboard Phase 6 row to show review done + next review date

**Automation option (not yet implemented)**: scheduled task via `mcp__scheduled-tasks__create_scheduled_task` fires every 90 days from last review date with a prompt: *"Battle cards quarterly review for <tenant> is due. Open chat with CM to start."* Operator can dismiss or fire. Recommendation: implement for any tenant with active sales motion; skip for one-shot campaigns.

## Producer agent contract additions

When Producer is fired for any Battle Cards asset:

- Producer MUST follow the structure above. Filename conventions (`asset.md` + `index.html` + `copy.md` + `objection-extended.md` + `asset.yaml`) are mandatory.
- Producer MUST author the `## Open questions for operator (gate)` section (per asset.md spec) — including at minimum: win-loss evidence framing (real names vs archetypal), walk-away threshold confirmation, screening-routing row count, quarterly review cadence + owner confirmation.
- Producer MUST author `## What the operator does next` section with the explicit chat-driven quarterly-review workflow surfaced.
- Producer MUST NOT fabricate competitor pricing, win-loss numbers, or named-client claims without explicit operator approval.

## Reference

Canonical implementation: `campaigns/soundtrak-ai-system-overview-2026q2/assets/17-battle-cards/asset.md` (v2, Gong-principles revision, 2026-06-01). Future Battle Cards across any tenant should mirror this shape unless the tenant's sales motion requires a different structure (in which case capture the deviation as an explicit operator decision).
