#!/usr/bin/env python3
"""Regression tests for the Stop hook's auto_publish() gate.

Stdlib only. Run directly:  python .claude/lib/test_auto_publish.py

The read-only SharePoint copy is the interface an organisation reads WITHOUT Claude Code, so
publishing cannot depend on someone remembering to run a script. But a hook that fires on every
session end has to be provably inert everywhere it is not wanted:

  - a single-operator install must never publish anything;
  - an operator who is not the nominated publisher must never publish;
  - the publisher machine must publish;
  - a target that has vanished (SharePoint un-synced, folder renamed) must be LOUD, because
    the audience downstream cannot check anything themselves;
  - nothing here may ever raise, since it runs inside the hook that also saves the work.
"""
from __future__ import annotations
import io
import os
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

_FAILED: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        _FAILED.append(name)


def _run(env_value, publish_impl=None, profile_on=True):
    """Call auto_publish() with MAS_PUBLISH_DIR set to env_value; return (called, stderr)."""
    import stop
    import publish_surfaces
    import deployment_profile as dp

    calls = []
    saved_env = os.environ.get("MAS_PUBLISH_DIR")
    saved_pub = publish_surfaces.publish
    saved_prof = dp.publish_to_sharepoint
    if env_value is None:
        os.environ.pop("MAS_PUBLISH_DIR", None)
    else:
        os.environ["MAS_PUBLISH_DIR"] = env_value

    def fake_publish(dest, *a, **k):
        calls.append(dest)
        if publish_impl:
            return publish_impl(dest)
        return {"total": 1, "copied": 1, "skipped": 0}

    publish_surfaces.publish = fake_publish
    dp.publish_to_sharepoint = lambda: profile_on
    buf = io.StringIO()
    try:
        with redirect_stderr(buf):
            stop.auto_publish()
    finally:
        publish_surfaces.publish = saved_pub
        dp.publish_to_sharepoint = saved_prof
        if saved_env is None:
            os.environ.pop("MAS_PUBLISH_DIR", None)
        else:
            os.environ["MAS_PUBLISH_DIR"] = saved_env
    return calls, buf.getvalue()


def main() -> int:
    print("auto_publish gate tests")
    with tempfile.TemporaryDirectory() as td:
        real = Path(td) / "synced"
        real.mkdir()

        calls, err = _run(None)
        check("unset MAS_PUBLISH_DIR publishes nothing (every normal operator)",
              not calls and not err, f"calls={calls} err={err!r}")

        calls, err = _run("   ")
        check("blank MAS_PUBLISH_DIR publishes nothing", not calls, f"calls={calls}")

        calls, err = _run(str(real), profile_on=False)
        check("profile with publishing off publishes nothing", not calls, f"calls={calls}")

        calls, err = _run(str(real))
        check("the publisher machine DOES publish", len(calls) == 1, f"calls={calls}")
        check("a publish is reported to the operator", "published" in err, repr(err))

        gone = Path(td) / "was-synced-until-tuesday"
        calls, err = _run(str(gone))
        check("a vanished target publishes nothing", not calls, f"calls={calls}")
        check("a vanished target is LOUD", "PUBLISH TARGET MISSING" in err, repr(err))

        def boom(dest):
            raise OSError("sync client locked the folder")
        calls, err = _run(str(real), publish_impl=boom)
        check("a failing publish never raises out of the hook", True)
        check("a failing publish is LOUD", "PUBLISH FAILED" in err, repr(err))

        calls, err = _run(str(real), publish_impl=lambda d: {"total": 3, "copied": 0, "skipped": 3})
        check("a no-op publish stays quiet", "published" not in err, repr(err))

    if _FAILED:
        print(f"\nFAILED ({len(_FAILED)}): " + ", ".join(_FAILED))
        return 1
    print("\nAll auto_publish gate tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
