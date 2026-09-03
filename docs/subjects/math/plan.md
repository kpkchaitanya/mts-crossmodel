# MTS Math Worksheet Generation — Optimization Plan

**Status:** P0 MVP READY FOR PILOT  
**Purpose:** Phased implementation plan to reduce worksheet-generation time and token usage while preserving curriculum alignment, answer correctness, template quality, approval gates, and auditability.

> **Guiding principle:** Reason about what changes. Structure what repeats. Verify what can be computed. Cache what is stable. Measure everything.

## 0. Implementation Tracking

**Tracking started:** 2026-08-24  
**Current objective:** Deliver a stable, faster MVP suitable for the next worksheet run while preserving verification and human gates.

**Repository standardization:** COMPLETE — `github-repo/` is the primary source of truth; root/sibling duplicates are retired after reconciliation.  

**Grade 1–12 progressive curriculum backbone:** HIGH-LEVEL V1 COMPLETE — standards-light conceptual progression added under `knowledge/curriculum/progressive/`; current CCS pacing remains a separate yearly layer.  

### P0 Priority Track

| Improvement | Status | Started | Completed | Baseline | Target | Notes |
|---|---|---|---|---|---|---|
| IMP-01 Local NC/CCS curriculum knowledge + resolver | COMPLETE | 2026-08-24 | 2026-08-24 | Repeated web research each run | Normal cached week requires no web research | Current-week + August fallback cache implemented; broader school-year fill remains Phase 1 |
| IMP-02 Template manifest/cache + revision invalidation | COMPLETE | 2026-08-24 | 2026-08-24 | Full template inspection/readback is a major token driver | Reinspect only when template revision changes | Manifest implemented; live revisions verified worksheet=3, key=2; guard regression-tested |
| IMP-03 Canonical Worksheet Spec | COMPLETE | 2026-08-24 | 2026-08-24 | Questions, answers, verification, and rendering are loosely coupled | One source of truth per worksheet | JSON Schema implemented and smoke-tested |
| IMP-04 Deterministic answer verifier | COMPLETE | 2026-08-24 | 2026-08-24 | Ad-hoc validation per run | Reusable validators + all-pass gate | MVP runtime covers common arithmetic/geometry/number/algebra methods; reasoning remains explicitly flagged |
| IMP-05 Targeted final QA | COMPLETE | 2026-08-24 | 2026-08-24 | Broad document rereads | Verify compact rendering invariants | Numbered-line QA implemented; preserves required visual QA |
| IMP-06 Run telemetry | COMPLETE | 2026-08-24 | 2026-08-24 | Time/token usage estimated manually | Stage metrics persisted per run | Runtime telemetry implemented; token_usage remains null when provider telemetry is unavailable |

### P0 MVP Validation

- Regression suite: **6/6 PASS**
- Integrated smoke test: **PASS**
- Curriculum cache: **HIT** for week starting 2026-08-24
- Template revision cache: **HIT** (`worksheet=3`, `answer_key=2`)
- Deterministic verification smoke: **3 checked / 0 failed / 1 reasoning-required**
- Targeted QA smoke: **PASS**
- Next validation: measure real worksheet-generation elapsed time, tool calls, cache hits, and available token telemetry.

### Phase Tracking

| Phase | Status | Start | Exit Criteria Status | Measured Time Improvement | Measured Token Improvement |
|---|---|---|---|---:|---:|
| Phase 0 — Instrumentation & Run State | IN PROGRESS | 2026-08-24 | Not yet measured | — | — |
| Phase 1 — Curriculum Knowledge | IN PROGRESS | 2026-08-24 | Not yet complete | — | — |
| Phase 2 — Structured Generation & Verification | PLANNED | — | — | — | — |
| Phase 3 — Rendering & QA Optimization | PLANNED | — | — | — | — |
| Phase 4 — Pedagogical Intelligence | BACKLOG | — | — | — | — |
| Phase 5 — Operational Hardening | BACKLOG | — | — | — | — |

### Tracking Rules

