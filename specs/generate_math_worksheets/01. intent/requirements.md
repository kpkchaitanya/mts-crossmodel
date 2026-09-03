# MTS Worksheet and Assessment Generation — Requirements v1.5

## 1. Purpose

Provide a repeatable, human-supervised, model-neutral workflow that produces curriculum-aligned, grade-appropriate, independently verified, template-consistent worksheet batches with answer keys across approved subject modules and Worksheet Types.

The requirements are organized by **Functional Area**. Functional Areas are the primary grouping concept for requirements, design, workflows, configuration, skills, tests, and traceability.

The default **Worksheet Type** is **Weekly Worksheet**.

---

## 2. Governing Source and Precedence

Canonical governing files:

1. `docs/knowledge/ai-native-sdlc-personal.md` — repository-wide development methodology and artifact reviewability standard.
2. `specs/generate_math_worksheets/01. intent/product_idea.md` — product intent, Functional Areas, Core Entities, scope, and vocabulary.
3. This requirements document — WHAT the system must do and acceptance criteria.
4. The approved architecture and design artifacts for this feature — HOW the system satisfies the requirements.
5. `config/*.yaml` and `subjects/<subject>/config/` — changeable defaults, feature flags, thresholds, IDs, and locations.
6. `skills/*.md` — reusable execution workflows.
7. `commands/*.md` — concise invocation entry points.
8. `AGENTS.md` — repository execution contract.
9. `.github/**` and other harness-specific files — thin compatibility adapters only.

Precedence:

**current user instruction > configuration > requirements/design default**

A run-level override must not be persisted unless the user explicitly requests persistence.

---

## 3. Functional Areas

| Code | Functional Area | Definition |
|---|---|---|
| SP | Setup Project | Establish long-lived project context, governance, and defaults. |
| SYC | Setup Yearly Curriculum | Establish academic-year curriculum progression. |
| PIC | Prepare Instructional Cycle | Establish the bounded instructional period/event. |
| RWC | Resolve Weekly Curriculum | Determine the actual curriculum scope for a specific week. |
| PB | Prepare Batch | Define worksheets to generate together. |
| PW | Prepare Worksheet | Define one worksheet's instructional and structural specification. |
| GW | Generate Worksheet | Create questions and expected answers. |
| VW | Verify Worksheet | Independently establish question/answer correctness. |
| FW | Format Worksheet | Render verified content into worksheet/key documents. |
| VAL | Validate Worksheet | Confirm completed artifacts are compliant and release-ready. |
| PUB | Publish Worksheet | Publish approved worksheet/key pairs. |
| DEL | Deliver Worksheet | Distribute published worksheet/key pairs to the target audience. |
| MT | Manage Templates | Maintain reusable template assets and revisions. |
| MW | Manage Workflow | Control gates, state, resume, invalidation, telemetry, and auditability. |

---

## 3.1 Requirements Hierarchy (M2 Review View)

This one-page hierarchy is the M2 review surface. Requirement ranges include every individual FR/NFR in the detailed sections below; those detailed requirements remain authoritative. "Not yet registered" means this feature specification does not currently define a dedicated command.

