# Rollout Architecture — Marketing AI System

**Status**: v2 spec · Updated 2026-06-04 (6-phase renumbering) · Locked 2026-06-03 in design conversation with the operator.
**Owners**: Architecture (the operator) · Implementation (CM skill + Producer agent + Brief / Plan specs).
**Supersedes**: `_archive/deployment-architecture-v1-superseded.md` (v1, written earlier this turn). v1 collapsed Phase 5 + 6 into one "deployment" concept and surfaced deployment intent at asset-build time. Both were wrong — see §11 decision log entry "Why v1 was superseded."
**Successor**: TBD — revisit after Phase 6 runs cleanly for 2-3 cycles with 2-3 tenants.

---

## 0. Purpose

This document defines **how a campaign moves through its full lifecycle from Brief to ongoing live operation, with explicit attention to Phases 5 and 6 (rollout) which the system had previously left implicit.**

Before this spec, the system had strong machinery for Phases 1-4 (Brief, Concept Design, Asset Development) and treated Phase 5 (Day 1 Rollout: install templates, train staff, deploy one-off assets) and Phase 6 (Ongoing Rollout: run the recurring cadence end-to-end) as implicit operator labour ("the operator uploads to Mailchimp / trains the team / runs Friday's cadence"). That worked for the first foundation-asset campaign (Beta Corp Wave 0). It breaks the moment a weekly cadence starts and breaks worse the moment a second tenant exists.

**Scope:** architecture, schemas, operator-facing surfaces, phase boundaries. Does NOT cover specific adapter implementations (Mailchimp API code, etc.) — those are downstream from the schemas here.

**Audience:** primarily future-Claude (CM skill + Producer agent + future specs of Brief, Plan, Phase 5 + Phase 6 artifacts). Secondarily future-the operator + any client operator at a tenant business who runs Phase 6 cadences.

---

## 1. The 6-phase campaign lifecycle (this spec's backbone)

Every campaign moves through six phases. Some campaigns only need Phases 1-5 (one-offs like Gamma Foods Launch). Cadenced campaigns (Beta Corp weekly Friday Note) continue into Phase 6 indefinitely.

| Phase | Who owns | Output | Existing in system? |
|---|---|---|---|
| **1 — Brief** | CM + operator | Brief + Brand Context — captures WHAT we're doing and WHY, plus **tech stack · human roles · cadence shape** (NEW) | Yes (extending) |
| **2 — Concept Design** | CD | Selected concept | Yes (unchanged) |
| **3 — Plan** | CM + operator | Locked asset list + waves + budget + **§N Phase 5 + 6 readiness** section (end-of-Phase-4 gate trigger) | Yes (extending) |
| **4 — Asset Production** | Producer + Brand Manager | Approved assets with `asset.yaml` + deployment block + gallery entry | Yes (extending) |
| **5 — Day-1 Rollout** | CM + tenant + the operator | **Setup checklist** · **training plan** · **one-off asset deployment** (Mailchimp templates installed · environment provisioned · team trained). Acceptance criteria: tenant team can independently trigger Phase 6 cadence. | **NEW** |
| **6 — Ongoing Cadence** (cadenced campaigns only) | Tenant operator (or the operator if outsourced) | **Per-cycle runbook executed end-to-end**. No the operator involvement unless outsourced. Escalation paths defined. | **NEW** |

Every phase has a gate. Phase 5 → Phase 6 gate is particularly load-bearing: the Plan gets *updated* with deployment knowledge gathered across Phases 1-4 before any Phase 5 work fires.

**Retros are end-of-phase touchpoints** (added 2026-06-04 per `feedback_retros_are_system_artifacts_not_conversations.md`). Each phase closes with a light retro (~10-15 min) capturing what worked / friction / system rules to update. Wave retros (heavier, ~30 min) fire at end of major asset waves. Campaign-end retros (~45-60 min) fire at one-off campaign closure or quarterly milestones of ongoing campaigns. System retros (~60-90 min) fire quarterly across all campaigns or after significant system upgrades. **Retros generate memory rules + spec amendments + playbook updates + task items — not just docs on disk.** See `docs/specs/retro.md` for the schema + CM trigger recognition + approval gate.

---

## 2. Phase 1 extension — Brief gains Tech Setup + Human Roles + Cadence Shape

Today's Brief captures: who/what/why/budget/timeline/compliance. It does NOT capture how the assets get into the world or who runs them.

**v2 adds three new mandatory Brief sections.** All are fact-find dimensions, captured at intake (not at deployment time). **These sections live in each campaign's `brief.md` after this spec lands** — they are NOT in this spec doc itself. This spec defines the schemas; the populated data lives per-campaign.

