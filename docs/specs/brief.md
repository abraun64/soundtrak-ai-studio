# Brief — Phase 1 Schema (v2)

**Spec version**: v3.3 · 2026-06-12: objective taxonomy REMOVED (operator ruling — constraints must earn their place). The objective is ONE plain-language sentence + ONE primary KPI; CM infers the campaign shape (market-facing vs foundation-shaped) from the grilling and confirms its read in plain words — the operator is never asked to classify against system definitions. Supersedes v3.2's class+menu design same-day. v3.1 · 2026-06-12: foundation campaigns (strategy development) + Audience reframed as targeting (select from the tenant segment map) + fit-maturity challenge. v3 · 2026-06-12 (Phase 2 redesign retro R1/R5): mandatory business-objective taxonomy + KPI-scale sanity gate + tenant playbook §0 cited as fixed input. Previously v2 · 2026-06-03: Tech Setup + Human Roles + Cadence Shape per Rollout Architecture v2 (`docs/specs/rollout-architecture.md` §2).

The **Brief** is the operator-approved fact set for the campaign. CM authors it in Phase 1 from operator inputs (chat, transcripts, URLs, docs). It's strategic, not operational — what / why / who / how-measured / **what tech stack we ship into / who runs it / how often**. Operational asset-level detail lives in the Phase 3 Plan.

**Length target: 1-2 pages.** Brevity remains a feature, but the v2 sections (Tech Setup + Human Roles + Cadence Shape) add necessary context for Phases 4-5 planning. Push concept-level + asset-level detail to Plan; keep Brief at the strategic + rollout-readiness layer.

**Stored**: `campaigns/<slug>/brief.md` (markdown authoritative) + rendered `brief.html` (operator-facing view).

**Locked**: at end of Phase 1 operator approval for the strategic sections (Why / Offer / Audience / Proposition / KPI / Mandatories / Budget / Timeline). The v2 sections (Tech Setup / Human Roles / Cadence Shape) MAY have `TBD` placeholders at Phase 1 approval but **must be fully resolved by end of Phase 3 (Plan approval gate)** before Phase 6 work fires — see Rollout Architecture v2 §4.1 for the end-of-Phase-3 gate. Material changes to any locked section (KPI / audience / proposition / tech_stack / ownership_model) require a vN+1 + re-approval. Filling a `TBD` placeholder is not a material change.

---

## Schema

