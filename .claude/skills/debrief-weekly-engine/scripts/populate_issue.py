#!/usr/bin/env python3
"""
populate_issue.py - fill the issue-header-template.html data-slot fields for one edition.

Design: the look kit's issue-header-template.html is the LOCKED format (Producer/Brand
approved A1). This script ONLY replaces the `data-slot` field contents. It never touches
the fixed elements: the 6px red top rule, the emblem + Fraunces masthead lockup, the
screen-card chrome (three dots, leftmost red), the two-column structure, or which field
carries red (always LEARNED + the SHOWN stamp). It also deletes the template's slot-legend
band (production editions drop it).

Reads a per-cycle inputs YAML (cycle-inputs.yaml) with this shape:

    eyebrow:        "Soundtrak · The Debrief · Lesson 04"
    this_lesson:    "The moment you can wind it all back."
    headline:       "I started saving to OneDrive. I ended with a versioned system."
    deck:           "One backup habit turned a pile of agents into software you can trust."
    read_cue:       "The full decision and the evidence, inside"
    hero:
      shot:         "images/hero-<slug>.png"     # a real Soundtrak surface (scrub-passed)
      path_chip:    "soundtrak/ai-studio/history"
      cap:          "The actual campaign history log. Not a mockup, the real surface."
    evidence:
      path_chip:    "debrief/ed-04/evidence"
      started:      "local OneDrive save"
      ended:        "versioned Git repo"
      changed:      "one backup habit"
      learned:      "you can wind the whole thing back"    # -> the red LEARNED line
      elapsed:      "1h 40m"
      files:        "6"
      tokens:       "$0.19"
      sendbacks:    "1  (kept in)"
      dated:        "2026-06-02"

Usage:
  python populate_issue.py --inputs cycle-inputs.yaml \
      --template ../../01-look-kit/issue-header-template.html \
      --out issue-header.html

Every slot value is HTML-escaped before insertion (copy is plain text). The receipts
guardrail is enforced here too: the record values are checked against a small deny-list
(no 'hour'/'hrs'/'ROI'/'proven'/'guaranteed'/'results' in the record) so a stray operator
hour or outcome claim can't slip into the Courier record. On a hit the script exits non-zero
with the offending field - it does not silently publish.
"""
import argparse
import html
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

# receipts guardrail - these must never appear in a record VALUE (look-guide.md 'Don't' rules)
RECORD_DENY = ("hour", "hrs", "roi", "proven", "guarantee", "results")
RECORD_FIELDS = ("elapsed", "files", "tokens", "sendbacks", "dated",
                 "started", "ended", "changed", "learned")


def set_slot(htmldoc: str, slot: str, value: str) -> str:
    """Replace the inner text of the element carrying data-slot="<slot>".

    Handles both the <img ...> self-closing case (sets src/alt) and the text-node case.
    Raises if the slot is not present so a typo in the inputs is caught, not swallowed.
    """
    esc = html.escape(value, quote=True)

    # image slot (hero-shot): set src (+ keep a sensible alt if none given elsewhere)
    img_pat = re.compile(rf'(<img\b[^>]*\bdata-slot="{re.escape(slot)}"[^>]*)>', re.DOTALL)
    if img_pat.search(htmldoc):
        def _img(m):
            tag = m.group(1)
            if 'src="' in tag:
                tag = re.sub(r'src="[^"]*"', f'src="{esc}"', tag)
            else:
                tag = tag + f' src="{esc}"'
            return tag + ">"
        return img_pat.sub(_img, htmldoc, count=1)

    # text slot: replace inner content of the first element with this data-slot
    text_pat = re.compile(
        rf'(<([a-zA-Z0-9]+)\b[^>]*\bdata-slot="{re.escape(slot)}"[^>]*>)(.*?)(</\2>)',
        re.DOTALL,
    )
    if not text_pat.search(htmldoc):
        raise KeyError(f'data-slot="{slot}" not found in template')
    return text_pat.sub(lambda m: m.group(1) + esc + m.group(4), htmldoc, count=1)


def check_receipts(ev: dict):
    problems = []
    for k, v in ev.items():
        if k in RECORD_FIELDS and isinstance(v, str):
            low = v.lower()
            for bad in RECORD_DENY:
                # allow the word 'hour' only inside an elapsed value like '1h 40m' is fine (uses h),
                # but a literal 'hour(s)' is the banned operator-hours pattern.
                if bad in low:
                    problems.append(f"record field '{k}' contains banned token '{bad}': {v!r}")
    return problems


def populate(inputs_path: Path, template_path: Path, out_path: Path):
    data = yaml.safe_load(inputs_path.read_text(encoding="utf-8"))
    tpl = template_path.read_text(encoding="utf-8")

    ev = data.get("evidence", {}) or {}
    problems = check_receipts(ev)
    if problems:
        sys.exit("RECEIPTS GUARDRAIL FAILED (look-guide.md - receipts not outcomes, never hours):\n  - "
                 + "\n  - ".join(problems))

    hero = data.get("hero", {}) or {}

    # map inputs -> data-slot names (the template's slot vocabulary)
    slots = {
        "eyebrow": data.get("eyebrow"),
        "this-lesson": data.get("this_lesson"),
        "headline": data.get("headline"),
        "deck": data.get("deck"),
        "read-cue": data.get("read_cue"),
        "hero-shot": hero.get("shot"),
        "hero-path-chip": hero.get("path_chip"),
        "hero-cap": hero.get("cap"),
        "path-chip": ev.get("path_chip"),
        "ev-started": ev.get("started"),
        "ev-ended": ev.get("ended"),
        "ev-changed": ev.get("changed"),
        "ev-learned": ev.get("learned"),
        "rec-elapsed": ev.get("elapsed"),
        "rec-files": str(ev.get("files")) if ev.get("files") is not None else None,
        "rec-tokens": ev.get("tokens"),
        "rec-sendbacks": ev.get("sendbacks"),
        "rec-dated": ev.get("dated"),
    }

    missing = [k for k, v in slots.items() if v in (None, "")]
    if missing:
        sys.exit(f"Missing required inputs for slots: {', '.join(missing)}. "
                 f"Every per-edition slot must be filled (see the YAML shape in this script's docstring).")

    for slot, value in slots.items():
        tpl = set_slot(tpl, slot, str(value))

    # drop the template-only slot legend + its <p class="slot-legend"> band (production drops it)
    tpl = re.sub(r'<p class="slot-legend">.*?</p>', "", tpl, flags=re.DOTALL)

    out_path.write_text(tpl, encoding="utf-8")
    print(f"Wrote {out_path} - {len(slots)} slots filled; slot legend removed; "
          f"receipts guardrail passed. Fixed elements untouched.")


def main():
    ap = argparse.ArgumentParser(description="Fill the issue-header-template.html data-slot fields for one edition.")
    ap.add_argument("--inputs", required=True, type=Path)
    ap.add_argument("--template", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    populate(args.inputs, args.template, args.out)


if __name__ == "__main__":
    main()