1. Update this table whenever an improvement changes state.
2. Allowed states: `PLANNED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`, `BACKLOG`.
3. Record measured time/token improvement only from run telemetry; do not replace measured values with estimates.
4. If an optimization weakens answer verification, curriculum provenance, required human gates, or final publish approval, it fails acceptance.
5. At the end of each worksheet run, record cache hits/misses and any fallback to web/template reinspection.
6. Update the change log below for material design or implementation changes.

### Change Log

| 2026-08-24 | Added standards-light Grade 1–12 progressive curriculum backbone with 6 vertical unit families and builds-from/leads-to context; integrated path into P0 config/design/runtime | COMPLETE — 12 grades × 6 unit families |
| 2026-08-24 | Reconciled root and sibling workflow assets into `github-repo/`; canonicalized requirements/design/config/skills/commands, preserved `.github` as thin adapters, consolidated `runs/` and canonical `outputs/`, and preserved `outputs-copilot/` as intentional Copilot staging | COMPLETE |
| Date | Change | Result |
|---|---|---|
| 2026-08-24 | Reconciled project into canonical `github-repo/`; standardized requirements/design/config/skills/commands; removed governing duplication | COMPLETE — repo is primary execution source |
| 2026-08-24 | Added P0/phase implementation tracking and began MVP P0 work | IN PROGRESS |
| 2026-08-24 | Completed P0 MVP runtime, curriculum cache, template revision guard, schemas, targeted QA, telemetry, and regression suite | READY FOR PILOT — regression 6/6 and integrated smoke PASS |

---

## 1. Target Architecture

```text
Authoritative Sources
        ↓
Local Curriculum Knowledge
        ↓
Curriculum Resolver
        ↓
Grade/Course Blueprint
        ↓
Worksheet Generator
        ↓
Canonical Worksheet Spec
        ↓
Deterministic Verifier
        ↓
Template Renderer
        ↓
Targeted QA
        ↓
Human Approval Gates
        ↓
Publish
```

### Initial optimization targets

For a run comparable to Grade 1 + Grade 6 + Grades 9/10:

| Metric | Recent Baseline | Target after Phases 1–3 |
|---|---:|---:|
| Execution time | ~11 min | ~4–6 min |
| Task-context tokens | ~87K–138K estimated | ~45K–70K |
| Answer verification | Required | Required |
| Human gates | Required | Required |
| Final approval before publish | Required | Required |

These are hypotheses until Phase 0 telemetry establishes measured baselines.

---

## 2. Prioritized Improvement Backlog

| ID | Improvement | Category | Priority | Importance | Effort | Complexity | Est. Time Reduction | Est. Token Reduction | Phase |
|---|---|---|---|---|---|---|---:|---:|---|
| IMP-01 | Local NC/CCS curriculum knowledge layer + resolver | Knowledge | P0 | Critical | Medium | Medium | 12–20% | 10–18% | 1 |
| IMP-02 | Template manifest/cache + revision invalidation | Rendering | P0 | Critical | Medium | Medium | 12–20% | 20–35% | 3 |
| IMP-03 | Canonical Worksheet Spec | Architecture | P0 | Critical | Medium | Medium | 8–15% | 8–15% | 2 |
| IMP-04 | Deterministic answer-verification library | Quality | P0 | Critical | Medium | Medium | 5–10% | 3–7% | 2 |
| IMP-05 | Targeted/diff-based final QA | QA | P0 | High | Medium | Medium | 8–15% | 10–20% | 3 |
| IMP-06 | Run telemetry: time/tokens/tool calls/cache hits | Observability | P0 | High | Low–Med | Low | Indirect | Indirect | 0 |
| IMP-07 | Grade/course worksheet blueprints | Generation | P1 | High | Low | Low | 5–8% | 5–10% | 2 |
| IMP-08 | Source/citation cache with freshness metadata | Knowledge | P1 | High | Low | Low | 3–7% | 5–10% | 1 |
| IMP-09 | Run manifest + gate/status state machine | Workflow | P1 | High | Medium | Medium | 3–6% | 2–4% | 0 |
| IMP-10 | Batch Google Docs reads/writes | Tooling | P1 | High | Low–Med | Low | 5–10% | 2–5% | 3 |
| IMP-11 | Curriculum refresh/change detection | Maintenance | P1 | High | Medium | Medium | Future savings | Future savings | 1 |
| IMP-12 | Question history + novelty fingerprints | Generation | P2 | High | Medium | Medium | 5–12% | 5–10% | 4 |
| IMP-13 | Visual QA using known template invariants | QA | P2 | High | Medium | Medium | 3–8% | 3–7% | 4 |
| IMP-14 | Transactional publishing helper | Workflow | P2 | Medium | Low | Low | 2–5% | 1–2% | 5 |
| IMP-15 | Resume/recovery + regression tests | Reliability | P2 | High | Medium | Medium | Indirect | Indirect | 5 |

