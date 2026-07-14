#!/usr/bin/env python3
"""deploy-static-folder adapter.

Reference implementation of the deploy-adapter contract
(.claude/skills/deploy-cookbook/ADAPTER-CONTRACT.md).

Deploys an asset's self-contained HTML deployment package (the folder containing index.html,
per docs/specs/asset.md §84-107) to a local static-hosting folder — a plain filesystem copy.
Real, offline, verifiable: after the copy it confirms index.html landed at the destination.

This is the simplest genuinely-real deploy target: no network, no credentials, but the same
input→deploy→verify→envelope flow every adapter follows. The destination folder stands in for
any static host that publishes a directory (a synced folder, a mounted web-root, a CDN drop dir).

INPUTS
  --asset <path>     path to the asset's deployment-package folder (the one holding index.html),
                     OR a folder containing a sibling asset.yaml with a deployment: block.
  --dest  <path>     target static-hosting folder to deploy INTO. In real use this is inherited
                     from integrations.yaml#platforms.static-folder.defaults.deploy_root; here it
                     is passed explicitly. Optional under --smoke-test (a temp dir is used).
  --smoke-test/--dry-run   plan + verify only, NO copy. Envelope status = "dry_run".

OUTPUT
  Adapter envelope (JSON) to stdout — see ADAPTER-CONTRACT.md.

Env-vars: none (offline target). REQUIRED_ENV is empty by design; the check is kept so the
control flow matches credentialled adapters exactly.
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REQUIRED_ENV = []  # offline target — no credentials


def find_asset_yaml(asset_path: Path):
    """Return the asset.yaml Path for the given asset folder, or None."""
    if asset_path.is_dir():
        cand = asset_path / "asset.yaml"
        if cand.exists():
            return cand
    return None


def load_deployment_block(asset_path: Path) -> dict:
    """Read the deployment: block from a sibling asset.yaml, if present."""
    ay = find_asset_yaml(asset_path)
    if ay and yaml is not None:
        data = yaml.safe_load(ay.read_text(encoding="utf-8")) or {}
        return data.get("deployment", {}) or {}
    return {}


def resolve_package_root(asset_path: Path) -> Path:
    """The folder we deploy is the one containing index.html.

    If the asset path already holds index.html, that's the package. Otherwise if it holds an
    index.html anywhere directly beneath it, use the asset path itself (the whole folder is the
    package, per asset.md: 'that folder IS the deployment package').
    """
    if (asset_path / "index.html").exists():
        return asset_path
    return asset_path  # deploy the folder as-is; verification will catch a missing index.html


def run_verification(dep: dict, deployed_root: Path | None) -> dict:
    """Execute automated checks; collect manual ones for the operator."""
    automated, manual = [], []
    # Contract-standard automated check for a static-folder deploy: index.html present at dest.
    if deployed_root is not None:
        landed = (deployed_root / "index.html").exists()
        automated.append({"check": "index.html present at destination", "passed": bool(landed)})
    # Any asset-declared verification entries.
    for entry in dep.get("verification", []) or []:
        check = entry.get("check", "")
        if entry.get("automated"):
            # We can only truly automate checks we understand; report unknown automated
            # checks as passed=False-unknown -> surface as manual to be safe.
            manual.append({"check": check, "operator_action": f"confirm: {check}"})
        else:
            manual.append({"check": check, "operator_action": check})
    return {"automated": automated, "manual": manual}


def build_envelope(status, target, verification, notes, operator_action=""):
    return {
        "status": status,
        "platform": "static-folder",
        "target": str(target),
        "verification": verification,
        "operator_action": operator_action,
        "notes": notes,
    }


def deploy(package_root: Path, dest_root: Path) -> Path:
    """Copy the package folder's contents into dest_root. Returns dest_root."""
    dest_root.mkdir(parents=True, exist_ok=True)
    for item in package_root.iterdir():
        target = dest_root / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    return dest_root


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True)
    ap.add_argument("--dest", default=None)
    ap.add_argument("--smoke-test", "--dry-run", dest="dry", action="store_true")
    args = ap.parse_args()

    asset_path = Path(args.asset)
    if not asset_path.exists():
        print(f"ABORT: asset path does not exist: {asset_path}", file=sys.stderr)
        return 2

    dep = load_deployment_block(asset_path)
    package_root = resolve_package_root(asset_path)
    notes = dep.get("deployment_notes", "") or ""

    if args.dry:
        # Plan + verify against the SOURCE package (index.html should exist to be deployable).
        verification = run_verification(dep, package_root)
        env = build_envelope(
            status="dry_run",
            target=f"[dry-run] {args.dest or dep.get('location', '<deploy_root>')}",
            verification=verification,
            notes=notes,
        )
        print(json.dumps(env, indent=2))
        return 0

    # ---- REAL deploy ----
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        print(f"ABORT: env-vars unset {missing}; fall back to deploy-cookbook", file=sys.stderr)
        return 3

    dest = args.dest or dep.get("location")
    if not dest:
        print("ABORT: no --dest and no deployment.location; nowhere to deploy", file=sys.stderr)
        return 2
    dest_root = Path(dest)

    if not (package_root / "index.html").exists():
        print(f"ABORT: no index.html in package {package_root}; not a deployable static package",
              file=sys.stderr)
        return 4

    deployed = deploy(package_root, dest_root)
    verification = run_verification(dep, deployed)
    all_auto_pass = all(c.get("passed") for c in verification["automated"])
    env = build_envelope(
        status="deployed" if all_auto_pass else "failed",
        target=deployed,
        verification=verification,
        notes=notes,
        operator_action=f"Static package deployed to {deployed}. Point the host at this folder.",
    )
    print(json.dumps(env, indent=2))
    return 0 if all_auto_pass else 1


if __name__ == "__main__":
    sys.exit(main())
