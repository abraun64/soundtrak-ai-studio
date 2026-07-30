---
name: content-subedit
description: |
  The authoritative copy-clean sub-edit gate for the Marketing AI System. Applies the
  five voice rules (em-dashes, banned words, punchy-fragment patterns, restatements,
  recap-closing) to any written copy — LinkedIn post, Substack article, email, web,
  ad, microcopy — flags every violation, fixes it, and reports counts per rule.
  MANDATORY: the Producer runs this as a distinct, labelled pass on EVERY copy asset
  it writes, after its own draft + internal sub-edit, before it surfaces the asset.
  Also invokable on demand: "sub-edit this", "check against the voice rules", "run the
  sub-edit", "clean this up", "check for AI tells".
---

# Content Sub-Edit Skill

This skill is the system's authoritative **copy-clean gate**. It applies five voice rules to
a piece of copy, flags every violation, fixes them, and reports what changed. It is deliberately
**deterministic** (Rule 1 is a literal `—` search; Rule 2 a fixed banned-list scan) so it cannot
rationalise past its own rules the way a vague self-QA can. Run it as a **separate, labelled pass** —
never fold it into the drafting step.

**Refuse-to-surface**: if after 3 fix-and-rerun cycles the copy still has un-cleared violations, do
NOT ship it. Return the violation list + the least-bad version and flag the blocker (per
[`craft/sub-edit-pipeline.md`](../../../craft/sub-edit-pipeline.md) refuse-to-surface rule).

---

## Step 1 — Load the rules

Read **both**, in this order, before checking any content:

1. **Tenant voice — AUTHORITATIVE** — the active tenant's Brand Context §2 Voice at
   `tenant-brand/<tenant>.md` (e.g. `tenant-brand/soundtrak.md`). This is the definitive,
   live voice guide. The invoker names the tenant; if none is named, infer it from the asset
   path / Per-Step Brief.
2. **Operational checklist — the universal baseline** — `references/voice-rules.md` from this
   skill's directory: the five structured rules.

### Precedence — the tenant Brand Context WINS (read carefully)

The five rules are a **floor**, not an absolute. Where the tenant Brand Context **explicitly
permits or names** something this skill's baseline would flag, **the tenant rule wins — do NOT
"fix" a deliberate, named device.** The brand built that on purpose; stripping it is the failure.

Concretely:
- **Named voice devices override the rule.** If §2 names a rhythm device (e.g. Soundtrak's
  "short four-word declarative transitions" — *"That's the Trailer. This is the Playbook."* — or
  "a short sentence is the signal"), then **Rule 3 (punchy pairs / staccato) does NOT apply to that
  device.** Leave it. This is the single most likely contradiction — respect it.
- **Carve-outs override the ban.** A word the baseline bans but §2 explicitly carves out (e.g.
  `leverage` in the mechanical-noun sense; `world-class` in client-goal framing) is **allowed** in
  exactly the carved-out use.
- **HARD RULES tighten, and win.** Where §2 sets a stricter line than the baseline, apply the
  stricter line. (Soundtrak's em-dash rule is calibrated to **near-zero** — default every em-dash
  to a comma, keep only a rare load-bearing one, flagged with its reason.)

The direction of resolution: tenant **tightens** freely (ban more), and tenant **loosens only via an
explicit, named exception** in §2 (never a silent un-ban of generic AI slop). If you're unsure
whether a pattern is a deliberate named device or accidental AI slop, **flag it for review — don't
auto-fix.** Record every such call in the report (see Step 5) as "tenant-permitted — left as-is".

*(Legacy fallback: if a `Soundtrak_Voice*.md` is supplied in an `uploads/` folder, read it too — but the in-repo Brand Context is authoritative when they disagree.)*

---

## Step 2 — Get the content

**Producer-inline (the mandatory case):** the content is the draft the Producer just wrote
(and ran its own L1/L2/L3 self-edit on). Work with the text directly. Do not re-draft — sub-edit.

**On demand:** the operator pastes content or gives a path. For a `.docx`, extract with python-docx:

```python
from docx import Document
doc = Document('/path/to/file.docx')
text = '\n'.join([p.text for p in doc.paragraphs])
print(text)
```

Work from the extracted text.

---

## Step 3 — Run all rules

Work through each rule in order (Rules 1–7 in `references/voice-rules.md`). For every candidate hit:
1. **Tenant-precedence check first** — is this an explicitly permitted / named device or carve-out in the tenant §2 (per Step 1 precedence)? If yes → **not a violation.** Leave it; log it as "tenant-permitted — left as-is."
2. Otherwise it's a violation: quote the offending text, state the fix applied.

For every rule, state the rule name and either the violations + fixes or "✓ No violations."

