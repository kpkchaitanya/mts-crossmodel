# Architecture Decision Records

One file per architecturally significant decision: `NNNN-kebab-case-title.md`, numbered in the order
decisions are accepted. A decision belongs here when it constrains future work and reversing it would
be expensive — otherwise it belongs in the relevant design document.

Records are append-only. A decision that no longer holds is superseded by a new record, not edited in
place; update the old record's status to `Superseded by ADR-NNNN` and leave its reasoning intact so
the history stays readable.

`../architecture.md` section 7 lists the M3 architecture decisions that predate this folder. Those
become ADRs only if they remain architecturally significant and stable.

## Format

```markdown
# ADR-NNNN: Title

- **Status:** Proposed | Accepted | Superseded by ADR-NNNN
- **Date:** YYYY-MM-DD
- **Scope:** which component or utility this constrains

## Context
What forced a decision, and what was measured or verified rather than assumed.

## Options
Each option considered, with its real cost — including the ones not chosen.

## Decision
What was chosen, and why that trade-off is the right one here.

## Consequences
What this makes easy, what it makes harder, and what would trigger revisiting it.
```

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-print-paper-metrics-page-count-source.md) | Page-count source for print paper metrics | Accepted |
| [0002](0002-project-scoped-delivery-destinations.md) | Final Delivery destinations are project-scoped, not subject-scoped | Accepted |
