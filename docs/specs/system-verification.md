# Verifying a system change — what "done" actually means (SYS-138)

**Status:** **AGREED AND LIVE — 2026-08-22.** Part 1 (this definition) was signed off by the
operator; Part 2 (the runner, the `verified:` field and the close rule) shipped the same day.
The three decisions are recorded at the bottom.

---

## Why this exists

Two failures, six weeks apart, have the same shape.

- **2026-08-08 — the onboarding build.** Its "UAT" checked that the expected files existed.
  They did. It had to be upgraded to actually *running* the seed build, the doctor and the
  surface renders before anyone knew whether the thing worked.
- **2026-08-22 — the freshness gate.** `surface_freshness.py --check` printed *"every surface
  is at least as new as its data"* while seven rendered surfaces sat up to four days behind
  their markdown. The check ran. It passed. It proved nothing, because it was never pointed at
  the surfaces that had gone stale.

Both are the same error: **confusing "the check ran and was green" with "the operator gets the
right outcome."** This doc defines the difference, and how deep to go on any given change.

---

## (a) What UAT means for this system

UAT is **User Acceptance** testing, and the user is the **operator** — the person who opens the
dashboard and decides whether an asset ships. Not the developer, not the agent that made the
change. So acceptance asks one question:

> **From a cold start, does the operator get the outcome they asked for, by doing what they'd
> actually do?**

Three consequences follow, and they are the whole discipline:

1. **Run the real thing.** Invoke the actual command, skill or hook, against real (or
   realistically shaped) data. Do not inspect the artifacts it *would have* produced.
2. **Assert the outcome, not the mechanism.** *"The dashboard shows the asset as Approved"* —
   not *"render.py exited 0"*. The operator never sees the exit code.
3. **Prove the check can fail.** A green assertion that cannot go red is not evidence. Every new
   assertion is run once against the broken state it is supposed to catch, and observed to fail.

**These are NOT UAT**, however convenient they are: a file exists · a script parses · a diff
looks right · an agent reports success · the same code that made the change also validated it.

---

## (b) The four levels, and how to pick one