> 📍 **For the Beta Corp instance**, see [`campaigns/beta-corp-podcast-engine-2026q2/brief.html`](../../campaigns/beta-corp-podcast-engine-2026q2/brief.html) — the three sections appear after "Timeline" and before "Open questions."

### 2.1 Tech Setup (schema)
What tools does the tenant use? Captured per-channel so Producer can build assets against the actual destination from the start.

```yaml
tech_stack:
  email_platform: "Mailchimp"           # or Constant Contact / ActiveCampaign / HubSpot / etc.
  intranet: "SharePoint"                # or Confluence / Slab / static-site / none
  cms_or_website: "WordPress"           # tenant-hosted or platform-name
  social_tools:
    linkedin: "manual (no Buffer/Hootsuite)"
    instagram: "manual"
    youtube: "Studio direct upload"
  file_storage: "OneDrive (Microsoft 365)"   # or Google Drive / Dropbox / Box
  crm: "Salesforce"                     # if relevant; many tenants won't have CRM in scope
  podcast_host: "Spotify for Podcasters"    # only for podcast-centric campaigns
  marketing_automation: "n/a"
  notes: "free-form anything else worth capturing"
```

### 2.2 Human roles
Who does what manual work? Critical for designing Phase 5 training + Phase 6 runbook.

**Capture ROLE TITLES, not specific NAMES.** Roles persist; people in those roles rotate week-to-week and quarter-to-quarter. Even when a role currently has one person filling it, capture the title — the system stays accurate when the tenant rotates their Marketing Manager next quarter or the Compliance Officer goes on parental leave. Named exceptions: public-facing bylines (podcast hosts, article bylines, video presenters) — those ARE named because they appear in published output as identities.

```yaml
human_roles:
  ai_trigger_person:
    role: "Marketing Manager"            # TITLE, not name; tenant confirms at deploy
    technical_literacy: "moderate"       # low / moderate / high
    tool_access: "Claude Code seat to be provisioned"
  approval_chain:
    - role: "CMO"
      stage: "Brief + Concept gates"
    - role: "Compliance Officer"
      stage: "Pre-publish for any client-facing piece"
    - role: "CEO"
      stage: "Quarterly review only"
  manual_publisher:
    role: "Marketing Manager"            # who clicks Send in Mailchimp / posts to LinkedIn
    name: "TBD"
  escalation_contact:
    role: "the operator (Slack #sb-marketing)" # who to ping when something breaks
    sla: "next business day"
```

### 2.3 Cadence shape
Is this a one-off or ongoing? If ongoing, what's the rhythm + ownership?

```yaml
cadence_shape:
  type: "ongoing"                        # "one-off" | "ongoing" | "hybrid"
  ongoing_details:
    frequency: "weekly"                  # weekly / fortnightly / monthly / quarterly
    trigger: "new Beta Corp Talks episode airs Wed; Friday Note ships Fri 9am AEST"
    duration: "indefinite (pilot 14 days)"
  ownership_model: "operator-runs-for-pilot-then-tenant-takes-over"
  # ownership_model values:
  #   "operator-runs"               — the operator operates indefinitely (agency model)
  #   "tenant-self-runs"          — tenant team owns from Day 1 (we set up + train)
  #   "operator-runs-then-tenant"   — pilot period the operator, then handoff (most common)
  #   "outsourced-to-operator"      — tenant pays the operator to run it forever (also agency)
```

### 2.4 Brief OQ pattern
Any of these fields can be `"TBD"` at Brief authoring. CM surfaces unknowns as Brief OQs in the same way it does today for budget/timeline. By end of Phase 4, all three sections must be fully populated (Phase 5 cannot start with TBDs in tech_stack or human_roles or ownership_model).

---

## 3. Phase 2 — Concept Design (unchanged)

The creative trio + selected-concept flow is unchanged. CD authors against Brief + Brand Context; operator selects; CM integrates. See existing `concept.md` spec.

Phase 2 may surface deployment-knowledge gaps (e.g. the chosen Wild concept implies an intranet asset and we don't know the tenant's intranet) — CM raises those as Brief OQs to be resolved before Phase 3 fires.

---

## 4. Phase 4 gate — End-of-production Plan update with deployment readiness

Today's Plan locks the asset list + waves + budget. v2 adds an **end-of-Phase-4 gate**: before Phase 4 closes, CM updates the Plan with a new section.

### 4.1 New Plan section: §N "Phase 5 + 6 readiness"