**Important:** Estimated savings overlap and must not be added directly.

---

# Phase 0 — Instrumentation and Run State

## Goal
Measure the current workflow before optimizing it and make every run resumable and auditable.

## Implement

### IMP-06 — Run telemetry
Capture per stage:

- start/end timestamp and elapsed time
- model/token usage when available
- tool-call count and latency
- cache hit/miss
- retries
- questions generated/regenerated
- verification failures
- documents read/written

Track metrics such as:

```text
seconds_per_question
tokens_per_question
tool_calls_per_worksheet
cache_hit_rate
verification_failure_rate
generation_retry_rate
render_retry_rate
qa_retry_rate
```

### IMP-09 — Run manifest
Persist workflow state:

```yaml
run_id: mts-2026-08-17
week_start: 2026-08-17
grades: [grade_1, grade_6, grade_9_10]

stages:
  curriculum: complete
  generation: complete
  verification: complete
  rendering: complete
  qa: complete

gates:
  gate_1: approved
  gate_2: approved
  gate_3: approved
  gate_4: approved
  gate_5: approved

publication:
  status: published
```

## Deliverables

```text
runs/<run-id>/
  manifest.yaml
  telemetry.json
```

## Exit criteria

- Every run has a unique ID.
- Every stage records elapsed time.
- Gate state is persisted.
- Interrupted runs can determine the last completed stage.
- At least one representative baseline run is measured.

---

# Phase 1 — Curriculum Knowledge Optimization

## Goal
Remove routine standards/pacing research from the weekly execution path.

## IMP-01 — NC standards master

Stable knowledge:

```text
knowledge/curriculum/nc/math/
  grade-1.yaml
  grade-4.yaml
  grade-5.yaml
  grade-6.yaml
  math-1.yaml
  math-2.yaml
```

Example:

```yaml
standard: NC.6.G.1
domain: Geometry
description: Find area of triangles, special quadrilaterals, and polygons.

concepts:
  - triangle area
  - parallelogram area
  - trapezoid area
  - composite figures

prerequisites:
  - multiplication
  - measurement
  - rectangle area

source:
  authority: NC DPI
  url: <source>
  last_verified: <date>
```

## IMP-01 — CCS annual pacing layer

School-year-specific knowledge:

```text
knowledge/curriculum/ccs/2026-2027/
  grade-1.yaml
  grade-4.yaml
  grade-5.yaml
  grade-6.yaml
  math-1.yaml
  math-2.yaml
```

Example:

```yaml
grade: 6
school_year: 2026-2027

weeks:
  - week_start: 2026-08-17
    month: August
    instructional_week: 1

    primary:
      - NC.6.G.1

    secondary:
      - NC.6.G.3
      - NC.6.G.4

    concepts:
      - triangle area
      - quadrilateral area
      - coordinate plane
      - surface area

    confidence: inferred

    provenance:
      - CCS 2026-27 calendar
      - NC Grade 6 Math Standards
      - NC assessment/check-in grouping
```

### Confidence values

```text
official
strongly_inferred
inferred
```

Do not represent inferred CCS pacing as official.

## Curriculum Resolver

Provide a stable interface:

```text
resolve_curriculum(grade=6, date=2026-08-17)
```

Return:

```yaml
grade: 6
week_start: 2026-08-17
current:
  - NC.6.G.1
  - NC.6.G.3
  - NC.6.G.4
spiral:
  - decimals
  - fractions
  - GCF
  - LCM
confidence: inferred
school_year: 2026-2027
```

