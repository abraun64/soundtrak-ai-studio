# Retro — System Schema (v1)

**Spec version**: v1 · Authored 2026-06-04 after first end-to-end Phase 6 validation revealed the need to embed retros as a recurring system mechanism rather than an ad-hoc conversation.

The **Retro** is the structured extraction of lessons from a completed body of work. It captures what worked, what didn't, what system rules to update, and what forward actions to commit. Retros generate **memory rules** + **spec amendments** + **playbook updates** + **task items** — not just a doc on disk.

**Stored**: `campaigns/<slug>/retros/<YYYY-MM-DD>-<scope-slug>.md` for campaign-scoped retros; `docs/retros/<YYYY-MM-DD>-<scope-slug>.md` for system-wide retros.

**Locked**: at operator approval of the retro's "Forward actions" section. Action items propagate to the cross-campaign tasks queue; system rules propagate to memory.

---

## Retro trigger points (when retros fire)

| Scope | When | Length | Depth |
|---|---|---|---|
| **Cycle retro** | After each Phase 6 cycle (ongoing campaigns only) | ~5 min | Logged in `phase-6-cadence.md` §5 procedural-refinements; only triggers a formal retro doc if friction escalates |
| **Phase boundary retro** | At close of each phase (1 → 2, 2 → 3, etc.) | ~10-15 min | Light retro doc. What worked / didn't / change-for-next-phase. Saved in `campaigns/<slug>/retros/` |
| **Wave retro** | End of a major wave (e.g. Wave 0 completion, Wave 1 completion) | ~30 min | Wave-scope retro doc. Includes spec/playbook implications |
| **Campaign-end retro** | When a one-off campaign closes OR when an ongoing campaign hits a quarterly milestone | ~45-60 min | Comprehensive retro. **Fed by the campaign Results Report** (`docs/specs/campaign-report.md` — the analyst's outcomes readout; its §0/§2 become this retro's §2 "what worked"). Both campaign-specific + system-level implications. **Includes the campaign-wrap graduation pass** — a candidate · destination · evidence · verdict table per `docs/workflow.md` §The three layers; "no candidates" is stated explicitly, never skipped. **Report + retro together are the close gate** — a campaign can't be Closed without both (check-state Layer H) |
| **System retro** | Quarterly across all active campaigns; OR after a significant system upgrade (like Rollout Arch v2 build) | ~60-90 min | Cross-campaign, cross-artifact. Memory rules + spec changes + playbook updates expected as outputs |

**Operator-triggered retros** (any time): phrases like *"pause + retrospective"*, *"let's retro"*, *"I want to capture what we learned"*, *"happy days"* (operator confirmation pattern from 2026-06-04). CM should recognize these as retro-trigger requests + open the structured flow.

---

## Schema

