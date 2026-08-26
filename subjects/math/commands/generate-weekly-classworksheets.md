# Command: Generate Weekly Class Worksheets

Execute `skills/worksheet-generation.md` for the requested week and grades. Use all enabled grades if none are specified.

Start from the local curriculum cache and current configuration. For combined Grades 9/10, resolve Grade 9 and Grade 10 independently and preserve the configured split.

Present the configured Gate 1 curriculum scope first and stop for approval when Gate 1 is enabled.

## Copilot output location
When this command is executed from the Copilot repository context, dump/stage generated artifacts under `outputs-copilot/`. Canonical `outputs/` is reserved for the approved publish step.
