#!/usr/bin/env python3
"""SYS-154 — AI-texture lint. The deterministic half of the anti-slop gate.

WHY THIS EXISTS. On 2026-08-28 an operator read a shipped resource library and said it "sounds
very AI". Both existing gates had passed it: content-subedit ran as a labelled pass and reported
clean, and the Brand Manager scored tone 5/5 and vocabulary 5/5 across twelve assets. Neither was
careless. They were structurally unable to see the fault.

  - content-subedit's rules are strong on ENUMERABLE things — banned words, em-dashes, specific
    patterns. The fault was not a word. It was a STATISTICAL PROPERTY of a body of text: one
    rhetorical construction repeated 95 times, ~18% of sentences the same short shape, sentence
    length barely varying. A checklist cannot see that, and neither can a human reading one
    asset at a time — "rather than" five times in one paragraph is invisible while you read that
    paragraph and obvious when you count across fifteen files.
  - An LLM grading LLM prose has a blind spot here that no prompt fixes: the reviewer's own
    generative distribution is the thing being detected. It needs a check that COUNTS.

The system had already solved this pattern twice — jargon_lint.py and brief_lint.py both exist
because LLM self-assessment of a countable property is unreliable. The anti-slop gate was the one
quality gate with no deterministic half. This is that half.

IT COUNTS; IT NEVER JUDGES. Every finding is a number against a threshold, with the worst
offenders named by file and line. Whether a flagged rhythm is a deliberate brand device is a
human call — set `exempt_phrases` for the tenant and it stops counting.

CORPUS MODE IS THE POINT. Pass a directory (or several files) and it reports across the whole
body. Per-asset review is exactly the vantage point that cannot see this fault.

Usage:
  python slop_lint.py <file.md|.html|dir> [...] [--tenant acme] [--quiet] [--json]

Exit 0 = within thresholds; 1 = at least one check over. Same contract as jargon_lint.py.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
import statistics
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))
try:
    import repo_paths
    DATA = repo_paths.data_root(ROOT)
except Exception:  # noqa: BLE001
    DATA = ROOT

TEXT_SUFFIXES = {".md", ".html", ".txt"}

# ---------------------------------------------------------------------------------------------
# Thresholds. Deliberately generous: this gate should fire on TEXTURE, not on a writer having a
# tic. Every one is per-tenant overridable — a punchy consumer voice and a plain instructional
# voice have legitimately different profiles, and a named brand device is not a defect.
# ---------------------------------------------------------------------------------------------
# CALIBRATION (2026-09-08). A threshold must SEPARATE the known-bad from the known-good, or the
# gate is worthless in one direction or the other. Measured against SYS-154's own recorded numbers
# for the Acme Co early-learning library:
#     known-bad  (2026-08-28): "rather than" x95 = 3.4 / 1000 words; worst page 7.8 / 1000
#     known-good (after the plain-language pass): "rather than" x34 = 1.2 / 1000,
#                                                 "X, not Y"   x52 = 1.8 / 1000
# A 1.0 cap flags the CORRECTED library, and a gate that fires on the fixed version teaches
# everyone to ignore it — the same trust loss as one that never fires. 2.0 sits between 1.8 and
# 3.4 with room on both sides. NOTE: the known-bad text itself was never committed (a single
# auto-backup is that campaign's entire git history), so those numbers are the operator's
# measurements rather than a corpus that can be re-run. test_slop_lint.py encodes them as a
# synthetic fixture so the separation stays asserted.
DEFAULTS = {
    # per 1000 words, per phrase
    "phrase_rate_per_1k": 2.0,
    # A RATE is meaningless on a short sample: one "rather than" in a 230-word resource card is
    # 4.3/1000 and means nothing, and most assets in this system are short (a LinkedIn post is
    # ~200 words). So the rate check needs a floor on BOTH the sample and the absolute count
    # before it is allowed to speak. Clustering is unaffected — it is an absolute pattern and
    # reads badly at any length.
    "min_words_for_rate": 400,
    "min_hits_for_rate": 3,
    # N hits of ONE phrase inside any window of M consecutive sentences. Clustering reads far
    # worse than the raw rate: "five instances in five consecutive sentences" was the operator's
    # first and loudest complaint. 4-in-8 catches that shape; 3-in-10 fires by chance in any long
    # corpus and would bury the real signal under its own noise.
    "phrase_cluster_hits": 4,
    "phrase_cluster_window": 8,
    # Standard deviation of sentence length, in words. Uniformity is the single most reliable
    # machine signature and it is trivially measurable — human prose changes gear.
    # 4.5, not 6.0: the corrected Acme Co resources sit at stdev 5.2-6.0 (mean 9-12 words), and a
    # threshold landing exactly on the observed data is one chosen by accident. These are
    # instructional cards — short, even sentences are the FORMAT there, not a machine tell. The
    # floor has to fire on genuinely flat prose, so it sits below the legitimate range.
    "sentence_len_stdev_floor": 4.5,
    "min_sentences_for_stats": 15,
    "aphorism_rate_per_1k": 1.5,
    "abstract_subject_ratio": 0.12,
    # Consecutive sentences opening with the same word. 5, not 3: an FAQ block legitimately runs
    # four "What ...?" questions in a row, and flagging that is noise rather than texture.
    "opener_run": 5,
    "opener_repeat_ratio": 0.10,
}

# The constructions. Each is (label, regex). Extend as new ones are caught — this list is the
# enumeration, and per this system's own lesson a guard only covers what it enumerates.
PHRASES = [
    ("rather than", r"\brather than\b"),
    ("not X but Y", r"\bnot\s+[\w\s,'-]{1,40}?\s+but\s+(?:rather\s+)?\b"),
    ("it is not … it is", r"\b(?:it|this|that)(?:'s| is| was)\s+not\b[^.!?]{0,60}?\b(?:it|this|that)(?:'s| is| was)\b"),
    ("the point is", r"\bthe point (?:is|of|here)\b"),
    ("what matters is", r"\bwhat matters (?:is|here)\b"),
    ("X, not Y", r",\s*not\s+[a-z]"),
    ("less about … more about", r"\bless about\b[^.!?]{0,60}?\bmore about\b"),
    ("isn't about … it's about", r"\bis(?:n't| not)\s+about\b[^.!?]{0,60}?\b(?:it's|is)\s+about\b"),
]

# The aphorism frame — "X is the win / the whole thing / the hard part", and superlative framing.
APHORISMS = [
    ("is the <noun> frame", r"\bis the (?:win|whole thing|hard part|fun part|point|trick|magic|"
                            r"real \w+|only \w+|entire \w+)\b"),
    ("that's the <noun>", r"\bthat(?:'s| is) the (?:win|whole thing|hard part|fun part|point|trick)\b"),
    ("the most/only/single biggest", r"\bthe (?:most|only|single (?:biggest|most))\b"),
]

# ---------------------------------------------------------------------------------------------
# SYS-156 — OFF-REGISTER PHRASES. A find-check, not a statistic: zero tolerance, one hit flags.
# The counting checks above cannot see a single phrase, and the content-subedit banned-word list
# only enumerates AI vocabulary, so register slang fell in the gap between the two. Ed 24 shipped
# "It took a beat to see it the other way around" and "a content problem wearing a volume
# problem's clothes" past both; the operator caught them on read. These are the literal lists from
# content-subedit Rules 8, 9 and the literal markers of Rule 10 (references/voice-rules.md), kept in
# step with them. Rule 10's staging/role JUDGEMENT stays a human read-pass; only its signature
# phrases are here. US WORDS (soccer, vacation...) were added 2026-10-02; -ize/-our SPELLINGS and
# Rule 9e evaluative adjectives remain judgement calls left to the human read.
#
# Patterns are deliberately NARROW. A zero-tolerance check that fires on "unpack the boxes" or
# "lean in" (a stage direction as often as the idiom) teaches everyone to ignore it, so "lean in"
# is left to the human read, and "level up" / "X's clothing" / "a smaller version of" are narrowed
# to their idiomatic forms - each found as a literal use in shipped copy (2026-10-02 sweep). Rule 9e (evaluative adjectives) and the US
# spellings in Rule 8 are judgement calls, not phrases, so they stay with the human read.
# A tenant adds its own with `register_phrases:` and silences one with `exempt_phrases:` (by label).
# ---------------------------------------------------------------------------------------------
REGISTER = [
    # Rule 8a — casual Americanisms / film / startup slang
    ("took a beat", "8a", r"\b(?:take|takes|took|taking) a beat\b"),
    ("dialled in", "8a", r"\bdiall?ed in\b"),
    ("no-brainer", "8a", r"\bno[- ]brainer\b"),
    ("crushing it", "8a", r"\bcrush(?:es|ed|ing)? it\b"),
    ("nail it", "8a", r"\bnail(?:s|ed|ing)? it\b"),
    ("move the needle", "8a", r"\b(?:move|moves|moved|moving) the needle\b"),
    ("circle back", "8a", r"\bcircl(?:e|es|ed|ing) back\b"),
    ("double down", "8a", r"\bdoubl(?:e|es|ed|ing) down\b"),
    ("deep dive", "8a", r"\bdeep[- ]dives?\b"),
    ("level up", "8a", r"(?<!one )(?<!two )(?<!a )\blevel(?:s|led|ed|ling|ing)? up\b"),
    ("unpack (metaphor)", "8a", r"\bunpack(?:s|ed|ing)? (?:this|that|what|why|how|the (?:idea|concept|"
                                r"question|argument|claim|data|numbers|problem))\b"),
    ("table stakes", "8a", r"\btable stakes\b"),
    ("secret sauce", "8a", r"\bsecret sauce\b"),
    ("drink the Kool-Aid", "8a", r"\b(?:drink|drank|drinking) the kool-?aid\b"),
    ("game-changer", "8a", r"\bgame[- ]chang(?:er|ers|ing)\b"),
    ("low-key", "8a", r"\blow[- ]key\b"),
    ("for sure", "8a", r"\bfor sure\b"),
    ("gonna / wanna", "8a", r"\b(?:gonna|wanna)\b"),
    # Rule 8a (US) — American words where the Australian term belongs (added 2026-10-02, ed 20
    # "soccer field" -> "footy field"). Discrete WORDS only, not -ize/-our spelling variants: a
    # spelling check fires on legitimate -ise/-ize variation and would bury the signal. High-signal
    # terms that almost never appear in the operator's AU B2B prose.
    ("soccer", "8a-US", r"\bsoccer\b"),
    ("vacation", "8a-US", r"\bvacation(?:s|ed|ing)?\b"),
    ("sidewalk", "8a-US", r"\bsidewalks?\b"),
    ("gotten", "8a-US", r"\bgotten\b"),
    ("parking lot", "8a-US", r"\bparking lots?\b"),
    ("cell phone", "8a-US", r"\bcell ?phones?\b"),
    ("math (not maths)", "8a-US", r"\bmath\b"),
    # Rule 8b — metaphor-dressing where a plain statement belongs
    ("wearing X's clothes", "8b", r"\bwearing (?:a|an|the) [\w' -]{1,40}?"
                                  r"(?:clothes|clothing|costume|disguise|mask)\b"),
    ("in X's clothing", "8b", r"\b(?:a|an) \w+ in [\w' -]{1,30}?'s clothing\b"),
    ("a problem in disguise", "8b", r"\bproblem in disguise\b"),
    # Rule 9a — staged pushback / imagined interlocutor
    ("a sharp operator will push back", "9a",
     r"\ba (?:sharp|smart|savvy|good|seasoned|thoughtful|careful) (?:operator|marketer|reader|cmo|"
     r"founder|leader|sceptic|skeptic|executive)s? (?:will|would|might|may|is going to) "
     r"(?:push back|object|ask|already be asking|say|point out)"),
    ("you might be thinking", "9a", r"\byou (?:might|may|could) be thinking\b"),
    ("here's where a sceptic pushes back", "9a", r"\bhere's where (?:a|the) (?:sceptic|skeptic|critic|cynic)\b"),
    ("the obvious objection is", "9a", r"\bthe obvious objection (?:is|here)\b"),
    # Rule 9b — told emotion / editorial aside
    ("and it is uncomfortable", "9b", r"\band (?:it|that|this)(?:'s| is) uncomfortable\b"),
    ("and that's the hard part", "9b", r"\band (?:that|this)(?:'s| is) the hard part\b"),
    ("harder than it sounds", "9b", r"\bwhich is harder than it sounds\b"),
    ("and that stings", "9b", r"\band (?:that|it) stings\b"),
    # Rule 9c — tired approval idioms
    ("earns its keep", "9c", r"\bearn(?:s|ed|ing)? (?:its|their|your|my|our) keep\b"),
    ("punches above its weight", "9c", r"\bpunch(?:es|ed|ing)? above (?:its|their|your|our) weight\b"),
    ("does the heavy lifting", "9c", r"\b(?:do|does|did|doing) (?:the|all the|most of the) heavy lifting\b"),
    ("pulls its weight", "9c", r"\bpull(?:s|ed|ing)? (?:its|their|your|our) weight\b"),
    ("worth its salt", "9c", r"\bworth (?:its|their|his|her) salt\b"),
    # Rule 9d — vague self-congratulatory verbs / comparatives
    ("has sharpened it", "9d", r"\bha(?:s|ve) (?:only )?sharpened (?:it|this|that)\b"),
    ("into sharp relief", "9d", r"\binto sharp(?:er)? relief\b"),
    ("a louder version of", "9d", r"\ba (?:louder|quieter) version of\b"),
    # Rule 10 — fabricated scene / interiority / callback. The RULE is judgement (did the source
    # supply the scene?), but a few literal MARKERS are high-precision AI tells that almost never
    # appear in the operator's own drafts, so they are worth flagging for the human to confirm. Added
    # 2026-10-02 from the eds 20-26 sweep. NOT the whole rule — the staging/role judgement stays a
    # read-pass; these just catch the signature phrases.
    ("the version of me that (callback)", "10/5b", r"\bthe version (?:of (?:me|us|you)|that) (?:who |that )?(?:walked|came|sat|started|finished)"),
    ("nodded along (staged reaction)", "10a", r"\b(?:the room|everyone|they all|heads) nodded(?: along)?\b"),
    ("my first reaction was (epiphany setup)", "10b", r"\bmy first (?:reaction|instinct|thought) was\b"),
]


# Words ending in -ing that are NOT gerunds. The opener test matched /^\w+ing\s/, which reads
# "Bring the trays in when the water goes cloudy." as an abstraction acting - it is an imperative
# addressed to a person, the exact opposite of what the check is looking for. Found by running the
# linter on a fresh document rather than on the corpus it was calibrated against.
_NOT_GERUND = {
    "bring", "sing", "ring", "king", "thing", "string", "spring", "swing", "cling", "fling",
    "sting", "wing", "wring", "during", "nothing", "something", "anything", "everything",
    "morning", "evening", "ceiling", "sibling", "being",
}

# Abstractions standing in for a person or a named thing as the actor. A curated list is
# sufficient and far cheaper than POS tagging (the ticket's own call).
ABSTRACT_SUBJECTS = {
    "the noise", "the work", "the point", "the difference", "the result", "the outcome",
    "the answer", "the question", "the challenge", "the goal", "the idea", "the thing",
    "the value", "the impact", "the approach", "the process", "the system", "the structure",
    "the rhythm", "the energy", "the atmosphere", "the environment", "the experience",
    "the learning", "the growth", "the change", "the shift", "the focus", "the balance",
    "the tension", "the connection", "the relationship", "the conversation", "the moment",
    "everything", "something", "nothing", "anything", "much of it", "most of it", "all of it",
}


def load_config(tenant: str | None) -> tuple[dict, list[str]]:
    """Thresholds + exempt phrases for a tenant. `tenant-brand/<tenant>-slop.yaml`:

        thresholds:
          phrase_rate_per_1k: 2.0
        exempt_phrases:
          - "rather than"        # a named brand device, deliberately repeated
        register_phrases:        # SYS-156: extra zero-tolerance phrases for this voice
          - "sidewalk"

    Absent file = defaults. A malformed one is reported, never silently ignored — a config that
    quietly fails open would make the gate report green while checking nothing.
    """
    cfg = dict(DEFAULTS)
    exempt: list[str] = []
    if not tenant:
        return cfg, exempt
    path = DATA / "tenant-brand" / f"{tenant}-slop.yaml"
    if not path.exists():
        return cfg, exempt
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:  # noqa: BLE001
        print(f"slop-lint: WARNING — {path.name} could not be read ({e}); using defaults",
              file=sys.stderr)
        return cfg, exempt
    for k, v in (data.get("thresholds") or {}).items():
        if k in cfg:
            cfg[k] = v
    exempt = [str(x).strip().lower() for x in (data.get("exempt_phrases") or [])]
    # SYS-156: a tenant's own off-register phrases, matched literally (whole words, any case).
    cfg["register_extra"] = [str(x).strip() for x in (data.get("register_phrases") or [])
                             if str(x).strip()]
    return cfg, exempt


# ---------------------------------------------------------------------------------------------
# Text extraction — same zone rules as jargon_lint: prose only. Code, fenced blocks, <details>
# and front-matter are not prose and must not skew the statistics.
# ---------------------------------------------------------------------------------------------
def prose_lines(path: Path) -> list[tuple[int, str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    is_html = path.suffix.lower() == ".html"
    if is_html:
        raw = re.sub(r"<style.*?</style>|<script.*?</script>", " ", raw, flags=re.S)
    out: list[tuple[int, str]] = []
    in_fence = in_details = in_front = False
    for i, line in enumerate(raw.splitlines(), 1):
        s = line.strip()
        if i == 1 and s == "---":
            in_front = True
            continue
        if in_front:
            if s == "---":
                in_front = False
            continue
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        low = s.lower()
        if "<details" in low:
            in_details = True
        if in_details:
            if "</details>" in low:
                in_details = False
            continue
        # Markdown files carry raw HTML too - inline SVG diagrams, <div> wrappers, tables. Tags
        # were only stripped for .html, so an SVG path element inside a .md file was counted as a
        # sentence. Found by running this skill on a spec that embeds a diagram. Strip tags in
        # BOTH, then drop what is left if it is markup rather than prose.
        s = _html.unescape(re.sub(r"<[^>]+>", " ", s))
        if len(re.findall(r"[A-Za-z]{2,}", s)) < 2:
            continue
        s = re.sub(r"`[^`]*`", " ", s)                        # inline code
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)        # link text, not the URL
        s = re.sub(r"^[#>\-*+\d.\s|]+", "", s)                # heading/list/table furniture
        s = re.sub(r"[*_]{1,2}", "", s)                       # emphasis marks
        if s.strip():
            out.append((i, s.strip()))
    return out


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def sentences_of(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    out = []
    for ln, text in lines:
        for s in _SENT_SPLIT.split(text):
            s = s.strip()
            if len(s.split()) >= 2:          # a 1-word fragment is furniture, not a sentence
                out.append((ln, s))
    return out


def word_count(sentences) -> int:
    return sum(len(s.split()) for _, s in sentences)


# ---------------------------------------------------------------------------------------------
# The checks. Each returns (over_threshold, headline, worst_offenders).
# ---------------------------------------------------------------------------------------------
def check_phrases(sentences, words, cfg, exempt, cluster: bool = True) -> list[dict]:
    findings = []
    per_1k = max(words, 1) / 1000.0
    for label, pat in PHRASES:
        if label.lower() in exempt:
            continue
        rx = re.compile(pat, re.I)
        hits = [(ln, s) for ln, s in sentences if rx.search(s)]
        if not hits:
            continue
        rate = len(hits) / per_1k
        rate_is_meaningful = (words >= cfg["min_words_for_rate"]
                              and len(hits) >= cfg["min_hits_for_rate"])
        # clustering — N hits inside any window of M consecutive sentences
        idx = [i for i, (_, s) in enumerate(sentences) if rx.search(s)]
        win, biggest = cfg["phrase_cluster_window"], 0
        for a in range(len(idx)):
            n = sum(1 for b in idx[a:] if b - idx[a] < win)
            biggest = max(biggest, n)
        clustered = cluster and (biggest >= cfg["phrase_cluster_hits"])
        if (rate_is_meaningful and rate > cfg["phrase_rate_per_1k"]) or clustered:
            findings.append({
                "check": "construction repetition",
                "detail": f'"{label}" x{len(hits)} = {rate:.1f}/1000 words'
                          + (f" \u00b7 {biggest} inside {win} consecutive sentences" if clustered else ""),
                "over": f"cap {cfg['phrase_rate_per_1k']:.1f}/1000"
                        + (f", cluster cap {cfg['phrase_cluster_hits']}" if clustered else ""),
                "worst": hits[:4],
            })
    return findings


def check_sentence_variance(sentences, cfg) -> list[dict]:
    if len(sentences) < cfg["min_sentences_for_stats"]:
        return []
    lens = [len(s.split()) for _, s in sentences]
    sd = statistics.pstdev(lens)
    if sd >= cfg["sentence_len_stdev_floor"]:
        return []
    return [{
        "check": "sentence-length uniformity",
        "detail": f"stdev {sd:.1f} words across {len(lens)} sentences "
                  f"(mean {statistics.mean(lens):.1f}) — the prose never changes gear",
        "over": f"floor {cfg['sentence_len_stdev_floor']:.1f}",
        "worst": [],
    }]


def check_aphorisms(sentences, words, cfg) -> list[dict]:
    per_1k = max(words, 1) / 1000.0
    hits = []
    for label, pat in APHORISMS:
        rx = re.compile(pat, re.I)
        hits += [(ln, s) for ln, s in sentences if rx.search(s)]
    if not hits:
        return []
    rate = len(hits) / per_1k
    if (words < cfg["min_words_for_rate"] or len(hits) < cfg["min_hits_for_rate"]
            or rate <= cfg["aphorism_rate_per_1k"]):
        return []
    return [{
        "check": "aphorism density",
        "detail": f"{len(hits)} aphorism frames = {rate:.1f}/1000 words "
                  f'("X is the win / the whole thing / the most …")',
        "over": f"cap {cfg['aphorism_rate_per_1k']:.1f}/1000",
        "worst": hits[:4],
    }]


def check_abstract_subjects(sentences, cfg) -> list[dict]:
    # A ratio is as meaningless on a short sample as a rate is: in a four-sentence document one
    # hit is 25% and means nothing. The rate checks already had this floor; the ratio did not,
    # which is how a clean four-sentence sample flagged.
    if len(sentences) < cfg["min_sentences_for_stats"]:
        return []
    hits = []
    for ln, s in sentences:
        low = s.lower().lstrip("\"'“‘ ")
        first_two = " ".join(low.split()[:2]).strip(",")
        first_three = " ".join(low.split()[:3]).strip(",")
        _g = re.match(r"^(\w+ing)\s+\w", low)
        gerund = _g and _g.group(1) not in _NOT_GERUND
        if first_two in ABSTRACT_SUBJECTS or first_three in ABSTRACT_SUBJECTS or gerund:
            hits.append((ln, s))
    if not sentences:
        return []
    ratio = len(hits) / len(sentences)
    if ratio <= cfg["abstract_subject_ratio"]:
        return []
    return [{
        "check": "abstraction as the actor",
        "detail": f"{len(hits)}/{len(sentences)} sentences ({ratio:.0%}) open on an abstraction "
                  f"or a gerund rather than a person or a named thing",
        "over": f"cap {cfg['abstract_subject_ratio']:.0%}",
        "worst": hits[:4],
    }]


def check_openers(sentences, cfg) -> list[dict]:
    if len(sentences) < cfg["min_sentences_for_stats"]:
        return []
    firsts = [s.split()[0].lower().strip(".,:;\"'") for _, s in sentences if s.split()]
    runs, best, start = 1, 1, 0
    best_at = 0
    for i in range(1, len(firsts)):
        if firsts[i] == firsts[i - 1]:
            runs += 1
            if runs > best:
                best, best_at = runs, start
        else:
            runs, start = 1, i
    repeated = sum(1 for i in range(1, len(firsts)) if firsts[i] == firsts[i - 1])
    ratio = repeated / max(len(firsts) - 1, 1)
    out = []
    if best >= cfg["opener_run"]:
        out.append({
            "check": "opener repetition",
            "detail": f'{best} consecutive sentences open with "{firsts[best_at]}"',
            "over": f"run cap {cfg['opener_run']}",
            "worst": sentences[best_at:best_at + min(best, 4)],
        })
    elif ratio > cfg["opener_repeat_ratio"]:
        out.append({
            "check": "opener repetition",
            "detail": f"{ratio:.0%} of sentences repeat the previous sentence's opening word",
            "over": f"cap {cfg['opener_repeat_ratio']:.0%}",
            "worst": [],
        })
    return out


# MENTION, NOT USE. A ban list, a voice rule or a QA note NAMES the phrase ("Banned: game-changing,
# synergy ..."); the 2026-10-02 sweep over every asset file found that was two-thirds of all hits.
# Skip a sentence that is plainly listing banned/avoided words, and a hit inside quotation marks
# (a quoted example, or a source's own words, is not the writer's register).
_MENTION_CONTEXT = re.compile(
    r"\b(?:banned|ban list|avoid(?:ed)?|words?[- ]we[- ]avoid|never these words|never say|"
    r"blocklist|prohibited|rejected|scan(?:ned)?)\b|\bnever\b[^:.]{0,40}:", re.I)
_QUOTES = "\"“”"


def _is_quoted(text: str, start: int, end: int) -> bool:
    before = text[:start]
    return sum(before.count(q) for q in _QUOTES) % 2 == 1 and any(q in text[end:] for q in _QUOTES)


def check_register(sentences, cfg, exempt) -> list[dict]:
    """SYS-156 — zero-tolerance find-check for the Rule 8/9 phrases. Per file only: a phrase is
    wrong wherever it appears, so a corpus total would just repeat the per-file findings."""
    rules = [(label, rule, re.compile(pat, re.I)) for label, rule, pat in REGISTER
             if label.lower() not in exempt]
    rules += [(x, "tenant", re.compile(r"\b" + re.escape(x) + r"\b", re.I))
              for x in cfg.get("register_extra") or [] if x.lower() not in exempt]
    counts: dict[str, int] = {}
    hits = []
    for ln, s in sentences:
        norm = s.replace("’", "'").replace("‘", "'")
        if _MENTION_CONTEXT.search(norm):
            continue
        for label, rule, rx in rules:
            m = rx.search(norm)
            if m and not _is_quoted(norm, m.start(), m.end()):
                key = f'"{label}" ({rule})'
                counts[key] = counts.get(key, 0) + 1
                hits.append((ln, s))
    if not hits:
        return []
    return [{
        "check": "off-register phrase",
        "detail": " · ".join(f"{k} x{n}" if n > 1 else k for k, n in counts.items())
                  + " — content-subedit Rules 8–10; say it plainly",
        "over": "limit 0",
        "worst": hits[:6],
    }]


def analyse(paths: list[Path], cfg, exempt) -> dict:
    per_file = {}
    corpus_sent: list[tuple[str, int, str]] = []
    for p in paths:
        lines = prose_lines(p)
        sents = sentences_of(lines)
        if not sents:
            continue
        words = word_count(sents)
        findings = (check_phrases(sents, words, cfg, exempt)
                    + check_sentence_variance(sents, cfg)
                    + check_aphorisms(sents, words, cfg)
                    + check_abstract_subjects(sents, cfg)
                    + check_openers(sents, cfg)
                    + check_register(sents, cfg, exempt))
        per_file[p] = {"words": words, "sentences": len(sents), "findings": findings}
        corpus_sent += [(p.name, ln, s) for ln, s in sents]

    # The corpus pass — the vantage point per-asset review cannot reach.
    flat = [(ln, s) for _, ln, s in corpus_sent]
    cw = word_count(flat)
    corpus = {
        "files": len(per_file), "words": cw, "sentences": len(flat),
        # cluster=False: sentence adjacency ACROSS files is an artefact of
        #        concatenation, not a rhythm a reader would ever meet.
        "findings": (check_phrases(flat, cw, cfg, exempt, cluster=False)
                     + check_sentence_variance(flat, cfg)
                     + check_aphorisms(flat, cw, cfg)
                     + check_abstract_subjects(flat, cfg)),
    } if len(per_file) > 1 else None
    return {"per_file": per_file, "corpus": corpus}


def collect(args: list[str]) -> list[Path]:
    out: list[Path] = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            out += [q for q in sorted(p.rglob("*")) if q.suffix.lower() in TEXT_SUFFIXES]
        elif p.exists():
            out.append(p)
        else:
            print(f"slop-lint: not found: {p}", file=sys.stderr)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="AI-texture lint (SYS-154).")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--tenant", help="load tenant-brand/<tenant>-slop.yaml thresholds + exemptions")
    ap.add_argument("--quiet", action="store_true", help="exit code only")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    a = ap.parse_args(argv)
    if not a.paths:
        ap.print_help()
        return 2

    cfg, exempt = load_config(a.tenant)
    files = collect(a.paths)
    if not files:
        print("slop-lint: no readable text files given — nothing was checked", file=sys.stderr)
        return 2   # never report OK having checked nothing

    res = analyse(files, cfg, exempt)
    total = sum(len(v["findings"]) for v in res["per_file"].values())
    total += len(res["corpus"]["findings"]) if res["corpus"] else 0

    if a.json:
        print(json.dumps({
            "files": [{"path": str(p), **{k: v for k, v in d.items() if k != "findings"},
                       "findings": [{**f, "worst": [[ln, s] for ln, s in f["worst"]]}
                                    for f in d["findings"]]}
                      for p, d in res["per_file"].items()],
            "corpus": ({**res["corpus"],
                        "findings": [{**f, "worst": [[ln, s] for ln, s in f["worst"]]}
                                     for f in res["corpus"]["findings"]]}
                       if res["corpus"] else None),
            "total_findings": total,
        }, indent=2))
        return 1 if total else 0

    if not a.quiet:
        for p, d in res["per_file"].items():
            if not d["findings"]:
                print(f"OK   {p.name}: {d['words']} words, {d['sentences']} sentences — within thresholds.")
                continue
            print(f"FLAG {p.name}: {len(d['findings'])} texture finding(s) "
                  f"({d['words']} words, {d['sentences']} sentences)")
            for f in d["findings"]:
                print(f"     [{f['check']}] {f['detail']}  (over: {f['over']})")
                for ln, s in f["worst"]:
                    print(f"        L{ln}: {s[:110]}")
        if res["corpus"]:
            c = res["corpus"]
            print(f"\n--- CORPUS ({c['files']} files, {c['words']} words, {c['sentences']} sentences) ---")
            print("    The vantage point per-asset review cannot reach: a construction five times")
            print("    in one paragraph is invisible while you read that paragraph.")
            if not c["findings"]:
                print("OK   corpus: within thresholds.")
            for f in c["findings"]:
                print(f"FLAG [{f['check']}] {f['detail']}  (over: {f['over']})")
                for ln, s in f["worst"]:
                    print(f"        L{ln}: {s[:110]}")
        print(f"\n{'FLAG' if total else 'OK'} — {total} finding(s) over threshold.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
