# Brief — Phase 1 Schema (v2)

**Spec version**: v4 · 2026-09-06: the intake interview is now EXHAUSTIVE by default — the 4–8 minute target is removed (a time budget was capping depth), replaced by a COVERAGE BAR over a named topic bank, an evidence sweep that runs BEFORE the first question, a HOMEWORK mechanic for evidence the operator has to go and collect, and a coverage ledger the operator sees at approval. New section: **What we already know**. Operator ruling 2026-09-06: full grilling on every campaign, no exceptions; homework classified load-bearing (blocks) vs useful (proceeds on a stated assumption). Previously v3.3 · 2026-06-12: objective taxonomy REMOVED (operator ruling — constraints must earn their place). The objective is ONE plain-language sentence + ONE primary KPI; CM infers the campaign shape (market-facing vs foundation-shaped) from the grilling and confirms its read in plain words — the operator is never asked to classify against system definitions. Supersedes v3.2's class+menu design same-day. v3.1 · 2026-06-12: foundation campaigns (strategy development) + Audience reframed as targeting (select from the tenant segment map) + fit-maturity challenge. v3 · 2026-06-12 (Phase 2 redesign retro R1/R5): mandatory business-objective taxonomy + KPI-scale sanity gate + tenant playbook §0 cited as fixed input. Previously v2 · 2026-06-03: Tech Setup + Human Roles + Cadence Shape per Rollout Architecture v2 (`docs/specs/rollout-architecture.md` §2).

The **Brief** is the operator-approved fact set for the campaign. CM authors it in Phase 1 from operator inputs (chat, transcripts, URLs, docs). It's strategic, not operational — what / why / who / how-measured / **what tech stack we ship into / who runs it / how often**. Operational asset-level detail lives in the Phase 3 Plan.

**Length target: 1-2 pages.** Brevity remains a feature, but the v2 sections (Tech Setup + Human Roles + Cadence Shape) add necessary context for Phases 4-5 planning. Push concept-level + asset-level detail to Plan; keep Brief at the strategic + rollout-readiness layer.

**Stored**: `campaigns/<slug>/brief.md` (markdown authoritative) + rendered `brief.html` (operator-facing view).

**Locked**: at end of Phase 1 operator approval for the strategic sections (Why / Offer / Audience / Proposition / KPI / Mandatories / Budget / Timeline). The v2 sections (Tech Setup / Human Roles / Cadence Shape) MAY have `TBD` placeholders at Phase 1 approval but **must be fully resolved by end of Phase 3 (Plan approval gate)** before Phase 6 work fires — see Rollout Architecture v2 §4.1 for the end-of-Phase-3 gate. Material changes to any locked section (KPI / audience / proposition / tech_stack / ownership_model) require a vN+1 + re-approval. Filling a `TBD` placeholder is not a material change.

---

## Canonical section order (SYS-085 — LOCKED; the brief-lint enforces it)

Every Brief uses THESE sections, in THIS order, with THESE names — so any reader (a marketer, not
just the author) can navigate any campaign's Brief the same way. Campaign-specific extras go in
**"Anything else"**, never as new top-level headings.

1. Why this campaign · 2. **What we already know** *(v4 — the evidence base: prior campaigns and
their real numbers · competitors · audience research we already hold · channel benchmarks. Sits BEFORE
the objective because the KPI baseline is derived from it, not invented after it)* · 3. Business
objective · 4. The offer · 5. Audience · 6. Insights that matter · 7. How to reach them ·
8. Single-minded proposition · 9. Goal & KPI · 10. Brand context · 11. Mandatories · 12. Budget ·
13. Timeline · 14. Tech setup · 15. Roles · 16. Cadence *(recurring campaigns only)* ·
17. **Anything else** *(campaign-specific context that doesn't fit above — the catch-all so extras
don't spawn inconsistent headings)* · 18. **Approval record** *(the audit / gate block at the
BOTTOM — kept; carries the interview coverage ledger)*.

**Decisions (2026-07-15):** Objective and Goal & KPI stay SEPARATE; "Open questions" folds into
"Anything else"; the top is the Campaign DNA header (no metadata paragraph, no clean-room note —
SYS-079 / SYS-084 / SYS-089). The v2 sections (Tech setup / Roles / Cadence) MAY be `TBD` at Phase-1
approval, resolved by end of Phase 3. Enforce with `.claude/skills/brief-lint/brief_lint.py` before
surfacing (mandatory, alongside the review-ready gate).

