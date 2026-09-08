#!/usr/bin/env python3
"""Smoke test for deploy-static-folder.

Runs OFFLINE, no credentials. Proves the adapter conforms to the deploy-adapter contract:
  1. dry-run reads the deployment: block + emits a well-formed envelope (status dry_run),
  2. a REAL deploy into a temp folder actually copies the package + verifies index.html landed,
  3. no external network is touched (target is the local filesystem only).

Exits 0 on PASS.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
ADAPTER = HERE / "adapter.py"
REQUIRED_KEYS = {"status", "platform", "target", "verification", "operator_action", "notes"}


def make_fixture(root: Path) -> Path:
    """Build a throwaway asset deployment-package folder with asset.yaml + index.html."""
    asset = root / "asset"
    asset.mkdir()
    (asset / "asset.yaml").write_text(
        "deployment:\n"
        "  destination_type: static-site\n"
        "  platform: static-folder\n"
        "  publish_method: api\n"
        "  location: \"<deploy_root>\"\n"
        "  deployment_notes: \"fixture package\"\n"
        "  verification:\n"
        "    - check: \"Public URL returns 200\"\n"
        "      automated: false\n",
        encoding="utf-8",
    )
    (asset / "index.html").write_text("<!doctype html><title>fixture</title>ok", encoding="utf-8")
    (asset / "assets").mkdir()
    (asset / "assets" / "style.css").write_text("body{}", encoding="utf-8")
    return asset


def run(*args) -> tuple[int, dict | None, str]:
    proc = subprocess.run([sys.executable, str(ADAPTER), *args], capture_output=True, text=True)
    env = None
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pass
    return proc.returncode, env, proc.stderr + proc.stdout


def fail(msg: str) -> int:
    print(f"FAIL: {msg}")
    return 1


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        asset = make_fixture(root)

        # (1) dry-run
        rc, env, out = run("--asset", str(asset), "--smoke-test")
        if rc != 0 or env is None:
            return fail(f"dry-run exit {rc}\n{out}")
        if REQUIRED_KEYS - env.keys():
            return fail(f"dry-run envelope missing keys {REQUIRED_KEYS - env.keys()}")
        if env["status"] != "dry_run":
            return fail(f"dry-run status should be 'dry_run', got '{env['status']}'")

        # (2) real deploy into a temp destination
        dest = root / "webroot"
        rc, env, out = run("--asset", str(asset), "--dest", str(dest))
        if rc != 0 or env is None:
            return fail(f"deploy exit {rc}\n{out}")
        if REQUIRED_KEYS - env.keys():
            return fail(f"deploy envelope missing keys {REQUIRED_KEYS - env.keys()}")
        if env["status"] != "deployed":
            return fail(f"deploy status should be 'deployed', got '{env['status']}'")
        # (3) the automated verification check actually passed
        auto = env["verification"]["automated"]
        if not any(c["check"] == "index.html present at destination" and c["passed"] for c in auto):
            return fail(f"index.html-present check did not pass: {auto}")
        # and the files really landed on disk
        if not (dest / "index.html").exists():
            return fail("index.html was not copied to destination")
        if not (dest / "assets" / "style.css").exists():
            return fail("nested assets/ not copied to destination")

    print("PASS: deploy-static-folder — dry-run envelope OK, real copy deployed + verified, offline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