```markdown
# <Campaign Name> — Brief v<N>

**Operator**: <name>     **Tenant**: <business name>     **Type**: B2B / B2C / Internal / Brand
**Status**: Draft / Approved / Locked     **Approved**: <date>

## Why this campaign
One paragraph. The business reason this exists *now*. Not features — outcomes.

## Business objective (declared FIRST, before any other field)
- **Primary objective**: ONE plain-language sentence — the single business outcome this campaign exists to produce, in the operator's own words (e.g. "book 5 qualified discovery calls", "establish our value proposition and positioning", "launch The Signal to the warm list"). No taxonomy, no menu, no jargon.
- **Campaign shape — CM-inferred, never operator-asked (v3.3)**: from the objective, CM infers whether this campaign is **market-facing** (trio = campaign ideas dramatising the tenant's §0 proposition; KPIs = market metrics) or **foundation-shaped** (strategy development — deliverables are tenant-layer artifacts that graduate at wrap; trio = positioning/value-prop routes; KPIs deliverable-gated). CM states its read in plain words during the interview ("this sounds like strategy-foundation work — the creative options will be positioning routes, not campaign mechanics — right?") and records it here with attribution. The operator never has to remember system definitions; CM carries them.
- **Why this one, now**: one line
- **Fit check (challenge, not block — v3.1)**: CM challenges the declared objective against the targeted segment's fit maturity (tenant fit-evidence base, where it exists). A brand-positioning campaign aimed at an `unproven` segment gets challenged toward validation/outreach first. The operator's call stands.
- **Split rule**: one campaign = one primary objective = one primary KPI. If a second objective keeps asserting itself during intake, the campaign gets SPLIT — separate campaigns connected through the tenant playbook (graduate-then-cite). Evidence (2026-06-12 Soundtrak C1/C2): a brief that mixes objectives lets every downstream artifact pick its own master.

## The offer
The thing being promoted, described as a product:
- **Name + one-liner**: <what it is in one sentence>
- **Format**: <newsletter / SaaS / event / lead magnet / product / etc., with cadence if recurring>
- **Pricing model**: <free / paid tier / subscription / one-time>
- **What's included**: <concrete inclusions, not benefits language>
- **Proof of existence**: <2–3 concrete examples — issue titles, features, screens, case-study names>
- **Destination URL**: <where the campaign drives to>
- **Not in offer**: <explicit exclusions>

## Audience (targeting — select from the tenant segment map, don't re-derive)
- **Segment**: selected from the tenant segment map where one exists — segment name(s) + why this campaign targets them + fit status (proven / promising / unproven). Map-less tenants only: describe from scratch, specific enough that a writer could write to one person.
- **Persona sketch**: <name + role + context + current belief/behavior — campaign-level sharpening of the selected segment>
- **Awareness level**: Unaware / Problem-aware / Solution-aware / Product-aware / Most-aware
- **Trigger event**: <what would make them seek a solution now>
- **Top objections + counters**: <2–3, each one line — pull from the segment map's landmines where mapped>

*Segmentation layering (v3.1)*: the segment MAP is built at foundation level (tenant layer); the Brief **selects** from it (targeting — an operator decision at intake, made right after the objective question); CD **mines** the selected segment for insight at Phase 2 (evidence-cited per concept spec §2). Building, selecting, and mining are three different activities with three different homes — the map is never rebuilt at brief time, and the target is never re-selected at concept time.

## Insights that matter (per segment) *(v3.4 — Insights Manager, 2026-06-20)*

Authored by the **Insights Manager** in Phase 1 (after the objective + segment(s) are set) — an evidence-backed read of *what is impacting the target market right now* that fuels the big idea. Full artifact: `campaigns/<slug>/insight-brief.md` (schema: [`insight-brief.md`](insight-brief.md)). The Brief surface shows two things:

- **Insights that matter — grouped by target segment.** For each segment, 1–3 insights, each one sentence (audience truth + tension) + named source(s) + date + why-it-matters-to-the-objective. Decision-first, above the fold.
- **Considered & cut** — a collapsed `<details markdown="1">` register of the ~top 10 candidates that didn't make it (each: insight · segment · why cut), **numbered + restorable**: the operator says *"restore insight #N"* → CM promotes it to the surfaced set + re-injects to the CD.

These are the **evidenced input to the CD's concept §2** — the big idea is built on them, not inferred cold. The operator approves the Brief *including* the insights (and any restores) before Phase 2 fires. **No-op for campaigns run before the Insights Manager existed** — the section simply doesn't appear.

## How to reach them (routes to market per segment) *(Insights Manager — informs the CD, not a media plan)*

Also authored by the Insights Manager (Insight Brief §2): **every GTM route marketing can influence to reach each segment** — not just media channels but **partnership / co-GTM** (an agency to partner with · complementary providers) and **intermediary** routes (VCs · incubators · associations · advisors who already hold the audience) and advocacy — filtered by **two hard gates: budget AND timeframe**. The lower the budget, the more the borrowed-audience routes matter. Each route: named + specific · type · why-it-works · budget-fit · **time-to-impact** (can it pay off before the KPI deadline?) · mainstream-vs-niche.

- **Per segment**, decision-first: *"<route(s)> — <budget + time note>"*; full reasoning in the [Insight Brief](insight-brief.md) §2.
- **This is reachability/GTM intelligence, not a media plan or asset mix.** The operator signs off *"yes, that's how we reach our audience"*; the CD uses it to shape concept rollout (incl. partnership plays a low-budget concept can be built around), and the Plan declares + sequences the actual assets against the deadline (the Brief still does not dictate the asset mix — that's the CD's call). **A slow-build partnership is flagged for a later campaign if it can't deliver inside this KPI window. No-op for pre-Insights-Manager campaigns.**

## Single-minded proposition
What this CAMPAIGN is trying to make them do, think, or feel — one sentence. Supporting messages (2–3) optional below.
**Not the tenant value proposition** — that lives at tenant playbook §0 and is inherited as FIXED INPUT, never authored or re-asked at campaign level (operator directive 2026-06-12).

## Goal & KPI
- **Primary KPI**: <metric + number + deadline> — exactly ONE; serves the declared primary objective
- **Secondary KPIs**: <1–3, each with metric + target — explicitly labelled secondary; they inform, never steer>
- **KPI-scale sanity gate (v3)**: the KPI's scale must match the instrument's scale. 5 discovery calls is an outreach-scale number (sales-led motion; content is air cover); 25k impressions is a content-campaign-scale number. A mismatch means the objective or the instrument is wrong — resolve before approval.
- **Foundation-shaped campaigns**: KPIs are deliverable-gated, never market metrics — primary = "operator-approved foundation set graduated by <date>"; optional validation metric (e.g. "value prop survives N real customer conversations"). A strategy project claiming revenue outcomes fails the sanity gate.
- **Effort Tier**: XS / S / M / L / XL

## Brand context
- **Tenant Brand Context record**: link to durable Brand Context page (voice + visual identity + positioning)
- **Tenant playbook §0 (value proposition + positioning)**: cited as FIXED INPUT where it exists — value prop, gate-survived lines, competitive claim map, only-we lines, segment-map pointer. Style / tone / target market are NEVER re-asked at campaign level.
- **Practitioner frameworks reference**: link to the playbook (`craft/frameworks/Soundtrak_Playbook.md`) — the durable practitioner-level layer. Brief authoring MUST cite specific playbook principles being applied or tested in this campaign (e.g. *"Tests principle 11 — Research Is a Competitive Content Moat"*).
- **Stretch tolerance for this campaign**: Tight / Standard / Loose
- **Anything campaign-specific that diverges from the durable Brand Context OR the practitioner frameworks**: <if any — capture in the campaign's own notes for material deviations>

## Mandatories
Legal, compliance, accessibility, region, brand mandatories. "None known" is valid; silence isn't.

## Budget
- **Total**: $<number> (LOCKED — not TBD)
- **Allocation logic**: <one line — e.g. "70% paid, 20% production, 10% contingency">

## Timeline
- **Start**: <date>
- **End**: <date or "ongoing">
- **Key dates**: <launch, milestone, deadline events>

## Tech Setup *(v2 — Rollout Architecture §2.1)*

The tenant's sales/martech stack. Captured per-channel so Producer can build assets against the actual destination from the start, and so Phase 6 setup work is concrete. `TBD` allowed at Phase 1 approval; must be resolved by end of Phase 3.

```yaml
tech_stack:
  email_platform: "<Mailchimp | Constant Contact | ActiveCampaign | HubSpot | MailerLite | Outlook (manual) | none>"
  intranet: "<SharePoint | Confluence | Slab | Coda | static-site | none>"
  cms_or_website: "<URL or platform-name>"        # tenant-hosted or platform-name
  social_tools:
    linkedin: "<manual / Buffer / Hootsuite / native scheduling>"
    instagram: "<manual / scheduled / off-limits-for-this-campaign>"
    youtube: "<Studio direct / TubeBuddy / off-limits>"
    facebook: "<as relevant>"
  file_storage: "<OneDrive | Google Drive | Dropbox | Box>"
  crm: "<Salesforce | HubSpot | Pipedrive | none in scope>"
  podcast_host: "<Spotify | Apple | Buzzsprout | n/a>"      # only for podcast-centric campaigns
  marketing_automation: "<Marketo | Pardot | HubSpot | n/a>"
  analytics:
    email: "<Mailchimp-native | platform-native>"
    web_and_site: "<GA4 | Plausible | Fathom | none>"
    social: "<platform-native | cross-platform aggregator>"
    podcast: "<host-native | Chartable | n/a>"
  notes: |
    Free-form context: per-asset destination mapping (default channels → tech platforms),
    Microsoft-365 vs Google-Workspace stack coherence observations, anything that affects
    Phase 5 install complexity or Phase 6 cadence ownership.
