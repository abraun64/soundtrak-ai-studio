---
name: cost-ledger
description: Per-dispatch AI cost ledger. CM appends one entry per subagent return (metered tokens from the usage report); dashboard AI-cost totals render from the ledger automatically via the COST_TOTAL_AUTO marker so they can never go stale. Also write-yaml to push per-phase aggregates into campaign.yaml. Use whenever a Producer/CD/BM/research dispatch returns, when the operator asks "what has this campaign cost", or to true-up against console billing.
---

# cost-ledger

**The metered answer to "the dashboard totals went stale" (caught twice: 2026-06-04 and 2026-06-09).**

Ledger: `.claude/state/cost-ledger.jsonl` — append-only, one JSON line per dispatch.
Each entry: `{ts, campaign, phase, asset, agent, tokens, cost_usd, basis, note}`.
`basis` is the honesty bit: `metered` (real usage report) vs `estimate` (judgment call) — reported separately, never silently blended.

## The CM rule (non-negotiable)

**Every subagent return that reports usage gets a ledger entry in the SAME turn.** The
usage block on a task notification (`subagent_tokens: N`) evaporates when the session
ends — if it isn't written down at return time, it's gone and the totals rot again.

```bash
python .claude/skills/cost-ledger/ledger.py add \
  --campaign <slug> --asset <NN> --agent producer \
  --tokens <subagent_tokens> --note "<what it built> (metered <date>)"
```

Main-loop work without a usage report → `--basis estimate` entries at natural
checkpoints (asset shipped, stage closed). Don't let unmetered work silently vanish;
don't dress estimates up as metered.

## Dashboard auto-render

Campaign dashboards carry `<!-- COST_TOTAL_AUTO -->` where the old hand-maintained
total line used to be. At every render, `operator_actions.py` replaces it with the
ledger aggregate (metered + estimated split, entry count, file pointer). No manual
upkeep; cannot go stale.

**Per-phase cells: `<!-- PHASE_COST:N -->`** (added 2026-07-08). Drop this marker in
the AI-cost column of the phases table and the render fills it live from the ledger's
phase-N total (metered / est. split shown when mixed). Use it instead of a hand-typed
number or "metered per asset" — the same anti-stale guarantee as the total row, per
phase. **This only works if dispatches carry their TRUE phase**: tag strategy subagents
with the phase they serve (`--phase 1` Insights · `--phase 2` CD trio · `--phase 3`
Plan/influencer research), NOT the `add` default of `4`. Mis-tagging lumps strategy
spend into Phase 4 and the per-phase cells lie (the 2026-07-08 buildlog retro fix).

## Commands

```bash
# Append (CM, same turn as the dispatch return)
python .claude/skills/cost-ledger/ledger.py add --campaign <slug> --asset 23 --agent producer --tokens 130659 --note "..."

# Report — metered vs estimate, per phase, per asset
python .claude/skills/cost-ledger/ledger.py report --campaign <slug>
python .claude/skills/cost-ledger/ledger.py report            # all campaigns

# Push per-phase aggregates into campaign.yaml ai_cost fields (then re-render dashboard)
python .claude/skills/cost-ledger/ledger.py write-yaml --campaign <slug>
```

## Rates

Blended $/Mtok, default **6.0** — derived from the one fully-metered baseline
(Soundtrak strategy phases: 710k tok = $4.30 ≈ $6.06/M). Override with `--rate`
or pass `--cost` explicitly when you have a real dollar figure (console billing).
True-up: when console billing diverges, add a correcting entry with
`--note "console true-up <period>"` rather than editing history — the ledger is
append-only.

## Known limitations (honest)

- Main-loop (non-subagent) tokens have no automatic usage report — they enter as
  estimates. The metered/estimate split in every report keeps this visible.
- Operator time is NOT ledgered (tracked per-phase in campaign.yaml human_time).
- Historical entries before 2026-06-09 were backfilled: strategy phases from
  yaml-metered numbers, production 2026-06-02→06-08 as one flagged estimate.