Generation consumes this object instead of independently researching curriculum.

## IMP-08 — Source/freshness cache

```yaml
sources:
  ccs_calendar:
    school_year: 2026-2027
    url: <source>
    last_verified: 2026-08-21
    refresh_policy: annual

  nc_grade_6_math:
    url: <source>
    last_verified: 2026-08-21
    refresh_policy: change_detection
```

Research externally only when:

- source missing
- freshness policy expires
- new school year begins
- source/version changes
- confidence is insufficient
- user explicitly requests fresh verification

## IMP-11 — Controlled refresh

```text
Authoritative Source Check
        ↓
Detect Change
        ↓
Review Diff
        ↓
Update Local Knowledge
        ↓
Record Version + Date
```

Never silently overwrite curriculum knowledge.

## Exit criteria

- Normal cached weeks require no curriculum web research.
- All mappings have provenance.
- Inferred pacing is explicitly labeled.
- NC standards and CCS pacing update independently.
- New school years do not require generation-logic changes.

## Expected cumulative improvement

- **Time:** 15–25% lower
- **Tokens:** 12–22% lower

---

# Phase 2 — Structured Generation and Verification

## Goal
Separate educational reasoning from rendering and make correctness reproducible.

## IMP-03 — Canonical Worksheet Spec

All generation first produces one structured representation:

```yaml
worksheet:
  grade: 6
  week_start: 2026-08-17
  duration_minutes: 15
  question_count: 32

curriculum:
  primary:
    - NC.6.G.1

sections:
  - id: A
    title: AREA BASICS
    questions:
      - number: 1
        type: computation
        skill: triangle_area
        standard: NC.6.G.1
        difficulty: easy
        prompt: Find the area of a triangle with base 8 and height 5.
        answer: 20
        verification:
          method: triangle_area
          inputs:
            base: 8
            height: 5
```

The Worksheet Spec becomes the single source of truth for:

- student worksheet
- answer key
- verification
- question counts
- standards
- difficulty
- sections
- QA expectations

The answer key must be rendered from the exact same question objects.

## IMP-04 — Deterministic verifier

Suggested modules:

```text
validators/
  arithmetic.py
  fractions.py
  decimals.py
  percentages.py
  equations.py
  algebra.py
  geometry.py
  patterns.py
  multiple_choice.py
  word_problem.py
```

Example:

```text
triangle_area(base=8, height=5)
→ 20
expected=20
→ PASS
```

Persist results:

```yaml
verification:
  total_questions: 32
  verified: 32
  failed: 0
  status: PASS
```

Verification failure blocks rendering.

## IMP-07 — Grade/course blueprints

Examples:

```yaml
# Grade 1
questions_per_worksheet: 20
sections:
  - number_sense
  - add_subtract
  - think_solve
  - bonus
```

```yaml
# Grades 4–6
questions_per_worksheet: 32
content_mix:
  current_curriculum: 21
  spiral: 8
  reasoning_challenge: 3
sections:
  A: 8
  B: 8
  C: 8
  D: 8
```

```yaml
# Grades 9/10
questions_per_worksheet: 32
grade_split:
  grade_9: 16
  grade_10: 16
```

## Exit criteria

- Every worksheet exists as a Worksheet Spec before Docs creation.
- Answer keys derive from Worksheet Spec.
- Deterministic questions independently verify.
- Verification failures block rendering.
- Blueprints enforce configured counts and content mix.

## Expected cumulative improvement vs baseline

- **Time:** 25–35% lower
- **Tokens:** 20–30% lower

---

# Phase 3 — Rendering and QA Optimization

## Goal
Stop repeatedly rediscovering stable Google Docs structure.

## IMP-02 — Template manifest/cache

Inspect each template once:

```text
templates/class-worksheet-32q/
  manifest.yaml
```

Example:

```yaml
template_version: 1.0

worksheet:
  document_id: <id>

answer_key:
  document_id: <id>

slots:
  title: <locator>
  subtitle: <locator>
  date: <locator>
  score: <locator>

sections:
  A: {question_slots: 1-8}
  B: {question_slots: 9-16}
  C: {question_slots: 17-24}
  D: {question_slots: 25-32}

styles:
  question_font_size: 9.5
  grade_1_question_font_size: 11

special:
  make24: true
  bonus: true

source_revision:
  worksheet: <revision-id>
  answer_key: <revision-id>
```