```markdown
## §N Phase 5 + 6 readiness

### N.1 Phase 5 — Day 1 rollout requirements

**One-off assets to deploy:**
| Asset | Destination | Method | Owner | Acceptance |
|---|---|---|---|---|
| #0a sb-talks-weekly.html | Mailchimp template | manual import via Content Studio | the operator (Day 1) | Template renders correctly in Mailchimp preview |
| #0a sb-news-monthly.html | Mailchimp template | manual import | the operator (Day 1) | Template renders |
| #0c pack-template.html | Intranet (SharePoint) | manual upload | the operator (Day 1) | First instance page lives at <sb-sharepoint-site>/sites/marketing/packs/ |

**Setup tasks:**
- Provision Mailchimp API key access (tenant-side action)
- Configure tenant/<name>/integrations.yaml with creds + audience IDs
- Install Claude Code on Marketing Manager's machine (if tenant-self-runs)
- Scaffold tenant OneDrive folder structure (per §8.2)

**Training plan:**
- 1.5-hr Day 1 walkthrough: Marketing Manager runs through one full cycle live with the operator
- Reference materials: phase-6-cadence.html · operator-onboarding.html · Mailchimp upload cookbook
- First 4 weeks the operator on Slack/email for questions

### N.2 Phase 6 — Ongoing rollout requirements (if cadenced)

**Per-cycle runbook ownership:** Marketing Manager
**Per-cycle estimated time:** 20 min operator + 5 min adapter-handled
**Cycle steps:**
1. New podcast episode airs Wednesday
2. Marketing Manager opens Claude Code Friday morning
3. Runs `/weekly-episode-pack`, answers 6-8 structured questions
4. Reviews + approves generated assets in gallery
5. Mailchimp adapter pushes Friday Note to draft campaign automatically
6. Marketing Manager clicks Send in Mailchimp (5-min manual)
7. LinkedIn post copy + 1080×1080 tile downloaded → manual post to Beta Corp company page
8. YouTube Shorts: render PNG → operator produces video in CapCut (out-of-scope v1)

**Escalation paths:**
- Mailchimp draft fails → Slack the operator
- Adviser unsubscribes → Beta Corp Compliance Officer per BC §6
- Brand Manager flags Pass-with-Required-Changes → Marketing Manager reviews surgical fix, escalates to the operator if uncertain
```

### 4.2 Why this gate matters

Phase 5 work is built against the Plan's §N. If §N is incomplete (tech_stack TBD, human_roles TBD, cadence_shape TBD), Phase 6 build is incomplete. The gate forces the operator + CM to close those gaps before any rollout machinery fires.

---

## 5. Phase 5 — Day-1 Rollout (NEW)

**Goal**: take the campaign from "approved assets sitting in the gallery" to "tenant team can independently run the cadence" (or for one-off campaigns: "everything is live and the campaign is done").

### 5.1 New per-campaign artifact: `phase-5-rollout.md` / `.html`

Authored by CM at the **end of Phase 4** from the Plan's §N (together with `phase-6-cadence.md` for cadenced campaigns — both built the moment Phase 4 assets are Approved, not at each phase's "start"). Single source of truth for Day 1 work.

**Schema:**
```markdown
# Phase 5 Day-1 Rollout — <Campaign Name>

**Tenant**: <name>     **Ownership model**: <from Brief>
**Phase 5 start**: <date>     **Target completion**: <date>     **Operator**: the operator

## §1 Setup checklist

| # | Task | Owner | Estimated time | Status |
|---|---|---|---|---|
| 1 | Provision Mailchimp API key + audience ID | Tenant Marketing Manager | 10 min | ⏳ pending |
| 2 | Populate `tenant/<name>/integrations.yaml` with creds | the operator | 15 min | ⏳ |
| 3 | Install Claude Code on Marketing Manager machine | the operator + Tenant | 45 min | ⏳ |
| 4 | Sync tenant OneDrive folder structure (shared + tenant-specific) | the operator | 30 min | ⏳ |
| 5 | First Mailchimp template install (sb-talks-weekly.html) | the operator | 30 min | ⏳ |
| 6 | First Mailchimp template install (sb-news-monthly.html) | the operator | 30 min | ⏳ |
| 7 | First intranet (SharePoint) page deploy (pack-template-test) | the operator | 30 min | ⏳ |

## §2 Training plan

### §2.1 Pre-session materials
- Phase 6 runbook (`phase-6-cadence.html`) — operator reads in advance
- Operator onboarding guide (`operator-onboarding.html`) — Day 1 walkthrough script
- Brand Context (`tenant/<name>/brand-context.html`) — operator should be familiar

### §2.2 Day 1 live session (1.5 hours)
1. Open Claude Code together (5 min)
2. Walkthrough of operator-quartet (dashboard / gallery / tasks / index) (15 min)
3. Run `/weekly-episode-pack` end-to-end on a sample episode (45 min)
4. Walk through Phase 6 runbook (15 min)
5. Escalation paths + Slack backup channel setup (10 min)

### §2.3 First-4-weeks support
- the operator on Slack #sb-marketing for ad-hoc questions
- Weekly 30-min check-in for first 4 cycles
- After cycle 4: monthly check-in only

## §3 One-off asset deployment matrix

| Asset | Destination | Method | Cookbook link | Status |
|---|---|---|---|---|
| #0a sb-talks-weekly.html | Mailchimp template | manual | [import-cookbook.html#mailchimp](...) | ⏳ |
| ... |

## §4 Acceptance criteria (Phase 5 → Phase 6 gate)

- [ ] Marketing Manager can independently run `/weekly-episode-pack` end-to-end
- [ ] Mailchimp adapter successfully drafts a test campaign
- [ ] First test Friday Note successfully sent + Marketing Manager confirms send
- [ ] First test LinkedIn post successfully published from generated tile + copy
- [ ] Escalation paths tested (Marketing Manager has Slack access + 1 ping resolved)
- [ ] Phase 6 runbook reviewed + signed-off by Marketing Manager

## §5 Phase 5 status + history
```

