---
name: join-studio
description: |
  Set this machine up to work in a team AI Marketing Studio, without the operator
  ever opening a terminal.

  Use when someone says "set up my studio", "join the studio", "connect me to the
  team studio", "finish my setup", "I'm new, get me started", or when they have two
  clone addresses from IT and do not know what to do with them. Also use to REPAIR a
  setup: "my studio is broken", "fix my setup", "I can't see any campaigns",
  "my studio is pointed at the wrong folder", "run the health check".

  Also handles UPDATES: "check for studio updates", "update the studio", "is there a
  new version", "roll back the studio".

  The operator is a marketer, not an engineer. They will never be asked to type a
  shell command, and never handed one to paste elsewhere.
---

# Join a team Studio

## Why this skill exists

The obvious way to spare a marketer the terminal is to hand them a double-clickable
script. **Do not do that, and do not propose it.** A script that installs software and
clones repositories, distributed on SharePoint, is indistinguishable from the attack it
imitates: unsigned, carrying Mark-of-the-Web, blocked by most Defender ASR rules, and it
trains staff to double-click executables from a shared drive. It also creates a trust
boundary nobody in IT reviewed.

Claude Code is already the approved, installed, audited tool that runs commands for the
operator. That makes it the right place for setup, and it needs no new artifact at all.
**You** run the commands. The operator watches, and answers questions in plain English.

## What the operator must have first

IT deploys these through Intune / Company Portal (`deploy/studio-prerequisites.winget.yaml`):
Python 3.12, Git, Git LFS, Claude Code, FFmpeg. If something is missing, say which one and
tell them to get it from **Company Portal**, or to ask IT. Do not install system software
yourself and do not walk them through a manual installer — on a managed device that is IT's
job, and attempting it will usually fail on permissions anyway.

## What you need from them

Two clone addresses, from whoever set up the organisation:

- code, ending `AI-marketing-studio-code.git` — they need **Read**
- data, ending `AI-marketing-studio-data.git` — they need **Write**

Ask for both in one message. If they only have one, stop and have them get the other; do
not guess an address by editing the one you have.

## Run it

1. **Pick a location.** Default `C:\Studio`. It must NOT be inside OneDrive — the two
   folders are already synchronised by Git, and OneDrive on top of that causes conflicts
   and slowdowns. If their chosen path is under OneDrive, say why and offer `C:\Studio`.

2. **Clone both.** Into `<location>\code` and `<location>\data`.
   A sign-in window appears on the first clone. Tell them BEFORE it appears that it is
   coming, that it is Git asking, and that they must use **the work account their access
   was granted to**. An unexpected credential prompt is exactly what phishing looks like;
   they should never have to guess whether one is genuine.

3. **If you see `Repository not found`**, do not report it as a missing repository. It is
   ambiguous by design — GitHub returns it identically for a wrong account, access not yet
   granted, and a wrong address, so that private repositories cannot be enumerated. In
   practice it is usually a personal GitHub already cached on the machine. Clear it with
   `git credential-manager github logout` and clone again. On Azure DevOps, remove the
   `git:` entries in Windows Credential Manager.

4. **Provision**, from inside the code folder:
   `python .claude/lib/provision.py --data ../data --full`
   `--full` is right for an organisation: it adds playwright and chromium so gallery
   thumbnails work from day one, instead of failing mid-campaign the first time someone
   builds a gallery.

5. **Identity.** Provisioning records who they are from `git config user.email`. If unset,
   ask for their work email and set it — attribution is required under `profile: team`, and
   without it every approval in the audit trail names nobody. On a domain-joined machine
   `whoami /upn` usually gives the right address; offer it and let them confirm rather than
   assuming it.

6. **Read the doctor back to them in their words.** Do not paste raw output and leave them
   to interpret it. `[FAIL]` is a blocker, `[WARN]` is usually ignorable — say which is
   which, and what you are doing about each.

7. **Brand setup.** If starting a campaign later reports `BLOCKED - Phase 0 incomplete`,
   that is not a fault and not their setup: the organisation's brand foundation has not been
   done yet. It happens once per organisation, not once per person.

## Hand over the folder switch — do not skip this

You will normally be running in the PARENT folder (e.g. `C:\Studio`), because that is where the
operator opened Claude Code so you could clone into it. Everything that makes this the Studio —
the skills, the hooks, the dashboards, the automatic saving — only loads when the **`code`**
folder is the open project. In the parent folder nothing happens and nothing explains why.

So end by telling them, in these terms:

1. click **+ New** for a fresh chat;
2. **Local** → **Select folder** → choose the `code` folder;
3. say **yes** to trusting it;
4. then ask for **"open my studio home"** and bookmark the page that opens — it is the one link
   back to their dashboards and guides.

Say plainly that this is a one-time switch and that it is easy to miss. Do not assume they will
infer it from the fact that you cloned into a subfolder.

They never open the `data` folder themselves; the Studio writes to it for them.

## Repairing an existing setup

"fix my setup" / "my studio is broken" / "I can't see any campaigns" / "my studio is pointed at
the wrong folder". Work in this order, and say what you find at each step rather than silently
moving on:

1. `python .claude/lib/install_state.py` — if it reports `unprovisioned-team`, that IS the fault.
   Re-provision; do not run first-run setup.
2. `python .claude/lib/provision.py --status` — is the data root where they think it is?
3. `python .claude/skills/system-smoke-test/doctor.py --fix` — installs anything missing and
   re-checks. Note that on older installs `--fix` also pulls chromium (~150 MB); say so first.
4. Read the result back in plain English, and name explicitly anything that is IT's to fix
   (missing system software) or the administrator's (access, an unpublished release), rather
   than leaving the operator to work out whose problem it is.

## Updating to a new version

`.claude/lib/system_update.py`, run from the code repo. `--check` (current version, what is
available, and the release notes for it), `--apply` (optionally `--to vX.Y.Z`), `--rollback`.

- **Always show what changed before applying.** An update whose contents the operator cannot read
  is one they postpone forever. `--check` prints the CHANGELOG for exactly the releases they do
  not yet have.
- **Never apply without them saying so.** Taking a version is their decision; the whole pinned-tag
  design exists so the system cannot change under someone mid-campaign.
- **"no release tags found" is usually not their problem.** Each organisation has its own copy of
  the code, and an administrator must publish the release into it before anyone is offered it. Say
  that, rather than implying they are up to date.
- **A dirty working tree refusal is a real signal, not an obstacle.** The code repo is pull-only,
  so nothing the operator does should ever modify it. Report it and say it is worth understanding;
  never offer to discard the changes.
- Their campaigns and brands live in the DATA repo and are untouched by any of this. Say so — it
  is the first thing people worry about.

## Finish

Tell them setup is done, that their work saves and reaches colleagues automatically at the
end of each session, and that they can start with **"what's awaiting me"**. Point them at
the Operator guide for how a campaign actually runs.

Never end by giving them commands to run themselves. If something could not be completed,
say precisely what is blocked and who unblocks it — IT, or whoever set up the organisation.