### Revision invalidation

```text
current_template_revision == cached_revision?
    YES → use manifest
    NO  → re-analyze, update manifest, review structure
```

## IMP-10 — Batch Docs operations

Reduce round trips by:

- grouping replacements
- grouping style changes
- grouping deletions
- reusing metadata already read
- avoiding full reads after every mutation

## IMP-05 — Targeted QA

After content verification, final QA should focus on rendering invariants:

```text
Expected question count == actual
Q1..Qn all present
No duplicate question numbers
Correct title/grade/date
Correct answer count
No unresolved placeholders
No old template questions
No truncated prompt
No obvious layout/render failure
```

Prefer targeted reads/text fingerprints over repeatedly loading full document structure.

## Exit criteria

- Unchanged templates require no full structural reinspection.
- Revision changes invalidate cached manifests.
- Rendering starts only from verified Worksheet Specs.
- QA checks content/render invariants efficiently.
- Visual structure remains intact.

## Expected cumulative improvement vs baseline

- **Time:** 40–55% lower
- **Tokens:** 40–55% lower

---

# Phase 4 — Pedagogical Intelligence and Reuse

## Goal
Improve continuity and novelty without creating a static question bank.

## IMP-12 — Question history and novelty fingerprints

Store structured history:

```yaml
skill: triangle_area
structure: numeric
base: 8
height: 5
difficulty: easy
week_used: 2026-08-17
```

Detect repetition across:

- numbers
- wording
- scenario
- operation pattern
- reasoning structure

Support policies such as:

```text
Review concepts from 2–4 weeks ago
while avoiding exact structural repetition.
```

Uses:

- controlled spiral review
- difficulty progression
- coverage analysis
- repetition avoidance
- fresh variants of proven archetypes

## IMP-13 — Visual QA invariants

Track:

- expected page count/range
- header/logo presence when configured
- no blank pages
- no overflow/truncation
- intact section blocks
- answer-key layout

Use visual QA only where it adds value beyond structured/text QA.

## Exit criteria

- Recent question history influences spiral selection.
- Repetition is measurable.
- Skill coverage can be reported over time.
- Visual QA catches defects text QA cannot.

---

# Phase 5 — Operational Hardening

## Goal
Make the workflow reliable for repeated production use.

## IMP-14 — Transactional publishing helper

```text
Final Gate Approved
        ↓
Validate run status
        ↓
Apply final names
        ↓
Move worksheet/key together
        ↓
Verify output folder
        ↓
Mark run PUBLISHED
```

Avoid partially published worksheet/key pairs.

## IMP-15 — Resume/recovery and regression tests

Implement:

- resume from last successful stage
- render retry without regenerating questions
- publish retry without regenerating docs
- template regression tests
- curriculum resolver tests
- validator unit tests
- Worksheet Spec schema validation
- known-answer fixtures
- gate-enforcement tests

## Exit criteria

- Interrupted runs continue without unnecessary work.
- Verified Worksheet Specs can be independently re-rendered.
- Publication failures do not trigger duplicate generation.
- Critical behavior is regression-tested.
- Human approval gates remain enforceable.

---

# 3. Recommended Implementation Order

| Rank | Improvement | Value / Effort |
|---:|---|---|
| 1 | Curriculum knowledge cache + resolver | ★★★★★ |
| 2 | Template manifest/cache | ★★★★★ |
| 3 | Canonical Worksheet Spec | ★★★★★ |
| 4 | Deterministic verification framework | ★★★★★ |
| 5 | Targeted final QA | ★★★★★ |
| 6 | Run telemetry | ★★★★½ |
| 7 | Grade/course blueprints | ★★★★½ |
| 8 | Batch Docs operations | ★★★★ |
| 9 | Source/freshness cache | ★★★★ |
| 10 | Run manifest/state | ★★★★ |
| 11 | Question history/novelty | ★★★½ |
| 12 | Transactional publishing | ★★★ |