### 5.2 When Phase 5 fires

Phase 5 fires *immediately* after the Plan's §N (end-of-Phase-4 readiness) is signed off by the operator. For Beta Corp specifically, that's the gate we're currently approaching.

### 5.3 Phase 5 ownership model dependencies

How Phase 5 plays out depends on the Brief's `cadence_shape.ownership_model`:

- **`tenant-self-runs`**: full Phase 5 fires immediately. the operator + tenant team work together for ~1-2 weeks to setup + train. Phase 5 closes when acceptance criteria met.
- **`operator-runs`**: Phase 5 is much lighter. the operator sets up his own environment + installs templates + skips most training. May skip §2 entirely. Phase 5 closes when one-off assets are deployed.
- **`operator-runs-then-tenant`**: Phase 5a (operator-runs setup) then later Phase 5b (handoff to tenant) — see §6.3 for the handoff flow.
- **`outsourced-to-operator`**: same as `operator-runs`. Phase 5 ends with the operator's environment configured; Phase 6 runs forever with the operator operating.

---

## 6. Phase 6 — Ongoing Cadence (NEW, where applicable)

**Goal**: the cadence runs end-to-end every cycle with the agreed-upon operator (tenant team or the operator), with no the operator involvement unless escalated.

### 6.1 New per-campaign artifact: `phase-6-cadence.md` / `.html`

Only created for cadenced campaigns (cadence_shape.type == "ongoing" or "hybrid"). Lives alongside dashboard.html. Operator opens this on cadence day.

