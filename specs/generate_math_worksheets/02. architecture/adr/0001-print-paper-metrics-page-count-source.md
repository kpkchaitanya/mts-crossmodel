# ADR-0001: Page-count source for print paper metrics

- **Status:** Accepted
- **Date:** 2026-09-04
- **Scope:** Print Worksheets utility (`/print-worksheets`, `src/mts/publishing/print_jobs.py`)

## Context

The print utility planned work in **copies**, which says nothing about paper. Two runs of 22 copies in
the same week consumed very different amounts of the tray:

| Subject | Document length | Copies | Pages | Sheets (duplex long-edge) |
|---|---|---|---|---|
| ELA | worksheets 2pp, keys 1pp | 22 | 40 | 22 |
| Math | worksheets 5–6pp, keys 2–5pp | 22 | 104 | 58 |

Grade 4 math alone was 6pp × 6 copies = 36 pages / 18 sheets. The plan showed `x6`, which read as
cheap. Paper is the one output of this utility that cannot be undone, so the quantity being confirmed
should be the quantity that leaves the tray.

Two facts were verified rather than assumed:

1. **Drive does not know the page count.** `files.get(fields="*")` on both a staged `application/pdf`
   and a Google Doc returns `size`, `md5Checksum`, `modifiedTime`, and `version` — there is no
   `pageCount` or equivalent for either type. A page count therefore has to come from something the
   repository records itself.
2. **Page count is derivable from PDF bytes without a new dependency.** Counting `/Type /Page`
   objects in the raw bytes agreed with the page tree's `/Count` on all 17 real documents produced in
   this session, across both Google-Docs exports and externally produced PDFs.

The constraint driving the choice: the number must be known **before** committing paper, and a dry run
should not become expensive.

## Options

**A. Declare pages in configuration, verify at print time.** `pages_by_grade` beside
`copies_by_grade`; the plan computes pages and sheets with zero Drive reads, and the apply — which
holds the bytes anyway — refuses to print when actual pages disagree with the declared value.
*Cost:* a reviewed number per grade per subject, drifting whenever a template changes. It makes
document length a reviewable property, but pays for that with configuration that must be kept true.

**B. Measure once, cache, reuse.** An explicit measure pass downloads each planned document, counts
pages, reports pages and sheets, and prints nothing. The confirming apply reuses those spooled files
while the Drive fingerprint (`modifiedTime` + `version`) still matches, so a week costs **one**
download rather than two. *Cost:* the measure pass does download; the plain dry run stays free but
reports no page numbers.

**C. Stamp `mts_pages` into Drive `appProperties`.** Read back for free by the existing listing call.
Rejected as a primary source: every week produces new documents that have never been measured, so the
first run of each week is still unknown. It only pays off on repeat runs of the same document.

## Decision

**Option B.** Measurement is automatic and always reflects the document that will actually print,
which A cannot guarantee without a config value someone remembered to update. The download it requires
is not additional work — the apply already downloads every document — it is the *same* download,
moved ahead of the paper commitment and reused afterwards.

Consequently `--confirm` matches **total sheets**, not total copies: the confirmed number is the number
of sheets the printer will consume.

## Consequences

- Three distinct modes: a free plan-only dry run, an explicit measure pass that reports pages and
  sheets, and an apply that verifies the cached fingerprint before printing.
- The spool cache is keyed on the Drive fingerprint, so a document edited between measuring and
  applying is re-downloaded rather than printed from a stale copy.
- Sheets are computed from the configured duplex setting. The Acrobat backend prints at the printer's
  default duplex, so its sheet figure is an estimate; SumatraPDF sets duplex explicitly and is exact.
- Revisit if measuring ever becomes slow enough to be disruptive — Option A's declared counts remain
  a viable plan-time source, with this measurement as its verification step.
