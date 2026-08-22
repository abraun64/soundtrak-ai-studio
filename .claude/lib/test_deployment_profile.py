#!/usr/bin/env python3
"""
Regression tests for deployment_profile — the small-business|team toggle (SYS-028).

Stdlib only (no pytest). Run directly:
    python .claude/lib/test_deployment_profile.py

THE PROPERTY THAT MATTERS MOST: with no config.yaml, every axis returns the
small-business answer. A fresh Seed and the operator's master must be byte-identical to their
pre-toggle selves — if that regresses, a single-operator install silently starts demanding
attribution or refusing to commit its own surfaces.

Second: a present-but-BROKEN config raises rather than defaulting. An install that meant
to be a team deployment and quietly ran single-operator would skip claim locks and
attribution with nobody noticing.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deployment_profile as dp  # noqa: E402

_FAILED: list[str] = []


def check(name, got, want):
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got {got!r}, want {want!r}")
        _FAILED.append(name)


def check_raises(name, fn, exc=dp.ProfileError):
    try:
        r = fn()
    except exc:
        print(f"  PASS  {name}")
        return
    except Exception as other:  # noqa: BLE001
        print(f"  FAIL  {name} — raised {type(other).__name__}: {other}")
        _FAILED.append(name)
        return
    print(f"  FAIL  {name} — returned {r!r} instead of raising {exc.__name__}")
    _FAILED.append(name)


def _root(tmp: Path, name: str, body: str | None) -> Path:
    d = tmp / name
    d.mkdir(parents=True, exist_ok=True)
    if body is not None:
        (d / dp.CONFIG_NAME).write_text(body, encoding="utf-8")
    return d


def main() -> int:
    saved = os.environ.get(dp.ENV_VAR)
    os.environ.pop(dp.ENV_VAR, None)
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()

            print("\nNO CONFIG — must be byte-identical to the pre-toggle system")
            bare = _root(tmp, "bare", None)
            check("profile defaults to small-business", dp.profile(bare), dp.SMALL_BUSINESS)
            check("is_team() is False", dp.is_team(bare), False)
            for a in sorted(dp.AXES):
                check(f"axis {a} = small-business default",
                      dp.axis(a, bare), bool(dp.AXES[a][dp.SMALL_BUSINESS]))
            # The two that would be most damaging to flip silently:
            check("generated HTML still committed", dp.commit_generated_html(bare), True)
            check("claim locks off", dp.claim_locks_enabled(bare), False)

            print("\nTEAM PROFILE — the §12 axis table")
            team = _root(tmp, "team", "profile: team\n")
            check("profile is team", dp.profile(team), dp.TEAM)
            check("is_team() is True", dp.is_team(team), True)
            check("claim locks on", dp.claim_locks_enabled(team), True)
            check("attribution required", dp.attribution_required(team), True)
            check("generated HTML NOT committed", dp.commit_generated_html(team), False)
            check("sharepoint publishing on", dp.publish_to_sharepoint(team), True)

            print("\nEXPLICIT PROFILE — small-business stated outright")
            sb = _root(tmp, "sb", "profile: small-business\n")
            check("explicit small-business", dp.profile(sb), dp.SMALL_BUSINESS)
            check("claim locks still off", dp.claim_locks_enabled(sb), False)

            print("\nPER-AXIS OVERRIDES")
            ov = _root(tmp, "ov", "profile: team\noverrides:\n  compliance_gating: false\n")
            check("override wins over profile default", dp.compliance_gating(ov), False)
            check("un-overridden axis keeps team default", dp.claim_locks_enabled(ov), True)
            ov2 = _root(tmp, "ov2", "profile: small-business\noverrides:\n  claim_locks: true\n")
            check("override can turn an axis ON in small-business", dp.claim_locks_enabled(ov2), True)

            print("\nENV OVERRIDE")
            os.environ[dp.ENV_VAR] = dp.TEAM
            check("$MAS_PROFILE wins over file", dp.profile(sb), dp.TEAM)
            os.environ.pop(dp.ENV_VAR)

            print("\nFAIL LOUD — a broken config must never default silently")
            check_raises("unknown profile name raises",
                         lambda: dp.profile(_root(tmp, "badname", "profile: enterprise-plus\n")))
            check_raises("unknown override axis raises",
                         lambda: dp.load(_root(tmp, "badaxis", "profile: team\noverrides:\n  nope: true\n")))
            check_raises("non-mapping config raises",
                         lambda: dp.load(_root(tmp, "badshape", "- just\n- a list\n")))
            check_raises("non-mapping overrides raises",
                         lambda: dp.load(_root(tmp, "badov", "profile: team\noverrides: 3\n")))
            check_raises("unknown axis name raises", lambda: dp.axis("no_such_axis", bare), KeyError)

            print("\nTABLE-DRIVEN — the toggle changes DEFAULTS, not code paths")
            # Every named accessor must be a thin wrapper over axis(), so adding an axis
            # means adding a table row — never an `if profile == ...` somewhere else.
            # If an accessor ever grows bespoke logic, it diverges here and this fails.
            accessors = {
                "multi_operator": dp.multi_operator, "claim_locks": dp.claim_locks_enabled,
                "attribution_required": dp.attribution_required,
                "shared_data_remote": dp.shared_data_remote,
                "pinned_release_updates": dp.pinned_release_updates,
                "commit_generated_html": dp.commit_generated_html,
                "publish_to_sharepoint": dp.publish_to_sharepoint,
                "multi_approver": dp.multi_approver, "compliance_gating": dp.compliance_gating,
            }
            check("every axis has a named accessor", sorted(accessors), sorted(dp.AXES))
            drift = [n for n, fn in accessors.items()
                     for r in (team, bare, ov) if fn(r) != dp.axis(n, r)]
            check("accessors agree with axis() in every profile", drift, [])

            # And the two shapes must genuinely differ, or the toggle is decorative.
            differing = [a for a in dp.AXES if dp.AXES[a][dp.SMALL_BUSINESS] != dp.AXES[a][dp.TEAM]]
            check("all 9 axes differ between the shapes", len(differing), len(dp.AXES))
    finally:
        os.environ.pop(dp.ENV_VAR, None)
        if saved is not None:
            os.environ[dp.ENV_VAR] = saved

    print()
    if _FAILED:
        print(f"RESULT: {len(_FAILED)} FAILED — {', '.join(_FAILED)}")
        return 1
    print("RESULT: all deployment-profile tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
