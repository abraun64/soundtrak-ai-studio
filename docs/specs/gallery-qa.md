# Gallery pre-surface QA — checklist

**Spec version**: v1 · 2026-06-15 (extracted from CM SKILL.md — operator flagged it as "overkill" inline; it's a real check, just not skill-body material).

CM runs this **before surfacing any Phase-4 asset to the operator**. The operator should never be the one who catches a gallery issue — that's CM's job. Read the asset's `asset.yaml` and verify each row against the Plan's **Review shape** + **Copy file** columns.

| Check | Verify | Fix if wrong |
|---|---|---|
| **Status** | `status: "For Human Review"` in asset.yaml | set it (the badge depends on it) |
| **Rationale** | `rationale:` written (1–3 sentences: what it is + why) | write from the Plan asset description (gallery modal shows it first) |
| **Review-shape match** | files in asset.yaml match the Plan shape — `output` → 1 tile · `template [+N]` → 1 `type: Template` + N `type: Instance` · `variant-comp [N×M]` → N comp tiles, all production instances `ship: false` | fix `type:` + `ship: false` on instances |
| **Copy file** | if Plan Copy file ≠ `none`: `copy_file:` points to an existing file | declare it (operator needs the edit button) |
| **Production file** | binary the operator downloads (PDF/PPTX/DOCX): `production_file:` on the PNG/HTML tile | add `production_file:` |
| **View source** | thumbnail file ≠ shipped deliverable: `view_source:` on the thumbnail entry | add `view_source:` |
| **Tile count** | count expected tiles — `variant-comp [6×4]` = 3–6 comp tiles (NOT 42); `template [+6]` = 1+6; `output` = 1 | `ship: false` on over-tiling files |
| **Scroll check** | any multi-section "View in full" HTML scrolls to the bottom (no `overflow: hidden` on body from copied inner-frame CSS) | add `overflow: auto` to outer body |
| **Deploy instructions** | any HTML web-page asset has a deploy cookbook (`cookbooks/deploy.md` / `deploy.md`) | author one before surfacing |
| **Copy surface (v3)** | every copy-bearing asset resolves a copy-review md (top-level `copy_file:`, a `copy.md`, or the primary prose `.md`; HTML-only ships a text extract). A build **WARNING** = unmet. | declare `copy_file:` / add a `copy.md` text extract |
| **What this is (v3)** | `asset_name` + `rationale` written so the lightbox title (`#id · name`) and the "What this is" lead are real, not fallbacks | write `asset_name` + `rationale` in asset.yaml |
| **Plan trace (v3)** | the asset's `asset_id` matches a Plan `#` row (Ships/Review-shape). No match = a deviation surfaced in the **Plan reconciliation** banner | reconcile: update the Plan or the asset (rename / add row / fix ship flags) |
| **Channel + name match (v3)** | `asset.yaml default_channel` = the Plan row's `Channel` **and** `asset_name` = the Plan name, VERBATIM — the Plan is the source of truth for the asset catalog. An off-Plan channel **silently drops** the asset (the render loop skips a channel it doesn't know). This is a **hard gate**: `check-state` **Layer K** *fails* (not warns) on any mismatch. | set `default_channel`/`asset_name` to the Plan values — never invent a channel or rename |

**Then**: `python .claude/skills/asset-gallery/build-gallery.py --campaign <slug>` and confirm the tile count looks right. **Read the build's stdout tail** — it prints (a) any **COPY-REVIEW WARNINGS** (copy-bearing assets with no resolvable copy surface) and (b) the **PLAN RECONCILIATION** block: `✓ Reflects the approved Plan` when the gallery matches 1:1, else the list of deviations (not-in-plan · planned-not-produced · ship-count · renamed). CM reconciles every deviation — update the Plan or the asset — before surfacing. The same reconciliation renders as a banner at the top of `gallery.html`.

**Automated pre-check (SYS-003)**: `python .claude/skills/asset-gallery/build-gallery.py --campaign <slug> --check` validates the *machine-checkable* rows above — every `ship: true` file (and any declared `copy_file` / `production_file` / `view_source`) exists on disk, each asset folder has an `asset.yaml`, review assets carry a `rationale`, and `gallery.html` is at least as new as the newest ship-affecting file (no stale gallery). It exits non-zero on drift, so CM and the smoke test can gate on it. It does **not** check tile-count vs Review-shape — eyeball that. Worktree-aware (resolves `campaigns/` to the main checkout).

**Re-occurrence policy**: operator catches a gallery issue (wrong tile count · missing download · wrong "View in full" · missing status badge · empty rationale) = **P1 CM process failure**. CM owns this check.

## Cross-references
- `asset.md` — the `asset.yaml` schema (`ship` / `type` / `copy_file` / `production_file` / `view_source`)
- `plan.md` — the Review-shape + Ships + Copy-file columns this checks against
- `.claude/skills/asset-gallery/build-gallery.py` — the builder
