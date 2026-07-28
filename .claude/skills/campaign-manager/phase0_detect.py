#!/usr/bin/env python3
"""Phase-0 baseline auto-detect (SYS-065) - report which baseline SECTIONS a tenant
already has, so CM can run Phase 0 idempotently: interview only for the gaps, and
scope an update to one section without redoing the whole baseline.

This is the read-only companion to phase0_gate.py. The GATE answers "may a campaign
start?" (a pass/block on the required minimum). This DETECTOR answers "what does this
tenant already have, section by section?" - the input CM needs to (a) skip what's
present on a re-run, (b) list what's missing, and (c) target a single --section update.

Section vocabulary (operator-facing update verbs map onto these):
  brand-context  -> tenant-brand/<tenant>.md            (voice is a sub-scope of this file)
  voice          -> tenant-brand/<tenant>.md  (§voice)  (same artifact; scoped edit)
  segments       -> tenant-brand/<tenant>-segments.md
  market         -> tenant-brand/<tenant>-market.md
  compliance     -> tenant-brand/<tenant>-compliance.md
  channels       -> tenant/<tenant>/integrations.yaml   (tech stack + channels in use)

Detection is dual-signal and deliberately conservative:
  - FILE signal:     does the underlying artifact file exist on disk?
  - BASELINE signal: is there a tenant.yaml `baseline:` entry with status: present?
A section is `present` only when BOTH agree (file exists AND declared present). If the
file exists but isn't declared (or vice-versa) it is `partial` - a mismatch CM should
reconcile with the operator, never silently. Absent on both = `missing` (interview it).

`voice` has no file of its own; it mirrors brand-context's presence but is reported
separately so "update just my voice" is a legible scoped verb.

Usage:
  python .claude/skills/campaign-manager/phase0_detect.py --tenant acme-co
  python .claude/skills/campaign-manager/phase0_detect.py --tenant acme-co --json
  python .claude/skills/campaign-manager/phase0_detect.py --tenant acme-co --section market
  python .claude/skills/campaign-manager/phase0_detect.py --tenant acme-co --root /path/to/checkout

Exit 0 always (this is a report, not a gate). Use phase0_gate.py for the block decision.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[3]  # .claude/skills/campaign-manager/ -> checkout root

# section -> (baseline-key in tenant.yaml, artifact path relative to checkout root)
# `voice` shares the brand-context artifact; it has no key/file of its own.
SECTIONS = {
    "brand-context": ("brand_context", "tenant-brand/{t}.md"),
    "voice":         (None,            "tenant-brand/{t}.md"),
    "segments":      ("segments",      "tenant-brand/{t}-segments.md"),
    "market":        ("market",        "tenant-brand/{t}-market.md"),
    "compliance":    ("compliance",    "tenant-brand/{t}-compliance.md"),
    "channels":      ("integrations",  "tenant/{t}/integrations.yaml"),
}


def _load_baseline(root: Path, tenant: str) -> tuple[dict, list[str]]:
    """Return ({key: status}, notes[]). Missing/unparseable yaml is not fatal here."""
    notes: list[str] = []
    yml = root / "tenant-brand" / f"{tenant}.yaml"
    if not yml.exists():
        notes.append(f"tenant-brand/{tenant}.yaml absent - no baseline declared yet")
        return {}, notes
    if yaml is None:
        notes.append("PyYAML not available - reading file signals only")
        return {}, notes
    try:
        data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    except Exception as e:
        notes.append(f"tenant-brand/{tenant}.yaml did not parse ({e}) - file signals only")
        return {}, notes
    out = {}
    for e in (data.get("baseline") or []):
        if isinstance(e, dict) and e.get("key"):
            out[e["key"]] = str(e.get("status", "")).lower()
    return out, notes


def detect(root: Path, tenant: str) -> dict:
    baseline, notes = _load_baseline(root, tenant)
    sections: dict[str, dict] = {}
    for name, (key, rel) in SECTIONS.items():
        path = root / rel.format(t=tenant)
        file_ok = path.exists()
        declared = (key is not None) and baseline.get(key) == "present"
        # voice inherits brand-context's declaration (shared artifact)
        if key is None:
            declared = baseline.get("brand_context") == "present"
        if file_ok and declared:
            state = "present"
        elif not file_ok and not declared:
            state = "missing"
        else:
            state = "partial"
        sections[name] = {"state": state, "file": rel.format(t=tenant),
                          "file_exists": file_ok, "declared_present": declared}
    present = [s for s, v in sections.items() if v["state"] == "present"]
    missing = [s for s, v in sections.items() if v["state"] == "missing"]
    partial = [s for s, v in sections.items() if v["state"] == "partial"]
    return {"tenant": tenant, "sections": sections, "present": present,
            "missing": missing, "partial": partial, "notes": notes}


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-0 baseline auto-detect (per-section report)")
    ap.add_argument("--tenant", required=True, help="tenant slug (matches tenant-brand/<slug>.yaml)")
    ap.add_argument("--section", help="report only this section (from the section vocabulary)")
    ap.add_argument("--root", default=str(ROOT), help="checkout root (default: this checkout)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    if a.section and a.section not in SECTIONS:
        print(f"unknown section '{a.section}'. Known: {', '.join(SECTIONS)}", file=sys.stderr)
        return 2

    r = detect(Path(a.root).resolve(), a.tenant)
    if a.section:
        r = {"tenant": r["tenant"], "sections": {a.section: r["sections"][a.section]},
             "notes": r["notes"]}

    if a.json:
        print(json.dumps(r, indent=2))
        return 0

    print(f"[phase0-detect] {r['tenant']}")
    for name, v in r["sections"].items():
        mark = {"present": "OK ", "missing": " - ", "partial": " ! "}[v["state"]]
        print(f"  [{mark}] {name:<14} {v['state']:<8} ({v['file']})")
    for n in r["notes"]:
        print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
