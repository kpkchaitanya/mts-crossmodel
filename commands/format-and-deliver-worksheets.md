# Command: Format-And-Deliver Worksheets

Publishing utility. Takes every loose staged pair, brings each up to pipeline standard, and delivers
it — in one step. A staged pair is either already conformant (rendered through the pipeline, so it
carries provenance) or an orphan (authored straight into Drive, with no Spec of record); orphans are
reconstructed into a Spec and re-rendered from the registered template before delivery.

Canonical design: [utility-design.md](<../specs/generate_math_worksheets/03. design/utility-design.md>) section 5.

This composes existing utilities rather than adding a new delivery, naming, or formatting rule: pairing
is [`/deliver-worksheets`](deliver-worksheets.md)'s staging-name pairing, delivery is
`deliver.run_deliver`, reconstruction is `reconstruct.reconstruct_spec`. It introduces no gate and
bypasses none.

Concrete CLI entry point:

```powershell
.\.venv\Scripts\python.exe scripts/format_and_deliver.py --week 2026-09-07 --grades grade_4 --dry-run
.\.venv\Scripts\python.exe scripts/format_and_deliver.py --week 2026-09-07 --grades grade_4 --apply
```

## Parameters

| Parameter | Values | Default | Notes |
|---|---|---|---|
| `week` | `current`, an instructional week number, or an ISO date | `current` | Same resolution as `/deliver-worksheets`. |
| `grades` | `all`, or a comma-separated grade list | `all` | A requested grade with no configured destination is a fail-closed error. |
| `source_folder` | a Drive folder ID | `publishing.staging.approved_folder_id` | Staging folder to pair from. |
| `batch_id` | a batch identifier | `reconstructed_<week_of>` | Where a reconstructed Spec is persisted under the grade's transaction tree. |
| `dry_run` | `yes`, `no` | `yes` | `yes` classifies and plans without reconstructing, rendering, or delivering anything. |

## Classification

Every staged pair is labeled from its documents' provenance (Drive `appProperties`):

- **`conformant`** — carries provenance naming its own grade and week. Delivered as-is; **never**
  re-rendered.
- **`orphan`** — no provenance, or provenance naming a different grade or week. Reconstructed and
  re-rendered before delivery.

## What happens to an orphan

1. Its worksheet and answer key are parsed into a Spec (`reconstruct.reconstruct_spec`). Parsing never
   guesses: a numbering gap, a section mismatch, or a question/answer count mismatch refuses, rather
   than producing a Spec that might misstate a question or an answer.
2. The Spec's `verification.status` is `PASS` so rendering can proceed, but it is recorded as
   **inherited, not recomputed** (`method: "inherited_from_source_document"`, `recomputed: false`,
   `source_documents`), so an inherited answer is never mistaken for one independently verified.
3. The Spec is persisted under the grade's transaction tree, so it stops being an orphan.
4. It is re-rendered from the registered template with per-day local numbering, and the fresh
   documents are stamped with provenance.
5. **The re-rendered documents are delivered, not the originals.** The record names which documents a
   rebuild replaced.

## Behavior

1. Resolve every parameter from this invocation and configuration only.
2. Echo the resolved parameter set and the classification of every staged pair before doing anything.
3. Run with `--dry-run` first. Present the classification, the planned action per grade, and every
   pairing issue.
4. Do not proceed to `--apply` without a new, explicit instruction.
5. Report the resulting record: reconstruction actions (with the replaced document IDs and persisted
   Spec path) plus the Delivery Record. One grade's reconstruction or delivery failure is recorded
   against that grade and does not block the others.

## Rollback

A `conformant` grade is untouched, so there is nothing to roll back. For a rebuilt `orphan` grade, the
original documents are not deleted or archived by this utility — they remain in staging alongside the
new ones — so recovery is deleting the newly delivered copies and, if needed, removing the persisted
Spec revision.

## Not in scope

Recovering a document whose *content* is wrong, only its provenance. This utility does not verify or
correct question or answer text — it inherits the answer key as-is. If a reconstructed document's
answers need independent re-verification, that is a separate, explicit request.