<div>
<svg viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" role="img"
     aria-label="Decision flow for choosing a verification level" style="max-width:100%;height:auto">
  <style>
    .bx { fill:#faf9f5; stroke:#111110; stroke-width:1.5 }
    .hit { fill:#e63c3c; stroke:#111110; stroke-width:1.5 }
    .t  { font:13px/1.3 Inter,system-ui,sans-serif; fill:#111110 }
    .tb { font:600 13px/1.3 Inter,system-ui,sans-serif; fill:#111110 }
    .tw { font:600 13px/1.3 Inter,system-ui,sans-serif; fill:#faf9f5 }
    .ar { stroke:#111110; stroke-width:1.5; fill:none; marker-end:url(#a) }
  </style>
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"
    orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#111110"/></marker></defs>

  <rect class="bx" x="8" y="14" width="196" height="46" rx="4"/>
  <text class="tb" x="20" y="34">A system change</text>
  <text class="t"  x="20" y="51">…is about to be called done</text>

  <rect class="bx" x="8" y="86" width="196" height="42" rx="4"/>
  <text class="t" x="20" y="104">Prose, comment or doc link</text>
  <text class="t" x="20" y="120">only?</text>
  <rect class="bx" x="8" y="150" width="196" height="42" rx="4"/>
  <text class="t" x="20" y="168">Touches shared code —</text>
  <text class="t" x="20" y="184">render, hooks, lib, the seed?</text>
  <rect class="bx" x="8" y="214" width="196" height="42" rx="4"/>
  <text class="t" x="20" y="232">Changes what a surface says,</text>
  <text class="t" x="20" y="248">or writes data by hand?</text>

  <rect class="bx" x="286" y="86" width="150" height="42" rx="4"/>
  <text class="tb" x="298" y="112">L0 · Sanity</text>
  <rect class="bx" x="286" y="150" width="150" height="42" rx="4"/>
  <text class="tb" x="298" y="176">L1 · Smoke</text>
  <rect class="hit" x="286" y="214" width="150" height="42" rx="4"/>
  <text class="tw" x="298" y="240">L2 · Behavioural UAT</text>

  <path class="ar" d="M204 107 H286"/>
  <path class="ar" d="M204 171 H286"/>
  <path class="ar" d="M204 235 H286"/>
  <path class="ar" d="M106 60 V86"/>
  <path class="ar" d="M106 128 V150"/>
  <path class="ar" d="M106 192 V214"/>

  <rect class="hit" x="514" y="150" width="228" height="106" rx="4"/>
  <text class="tw" x="528" y="176">L3 · Unit — add on top</text>
  <text class="tw" x="528" y="198" style="font-weight:400">Logic with real cases, or a bug</text>
  <text class="tw" x="528" y="216" style="font-weight:400">of this class that already shipped</text>
  <text class="tw" x="528" y="234" style="font-weight:400">once. Must reproduce the</text>
  <text class="tw" x="528" y="252" style="font-weight:400">historical failure.</text>
  <path class="ar" d="M436 203 H514"/>

  <text class="t" x="514" y="52">Take the HIGHEST level any</text>
  <text class="t" x="514" y="70">criterion below reaches —</text>
  <text class="t" x="514" y="88">never the cheapest that applies.</text>
  <text class="t" x="514" y="112">Levels stack: L2 includes L1, L1 includes L0.</text>
</svg>
</div>

| Level | What it proves | Cost |
|---|---|---|
| **L0 · Sanity** | the change is loaded and parses | seconds |
| **L1 · Smoke** | the system still runs end to end | ~1 min |
| **L2 · Behavioural UAT** | the operator's actual outcome, on the real surface | 5–20 min |
| **L3 · Unit** | one piece of logic, at its boundaries, repeatably | 10–30 min to write, seconds to run forever after |

**Trigger criteria — take the highest level any of these reaches:**

| If the change… | Minimum level |
|---|---|
| is prose, a comment, or a doc link, and nothing executes it | **L0** |
| touches shared code — `render-html/`, `.claude/hooks/`, `.claude/lib/`, a skill entry point | **L1** |
| goes into the **seed** (a stranger runs it on a machine you can't see) | **L1**, plus the doctor + leak gate |
| changes **what an operator surface says** — dashboard, gallery, tasks, index, tenant home, an asset record | **L2** |
| **writes data** the operator can't trivially undo — `backlog.yaml`, asset states, published files | **L2** |
| is a **gate, guard or diagnostic** (something whose job is to catch problems) | **L2** — a guard that cannot be observed failing is not a guard |
| contains **logic with cases** — a parser, a derivation, a threshold, an id allocation, a recursion | **L3** |
| is a **repeat** of a class of bug that has shipped before | **L3**, and the test must reproduce the historical failure |

**Proportionality is the point.** Most changes are L0 or L1. L3 is for logic and for repeats —
unit-testing a prose edit is waste, and this framework should never be used to justify it.

---

## (c) The concrete steps

### L0 · Sanity
1. `python .claude/skills/system-manager/verify.py --level 0 <files>` — parses `.py` via `ast`
   and `.yaml` via `safe_load`. For a skill, confirm the frontmatter parses.
2. Say plainly that L0 was all that ran, and why.

### L1 · Smoke
1. `python .claude/skills/system-manager/verify.py --level 1` (wraps `smoke_test.py`) → must be
   **ALL GREEN**.
2. Seed-bound changes also: `python .claude/skills/system-smoke-test/doctor.py` → READY, and the
   leak gate clean.
3. A pre-existing RED is not a pass. Either fix it, or state it explicitly as a known standing
   failure with its ticket id.

### L2 · Behavioural UAT
1. **Name the outcome first, in the operator's words.** *"Opening the buildlog gallery shows
   Edition 03 with this week's copy."* If you can't write that sentence, you don't yet know
   what you're accepting.
2. **Put the system in the "before" state** — the state a real operator would be in.
3. **Run the real entry point** the operator would use: the skill, the hook, the command. Not a
   reimplementation of it inside the test.
4. **Read the rendered output**, not the source. The `.html` the operator opens, the digest text,
   the console output they'd actually see.
5. **Assert the outcome sentence from step 1.**
6. **Confirm the loud-failure path.** Break the input, re-run, and watch it go red. A guard you
   have only ever seen green is untested.
7. **Record the evidence** — the command, and the line of output that proves it — in the ticket.

### L3 · Unit
Run them all with `python .claude/skills/system-manager/verify.py --level 3`. To add one:
1. Put `test_<module>.py` **beside the module**. Stdlib only (pytest is not installed).
2. Runnable directly; exit 0 = pass, 1 = fail; one printed line per assertion.
3. Every test **names the live failure it guards**, with the date. That is what stops a later
   reader deleting it as noise.
4. **Verify it fails without the fix**: revert the fix, run, observe the failure, restore.
5. **Wire it into the smoke test (Layer 1)** so it runs forever after without anyone remembering.

---

## Worked example — 2026-08-22, the tickets that produced this doc

| Change | Level | Evidence that made it acceptance rather than assertion |
|---|---|---|
| SYS-143 — freshness gate missed doc + asset-record surfaces | **L3 + L2** | Unit: 10 assertions on the enumeration; removing the fix drops the two stale-doc assertions to `got []`. Behavioural: ran `--heal` on live data (9 rebuilt), then ran **both** sensors and watched them agree at 0 — their disagreement was the bug. |
| SYS-136 — `operator_actions` mutual recursion hung a render | **L3 + L2** | Unit: asserts nesting depth ≤ 2; without the guard it measures **196**. Behavioural: the gamma dashboard render went from **>120 s (killed at the hook's 60 s budget)** to **1.3 s**. |
| SYS-141 — weekly-digest escalation defects | **L3 + L2** | Unit: without the fix, the backlog test reproduces the historical `['SYS-140','SYS-141','SYS-141']` id collision exactly. Behavioural: ran the real digest; its new recovery section immediately named SYS-141 and SYS-142 as close candidates. |
| SYS-138 Part 2 — the runner, the `verified:` field, the close rule | **L2 + L3** | Unit: `verify.py --audit` asserted against synthetic backlogs. Behavioural: ran `--level 3` (6 suites), then `--audit` on the live board, which immediately named the four tickets closed that day with nothing recorded — the report earning its place on its first run. |
| This document | **L0** | Prose. Nothing executes it. Parsed, linked, rendered — that is the whole appropriate cost. |

---

## Part 2 — what shipped (2026-08-22)

- **`verify.py`** — the level runner, in the System Manager skill.
  `--criteria` prints the table above plus the L2 checklist · `--level 0 <files>` sanity ·
  `--level 1` smoke · `--level 3` runs every `test_*.py` suite in the repo (the glob IS the
  registry — a new suite needs no wiring) · `--audit` lists closures that recorded nothing.
  **L2 is deliberately absent from the runner.** A script standing in for "run the real thing
  and read the rendered result" would be the file-existence UAT all over again.
- **`verified:` on the backlog schema** — `"L<n> — <what was run> — <the line that proved it>"`,
  rendered on the dashboard card.
- **The close rule** — in the System Manager skill's Verify job, below.
- **The nudge** — the weekly digest runs `--audit` as a diagnostic. It reports; it never
  escalates to a ticket (a P1 about unverified tickets would be circular, and board noise).

## The three decisions (operator, 2026-08-22)

1. **Record the level on the ticket — yes.** A `verified:` field on the backlog item, rendered
   on the dashboard card. *Why:* the board is where the operator decides; a commit message is
   not a surface, so "done" and "claimed done" would stay indistinguishable where it matters.
2. **L2 is a must-RECORD, not a must-PASS.** A ticket may not close with an empty `verified:`,
   but it MAY record a level lower than the table asks **with the reason stated in the same
   field**. *Why:* a hard must-pass gate on an agent-run workflow gets satisfied theatrically —
   that is exactly what produced the 2026-08-08 file-existence "UAT". Forcing an auditable
   claim gets the honesty without creating pressure to manufacture evidence. `--audit` and the
   weekly digest make an unrecorded close visible.
3. **L2 scripts are disposable; only L3 accumulates.** Run it, paste the command and the proving
   line into `verified:`, discard the script. *Why:* L2 checks are pinned to live campaign data,
   so a retained suite of them goes stale and starts throwing false REDs — the same trust
   erosion SYS-141 was about. L3 suites are hermetic (temp dirs, no live data), so those are the
   ones worth keeping, and they already run in the smoke test's Layer 1.

---

**Related:** [surface-freshness.md](surface-freshness.md) · [system-manager.md](system-manager.md) ·
`.claude/skills/system-smoke-test/` (L1) · `.claude/skills/cm-audit/` and
`.claude/skills/check-state/` (diagnostics this framework governs, not replaces).
