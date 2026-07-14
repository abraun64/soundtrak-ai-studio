# Investigation Reference — deploy-static-folder

**Target**: a local static-hosting folder (a filesystem directory a static host serves from).
**Captured**: 2026-07-14 (reference adapter for the deploy-adapter contract, SYS-066).

This is the simplest genuinely-real deploy target in the system, chosen to prove the contract
end-to-end without any network or credentials. The "target" is a directory that some static
host serves: a synced folder (OneDrive/Dropbox public dir), a mounted web-root on a box, a
CDN/edge drop directory, or a git-worktree that a downstream push publishes. From this adapter's
point of view they are all "copy the deployment package into folder X".

## Deploy mechanism

A plain recursive filesystem copy. The unit of deploy is the asset's **self-contained HTML
deployment package** — the folder that holds `index.html` plus its sibling `assets/` etc.
(defined in `docs/specs/asset.md` §84-107: "that folder IS the deployment package"). The adapter
copies every entry of the package folder into the destination `deploy_root` (files with
`shutil.copy2`, subfolders with `shutil.copytree(dirs_exist_ok=True)`), then confirms
`index.html` exists at the destination.

- Source: `--asset <package-folder>` (the folder containing `index.html`; may also hold `asset.yaml`).
- Destination: `--dest <deploy_root>` (in real use, inherited from
  `integrations.yaml#platforms.static-folder.defaults.deploy_root`).

## Auth model + env-vars

**None.** The target is the local filesystem; no credentials. `REQUIRED_ENV = []`. The empty-env
check is kept in the code path so the control flow is identical to a credentialled adapter (an
unset required var would ABORT + fall back to deploy-cookbook — there just are no required vars
here).

## File-layout shape

Destination after a deploy mirrors the package:

```
<deploy_root>/
  index.html
  assets/…            (and any other package contents, copied recursively)
```

Idempotent: re-running overwrites in place (`dirs_exist_ok=True`, `copy2` overwrites). No stale
files are pruned — a removed source file is NOT deleted from the destination (documented gotcha).

## Verification signals — how you know it landed

- **Automated** (run by the adapter): `index.html` exists at `<deploy_root>`. This maps to the
  contract's automated-verification slot and drives the envelope `status`
  (`deployed` if it passes, `failed` if not).
- **Manual** (surfaced to operator): any `deployment.verification` entry from the asset.yaml —
  e.g. "Public URL returns 200 with expected title" — since the adapter can't know the public URL
  of an arbitrary static host.

## Known gotchas

- **No prune on redeploy.** Files removed from the source stay at the destination. Clean-deploy
  would need an explicit wipe of `deploy_root` first (not done, to avoid destroying an unrelated
  dir passed by mistake).
- **Package must contain `index.html`.** A real deploy ABORTs (exit 4) if it doesn't — that's the
  "is this actually a deployable static package?" guard.
- **`--dest` is the whole web-root.** Contents are copied INTO it, not into a subfolder — pass a
  per-asset subfolder if you don't want assets from multiple deploys mingling.

## Links

- `docs/specs/asset.md` §84-107 — the HTML deployment-package folder contract this consumes.
- `docs/specs/integrations.md` §`netlify`/`github` — sibling static-site targets whose
  `deploy_root`/branch defaults this adapter's `--dest` generalises.
- Python `shutil` docs — `copytree` / `copy2` semantics.