```text
L0. Product
`-- MTS Worksheet and Assessment Generation
    `-- L1. Full Scope Hierarchy
        |-- L2.1 Area: SP - Setup Project
        |   |-- L3 Capabilities: Project context, subject modules, supported grades, Worksheet Types, Worksheet Type lifecycle status and compatibility, override rules, model/harness neutrality
        |   |-- L3 Most Important Capabilities: Default Weekly Worksheet while preserving existing types and supporting approved SAT/ACT Worksheet Types
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-SP-001 through FR-SP-017
        |           `-- L4 One-line ACs: Load canonical artifacts; default to Weekly Worksheet unless another type is requested; resolve the selected subject and Worksheet Type. (Section 12: 1-2, 19)
        |
        |-- L2.2 Area: SYC - Setup Yearly Curriculum
        |   |-- L3 Capabilities: Grade/course yearly progression, NC standards, prerequisite relationships, provenance, targeted invalidation
        |   |-- L3 Most Important Capabilities: Reusable curriculum progression that is not reconstructed for every weekly run
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-SYC-001 through FR-SYC-007
        |           `-- L4 One-line ACs: Resolve or reuse the relevant Yearly Curriculum. (Section 12: 3)
        |
        |-- L2.3 Area: PIC - Prepare Instructional Cycle
        |   |-- L3 Capabilities: Weekly/review/diagnostic/exam-prep/special cycles, dates, calendar context, school-year week numbering and week resolution, grades, overrides
        |   |-- L3 Most Important Capabilities: Keep Instructional Cycle distinct from Batch and technical Run
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-PIC-001 through FR-PIC-010
        |           `-- L4 One-line ACs: Prepare the Instructional Cycle and resolve the requested week to a canonical week start. (Section 12: 4)
        |
        |-- L2.4 Area: RWC - Resolve Weekly Curriculum
        |   |-- L3 Capabilities: Cache-first scope resolution, source hierarchy, confidence labels, grade-specific scope, Gate 1
        |   |-- L3 Most Important Capabilities: Resolve current scope without representing inferred pacing as official CCS pacing
        |   |-- L3 Slash Commands: /generate-weekly-classworksheets
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-RWC-001 through FR-RWC-010
        |           `-- L4 One-line ACs: Resolve Weekly Curriculum with cache-first source-aware logic and stop at Gate 1 when enabled. (Section 12: 5-6)
        |
        |-- L2.5 Area: PB - Prepare Batch
        |   |-- L3 Capabilities: Multi-grade requests, shared overrides, expected Worksheet set, independent regeneration
        |   |-- L3 Most Important Capabilities: Detect missing or partial Batch outputs without regenerating unaffected Worksheets
        |   |-- L3 Slash Commands: /generate-weekly-classworksheets
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-PB-001 through FR-PB-006
        |           `-- L4 One-line ACs: Prepare the Batch and the requested individual Worksheet specifications. (Section 12: 7)
        |
        |-- L2.6 Area: PW - Prepare Worksheet
        |   |-- L3 Capabilities: Type, grade/course, counts, sections/days, content mix, difficulty and diversity planning, topic overrides, numbering scheme, template profile, overrides
        |   |-- L3 Most Important Capabilities: Produce an approved plan for each Worksheet before Questions are generated
        |   |-- L3 Slash Commands: /generate-weekly-classworksheets
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-PW-001 through FR-PW-028
        |           `-- L4 One-line ACs: Apply the selected/default Worksheet Type and prepare individual Worksheet specifications. (Section 12: 2, 7)
        |
        |-- L2.7 Area: GW - Generate Worksheet
        |   |-- L3 Capabilities: Canonical Worksheet Spec, immutable revisions, ordered sections/days, questions, answers, standards, difficulty/diversity checks, Gate 2
        |   |-- L3 Most Important Capabilities: Generate one complete editable Question set from which student and key artifacts derive
        |   |-- L3 Slash Commands: /generate-weekly-classworksheets
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-GW-001 through FR-GW-018
        |           `-- L4 One-line ACs: Generate the complete editable Question set and stop at Gate 2 when enabled. (Section 12: 8)
        |
        |-- L2.8 Area: VW - Verify Worksheet
        |   |-- L3 Capabilities: Deterministic recomputation, reasoning review, ambiguity checks, invalidation, reverification, Gate 3
        |   |-- L3 Most Important Capabilities: Verify every approved Question/Answer independently before rendering
        |   |-- L3 Slash Commands: /verify-worksheet
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-VW-001 through FR-VW-009
        |           `-- L4 One-line ACs: Independently verify every approved Question/Answer and stop at Gate 3 when enabled. (Section 12: 9)
        |
        |-- L2.9 Area: FW - Format Worksheet
        |   |-- L3 Capabilities: Template-copy rendering, editable Google Docs, separate key, shared notation source, answer display precision, placeholder cleanup, natural pagination, Gate 4
        |   |-- L3 Most Important Capabilities: Render student and key documents from the same verified Worksheet Spec without modifying masters
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-FW-001 through FR-FW-018
        |           `-- L4 One-line ACs: Render the Student Worksheet and Answer Key from the canonical Worksheet Spec without modifying masters. (Section 12: 10)
        |
        |-- L2.10 Area: VAL - Validate Worksheet
        |   |-- L3 Capabilities: Content QA, visual/layout QA, editability checks, artifact correspondence, final QA readiness
        |   |-- L3 Most Important Capabilities: Prove rendered output is complete, synchronized, readable, and release-ready
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-VAL-001 through FR-VAL-009
        |           `-- L4 One-line ACs: Perform targeted content and visual/layout QA, then stop at Gates 4 and 5 when enabled. (Section 12: 11-13)
        |
        |-- L2.11 Area: PUB - Publish Worksheet
        |   |-- L3 Capabilities: Final approval, paired publication, naming, destination verification, status/link recording
        |   |-- L3 Most Important Capabilities: Publish only approved Worksheet/Answer Key pairs to canonical outputs/
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-PUB-001 through FR-PUB-008
        |           `-- L4 One-line ACs: Publish only approved Worksheet/Answer Key pairs to the configured canonical destination. (Section 12: 14)
        |
        |-- L2.12 Area: DEL - Deliver Worksheet
        |   |-- L3 Capabilities: Audience destinations by grade/course, per-week delivery folders, idempotent re-delivery, staging retention, delivery evidence
        |   |-- L3 Most Important Capabilities: Put the approved batch where parents actually look, without changing approved content
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-DEL-001 through FR-DEL-011
        |           `-- L4 One-line ACs: Deliver each published pair into the configured per-grade, per-week audience destination and record the result. (Section 12: 15)
        |
        |-- L2.13 Area: MT - Manage Templates
        |   |-- L3 Capabilities: Template registration, revision manifest, cache validity, fallback templates, controlled template promotion
        |   |-- L3 Most Important Capabilities: Protect master templates and re-inspect only the template state affected by revision changes
        |   |-- L3 Slash Commands: Not yet registered
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-MT-001 through FR-MT-010
        |           `-- L4 One-line ACs: Copy, rather than modify, master templates when rendering the Worksheet/Answer Key pair. (Section 12: 10)
        |
        |-- L2.14 Area: MW - Manage Workflow
        |   |-- L3 Capabilities: Run manifests, hard gates, explicit recorded gate bypass, run-mode change control, resume, invalidation, telemetry, thin harness adapters, regression protection
        |   |-- L3 Most Important Capabilities: Enforce a resumable, auditable lifecycle without weakening human approval or correctness
        |   |-- L3 Slash Commands: /generate-weekly-classworksheets, /verify-worksheet
        |   `-- L3 Requirements And Acceptance
        |       `-- L4 Requirements: FR-MW-001 through FR-MW-025
        |           `-- L4 One-line ACs: Enforce all enabled gates or record explicit bypasses, persist run state/telemetry, resume valid work, hold shared infrastructure immutable mid-run, and preserve behavior through regression tests. (Section 12: 6, 8-9, 12-13, 16-18, 20)
        |
        `-- L2.15 Cross-Cutting: Non-Functional Requirements
            |-- L3 Capabilities: Correctness, synchronization, curriculum integrity, reviewability, quality, performance, portability, observability, subject and assessment extensibility
            |-- L3 Most Important Capabilities: Prioritize independently verified, reviewable, template-faithful, recoverable Worksheet/Answer Key pairs
            |-- L3 Slash Commands: Applies to all commands and workflows
            `-- L3 Requirements And Acceptance
                `-- L4 Requirements: NFR-001 through NFR-027
                    `-- L4 One-line ACs: A completed normal run satisfies the end-to-end acceptance scenario in Section 12, including verification, gates, rendering, validation, publication, delivery, persistence, resumption, and regression protection.
```

---

## 4. Core Entity Model

### 4.1 Instructional hierarchy

```text
Project
└── Subject
    └── Yearly Curriculum
        └── Instructional Cycle
            └── Weekly Curriculum
```

### 4.2 Worksheet-production hierarchy

```text
Instructional Cycle
└── Batch
    └── Worksheet
        └── Section / Day
            └── Question
                └── Answer
```

### 4.3 Rendered output relationship

```text
Worksheet
├── Student Worksheet Document
└── Answer Key
```

### 4.4 Entity definitions

| Entity | Definition |
|---|---|
| Project | Long-lived educational/product context containing reusable policies and defaults. |
| Subject | Academic discipline governed by the Project. |
| Yearly Curriculum | Planned progression of standards, concepts, prerequisites, and approximate sequence across the academic year. |
| Instructional Cycle | Bounded instructional period or event for which curriculum is resolved and materials may be generated. |
| Weekly Curriculum | Approved actual curriculum scope for a specific instructional week. |
| Batch | Collection of Worksheets requested/generated together for an Instructional Cycle. |
| Worksheet | One logical practice product for a target grade/course and Worksheet Type. |
| Worksheet Type | Configured worksheet mode, such as Weekly Worksheet, Class Worksheet, SAT, SAT Mini, ACT, or ACT Mini, with its sections, timing, scoring, template selection, and validation rules. |
| Section / Day | Ordered logical grouping of Questions within a Worksheet. |
| Question | Atomic student activity. |
| Answer | Expected correct response associated with a Question. |
| Student Worksheet Document | Student-facing rendered representation of a Worksheet. |
| Answer Key | Teacher-facing rendered representation derived from the same Worksheet question objects. |

