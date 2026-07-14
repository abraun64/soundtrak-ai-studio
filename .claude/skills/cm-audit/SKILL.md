---
name: cm-audit
description: |
  CM self-audit — verify CM is actually doing its job on the live operator surfaces.

  Read-only check that answers "do you know they're doing it?" for the machine-checkable
  slice of the CM responsibility catalog: are the operator surfaces PRESENT, CURRENT
  (rendered at least as recently as their data sources), and is the tenant-layer data
  CM must maintain (campaign.yaml `tenant:` · tenant.yaml · tenant home) in place?

  Complements the system smoke test (presence) by adding CURRENCY + tenant-layer +
  per-campaign data-contract checks. Does NOT judge content quality.

  TRIGGER when: after CM-orchestrated turns; before an end-to-end test or a demo;
  when a surface "feels behind"; periodic check. Common phrasings: "run the cm audit",
  "are the surfaces current?", "is CM keeping things up to date?".

  DO NOT TRIGGER for: content-quality review; single-asset status (use the dashboard).
---

# CM Self-Audit

Run it:

```
python .claude/skills/cm-audit/cm_audit.py
```

Read-only, < 15s, stdlib + PyYAML. Prints a traffic-light report grouped per campaign / cross-surface / per tenant, and exits 0 (all green) or 1 (any finding, reason inline). **When invoked, run that command and relay the report** — don't just describe the checks.

## What it checks

**Per active campaign**
- canonical `dashboard.html` present (the surface the index links to)
- `dashboard.html` **current** — its mtime ≥ `<slug>.md` + `campaign.yaml` (a newer source = CM changed state without re-rendering)
- dashboard md carries a `Last updated` stamp
- `gallery.html` present
- `campaign.yaml` has `tenant:` set (groups it under a tenant; powers cross-links)
- `gallery-config.yaml` present (else the gallery degrades to a generic skeleton)

**Cross-surface**
- `index.html` present + current vs the newest `campaign.yaml`
- `tasks.html` present

**Per tenant** (each `tenant-brand/<tenant>.yaml` identity file)
- `<tenant>-home.html` present
- tenant home **current** — mtime ≥ every owned campaign's `campaign.yaml` (a newer campaign yaml = the home's phase pills are stale)

**Surface-honesty (SYS-059)** — a green tick "✅" on an operator surface may sit ONLY on a genuinely-gated artifact. Flags any ✅ *attached to an artifact name* that is an ungated INPUT (Insight Brief, concept trio/menu, moodboard, editorial backlog, research, influencer targets …). The gated set that MAY carry ✅: the **Brief**, the **Selected concept** (the pick), the **Plan**, **finished assets**, and **Phase-5/6 plans**. Scans, per campaign, `<slug>.md` (dashboard phase table + artifact links) and `campaign.yaml` (`phases[].artifacts[].title`). Only a ✅ inside a markdown link's visible text or a yaml `title:` is inspected — a bare ✅ in a status cell / history row / budget line is a verdict marker, not an artifact approval, and is out of scope. Enforces docs/workflow.md "CM rules of orchestration" rule 8; marking an ungated input ✅ fabricates an operator approval and erodes gallery trust.

Run the guard standalone (focused report):

```
python .claude/skills/cm-audit/surface_honesty.py
```

Gated/ungated logic is a small allow/deny pattern list in `surface_honesty.py` (`GATED_PATTERNS` / `UNGATED_PATTERNS`) — deny wins over allow, and an unrecognised name fails **open** (not flagged) so the guard never fabricates a false violation on a novel artifact; extend the deny list when a new input type appears. Unit test: `python .claude/skills/cm-audit/test_surface_honesty.py`.

## Currency principle

A render should be **≥ the mtime of its data sources**. Comparing render-vs-source (not render-vs-any-file) means re-render noise doesn't trip it — only a genuine "source changed, render didn't follow" does. That's the exact stale-operator-surface failure the responsibility audit found.

## Not yet automated (catalog items with no check)

Phase-0 orchestration · per-step-brief slicing · governance/brand sequence · cost-ledger discipline · graduate-then-cite · cold-start recovery · the interaction modes. These are only observable during a CM run — see `docs/specs/_proposals/cm-responsibility-audit.md` for the full catalog.