```

## Human Roles *(v2 — Rollout Architecture §2.2)*

Who does what manual work? Critical for designing Phase 5 training + Phase 6 cadence ownership.

**v2 principle: capture ROLE TITLES, not specific NAMES.** Roles persist; people in those roles rotate week-to-week and quarter-to-quarter. Even when a role currently has one person filling it, capture the title — the system stays accurate when the tenant rotates their Marketing Manager next quarter or the Compliance Officer goes on parental leave.

**Named exceptions**: public-facing bylines (podcast hosts, article bylines, video presenters). Those ARE named because they appear in published output as identities. Internal operational roles (cadence operator, approver, Send-clicker, escalation contact) are title-based.

**When CM doesn't know the tenant's actual title for a role**: use best-guess based on tenant size + sector (e.g. "Marketing Manager" for mid-size services firm; "Marketing Operations Lead" if more technical). Flag the best-guess as such; tenant confirms / overrides at deploy time per `onboard-tenant.md` §4. Title swaps propagate via search-and-replace through integrations.yaml + phase-5-rollout.md + phase-6-cadence.md.

```yaml
human_roles:
  # ── Named bylines (publicly attributed — captured by name) ──
  hosts_and_bylines:
    # Named individuals who appear publicly (podcast hosts, article bylines, video hosts).
    # These MUST be captured by name (they appear in published output).
    - <Name (Role)>

  # ── Internal operational roles (captured by TITLE, not name) ──
  # Title patterns: "<Tenant>+<Role>" e.g. "Acme Co Marketing Manager",
  # "Acme Co Marketing Coordinator", "Soundtrak Head of Growth".
  # When unknown: use CM best-guess + flag for tenant confirmation at deploy.

  ai_trigger_person:
    # The TITLE of the role that opens Claude Code and triggers the cycle each week.
    role: "<Tenant Title>"                # e.g. "Acme Co Marketing Manager"
    pilot_period: "the operator (external — setup + training) OR <Tenant Title>"
    post_pilot: "<Tenant Title — the human in this role on cadence day>"
    technical_literacy_needed: "low / moderate / high"
  approval_chain:
    # Per-stage approval ownership — by ROLE TITLE.
    - role: "<Tenant Title or 'the operator (external)'>"
      stage: "<Brief / Concept / Plan / per-asset / Phase 6 ongoing>"
      coverage: "<when this approver is in the loop>"
  manual_publisher:
    # The TITLE of the role that clicks Send, posts to social, uploads, etc.
    role: "<Tenant Title>"
    function: "<what they actually do — Send button, social post, upload, etc.>"
  linkedin_poster:
    company_page_role: "<Tenant Title>"
    personal_pages_role: "<Tenant Title or 'Tenant Adviser/Author (any of N)' for byline pools>"
  escalation_contact:
    role: "the operator (external — Slack/email)"
    sla: "next business day; same-day for compliance / cycle-blocking"
    scope: "<duration + intensity — e.g. first 4 weeks intensive, quarterly thereafter>"