Supporting entities include Grade/Course, Worksheet Type, Standard, Skill/Concept, Curriculum Source, Template, Formatting Profile, Verification Result, Validation Result, Approval, Run, Output Artifact, Destination, Audience Destination, and Delivery Record.

A **Destination** is where an approved artifact is published for the system of record. An **Audience Destination** is the grade/course-scoped location the target audience (parents/students) actually reads from. A **Delivery Record** captures which published pair was placed in which Audience Destination, for which week, and how.

A **Run** is a technical execution attempt and must remain distinct from an **Instructional Cycle** and a **Batch**.

---

# 5. Functional Requirements

## 5.1 Setup Project — SP

| ID | Requirement |
|---|---|
| FR-SP-001 | The system shall support a persistent Project containing subject, academic year, district/state context, supported grades/courses, educational guidelines, quality rules, curriculum-source policies, publishing defaults, and Worksheet Type defaults. |
| FR-SP-002 | The Math subject shall support Grade 1, Grade 4, Grade 5, Grade 6, and combined Grades 9 & 10 unless configuration overrides the enabled set. |
| FR-SP-003 | The system shall use **Worksheet Type** as the canonical term and shall not use “worksheet archetype” in governing requirements, design, configuration, workflows, schemas, or user-facing terminology. |
| FR-SP-004 | The default Worksheet Type shall be **Weekly Worksheet** when the user requests a worksheet or weekly batch without explicitly naming another type. |
| FR-SP-005 | Supported Worksheet Types shall include Weekly Worksheet, Class Worksheet, 4-Day Homework, Compact/Unbranded Worksheet, and Speed Math Worksheet. |
| FR-SP-006 | Existing Class, Homework, Compact/Unbranded, and Speed Math behavior shall remain available when Weekly becomes the default. |
| FR-SP-007 | Project defaults shall remain configurable without requiring workflow redesign. |
| FR-SP-008 | A current user instruction shall override configuration/default behavior for the current run. |
| FR-SP-009 | A run-level override shall not become persistent Project configuration unless explicitly requested by the user. |
| FR-SP-010 | The system shall preserve a model-neutral and harness-neutral canonical contract so ChatGPT, Codex, Copilot, Claude, Claude Code, or equivalent harnesses can follow the same governing behavior. |
| FR-SP-011 | The system shall support approved subject modules, initially Math and ELA, while preserving subject-specific curriculum, generation, verification, and layout rules. |
| FR-SP-012 | The system shall support approved Worksheet Types, initially SAT, SAT Mini, ACT, and ACT Mini, whose sections, timing, scoring, template selection, and validation rules remain configuration-driven. |
| FR-SP-013 | Subject modules and Worksheet Types shall reuse the shared Run, gate, artifact-pairing, template-protection, publication, and evidence lifecycle unless an approved cross-cutting requirement explicitly changes it. |
| FR-SP-014 | A new subject module or Worksheet Type shall not be enabled until its requirements, configuration, knowledge, templates, verification rules, and regression tests are approved. |
| FR-SP-015 | Every Worksheet Type shall declare a lifecycle status. Only an active Worksheet Type shall execute a run; a draft or disabled type shall be refused with an explanation rather than silently substituted. |
| FR-SP-016 | A Worksheet Type shall declare the subjects it is compatible with, and a request pairing a subject with an incompatible Worksheet Type shall be refused before generation begins. |
| FR-SP-017 | Known readiness blockers for a Worksheet Type shall be reported to the user, and a run shall proceed despite them only on explicit current-user acceptance for that run. |

## 5.2 Setup Yearly Curriculum — SYC

| ID | Requirement |
|---|---|
| FR-SYC-001 | The system shall support a Yearly Curriculum for each enabled grade/course. |
| FR-SYC-002 | A Yearly Curriculum shall capture standards, major units/concepts, prerequisite relationships, concept progression, approximate sequence, and source provenance. |
| FR-SYC-003 | The long-term progressive Math backbone shall be treated as conceptual progression guidance, not as official CCS pacing. |
| FR-SYC-004 | The Yearly Curriculum shall support `builds_from` and `leads_to` relationships so weekly worksheets can intentionally spiral prerequisites and prepare future concepts. |
| FR-SYC-005 | The Yearly Curriculum shall reference authoritative NC standards and maintain source/freshness metadata. |
| FR-SYC-006 | Yearly Curriculum data shall be reusable across weekly cycles and shall not need to be reconstructed from raw external standards on every worksheet run. |
| FR-SYC-007 | Updating Yearly Curriculum shall invalidate only dependent downstream curriculum resolutions/runs whose assumptions changed. |

## 5.3 Prepare Instructional Cycle — PIC

| ID | Requirement |
|---|---|
| FR-PIC-001 | The system shall represent the working period/event as an **Instructional Cycle**. |
| FR-PIC-002 | Instructional Cycle types shall support at least weekly, review, diagnostic, exam-prep, and special cycles, while allowing future configured types. |
| FR-PIC-003 | An Instructional Cycle shall capture start/end dates, academic calendar context, target grades/courses, and special overrides. |
| FR-PIC-004 | The system shall consider holidays, teacher workdays, breaks, shortened weeks, and other relevant school-calendar context when preparing a weekly cycle. |
| FR-PIC-005 | The Instructional Cycle shall remain distinct from a Batch and a Run. |
| FR-PIC-006 | Multiple Batches may be associated with one Instructional Cycle. |
| FR-PIC-007 | The same Instructional Cycle may support different Subjects or special-generation Batches without redefining the instructional dates. |
| FR-PIC-008 | The system shall maintain a configured school-year week numbering origin so an instructional week can be identified consistently across runs. |
| FR-PIC-009 | A requested week shall be resolvable as the current week, an instructional week number, or an explicit date, and each form shall resolve to the same canonical week start so all three name the same Instructional Cycle. |
| FR-PIC-010 | The resolved week start and its derived instructional week number shall be reported to the user and recorded in run state, so the reviewer can confirm which week was generated. |

## 5.4 Resolve Weekly Curriculum — RWC

