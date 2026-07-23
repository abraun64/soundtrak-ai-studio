#!/usr/bin/env python3
"""
hero_scrub.py - the LOCKED 6-point hero-screenshot scrub gate (Governance 2026-07-08).

Soundtrak's operator surfaces are multi-tenant, and a screenshot publishes whatever is in
frame, permanently. Every edition's hero image MUST pass this scrub before it publishes.
This script is the mechanical gate the engine runs: it prints the six locked checks, records
the reviewer's per-point verdict, and BLOCKS (exit 2 = Governance Hold) unless all six are an
explicit pass. "In doubt -> Governance Hold, not a judgment call" is enforced: any point left
unanswered, or answered 'unsure', is a Hold.

The six points are verbatim from look-guide.md (LOCKED scrub):
  1. No other tenant in frame (no client/tenant name in any list, breadcrumb, slug, switcher,
     filename, nav label). Crop/scope to the one Soundtrak campaign.
  2. No client data (no client campaign, KPI, budget, spend, metric, or asset title).
  3. No PII (no real subscriber email, contact, or lead row). Placeholder / Soundtrak-internal only.
  4. No prohibited claim in frame (no guaranteed/proven/results/ROI language or results figure
     visible in any panel).
  5. Own-numbers on screen too (any cost/receipt figure reads as Soundtrak's own build economics:
     elapsed / files / tokens / send-backs; never operator hours, never a client's).
  6. In doubt -> Governance Hold, not a judgment call.

Usage (interactive review, the default):
  python hero_scrub.py --image images/hero-ed04-history.png
     -> prints the checklist; the reviewer (operator or Governance, via the skill) answers
        pass/fail/unsure for points 1-5; point 6 is the policy, applied automatically.

Usage (engine/automated with an explicit pre-recorded verdict file):
  python hero_scrub.py --image <img> --verdicts scrub-verdicts.yaml
     scrub-verdicts.yaml:  {p1: pass, p2: pass, p3: pass, p4: pass, p5: pass, reviewer: "the operator"}

Exit codes:  0 = CLEAR (all six pass)   2 = HOLD (any fail/unsure/unanswered)
The skill treats a non-zero exit as a hard block: the edition does not publish.
"""
import argparse
import sys
from pathlib import Path

POINTS = [
    ("p1", "No OTHER TENANT anywhere in frame (list, breadcrumb, slug, switcher, filename, nav label). Scoped to the one Soundtrak campaign?"),
    ("p2", "No CLIENT DATA (client campaign, KPI, budget, spend, metric, or asset title) visible?"),
    ("p3", "No PII (real subscriber email, contact, lead row)? Placeholder / Soundtrak-internal only?"),
    ("p4", "No PROHIBITED CLAIM in frame (guaranteed / proven / results / ROI language, or a results figure in any panel)?"),
    ("p5", "OWN-NUMBERS only on screen (elapsed / files / tokens / send-backs) - never operator hours, never a client's?"),
]
PASS = {"pass", "y", "yes", "true", "ok", "clear"}


def load_verdicts(path: Path):
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML required for --verdicts: pip install pyyaml")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def prompt_verdicts():
    verdicts = {}
    print("\nAnswer pass / fail / unsure for each. 'unsure' or blank = HOLD (point 6 policy).\n")
    for key, text in POINTS:
        try:
            ans = input(f"  [{key}] {text}\n        verdict> ").strip().lower()
        except EOFError:
            ans = ""
        verdicts[key] = ans
    return verdicts


def run(image: Path, verdicts: dict):
    print("=" * 74)
    print("HERO-SCREENSHOT SCRUB (LOCKED - Governance 2026-07-08)")
    print(f"Image under review: {image}")
    print("=" * 74)
    for key, text in POINTS:
        print(f"  {key}. {text}")
    print("  p6. IN DOUBT -> Governance Hold, not a judgment call. (policy, auto-applied)")
    print("-" * 74)

    fails, unsure = [], []
    for key, _ in POINTS:
        v = str(verdicts.get(key, "")).strip().lower()
        if v in PASS:
            status = "PASS"
        elif v in ("fail", "n", "no", "false", "block"):
            status = "FAIL"
            fails.append(key)
        else:
            status = "UNSURE/UNANSWERED -> HOLD"
            unsure.append(key)
        print(f"  {key}: {status}")
    print("=" * 74)

    if fails or unsure:
        reasons = []
        if fails:
            reasons.append(f"failed: {', '.join(fails)}")
        if unsure:
            reasons.append(f"unsure/unanswered (point-6 policy): {', '.join(unsure)}")
        print(f"VERDICT: GOVERNANCE HOLD - {'; '.join(reasons)}.")
        print("The edition does NOT publish. Crop/scope/replace the hero, or escalate to Governance.")
        return 2

    print("VERDICT: CLEAR - all six points pass. Hero may publish.")
    if verdicts.get("reviewer"):
        print(f"Reviewed by: {verdicts['reviewer']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Run the locked 6-point hero-screenshot scrub.")
    ap.add_argument("--image", required=True, type=Path, help="path to the hero screenshot under review")
    ap.add_argument("--verdicts", type=Path, help="YAML of pre-recorded verdicts (p1..p5 + reviewer); else prompt")
    args = ap.parse_args()

    if not args.image.exists():
        print(f"WARNING: hero image not found at {args.image} - scrub a real captured surface, not a missing file.")

    verdicts = load_verdicts(args.verdicts) if args.verdicts else prompt_verdicts()
    sys.exit(run(args.image, verdicts))


if __name__ == "__main__":
    main()
