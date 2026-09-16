#!/usr/bin/env python3
"""Guard: what we PRINT AT an operator must be runnable and readable by them.

Two rules. No shell `&&`, and no spec section numbers.

Windows PowerShell 5.1 — the default shell on every Windows machine we deploy to — rejects
`&&` with "The token '&&' is not a valid statement separator in this version." A remediation
line that cannot run as typed is worse than no remediation: it sends the operator hunting for
a fault in their own typing, which is exactly what happened three separate times during the
2026-09-16 team-deployment UAT. The last one came out of the install doctor itself.

`;` is NOT the fix — it runs the second command even when the first fails. Two commands are
stated as two.

Stdlib only. Run directly:  python .claude/lib/test_operator_commands.py
A section reference like §11 is developer shorthand. To an operator it is a dead end:
it names a document they do not have, in place of the instruction they needed. Live
2026-09-16: \"set MAS_PUBLISH_DIR to a synced SharePoint library folder (§11)\" sent the operator
hunting for a folder that had never been created.

Exit 0 = clean; exit 1 = an operator-facing string still carries one.
"""
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Every file that builds a string an operator is expected to TYPE.
SCANNED = [
    ".claude/skills/system-smoke-test/doctor.py",
    ".claude/lib/provision.py",
    ".claude/lib/install_state.py",
    ".claude/lib/export_portable_assets.py",
    ".claude/lib/storyboard_frames.py",
    ".claude/lib/system_update.py",
    ".claude/lib/surface_freshness.py",
    ".claude/skills/asset-gallery/build-gallery.py",
    ".claude/hooks/post_tool_use.py",
    ".claude/hooks/stop.py",
]

# These files embed browser JavaScript in string literals, where `&&` is correct and required.
# The discriminator is that a SHELL instruction names a shell tool; JS never does.
SHELL_MARKERS = ("pip install", "python ", "git ", "playwright install", "npm ")

# The section-ref rule is scoped to the INSTALL/SETUP path only — the surface a new operator
# meets before they have any context, where a pointer to a document they do not have is a dead
# end rather than a shortcut. build-gallery is deliberately out of scope: it embeds a large
# browser-JS blob with its own UI text, a different surface for a different reader. A guard
# that over-reaches gets bypassed, and a bypassed guard protects nothing.
SECTION_SCANNED = [
    ".claude/skills/system-smoke-test/doctor.py",
    ".claude/lib/provision.py",
    ".claude/lib/install_state.py",
    ".claude/lib/system_update.py",
]


def offenders() -> list[str]:
    found: list[str] = []
    for rel in SCANNED:
        p = ROOT / rel
        if not p.is_file():
            continue
        src = p.read_text(encoding="utf-8")
        # module docstrings and comments are instructions too, but ast only sees the former;
        # check raw comment lines separately.
        for i, line in enumerate(src.splitlines(), 1):
            st = line.strip()
            if st.startswith("#") and "&&" in st and any(m in st for m in SHELL_MARKERS):
                found.append(f"{rel}:{i} (comment) {st[:90]}")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            found.append(f"{rel}: WILL NOT PARSE ({e})")
            continue
        docstrings = set()
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                b = getattr(n, "body", None)
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant)                         and isinstance(b[0].value.value, str):
                    docstrings.add(id(b[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if "&&" in v and any(m in v for m in SHELL_MARKERS):
                    found.append(f"{rel}:{node.lineno} {v.strip()[:90]}")
                if "§" in v and id(node) not in docstrings and rel in SECTION_SCANNED:
                    found.append(f"{rel}:{node.lineno} spec section ref in operator text: "
                                 f"{v.strip()[:80]}")
    return found


def main() -> int:
    print("operator-command guard — shell `&&` in printed instructions")
    bad = offenders()
    for b in bad:
        print(f"  FAIL  {b}")
    if bad:
        print(f"\nFAILED ({len(bad)}): PowerShell 5.1 rejects `&&`. State the commands as two, "
              "not joined — and not with `;`, which runs the second even when the first fails.")
        return 1
    print(f"  PASS  {len(SCANNED)} files clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