```markdown
# Retro — <Scope> — <YYYY-MM-DD>

**Scope**: cycle / phase-N-boundary / wave-N / campaign-end / system-quarterly / ad-hoc
**Period covered**: <start-date> → <end-date>
**Trigger**: <operator-requested / phase-boundary / cycle-end / scheduled>
**Facilitator**: CM (or the operator if self-led)
**Status**: Draft / ✅ Approved (= forward actions committed)

## §1 Scope

Brief paragraph naming what's in scope and what's explicitly out of scope. This anchors the conversation; without it, retros drift.

## §2 What worked (in rough priority order of magnitude)

Each item: one paragraph naming the pattern + why it worked + whether it generalises beyond this scope.

- AI's honest read (drafted first; operator amends or replaces)
- Operator's read (operator-driven additions or disagreements)
- Final list: agreed-upon "patterns to keep / amplify"

## §3 What didn't work / friction points

Same format. Each item: pattern name + symptom + root cause + whether it's pattern-level or one-off.

## §4 System rules to update

Concrete proposals derived from §2 + §3. Each item points at a target artifact:
- **Memory rule**: new file at `~/.claude/projects/<...>/memory/<feedback_or_learning>_<slug>.md`
- **Spec amendment**: edit to `docs/specs/<spec>.md`
- **Playbook amendment**: edit to `docs/playbooks/<playbook>.md`
- **Agent definition**: edit to `.claude/agents/<agent>/AGENT.md`
- **Skill amendment**: edit to `.claude/skills/<skill>/SKILL.md`
- **Tenant-layer graduation** (three-layer model — `docs/workflow.md` §The three layers): tactical learning → `tenant-brand/<tenant>-playbook.md` (per `docs/specs/tenant-playbook.md`) / winning asset → `tenant/library/` via `/library-add` / brand drift → `tenant-brand/_recommendations-queue.md`

Each row is a concrete action, not vibes ("Producer should be more rigorous" → no. "Producer AGENT.md §QA gains a layer-4 inflation check, language in §...." → yes).

## §5 Forward actions

Operator-prioritised. Each row: what / who / when / dependency.

## §6 Approval gate

Operator confirms the §5 list. On approval:
- Memory rules get written
- Spec/playbook/agent/skill amendments get applied
- Action items land in `campaigns/tasks.md` (or `campaigns/<slug>/dashboard.md` if campaign-scoped)
- Retro doc moves Status to ✅ Approved

## §7 Status + propagation history (post-approval)

Tracks which §4 / §5 items actually shipped + when. This isn't filled at retro time; it's appended as items complete. Keeps the audit trail visible.
```

---

## Authoring discipline

- **AI drafts §2 + §3 first** with honest reads. Don't ask operator to fill blanks; bring observations to the table. Operator amends.
- **Specifics beat vibes** in §4. "Producer should be more rigorous" is not an action. "Producer AGENT.md Step 4.6 gains a check that the operator confirmed the channel mapping" is.
- **§5 is operator-prioritised**. AI proposes ordering; operator overrides.
- **Approval is explicit**. Operator says "approve retro" or names specific items to skip/defer. CM does NOT self-approve.
- **Retro doc length target**: 1-3 pages. Long retros indicate the scope was too wide; split into sub-retros.
- **Queued-cleanup items decay.** If a friction-point cleanup item is approved in §5, it must be committed in the same session or killed (explicitly dropped with rationale in §7). Do NOT queue cleanup items as "later" tasks when they can be done in ~15 min now. Items that survive multiple retros without execution are a signal the cleanup isn't actually valued — kill them rather than carrying the queue indefinitely. Per `feedback_cadence_skill_is_phase3_deliverable.md` pattern (deferred → never) and retro §3.7 (email re-theme). Rule added 2026-06-04.

---

## CM behaviour at retro triggers

When CM detects a retro-trigger phrase (see §triggers above) OR reaches a configured trigger point (phase close, wave close, etc.):

1. **Acknowledge** the trigger explicitly. "OK retroing Phase N — locking the scope now."
2. **State scope** per §1 (what's in, what's out).
3. **Propose structure** (which retro parts, approximate time per part).
4. **Open with AI's §2 (What worked) read** — first opening volley, not a question.
5. **Iterate per-section** with operator. CM drafts; operator amends.
6. **At §4 / §5** propose concrete artifact targets + action ordering.
7. **Drive to approval gate** (§6). Don't leave retros open indefinitely.
8. **On approval**: execute §4 mechanical changes + write the retro doc + update tasks queue.

If operator cuts the retro short (*"that's enough, let's ship"*), CM still captures whatever sections were completed + flags the retro as **Status: Draft (partial)** so it can be resumed later.

---

## Cross-references

- **Rollout Architecture v2 spec**: `docs/specs/rollout-architecture.md` — retros are now positioned at end of each phase + at wave / campaign boundaries
- **Plan spec v2**: `docs/specs/plan.md` §N - gains a "retro milestones" sub-section noting which phase boundaries trigger a retro for this campaign
- **CM SKILL.md** — trigger phrases recognised + retro flow invoked
- **Campaign Report spec**: `docs/specs/campaign-report.md` — the outcomes readout that feeds the campaign-end retro; report + retro together are the enforced close gate
- **Memory rule** capturing the principle: `feedback_retros_are_system_artifacts_not_conversations.md`
