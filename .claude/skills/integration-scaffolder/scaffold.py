#!/usr/bin/env python3
"""integration-scaffolder — stamp a new deploy adapter skeleton conforming to the
deploy-adapter contract (.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md).

SCOPE: deploy adapters only (SYS-066). Template-driven; keeps it simple.

Usage:
    python scaffold.py --name <adapter-name> --target "<human target description>"
                       [--dest <skills-dir>] [--force]

Produces .claude/skills/deploy-<name>/ with four contract files:
    SKILL.md                    (interface stub — INPUTS/OUTPUTS/deploy/verify)
    adapter.py                  (implementation stub with --smoke-test path + envelope)
    investigation-reference.md  (reference stub to fill in)
    smoke_test.py               (test stub that runs the adapter in smoke mode)

Prints the created file paths (one per line) + a final "SCAFFOLD OK" line.
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates"
REQUIRED_FILES = ["SKILL.md", "adapter.py", "investigation-reference.md", "smoke_test.py"]


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not s:
        raise ValueError("name reduces to empty slug")
    return s


def title_case(slug: str) -> str:
    return " ".join(p.capitalize() for p in slug.split("-"))


def render(template_name: str, ctx: dict) -> str:
    raw = (TEMPLATES / template_name).read_text(encoding="utf-8")
    # Simple {{KEY}} substitution — deliberately minimal, no template engine.
    for k, v in ctx.items():
        raw = raw.replace("{{" + k + "}}", v)
    return raw


def default_skills_dir() -> Path:
    # scaffold.py lives at .../.claude/skills/integration-scaffolder/scaffold.py
    return Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="adapter name, e.g. 'static-folder'")
    ap.add_argument("--target", required=True, help="human description of the deploy target")
    ap.add_argument("--dest", default=None, help="skills dir (default: alongside this skill)")
    ap.add_argument("--force", action="store_true", help="overwrite existing adapter dir")
    args = ap.parse_args()

    slug = slugify(args.name)
    skills_dir = Path(args.dest).resolve() if args.dest else default_skills_dir()
    adapter_dir = skills_dir / f"deploy-{slug}"

    if adapter_dir.exists() and not args.force:
        print(f"ERROR: {adapter_dir} already exists (use --force to overwrite)", file=sys.stderr)
        return 2

    ctx = {
        "NAME": slug,
        "TITLE": title_case(slug),
        "TARGET": args.target,
        "DATE": date.today().isoformat(),
    }

    adapter_dir.mkdir(parents=True, exist_ok=True)
    template_map = {
        "SKILL.md": "SKILL.md.tmpl",
        "adapter.py": "adapter.py.tmpl",
        "investigation-reference.md": "investigation-reference.md.tmpl",
        "smoke_test.py": "smoke_test.py.tmpl",
    }
    created = []
    for out_name, tmpl in template_map.items():
        out_path = adapter_dir / out_name
        out_path.write_text(render(tmpl, ctx), encoding="utf-8")
        created.append(out_path)

    for p in created:
        print(str(p))
    # Self-check: all four contract files present.
    missing = [f for f in REQUIRED_FILES if not (adapter_dir / f).exists()]
    if missing:
        print(f"ERROR: contract files missing: {missing}", file=sys.stderr)
        return 1
    print("SCAFFOLD OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
