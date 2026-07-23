---
name: review-ready
description: >-
  The MANDATORY "is this ready for a human to review?" gate the Campaign Manager runs on
  every operator surface BEFORE surfacing it for approval — Brief, Insight Brief, Concept,
  Plan, campaign dashboard, and each asset preview. Checks the surface reads for a marketer
  who did NOT write it, with no internal jargon. Two layers: a deterministic jargon lint
  (jargon_lint.py) + an LLM "cold-reader" pass. Auto-applies the safe rewrites, surfaces the
  judgment calls. Sibling to content-subedit (which does published-COPY voice; this does
  operator-SURFACE readability). Invoke before any "surface for review" step, or on demand:
  "is this review-ready?", "run the readability gate", "check this reads for a non-author".
---

# review-ready — the operator-surface readability gate (SYS-087)

Operator surfaces were being written for the AUTHOR, not the human-in-the-loop REVIEWER
("the +100 floor engine", "§2", "clean-room", "Wave 2 · gate-cleared"). This gate makes a
surface prove it reads for the reviewer **before** the CM surfaces it for approval.

## The contract — two rules

1. **Assume the reader is a MARKETER but NOT the author** — nothing may rely on context only
   the author holds ("the +100 floor engine" means nothing to a fresh reader).
2. **No jargon unless it is marketing-industry-accepted.** Accepted: KPI · CTA · positioning ·
   single-minded proposition · top-of-funnel · mental availability · funnel · awareness ·
   CPA/CTR. Flagged (internal): §N cross-refs · clean-room · grill-me · graduate-then-cite ·
   raw-voice · Wave N · gate-cleared · foundation-shaped · CM-inferred · TBD-as-status · SDT ·
   moral-disgust. (Full list in `jargon_lint.py`.)

## When it runs — MANDATORY (decided by the operator, 2026-07-15)

The CM runs this on EVERY operator surface **immediately before surfacing it for review** —
same non-negotiable shape as content-subedit on copy assets. Surfaces in scope: Brief ·
Insight Brief · Concept (trio + selected) · Plan · campaign dashboard · each asset preview ·
**Phase-5 launch rollout · Phase-6 cadence runbook** (SYS-118 — a non-technical operator, or a
delegated teammate, must be able to run a launch or a cadence from the surface alone).
Not advisory: a surface that fails the gate is not surfaced until it's fixed.

**The standard (SYS-118): plain prose, technical detail in collapsibles only.** The MAIN PROSE
must read for a non-technical human — no code identifiers (`hero_scrub.py`, exit codes,
slash-command internals), no internal jargon (dogfood, multi-tenant, content-subedit, UTM,
au-sender-id, nav-crop), no unexplained acronyms. The execution "how" belongs in the clearly
marked collapsible `<details>` blocks and code spans, for whoever runs it — NEVER the lead prose.
The lint enforces exactly this: it skips `<details>` blocks and code (fenced ``` + inline `spans`),
so it flags jargon **only** in the plain prose a reader acts on. This EXTENDS the plain-language
rule (docs/specs/plan.md "Name + Description") from asset names to the full operator prose.

## The two layers

**Layer 1 — jargon lint (deterministic, fast):**
```
python .claude/skills/review-ready/jargon_lint.py <surface.md|.html>
```
Flags every internal-jargon hit with its line + a suggested plain rewrite. Exit 1 if any
found (so it can gate a script). This catches the KNOWN jargon cheaply.

**Layer 2 — cold-reader pass (LLM, catches what a denylist can't):**
Read the surface **as a marketer who did NOT write it**. For every sentence you cannot fully
follow without the author's head, flag it and write a plain-English rewrite. This catches
author-context opacity the lint misses — e.g. "the build diary is the proof-shape this burned
audience trusts", "borrowed-audience swaps time-gated on relationships". Prompt yourself with:
*"Would a competent marketer who just walked in understand this sentence? If not, rewrite it."*

## The flow (mirrors content-subedit)

1. Run Layer 1 (lint) + Layer 2 (cold-reader) on the surface.
2. **Auto-apply the safe rewrites** — jargon→plain and opaque→clear where the meaning is
   unambiguous (same as content-subedit auto-fixing voice violations).
3. **Surface the judgment calls** — where the fix would change meaning, or a term might be
   deliberate, list them for the operator rather than guessing.
4. Record a one-line report ("review-ready: N jargon fixed, M cold-reader rewrites, K flagged").
5. Only then surface the artifact for approval.

## Extending it

`jargon_lint.py` DENYLIST is a curated, growing corpus — add a `(regex, label, rewrite)` row
whenever new internal jargon is caught in a review. The ALLOWLIST documents the
marketing-accepted bar (single-minded proposition IN; mental availability / 95:5 IN;
SDT / moral-disgust / loss-aversion OUT — flag + gloss).

## Boundaries

- **Not content-subedit.** content-subedit does published-COPY voice (em-dashes, banned words,
  AI-tells) for the reader of the asset. This does operator-SURFACE readability for the
  reviewer of the artifact. Different audience, different corpus. Both are mandatory pre-surface
  passes.
- **Not cm-audit.** cm-audit checks surfaces are present + current (structural). This checks
  they're readable (content). Complementary.
