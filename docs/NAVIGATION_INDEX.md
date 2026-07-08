# AI Marketing System — Navigation Index

**The system's own dashboard.** Everything in the system lives in one of the document classes below. If you're cold-starting and don't know where something is, start here.

**Last updated**: 2026-07-08
**Version**: v3

> **Kept fresh by `nav-audit`** (`.claude/skills/nav-audit/nav_audit.py`) — diffs this index against the specs/skills/agents/playbooks on disk and flags anything missing, any dead link, a stale stamp, and the oldest-untouched docs. It runs as part of `system-smoke-test` (so any "run smoke test" catches index drift) and on demand ("run nav audit"). When you add a spec/skill/agent/playbook, add a row here — the audit will catch it if you forget.

---

## How to read this index

Each section answers: *what kind of thing is this, when do you read it, and where does it live?*

---

## 1. Operating manual (read first in every session)

| What | What it is | Where |
|---|---|---|
| **workflow.md** | The operating manual. How the system works end-to-end: agent inventory, campaign phases, operator gates, render pipeline. READ FIRST in any new session. | `docs/workflow.md` |
| **README.md** | System overview + repository structure + backup instructions. Written for GitHub; useful for orientation. | `Marketing AI System/README.md` |

---

## 2. Specs (canonical schemas — all campaigns inherit)

*Specs define the structure of artifacts. When an artifact doesn't look right, check the spec first.*

**Grouped by category** — artifact schemas · asset-type specs · architecture & process — in [`docs/specs/README.md`](specs/README.md).

