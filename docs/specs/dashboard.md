# Campaign Dashboard — schema

**Spec version**: v1 · 2026-06-15 (extracted from CM SKILL.md to de-bloat the skill; CM cites this).

The per-campaign dashboard (`campaigns/<slug>/<slug>.md` → `dashboard.html`) is the operator's persistent view of where a campaign is. CM authors it at Phase 1 and re-renders it on every state change. The cross-campaign `index.html` links to it — never to a downstream artifact.

**Auto-marker first.** Prefer the injection markers over hand-authored blocks (they self-maintain and can't drift): `<!-- PHASES_AUTO -->` (phases from `campaign.yaml`, artifact links existence-checked) · `<!-- OPERATOR_ACTIONS_AUTO -->` (the 🚨 To Do, same styled priority-pill table as tasks.html) · `<!-- ASSET_LIST_AUTO -->` (full asset list, rows route to the gallery) · `<!-- COST_TOTAL_AUTO -->` (ledger-derived AI-cost line). Hand-authored To Do / asset-list / cost blocks drift — use the markers.

## 7-block structure (confirmed 2026-06-04; supersedes the 5-block structure)

### Block 1 — Phases + Artifacts (above fold, always visible — primary nav anchor)
One table: **Phase | Description | Status | Window | Human Time | AI Cost | Artifacts**. One row per Phase 1–6 (+ a **Total** row).

| Phase | Description | Status | Window | Human Time | AI Cost | Artifacts |
|---|---|---|---|---|---|---|
| 1 | Fact-Find (Brief + Brand Context) | ✅ Approved | 2026-05-29 | ~55 min | ~$0.96 · ~160k tok | [Brief ✅](brief.html) · [Brand Context ✅](../../tenant-brand/x.html) |
| 2 | Concept Design | ✅ Approved | … | … | … | [Selected concept ✅](concepts/selected.html) |
| 3 | Plan | ✅ Approved | … | … | … | [Plan ✅](plan.html) |
| 4 | Asset Production | 🔄 In progress | … | — | … | [Gallery](gallery.html) |
| 5 | Launch / Day-1 Rollout | ⏳ Pending | — | — | — | [Phase 5 Launch](phase-5-rollout.html) (built at end of Phase 4) |
| 6 | Ongoing Cadence | ⏳ Pending | — | — | — | [Phase 6 Cadence](phase-6-cadence.html) (built at end of Phase 4; cadenced) |
| **Total** | | | | **~Xh Xm** | **~$X.XX · ~Xk tok** | |

Artifact links: `[Name ✅/🔄/⏳](url)` — ✅ approved · 🔄 drafted/in-review · ⏳ pending.

### Block 2 — 🚨 To Do (above fold, always visible)
Columns: **Priority | Phase | Task | What to do | Last touched | Time | Where**. ALL operator-actionable items (pending gates · pre-flight · optional momentum). Completed items move to History (Block 7) immediately — never linger.

### Blocks 3–7 (`<details markdown="1">` collapsed)
- **3 — 🤖 Producers in flight**: Producer · Asset · doing-now · expected return. "None in flight" when idle.
- **4 — 📋 Full asset list**: Gallery link at top, then Asset # · name · Status · Human Time · AI Cost. Mirrors the Plan.
- **5 — 🎯 KPIs**: KPI · Target · Stretch · Deadline · Result (baseline → current).
- **6 — 💰 Budget**: Total (LOCKED) · Spent · Remaining · one-line allocation note.
- **7 — 📜 History** (absorbs the old ✅ Done block): Date · What · Status. Append-only, most recent first.

## Task-entry format (Block 2 + `tasks.md`)

| Column | Content |
|---|---|
| Task | One-line action ("Approve the Comparison Run Pool") |
| Context | One sentence: what it is · what triggered it · what the outcome enables |
| Last touched | Date of last state change |
| Why it matters | The decision/outcome it enables, in business terms |
| What's needed | Link to cookbook (execution gap) OR decision frame (operator-owned call) |

**Cold-start test**: an operator returning after 7 days orients in 30 seconds. If not, the entry is too summarised — expand.

## Header discipline

- **Every dashboard carries a `**Last updated**: YYYY-MM-DD` line** in its header block, bumped on every state-changing turn. (A dashboard with no stamp is a surface-quality failure — the operator can't tell if it's current.)
- **Tenant breadcrumb** (`🏢 Tenant: <name>`) is injected after the H1 at render time from `campaign.yaml` `tenant:` — see `phase-0-tenant-baseline.md` §Tenant Dashboard.

## Phase-1 minimum dashboard (mandatory at campaign open)

Per [[feedback_campaign_dashboard_exists_from_stage_1a]]: the dashboard exists from the moment the Brief exists. Phases table shows Brief = Drafted, everything else Pending; per-asset table = "Pending Plan approval"; 🚨 To Do shows only "Approve Brief". Mostly empty by design — emptiness reflects state truthfully, and the index never points at `brief.html` instead of a dashboard.

## Human-Time estimation (populate at gate close only — never project forward)

| Operator action | Estimate |
|---|---|
| Grill-me brief interview (per field) | +2 min |
| Reading + approving a Brief | +10 min |
| Reviewing a Concept trio (full three) | +25 min |
| Reviewing a single asset preview | +8 min |
| Reviewing a Plan | +10 min |
| Each send-back cycle | +5 min |
| Each additional Q&A exchange in a gate | +2 min |

Round to nearest minute: `~X min` (<60) or `~Xh Xm` (≥60). Human Time is `—` until the phase gate closes.

## AI Cost

**Do not hand-estimate.** AI cost renders from the cost ledger via `<!-- COST_TOTAL_AUTO -->` (metered per dispatch — see the `cost-ledger` skill). CM appends a ledger entry on every subagent return that reports usage; the dashboard total can't go stale because nobody hand-maintains it. Cost footnote (paste below the Phases table):

> *AI cost from the metered ledger (`.claude/state/cost-ledger.jsonl`) where available; CM estimates flagged separately. CD = Opus 4.8; CM / Brand / Producer / Governance = Sonnet 4.6. Actual charges at [console.anthropic.com](https://console.anthropic.com).*

## Operator-surface copy contract (SYS-069 review · 2026-07-15)

Every operator surface obeys these so the language stays human and consistent (`feedback_operator_facing_plain_language`):
- **One name for the operator's action list: "To Do"** (Title Case) — never "Tasks queue" / "Next action" / "Awaiting you". *(Exception: the System Manager dashboard's deliberate "Needs you" / "AI can action" split is a considered distinction, not drift.)*
- **Plain asset names, never internal codes.** Say the asset's plain name; never surface "A6" / "Wave 2" / "gate-cleared" to the operator (say "checked and ready for you"). Per `feedback_plan_is_source_of_truth` + `feedback_operator_facing_plain_language`.
- **No system/file jargon on the surface.** Never show `campaign.yaml` / `asset.yaml` / `_AUTO` / `§N` / template names / file paths in operator-facing text. Auto-injected footnotes read as plain English ("This list keeps itself up to date…"), not "auto-derived from …yaml".
- **Audit detail collapses.** Dense history / per-asset verdict prose goes below the fold in `<details>`; the top of the surface carries only the decision.
- **Empty states greet + point** ("No campaigns yet — say 'start a campaign' to begin."), never a curt "(no X found)".
- **The test:** *could a smart person who has never seen this system act on this line without asking?* If no, rewrite or cut it.
- **Emoji in headings** are a consistent wayfinding aid or absent — not sprinkled on some surfaces and not others.

## Cross-references
- `render-pipeline.md` — the auto-injection markers + operator-surface rendering contract
- `cost-ledger` skill — the metered AI-cost source for `COST_TOTAL_AUTO`
- `phase-0-tenant-baseline.md` — the tenant breadcrumb + tenant-home cross-links
