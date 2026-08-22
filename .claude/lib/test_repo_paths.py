#!/usr/bin/env python3
"""
Regression tests for repo_paths.data_root() — the resolver every tool uses to find the
DATA dirs (campaigns/, system/, tenant-brand/).

Stdlib only (no pytest — it isn't installed). Run directly:
    python .claude/lib/test_repo_paths.py
Exit 0 = all pass; exit 1 = one or more failed (details printed).

WHY THIS EXISTS. data_root() gained an explicit override for the team deployment
(docs/specs/team-deployment.md §3), where DATA is a separate repo cloned per operator.
The override is the dangerous kind of change: get it wrong and a tool writes campaign or
system data into the CODE checkout, where it would then ride a code release. That is the
worktree blind spot (SYS-103) in a worse form.

So these tests assert the two properties that matter:
  1. WITH NO CONFIGURATION, behaviour is unchanged — the single-operator install must not
     move at all. (Tests 1-2.)
  2. A CONFIGURED-BUT-BROKEN root FAILS LOUD rather than falling back to the checkout.
     (Tests 5-7 — the "prove the assertion can fail" half.)

Read-only: every test builds a synthetic tree in a temp dir. Nothing on OneDrive is touched.
The MAS_DATA_ROOT env var is saved and restored around the whole run.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repo_paths as rp  # noqa: E402

_FAILED: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}\n          got:  {got!r}\n          want: {want!r}")
        _FAILED.append(name)


def check_raises(name: str, fn, exc=rp.DataRootError) -> None:
    try:
        result = fn()
    except exc:
        print(f"  PASS  {name}")
        return
    except Exception as other:  # noqa: BLE001 — a wrong exception type is a real failure
        print(f"  FAIL  {name}\n          raised {type(other).__name__}: {other}")
        _FAILED.append(name)
        return
    print(f"  FAIL  {name}\n          returned {result!r} instead of raising {exc.__name__}")
    _FAILED.append(name)


def _checkout(tmp: Path, name: str) -> Path:
    """A bare stand-in for a code checkout: just a dir with a .claude/ in it."""
    root = tmp / name
    (root / ".claude").mkdir(parents=True)
    return root


def _write_config(root: Path, payload) -> Path:
    cfg = root / rp.CONFIG_REL
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
    return cfg


def main() -> int:
    saved_env = os.environ.get(rp.ENV_VAR)
    os.environ.pop(rp.ENV_VAR, None)
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td).resolve()

            # ---- 1-2. UNCONFIGURED: behaviour must not move -------------------------
            print("\nUNCONFIGURED — the single-operator install must be untouched")

            plain = _checkout(tmp, "plain-checkout")
            check("bare checkout resolves to itself", rp.data_root(plain), plain)
            check("configured_data_root() is None when nothing is set",
                  rp.configured_data_root(plain), None)

            # The legacy in-tree worktree layout must still walk up to its main checkout.
            main_co = _checkout(tmp, "main-checkout")
            wt = main_co / ".claude" / "worktrees" / "some-branch"
            wt.mkdir(parents=True)
            check("in-tree worktree still walks up to main", rp.data_root(wt), main_co)

            # ---- 3-4. EXPLICIT config: env var and config.json ----------------------
            print("\nEXPLICIT — env var and per-machine config")

            data = tmp / "data-repo"
            data.mkdir()

            _write_config(plain, {"data_root": str(data)})
            check("config.json data_root is honoured", rp.data_root(plain), data)

            other = tmp / "other-data"
            other.mkdir()
            os.environ[rp.ENV_VAR] = str(other)
            check("env var wins over config.json", rp.data_root(plain), other)
            os.environ.pop(rp.ENV_VAR)

            # A worktree must inherit the MACHINE's config from the main checkout,
            # not silently fall back to the walk — the SYS-103 blind-spot class.
            _write_config(main_co, {"data_root": str(data)})
            check("worktree inherits main checkout's config", rp.data_root(wt), data)

            # ---- 5-7. FAIL LOUD: prove the guard can actually fail -------------------
            print("\nFAIL LOUD — a configured-but-broken root must never fall back")

            broken = _checkout(tmp, "broken-config")
            _write_config(broken, {"data_root": str(tmp / "does-not-exist")})
            check_raises("config pointing at a missing dir raises", lambda: rp.data_root(broken))

            malformed = _checkout(tmp, "malformed-config")
            _write_config(malformed, "{not valid json")
            check_raises("unparseable config.json raises", lambda: rp.data_root(malformed))

            os.environ[rp.ENV_VAR] = str(tmp / "also-missing")
            check_raises("env var pointing at a missing dir raises", lambda: rp.data_root(plain))
            os.environ.pop(rp.ENV_VAR)

            # An empty / absent value is "unset", not "broken" — it must fall through
            # to the normal walk rather than raising.
            empty = _checkout(tmp, "empty-config")
            _write_config(empty, {"note": "no data_root key here"})
            check("config without a data_root key falls through", rp.data_root(empty), empty)
    finally:
        os.environ.pop(rp.ENV_VAR, None)
        if saved_env is not None:
            os.environ[rp.ENV_VAR] = saved_env

    print()
    if _FAILED:
        print(f"RESULT: {len(_FAILED)} FAILED — {', '.join(_FAILED)}")
        return 1
    print("RESULT: all repo_paths tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