```

**CM best-guess title patterns** (for when tenant doesn't yet have a designated title):

| Tenant size + sector | Likely cadence-operator title |
|---|---|
| Wealth management / Financial services (mid-size) | "Marketing Manager" |
| Professional services / Agency | "Marketing Coordinator" or "Marketing Manager" |
| SaaS / Tech | "Growth Manager" or "Demand Gen Manager" |
| Consumer brand | "Brand Manager" or "Content Manager" |
| Tiny tenant (founder-led) | "Founder" (named because founder = byline) |
| Other / unknown | "Marketing Manager" — most universally applicable |

## Cadence Shape *(v2 — Rollout Architecture §2.3)*

Is this a one-off or ongoing? If ongoing, what's the rhythm + ownership? Determines whether Phase 6 exists for this campaign + how heavy Phase 6 needs to be.

```yaml
cadence_shape:
  type: "one-off | ongoing | hybrid"
  ongoing_details:                    # populate only if type != "one-off"
    primary_cadence:
      name: "<e.g. 'Friday Note'>"
      frequency: "<weekly / fortnightly / monthly / quarterly / event-triggered>"
      trigger: "<what makes a cycle fire>"
      duration: "<pilot 14 days | indefinite | through 2026-Q4 | etc.>"
    secondary_cadence:               # if applicable
      name: "<e.g. 'Acme Co News monthly'>"
      frequency: "<...>"
  ownership_model: "<the operator-runs | tenant-self-runs | the operator-runs-then-tenant | outsourced-to-the operator>"
  # ownership_model values:
  #   "the operator-runs"              — the operator operates indefinitely (agency model)
  #   "tenant-self-runs"         — tenant team owns from Day 1 (we set up + train)
  #   "the operator-runs-then-tenant"  — pilot period the operator, then handoff
  #   "outsourced-to-the operator"     — tenant pays the operator to run it forever (also agency)
  phase_6_emphasis: "light | heavy"   # heavy = tenant-self-runs (no pilot cushion); light = the operator-runs
  phase_6_emphasis: "<one-liner: 'Acme Co-solo from cycle 1' | 'the operator runs pilot → handoff at cycle 5' | n/a>"
  estimated_phase_6_closure: "<date or trigger>"
  first_phase_6_cycle_target: "<date>"
```
```

---

## Attribution discipline (post-Retro-001 — Extract before extend)

Every Brief section attributes its source so future readers can see what came from where:

