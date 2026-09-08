# Campaign Report — Spec (v1)

**Spec version**: v1 · 2026-06-15.

The **Campaign Report** is the **results readout** produced when a campaign closes — *did it hit its KPIs, what drove the result, what we'd do differently*. It is the evidence-and-outcomes counterpart to the [Retro](retro.md): the **report** says *what happened* (outcomes, from the data); the **retro** captures *what we learned* (internal lessons) and graduates learnings to the tenant layer. **Every campaign produces a report at close**, and **a campaign cannot be marked Closed without one** (enforced — see §Enforcement).

**Produced by**: the **`marketing-forensic-analyst`** agent (read-only data investigator) from the campaign's performance data. The analyst returns a standalone HTML report (matplotlib viz, brand palette) + an evidence-tagged findings brief; CM captures the headline readout as the markdown. The analyst **never invents numbers** — a missing metric is flagged, not fabricated.

**Stored**: `campaigns/<slug>/report/<YYYY-MM-DD>-results.md` (markdown authoritative — the readout) + the analyst's `<...>-analysis.html` (the deep evidence + charts) in the same `report/` folder.

**When**: at campaign close — one-off campaigns at the end of Phase 5/6; cadenced campaigns at quarterly milestones (and at final close). It **feeds the campaign-end retro** (its §2 "what worked") and the **graduation pass** (winning assets → `tenant/library/` · a strong result → a case study).

---

## Schema

```markdown
# Campaign Report — <Campaign Name> — <YYYY-MM-DD>

**Period**: <start> → <end>     **Full analysis**: [analyst report](<...>-analysis.html)     **Status**: Draft / ✅ Approved

## §0 Did we hit the goals? (the headline)

| KPI | Target | Result | Hit? |
|---|---|---|---|
| <KPI floor 1> | <target> | <actual> | ✅ / ⚠️ / ❌ |
| ... | | | |

**Verdict** (one line, binary — hit / partial / missed): <plus the single most important number of the campaign>.

## §1 What drove the result

The funnel's biggest leak + per-channel efficiency (cost-per-signup / cost-per-reply / etc.). Every material claim **evidence-tagged** — FINDING (defensible) / HYPOTHESIS (directional, small-n or confounded) / MYTH-CHECK (an assumption the data does NOT support).

## §2 What worked / what didn't (from the data)

Short, evidence-led. This feeds the retro's §2 (worked) + §3 (didn't).

## §3 Recommendations

Split **do-now** (act on it) vs **test-before-believing** (directional, verify first) — the analyst's own split.

## §4 Full analysis

→ the analyst's standalone HTML report (the deep evidence, funnel charts, demographic fit). The markdown above is the readout; the HTML is the proof.
```

---

## Drafting discipline

- **Outcomes, not lessons.** The report is the *what-happened* readout; the retro is the *what-we-learned*. Don't merge them — the report **feeds** the retro.
- **§0 is binary.** Hit / partial / missed per KPI — no hedging in the headline.
- **Evidence-tag everything material** (FINDING / HYPOTHESIS / MYTH-CHECK). A HYPOTHESIS must never masquerade as a FINDING.
- **No invented numbers.** Missing metric → flag it + say what data would settle it.
- **Length**: 1 page of markdown readout; the depth lives in the analyst HTML.

---

## Enforcement (this report is mandatory at close)

- **CM wrap gate** (`campaign-manager/SKILL.md` §Campaign close): the close sequence is **(1) results report → (2) campaign-end retro (fed by it) → (3) graduation → (4) `closed: true` + freeze**. CM must NOT set `closed` / Status → Closed without the report + retro present.
- **check-state Layer H** (`.claude/skills/check-state/check.py`): a campaign with `closed: true` (or a Closed dashboard status) and no `report/<*>-results.*` is **drift** — surfaced by `python .claude/skills/check-state/check.py --campaign <slug>`.

---

## Cross-references

- **Retro spec**: `docs/specs/retro.md` — the lessons artifact this report feeds
- **Forensic-analyst agent**: `.claude/agents/marketing-forensic-analyst/AGENT.md` — produces the analysis
- **Workflow**: `docs/workflow.md` §The three layers — the report's winning-asset findings graduate to the tenant library
- **Phase 6 spec**: `docs/specs/phase-6-cadence.md` — the close steps live in the cadence runbook's final cycle