| ID | Requirement |
|---|---|
| FR-RWC-001 | For a weekly Instructional Cycle, the system shall resolve a **Weekly Curriculum** for each target grade/course before worksheet generation. |
| FR-RWC-002 | Weekly Curriculum resolution shall begin from the Yearly Curriculum and progressive context rather than reconstructing scope from scratch. |
| FR-RWC-003 | Resolution shall use local curriculum caches first during a valid normal run. |
| FR-RWC-004 | Source authority shall prioritize: (1) CCS current curriculum/pacing evidence, (2) CCS guidance/current academic calendar, (3) NC DPI / NC Standard Course of Study / unpacking/progression sources, (4) NC assessment/check-in specifications when useful, and (5) logical instructional sequencing. |
| FR-RWC-005 | External research/refresh shall occur only on documented fallback conditions such as cache miss, source changed/expired, insufficient confidence, contradiction, or explicit freshness request. |
| FR-RWC-006 | Each Weekly Curriculum scope shall include topic/unit, standards, spiral/prerequisite review, progression context, recommended question count/difficulty, source/basis, and confidence. |
| FR-RWC-007 | Allowed curriculum confidence labels shall include `confirmed`, `strongly_inferred`, and `inferred`. |
| FR-RWC-008 | Inferred pacing shall never be presented as exact or official CCS pacing. |
| FR-RWC-009 | For combined Grades 9 & 10, Weekly Curriculum shall be resolved independently for Grade 9 and Grade 10 even when rendered in one combined worksheet. |
| FR-RWC-010 | Weekly Curriculum shall remain advisory until explicitly approved at Gate 1 when that gate is enabled. |

## 5.5 Prepare Batch — PB

| ID | Requirement |
|---|---|
| FR-PB-001 | The system shall support a **Batch** representing worksheets requested/generated together. |
| FR-PB-002 | A Batch shall identify its Instructional Cycle, Subject, target grades/courses, Worksheet Types, destinations, and shared overrides. |
| FR-PB-003 | A Batch may contain one, several, or all enabled grades/courses. |
| FR-PB-004 | Each Worksheet in a Batch shall retain independent grade/course curriculum scope even when sharing the same Instructional Cycle. |
| FR-PB-005 | The system shall support regenerating a single Worksheet from a Batch without forcing unrelated Worksheets to regenerate. |
| FR-PB-006 | Batch state shall record the expected Worksheet set so missing or partial outputs can be detected. |

## 5.6 Prepare Worksheet — PW

| ID | Requirement |
|---|---|
| FR-PW-001 | Each Worksheet shall be prepared from an approved curriculum scope before Questions are generated. |
| FR-PW-002 | Worksheet preparation shall capture grade/course, Worksheet Type, question count, duration when applicable, sections/days, content mix, difficulty profile, template/formatting profile, and run-level overrides. |
| FR-PW-003 | Weekly Worksheet shall be the default Worksheet Type unless the user explicitly selects another type. |
| FR-PW-004 | A Weekly Worksheet shall use five ordered sections: Monday — Foundation; Tuesday — Discover; Wednesday — Practice; Thursday — Apply & Review; Friday — Mastery. |
| FR-PW-005 | Monday — Foundation shall emphasize facts, mental math, prerequisites, and quick review. |
| FR-PW-006 | Tuesday — Discover shall emphasize the current concept, patterns, representations, and guided skill development. |
| FR-PW-007 | Wednesday — Practice shall emphasize core skill practice with increasing difficulty. |
| FR-PW-008 | Thursday — Apply & Review shall emphasize word problems, connections, application, and spiral review. |
| FR-PW-009 | Friday — Mastery shall emphasize challenge, explanation, error analysis, puzzles, or mastery evidence. |
| FR-PW-010 | Default Weekly Worksheet question counts shall be configurable by school level and initially target Primary/Elementary = 10/day (50/week), Middle = 8/day (40/week), High = 5/day (25/week). |
| FR-PW-011 | Weekly question counts may be overridden for a grade/course or individual run. |
| FR-PW-012 | Weekly Worksheets shall use natural pagination; the renderer shall not shrink content or working space solely to force a fixed page count. |
| FR-PW-013 | Class Worksheet behavior shall remain supported, including prior grade-specific counts where configured. |
| FR-PW-014 | 4-Day Homework shall remain a separate supported Worksheet Type and may use continuity from class/current concepts, reinforcement, and slight extension. |
| FR-PW-015 | Compact/Unbranded Worksheet shall permit simplified presentation and user-defined compact question/page constraints. |
| FR-PW-016 | Speed Math Worksheet shall support fluency, mental math, concept application, multi-step/pattern work, and configured challenge/bonus structures. |
| FR-PW-017 | For combined Grades 9 & 10, the Worksheet shall preserve the configured grade split while keeping the curriculum resolution independent. The combined `questions_per_week` shall equal `questions_per_day` multiplied by the number of configured weekly sections; the course split shall sum to that combined weekly count. |
| FR-PW-018 | Default content mix shall be configuration-driven; current baseline is 65% current curriculum, 25% spiral review, and 10% reasoning/challenge. |
| FR-PW-019 | Difficulty and diversity shall be independent, run-selectable settings on a shared configured ordinal scale, each with a configured default, so a run can be made more or less ambitious without redefining the Worksheet Type. |
| FR-PW-020 | The selected difficulty shall produce a planned difficulty for every question slot before authoring, such that difficulty increases across the week and within each day rather than being applied ad hoc during authoring. |
| FR-PW-021 | The selected diversity shall determine a minimum number of distinct skills per day and the cadence at which spiral-review skills are substituted into the day's skill sequence, so no day drills a single skill. |
| FR-PW-022 | The system shall support topic overrides that force a specified share — as a percentage or a fixed count — of a named grade/course's questions onto a named topic. |
| FR-PW-023 | A topic override on a daily-sectioned Worksheet Type shall apply to each day's questions, not once across the whole week, and the applied overrides shall be reported to the user. |
| FR-PW-024 | Question numbering shall be defined by the Worksheet Type. Weekly Worksheets shall number questions locally within each day rather than continuously across the week, and the chosen scheme shall govern rendering and QA consistently. |
| FR-PW-025 | Form Diversity shall be an independent, run-selectable setting on the configured ordinal scale, with a configured default. It controls how a skill is represented and assessed, not which skills are covered or how difficulty is assigned. |
| FR-PW-026 | Form Diversity shall use reusable mathematical form families described by cognitive action, representation, context when applicable, and response type; it shall not require a prewritten question inventory for every grade/topic combination. |
| FR-PW-027 | A profiled topic shall declare only its compatible form families. When a profile applies, the planner shall select compatible forms using a persisted per-run variation seed. |
| FR-PW-028 | A topic without an active compatibility profile shall preserve established generation behavior until a profile is added and validated. |

## 5.7 Generate Worksheet — GW

