---
name: slop-lint
description: >-
  Catch writing that reads as machine-written, by counting rather than judging. Use when
  reviewing any document or set of documents for AI texture — repeated constructions, sentences
  that never change length, abstractions where instructions belong. Run it before saying a draft
  is clean. Triggers: "does this sound AI", "check for AI tells", "sub-edit this", "review this
  document set".
---

# Slop lint — the deterministic half of an anti-AI-slop review

## Why this exists

A fifteen-document library shipped after passing two review gates. A copy sub-edit ran as a
labelled pass and reported clean. A separate brand reviewer scored tone 5/5 and vocabulary 5/5
across twelve of the documents. Then a human read it and said, in the first sentence: *it sounds
very AI.*

Both gates were wrong, and neither was careless. They were structurally unable to see the fault.

**A checklist can't see it.** Rules are strong on *enumerable* things — banned words, em-dashes,
named patterns. The fault was none of those. It was a **statistical property of a body of text**:
one rhetorical construction used 95 times, roughly 18% of sentences the same short shape,
sentence length that barely varied. Every individual line was good. The tell was that they were
all the *same shape*. Human prose changes gear; this didn't.

**A human reading one document at a time can't see it either.** "Rather than" five times in one
paragraph is invisible while you're reading that paragraph, and obvious the moment you count
across fifteen files. The vantage point matters more than the attention.

**And an AI grading AI prose is close to blind here.** "Does this read as machine-written" is
very hard to answer from the inside, because the reviewer's own generative distribution is the
thing being detected. This is not fixable with a better prompt. It needs a check that **counts**.

That's what this is. It counts; it never judges. Every finding is a number against a threshold,
with the worst offenders named by file and line. Whether a flagged rhythm is a deliberate device
is a human call — exempt it and it stops counting.

## There is ONE script, and it lives in content-subedit

```
.claude/skills/content-subedit/slop_lint.py
```

**This skill deliberately does not carry its own copy.** Two copies of one contract drift, and one
of them silently becomes wrong — the failure behind SYS-149, SYS-151 and SYS-152 in a single week.
`content-subedit` owns the script because the script is its deterministic half; this skill is the
front door for pointing it at documents that never go near a campaign: a spec, a guide, a report,
a set of resources.

## Run it

```bash
python .claude/skills/content-subedit/slop_lint.py <file-or-folder> [...] [--tenant <slug>] [--json]
```

`--tenant <slug>` loads `tenant-brand/<slug>-slop.yaml` for per-voice thresholds and exemptions.

**Pass the whole set when there is one.** A folder, or several files at once. Per-document review
is exactly the vantage point that cannot see this fault, so the corpus report is the point rather
than a convenience. Reads `.md`, `.html`, `.txt`. Code blocks, `<details>` blocks and YAML
front-matter are excluded — they aren't prose and would skew the statistics.

Exit 0 = within thresholds, 1 = at least one check over.

## What it counts

| Check | What it catches |
|---|---|
| **Construction repetition** | One phrase used over and over — "rather than", "X, not Y", "it's not … it's", "the point is". Rate per 1000 words, **plus** a hard flag on clustering: several inside a handful of consecutive sentences, which reads far worse than the raw rate. |
| **Sentence-length uniformity** | Standard deviation of sentence length. The single most reliable machine signature, and trivially measurable. Human prose changes gear. |
| **Aphorism density** | The "X is the win / the whole thing / the hard part" frame, and "the most/only/single biggest". |
| **Abstraction as the actor** | Sentences opening on an abstraction or a gerund instead of a person or a named thing — "The noise goes up, the bodies come down". |
| **Opener repetition** | Consecutive sentences starting the same way. |

## Reading the output

```
FLAG guide.md: 2 texture finding(s) (2113 words, 170 sentences)
     [construction repetition] "rather than" x12 = 5.7/1000 words  (over: cap 2.0/1000)
        L44: Say what to do rather than what to stop.
```