| Spec | What it governs | Where |
|---|---|---|
| **Rollout Architecture v2** | The 6-phase campaign lifecycle backbone. Why the phases exist and what each produces. | `docs/specs/rollout-architecture.md` |
| **Brief spec v2** | Campaign brief schema + grill-me interview discipline. | `docs/specs/brief.md` |
| **Concept spec** | Creative trio (Safe/Smart/Wild) schema + CD outputs required. | `docs/specs/concept.md` |
| **Plan spec v2** | Asset list schema (incl. Review shape + Copy file columns) + §N Phase readiness gate. | `docs/specs/plan.md` |
| **Per-Step Brief spec** | CM → Producer dispatch envelope. What every brief must contain. | `docs/specs/per-step-brief.md` |
| **Asset spec** | Asset folder structure standard + asset.yaml schema + gallery modal rules (3-block: rationale / gate questions / next steps). | `docs/specs/asset.md` |
| **Brand Context spec** | Tenant brand context schema + BC slicing guide by asset form. | `docs/specs/brand-context.md` |
| **Phase 5 spec** | Day-1 Rollout artifact schema. | `docs/specs/phase-5-rollout.md` |
| **Phase 6 spec** | Ongoing Cadence artifact schema + cycle checklist structure. | `docs/specs/phase-6-cadence.md` |
| **integrations.yaml spec** | Per-tenant platform integrations schema (credentials refs, channel defaults, adapters). | `docs/specs/integrations.md` |
| **Retro spec** | Retro schema + authoring discipline + approval gate. | `docs/specs/retro.md` |
| **Battle Cards spec** | Gong-aligned battle card structure (4 principles, Rule of Three, FIA format). | `docs/specs/battle-cards.md` |
| **Pitch Deck spec** | 7-act canonical pitch deck narrative arc. 11-13 slides. | `docs/specs/pitch-deck.md` |
| **Cookbook spec** | Operator-facing deploy/verify cookbook schema. | `docs/specs/cookbook.md` |
| **Render pipeline spec** | Inventory of the 5 render scripts + consolidation proposal (deferred). | `docs/specs/render-pipeline.md` |
| **Practitioner frameworks** | The embedded practitioner playbook (the full 53 principles) + how agents use it. | `craft/frameworks/README.md` |
| **Tenant Playbook spec** | Per-tenant tactical learnings record — the campaign-to-campaign inheritance vehicle (graduate-then-cite, three-layer model). | `docs/specs/tenant-playbook.md` |
| **Phase 0 — Tenant Baseline spec** | The per-tenant baseline every campaign inherits: Brand Context · Compliance Profile · segment map · market landscape · playbook · research library · audience-truths · integrations. | `docs/specs/phase-0-tenant-baseline.md` |
| **Insight Brief spec** | Phase-1 Insights Manager artifact: per-segment human+market insight (§1) · routes to market (§2, channels + GTM partnerships) · restorable kill register (§3) · source sweep · durable updates · freshness. | `docs/specs/insight-brief.md` |
| **Research Library spec** | The SHARED, faceted research corpus (public research, cross-tenant) the `insight-scan` cites before fetching. Distinct from the creative `tenant/library/`. | `docs/specs/research-library.md` |
| **Audience Truths spec** | Durable per-segment enduring truths (tenant-scoped), refreshed from each Insight Brief §5 at wrap. | `docs/specs/audience-truths.md` |
| **Compliance Profile spec** | Per-tenant regulatory ruleset the Governance Manager authors (Phase 0) + gates against (Phase 4) — disclaimer library, prohibited claims, mandatories, risk tiers. | `docs/specs/compliance-profile.md` |
| **Campaign Report spec** | Forensic Data analyst's close-out results report schema (KPIs vs target, funnel, drivers, evidence-tagged). | `docs/specs/campaign-report.md` |
| **Dashboard spec** | Per-campaign dashboard structure (7-block) + the auto-injection markers (STATUS / PHASES / OPERATOR_ACTIONS / …). | `docs/specs/dashboard.md` |
| **Gallery QA spec** | Pre-surface gallery checklist + the Plan-Ships ⇄ gallery-tile contract (check before the operator sees it). | `docs/specs/gallery-qa.md` |
| **Data Architecture spec** | Storage model — markdown authoritative, HTML rendered, OneDrive + Git dual-backed; render-pipeline contract. | `docs/specs/data-architecture.md` |
| **System Manager spec** | The System-layer owner: backlog + idea inbox + audit schema, the operator dashboard (To Do split "Needs you" / "AI can action" + audit history), and the capture / triage / retro / groom workflows. | `docs/specs/system-manager.md` |
| **Agent I/O Contract spec** | Structured dispatch + return envelopes for CM↔agent handoffs (machine-checkable orchestration: ship-file existence, explicit verdicts, cost capture). WIRED (additive) — SYS-004 Steps 2-3: validator (`agent-io` skill) + agents emit + CM validates; Step 4 (sole source of truth) gated. | `docs/specs/agent-io-contract.md` |
| **Standalone Deployment spec** | Retro-5: packaging the system as a clean single-tenant "Seed" — ship/tenant/personal manifest, the `build_seed` allowlist cut + leak scan, Phase-0 hard gate, install doctor, the phased plan + safety model. | `docs/specs/standalone-deployment.md` |
| **Download-gate spec** | SYS-048: the soundtrak.com "Agree & Download" click-wrap gate (spec + copy) that strengthens contract formation beyond the repo's browse-wrap, pairing with the in-tool first-run acceptance gate. Master-internal (not shipped in the Seed). | `docs/specs/download-gate.md` |

---

## 3. Playbooks (the operator's runbooks)

*Playbooks are step-by-step operator runbooks for recurring processes. They tell you exactly what to do, in order.*

| Playbook | What it covers | When to use | Where |
|---|---|---|---|
| **Onboard a new tenant** | Fact-find → Brand Context → folder structure → integrations → first campaign Brief. Includes §7 System design rationale (transfer the "why" to new tenants). | First conversation after "yes, let's do this" | `docs/playbooks/onboard-tenant.md` |
| **Client operator onboarding** | Day-1 handoff session + 4-week standby for tenant-self-runs or handoff models. | Phase 5 execution for non-the operator-runs tenants | `docs/playbooks/client-operator-onboarding.md` |
| **Pre-sync hygiene** | Checklist before running sync-tenant.ps1. Prevents cross-tenant leakage and dirty master propagation. | Before any master → tenant sync | `docs/playbooks/pre-sync-hygiene.md` |
| **Sync master to tenant** | PowerShell + rsync mechanics for propagating master to a tenant's OneDrive. | Phase 6 setup | `docs/playbooks/sync-master-to-tenant.md` |
| **Deployment guide** | Non-technical install/setup runbook. **Superseded by `docs/guide/deployment-guide.html`** (Soundtrak HTML); kept as source. | Reference only | `docs/playbooks/deployment-guide.md` |
| **Onboarding checklist** | First-run getting-started checklist. **Superseded by `docs/guide/getting-started.html`**; kept as source. | Reference only | `docs/playbooks/onboarding-checklist.md` |
| **FAQ** | Self-service Q&A. **Superseded by `docs/guide/help.html`** (Help & Guides hub); kept as source. | Reference only | `docs/playbooks/faq.md` |