**Schema:**
```markdown
# Phase 6 Ongoing Cadence — <Campaign Name>

**Tenant**: <name>     **Cadence**: weekly · Friday 9am AEST
**Operator**: Marketing Manager (Mode 2 v1: Claude Code + OneDrive)
**Phase 6 start date**: <date>     **Cycles completed**: <count>

## §1 This cycle's checklist

**Cycle <N>** · Episode "<title>" · Recorded <date> · Target ship <date>

| # | Step | Owner | Method | Time | Status |
|---|---|---|---|---|---|
| 1 | New episode airs Wednesday | n/a (passive trigger) | — | — | 🟢 |
| 2 | Open Claude Code Friday morning | Marketing Manager | manual | 1 min | ⏳ |
| 3 | Run `/weekly-episode-pack` | Marketing Manager | slash command | 5 min | ⏳ |
| 4 | Answer 6-8 structured questions (episode title, summary, 3 quotes, Spotify URL) | Marketing Manager | chat | 10 min | ⏳ |
| 5 | Review approved assets in gallery | Marketing Manager | gallery.html | 3 min | ⏳ |
| 6 | Mailchimp adapter auto-pushes Friday Note to draft | CM (automated) | API | <30 sec | ⏳ |
| 7 | Marketing Manager opens Mailchimp draft, previews, clicks Send | Marketing Manager | Mailchimp UI | 5 min | ⏳ |
| 8 | Download LinkedIn tile + copy → post to Beta Corp company page | Marketing Manager | manual | 5 min | ⏳ |
| 9 | Render YouTube Shorts PNG → produce video in CapCut → upload (v1: out-of-scope) | Marketing Manager (later) | manual | 15 min | ⏳ |

**Cycle complete when**: steps 7 + 8 done. Total operator time: ~30 min. (Step 9 deferred to v2.)

## §2 Escalation paths

| If this happens | Do this | Then this |
|---|---|---|
| Mailchimp draft fails to create | Check `integrations.yaml#mailchimp` creds are still valid | Slack the operator if creds OK |
| Generated quote tile looks off-brand | Reject in gallery review; re-run with different quote | If still broken after 2 tries, Slack the operator |
| Adviser unsubscribes from Friday Note | Log in compliance register | Notify Beta Corp Compliance Officer per BC §6 |
| Brand Manager flags Pass-with-Required-Changes | Marketing Manager reviews surgical fix | Escalate to the operator if uncertain about fix |
| CM skill errors with cryptic message | Screenshot + Slack the operator | (don't try to debug Claude Code internals) |

## §3 Cycle history (last 8 cycles)

| Cycle | Episode | Ship date | Operator | Send count | Open rate | Notes |
|---|---|---|---|---|---|---|
| 88 | Boeing, Beef and Beans | 2026-06-05 | MM | TBD | TBD | First Phase 6 cycle |
| ... |

## §4 KPI tracking

Tracked against Brief §N KPIs:
- Primary: total impressions per episode (target: 2,000)
- Secondary: Beta Corp Talks email open rate (target: 30%)
- Secondary: adviser uses repurposed asset 1:1 (target: 3 of 5)
- ...
```

### 6.2 Operator modes (anchored under Phase 5)

The Mode 1 / Mode 2 v1 framing from v1 spec now lives here as the ownership-model branch of Phase 6:

- **Mode 1 — the operator runs it.** Used when `ownership_model: "operator-runs"` or `"outsourced-to-operator"`. the operator opens his own Claude Code, runs `/weekly-episode-pack`, etc.
- **Mode 2 v1 — Tenant team runs it (Code + OneDrive on their machine).** Used when `ownership_model: "tenant-self-runs"` or `"operator-runs-then-tenant"` (post-handoff). Marketing Manager opens Claude Code on their own machine pointed at tenant OneDrive root.

Both modes use the same skills, agents, hooks, and templates. The only difference is whose Claude Code seat is being used and whose OneDrive houses the campaign.

### 6.3 The handoff flow (`operator-runs-then-tenant`)

Most common ownership model: the operator runs Phase 6 for the pilot period (first 4-6 cycles), then hands off to the tenant Marketing Manager. The handoff itself is its own discrete event:

1. **Pre-handoff (the operator-side)**: Confirm cadence is stable across 4+ cycles. No escalations in last 2 cycles. Brand verdicts clean.
2. **Handoff session (1.5 hours)**: the operator runs the cycle live with Marketing Manager watching, then Marketing Manager runs the next cycle with the operator watching. the operator provisions Marketing Manager's Claude Code + OneDrive folder.
3. **Post-handoff (first 4 weeks)**: Marketing Manager runs solo; the operator on Slack/email backup; weekly 30-min check-ins.
4. **Steady state (after first month)**: Marketing Manager runs solo; the operator monthly check-ins only; escalation channel still open.

---

## 7. Per-asset deployment block (carried forward from v1, scope narrowed)

The `asset.yaml` `deployment:` block from v1 is still useful — it captures **per-asset specifics** within the campaign-wide deployment shape captured in the Brief. v2 narrows its scope: the block doesn't capture the destination decision (that's at Brief level now); it captures the per-asset format-requirements + verification + per-asset notes.

```yaml
deployment:
  # Inherited from campaign Brief tech_stack — Producer can read default
  # from tenant/<name>/integrations.yaml#channel_defaults if the asset's
  # default_channel maps cleanly.
  destination_type: email
  platform: "Mailchimp"  # inherited from Brief; explicit here for asset-level audit
  publish_method: api  # whether CM auto-deploys or generates cookbook
  format_requirements:
    - "HTML email importable to Mailchimp Content Studio"
    - "Inline styles only (no <style> blocks — Mailchimp strips them)"
    - "Hosted PNG for hero lockup (Content Studio image upload)"
  verification:
    - check: "Mailchimp preview renders without broken images"
      automated: false
    - check: "Test send to the operator's inbox renders clean in Gmail + Outlook"
      automated: false
  deployment_notes: >
    First-time Beta Corp Mailchimp install. Operator action: upload sb-wordmark-lockup-white.png
    to Content Studio first, replace src in HTML before importing.
```

### 7.1 Inheritance flow — Brief → integrations.yaml → asset.yaml

Per-asset deployment intent is NOT a parallel capture to the Brief. It's **gap-fill** on top of inheritance. For ~80% of assets, Producer fills the block almost entirely from inheritance with zero operator interaction. The flow:

1. **Brief authoring (Phase 1)** — operator + CM author `brief.md` tech_stack section. Captures the tenant's whole sales/martech stack: email platform, intranet, CMS, social tools, analytics, CRM, file storage, podcast host. This is the **forcing function** — by end of Phase 3, the campaign knows what platforms it's shipping into.

2. **integrations.yaml setup (start of Phase 5)** — CM (or the operator) configures `tenant/<name>/integrations.yaml` from the Brief's tech_stack. Per-platform: credentials (env-var refs), `has_adapter` flag (api vs cookbook), `defaults` (audience IDs, from-email, hashtags, etc.). Critically: `channel_defaults` maps **asset default_channel → platform**, so the Producer's lookup at build time is one-step.

3. **Producer asset build (Phase 4 for current campaign; Phase 6 for each cycle thereafter)** — Producer reads the asset's `default_channel` (set during Plan stage), looks up `integrations.yaml#channel_defaults[<channel>]`, and auto-populates these `deployment:` fields without asking:
   - `destination_type`
   - `platform`
   - `publish_method` (from `has_adapter` flag)
   - location default pattern (from platform defaults)
   - inherited platform defaults (send-time, audience IDs, hashtags, etc.)

4. **Producer manually fills** (per-asset specifics that DON'T inherit cleanly):
   - `format_requirements` — what does THIS asset need from its destination? (Inline styles only because Mailchimp strips `<style>`; hosted PNG for hero lockup; alt text on chart tile; etc.)
   - `verification` — how do we know THIS asset landed correctly?
   - `deployment_notes` — anything the deployer needs to know that's specific to this asset

5. **Brief OQ escalation** — Producer surfaces a Brief-OQ-back-to-operator ONLY if the asset's `default_channel` has NO mapping in `integrations.yaml#channel_defaults`. This means a genuinely new destination not anticipated in Brief — rare, but legitimate (e.g. a campaign that surfaces "print mailer for top-100 advisers" at Plan stage when the Brief tech_stack didn't anticipate print). Operator answers; integrations.yaml gains the new entry; Producer proceeds.

**Plumbing implication for CM/Producer:**
- ~30 lines of inheritance logic in CM's per-asset dispatch.
- Producer's per-step brief gains an `inheritance_summary:` block CM pre-fills (so Producer sees what's inherited vs what it must author).
- `build-gallery.py` warns when `deployment:` block is missing, with hint "Did Producer skip Step 4.6?"
- Spec propagation noted in §13 below — `docs/specs/asset.md` + Producer `AGENT.md` get the matching schema-level + step-level updates in Phase 6 of the build sequence.

