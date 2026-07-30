# Playbook — Onboard a New Tenant

**Spec version**: v1 · Authored 2026-06-03 per Rollout Architecture v2 build sequence Phase 8.
**Owner**: the operator. This is YOUR runbook for bringing a new tenant onto the Marketing AI System.
**Replaces**: clone-by-hand pattern. Replaced by `/onboard-tenant` skill after 2-3 successful manual runs reveal the right shape.
**Also the Phase 0 runbook** (2026-06-15): operationalizes [`docs/specs/phase-0-tenant-baseline.md`](../specs/phase-0-tenant-baseline.md) — the durable per-tenant compound (Brand Context · segments · market · **Compliance Profile** · library · integrations). **Future-only / opt-in**: new tenants get the full baseline; existing tenants migrate only on explicit request — no retrofit.

---

## When to run this playbook

A new tenant wants the system. Trigger events:
- Direct ask: "set me up like Beta Corp"
- Sales conversation reaches "yes, let's do this"
- Existing tenant adds a second campaign type that needs separate brand context
- You're onboarding yourself onto your own system for a new business venture

**Time budget**: ~3-4 hours of your time per tenant, spread across 1-3 days. First two phases (fact-find + brand context) can be operator-async; the rest is heads-down.

**Pre-flight**: tenant exists as a real business, you've had at least one conversation about scope, you have access to enough of their public output (website, podcast, social, prior assets) to author Brand Context.

---

## §1 — Tenant fact-find (~30 min operator time + ~30 min Claude)

Same shape as a campaign Brief intake but ONE LEVEL UP — tenant-level facts, not campaign-level.

### §1.1 Capture (5-8 questions, structured interview pattern per Brief spec)

