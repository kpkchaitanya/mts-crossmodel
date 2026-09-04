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
.\.venv\Scripts\python.exe scripts/print_worksheets.py --week current --apply --confirm 20
.\.venv\Scripts\python.exe scripts/print_worksheets.py --subject ela --week 2026-09-07 --dry-run
```

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `week` | `current`, an instructional week number, or an ISO date | `current` | Resolved to that week's ISO Monday. Selects which staged documents match, and which `Week_<WEEK_OF>` folder to read in `publish` mode. |
| `grades` | `all`, or a comma-separated grade list | `all` | A named grade with no configured copy counts is a fail-closed error. |
| `source` | `staging`, `publish` | `publishing.printing.default_source` (`staging`) | `staging` reads the approved staging folder; `publish` reads each grade's delivered `Week_<WEEK_OF>` folder. |
| `include` | `both`, `worksheet`, `key` | `both` | `key` prints answer keys only; `worksheet` prints student copies only. |
| `copies` | per-grade overrides, e.g. `grade_5=6` or `grade_5=6:2` | configured counts | `<grade>=<worksheets>[:<keys>]`. Applies to this run only and is never persisted. |
| `printer` | a Windows printer name | `publishing.printing.printer_name` | Must match `Get-Printer` exactly. |
| `subject` | a configured subject id (e.g. `math`, `ela`) | the subject the command is running under | Selects that subject's naming and copy counts. |
| `dry_run` | `yes`, `no` | `yes` | `yes` resolves, pairs, and plans without printing. |

## Subjects

Printing is a distribution step, so it resolves configuration from `base.yaml` plus the subject file
only — no worksheet type, no template registry. A subject whose templates and verification rules are
not yet approved for authoring can therefore still print artifacts it already has, while staying unable
to generate new ones.

- **Math** is staged as Google Docs and exported to PDF on the way to the printer.
- **ELA** is staged as finished PDFs and downloaded as-is. Its key suffix precedes the file extension
  (`…-2026-09-07-KEY.pdf`), which `naming.weekly.file_extension` accounts for.
- ELA has no configured Final Delivery destinations, so `source=publish` is unavailable for it; print
  ELA from `staging`.

## Class counts

Copies live in the subject configuration (`data/config/subjects/<subject>.yaml`,
`publishing.printing.copies_by_grade`) so class sizes are reviewed in one place rather than typed at
the prompt. Math and ELA currently ship the same counts:

| Grade | Student worksheets | Answer keys |
|---|---|---|
| Grade 1 | 5 | 1 |
| Grade 4 | 6 | 1 |
| Grade 5 | 4 | 1 |
| Grade 6 | 3 | 1 |

Math's grade 9/10 has no configured counts, so `grades=all` skips it and reports
`no_copy_counts_configured`. Add it to the configuration when its class count is known — do not print
it via a `copies` override as a matter of routine.

## Behavior

1. Resolve every parameter from this invocation and configuration only.
2. Echo the resolved parameter set, including the resolved `week_of`, source folder, printer, and the
   per-grade copy counts that will be used.
3. Run with `--dry-run` first. Present the effective folder, every planned job (grade, role, document
   name, copies), the total copy count, and every reported issue.
4. Do not proceed to `--apply` without a new, explicit instruction.
5. `--apply` requires `--confirm <total copies>` matching the plan **at apply time**. Re-run the dry
   run immediately before applying; staging folders change between runs.
6. Report the resulting Print Record.

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

## Rollback

There is none. Printing is the one publishing utility whose output cannot be undone, which is why the
confirmation count is required and why the dry run is not optional.