**What this is NOT:**
- NOT Producer asking the operator destination questions every asset build (high friction, would compound across 8 assets × 52 weeks).
- NOT a parallel capture that can drift from the Brief (single source of truth: Brief tech_stack + integrations.yaml are canonical; asset.yaml inherits).
- NOT mandatory operator interaction at asset build time — Producer escalates only on genuine gaps.

Producer fills this block at build time using:
- Tenant defaults from `integrations.yaml#channel_defaults[<asset_default_channel>]` (inherited)
- Asset-specific format requirements + verification that emerge during build (authored)
- `deployment_notes` for anything the operator/deployer needs to see (authored, optional)

---

## 8. Tenant infrastructure (carried forward from v1)

### 8.1 `tenant/<name>/integrations.yaml`

Schema unchanged from v1. See archived v1 spec §4.1 for the full schema reference. Key elements:
- Per-platform `has_adapter` flag (true = coded adapter; false = cookbook-only)
- Per-platform credentials (env-var references; never committed)
- Per-platform defaults (send-time, audience IDs, hashtags, etc.)
- `channel_defaults` mapping asset channels → platforms
- `escalation` paths surfaced in Phase 5 rollout + Phase 6 runbook §2

### 8.2 Tenant OneDrive canonical structure

Schema unchanged from v1. See archived v1 spec §5. Two changes:
- `<campaign-slug>/operations.md` from v1 is **replaced** by two artifacts: `phase-5-rollout.md` + `phase-6-cadence.md` (the latter only for cadenced campaigns).
- `<campaign-slug>/plan.md` gets the new §N "Phase 5 + 6 readiness" section appended at end-of-Phase-3.

---

## 9. Build sequence (v2)

Phase-gated. Each phase produces a real artifact.