---

## 4. Agent definitions (specialist AI agents)

*Agent definitions tell each agent who they are, what they do, and how to do it. CM reads these when dispatching.*

| Agent | Role | Where |
|---|---|---|
| **Campaign Manager** | Orchestrator. Runs the phases, authors briefs/plans, dispatches specialists. | `.claude/skills/campaign-manager/SKILL.md` |
| **Insights Manager** | Phase-1 Insight Brief author (per-segment human + market insight that fuels the big idea); Phase-4 advisory resonance read. | `.claude/agents/insights-manager/AGENT.md` |
| **Creative Director** | Concept trio author (built on the Insight Brief) + Brand Context author. | `.claude/agents/creative-director/AGENT.md` |
| **Governance Manager** | Compliance/legal/regulatory gate (Phase 4); Compliance Profile author (Phase 0). Red-flag-for-human-review, not legal advice. | `.claude/agents/governance-manager/AGENT.md` |
| **Brand Manager** | Asset verdict giver. Reviews every asset before operator sees it. | `.claude/agents/brand-manager/AGENT.md` |
| **Producer** | Builds the finished asset: copy + visuals + structural elements + cookbooks. | `.claude/agents/producer/AGENT.md` |
| **Marketing Forensic Analyst** | Performance data investigator. Forensic pass on analytics, funnels, campaign post-mortems. | `.claude/agents/marketing-forensic-analyst/AGENT.md` |

---

## 5. Skills (operator-invocable entry points)

*Skills are invoked by natural language. The `description:` block in each SKILL.md is the trigger mechanism — not the slash command.*

*All skills live in `.claude/skills/<name>/` (the SKILL.md is the entry point).*