| ID | Requirement |
|---|---|
| FR-GW-001 | Question generation shall create one canonical **Worksheet Spec** before document rendering. |
| FR-GW-002 | The Worksheet Spec shall contain Worksheet metadata, curriculum context, ordered Sections/Days, Questions, Answers, skills/concepts, difficulty, standards where applicable, and verification status. |
| FR-GW-003 | Student Worksheet and Answer Key shall derive from the same canonical question objects. |
| FR-GW-004 | Question generation shall emphasize understanding over memorization. |
| FR-GW-005 | Questions shall incorporate mental math, number sense, pattern recognition, progressive difficulty, application, reasoning, variation, and age-appropriate challenge where appropriate. |
| FR-GW-006 | The generator shall avoid excessive rote repetition. |
| FR-GW-007 | Questions shall be sufficiently specified and avoid unintended ambiguity. |
| FR-GW-008 | Grade 1 content shall use age-appropriate number ranges, language, font/space expectations, and foundational strategies such as place value and Make 10 where applicable. |
| FR-GW-009 | Grades 4–6 content may include fractions, decimals, multi-step reasoning, operations, patterns, and applications appropriate to the approved Weekly Curriculum. |
| FR-GW-010 | Grades 9–10 content may include algebra, radicals, functions, factoring, equations, and other approved course-level concepts. |
| FR-GW-011 | Challenge/bonus questions shall be subject to the same verification and ambiguity standards as standard Questions. |
| FR-GW-012 | When Gate 2 is enabled, the complete editable proposed Question set shall be presented for explicit human review before verification proceeds. |
| FR-GW-013 | Each Worksheet Spec revision shall be persisted immutably. An edit shall create a new revision rather than overwrite an existing one, and rewriting an existing revision with different content shall be rejected. |
| FR-GW-014 | Gate 2 shall fail closed until every Worksheet planned for the Batch has a persisted Worksheet Spec reference, so no Worksheet can advance on unrecorded content. |
| FR-GW-015 | A generated Question set shall pass the configured difficulty-progression and skill-diversity checks before it is persisted or presented for review; a failing set shall be revised rather than accepted. |
| FR-GW-016 | A Question generated for an active Form Diversity profile shall persist its selected `form_family`, `cognitive_action`, `representation`, `response_type`, and `variation_seed` in the canonical Worksheet Spec. |
| FR-GW-017 | At configured High Form Diversity, a form family shall not repeat within a day, and an unused compatible form shall be selected before the same skill/form combination repeats within the week. |
| FR-GW-018 | Before Gate 2, deterministic QA shall reject normalized duplicate prompts, missing or incompatible form metadata, and form reuse that violates the configured Form Diversity policy. |

## 5.8 Verify Worksheet — VW

| ID | Requirement |
|---|---|
| FR-VW-001 | Every approved Question and Answer shall be independently verified before document rendering. |
| FR-VW-002 | The Answer generated alongside a Question shall never be treated as evidence that the Answer is correct. |
| FR-VW-003 | Deterministic verification utilities shall be used for supported arithmetic, fractions, decimals, percentages, equations, algebra, geometry, patterns, and other machine-checkable forms. |
| FR-VW-004 | Independent reasoning review shall verify wording, sufficient information, conceptual correctness, grade appropriateness, ambiguity, multiple unintended answers, pattern uniqueness, units, and question-answer consistency. |
| FR-VW-005 | Items not supported by deterministic verification shall still receive explicit reasoning review. |
| FR-VW-006 | Any edited Question shall invalidate its prior verification and shall be reverified before downstream rendering or publication. |
| FR-VW-007 | Unresolved verification failures or ambiguities shall block Format Worksheet. |
| FR-VW-008 | Verification shall produce counts of checked, failed, and ambiguous Questions plus corrections or unresolved issues. |
| FR-VW-009 | When Gate 3 is enabled, the independent verification summary shall be presented for explicit approval before rendering. |

## 5.9 Format Worksheet — FW

| ID | Requirement |
|---|---|
| FR-FW-001 | Verified logical Worksheet content shall be rendered using configured Google Docs templates and formatting profiles. |
| FR-FW-002 | A master template shall always be copied before population; the master shall never be edited directly. |
| FR-FW-003 | Rendering shall preserve the approved template's layout, section colors, readability, answer space, and editability unless explicitly overridden. |
| FR-FW-004 | Student-facing math notation shall be readable plain notation such as `3/8`; raw LaTeX such as `\\frac{3}{8}` shall not appear in final student-facing documents. |
| FR-FW-005 | Grade 1 shall use larger, age-appropriate font/spacing when configured. |
| FR-FW-006 | Each Worksheet shall produce a separate Student Worksheet Document and Answer Key unless an explicit alternate draft format is requested. |
| FR-FW-007 | When a combined editable draft contains questions and answer key in one document, it shall include `[[PAGE BREAK — ANSWER KEY]]` immediately before the Answer Key; final document rendering shall convert the marker to a real page break. |
| FR-FW-008 | Answer Key numbering and sections shall match the Student Worksheet exactly. |
| FR-FW-009 | Weekly Worksheets shall be allowed to spill naturally across pages to preserve readability and student working space. |
| FR-FW-010 | Formatting shall minimize unnecessary whitespace without creating a cramped page. |
| FR-FW-011 | Explicit user-specified page constraints shall be honored when compatible with readability and completeness. |
| FR-FW-012 | When Gate 4 is enabled, draft Worksheet/Answer Key links and formatting/layout QA results shall be presented for explicit review. |
| FR-FW-013 | Student-facing content shall never expose raw code or programming syntax, including expressions such as `25**(1/2)`, `x^2`, `*`, `/`, `>=`, and `<=`. |
| FR-FW-014 | Display notation shall be produced from a single shared subject notation source rather than ad hoc per-question formatting, so exponents, roots, fractions, operators, geometry symbols, sets/intervals, and absolute value render consistently. |
| FR-FW-015 | Grade-band notation guidance shall be available to authoring as advisory support; it shall not replace the required reasoning review for grade appropriateness. |
| FR-FW-016 | Numeric answers shall be displayed using a configured decimal precision, applied only when the raw value carries more decimal digits than a configured noise threshold, so an intentionally exact short decimal is never truncated or padded. |
| FR-FW-017 | Answer display formatting shall never alter the stored answer used for verification. |
| FR-FW-018 | A rendered Worksheet shall populate only the configured number of questions, remove unused numbered placeholders inherited from the template, and contain no empty numbered rows or unresolved placeholders. |

## 5.10 Validate Worksheet — VAL

| ID | Requirement |
|---|---|
| FR-VAL-001 | Validation shall occur after rendering and before publishing. |
| FR-VAL-002 | Content QA shall confirm expected question count, numbering, grade/course labels, dates/titles, all intended Sections/Days, answer count, worksheet-key correspondence, and absence of missing/stale placeholders. |
| FR-VAL-003 | Visual/layout QA shall inspect pagination, blank/large gaps, wrapping, section balance, table geometry where applicable, font readability, answer space, colors, and key density. |
| FR-VAL-004 | Targeted content QA shall not replace required visual/layout QA. |
| FR-VAL-005 | The system shall reject accidental blank pages or unexplained large whitespace when they materially reduce print quality. |
| FR-VAL-006 | Validation shall confirm no Question or Answer was lost, duplicated, truncated, or rendered inconsistently. |
| FR-VAL-007 | Validation shall confirm the final artifact remains editable when editable Google Docs are required. |
| FR-VAL-008 | The final QA result shall be complete before Gate 5 / Publish Approval. |
| FR-VAL-009 | Content QA shall apply the Worksheet Type's question-numbering scheme. A numbering check written for one scheme shall not be applied to a Worksheet Type using another, and a mismatch shall be corrected rather than resolved by skipping QA. |