| # | Phase | Output | Depends on | Effort |
|---|---|---|---|---|
| 1 | This document v2 | `docs/specs/rollout-architecture.md` v2 — operator review gate | — | done (~3 hrs) |
| 2a | **Brief spec extension** | `docs/specs/brief.md` updated with tech_stack + human_roles + cadence_shape sections | Phase 1 reviewed | ~2 hrs |
| 2b | **Beta Corp Brief retrofit** | Populate Beta Corp Brief with what we know; surface 3 gap questions to operator | Phase 2a | ~1 hr + operator answers |
| 3 | **Plan spec extension** | `docs/specs/plan.md` updated with §N "Phase 5 + 6 readiness" template + end-of-Phase-3 gate | Phase 2a | ~2 hrs |
| 4 | **`asset.yaml` deployment block + Producer Step 4.6** | asset.md spec update + Producer AGENT.md + build-gallery.py warning when block missing | Phase 3 | ~3 hrs |
| 5 | **L3 integrations.yaml + first adapter** | Schema + Mailchimp API adapter + cookbook-generator fallback | Phase 6 | ~6 hrs |
| 6 | **Phase 5 + 6 artifact specs** | `docs/specs/phase-5-rollout.md` + `docs/specs/phase-6-cadence.md` + render-html templates | Phase 6 | ~4 hrs |
| 7 | **First Beta Corp Friday Note shipped through the v2 stack** | Phase 6 cycle 1 — Boeing/Beef/Beans episode | Phases 2-6 | ~half day operator |
| 8 | `docs/playbooks/onboard-tenant.md` | the operator's runbook for new tenant | Phase 7 | ~3 hrs |
| 9 | `docs/playbooks/client-operator-onboarding.md` | the operator's runbook for Mode 2 v1 handoff | Phase 8 | ~3 hrs |

**Total: ~4 working days Claude time + half-day the operator time.** (~1 day more than v1 estimate because Brief + Plan spec extensions + Phase 4/5 artifact specs are new.)

