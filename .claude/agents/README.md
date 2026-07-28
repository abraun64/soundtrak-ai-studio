# Agents (subagents)

Per-role specialist **subagents** live here. A subagent runs in isolated context, is invoked via the Task tool (usually by the Campaign Manager skill), does one-shot work, and returns a single verdict or artifact. Good fit for parallelisable, context-isolated, single-deliverable work.

**Orchestration lives in `.claude/skills/`, not here.** The Campaign Manager is a *skill* — it runs in the main thread and holds sustained campaign context; it invokes the subagents below as needed.

## The roster (7 roles)

Seven roles run the system: the Campaign Manager skill, plus six specialist subagents.

| Role | Kind | Lives in | Does |
|---|---|---|---|
| **Campaign Manager** | skill | `.claude/skills/campaign-manager/` | Orchestrator — authors the Brief, routes work to the specialists, holds the gates, owns the operator surfaces. |
| **Creative Director** | subagent | `creative-director/` | Phase 2 — authors the creative trio of three Concepts (one Recommended) via a divergent→convergent process. |
| **Insights Manager** | subagent | `insights-manager/` | Phase 1 — evidence-backed Insight Brief (per-segment insights + routes to market); Phase 4 advisory resonance read; stewards the tenant Audience Truths + research library. |
| **Governance Manager** | subagent | `governance-manager/` | Phase 0 Compliance Profile; Phase 4b compliance gate — the legal floor, runs **before** Brand Manager. |
| **Brand Manager** | subagent | `brand-manager/` | Phase 0 Brand Context steward; Phase 4b brand gate — the taste ceiling. |
| **Producer** | subagent | `producer/` | Produces every asset across every form — copy + visuals + structure — from a self-contained Per-Step Brief. |
| **Marketing Forensic Analyst** | subagent | `marketing-forensic-analyst/` | Read-only deep forensic pass on performance data (channel analytics, post-mortems, funnel diagnosis); returns an evidence-tagged report. Never invents numbers. |

Each subagent has its own subfolder with an `AGENT.md`: the frontmatter declares when it's invoked; the body defines its responsibilities and the skills it calls. Subagents read only the slices the Campaign Manager injects — they do **not** load tenant brand files directly.

## Why skill vs subagent

| Concern | Skill | Subagent |
|---|---|---|
| Runs in | Main conversation context | Isolated fresh context |
| Memory across turns | Yes | No — every invocation starts blank |
| Invoked by | User / auto-trigger | Task tool (usually by CM) |
| Best fit | Orchestration, sustained workflows | Specialised one-shot, parallelisable work |

The Campaign Manager needs sustained state across turns, so it's a skill; the specialists do one-shot work invoked by it, so they're subagents.

## Archive

`_archive/` holds superseded agents — the five split Copywriters and the Social/Community Manager, all collapsed into the single **Producer** in the 2026 refactor. Kept for reference only.