| Skill | What it does | Trigger phrases | Where |
|---|---|---|---|
| **campaign-manager** | Main system entry point. Start campaigns, advance them, get status. | "start campaign", "what's next", "ship the asset" | `.claude/skills/campaign-manager/` |
| **render-html** | Markdown → HTML for any doc class. | "render this", "generate HTML" | `.claude/skills/render-html/` |
| **asset-gallery** | Builds the per-campaign gallery.html with tiles, lightbox, modal. | Called by CM automatically | `.claude/skills/asset-gallery/` |
| **canva-design** | Mode B visual production via Canva MCP. | Called by Producer | `.claude/skills/canva-design/` |
| **replicate-generate** | Mode A AI visual generation via Replicate API. | Called by Producer | `.claude/skills/replicate-generate/` |
| **library-add** | Adds a URL/asset to the tenant library. | "add this to the library" | `.claude/skills/library-add/` |
| **insight-scan** | The Insights Manager's disciplined multi-source web sweep (research library cite-first · human-behaviour · cohort voice · trade media · GTM/partnership routes). Feeds the Insight Brief. | Called by Insights Manager (Phase 1) | `.claude/skills/insight-scan/` |
| **cost-ledger** | Per-dispatch AI cost ledger; dashboard AI-cost totals render from it (COST_TOTAL_AUTO). | Called by CM on each subagent return | `.claude/skills/cost-ledger/` |
| **agent-io** | Validates the agent I/O contract (SYS-004) — the structured `return:` envelope that rides alongside each agent's prose. CM runs `validate_envelope.py` on every return (dispatch_id pairing · status · per-agent required fields · ship-file existence) + appends the pair to the dispatch ledger. Additive / non-breaking. | Called by CM on each subagent return; "validate the envelope" | `.claude/skills/agent-io/` |
| **content-subedit** | Sub-edits LinkedIn posts / Substack articles against the Soundtrak voice rules. | "sub-edit this", "check against the voice rules" | `.claude/skills/content-subedit/` |
| **deploy-mailchimp** | Pushes email assets to Mailchimp via API. | Called by CM at Phase 6 | `.claude/skills/deploy-mailchimp/` |
| **deploy-cookbook** | Universal cookbook-based deployment fallback. | Called by CM at Phase 6 | `.claude/skills/deploy-cookbook/` |
| **system-smoke-test** | Health check: render pipeline + operator-quartet (all campaigns) + hooks + git + nav-index. Returns red/amber/green. | "run system smoke test", "check system health" | `.claude/skills/system-smoke-test/` |
| **system-drift-watcher** | Cross-campaign drift scan (stale dashboards · zombie To-Do rows · in-flight Producers · stale cross-refs). | "check system drift", "anything stale?" | `.claude/skills/system-drift-watcher/` |
| **cm-audit** | Surface-currency audit — every operator surface (dashboard/gallery/tasks/index/tenant-home) re-rendered after its data source changed. | "run cm audit", "are the surfaces current?" | `.claude/skills/cm-audit/` |
| **nav-audit** | Keeps this index honest — diffs `NAVIGATION_INDEX.md` against specs/skills/agents/playbooks on disk; flags missing entries, dead links, stale stamp + oldest docs. | "run nav audit", "is the navigation index fresh?" | `.claude/skills/nav-audit/` |
| **docs-audit** | The CONTENT/STRUCTURE layer over nav-audit — reads INSIDE the docs: stale agent-count prose (five/six after the 7th agent), class tables that lost a column, `docs/public/` behind the roster/specs, and §9/§10/§11 coverage vs disk (SYS-018/SYS-026 drift class). | "run docs audit", "are the docs consistent?", "is the agent count right everywhere?" | `.claude/skills/docs-audit/` |
| **cadences** | Four proactive scheduled sweeps — competitor/library scan · tenant brand-drift · stale-asset/surface · per-tenant shipped/blocked rollup. Surface-only (file deduped inbox ideas, never auto-ship). | Scheduled (weekly/monthly) via Windows tasks | `.claude/skills/cadences/` |
| **system-manager** | Owner of the System layer — maintains the system-improvement backlog + idea inbox + audit history and the operator dashboard (To Do split Needs-you / AI-can-action + audit history), independent of any campaign. Capture / triage / retro / groom. | "system idea: …", "triage the inbox", "run a system retro", "/system-manager" | `.claude/skills/system-manager/` |

### Tenant-specific skills

*Scoped to one tenant's workflow (Soundtrak content · Acme Co podcast), not the general system. **Excluded from the public Seed** (the `build_seed` deny-list) — a fresh deployment ships without them. Listed here for completeness.*

| Skill | What it does | Trigger phrases | Where |
|---|---|---|---|
| **thought-leadership** | the operator's content workflow: a pasted concept / principle / research → LinkedIn + Substack pieces (orchestrates the three skills below). | "new concept", "let's do a piece on X", "run the feedback loop" | `.claude/skills/thought-leadership/` |
| **behavior-gap-sketch** | Distils raw text into one Carl Richards / Behavior-Gap visual metaphor + a copy-paste image prompt. | `/carl-image` | `.claude/skills/behavior-gap-sketch/` |
| **linkedin-post** | Turns the same principle into a high-impact LinkedIn post, paired with the sketch. | `/image-social-post` | `.claude/skills/linkedin-post/` |
| **long-form** | Turns the same principle into a feature-length Substack article. | `/long-form` | `.claude/skills/long-form/` |
| **publish-soundtrak-article-website** | Publishes a finished article to soundtrakconsulting.com/thinking/ (docx + hero image + Substack URL). | "publish article", "publish to soundtrak" | `.claude/skills/publish-soundtrak-article-website/` |
| **sb-podcast-weekly-assets** | Acme Co "Acme Co Talks" Friday cycle: transcript + URL → full asset bundle. | "run weekly cadence for Acme Co Talks" | `.claude/skills/sb-podcast-weekly-assets/` |

---

## 6. Tenant data (per-client, not system)

