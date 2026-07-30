# Pitch Deck — Starter Template (per `docs/specs/pitch-deck.md`)

**Use**: Producer reads this at production time as the structural scaffold. Adapt to the tenant; preserve the 7-act arc + slide order.

**Spec reference**: [`docs/specs/pitch-deck.md`](../../../docs/specs/pitch-deck.md) — read it first for voice rules + variant guidance + Producer contract.

---

## Cover slide

```
{Tenant wordmark}
{Deck title — 1 line}
{Presenter name + role}
{Date}
```

Background: tenant's cream / off-white surface. ONE Signal Red mark (typically on the operative phrase in the deck title).

---

## §1 — The problem, framed as a specific moment

**Slide H1**: Name the felt moment. Concrete, second-person, present-tense.

> *Example pattern*: "It's [day]. You're [doing specific thing] because [specific cause]. [Felt consequence]."

**Sub-body** (≤30 words): Ground the moment in the audience's context. NOT a generic market statement.

**Visual**: subtle. Don't compete with the words. Could be: a single illustrative object, a quiet background photograph, or pure typography.

**Voice rules**: second-person, present-tense, concrete sensory detail. AVOID "B2B companies face…", "Most organisations struggle with…", "Marketing has changed…".

---

## §2 — Why now / market shift

**Slide H1**: Name the specific shift that makes this conversation worth having NOW vs 6 months ago.

> *Example pattern*: "[Specific quantified shift] in [defined window]. The economics of [thing] just inverted."

**Sub-body** (≤25 words): The proof point. A stat, a recent event, a named example. Must be verifiable.

**Visual**: simple chart, before/after frame, or single quoted source. Quote the source.

**Voice rules**: declarative. Specific. AVOID "AI is changing everything", "The market is evolving", "Disruption is here".

---

## §3a — Solution conceptual reveal

**Slide H1**: Name what we are. Contrast with the obvious alternative.

> *Example pattern*: "Not a [obvious thing]. A [different thing]. Configured for [specific buyer]."

**Sub-body** (≤30 words): One sentence that captures the conceptual essence. The thesis statement of the deck.

**Visual**: a single conceptual diagram or arresting visual that reinforces the reveal.

---

## §3b — How it works / the mechanism

**Slide H1**: Name the system / architecture / process — how the solution actually delivers.

**Layout**: usually a diagram + 3-4 labelled components. Could be: agent stack, process flow, capability grid.

**Sub-body** (≤25 words): What the diagram is showing in one sentence.

---

## §3c — Product evidence (optional but recommended)

**Slide H1**: "What this looks like in practice." OR a domain-specific equivalent.

**Layout**: a real artifact. Screenshot, sample output, dashboard mock, before/after pair. Concrete proof the thing exists.

**Sub-body** (≤25 words): What the artifact is + what the reader is looking at.

---

## §4 — Why us / unique insight

**Slide H1**: Name the differentiated point of view that makes the team credible to solve THIS problem.

> *Example pattern*: "After [N years] [doing specific thing] inside [specific environment], one pattern keeps surfacing: [the insight]."

**Sub-body** (≤30 words): The insight elaborated in one sentence. The thing the competition doesn't see.

**Voice rules**: first-person, observational, earned-not-asserted. AVOID credentials list (that's §6 Team).

---

## §5 — Credibility evidence

**Slide H1**: Choose framing based on what evidence the tenant has:

- **Case studies**: "How we've done this before." [name N engagements + concrete outcomes]
- **Traction signals**: "Where we are right now." [pipeline / customers / waitlist / engagement]
- **Design-partner conversations**: "Who's at the table." [named ICP prospects in active conversation]
- **Founder credibility + early signals**: "What's already working." [career anchor + qualitative validation]

**Layout**: 2-4 cards. Each card: a name (client / metric / signal) + a one-line outcome. NUMBERS where possible.

**If no defensible content exists in any of the four fallbacks: SKIP this slide entirely.** Don't ship an empty section.

---

## §6 — Team

**Slide H1**: "The team." OR "Who's behind this." OR similar.

**Layout**: 1 line per person. Headshot optional. Each line carries ONE credibility anchor.

**Solo-practitioner version**: just the operator's career arc compressed to 5-7 lines. NOT a CV.

**Voice rules**: third-person, declarative. AVOID "passionate", "experienced", "talented" — name the work instead.

---

## §7 — Operating model

**Slide H1**: Name HOW the work actually happens. Process / cadence / gates / accountability.

> *Example pattern*: "Every [cadence]: [stage 1] → [stage 2] → [stage 3]. Practitioner gate at [named stages]."

**Layout**: process diagram, sprint cadence, gate map, OR labelled bullet list of stages.

**Voice rules**: precise. AVOID "Agile, customer-centric, iterative" — those describe any agency. The operating model must be the differentiator.

**Visual rule**: this slide often benefits from the same dashboard / system mock used on §3c — operating model is what the dashboard makes visible.

---

## §8 — Pricing

**Slide H1**: "Pricing. Anchor and range." OR similar declarative.

**Layout**: pricing table. Anchor-and-range format per tenant's `pricing_anchor` (cross-reference Battle Cards single source of truth):

| Item | Range | What it covers |
|---|---|---|
| {Engagement type 1} | {range} | {one-line scope} |
| {Engagement type 2} | {range} | {one-line scope} |

**Sub-body** (≤25 words): Custom-scoped per engagement. Discovery call surfaces real number.

**Voice rules**: declarative, no hedging. AVOID "Pricing varies, let's discuss" or any version of hidden pricing.

---

## §9 — The ask / next step

**Slide H1**: The specific, concrete action the prospect takes next.

> *Example pattern* (Soundtrak): "Reply with: what marketing function do you have today?"
> *Example pattern* (other tenants): "Book the 30-min discovery call: [link]" OR "Email [address] with [one specific thing]"

**Sub-body** (≤20 words): What happens after the prospect does the ask. Time-bound.

**Voice rules**: action verb. Specific. AVOID "Let's continue the conversation", "Reach out anytime", "Get in touch".

---

## Closing manifesto (optional)

**Slide H1**: One-line manifesto OR vision statement. Forward-look beat.

Use sparingly. Skip if the deck closes strongly on §9 already.

---

## Producer notes

- **Total slides**: 11-13. Don't pad. Don't compress under 10.
- **Background alternation**: cream → white → ink rotation per tenant's brand context. Avoid two same-coloured slides in a row.
- **ONE Signal Red mark per slide** (or per tenant's accent rule).
- **Print-to-PDF check**: every slide must break cleanly at page boundary (no orphaned text or overflow into next page).
- **Mobile / responsive**: slides stay 16:9 fixed-ratio; deck stacks vertically in browser, scales down proportionally.

## Required peer artifacts

Producer ships:
- `index.html` — canonical HTML deck
- `build-pptx.py` — python-pptx export script
- `deck.pptx` — auto-generated PowerPoint (declared `ship: true` in asset.yaml)
- `presenter-notes.md` — per-slide speaker notes
- `asset.md` + `copy.md` + `asset.yaml`

## Required Producer self-QA

- Each act §1-§9 has at least its required slide
- Voice rules per act (especially §1 second-person + §4 first-person)
- Pricing anchor matches Battle Cards (cross-reference)
- No fabricated case-study / competitor / client data
- Em-dash sweep clean
- Banned-words sweep clean per tenant brand context
