---
name: setup
description: First-run setup for a fresh AI Studio instance. Triggers on "Setup Studio" (the canonical phrase) and any close variant or misspelling ("setup studio", "set up studio", "studio setup", "set up the studio"), as well as the older aliases "set yourself up", "set up the system", "first run", "get me started", or when an operator opens a freshly-downloaded instance and asks how to begin. Fire even if the operator's spelling or spacing is slightly off. Installs missing prerequisites, verifies the install, builds the operator surfaces + Studio home, and turns on backup. Do NOT trigger for campaign work or once setup is already complete (a tenant baseline exists).
---

# First-run setup

You are setting up a fresh instance for a (possibly non-technical) operator. Be plain-spoken
and encouraging. Run the steps in order; say in one line what each does *before* you run it.
You run the commands — never ask the operator to type pip/git commands themselves.

## 1. Show the licence and get agreement (once, before anything installs)

Show the operator this and get a clear yes before running anything:

> **Licence:** this software is for your own company's **internal business use** (PolyForm
> Internal Use) — including marketing your own business. It is **not** licensed for client /
> agency work, resale, SaaS/hosting, or redistribution without a separate commercial licence
> from Soundtrak Consulting. Full terms are in the `LICENSE` file. Do you agree? (yes / no)

If they don't agree, stop here. If they agree, continue — you'll pass `--accept-license` on the
next command so the install isn't blocked by the interactive licence prompt (which can't be
answered inside this non-interactive shell, so a plain `--fix` would silently halt).

## 2. Install + verify prerequisites

Run (the `--accept-license` records the agreement you just got, so `--fix` actually runs):

```
python .claude/skills/system-smoke-test/doctor.py --fix --accept-license
```

This installs the required libraries (`markdown`, `pyyaml`) plus the optional `playwright`
(gallery thumbnails only) and prints a health report. Required items must read `[ OK ]`;
`[WARN]` items (playwright, git, git-lfs) are optional — fine to leave. Don't go on until the
summary reads **READY**.

Two common blockers, both named by the doctor:
- **Windows** — if `python` isn't found at all, Python was installed without "Add to PATH".
  Point them back to the deployment guide.
- **macOS/Linux** — the doctor flags if only `python3` exists. The studio's hooks call the
  literal `python`, so alias/symlink `python`→python3 (the doctor prints the exact command)
  or the auto-update/backup engine silently won't run. `--fix` attempts this symlink for them.

## 2. Turn on backup (so they never lose work)

- If this folder isn't a git repo yet (`git rev-parse --git-dir` fails), run `git init`,
  then `git add -A` and commit `"Initial setup"`.
- Ask: "Do you have a private online repository to back up to (GitHub/GitLab), or shall we
  keep backups local for now?"
  - **Has one** → `git remote add origin <their-url>` then `git push -u origin main`.
  - **Not sure / no** → fine. Explain: their work is committed locally every session, and if
    this folder lives in OneDrive/Dropbox that's their offsite copy. They can connect an
    online backup later by re-running setup.
- The system auto-saves (commits, and pushes if a remote is connected) at the end of each
  session — they don't have to remember to save.

## 3. Build the operator surfaces + open the home page

The operator reviews everything on HTML pages, and bookmarks ONE of them. Make sure the
surfaces exist and are current, then open the home page. All idempotent — safe to re-run.

- Refresh the System dashboard:
  `python .claude/skills/system-manager/build-dashboard.py`
- Make sure the campaigns index exists and is current. If `campaigns/index.md` is missing,
  create it with an H1 plus the `<!-- CAMPAIGN_INDEX_AUTO -->` marker, then render:
  `python .claude/skills/render-html/render.py --markdown campaigns/index.md --template index --output campaigns/index.html`
  It renders a friendly "No campaigns yet" state — expected on a fresh install.
- Open their **Studio home** (`index.html` at the project root) so they can bookmark the one
  page linking the Campaign dashboard, the System dashboard and the guides:
  Windows `powershell -c "Start-Process index.html"` · macOS `open index.html` · Linux `xdg-open index.html`.

## 4. (Windows only) Enable the gallery quick-buttons — optional polish, never a blocker

On Windows, register the gallery quick-buttons so the gallery's "Open folder" / "Edit copy"
buttons open File Explorer / an editor. Say in ONE line what you're doing ("Enabling the
gallery quick-buttons — a Windows convenience, reversible any time"), then run:

```
powershell -ExecutionPolicy Bypass -File ".\.claude\skills\asset-gallery\protocol\setup-protocol.ps1"
```

- It writes one user-level registry key (no admin). It is OPTIONAL POLISH: if it errors, or the
  OS isn't Windows, SKIP it and carry on — it must NEVER block or fail READY.
- Tell the operator: the FIRST time they click a gallery button, the browser asks permission
  once and they tick "Always allow". You can't do that step for them.

## 5. Confirm + hand off

Run the doctor once more (no `--fix`) to confirm **READY**, then say:

> "You're set up — I've opened your Studio home; bookmark that one page. To begin, just say:
> **Onboard \<your business name\>** — I'll walk you through it."

## Do NOT do here

- Don't author any campaign or tenant content — that's Phase 0 (the Onboard step).
- Don't make the operator run commands themselves; you run them and report what happened.