*Tenant data is campaign-specific. It lives alongside the system but belongs to individual clients.*

| What | What it contains | Where |
|---|---|---|
| **Brand Context** | Voice rules, visual identity, compliance posture, channels, gold standards. Per tenant. | `tenant-brand/<tenant-slug>.md` |
| **Compliance Profile** | Per-tenant regulatory ruleset the Governance Manager authors in Phase 0 + gates against in Phase 4: disclaimer library, prohibited claims, mandatories, risk tiers. | `tenant-brand/<tenant>-compliance.md` |
| **Segment map** | Per-tenant needs-based segmentation (the buyer groups the Insight Brief works per-segment). | `tenant-brand/<tenant>-segments.md` |
| **Market landscape** | Per-tenant market context: category, competitors, positioning terrain the insight + concept build on. | `tenant-brand/<tenant>-market.md` |
| **Tenant playbook** | Per-tenant tactical-learnings record — the campaign-to-campaign inheritance vehicle (graduate-then-cite, three-layer model). | `tenant-brand/<tenant>-playbook.md` |
| **Audience truths** | Durable per-segment enduring truths, per tenant. Refreshed from each Insight Brief §5 at wrap. | `tenant-brand/<tenant>-audience-truths.md` |
| **Tech / martech stack** | The tenant's tooling. Authored as the Brief's `tech_stack` block (per campaign) + each tenant's `integrations.yaml` `channel_defaults` (platform defaults). NOT a hidden field — it is an explicit, authored artifact. | Brief `tech_stack` + `tenant/<tenant-slug>/integrations.yaml` |
| **Tenant config** | `integrations.yaml` (platform creds refs + `channel_defaults`), brand assets, per-tenant library. | `tenant/<tenant-slug>/` |
| **Reference library** | 92-entry inspiration + gold-standard library. Cross-tenant. Faceted (vertical, shape, idea_or_tactic). | `tenant/library/` |
| **Research library (SHARED)** | Cross-tenant public-research corpus the `insight-scan` cites before fetching. Faceted (vertical · audience · topic · layer [market/human-behaviour] · source-type). Distinct from the creative `tenant/library/`. | `tenant/research-library/` |

---

## 7. Campaign artifacts (per-campaign)

*Each active campaign lives in its own folder. Every campaign has the same structure.*

| Artifact | What it is | Path pattern |
|---|---|---|
| Campaign dashboard | The campaign's home page. Phases + Artifacts, To Do, History. | `campaigns/<slug>/<slug>.md` |
| Brief | Campaign strategy: who/what/why/budget/timeline/tech/people. | `campaigns/<slug>/brief.md` |
| Concept | Selected creative concept. Big Idea, Key Message, 15-sec pitch, visuals. | `campaigns/<slug>/concepts/selected.md` |
| Plan | Asset list with Review shape + Copy file columns. Phase readiness. | `campaigns/<slug>/plan.md` |
| Gallery | Visual gallery of all campaign assets. Channel-grouped, with modal. | `campaigns/<slug>/gallery.html` |
| Phase 5 Rollout | Day-1 deployment runbook for this campaign. | `campaigns/<slug>/phase-5-rollout.md` |
| Phase 6 Cadence | Ongoing cycle runbook. Campaign DNA header. | `campaigns/<slug>/phase-6-cadence.md` |
| Assets | Per-asset folders: HTML/PNG + asset.yaml + copy.md + cookbooks. | `campaigns/<slug>/assets/<asset-slug>/` |
| Retros | Campaign-specific retros. | `campaigns/<slug>/retros/` |

---

## 8. System infrastructure (runtime machinery)

*Don't touch unless you know what you're doing. These files make the system work.*