- **[the operator's read]** — the operator's view extracted via Phase 1 Q&A or pulled from Operator Playbook principles. Authoritative. AI does not override.
- **[AI extension]** — AI elaboration on the operator's read (e.g. fleshing out an audience segment from a one-line operator hint). the operator can re-read and override.
- **[AI synthesis]** — AI's own pattern-recognition from inputs (e.g. inferring KPI numbers from comparable campaigns). Lowest weight; flag for the operator confirmation.

Use these tags inline at section level or paragraph level. Briefs without attribution are incomplete.

**v2 sections — attribution applies equally**: tech_stack values pulled from operator's existing tooling get `[the operator's read]`; AI's best-guess defaults during interview get `[AI synthesis]` and must be confirmed.

---

## Interview discipline (grill-me pattern)

CM extracts the Brief via a **per-field structured interview**, not a single batch questionnaire. Rules:

- **The business-objective question comes FIRST** — before any other field, in plain English: "What is this campaign for — the single business outcome — and what one number will tell us it worked?" CM then states its inferred campaign shape (market-facing vs foundation-shaped) as a plain-words confirm — never a classification question the operator must answer. Everything downstream inherits this anchor.
- **One field at a time.** State the current read → probe → recommend → confirm → move on.
- **Maximum 2 questions per turn.** Never send a list of 8+ questions.
- **Pre-fill unambiguous fields** from pasted inputs; don't ask about things already known.
- **Full interview target: 4–8 minutes** of operator time for the strategic core (Why / Offer / Audience / Proposition / KPI / Mandatories / Budget / Timeline).
- **v2 sections — separate interview pass at end of Phase 1 OR during Phase 3**: tech_stack + human_roles + cadence_shape can be a single grouped pass (~3-5 min). Many fields will be operator-known from prior tenant context; CM pre-fills from `tenant/<name>/brand-context.md` defaults where present.
- **Attribution is live**: every confirmed field gets tagged `[the operator's read]`, `[AI extension]`, or `[AI synthesis]` at capture, not retroactively.
- **Dependency pass**: after all fields have a first pass, surface logical tensions (budget vs. tier, timeline vs. KPI, **tech_stack vs. asset list**) and resolve before drafting.
- **Fast-path override**: operator can say "fast-path" or "batch" to revert to single proactive ask.

---

## Drafting discipline

- 1-2 page target including v2 sections. If you're writing more, ask why.
- One primary objective. If you find two equally-weighted primaries, force a choice — or split the campaign (separate campaigns connected through the tenant playbook). Never let a brief carry two masters.
- Audience specific enough that a writer could write to one person — not "B2B buyers".
- Every KPI has a metric AND a number AND a deadline. Unmeasurable goals get translated.
- Budget LOCKED at brief stage. Force a best-estimate / not-to-exceed number if operator is uncertain. Allocation can iterate; total can't.
- `TBD` placeholders allowed for soft fields (strategic insight, secondary persona detail) — but flagged in operator approval surface.
- **v2 sections may have TBD at Phase 1 approval** but must be fully resolved by end of Phase 3 (Plan approval gate) before Phase 6 fires — see Rollout Architecture §4.1.

---

## What this Brief does NOT contain

- Channel mix / per-asset list / wave sequencing (lives in Plan)
- Concept-level creative direction (lives in Concept)
- Per-asset specs (lives in Per-Step Briefs)
- Voice rules (lives in Brand Context — only campaign-specific stretches sit here)
- Per-asset deployment destinations (inherited from Brief tech_stack + integrations.yaml by Producer at build time — see Rollout Architecture §7.1)
- Tenant-internal org chart (where the tenant owns a role, the Brief records `tenant-managed` not specific names)

---

## v2 retrofit pattern (when applied to in-flight campaigns)

When a v1-era Brief needs v2 retrofit mid-campaign (as Acme Co did 2026-06-03):

1. CM appends the three new sections to the Brief markdown.
2. CM pre-populates everything inferable from prior session context (chat, prior assets, BC).
3. Anything genuinely unknown becomes a Brief OQ batch — non-blocking for current-stage work; blocks any Phase 5 work.
4. Brief version bumps to vN+1 (or v2.x for the retrofit batch); CM does NOT self-approve — operator approval required for v2 sections to lock.
5. Dashboard reflects retrofit state: 🟡 "v2.X retrofit — N OQs pending" → ✅ "v2.X fully resolved" once operator answers.

---

## Cross-references

- **Rollout Architecture v2 spec**: `docs/specs/rollout-architecture.md` — §2 defines the schemas here; §4.1 defines the end-of-Phase-4 gate; §7.1 defines the inheritance flow from Brief tech_stack to per-asset `deployment:` block.
- **Plan spec** (extended in build sequence Phase 3): gains §N "Phase 5 + 6 readiness" populated from Brief v2 sections + asset list.
- **integrations.yaml** (built in build sequence Phase 5): per-tenant credentials + adapter selection sourced from Brief tech_stack.
- **Producer AGENT.md** (extended in build sequence Phase 4): Step 4.6 captures per-asset `deployment:` block via inheritance from Brief + integrations.yaml.