## Schema

```markdown
# <Campaign Name> — Brief v<N>

<!-- CAMPAIGN_DNA_AUTO -->

<small>**Attribution key** (how each line was sourced): `[the operator's read]` = operator-stated · `[interview]` = captured in the intake interview · `[AI synthesis]` = AI-composed from inputs.</small>

## Why this campaign
One paragraph. The business reason this exists *now*. Not features — outcomes.

## What we already know
*(v4. The evidence base, assembled by CM's sweep BEFORE the interview and corrected by the operator
during it — not a research task the operator is set. Every line is either sourced from disk with a
link, or attributed to the operator. If a line is a guess, it says so.)*

**Prior campaigns in this channel / area** — what we ran, when, and what it actually did. Link the
campaign and its results (`campaigns/<slug>/`, its analysis folder, its campaign report). One line
each on what worked and what didn't, with the reason we believe it.

**Channel benchmark** — the number we have actually achieved here before. This is what the KPI is
derived FROM; a target that is a multiple of it must say what changed to justify the multiple.

**Competitors / category** — who else is speaking to this audience, what they are running now, what
is visibly working for them, and what we will NOT copy (feeds tenant playbook §0a). Include the
**differentiation check**: if our intended claim is what everyone in the category already says, say
so here rather than discovering it at concept stage.

**Audience research we already hold** — surveys, interviews, analytics, CRM segments, win/loss,
recurring themes from sales calls. Name it, link it, and say what it is good for. What we believe
about this audience but have never tested goes here too, marked as belief.

**Gaps** — what we wanted and don't have, each carrying its homework state (below).

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

**Approval covers the insights (SYS-067).** The single Phase-1 Brief verdict approves **both** the Brief and the Insight Brief — the digest above is shown *at the gate* so that approval is informed. On approval CM derives the Insight Brief's approved-state from the Brief verdict (approved-*as-part-of*-the-Brief; not a separate gate). A send-back scoped to a segment's insights re-runs just the Insights Manager, not the whole Brief.

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
  # Title patterns: "<Tenant>+<Role>" e.g. "Beta Corp Marketing Manager",
  # "Gamma Foods Marketing Coordinator", "Soundtrak Head of Growth".
  # When unknown: use CM best-guess + flag for tenant confirmation at deploy.

  ai_trigger_person:
    # The TITLE of the role that opens Claude Code and triggers the cycle each week.
    role: "<Tenant Title>"                # e.g. "Beta Corp Marketing Manager"
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
      name: "<e.g. 'Beta Corp News monthly'>"
      frequency: "<...>"
  ownership_model: "<operator-runs | tenant-self-runs | operator-runs-then-tenant | outsourced-to-operator>"
  # ownership_model values:
  #   "operator-runs"              — the operator operates indefinitely (agency model)
  #   "tenant-self-runs"         — tenant team owns from Day 1 (we set up + train)
  #   "operator-runs-then-tenant"  — pilot period the operator, then handoff
  #   "outsourced-to-operator"     — tenant pays the operator to run it forever (also agency)
  phase_6_emphasis: "light | heavy"   # heavy = tenant-self-runs (no pilot cushion); light = operator-runs
  phase_6_emphasis: "<one-liner: 'Beta Corp-solo from cycle 1' | 'the operator runs pilot → handoff at cycle 5' | n/a>"
  estimated_phase_6_closure: "<date or trigger>"
  first_phase_6_cycle_target: "<date>"

## Anything else
Campaign-specific context that doesn't fit the sections above (workstream structure · open questions still resolving · sequencing quirks). The catch-all — so extras never spawn inconsistent top-level headings.

## Approval record
The audit + gate block at the BOTTOM of every Brief. `Gate closed <date>` · who approved · what the verdict covered ("Brief + the insights that inform it"). Append-only.
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

## Interview discipline (grill-me pattern) — v4

The Brief is the highest-leverage artifact in the system: everything downstream inherits its errors,
and a vague Brief is the usual reason a concept trio comes back generic. So the intake is an
**exhaustive interview**, run in full on **every campaign — no exceptions** (operator ruling
2026-09-06). What varies is how much the operator has to say, not how much gets covered.

### The rule that changed, and the one that didn't

- **REMOVED: the 4–8 minute target.** It was a time budget wearing the clothes of a service
  standard, and it was the reason the interview stopped early. There is no time target.
- **KEPT: maximum 2 questions per turn.** That is *pacing*, not depth. Fifteen questions in one
  message returns fifteen shallow answers. Exhaustive means many turns, not long ones.
- **The interview ends on a COVERAGE BAR, not a clock**: every topic in the bank below is
  `answered`, `assumed` (with the assumption written down), `homework` (with an owner and a stated
  default), `inherited` (already settled at the tenant layer, with a pointer), or `n/a` (with the
  reason). No topic may be silently absent — the ledger is what makes "exhaustive" checkable rather
  than a feeling.
- **Fast-path is now a PACING override only.** "fast-path" / "batch" lets the operator answer in
  bulk instead of turn-by-turn. It does **not** reduce coverage — every topic still lands in the
  ledger.

### Step 0 — sweep the evidence BEFORE the first question

Do not open cold. Assemble **What we already know** first, from what the system already holds:

- prior campaigns for this tenant — `campaigns/*/campaign.yaml` (objective + KPI blocks), any
  `analysis/` folder, any campaign report;
- the tenant playbook §0 (value prop · claim map · only-we lines) and **§0a disqualifiers**;
- `tenant-brand/<tenant>-audience-truths.md`, `tenant-brand/<tenant>-market.md`, the research
  library, the best-practice library.

Then **open with the read, not a question**: *"Here is what I already know about this audience and
what your last campaigns in this channel actually did — correct me where I'm wrong."* Grilling
someone on facts the system could have looked up is what turns an interview into an interrogation,
and it produces worse answers than reacting to something concrete.

### What earns a question

**Grill on evidence; recommend on decisions.** If AI can look it up, research it, or reasonably
assume it, it is not a question — it is a stated read the operator confirms or corrects. Only things
that live solely in the marketer's head get asked. This is what lets the interview be exhaustive
without being an interrogation, and it is the standing rule that CM does not push operational labour
onto the operator.

**Never re-ask the tenant layer.** Anything settled in Brand Context or playbook §0/§0a is a FIXED
INPUT: confirm it in one line, never re-interview it. If an answer *changes* a tenant-level fact, it
graduates UP to the playbook — it does not get buried in a campaign Brief. Exhaustive grilling that
duplicates the tenant layer into every campaign is exactly what the three-layer model exists to
prevent.

### The topic bank

Every topic gets a status in the ledger. Ids are stable so the ledger can reference them.

| # | Topic | The point of it |
|---|---|---|
| **A — Objective & outcome** | | |
| A1 | The business outcome, one sentence | The anchor everything inherits |
| A2 | The one number that says it worked, + deadline | One primary KPI, never two masters |
| A3 | **Baseline — what we actually achieved here before** | The KPI is derived, not invented |
| A4 | If the target is a multiple of the baseline, what changed to justify it | See "KPI baseline check" below |
| A5 | Secondary measures, explicitly labelled secondary | Stops a second master creeping in |
| A6 | What decision does hitting or missing this drive | A KPI nobody acts on is a vanity metric |
| **B — What we already know** | | |
| B1 | Prior campaigns in this channel / area | Mostly pre-filled by the sweep |
| B2 | Their actual results — the data, not the recollection. Where does it live? | Prime homework candidate |
| B3 | What worked, and why we believe that | Separates causation from coincidence |
| B4 | What failed, and why | The more useful half, and the half people skip |
| B5 | Anything we tried that we would never repeat | Cheap, and it prevents a repeat |
| **C — Competitors & category** | | |
| C1 | Who else is speaking to this audience | |
| C2 | What they are running in this channel now | |
| C3 | What is visibly working for them | |
| C4 | What we will NOT copy / off-limits framings | Feeds playbook §0a |
| C5 | **Differentiation check** — is our intended claim what everyone already says? | Better found now than at concept stage |
| **D — Audience & research** | | |
| D1 | Which segment, selected from the tenant map | Select, never re-derive |
| D2 | Research already done — surveys, interviews, analytics, CRM, win/loss, sales-call themes | |
| D3 | Where it lives, and can we have it | Prime homework candidate |
| D4 | What we believe about them that we have never tested | Marked as belief, not fact |
| D5 | Who is explicitly NOT the audience | |
| **E — The offer** | | |
| E1 | What exactly is being offered | |
| E2 | Why would they act now | Urgency + reason to believe |
| E3 | What is genuinely different vs category-standard | Pairs with C5 |
| E4 | Is the offer fixed, or can it change if the Brief says it should | Names the real authority |
| **F — Proposition & message** | | |
| F1 | The single-minded proposition | |
| F2 | Claims we can make, and the evidence for each | |
| F3 | Claims we must not make | Compliance / legal floor |
| **G — Constraints** | | |
| G1 | Budget — LOCKED at this stage | Force a not-to-exceed number |
| G2 | Timeline + any immovable dates | |
| G3 | Mandatories | |
| G4 | Who does what, and how much operator time is actually available | |
| G5 | Tech setup — where things publish | May be TBD until Phase 3 |
| **H — Risk** | | |
| H1 | **Pre-mortem: it is the deadline and this flopped. What happened?** | Surfaces risks no other framing gets |
| H2 | What would make us kill or pivot mid-flight | |
| H3 | Dependencies on other people or teams | |

Then the **dependency pass** as before: surface the tensions (budget vs effort, timeline vs KPI,
tech setup vs asset list, KPI vs baseline) and resolve them before drafting.

### KPI baseline check (A3/A4)

A KPI with a number and a deadline is not enough if the number came from nowhere. **Every KPI
records the baseline it was derived from**, and CM flags a target that implies an unexplained
multiple of it. This is not theoretical: the Soundtrak brand bank's "45,000+ / 16,500+" are
*inherited* audience numbers, not owned reach — the real owned figures are roughly 50 Substack
subscribers and 3,000 LinkedIn followers. A content-campaign KPI set against the inherited numbers
would have been unreachable by an order of magnitude, and nothing in the old Brief would have
caught it. If no baseline exists, say so explicitly — "first time in this channel, no baseline" is
a legitimate answer and a very different one from silence.

### Homework — evidence the operator has to go and collect

When a topic needs something the operator can't answer from memory, CM opens a homework item rather
than accepting a guess. Each one records:

- **What** is needed, in plain words, and **where to find it** (the specific export, dashboard,
  file or person);
- **Why it is load-bearing** — what downstream decision it changes;
- **The default** — what we will assume if it never arrives, so a decline never blocks; and
- **The classification** (operator ruling 2026-09-06):
  - **load-bearing** → **blocks Brief approval.** Being wrong here would invalidate the work. Say so
    plainly and park the campaign in that state.
  - **useful** → **proceeds under the stated assumption**, which is visible on the Brief and in the
    ledger, so the operator can see what the campaign is resting on.

Homework appears on the campaign dashboard as a real To Do, not a note buried in the Brief. CM
applies the orchestrates-not-delegates contract first: if AI can close the gap (research, a reachable
public source, an existing export), it does that instead of setting the operator homework.

### The interview transcript

The Brief is a 1–2 page distillation; an exhaustive interview produces far more than fits, and that
surplus is exactly the raw material the Creative Director and Producer need. CM writes the full Q&A
to **`campaigns/<slug>/research/intake-notes.md`** and links it from the Brief. The Brief stays
short; nothing gets thrown away.

### The coverage ledger

A compact table in the Brief's **Approval record**, collapsed, one row per topic id:

```markdown
<details markdown="1">
<summary><strong>Interview coverage</strong> — 34 topics · 28 answered · 3 assumed · 2 homework · 1 n/a</summary>

| Topic | Status | Note |
|---|---|---|
| A3 Baseline | answered | 4.1% avg engagement across 6 LinkedIn posts (link) |
| B2 Prior results | homework · load-bearing | LinkedIn export, operator, by Fri. Default if absent: use the-signal-amp figures |
| D4 Untested beliefs | assumed | "They read on mobile" — no data; flagged for the CD |
| G5 Tech setup | n/a | Resolved at Phase 3 per Rollout Architecture §4.1 |
</details>
```

`brief_lint.py` checks it: a Brief that carries a ledger must also carry **What we already know**,
and no ledger row may be left without a status. A ledger with blanks is worse than none — it looks
like coverage while proving nothing.

- **Attribution stays live**: every confirmed field gets tagged `[the operator's read]`, `[AI extension]`
  or `[AI synthesis]` at capture, not retroactively.
- **v2 sections (tech setup / roles / cadence)** may still be a grouped pass at the end of Phase 1 or
  during Phase 3, pre-filled from tenant context where present.

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

When a v1-era Brief needs v2 retrofit mid-campaign (as Beta Corp did 2026-06-03):

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