Do not skip any rule. Do not group rules together. **Never strip a deliberate, named brand device to satisfy a baseline rule** — when genuinely unsure whether something is a named device or AI slop, flag for review rather than auto-fix.

---

## Step 4 — Apply all fixes

Rewrite the content with every fix applied. When fixing punchy pairs (Rule 3),
absorb the contrast into the surrounding sentence rather than just deleting it.
The argument should still land — just without the mechanical two-sentence pattern.

Then **re-scan** the fixed draft (Step 3 again). Max **3 fix-and-rerun cycles**. If clean → report.
If still un-clean after 3 → **refuse to surface** (return the blocker, do not ship).

---

## Step 5 — Report and return

Present the corrected content with a summary of changes. Format:

```
RULE 1 — EM-DASHES: [N] violations fixed
RULE 2 — BANNED WORDS: [N] violations fixed — [list the words]
RULE 3 — PUNCHY PAIRS: [N] violations fixed
RULE 4 — RESTATEMENTS: [N] violations fixed
RULE 5 — RECAP CLOSING: [fixed / no violation]
RULE 6 — HOLLOW CONTRAST (many-say-few-do + significance kicker): [N] violations fixed
RULE 7 — UNVERIFIED / MIS-ATTRIBUTED STATISTIC: [N] flagged — [list each number + its missing/unverified source]
TENANT-PERMITTED (left as-is): [N] — [list each named device / carve-out respected, e.g. "four-word declarative (§2 #9)"]

[Corrected content]
```

**Producer-inline (the mandatory case):** return the corrected copy + the per-rule report to the
Producer. The Producer writes the cleaned copy into the asset and records this report block in the
asset's **§7 Sub-edit report** (it is part of the reviewable surface Brand Manager reads). Do NOT
write docx files or regenerate any Python script from here — the Producer owns the asset write.

**On demand:** save the corrected content back to the given path if one was provided, and report
where it was saved. Otherwise just return the corrected content + report in chat.

---

## Integration with the Producer (mandatory gate)

The Producer engages this skill on **every copy asset it writes**. Sequence inside the Producer's
production step:

1. Draft the copy
2. Run the Producer's own internal L1/L2/L3 sub-edit (first pass)
3. **Run THIS skill as the authoritative copy-clean gate** (distinct, labelled pass)
4. Fix all violations; re-scan up to 3 cycles
5. If clean → write the cleaned copy into the asset + record the §7 report; if not → refuse to surface
6. Repeat per copy deliverable (e.g. LinkedIn post, then the Substack article)

The gate runs **before** the asset is surfaced to CM / the operator — clean is the only shippable state.

---

## Quick reference — most common violations

**Em-dashes:** Search for the — character (U+2014). Default: replace every one with a comma where the
sentence breathes, or a spaced hyphen ( - ) per the tenant's beat convention. **Near-zero, not zero** —
keep an em-dash only where a comma would create genuine ambiguity or the pause is load-bearing, and
flag each keep with its reason.

**Banned words to scan for first:** showcase, leverage, transformative, ecosystem,
holistic, seamless, robust, pivotal, underscore, genuinely, honestly, navigate
(metaphorical), unlock, synergy, realm, foster, garner, multifaceted, curate.
**Plus** every word in the active tenant's §2 banned list (load it — it extends this baseline).

**This is a LITERAL find-check, not a vibe check (reinforced 2026-07-15).** Run an explicit, deterministic pass over the *exact* word list — search the copy for each banned word in turn, one at a time. Do not skim the text and trust your sense that it "reads clean." "genuinely" slipped into the Ed 19 draft **twice** and Ed 20 once despite this rule already existing, precisely because the pass was done by feel. Scan the literal strings every pass, including short common words like "genuinely" and "quietly" that a vibe read glides over.

**Punchy pairs to find:**
- Any sentence ending in a period followed by a very short sentence (under 8 words)
  that reframes or concludes the first. Read the pair out loud — does the second
  sentence exist only to land the first? If yes, it's a violation.

**Restatements:**
- Read each sentence against the one before it. Could you delete the second without
  losing meaning not already in the first?

**Recap closing:**
- Read the last paragraph. Does it restate the article's main argument?
  If you could place it at the top as an introduction, it's a recap — cut it.

**Unverified / mis-attributed statistics (Rule 7):**
- For every number in the copy, check there is a named, verifiable source (who, what report, what year) and that the number was confirmed present in the actual primary source. Flag any figure with a missing source, or one hung on a source that may not contain it (Ed 20's fabricated "44%" / "9%" mis-attributed to a McKinsey report). The sub-edit flags for verification — it never passes an unverifiable number through.