Implementation should still follow phase dependencies rather than rank alone.

---

# 4. Proposed Repository Structure

```text
MTS Math Worksheet Generation/
├── README.md
├── design.md
├── archive/mts-math-worksheet-config.yaml
├── plan.md
│
├── knowledge/
│   ├── curriculum/
│   │   ├── nc/math/
│   │   │   ├── grade-1.yaml
│   │   │   ├── grade-4.yaml
│   │   │   ├── grade-5.yaml
│   │   │   ├── grade-6.yaml
│   │   │   ├── math-1.yaml
│   │   │   └── math-2.yaml
│   │   └── ccs/2026-2027/
│   │       ├── grade-1.yaml
│   │       ├── grade-4.yaml
│   │       ├── grade-5.yaml
│   │       ├── grade-6.yaml
│   │       ├── math-1.yaml
│   │       └── math-2.yaml
│   └── sources.yaml
│
├── blueprints/
│   ├── grade-1.yaml
│   ├── standard-32q.yaml
│   └── grade-9-10.yaml
│
├── schemas/
│   ├── worksheet-spec.schema.json
│   └── run-manifest.schema.json
│
├── templates/
│   └── class-worksheet-32q/
│       └── manifest.yaml
│
├── validators/
│   ├── arithmetic.py
│   ├── fractions.py
│   ├── decimals.py
│   ├── algebra.py
│   ├── equations.py
│   ├── geometry.py
│   ├── patterns.py
│   └── word_problem.py
│
├── runs/
│   └── <run-id>/
│       ├── manifest.yaml
│       ├── telemetry.json
│       └── worksheet-spec-*.yaml
│
└── outputs/
```

---

# 5. Phase Gates

### Phase 0 exit
- Baseline captured
- Run manifest operational
- Telemetry available

### Phase 1 exit
- Local resolver works for enabled grades/courses
- Provenance/confidence present
- Normal cached week needs no curriculum web research

### Phase 2 exit
- Worksheet Spec is source of truth
- Key derives from spec
- Verification blocks invalid worksheets

### Phase 3 exit
- Templates use cached manifests
- Revision invalidation works
- Targeted QA replaces unnecessary full rereads
- Measured savings versus Phase 0

### Phase 4 exit
- Question history prevents unwanted repetition
- Spiral history is usable
- Visual QA adds measurable value

### Phase 5 exit
- Runs resume cleanly
- Publishing is reliable
- Regression suite protects critical behavior

---

# 6. Non-Negotiable Quality Constraints

Optimization must not weaken:

1. Current MTS design/configuration rules.
2. Configured instruction precedence.
3. Human approval gates.
4. Final approval before publication.
5. Independent answer verification.
6. Reverification after impacted user edits.
7. Curriculum provenance/confidence.
8. Clear distinction between official and inferred CCS pacing.
9. Worksheet/key visual standards.
10. Correctness checks merely to save time or tokens.

---

# 7. First Implementation Slice

Start with:

```text
1. Add run manifest + telemetry
2. Build NC standards master
3. Build CCS 2026-27 weekly pacing maps
4. Implement curriculum resolver
5. Define Worksheet Spec schema
6. Convert one grade end-to-end
7. Add deterministic verifier for that grade
8. Measure against baseline
9. Generalize to remaining grades
10. Implement template caching/render optimization
```

**Recommended pilot: Grade 6**

Why Grade 6:

- full 32-question template
- arithmetic + fractions/decimals + geometry
- multi-step reasoning
- broad enough to exercise verifier design
- simpler than combined Grade 9/10

---

# 8. Definition of Success

A normal weekly run should:

1. Resolve curriculum primarily from validated local knowledge.
2. Generate a canonical Worksheet Spec.
3. Verify answers deterministically where possible.
4. Use cached template structure unless the template changed.
5. Perform targeted rather than redundant QA.
6. Preserve human approval gates.
7. Publish only approved worksheet/key pairs.
8. Produce measurable telemetry.
9. Resume after interruption without repeating completed work.
10. Use materially less execution time and model context than the Phase 0 baseline.
