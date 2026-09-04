# ADR-0002: Final Delivery destinations are project-scoped, not subject-scoped

- **Status:** Accepted
- **Date:** 2026-09-04
- **Scope:** Final Delivery configuration and every utility that resolves a `publish` target
  (`/deliver-worksheets`, `/archive-folder`, `/cleanup-folder`, `/print-worksheets`)

## Context

`publishing.final_delivery.destinations_by_grade` lived in `data/config/subjects/math.yaml`. It maps
each grade to the Drive folder that grade's families actually look in — "1st Grade", "4th Grade", and
so on.

When ELA needed to deliver into those same folders, the subject-scoped placement forced a choice
between two bad options: copy five canonical folder IDs into `ela.yaml`, or give ELA its own parallel
folders. The first duplicates canonical identifiers, which the repository forbids precisely because
duplicated IDs drift. The second splits a family's weekly material across two folders per grade for no
reason the audience would recognise.

The placement was also simply wrong about ownership. A destination describes **who reads it** — a
grade cohort — not **what is put in it**. Nothing about "1st Grade" is mathematical.

## Options

**A. Duplicate the folder IDs into each subject file.** Immediate, and wrong for the obvious reason:
five IDs × every future subject, with no mechanism to keep them equal.

**B. Move `destinations_by_grade` to `base.yaml`, allow subject override.** One definition at project
scope; a subject may still override if its audience genuinely differs. Requires handling grades a
subject does not produce.

**C. Give ELA its own destination folders.** Defensible only if ELA's audience differed from math's.
It does not — the same family opens the same grade folder.

## Decision

**Option B.** Destinations move to `base.yaml`. The merge order already lets any subject override the
block, so the shared default costs no flexibility.

This forces a companion rule, because the shared destination list is now broader than any one
subject's output: **a destination grade the subject has no `naming.weekly` prefix for is skipped and
reported (`no_naming_for_subject`) under `grades=all`, and refused when named explicitly.** ELA
produces no 9/10, and that must not turn an otherwise complete ELA delivery into a failed run. Naming
the grade directly is still fail-closed, so the rule never hides a genuine mistake. `deliver` owns the
single implementation; `print_jobs` calls it rather than repeating it, so the two utilities cannot
disagree about which grades a subject covers.

## Consequences

- All four `publish`-resolving utilities gain ELA support from one config move, including printing ELA
  from delivered folders.
- Each grade's `Week_<date>` folder holds that grade's math and ELA material together.
- Adding a subject means adding its naming and copy counts, not another copy of the folder IDs.
- A subject that genuinely needs separate destinations overrides the block in its own file; that
  override is now a visible, deliberate act rather than the default.
