---
name: print-worksheets
description: Run the repository's canonical print-worksheets command to export approved worksheet/answer-key pairs to PDF and print them at each grade's class count.
---

Read and follow `commands/print-worksheets.md` in this repository; it is the canonical, harness-neutral
definition of this command. Resolve every parameter from the current invocation, `publishing.printing`
in `data/config/project/base.yaml`, and the subject's `publishing.printing.copies_by_grade`; echo the
resolved parameter set including the per-grade copy counts; invoke `scripts/print_worksheets.py` with
`--dry-run` first; and only re-invoke with `--apply --confirm <total copies>` after a new explicit
instruction, using a dry run taken immediately beforehand. Printing cannot be undone.