## 5.11 Publish Worksheet — PUB

| ID | Requirement |
|---|---|
| FR-PUB-001 | The system shall never publish before explicit final approval when Gate 5 is enabled. |
| FR-PUB-002 | Only approved Student Worksheet / Answer Key pairs shall be published to the canonical `outputs/` destination. |
| FR-PUB-003 | `outputs-copilot/` shall remain staging/dump space only and shall never be treated as published output. |
| FR-PUB-004 | Publishing shall apply the configured naming convention for the Worksheet and corresponding `_KEY`. |
| FR-PUB-005 | After publication, the system shall verify the final file name and parent/destination folder. |
| FR-PUB-006 | Worksheet and Answer Key shall be treated as one logical publish set so partial or mismatched outputs are surfaced as an error. |
| FR-PUB-007 | The configured Google Drive output destination shall remain changeable through configuration or explicit run override. |
| FR-PUB-008 | Publication status and final artifact links shall be recorded in run state. |

## 5.12 Deliver Worksheet — DEL

Publication completes **Staging**. Delivery is the separate **Final Delivery** step that puts approved material in front of the target audience.

| ID | Requirement |
|---|---|
| FR-DEL-001 | The system shall distinguish Staging from Final Delivery. Staging locations, including `outputs-copilot/` and the configured staging Drive folders, shall never be treated as audience-facing delivery. |
| FR-DEL-002 | Final Delivery shall distribute only an already-published Worksheet/Answer Key pair; it shall not generate, render, renumber, edit, or re-verify content. |
| FR-DEL-003 | Final Delivery shall require the recorded Publish Approval for the delivered revision when Gate 5 is enabled, and shall not introduce an additional human gate. |
| FR-DEL-004 | Each grade/course shall have a configured Audience Destination parent location; a grade/course with no configured Audience Destination shall fail closed rather than fall back to a shared or default location. |
| FR-DEL-005 | Each delivered Batch shall be placed in a per-week folder within the grade/course Audience Destination, named by a configurable pattern that defaults to `Week_<WEEK_OF>`, where `WEEK_OF` is the ISO Monday of the delivered instructional week. |
| FR-DEL-006 | Final Delivery shall be idempotent: re-delivering a week shall resolve and reuse that week's existing folder rather than create a duplicate, so a correction replaces rather than multiplies audience material. |
| FR-DEL-007 | The delivery mode shall be configurable; the default shall retain the staged artifacts as the audit trail rather than removing them from Staging. |
| FR-DEL-008 | Whether the Answer Key accompanies the Student Worksheet into the Audience Destination shall be a configuration decision, not a rendering or authoring decision. |
| FR-DEL-009 | Audience Destinations, week-folder naming, delivery mode, and answer-key delivery shall be changeable through configuration or explicit run override, and shall not be embedded in code or scripts. |
| FR-DEL-010 | Each Final Delivery shall record a Delivery Record in run state identifying the source published artifacts, grade/course, instructional week, delivery mode, destination folders, and resulting audience-facing links. |
| FR-DEL-011 | Final Delivery shall be run-selectable with a configured default. Requesting delivery without publication shall be refused rather than silently downgraded, and the resolved delivery decision shall be echoed to the user before the run proceeds and reported in the run summary. |

## 5.13 Manage Templates — MT

| ID | Requirement |
|---|---|
| FR-MT-001 | Templates shall be registered by Worksheet Type and/or grade/course formatting need. |
| FR-MT-002 | Template management shall support Student Worksheet and Answer Key masters. |
| FR-MT-003 | The system shall maintain a template revision manifest or equivalent revision metadata. |
| FR-MT-004 | Live template revision shall be compared with the cached revision before expensive structural reinspection. |
| FR-MT-005 | A cache HIT may avoid full structural reinspection but shall not eliminate final visual/layout QA. |
| FR-MT-006 | A changed template revision shall invalidate only the affected template cache entry and trigger targeted reinspection. |
| FR-MT-007 | Existing standard-template fallbacks shall remain available until dedicated Grade 1, Grades 9/10, or Weekly templates are approved. |
| FR-MT-008 | Branded and unbranded/compact formatting shall be supported as configured Worksheet/Formatting Profiles. |
| FR-MT-009 | A user-edited visual document may become a new approved template only through an explicit promotion/versioning action; generation shall not silently replace masters. |
| FR-MT-010 | Rendering shall obtain its working document only by copying a master. No rendering path shall be capable of writing to a master template. |

## 5.14 Manage Workflow — MW

