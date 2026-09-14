---
description: "Copy and rename one worksheet/answer-key pair for a target subject, Worksheet Type, and grade."
agent: "agent"
argument-hint: "from_subject=<id> from_grade=<grade> to_subject=<id> to_grade=<grade> [from_worksheettype=weekly] [to_worksheettype=weekly] [week=current|<n>|<iso-date>] [source_folder=staging|<id>|<url>] [target_folder=<preset>|<id>|<url>] [dry_run=yes|no]"
---

# Command: Duplicate Worksheet

## Canonical definition

- [commands/duplicate-worksheet.md](../../commands/duplicate-worksheet.md)

This prompt is a thin entry point only. Follow the canonical command for parameter resolution,
pairing, collision handling, and reporting. Also read:

- [AGENTS.md](../../AGENTS.md)
- [specs/generate_math_worksheets/03. design/utility-design.md](<../../specs/generate_math_worksheets/03. design/utility-design.md>) section 9
- [data/config/project/base.yaml](../../data/config/project/base.yaml) `publishing.duplicate_worksheet`

Parse `from_subject`, `from_worksheettype`, `from_grade`, `to_subject`, `to_worksheettype`, `to_grade`,
`week`, `source_folder`, `target_folder`, and `dry_run` exactly as documented. Default both Worksheet
Types to `weekly`, `week` to `current`, `source_folder` through the configured `staging` preset,
`target_folder` to the resolved source folder, and `dry_run` to `no`.

Echo the resolved parameters, invoke `scripts/duplicate_worksheet.py`, and report its Duplicate
Worksheet Record. Pass `--dry-run` only when requested. Never overwrite an existing target name or
guess a missing or ambiguous source pair.