Skills (`/onboard-tenant`, `/weekly-episode-pack`) extract after 2-3 hand-runs reveal the right shape (parked per operator's "playbook only - and we can build the skill overtime once I have done a few").

---

## 10. Why v1 was superseded

v1 was written earlier today (~3 hrs ago in conversation time). Two structural errors caught by operator:

**(A) v1 collapsed Phase 5 and Phase 6 into a single "operations.html" surface.** Operator reframe: Phase 5 (one-time Day 1 setup + training + one-off asset deployment) and Phase 6 (ongoing recurring cadence) are different workflows with different artifacts, different acceptance criteria, different operators in many cases. v2 splits them into `phase-5-rollout.md` + `phase-6-cadence.md`.

**(B) v1 had deployment knowledge surfacing at asset-build time (Producer captures in `asset.yaml`).** Operator reframe: that's too late. By the time you discover Beta Corp uses Mailchimp, you might have built the email asset in a format Mailchimp can't cleanly import. The right place to capture tech + human + cadence is during Phases 1-3, with the Plan updated at end-of-Phase-3 with full deployment knowledge. v2 moves the primary capture to the Brief (tech_stack + human_roles + cadence_shape) and narrows the asset.yaml block's scope to per-asset format-requirements + verification.

v1 archived to `_archive/deployment-architecture-v1-superseded.md` for reference. Most of v1's content (asset.yaml block schema, integrations.yaml schema, OneDrive structure, Mode 1/Mode 2 framing, hooks system reference) carried forward into v2 unchanged.

---

## 11. Decision log

Cumulative from v1 + this v2 conversation.

| Decision | Chose | Rejected | Why |
|---|---|---|---|
| Where deployment intent lives (PRIMARY) | Brief tech_stack + human_roles + cadence_shape sections (Phase 1) is PRIMARY; asset.yaml deployment block is gap-fill via inheritance | Per-asset (asset.yaml) at Producer-build time as parallel capture | Asset-build time is too late as PRIMARY; Producer might author against wrong destination. Brief captures shape; asset.yaml block inherits from Brief + integrations.yaml channel_defaults and narrows to per-asset format/verification specifics. See §7.1 for the inheritance flow. **Operator confirmed 2026-06-03: Pattern A (upfront-primary + Producer-gap-fills) over Pattern B (per-asset only) — runtime friction trumps marginal plumbing simplicity.** |
| Phase 5 vs Phase 6 | Separate artifacts: `phase-5-rollout.md` + `phase-6-cadence.md` | Single `operations.md` surface | They're different workflows with different operators, acceptance criteria, cadence. Single artifact obscured that. |
| End-of-Phase-4 gate | Plan §N "Phase 5 + 6 readiness" updated before Phase 5 fires | No gate; Phase 6 starts fresh | Without explicit deployment-readiness section, Phase 6 work is built against incomplete knowledge. Gate forces gaps to close. |
| Operator persona model | Hybrid: ownership_model field on Brief (operator-runs / tenant-self-runs / hybrid / outsourced) | Binary Mode 1 vs Mode 2 | Operator named the actual shape; ownership_model captures it cleanly. Modes are now branches of Phase 6. |
| Build order | Generic L1-L3 first, then Beta Corp as first customer | Beta Corp-first then generalise | Refactoring under load is harder than designing up-front. |
| Mode 2 v1 tool | Claude Code + OneDrive on client machine | Claude CoWork + Google Drive | (a) zero skill-porting cost vs ~1-2 weeks rework; (b) professional-services clients live in OneDrive; (c) brand-context curation in OneDrive IS the value-add. |
| Tenant onboarding | Playbook only for v1; extract skill after 2-3 hand-runs | Fully automated skill | Don't pave the cowpath until there's a cowpath. |
| Cron Layer 3 reconciler (state-drift hooks) | Parked | Build now | Hooks Layer 1+2 installed 2026-06-03; build Layer 3 if drift slips through after 2-4 weeks. |
| Block-on-prose-drift behavior (state-drift hooks) | Stderr advisory only | Force-block Stop hook | Heavier control-loop intervention requires its own explicit auth; soft advisory may prove sufficient. |
| Spec v1 → v2 | Rewrite cleanly with 5-phase backbone | Amendment doc on top of v1 | Future readers shouldn't have to reconcile two docs; clean rewrite preserves coherence. v1 archived for reference. |
| Beta Corp Brief retrofit | Populate now (retroactive) | Forward-only (next campaign onwards) | We're about to do Phase 4+5 for Beta Corp. Without the new fields populated, Phase 6 planning is harder. |

---

## 12. Open questions / parked items

These don't block the build sequence. Capture for future sessions.

- **Q1 — Spotify timestamp URLs**: per-cycle Producer input. Confirm during Phase 7 smoke test.
- **Q2 — Email demo re-theme**: P2 cleanup. Fold into Phase 7.
- **Q3 — CAR No.**: Beta Corp's Corporate Authorised Representative number remains unresolved. Non-blocking.
- **Q4 — YouTube Shorts MP4 generation**: out-of-scope v1. Render PNG only; operator handles video step. Revisit in v2.
- **Q5 — Beta Corp Mailchimp API credentials**: Phase 5 gate item.
- **Q6 — Beta Corp intranet platform**: ✅ resolved 2026-06-03 — **SharePoint** (Microsoft 365 native; aligns with OneDrive file storage stack). Default spec assumption updated.
- **Q7 — Per-tenant cost model**: $100-200/mo Code subscription per operator seat. Out of architecture scope; flagged for commercial planning.
- **Q8 (NEW) — Beta Corp ownership_model**: pilot-period operator-runs vs immediate tenant-self-runs vs hybrid? Need to capture during Beta Corp Brief retrofit.
- **Q9 (NEW) — Beta Corp Marketing Manager identity**: who at Beta Corp is the designated Phase 6 cadence operator? Need name + email + technical literacy assessment during Beta Corp Brief retrofit.
- **Q10 (NEW) — Tenant's compliance officer for adviser-pack reviews**: BC §6 references compliance review; name + escalation path needed.

---

## 13. Memory rule cross-references

This spec aligns with and extends:

- `feedback_state_changes_enforced_by_hooks_not_prose.md` — the rollout system relies on the state-hooks installed 2026-06-03 to keep operator surfaces current across Phase 5 + 6.
- `feedback_gallery_publish_aware_producer.md` — Producer ship-complete contract requires `asset.yaml`. v2 extends with the narrowed deployment block.
- `feedback_cm_orchestrates_does_not_delegate_to_human.md` — CM fires adapters during Phase 5; surfaces only irreducible-manual cookbook steps to operator.
- `reframe_cmo_force_multiplier.md` — the rollout system is part of the "ship-complete asset" contract: Phases 5 and 6 are part of the campaign, not a post-campaign operator task.

This spec SHOULD propagate to (handled in Phase 2a-6 of the build sequence above):

- `docs/specs/brief.md` — gain tech_stack + human_roles + cadence_shape sections
- `docs/specs/plan.md` — gain §N "Phase 5 + 6 readiness" template + end-of-Phase-3 gate
- `docs/specs/asset.md` — gain §N on the per-asset deployment block (narrowed scope)
- `docs/specs/phase-5-rollout.md` (NEW) — full spec for the Day 1 rollout artifact
- `docs/specs/phase-6-cadence.md` (NEW) — full spec for the ongoing cadence artifact
- Producer `AGENT.md` (wherever it lives) — Step 4.6 for deployment-block capture using campaign defaults
- `docs/workflow.md` — extend the workflow narrative to include Phases 5 + 6 as explicit stages
- `.claude/skills/campaign-manager/SKILL.md` — extend operator-quartet → operator-quintet (+ phase-5-rollout.html OR phase-6-cadence.html depending on campaign state)

These propagations happen in Phases 2a-6. Not now.
