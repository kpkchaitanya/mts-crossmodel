# Command: Print Worksheets

Publishing utility. Exports the week's approved worksheet/answer-key pairs to PDF and spools them to
a local printer at each grade's class count.

Canonical design: [utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>)
section 6.

This is a distribution step, never an authoring step: it never renders, edits, re-numbers, re-verifies,
moves, or deletes anything. It introduces no gate and bypasses none. It reads the same folders
`/deliver-worksheets` writes and reuses that command's pairing, so the printed set can never disagree
with the delivered set.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/print_worksheets.py --week current --dry-run
.\.venv\Scripts\python.exe scripts/print_worksheets.py --subject ela --week current --dry-run
```

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `week` | `current`, an instructional week number, or an ISO date | `current` | Resolved to that week's ISO Monday. Selects which staged documents match, and which `Week_<WEEK_OF>` folder to read in `publish` mode. |
| `grades` | `all`, or a comma-separated grade list | `all` | A named grade with no configured copy counts is a fail-closed error. |
| `source` | `staging`, `publish` | `publishing.printing.default_source` (`staging`) | `staging` reads the approved staging folder; `publish` reads each grade's delivered `Week_<WEEK_OF>` folder. |
| `include` | `both`, `worksheet`, `key` | `both` | `key` prints answer keys only; `worksheet` prints student copies only. |
| `copies` | per-grade overrides, e.g. `grade_5=6` or `grade_5=6:2` | configured counts | `<grade>=<worksheets>[:<keys>]`. Applies to this run only and is never persisted. |
| `printer_name` | a configured Windows printer name | `publishing.printing.printer_name` (`Brother HL-L2380DW series Printer`) | Selects the configured Brother or HP queue; must match the configured name exactly. The CLI also accepts legacy `--printer`. |
| `subject` | one or more comma-separated configured subject ids (e.g. `math`, `ela`, `math,ela`) | `math,ela` | Selects each subject's naming and copy counts. Subjects are planned together and printed sequentially in the specified order. |
| `dry_run` | `yes`, `no` | `yes` | `yes` resolves, pairs, and plans without printing. |

## Subjects

Printing is a distribution step, so it resolves configuration from `base.yaml` plus the subject file
only — no worksheet type, no template registry. A subject whose templates and verification rules are
not yet approved for authoring can therefore still print artifacts it already has, while staying unable
to generate new ones.

- **Math** is staged as Google Docs and exported to PDF on the way to the printer.
- **ELA** is staged as finished PDFs and downloaded as-is. Its key suffix precedes the file extension
  (`…-2026-09-07-KEY.pdf`), which `naming.weekly.file_extension` accounts for.
- Final Delivery destinations are project-scoped in `data/config/project/base.yaml` and are shared by
  Math and ELA. ELA can use `source=publish` for grades that have both a configured naming prefix
  and configured copy counts in `data/config/subjects/ela.yaml`.

## Class counts

Copies live in each subject configuration (`data/config/subjects/<subject>.yaml`,
`publishing.printing.copies_by_grade`) so class sizes are reviewed in one place rather than typed at
the prompt. Current configured counts are:

| Grade | Math worksheets | Math keys | ELA worksheets | ELA keys |
|---|---:|---:|---:|---:|
| Grade 1 | 5 | 1 | 5 | 1 |
| Grade 4 | 6 | 1 | 6 | 1 |
| Grade 5 | 0 | 0 | 0 | 0 |
| Grade 6 | 6 | 1 | 6 | 1 |
| Grades 9 & 10 | Not configured | Not configured | 7 | 1 |

Zero suppresses printing for that role. Math's Grade 9/10 has no configured counts, so the default
combined run skips it and reports `no_copy_counts_configured` for Math. ELA's Grade 9/10 count is
configured separately.

## Behavior

1. Resolve every parameter from this invocation and configuration only. `printer_name` defaults to
  the configured Brother queue and may select the configured HP queue for the current run.
2. Echo the resolved parameter set, including the resolved `week_of`, source folder, printer, color
  mode, and the per-grade copy counts that will be used. The configured default color mode is
  `black_and_white`.
3. Run with `--dry-run` first. Present the effective folder, every planned job (grade, role, document
  name, copies) grouped by subject, the combined total copy count, and every reported issue.
4. Do not proceed to `--apply` without a new, explicit instruction.
5. `--apply` requires `--confirm <total copies>` matching the combined plan **at apply time**. Re-run
  the dry run immediately before applying; staging folders change between runs. Check the combined
  total before any subject begins printing.
6. Print subjects sequentially in the requested order, stopping after a subject has a print failure.
  Report one Print Record per subject.

Pairing issues (`ambiguous_name`, `incomplete_pair`, `unmatched_files`) are reported and skipped,
never resolved on the user's behalf. Handing a class the answer key by accident is worse than printing
nothing.

## Backend setup

`publishing.printing.backend` selects how the PDF reaches the printer:

- `sumatra` (default) — SumatraPDF prints silently with exact copy counts and duplex control. It is a
  single portable executable; place it at the configured `backends.sumatra.executable` path
  (`tools/SumatraPDF.exe`). No installation or admin rights are required.
- `acrobat` — fallback using the installed Acrobat. It prints one copy per invocation, briefly shows a
  window, and uses the printer's default duplex setting rather than the configured one.

The configured default `color_mode` is `black_and_white`, mapped to SumatraPDF's `monochrome` print
setting. The Acrobat fallback cannot force a color mode and therefore uses the printer's default color
setting.

## Rollback

There is none. Printing is the one publishing utility whose output cannot be undone, which is why the
confirmation count is required and why the dry run is not optional.
