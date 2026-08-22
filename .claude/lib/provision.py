#!/usr/bin/env python3
"""
provision — set THIS machine up for a team deployment (team-deployment.md §16.2).

Every manual install step is a step someone gets wrong at the fifth organisation. This is
the one command an operator runs after cloning, so the sequence is identical every time:

  1. locate (or clone) the DATA repo
  2. write .claude/local/config.json so data_root() resolves to it
  3. register operator identity from git config (§4)
  4. run the install doctor and report READY / not

  python .claude/lib/provision.py --data <path to the data clone>
  python .claude/lib/provision.py --data-url <git url>          # clones it for you
  python .claude/lib/provision.py --status                      # what is this machine set to?

Idempotent: safe to re-run. Re-running after moving the data clone is how you re-point it.

NOT for a small-business install. A single-repo Seed needs none of this — code and data are
the same directory — and running it there is refused rather than silently writing a config
that pins data_root to the checkout it already resolves to.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude" / "lib"))

CONFIG_REL = Path(".claude") / "local" / "config.json"
# A directory only counts as a DATA root if it looks like one. Guessing wrong here means
# writing campaign data into a random folder, so require real evidence.
DATA_MARKERS = ("campaigns", "tenant-brand", "system", "config.yaml")


def _git(args: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                           capture_output=True, text=True, timeout=300)
        return r.returncode == 0, (r.stdout or r.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)


def looks_like_data_root(p: Path) -> tuple[bool, list[str]]:
    found = [m for m in DATA_MARKERS if (p / m).exists()]
    return (len(found) >= 2, found)


def write_config(data_root: Path, code_root: Path = ROOT) -> Path:
    """Write .claude/local/config.json. Merges into an existing file rather than clobbering
    it — other per-machine settings may live there."""
    cfg_path = code_root / CONFIG_REL
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if cfg_path.is_file():
        try:
            existing = json.loads(cfg_path.read_text(encoding="utf-8")) or {}
        except (OSError, ValueError):
            existing = {}          # unreadable: replaced, not merged
    if not isinstance(existing, dict):
        existing = {}
    existing["data_root"] = str(data_root.resolve())
    cfg_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return cfg_path


def operator_identity(code_root: Path = ROOT) -> str | None:
    """This operator's identity for attribution (§4) — their git email, which on an
    Entra-backed host is their work identity. None if git has no user configured."""
    ok, out = _git(["config", "user.email"], cwd=code_root)
    return out.strip() if ok and out.strip() else None


def clone_data(url: str, dest: Path) -> tuple[bool, str]:
    """Partial clone by default (§8) — blobs download on demand, so day-one checkout is
    metadata plus what the operator actually opens. Falls back to a full clone on any host
    that does not support filtering, rather than failing the install."""
    if dest.exists() and any(dest.iterdir()):
        return False, f"{dest} already exists and is not empty"
    dest.parent.mkdir(parents=True, exist_ok=True)
    ok, out = _git(["clone", "--filter=blob:none", url, str(dest)])
    if ok:
        return True, "cloned (partial: --filter=blob:none)"
    ok2, out2 = _git(["clone", url, str(dest)])
    return (ok2, "cloned (full — this host rejected --filter)" if ok2 else f"{out}\n{out2}")


def run_doctor(code_root: Path = ROOT) -> int:
    doctor = code_root / ".claude" / "skills" / "system-smoke-test" / "doctor.py"
    if not doctor.is_file():
        print("  (doctor.py not present in this checkout — skipping)")
        return 0
    # The doctor is INTERACTIVE on a fresh install (first-run licence gate) and writes
    # straight to the terminal. Flush our own buffered output first, or the licence prompt
    # appears ABOVE the steps that led to it and the operator cannot tell what is asking.
    sys.stdout.flush()
    sys.stderr.flush()
    return subprocess.run([sys.executable, str(doctor)], cwd=str(code_root)).returncode


def status(code_root: Path = ROOT) -> int:
    print("=== provisioning status ===")
    cfg = code_root / CONFIG_REL
    print(f"code root   : {code_root}")
    if cfg.is_file():
        try:
            print(f"config      : {cfg}\n              {json.loads(cfg.read_text(encoding='utf-8'))}")
        except (OSError, ValueError) as exc:
            print(f"config      : {cfg} — UNREADABLE ({exc})")
    else:
        print(f"config      : none at {cfg}")
    try:
        import repo_paths
        print(f"data root   : {repo_paths.data_root(code_root)}")
    except Exception as exc:  # noqa: BLE001 — status must report a broken root, not die on it
        print(f"data root   : UNRESOLVED — {type(exc).__name__}: {exc}")
    try:
        import deployment_profile as dp
        print(f"profile     : {dp.profile()}")
    except Exception as exc:  # noqa: BLE001
        print(f"profile     : UNRESOLVED — {type(exc).__name__}: {exc}")
    print(f"operator    : {operator_identity(code_root) or 'UNSET (git config user.email)'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="path to an existing DATA clone")
    ap.add_argument("--data-url", help="git URL of the DATA repo — clones it to --data")
    ap.add_argument("--status", action="store_true", help="report what this machine is set to")
    ap.add_argument("--skip-doctor", action="store_true", help="do not run the install doctor")
    a = ap.parse_args()

    if a.status or not (a.data or a.data_url):
        return status()

    print("=== provisioning this machine for a team deployment ===\n")

    if a.data_url:
        dest = Path(a.data).resolve() if a.data else (ROOT.parent / "data")
        print(f"[1/4] cloning DATA from {a.data_url}\n      -> {dest}")
        ok, msg = clone_data(a.data_url, dest)
        if not ok:
            print(f"      FAILED: {msg}", file=sys.stderr)
            return 1
        print(f"      {msg}")
        data = dest
    else:
        data = Path(a.data).expanduser().resolve()
        print(f"[1/4] using DATA at {data}")

    if not data.is_dir():
        print(f"      FAILED: {data} is not a directory", file=sys.stderr)
        return 1
    looks, found = looks_like_data_root(data)
    if not looks:
        # Refuse rather than guess. Pointing data_root at the wrong folder means campaign
        # and system writes land somewhere nobody looks.
        print(f"      FAILED: {data} does not look like a DATA root "
              f"(expected at least two of {', '.join(DATA_MARKERS)}; found "
              f"{', '.join(found) or 'none'})", file=sys.stderr)
        return 1
    print(f"      looks like a DATA root ({', '.join(found)})")

    if data.resolve() == ROOT.resolve():
        print("      FAILED: that is this checkout. A team deployment is TWO repos; a "
              "single-repo (small-business) install needs no provisioning.", file=sys.stderr)
        return 1

    print(f"\n[2/4] writing {CONFIG_REL}")
    print(f"      {write_config(data)}")

    print("\n[3/4] operator identity (attribution, §4)")
    who = operator_identity()
    if who:
        print(f"      {who}")
    else:
        print("      UNSET — run: git config --global user.email you@example.com\n"
              "      Attribution is required under `profile: team`; audit entries would "
              "otherwise say nothing about who acted.", file=sys.stderr)

    if a.skip_doctor:
        print("\n[4/4] doctor skipped (--skip-doctor)")
        return 0
    print("\n[4/4] install doctor")
    print("      On a fresh install this asks you to accept the licence before it will run.\n")
    rc = run_doctor()
    print("\nprovisioning complete." if rc == 0 else
          "\nprovisioning wrote its config, but the doctor reports blocking items above.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