| What | What it does | Where |
|---|---|---|
| **PostToolUse hook** | Classifies every file write and updates the dirty-campaigns ledger. | `.claude/hooks/post_tool_use.py` |
| **Stop hook** | Drains the ledger: re-renders dashboards, galleries, tasks, index. Auto-backs up to GitHub. | `.claude/hooks/stop.py` |
| **settings.json** | Wires hooks into Claude Code. Uses `${CLAUDE_PROJECT_DIR}` for CWD-safe paths. | `.claude/settings.json` |
| **dirty-campaigns.json** | Per-session ledger of which campaigns were touched. Drained by Stop hook. | `.claude/state/dirty-campaigns.json` |
| **hook-latency.json** | Latency log for PostToolUse hook. Check if sessions feel slow. | `.claude/state/hook-latency.json` |
| **build-gallery.py** | Generates gallery.html: thumbnails via Playwright, 3-block modal, campaign DNA, copy/download buttons. Reads `asset.yaml` `status:` field first (load-bearing); falls back to MD scan. | `.claude/skills/asset-gallery/build-gallery.py` |
| **render.py** | Markdown → HTML renderer. Templates: base, dashboard, tasks, index, asset-preview. Dashboard template auto-injects operator-actions To Do table via `operator_actions.py` (replaces `<!-- OPERATOR_ACTIONS_AUTO -->` marker). | `.claude/skills/render-html/render.py` |
| **operator_actions.py** | Scans every `assets/*/asset.yaml` in a campaign for pending `operator_actions:` entries and renders them as the dashboard's auto-generated To Do block. Single source of truth — dashboard To Do is now derived, not hand-authored. | `.claude/skills/render-html/operator_actions.py` |
| **status-propagator** | Single command updates asset status across all the layers that gallery + dashboard read from (asset.yaml + numeric-prefix .md + preview.md + HTMLs + gallery + dashboard). Also handles `--task <id> --done` to mark individual operator-actions complete. Replaces the manual ~9-touch-point discipline. | `.claude/skills/status-propagator/propagate.py` · [SKILL.md](../.claude/skills/status-propagator/SKILL.md) |
| **check-state** | Read-only drift detector. Walks every asset folder in one campaign or all campaigns and reports any disagreement between yaml status, numeric-prefix asset record, preview.md, and dashboard mentions of approved assets. Pair with status-propagator to fix what it finds. | `.claude/skills/check-state/check.py` · [SKILL.md](../.claude/skills/check-state/SKILL.md) |
| **build-dashboard.py** | Generates `system/dashboard.html` (the System Operator Dashboard): To Do split into Needs-you / AI-can-action (in_progress as a tag) + a prominent inbox CTA → triage lightbox + audit history. Reads the `system/` data store; inlines system.css. Re-run after any backlog/ideas/audit edit. | `.claude/skills/system-manager/build-dashboard.py` |
| **system/ data store** | The System-layer source of truth: `backlog.yaml` (tickets) · `ideas.yaml` (idea inbox) · `audit-log.yaml` (history) → `dashboard.html` (generated). In-repo (campaigns/ is a separate repo). | `system/` |
| **repo_paths.py** | Canonical data-root resolver: `data_root()` / `is_worktree()`. Lets diagnostics + the System Manager resolve campaigns/ · system/ · tenant-brand/ to the MAIN checkout when run from a `.claude/worktrees/*` checkout (SYS-002). | `.claude/lib/repo_paths.py` |
| **weekly-digest.py** | SYS-005 — read-only weekly groom-lite: runs diagnostics, summarises open work + inbox, auto-files new failures as deduped ideas, writes `system/digests/<date>.md`. Built for a weekly schedule. | `.claude/skills/system-manager/weekly-digest.py` |

---

## 9. Memory rules (system learnings — indexed by subject)

*Memory rules capture what the system learned through doing. They're stored in `~/.claude/projects/.../memory/`. Listed here by subject area.*