| ID | Requirement |
|---|---|
| FR-MW-001 | Each execution shall initialize or resume a Run manifest under `runs/`. |
| FR-MW-002 | A Run shall capture Instructional Cycle, Batch, target Worksheets, stage state, approvals, verification status, artifact links, and telemetry. |
| FR-MW-003 | Enabled human gates shall be hard state transitions and shall not be bypassed for optimization or speed. Bypass is permitted only under the explicit, recorded conditions in FR-MW-018 through FR-MW-021. |
| FR-MW-004 | Gate 1 shall review Weekly Curriculum/curriculum scope before Question generation. |
| FR-MW-005 | Gate 2 shall review the complete editable Question set. |
| FR-MW-006 | Gate 3 shall review independent verification results. |
| FR-MW-007 | Gate 4 shall review formatted Worksheet/Answer Key artifacts and rendering QA. |
| FR-MW-008 | Gate 5 shall review final QA and grant explicit Publish Approval. |
| FR-MW-009 | The workflow shall resume from the next valid incomplete state when approved upstream inputs have not changed. |
| FR-MW-010 | A changed Question shall invalidate dependent verification and downstream artifacts for that Question/Worksheet as appropriate. |
| FR-MW-011 | A changed Weekly Curriculum or Worksheet preparation decision shall invalidate dependent Questions and downstream states. |
| FR-MW-012 | A changed template revision shall invalidate template cache/rendering state without unnecessarily invalidating approved curriculum or Questions. |
| FR-MW-013 | Telemetry shall record available stage timing, tool calls, cache hits/misses, retries, approvals, verification status, and document links. |
| FR-MW-014 | Token telemetry shall be recorded only when authoritative usage data is available; otherwise it shall be `null`, not estimated. |
| FR-MW-015 | Harness-specific adapters shall remain thin and shall point to canonical requirements/design/skills rather than redefine behavior. |
| FR-MW-016 | Workflow optimizations shall preserve correctness, provenance, human gates, and reviewability. |
| FR-MW-017 | Regression tests shall protect critical existing behavior before repository, workflow, or cross-harness changes are treated as production-ready. |
| FR-MW-018 | A gate shall be bypassable only on an explicit current-user instruction for that run. Bypass shall never be inferred, defaulted, or applied silently. |
| FR-MW-019 | Every bypassed gate shall be named explicitly to the user and recorded in run state, so the audit trail shows which human review was skipped and on whose instruction. |
| FR-MW-020 | Bypassing a gate shall remove only its stop-and-approve checkpoint. It shall never waive the canonical Worksheet Spec, independent verification of every item, reverification after edits, or required visual QA. |
| FR-MW-021 | Where an approval must be recorded before an action, bypass shall not remove the recorded approval; it shall only remove the interactive wait. |
| FR-MW-022 | During a run, shared source code, configuration, master templates, and canonical workflow documents shall be treated as immutable operational infrastructure. |
| FR-MW-023 | On an execution, verification, rendering, QA, authentication, or publication failure, the affected step shall stop before retrying or producing replacement artifacts, and the observed issue, supporting evidence, and affected artifact state shall be reported. |
| FR-MW-024 | A change to shared code, configuration, templates, or canonical workflow documents during a run shall require explicit current-user approval, including the smallest proposed change and its gate-invalidation impact. An instruction to continue a run shall not by itself authorize such a change. |
| FR-MW-025 | Run-local evidence may record commands, diagnostics, and QA results, but shall not alter the approved workflow, effective config, or gate requirements. |

---

# 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | **Correctness:** Mathematical/content correctness takes precedence over generation speed. |
| NFR-002 | **Verification completeness:** 100% of approved Questions shall receive independent verification before rendering. |
| NFR-003 | **Consistency:** Student Worksheet and Answer Key shall remain synchronized through a single canonical Worksheet Spec. |
| NFR-004 | **Curriculum integrity:** Source provenance and confidence shall remain visible and inferred pacing shall not be misrepresented as confirmed. |
| NFR-005 | **Reviewability:** Human-review outputs shall be concise enough to inspect while retaining all unique decisions, corrections, risks, and evidence. |
| NFR-006 | **Print quality:** Final documents shall be print-friendly, readable, balanced, and free of avoidable blank pages or extreme whitespace. |
| NFR-007 | **Editability:** Final Google Docs shall remain editable when the configured workflow requires editable outputs. |
| NFR-008 | **Template fidelity:** Approved structure and visual behavior shall be preserved unless explicitly overridden. |
| NFR-009 | **Performance:** Valid caches and template revision guards shall reduce repeated expensive work without weakening correctness or QA. |
| NFR-010 | **Fallback safety:** External research or full template reinspection shall be triggered when cache confidence/freshness is insufficient. |
| NFR-011 | **Resumability:** Interrupted or reviewed workflows shall resume from the latest valid state instead of unnecessarily restarting. |
| NFR-012 | **Maintainability:** Stable behavior shall live in canonical requirements/design/skills and executable source shall be organized by Functional Area capability and subject specialization, not duplicated across prompts, adapters, scripts, or mixed-purpose folders. |
| NFR-013 | **Portability:** Governing behavior shall remain model-neutral and harness-neutral. |
| NFR-014 | **Master protection:** Master templates shall never be directly modified during generation. |
| NFR-015 | **Observability:** Runs shall retain enough state and telemetry to diagnose failures, retries, cache use, approvals, publication, and links to the affected Subject, Grade/Course, Cycle, Batch, Worksheet, and artifact records. |
| NFR-016 | **Cache freshness:** Cache use shall never be treated as proof that inferred curriculum is official or current. |
| NFR-017 | **Batch scalability:** Generating multiple grades/courses together shall not reduce verification, QA, or human-gate quality. |
| NFR-018 | **Deterministic naming:** File names and worksheet/key pairing shall be predictable and configuration-driven. |
| NFR-019 | **Backward compatibility:** Introducing Weekly Worksheet as the default shall not remove existing supported Worksheet Types. |
| NFR-020 | **Behavior preservation:** Migration or optimization shall not be considered successful unless established worksheet-generation functionality remains regression-tested and legacy mixed roots are not retired until replacement source, tests, and data paths pass their regression gate. |
| NFR-021 | **Artifact reviewability:** Consequential product artifacts shall be concise, structured, traceable, and include a visual summary when relationships, flow, state, hierarchy, boundaries, comparison, or traceability cannot be understood efficiently from prose alone. |
| NFR-022 | **Lifecycle traceability:** Requirements, architecture, design, implementation, verification evidence, and runtime evidence shall trace to the authoritative Product Idea, the Functional Areas they satisfy, and the durable entity hierarchy from Subject to Worksheet when runtime records are involved. |
| NFR-023 | **Responsibility placement:** Human approval/accountability, AI interpretation/generation/reasoning, deterministic software execution, configuration defaults, master knowledge, and transaction evidence shall remain explicitly separated. Repeatable deterministic behavior shall not rely solely on prompts or AI reasoning, and durable facts shall not be hard-coded in source. |
| NFR-024 | **Executable quality evidence:** Critical quality attributes, including verification completeness, worksheet/key synchronization, gate enforcement, master-template protection, publication-pair integrity, and repository organization invariants, shall have automated fitness functions or documented manual verification evidence when automation is not practical. |
| NFR-025 | **Subject and Worksheet Type extensibility:** New subject modules and Worksheet Types shall be additive through subject executable behavior, approved knowledge, configuration, templates, verification rules, and tests without changing shared Run control, gate enforcement, artifact synchronization, template protection, publication-pair semantics, data ownership, or run-evidence behavior unless an approved cross-cutting requirement requires the change. |
| NFR-026 | **Delivery integrity:** Content reaching the audience shall be byte-identical to the approved published artifact; Final Delivery shall have no capability to alter worksheet or key content. |
| NFR-027 | **Delivery repeatability:** Re-delivering the same instructional week shall converge on one audience-facing folder per grade/course per week rather than accumulating duplicates, so the audience is never presented with ambiguous versions. |

---

# 7. Human Gate Model

| Gate | Functional Area Boundary | Approval |
|---|---|---|
| Gate 1 | Resolve Weekly Curriculum → Prepare/Generate Worksheet | Curriculum Scope Review |
| Gate 2 | Generate Worksheet → Verify Worksheet | Question Review |
| Gate 3 | Verify Worksheet → Format Worksheet | Verification Review |
| Gate 4 | Format/Validate Worksheet → Final QA | Formatting Review |
| Gate 5 | Validate Worksheet → Publish Worksheet | Publish Approval |

