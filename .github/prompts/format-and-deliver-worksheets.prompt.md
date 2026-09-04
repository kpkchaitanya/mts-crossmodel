---
description: "Bring every staged pair to pipeline standard (reconstructing orphans) then deliver."
agent: "agent"
argument-hint: "[week=current|<n>|<iso-date>] [grades=all|<list>] [source_folder=<folder-id>] [batch_id=<id>] [dry_run=yes|no]"
---

# Command: Format-And-Deliver Worksheets

## Canonical definition — load this first

- [commands/format-and-deliver-worksheets.md](../../commands/format-and-deliver-worksheets.md)

This prompt is a thin entry point only. Follow `commands/format-and-deliver-worksheets.md` for
classification, reconstruction, and the mandatory dry-run-then-confirm sequence. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/utility-design.md](<../../specs/generate_math_worksheets/03. design/utility-design.md>) section 5 (canonical design)
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.provenance`

## Parameters

Parse `week`, `grades`, `source_folder`, `batch_id`, and `dry_run` exactly as documented in
`commands/format-and-deliver-worksheets.md`. Default `week` to `current`, `grades` to `all`,
`batch_id` to `reconstructed_<week_of>`, and `dry_run` to `yes`.

## Required sequence

1. Echo the resolved parameter set.
2. Invoke `scripts/format_and_deliver.py` with `--dry-run` and present each grade's classification
   (`conformant` or `orphan`) and planned action, plus every pairing issue.
3. Stop. Wait for an explicit instruction before re-invoking with `--apply`.

Never reconstruct or re-render a `conformant` pair — provenance is what makes a document trustworthy,
and a document that already has it must not be replaced. Never treat an inherited answer as
independently verified; the reconstructed Spec records it as inherited, and that record must not be
overwritten or hidden when reporting results.
