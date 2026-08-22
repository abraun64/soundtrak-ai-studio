#!/usr/bin/env python3
"""
secret_scan — keep credentials out of the DATA repo (team-deployment.md §9.2).

A secret committed to a shared repo is permanent: it is in every clone's history, and
rotating it is the only real remedy. So the cheap moment to catch one is BEFORE the commit,
not in review. This is the check the Stop hook runs before it stages anything.

  python .claude/lib/secret_scan.py <path>...      # scan files or dirs
  python .claude/lib/secret_scan.py --staged       # scan what git has staged (pre-commit)

Exit 0 = clean, 1 = findings.

DELIBERATELY NARROW. Patterns match credential SHAPES with distinctive prefixes and length
floors (`sk-ant-...`, `ghp_...`, an AWS key id) rather than any string near the word "key".
A scanner that cries wolf gets bypassed, and a bypassed scanner protects nothing — the same
failure mode as the cadence inbox that refiled decided findings (SYS-144).

Placeholders are NOT secrets: `${VAR}`, `<your-key-here>`, `xxx`, `changeme`, and the
`.env.example` file exist precisely to be committed.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

# (label, compiled pattern). Prefix-anchored and length-floored to stay specific.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Anthropic API key",   re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI API key",      re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("GitHub token",        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token",         re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("AWS access key id",   re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google API key",      re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Replicate token",     re.compile(r"\br8_[A-Za-z0-9]{30,}")),
    ("Mailchimp API key",   re.compile(r"\b[0-9a-f]{32}-us[0-9]{1,2}\b")),
    ("private key block",   re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("hardcoded password",  re.compile(r"(?i)\b(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"$<{\s]{8,}['\"]")),
]

# A finding containing any of these is a placeholder, not a credential.
# NOTE: deliberately does NOT include digit runs like `1234567` or `000000`. Those read like
# obvious dummy values, but real generated keys contain digit runs too — including them made
# the scanner miss a genuine `sk-ant-...` and a `ghp_...` in testing. A false NEGATIVE here is
# a credential in permanent history; a false positive is ten seconds of an operator's time.
PLACEHOLDER = re.compile(
    r"(\$\{|\$[A-Z_]{3,}|<[^>]+>|xxx+|changeme|your[-_]?(key|token|secret)|placeholder|example|"
    r"redacted|dummy|sample|todo|\.\.\.)", re.I)

SKIP_NAMES = {".env.example"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".mp4", ".mov", ".mp3", ".zip",
               ".woff", ".woff2", ".ttf", ".ico", ".pyc", ".docx", ".pptx", ".xlsx"}
MAX_BYTES = 2_000_000     # a credential does not live in a 2MB file; skip the cost


def scan_text(text: str, origin: str) -> list[tuple[str, int, str, str]]:
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if len(line) > 4000:          # minified/base64 blobs: not where secrets hide readably
            continue
        for label, pat in PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            hit = m.group(0)
            if PLACEHOLDER.search(hit) or PLACEHOLDER.search(line):
                continue
            masked = hit[:6] + "..." + hit[-4:] if len(hit) > 14 else hit[:4] + "..."
            out.append((origin, lineno, label, masked))
    return out


def scan_file(p: Path) -> list[tuple[str, int, str, str]]:
    if p.name in SKIP_NAMES or p.suffix.lower() in SKIP_SUFFIX:
        return []
    try:
        if p.stat().st_size > MAX_BYTES:
            return []
        return scan_text(p.read_text(encoding="utf-8", errors="replace"), str(p))
    except OSError:
        return []


def scan_paths(paths) -> list[tuple[str, int, str, str]]:
    findings = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not (SKIP_DIRS & set(f.parts)):
                    findings.extend(scan_file(f))
        elif p.is_file():
            findings.extend(scan_file(p))
    return findings


def staged_files(repo: Path) -> list[Path]:
    try:
        r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                           cwd=str(repo), capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return []
        return [repo / line for line in r.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


def report(findings) -> str:
    if not findings:
        return "secret-scan: clean."
    lines = [f"secret-scan: {len(findings)} possible credential(s) - DO NOT COMMIT:"]
    for origin, lineno, label, masked in findings[:40]:
        lines.append(f"  {origin}:{lineno}  {label}  {masked}")
    if len(findings) > 40:
        lines.append(f"  ... and {len(findings) - 40} more")
    lines.append("  A secret in a shared repo is permanent - it is in every clone's history.")
    lines.append("  Move it to a per-operator .env (never committed) and ROTATE the exposed value.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files or dirs to scan")
    ap.add_argument("--staged", action="store_true", help="scan git's staged files")
    ap.add_argument("--repo", default=".", help="repo root for --staged")
    a = ap.parse_args()

    targets = staged_files(Path(a.repo).resolve()) if a.staged else a.paths
    if not targets:
        print("secret-scan: nothing to scan.")
        return 0
    findings = scan_paths(targets)
    print(report(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
