# Marketing AI System — Operating Workflow

**The anchor doc.** Read this first. Everything in `docs/specs/`, every agent definition, every template serves the workflow described here.

## Mission

**Supercharge a senior practitioner** (the operator — a CMO with deep marketing experience) by orchestrating a bespoke AI specialist team that extends their judgment at scale. The operator IS the CMO; the system is the force multiplier. AI is additive — never replacement.

This means the system must:
1. **Extract the operator's knowledge before extending it** — the strategy phases (1–3) ask good questions, draw on the operator's durable Playbook, attribute "operator's read" vs "AI extension" vs "AI synthesis" in every Brief
2. **Recognise the operator's knowledge gaps** — distinguish marketing decisions the operator owns (frame the choice; trust the call) from technical execution the operator may not know (deliver a cookbook recipe with verification step)
3. **Ship assets complete** — every asset bundles everything needed to ship it: copy + visuals + technical-setup cookbook + deploy cookbook + verify cookbook. No "go figure out the technical bit" handoffs.
4. **Render decision-first, reference-collapsed, in plain language** — every operator surface puts the next action at the top; history, audit trails, deliberation rationale, version notes go below the fold in expand/collapse. Cold-start safe. And it reads in **plain language a person with zero context can act on** — no internal jargon, every acronym spelled out, no cryptic codes (the test: could a non-marketer act on it without asking?). Names + descriptions especially. Per `docs/specs/plan.md` §"Name + Description".
5. **Keep the operator-trio coherent** — dashboard / tasks / index must read meaningfully after a week of context-switching (tasks include one-sentence context + why-it-matters + what's-needed; not just summarised names)

The work runs as **six phases in two stages**. **Strategy (Phases 1–3)** is operator-led with three approvals — but each approval is informed by the operator's Q&A-extracted read, not by AI's synthesis alone. **Production (Phases 4–6)** is CM-orchestrated with one approval per finished asset. Everything else happens behind the scenes. (Before a tenant's first campaign, **Phase 0 — Tenant Baseline** establishes the durable per-tenant compound every campaign inherits — see [`docs/specs/phase-0-tenant-baseline.md`](specs/phase-0-tenant-baseline.md).)

**Positioning alignment**: this is the same product Soundtrak sells externally — *"Generic AI gives you generic marketing; bespoke AI configured on practitioner discipline gives you a senior practitioner's marketing at scale."* The system embodies what it claims to be.

---

## At a glance

```
┌──────────────────── STRATEGY · Phases 1–3 ──────────────────┐
│                                                             │
│  P1 Fact-Find ──► P2 Concept Design ──► P3 Plan             │
│      │                  │                   │               │
│      └─ approve         └─ pick one         └─ approve      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────── PRODUCTION + LAUNCH · Phases 4–6 ────────────┐
│                                                             │
│  P4 Asset Production (per asset):                           │
│   CM writes brief ─► Producer ─► Governance ─► Brand        │
│   (no approval)     (copy+visual) (compliance)  review      │
│                          CM applies fixes ◄─────────┘       │
│                                  │                          │
│                                  ▼                          │
│              Operator approves the finished asset           │
│                                                             │
│  P5 Launch / Day-1 Rollout  ──►  P6 Ongoing Cadence         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Strategy (Phases 1–3) = 3 operator approvals.** Production (Phase 4) = 1 operator approval per asset; Phases 5–6 are launch + cadence. Nothing else asks the human anything.

---

## The three layers — System / Tenant / Campaign (constitutional)

The system is two things in essence: **the system itself** (continually improving) and **the campaigns it runs** (isolated instances). Inheritance between related campaigns needs a durable home that is neither — the **tenant layer**. Codified 2026-06-10 (operator-stated; memory: `project-system-tenant-campaign-layering.md`).

| Layer | What it is | Lives at | Changes |
|---|---|---|---|
| **System** | The platform — specs, skills, agents, hooks, craft lenses, memory rules | `docs/` · `.claude/` · `craft/` · memory | Continuously, via retros + rule graduation |
| **Tenant** | The durable per-client compound — Brand Context, tenant playbook, library, integrations, cadence skills | `tenant-brand/` · `tenant/<tenant>/` · `tenant/library/` | Only at gated graduation moments |
| **Campaign** | The isolated instance — brief, concepts, plan, assets | `campaigns/<slug>/` | Live during the campaign; frozen at wrap |

**Rule 1 — inheritance is vertical, never horizontal.** A campaign reads UP (tenant + system layers, via CM slicing); it never reads a sibling campaign's files. If a previous campaign's element is wanted, it must **graduate to the tenant layer first, then be cited** — the *graduate-then-cite* rule. CM is the only layer-crossing point: Producer / Brand Manager / CD read only what CM injects, so enforcement has one locus.

**Rule 2 — graduation is gated.** Nothing compounds silently. At campaign wrap (and retros), CM proposes graduation candidates in ONE operator decision moment:

| Candidate | Destination |
|---|---|
| Winning assets / reference pieces | `tenant/library/` (via `/library-add`) |
| Tenant tactical learnings (audience · channel/timing · format · messaging · operational) | `tenant-brand/<tenant>-playbook.md` (schema: `docs/specs/tenant-playbook.md`) |
| Brand voice/visual drift | `tenant-brand/_recommendations-queue.md` |
| System-level lessons | Memory rules + spec amendments (retro §4) |

**Foundation campaigns (added 2026-06-12).** Some campaigns are market-facing; some exist to build strategy itself. The operator never declares a taxonomy — the Brief captures ONE plain-language objective + ONE primary KPI, and CM infers the campaign's shape from it, confirming in plain words. When a tenant's strategic foundation (value proposition · segment map · claim map · fit evidence) is absent or contested, it gets built BY a campaign, not by special machinery: a foundation-shaped campaign, run through the same gates. The CD trio returns **positioning/value-prop ROUTES** instead of campaign ideas (the concept-spec litmus flips with the objective), the asset list comprises strategy artifacts (`plan.md` §Asset list discipline), and **the wrap graduation IS the foundation approval** — deliverables land in playbook §0 / Brand Context / the tenant segment map, and the frozen campaign folder remains the audit trail of how the strategy was made. Sizing spectrum (CM judges at Phase 1): ingest-and-normalise at onboarding → light CD authoring → full foundation campaign. Segmentation layering: the map is **built** at foundation level, the Brief **selects** from it (targeting), CD **mines** the selection for insight.

**Why it matters**: campaign #2 for a tenant is faster and cheaper because the tenant layer has compounded — that's the commercial story. And tenant A's learnings physically cannot leak into tenant B's campaigns: there is no horizontal read path below the system layer.

---

## Storage + presentation model

**Markdown is authoritative; HTML is the operator's view.**

| Layer | Tech | Purpose |
|---|---|---|
| Content (specs, briefs, concepts, plans, assets, brand context) | Markdown in `campaigns/` and `tenant-brand/` | Authoritative source — what agents read |
| Operator review surface (approval gates, dashboard, tasks) | HTML rendered from markdown via `render-html` skill | What the operator opens in browser |
| Visual production | Replicate (Mode A) + Canva MCP (Mode B) + HTML/CSS (Mode C) | Producer dispatches per asset |
| Persistence + sharing | OneDrive (or equivalent synced folder) | Cloud sync, share via link |

**No Notion.** Notion was retired in the v3 refactor — the MCP friction (newline literalization, no DB schema modification, broken local-path links, retry policies) cost more than it earned.

**Render pipeline**: every time CM writes a markdown artifact (Brief, Concept, Plan, Asset, dashboard, tasks), it invokes the `render-html` skill, which converts markdown + a template type → HTML in the same folder. Operator opens `file:///.../brief.html` (or whatever) in browser. One pre-render step per artifact write; no client-side JS, no server.

---

## Strategy — Phases 1–3

### Phase 1 — Fact-Find

CM gathers everything needed to brief the campaign. Inputs accepted in any shape — chat, transcript, voice memo, URL, doc.

**Operating discipline (post-Retro-001 — *extract before extend*)**:

Before AI synthesises anything, Phase 1 MUST:

1. **Read the practitioner frameworks** at `craft/frameworks/` — surface which framework principles are relevant to this campaign's strategic intent.
2. **Ask the operator good questions** — the operator IS the CMO; their read trumps AI's first guess. CM authors a small set of focused discovery questions (drawn from a question library + the frameworks' relevant principles) BEFORE drafting the Brief.
3. **Synthesise the Brief with attribution markers** — every section tagged `[the operator's read]`, `[AI extension]`, or `[AI synthesis]`. Future readers (the operator and the agents) can see what came from where.
4. **Cite framework principles** in the Brief when a principle is being applied or tested (e.g. *"This campaign tests principle 11 — Research Is a Competitive Content Moat"*).

This is the foundational discipline that makes the system a *force multiplier* rather than a *replacement*. AI extends the operator's judgment; it never substitutes for it.

**What CM collects**:
- Why this campaign (the business reason)
- Target audience (segment + persona)
- The product / offer being promoted
- KPIs (primary + secondary, with numbers + dates)
- Budget (locked, not TBD)
- Mandatories + constraints
- Tone of voice / brand voice — **collected from operator OR created by CD if absent**
- Visual identity / brand guidelines — same
- **Canva brand kit ID** — inherited from the tenant Brand Context (set up in Phase 0); capture it into the Brief
- Inspiration / competitor refs / past adjacent campaigns

**Brand context handling**:
- If operator points to existing brand assets (HTML guide, voice doc, prior campaign, URL) — CM/CD extract + normalise into the tenant's durable Brand Context record (`docs/specs/brand-context.md`).
- If absent — authored in **Phase 0 (tenant baseline)** before the first campaign (`docs/specs/phase-0-tenant-baseline.md`), not during the campaign. Phase 1 inherits it.
- **Canva brand kit**: set up in Phase 0 (palette + fonts + logos) so Producer can use it in Mode B for all subsequent assets. Captured as `canva_brand_kit_id` in the Brand Context record.
- Brand Context is durable per-tenant — reused on subsequent campaigns for the same business, updated as needed.

**Practitioner frameworks layering**:
- The practitioner frameworks (`craft/frameworks/`) and the tenant Brand Context don't conflict — they layer.
- Frameworks = the practitioner-level discipline (the strategic playbook + marketing philosophy). Applies across ALL campaigns.
- Tenant Brand Context = THIS tenant's brand voice/visual/positioning. Applies to this campaign only.
- Per-step briefs cite both sources inline when pulling voice/principle slices. See [`craft/frameworks/README.md`](../craft/frameworks/README.md) for how the frameworks are used.

**Insight Brief (Insights Manager)**: once the objective + target segment(s) are set, CM dispatches the **Insights Manager**, which runs a disciplined multi-source web sweep (`insight-scan`) and authors the **Insight Brief** (`docs/specs/insight-brief.md`) — the *human* insight that fuels the big idea (identity / motivation / fear / aspiration), paired with its *market* context, **per segment**, every claim evidence-backed, plus a restorable "considered & cut" kill register. It cites the shared **research library** (`tenant/research-library/`) and the durable tenant **audience-truths** first. The distilled insights surface on the Brief; §1 for the selected segment becomes a fixed input to the CD's concept.

**Output**: a 1-page **Brief** (`docs/specs/brief.md`, including the "insights that matter" sections) + the **Insight Brief** + a normalised **Brand Context** record (`docs/specs/brand-context.md`). All rendered to HTML for operator review.

**Operator approval**: opens `brief.html` (and `brand-context.html` if newly created) in browser; confirms facts + insights are right; replies in chat with verdict.

### Phase 2 — Concept Design (creative trio)

CD authors **three campaign options** for operator to choose from, building each *on* the Insight Brief §1 for the selected segment(s). Each option contains: key audience insight (from the Insight Brief) + big idea + key message + moodboard / creative treatment.

Trio shape: Safe / Smart / Wild by default. One marked **Recommended** with rationale tying the call to the Brief's KPI.

**Output**: three **Concept** records (`docs/specs/concept.md`, one per option), rendered to a single side-by-side `concept-trio.html` for operator comparison.

**Operator approval**: opens `concept-trio.html`; picks one in chat.

### Phase 3 — Plan

CM authors the campaign plan: step-by-step list of assets to produce, with which agent owns each step, sequencing, dependencies, budget allocation per line.

**The plan dictates the assets.** Each asset row carries an explicit **`Ships` (output) column** naming *exactly* what that asset produces — one entry per distinct output, intermediate or final. Sales deck → `HTML + PPTX`. Video → `storyboards + MP4 files`. This is a load-bearing contract, not a description: **gallery tiles = asset.yaml `ship:true` = the plan's `Ships`, 1:1.** The Producer builds exactly the declared outputs and nothing improvised; the gallery shows exactly those. If you can't fill `Ships` cleanly, the asset isn't specified yet — tighten the plan before production. (Full rule: `docs/specs/plan.md` Ships values; enforcement: `check-state` Layer G.)

**Output**: a 1-page **Plan** (`docs/specs/plan.md`) rendered to `plan.html`.

**Operator approval**: opens `plan.html`; confirms in chat.

---

## Production + Launch — Phases 4–6

**Phase 4 (Asset Production) repeats per asset.** CM owns the entire orchestration; operator only sees the finished asset. Phases 5–6 (Launch + Cadence) follow once assets are approved.

### Phase 4a — CM writes the per-step brief (no operator approval)

For each asset in the plan, when its turn comes, CM authors a **Per-Step Brief** (`docs/specs/per-step-brief.md`) and hands it to the Producer in the invocation prompt.

The Per-Step Brief is **self-contained**. It carries:
- The asset task (what to produce, form, destination)
- The relevant **voice slice** from Brand Context (only what this asset needs)
- The relevant **visual identity slice** from Brand Context (palette, type, composition rules)
- **Canva brand kit ID** (if Producer dispatches Mode B)
- The relevant **strategy slice** (audience, key message, mandatories from Brief + Concept)
- 1 gold-standard reference if useful
- Any open questions or known constraints

Producer does **not** load tenant brand files. Producer reads the brief. CM is the librarian.

No operator approval gate here. CM authors, fires Producer.

### Phase 4b — Producer drafts → Governance → Brand → Insights (advisory) → CM applies fixes → operator approves

**Producer produces the bundled asset**: copy + visuals + any structural elements (slide briefs, storyboards, page architecture) — whatever the asset type requires.

**Visual production modes**:
- **Mode A — Replicate**: original AI generation. Photography, illustration, hand-drawn — anything where text is NOT load-bearing. FLUX / Ideogram / Recraft / etc. dispatched by `/replicate-generate` skill.
- **Mode B — Canva MCP**: text-led tiles, brand-kit layouts, recurring templates (scoreboard tiles, social-post tiles, ad creative variants), simple PDFs. Producer calls Canva MCP with the brand kit ID + a generation prompt or template ID; Canva returns a design + export URL; Producer downloads to `campaigns/<slug>/assets/<asset>/`. Typography exact by definition (Canva is a layout tool, not a generator).
- **Mode C — HTML/CSS**: pure markup output (email signature, simple text tiles, embedded web components).

**Producer runs in-agent self-QA**: copy 3-layer sub-edit + visual 3-layer sub-edit (where applicable). If self-QA fails after 3 cycles, refuse-to-surface — back to CM for rescope.

**Governance Manager reviews for compliance** (sequence: Producer → Governance → Brand). Fires when the tenant has a Compliance Profile (`docs/specs/compliance-profile.md`); verdict **Clear / Clear-with-disclaimers / Hold-for-operator / Block**. CM writes the verdict to the asset's `asset.yaml` `compliance:` block, and it surfaces on the asset preview via the `<!-- COMPLIANCE_AUTO -->` marker. **No-op when the tenant has no Compliance Profile** — existing behaviour, NO-RETROFIT. Governance is *red-flag-for-human-review*, not legal advice: a `hold` / `blocked` verdict routes the asset to the operator, never auto-publishes.

**Brand Manager reviews behind the scenes**: severity-rated findings. Pass / Pass-with-Required-Changes / Pass-with-Notes / Fail. (Where no Compliance Profile exists, Brand Manager keeps the mandatories check as a fallback.)

**Insights Manager — advisory resonance read** (sequence: … → Brand → Insights → operator). On every **external-touchpoint** asset, the Insights Manager reads the finished asset against the Insight Brief §1 for its segment and returns **On-insight / Mixed / Off-key**, anchored to a specific insight. CM writes it to `asset.yaml` `resonance:`; it surfaces on the preview via the `<!-- RESONANCE_AUTO -->` marker. **This is advisory — it never gates, never blocks, never sends back; the operator still decides.** No-op when the campaign has no Insight Brief or the asset is internal/Foundation (NO-RETROFIT).

**CM applies unambiguous fixes automatically**:
- If Brand returns Pass-with-Required-Changes and the fixes are surgical (swap a word, drop hashtags, fix a verbatim brand-guide violation), CM applies them.
- If Brand Fails, CM sends back to Producer with the findings. Counts toward 3-strike rule.
- If Brand Passes clean, asset goes straight to operator.

**Operator sees**: the finished, agent-QA-cleared asset rendered as an HTML preview that shows what the asset will look like in-context (e.g. LinkedIn post mockup with the tile embedded, email rendered in an inbox-preview frame, landing page rendered as a page). One verdict in chat: approve / send back / kill.

On approval: Asset Status → Approved. If publish needs a human action, CM creates a publish entry that surfaces in `tasks.html`.

### Phase 5 — Launch / Day-1 Rollout

Once assets are Approved, the campaign deploys. Each asset ships complete (copy + visuals + setup / deploy / verify cookbooks) so there's no "go figure out the technical bit" handoff; CM creates publish tasks in `tasks.html` for any human action. Full schema: [`docs/specs/phase-5-rollout.md`](specs/phase-5-rollout.md).

### Phase 6 — Ongoing Cadence

Recurring publish + read cycles per the campaign's cadence schedule (`campaign.yaml` `cadence:`). At wrap, CM proposes graduation candidates UP to the tenant layer in one operator decision (the three-layer rule). Tenant cadence skills (where extracted) run here.

---

## The agents

| Agent | Type | Role |
|---|---|---|
| **Campaign Manager** | Skill | Orchestrator. Runs Phases 1–3 (strategy). Authors per-step briefs in Phase 4. Applies Brand fixes. Manages gates. Holds campaign state. Invokes render pipeline after every artifact write. |
| **Insights Manager** | Subagent | Phase 1 — runs a disciplined multi-source web sweep and authors the evidence-backed Insight Brief: the human + market insight that fuels the big idea, per segment (the planner's *"what makes the audience tick"*). Phase 4 — an *advisory* resonance read on every external-touchpoint asset (does it still carry the insight, or has it drifted generic?). Never gates. Also seeds the durable tenant audience-truths + the shared research library. |
| **Creative Director** | Subagent | Phase 2 creative trio, built *on* the Insight Brief. Phase 3 plan input. (Brand Context authoring now lives in Phase 0 — `docs/specs/phase-0-tenant-baseline.md` — not Phase 1.) |
| **Governance Manager** | Subagent | Reviews assets for compliance / legal / regulatory red-flags in Phase 4 when the tenant has a Compliance Profile. Verdict Clear / Clear-with-disclaimers / Hold / Block — *red-flag-for-human-review*, not legal advice. Also authors the Compliance Profile in Phase 0. |
| **Brand Manager** | Subagent | Reviews every asset behind the scenes before operator sees it. Stewards the Brand Context record across campaigns. |
| **Producer** | Subagent | Produces every asset across every form — copy + visuals + structural elements bundled. Form-specific lenses for web/email/social/long-form/presentation/etc. Visual production via Replicate (Mode A) or Canva MCP (Mode B). |
| **Forensic Data analyst** | Subagent | Post-launch performance-data investigator (`marketing-forensic-analyst`) — interrogates campaign metrics to explain *why* a number moved, feeding learnings back up to the tenant layer at wrap. |

**Skills** (not agents):
- **`/campaign-manager`** — invokes the orchestrator
- **`/replicate-generate`** — Mode A AI visual generation
- **`/render-html`** — converts markdown + template type → HTML (CM invokes after every artifact write)
- **`/canva-design`** — wraps Canva MCP for Mode B visual production (Producer invokes)

---

## File structure

```
campaigns/<slug>/
  brief.md / brief.html              ← Phase 1 output
  concepts/
    safe.md / smart.md / wild.md
    concept-trio.html                ← side-by-side comparison view
  plan.md / plan.html                ← Phase 3 output
  assets/
    <asset-slug>/
      <asset-slug>.md                ← finished asset (copy + structural elements)
      <asset-slug>.html              ← operator-facing preview (in-context mockup)
      <asset-slug>.png               ← finished visual (if Mode A/B)
      brief.md                       ← per-step brief, saved if high-stakes
  dashboard.html                     ← live state for this campaign
  history/                           ← prior versions if any

campaigns/
  index.html                         ← all active campaigns at a glance
  tasks.html                         ← cross-campaign review queue

tenant-brand/
  <tenant-slug>.md / .html           ← durable Brand Context record
  <tenant-slug>-playbook.md / .html  ← tenant tactical playbook (graduated learnings)
  _recommendations-queue.md          ← Brand Manager improvement proposals queue

docs/
  workflow.md                        ← this file
  specs/                             ← schemas
  templates/                         ← HTML templates for render-html skill
    brief.html.jinja
    concept-trio.html.jinja
    plan.html.jinja
    asset-preview.html.jinja
    dashboard.html.jinja
    tasks.html.jinja
    base.css                         ← clean-default-minimal system UI
```

**Authoritative is markdown.** HTML is regenerated from markdown on every CM invocation that touches the artifact. If they ever diverge, markdown wins.

**Sharing**: campaign folders live in OneDrive (or equivalent). Operator opens HTML files via `file:///` URLs in browser. Share by sending the file path or OneDrive share link.

---

## CM rules of orchestration (the don'ts)

1. **CM does not delegate operational work to the operator.** If Brand returns unambiguous fixes, CM applies them. If a tile can be produced via Canva MCP, CM dispatches Mode B before pushing operator labour.
2. **CM surfaces exactly one decision per human moment.** If the moment has multiple decisions, fold them or auto-action them.
3. **CM never asks for what it already has.** Brand Context is durable; reuse across campaigns. Canva brand kit ID persists per tenant.
4. **CM does not create intermediate gates.** Phases 1–3 have 3 gates (one each). Phase 4 has 1 gate per asset.
5. **CM never surfaces an un-QA'd asset.** Brand verdict must clear before the operator sees the asset.
6. **CM re-renders HTML on every markdown write.** Stale HTML is a worse failure mode than no HTML.

---

## Success criterion (MVP viability test)

**End-to-end time from "start campaign" to "publish-ready asset" ≤ 60 minutes for a single-asset campaign.**

If the system can't hit this, the simplification isn't done.