Never publish before configured final approval.

Gate 5 authorizes both publication and the subsequent Final Delivery of that same approved revision. Deliver Worksheet adds no gate of its own and must never run against material Gate 5 has not approved.

A gate may be bypassed only on an explicit current-user instruction for the current run, and every bypass must be named and recorded. Bypass removes the stop-and-approve checkpoint only; the canonical Worksheet Spec, independent verification of every item, reverification after edits, and required visual QA remain enforced.

---

# 8. Default Weekly Worksheet Behavior

When the user says, for example:

> Generate this week's Math worksheets for Grades 1, 4, 5, 6, and 9/10.

and does not specify another Worksheet Type, the request shall resolve to **Weekly Worksheet**.

Default weekly structure:

1. Monday — Foundation
2. Tuesday — Discover
3. Wednesday — Practice
4. Thursday — Apply & Review
5. Friday — Mastery

Default counts:

- Primary / Elementary: 10/day = 50/week
- Middle School: 8/day = 40/week
- High School: 5/day = 25/week

These are defaults, not hard-coded limits. Explicit user instructions override them.

Weekly documents shall paginate naturally rather than being compressed to a fixed page count.

---

# 9. Constraints

- Google Drive / Google Docs are the current primary document and publishing platform.
- Master templates must not be edited directly.
- Human approval gates are mandatory whenever enabled.
- Exact public CCS weekly pacing may not always be accessible.
- Inference must be labeled with the configured confidence model.
- Weekly Worksheet and prior Worksheet Types must coexist.
- Readable math notation must be used; raw LaTeX is prohibited in final student-facing content.
- Raw code syntax is likewise prohibited in student-facing content; display notation comes from the shared subject notation source.
- Readability and completeness take precedence over forcing Weekly Worksheets into a fixed number of pages.
- `outputs/` is canonical final output; `outputs-copilot/` is staging only.
- Audience-facing delivery locations are separate from `outputs/` and are owned per grade/course by configuration.
- The current repository/configuration may temporarily contain older Class-oriented defaults; updated requirements are authoritative product intent until configuration/design are reconciled.

---

# 10. Assumptions

- The system has access to the canonical repository, curriculum caches, templates, and output folders.
- A human reviewer is available at configured gates.
- Curriculum caches and source metadata can be maintained over time.
- Template IDs/revision metadata can be read before rendering.
- Existing Math generation behavior forms the regression baseline during refactoring.
- Weekly Worksheet becoming the default does not delete other Worksheet Types.
- Combined Grades 9 & 10 may remain a combined physical product while their curriculum scopes are resolved independently.
- Configuration, schemas, design, skills, and tests will be updated to align with this requirement model.

---

# 11. Risks and Open Decisions

| ID | Risk / Open Decision |
|---|---|
| R-001 | Current YAML remains Class-oriented and must be reconciled with Weekly Worksheet as the new default. |
| R-002 | Exact grade-band mapping for weekly question defaults, especially Grade 6, still needs explicit canonical configuration. |
| R-003 | Dedicated Weekly template registrations may be incomplete. |
| R-004 | Dedicated Grade 1 and Grades 9/10 templates may still use standard fallbacks. |
| R-005 | Stale curriculum caches could produce outdated weekly scope if freshness controls fail. |
| R-006 | Inferred pacing could be accidentally presented as official without confidence enforcement. |
| R-007 | Advanced or conceptual items may exceed deterministic verifier coverage and depend on careful reasoning review. |
| R-008 | Post-verification Question edits can create answer/key defects unless invalidation/reverification is enforced. |
| R-009 | Weekly natural pagination can create layout variation that requires stronger visual QA. |
| R-010 | User-edited template promotion/versioning needs a clear controlled process. |
| R-011 | Different AI harnesses could drift if adapters begin duplicating governing logic. |
| R-012 | Publishing could become partial if Worksheet and Answer Key are not treated as one logical publish set. |
| R-013 | Semantic regression tests alone may miss visual-template regressions; visual regression scope remains to be finalized. |
| R-014 | Repository migration/cutover must not retire the working baseline before end-to-end validation. |
| R-015 | An unconfigured or mistyped Audience Destination could deliver a grade's material to the wrong families; delivery must fail closed rather than fall back. |
| R-016 | Re-delivering a corrected week could leave stale material visible to the audience if week-folder resolution is not idempotent. |
| R-017 | Gate bypass is convenient and could normalize into a default, eroding human review unless every bypass stays explicit, named, and recorded. |
| R-018 | Fixing shared code or configuration mid-run can silently invalidate already-approved gates, so run-mode changes must stop and seek approval rather than being repaired in place. |
| R-019 | QA checks written for one question-numbering scheme produce false results on a Worksheet Type using another, creating pressure to skip QA rather than correct the check. |

---

# 12. Acceptance Criteria

A normal run can begin with a request such as:

> Generate this week's MTS Math worksheets.

The system must be able to:

1. Load canonical project requirements, design, configuration, and workflow instructions.
2. Default to **Weekly Worksheet** unless another Worksheet Type is explicitly requested.
3. Resolve or reuse the relevant Yearly Curriculum.
4. Prepare the Instructional Cycle, resolving the requested week to a canonical week start and reporting the resolved instructional week.
5. Resolve Weekly Curriculum for each target grade/course using cache-first source-aware logic.
6. Stop at Gate 1 for curriculum approval when enabled, or record an explicit, named bypass.
7. Prepare the Batch and individual Worksheet specifications, including the planned difficulty, diversity, and any topic overrides.
8. Generate a complete editable Question set, persist it as an immutable revision, and stop at Gate 2 when enabled.
9. Independently verify every approved Question/Answer and stop at Gate 3 when enabled.
10. Render Student Worksheet and Answer Key from the same canonical Worksheet Spec without modifying master templates.
11. Perform targeted content QA and visual/layout QA.
12. Stop at Gate 4 for formatting review when enabled.
13. Complete final validation and stop at Gate 5 for explicit Publish Approval.
14. Publish only approved Worksheet/Answer Key pairs to the configured canonical destination.
15. Deliver each published pair into its grade/course Audience Destination under the week's delivery folder, reusing that folder on re-delivery, and record the delivery evidence.
16. Persist run state and authoritative telemetry.
17. Resume from the latest valid state after interruption or edits.
18. Preserve existing supported Worksheet Types and all critical behavior through regression testing.
19. Resolve the requested subject module and Worksheet Type, and reject unapproved, inactive, or incompatible extensions before generation begins.
20. Stop and seek explicit approval, rather than repairing shared code, configuration, templates, or canonical workflow documents in place, when a run step fails.
