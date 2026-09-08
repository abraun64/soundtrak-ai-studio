#!/usr/bin/env python3
"""
operator_identity — who did this? (team-deployment.md §4)

Every operator-facing surface says "the operator", singular. With N operators that is a
defect: an audit entry, an approval, or a claim that names nobody cannot be questioned,
credited, or followed up.

Identity resolves from `git config user.email`, which on an Entra-backed host IS the
person's work identity — so there is nothing extra to provision and nothing to keep in
sync with the organisation's directory.

    import operator_identity as who
    who.current()        # 'jane.smith@example.com' or None
    who.display()        # 'jane.smith'  — short, for a table cell
    who.stamp()          # 'jane.smith@example.com' or 'the operator' (never None)

THIS IS AN AUDIT TRAIL, NOT A PERMISSION SYSTEM. Decision #5 puts no access boundary
anywhere: everyone in a deployment can see and change everything. Identity answers "who
did this?", never "may they?".

Under `profile: small-business` attribution is not required, and stamp() falls back to
"the operator" — exactly the string the surfaces use today, so nothing changes for a
single-operator install. Under `profile: team` a missing identity is a doctor FAIL.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

ENV_VAR = "MAS_OPERATOR"          # explicit override; also the test hook
ANONYMOUS = "the operator"        # what every surface says today


def _git_email(cwd: Path | None = None) -> str | None:
    try:
        r = subprocess.run(["git", "config", "user.email"],
                           cwd=str(cwd or ROOT), capture_output=True, text=True, timeout=10)
        v = (r.stdout or "").strip()
        return v or None
    except (OSError, subprocess.SubprocessError):
        return None


def current(cwd: Path | None = None) -> str | None:
    """This operator's identity, or None if unset. $MAS_OPERATOR wins over git config."""
    env = os.environ.get(ENV_VAR, "").strip()
    if env:
        return env
    return _git_email(cwd)


def display(cwd: Path | None = None) -> str:
    """Short form for a table cell: the local part of the email. Surfaces are read at a
    glance, and a full address in every row of a To Do table is noise."""
    who = current(cwd)
    if not who:
        return ANONYMOUS
    return who.split("@", 1)[0] if "@" in who else who


def stamp(cwd: Path | None = None) -> str:
    """Identity to write into a record. NEVER None — a record that cannot name an actor
    still needs a value, and `the operator` is what the surfaces already say."""
    return current(cwd) or ANONYMOUS


def required() -> bool:
    """Does this deployment REQUIRE attribution? (profile axis, §12.)"""
    try:
        import deployment_profile as dp
        return dp.attribution_required()
    except Exception:  # noqa: BLE001 — an unresolvable profile must not break a write path
        return False


def check() -> tuple[bool, str]:
    """(ok, message) for the doctor and the Stop hook. Unset identity is only a failure
    where the deployment actually requires attribution."""
    who = current()
    if who:
        return True, who
    if required():
        return False, ("operator identity UNSET and `profile: team` requires attribution - "
                       "run: git config --global user.email you@example.com")
    return True, f"unset (not required under this profile; records say '{ANONYMOUS}')"


if __name__ == "__main__":
    ok, msg = check()
    print(f"operator: {stamp()}")
    print(f"display : {display()}")
    print(f"required: {required()}")
    print(f"check   : {'OK' if ok else 'FAIL'} - {msg}")
    sys.exit(0 if ok else 1)