| Subject | Memory rule | Key learning |
|---|---|---|
| **System architecture** | `reframe_cmo_force_multiplier.md` | Force multiplier, not replacement. All downstream flows from this. |
| **Propagation** | `feedback_captured_rules_require_explicit_propagation.md` | Memory writes are inert until specs/agents/skills are updated. |
| **Propagation** | `feedback_propagation_failure_modes_recur_across_dimensions.md` | Generalised: ANY artifact change needs downstream propagation. |
| **Plan authoring** | `feedback_plan_declares_review_shape_and_copy_file.md` | Plan must declare Review shape + Copy file for every asset. Drives Producer, gallery, approval scope. |
| **Gallery QA** | `feedback_cm_owns_gallery_qa_before_operator_surface.md` | CM checks gallery before operator sees it. 7-point checklist. |
| **HTML deployment** | `feedback_html_web_page_folder_structure.md` | `index.html` + `images/` at root. No campaign files in the deployable folder. |
| **Asset review** | `feedback_gallery_publish_aware_producer.md` | Producer ships asset.yaml + gallery-recognised headers. Gallery reads declarative metadata. |
| **Retros** | `feedback_retros_are_system_artifacts_not_conversations.md` | Retros generate memory rules + spec changes. Incomplete until §4 propagated. |
| **Tenant onboarding** | `feedback_build_while_doing_pattern_doesnt_replicate.md` | The dialectic that built the system doesn't transfer automatically. Read onboard-tenant.md §7. |
| **Skills** | `feedback_skill_discovery_is_description_match_not_autocomplete.md` | Description block is the load-bearing discovery path. Host UX is fragile. |
| **GitHub backup** | `reference_github_repos.md` | Two repos: ai-marketing-system + soundtrak-campaigns. Auto-backup via stop hook. |

*Full memory rule list lives in `~/.claude/projects/C--Users-operator-OneDrive-Claude-Marketing-AI-System/memory/`. This index covers the highest-leverage rules.*

---

## 10. System retros

*System-level retros track what the system learned about itself.*

| Retro | Scope | Status |
|---|---|---|
| Retro 001 — 2026-05-28 | First end-to-end system build. CMO force-multiplier reframe. | ✅ Closed (see MEMORY.md) |
| Retro 002 — 2026-06-04 | Architecture + Wave 0 + first Phase 6 cycle. 13 items, all executed. | ✅ Closed — `campaigns/acme-co-podcast-engine-2026q2/retros/2026-06-04-rollout-arch-v2-end-to-end.md` |
| Retro 003 — 2026-06-08 | AI Marketing System process retro (this doc's execution session). 12 items E1-E12. | ✅ Closed — `docs/retros/2026-06-04-ai-marketing-system.md` |
| Retro 004 — 2026-06-12 | Phase 2 redesign inputs (objective taxonomy · concept litmus · §0 schema · graduate-then-cite). | ✅ Closed — `docs/retros/2026-06-12-phase2-redesign-inputs.md` |
| Retro 005 — 2026-06-23 | Insights Manager (7th agent) + enhancement arc (resonance read · human-first method · shared research library · §2 routes-to-market · gallery lightbox · concept visual board + exposed kill register · nav-audit · Claude-in-Chrome raw-voice store). §4 shipped in-session; all checks green. | ✅ Closed — `docs/retros/2026-06-23-insights-manager-and-enhancements.md` |

---

## 11. Public-facing artifacts (`docs/public/`)

*Prospect/RFP/demo materials. Versioned. Maintained as the system evolves.*

| Doc | Audience | Purpose |
|---|---|---|
| [`docs/public/system-overview.md`](public/system-overview.html) | Prospects, first conversations | Plain-English what-it-does. Benefits-led. Leave-behind reference. |
| [`docs/public/feature-list.md`](public/feature-list.html) | RFP responders, procurement, technical evaluators | Technical/structural feature inventory. Side-by-side comparison vs typical in-house team and traditional agency. Architecture, agents, phases, surfaces, toolchain, multi-tenancy, audit, RFP-checklist. |
| [`docs/public/demo-walkthrough.md`](public/demo-walkthrough.html) | the operator (running a prospect demo) | 10-min screen-by-screen demo script. Uses Acme Co as the live tenant. 10 steps · timing table · short/technical/compliance variations. |
| [`docs/public/architecture-ai-native.md`](public/architecture-ai-native.html) | Engineers, AI practitioners, technical founders | Full architecture explainer: context stack, agent topology (librarian pattern), three-layer model, control flow, deterministic layer, technical feature list, inventory. |
| [`docs/public/architecture-plain-english.md`](public/architecture-plain-english.html) | Anyone — zero technical knowledge assumed | Same system explained as a small agency: the seven roles (Campaign Manager + six specialists), the four decisions, what you see in the browser, memory + safety rails, FAQ. |