1. **Business identity** — tenant name + tagline + sector + market position
2. **Audience** — who do they sell to / serve (demographic + psychographic)
3. **Voice + tone** — how they talk (formal / conversational / contrarian / measured / etc.)
4. **Visual identity** — colors / typography / logo assets (request files if not on public-facing pages)
5. **Compliance posture** — regulated industry? Disclaimers required? AFSL / FINRA / similar?
6. **Tech stack** — same fields as Brief §Tech Setup (email platform · intranet · CMS · social tools · CRM · storage · podcast host · analytics) **+ AI tooling** — which AI tools they already use (ChatGPT / Claude / Gemini / Jasper / Midjourney / etc.); informs how the system slots into their existing workflow
7. **Ownership model** — will they self-run or will the operator run? `operator-runs / tenant-self-runs / operator-runs-then-tenant / outsourced-to-operator`
8. **Best practices** — pointers to the brand's own exemplary work: best assets, standout campaigns, URLs, key website pages — anything they're proud of. These seed the gold-standard library (§3). **A living list — add to it over time** as more good work surfaces; not a one-shot capture. *(The first campaign is NOT captured here — that's the next phase, Phase 1; see §5.)*

### §1.2 Source what's already public

In parallel with the interview, harvest:
- Tenant's website (positioning, sample content, voice samples)
- Social profiles (LinkedIn / IG / YouTube / podcast — whichever they have)
- Any prior published artifacts they're proud of (gold-standard refs)
- Their best competitor or aspirational peer (for the visual / voice ceiling)
- **Competitive scan (REQUIRED before first concepts — retro R6, 2026-06-12)**: a structured pass over the tenant's claim landscape (~10-15 named players where the category supports it). Output: a competitive claim map (wallpaper / contested / open-territory buckets + nearest named threat) seeded into the tenant playbook §0. Cheap (~$0.50 of search) and decisive — concepts authored without it lead with category wallpaper. Refreshed per-campaign at brief time thereafter. **Powered by** `company-intelligence` (market structure + competitors → `tenant-brand/<tenant>-market.md`) and `segmentation-strategy` (needs-based segments → `tenant-brand/<tenant>-segments.md`); capture the markdown substance into the tenant artifacts, keep the skills' HTML in `tenant/<slug>/_discovery/`.

Drop public-discovery findings into a `tenant/<slug>/_discovery/` folder for the Brand Context authoring step.

---

## §2 — Tenant Brand Context authoring (~1-2 hrs Claude time + 30 min operator review)

CD or the operator-as-CD authors the durable Brand Context per the `docs/specs/brand-context.md` spec. Output: `tenant/<slug>/brand-context.md` + rendered `.html`.

Key blocks to populate:
- §1 Compliance posture (verbatim disclaimer text if regulated)
- §2 Audience persona (mirrors Brief §Audience but tenant-level)
- §3 Visual identity (palette hex codes + typography + logo + grid)
- §4 Voice + tone (rules, vocab, prohibited words, sample sentences)
- §5 Channels in use (LinkedIn / podcast / blog / etc. with profile URLs)
- §6 Compliance officer + escalation chain (or `tenant-managed internally`)
- §7 Strategic positioning + tagline candidates
- §8 BC recommendations queue (deferred decisions, future-state items)

Operator reviews; iterates 1-2 rounds; explicit approval gate.

---

## §2.5 — Compliance Profile authoring (regulated tenants — ~1 hr Claude + operator/counsel review)

For any tenant in a regulated industry (financial advice, health, food, etc.), author the dedicated **Compliance Profile** via the **`governance-manager`** agent (authoring role) per [`docs/specs/compliance-profile.md`](../specs/compliance-profile.md). Output: `tenant-brand/<tenant>-compliance.md` + `.html`.

- The agent **researches the applicable regimes** (AFSL/ASIC, FINRA/SEC, FCA, GDPR/Privacy Act, FTC, sector codes) via web search — each tagged FINDING (cited) or HYPOTHESIS (inferred) — and **captures the company-specific rules** from the operator/counsel (approved disclaimers verbatim, prohibited claims, mandatories, compliance officer + escalation).
- It needs **(a) industry/category and (b) jurisdiction(s)** to start — capture these first.
- **NOT LEGAL ADVICE**: mark `Counsel-confirmed: no` until the tenant's counsel reviews; flag High-risk items (§8) as counsel-sign-off-mandatory.
- The full Compliance Profile **supersedes** the Brand Context's light §1/§6 compliance posture for regulated tenants (Brand Context keeps a pointer to it).
- **Skip for unregulated tenants** — mark `N/A (unregulated)`; Brand Manager's mandatory-check fallback then applies.

Operator (+ counsel where required) reviews; explicit approval gate.

---

## §3 — Tenant folder structure scaffolding (~30 min)

> 📋 **The file-copy mechanics** for syncing your master to a tenant's OneDrive at deploy time are in [`sync-master-to-tenant.md`](sync-master-to-tenant.md) — PowerShell script (Windows) + rsync equivalent (macOS). This §3 scaffolds the structure on YOUR master; the sync cookbook propagates it to the tenant at Phase 6.

New tenants use the **same flat structure as existing tenants** (Beta Corp · Gamma Foods · Soundtrak) — **no business-rooted nesting**. Baseline artifacts live in `tenant-brand/`, tenant working files in `tenant/<slug>/`, campaigns in the shared `campaigns/` root tagged by a `tenant:` field:

```
tenant-brand/
  <tenant>.md / .html            # Brand Context (§2)
  <tenant>.yaml                  # tenant identity + baseline pointers (§6) — powers the Tenant Dashboard
  <tenant>-playbook.md / .html   # Playbook §0 positioning + tactical learnings (graduates over time)
  <tenant>-compliance.md / .html # Compliance Profile (§2.5; regulated tenants, else N/A)
  <tenant>-segments.md / .html   # segmentation-strategy output
  <tenant>-market.md / .html     # company-intelligence / competitive output
  <tenant>-home.md / .html       # Tenant Dashboard — generated by build-tenant-home.py (§6)
tenant/<slug>/
  integrations.yaml              # tech stack (§4)
  _discovery/                    # §1.2 raw + skill HTML companions (archive after baseline v1.0)
  brand-assets/  (logos/ · fonts/ · stock/)
tenant/library/                  # UNIFIED shared gold-standard library (not per-tenant) — seed via /library-add
campaigns/<slug>/                # each campaign; set `tenant: <slug>` in its campaign.yaml
```

> **Grouping is logical, not physical** (decided 2026-06-15). The `tenant:` field on each campaign.yaml + `tenant-brand/<tenant>.yaml` give you the Tenant Dashboard + cross-links **without moving folders**. The earlier business-rooted (`<Tenant>/baseline/` + `<Tenant>/campaigns/`) restructure was superseded — see `docs/specs/phase-0-tenant-baseline.md` §Tenant Dashboard. New tenants and existing tenants share the one flat structure; nothing to migrate.

Use `/library-add` to seed `tenant/library/` with 3-5 best examples from §1.2 discovery — the gold-standard references CD pulls when authoring concepts.

If the tenant supplied actual brand assets (logos as SVG / PNG, fonts as TTF), drop them into `tenant/<slug>/brand-assets/`. Otherwise extract from website at production resolution + flag for upgrade.

---

## §4 — integrations.yaml population (~30-60 min)

Author `tenant/<slug>/integrations.yaml` per the `docs/specs/integrations.md` schema. Sourced from §1.1 Q6 (tech stack) + §1.1 Q5 (compliance posture for escalation paths).

For each platform the tenant uses:
- Set `has_adapter: true | false` based on what's coded in `.claude/skills/deploy-<platform>/`
- Use env-var refs for credentials (`${TENANT_PLATFORM_API_KEY}` — never literal values; deployer fills via OS env at deploy time)
- Populate `defaults` block with anything the tenant already knows (audience IDs, hashtags, from-email patterns)
- Map `channel_defaults` from likely campaign channels → platforms

Populate `escalation` block from §1.1 Q5 (compliance officer) + the operator's standing offer (Slack/email backup).

**Don't ship literal credentials in this file.** Env-var refs only.

---

## §5 — Next phase: Phase 1, the first campaign (NOT part of Phase 0)

**Phase 0 onboarding is complete after §1–§4 + the §6 Tenant Dashboard** — the durable tenant baseline now exists. §5 is the **handoff into Phase 1**: the tenant's first actual campaign. Shown here for continuity, but it is the *next phase*, not an onboarding step.

Phase 1 = run the existing CM **Phase 1 (Fact-Find / Brief)** intake for the first campaign. The tenant Brand Context + Compliance Profile + integrations.yaml + best-practice library already populate most of the Brief by inheritance — the interview is shorter than first-time-without-context because the tenant baseline is pre-captured.

Output: `campaigns/<slug>/brief.md` v1 (set `tenant: <slug>` in the new campaign.yaml so it joins the Tenant Dashboard).

From here the campaign moves through the standard phase flow the dashboards track: **Phase 2 (Concept Design) → Phase 3 (Plan) → Phase 4 (Asset Production) → Phase 5 (Launch / Day-1 Rollout) → Phase 6 (Ongoing Cadence)**.

> **Naming note**: the operator-facing model is **Phase 1–6** (from `campaign.yaml`, shown on every dashboard). The agents and specs were canonicalised onto Phase 1–6 (2026-06-27, Retro-5 Phase 3); the legacy `Stage 1 (1a/1b/1c) / Stage 2` framing is retired.

---

## §6 — Done. What you ship to the tenant.

**Create the tenant identity file** (the last Phase 0 step) — `tenant-brand/<tenant>.yaml`. This is the data that powers the Tenant Dashboard + cross-links. Copy an existing one (`tenant-brand/soundtrak.yaml`) and fill in:
- `tenant` (slug — MUST match the `tenant:` field you'll set on each campaign.yaml), `name`, `nickname`, `summary`
- `baseline:` — one row per Phase 0 artifact with `title` · `href` (relative to `tenant-brand/`) · `status` (`present` once built, else `planned`)

Then build the home:
```
python .claude/skills/render-html/build-tenant-home.py --tenant <tenant>
```
(After this it stays fresh automatically — the stop hook rebuilds all tenant homes whenever a campaign changes.)

**The single surface: the Tenant Dashboard** (`tenant-brand/<tenant>-home.html`) — one operator HTML page that lists the **Phase 0 — Tenant Baseline** compound with links to each underlying artifact (Brand Context · Playbook §0 · Compliance · Segments · Market) **and** lists the tenant's campaigns with links to each campaign dashboard. This is the tenant's home; everything else hangs off it. Generated from `tenant-brand/<tenant>.yaml` + a scan of campaigns where `tenant: <slug>` (operator-surfaces-from-data — same discipline as `campaign.yaml` → dashboard).

Underlying deliverables it links to (flat structure):
- `tenant-brand/<tenant>.html` — durable Brand Context
- `tenant-brand/<tenant>-compliance.html` — Compliance Profile (regulated tenants)
- `tenant-brand/<tenant>-segments.html` · `<tenant>-market.html` · `<tenant>-playbook.html`
- `tenant/<slug>/integrations.yaml` — tech stack codified
- `campaigns/<slug>/dashboard.html` — each campaign (set `tenant: <slug>` in its campaign.yaml)

**Cross-linking — the navigation hierarchy (BUILT, flat):**
- The **master campaign dashboard** (`campaigns/index.html`) gives each campaign card a 🏢 tenant chip → its Tenant Dashboard.
- Each **individual campaign dashboard** carries a 🏢 breadcrumb UP to its Tenant Dashboard.
- The Tenant Dashboard links DOWN to its campaigns + its Phase 0 baseline artifacts.

> **Status (2026-06-15)**: the Tenant Dashboard + cross-links are **built on the flat structure** (`tenant.yaml` + `tenant:` field + `build-tenant-home.py` + breadcrumb/chip in `operator_actions.py`). The earlier W4 business-rooted restructure was superseded — see `docs/specs/phase-0-tenant-baseline.md` §Tenant Dashboard. The only operator step is creating `tenant-brand/<tenant>.yaml` above; everything else is automatic.

If ownership_model is `tenant-self-runs` or `operator-runs-then-tenant`, also schedule the Day 1 session per [`docs/playbooks/client-operator-onboarding.md`](client-operator-onboarding.md).

---

## §7 — System design rationale (read before onboarding — transfers the "why", not just the "how")

The system was built through a dialectic — building it while using it on the Beta Corp campaign. That dialectic produced specific design decisions that aren't obvious from the artifacts alone. A tenant who only learns the "how" will break the system in ways that are hard to diagnose. This section transfers the "why."

**Why markdown-authoritative + HTML-rendered, not a platform (Notion/CMS)?**
Platform lock-in was the risk. If the platform changes pricing, shuts down, or loses a feature, the entire system breaks. Markdown on disk survives any platform change. HTML is just a rendering layer — regenerable in seconds. The system's longevity depends on its independence from any third-party.

**Why operator-in-loop at every gate, not "AI just ships it"?**
Senior practitioners won't trust a system that removes their judgment. The system is a force multiplier, not a replacement. Every gate is a moment where the operator's experience catches something the AI couldn't know. Remove the gates and you get fast mediocrity instead of considered craft.

**Why specs-then-code, not code-then-document?**
Every spec-first cycle caught design errors that would have been ~10x more expensive to fix after building. The Beta Corp Rollout Architecture v2 is the clearest example: the operator caught two structural errors in the v1 spec before a single line of code was written. Specs are cheap; rework is expensive.

**Why hooks for HTML re-render, not manual reminders?**
"Remember to re-render HTML" is a prose discipline — fragile, doesn't survive context switches. State-drift hooks are deterministic mechanisms. The general principle: any rule expressible as "after X, do Y mechanically" should be hook-enforced. Prose disciplines compound into entropy; mechanisms hold.

**Why per-tenant folders + shared infrastructure?**
Cross-tenant data leakage in AI marketing is a liability risk. Structural isolation (tenant A's data physically separate from tenant B's) is more reliable than procedural isolation (discipline about what you feed the AI). The shared `.claude/` + `docs/` layer means improvements to the system benefit all tenants simultaneously, without any data crossing tenant boundaries.

**Why the "compounding foundation" pattern (Wave 0 before Wave 1)?**
A campaign's first wave builds durable assets (email templates, visual system, brand voice implementation) that every subsequent cycle inherits at near-zero marginal cost. The Beta Corp Friday Note cycle 89 cost ~$1.50 in AI + ~30 min operator time because all the capital was already built. Without Wave 0 discipline, every cycle is full-cost.

**What the next tenant needs to know that the first tenant discovered the hard way:**
1. The system has opinions baked in. Don't fight them; understand why they're there first.
2. Memory rules and specs are living artifacts. When something feels wrong, the answer is usually to update the spec — not to work around it.
3. The operator IS part of the system. AI quality scales with the quality of operator input and pushback.
4. Build Wave 0 before Wave 1. Every shortcut here compounds as tech debt.

Per `feedback_build_while_doing_pattern_doesnt_replicate.md`.

---

## §8 — Time-to-skill-extraction

After running this playbook 2-3 times manually:
- Notice which steps you always do the same way → skill-able
- Notice which questions you always ask → skill-able
- Notice which decisions need human taste → keep manual
- Build `.claude/skills/onboard-tenant/SKILL.md` from the deterministic 70%; leave 30% as human-judgment touchpoints

Until then, this playbook is the source of truth.

---

## Cross-references

- **Brand Context spec**: `docs/specs/brand-context.md` — what §2 produces
- **Brief spec v2**: `docs/specs/brief.md` — what §5 produces
- **integrations.yaml spec**: `docs/specs/integrations.md` — what §4 produces
- **Rollout Architecture v2**: `docs/specs/rollout-architecture.md` — system context for why this playbook exists
- **Client-operator onboarding**: `docs/playbooks/client-operator-onboarding.md` — what comes after this for tenant-self-runs / handoff models