Every finding gives you the count, the rate, the threshold it crossed, and up to four real lines
to look at. Go and read those lines. The linter has no opinion about whether they're bad — it
only knows there are a lot of them.

## The one rule that matters

**When it flags, fix the text. Do not raise the threshold.**

The thresholds are calibrated to *separate* a known-bad body of text from a known-good one. Move
them to get green and you destroy the only property that makes the check worth running. A gate
that fires on good prose gets ignored exactly like one that never fires.

If a flagged rhythm is a genuine brand device, exempt it *deliberately*, per tenant:

```yaml
# tenant-brand/<slug>-slop.yaml
thresholds:
  phrase_rate_per_1k: 2.5      # a punchy consumer voice legitimately repeats more
exempt_phrases:
  - "rather than"              # named device, deliberate
```

Different voices have different legitimate profiles. A plain instructional voice and a punchy
consumer voice will not measure the same, and that's fine — but decide it once, in the file,
rather than waving through a flag each time.

## Calibration, so you can judge the numbers

Defaults were set against a real before/after pair:

- **known-bad**: one construction at 3.4 per 1000 words across the corpus, worst page 7.8 per
  1000, five instances in five consecutive sentences
- **known-good**, after a plain-language rewrite: the same construction at 1.2 per 1000

A cap of 1.0 flags the *corrected* text. 2.0 sits between 1.8 and 3.4 with room on both sides.

Two floors stop it talking nonsense about short documents: a **rate** needs at least 400 words
*and* 3 hits before it's allowed to speak, and the ratio checks need at least 15 sentences. In a
four-sentence document one hit is 25% and means nothing.

## What it does NOT do

It doesn't check facts, structure, argument or whether the writing is any good. It catches one
specific failure — text that has the texture of having been generated — and nothing else. Pair it
with a human read, and with the word-level pass below.

## The companion pass — things a human or an LLM should check, that this script can't

Run these as a **literal** pass, not a vibe read. Search for each item explicitly. In practice
banned words slip through repeatedly when someone skims and trusts their sense that it "reads
clean" — short common words are exactly the ones a vibe read glides over.

**Em-dashes.** Search for the — character. Replace with a comma where the sentence breathes.
Keep one only where a comma would create genuine ambiguity, and say why you kept it.

**Banned words** — scan for each, one at a time: showcase, leverage, transformative, ecosystem,
holistic, seamless, robust, pivotal, underscore, genuinely, honestly, navigate (metaphorical),
unlock, synergy, realm, foster, garner, multifaceted, curate.

**Punchy pairs.** A sentence, then a very short one (under 8 words) that reframes or concludes
it. Read the pair aloud — does the second exist only to land the first? Then cut it.

**Restatements.** Read each sentence against the one before. Could you delete the second without
losing anything the first didn't already say?

**Recap closings.** Does the last paragraph restate the argument? If you could move it to the top
as an introduction, it's a recap — cut it.

**Metaphor where instruction belongs.** "Bringing a room down only holds if there's somewhere for
it to land" has to be decoded before it can be used. If a sentence's job is to tell someone what
to do, it should tell them what to do.

**Unverified numbers.** For every figure, check there's a named, verifiable source, and that the
number is actually in that source. Flag anything hung on a source that may not contain it. Never
pass an unverifiable number through.

## Where it is already wired in

- **`content-subedit`** runs it as a MANDATORY pass on every copy asset and quotes its numbers. A
  sub-edit report without the linter output attached is not a clean sub-edit.
- **Brand Manager** may not assert a tone score without citing it; a score/linter contradiction
  must surface rather than resolve silently in the LLM's favour.
- **The smoke test** runs `test_slop_lint.py` at Layer 1, so a regression in the thresholds'
  ability to separate good from bad goes RED before it reaches an asset.

So do NOT invoke this on campaign copy going through the Producer — that already runs it, and
calling it again just repeats the same numbers.

A portable, self-contained copy (no repo paths, no client names) lives outside the system for use
on machines that do not have it.
