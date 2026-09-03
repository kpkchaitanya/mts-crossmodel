# MTS Worksheet and Assessment Generation — Product Idea

## Product Idea Brief

**Project name:** MTS Worksheet and Assessment Generation

**One-sentence idea:**  
A model-neutral, human-supervised worksheet production system that turns subject curriculum and a specific instructional cycle into curriculum-aligned, grade-appropriate, independently verified, template-consistent worksheet batches and answer keys, with Weekly Worksheet as the default Worksheet Type.

**Who is this for?**
- MTS curriculum owners and educators who define curriculum intent, instructional priorities, and quality expectations.
- Tutors and teachers who review curriculum scope, worksheet questions, verification results, formatting, and final outputs.
- AI workflow operators and maintainers using ChatGPT, Codex, GitHub Copilot, Claude, Claude Code, or other compatible harnesses.

**What problem does it solve?**  
Worksheet-generation behavior has evolved across prompts, configuration, templates, skills, workflows, curriculum caches, run state, validation rules, and user decisions. Rebuilding or changing the workflow can easily lose important behavior such as curriculum alignment, progression, grade adaptation, human review gates, independent answer verification, worksheet/key consistency, template fidelity, pagination, naming, and controlled publishing. The product provides one structured, reviewable system that preserves these behaviors and organizes them around stable Functional Areas and Core Entities.

**What outcome should the user get?**  
The user should be able to establish a project and yearly curriculum once, prepare an instructional cycle, resolve the actual weekly curriculum, define a worksheet batch, generate one or more worksheets, review and edit them through explicit human gates, independently verify every answer, render and validate the finished documents, and publish only approved worksheet/key pairs. The process should be resumable, repeatable, auditable, and portable across AI models and harnesses.

## Methodology Alignment And Artifact Role

This Product Idea is the M1 Human Intent and Domain Ontology artifact for MTS Worksheet and Assessment Generation. It is the authoritative source for the product's purpose, vocabulary, Functional Areas, core entities, scope, and quality intent.

The repository-wide development methodology is [AI-Native SDLC --- Personal](../../docs/knowledge/ai-native-sdlc-personal.md). Requirements, architecture, design, implementation, tests, evaluations, and runtime evidence must preserve and trace back to the intent in this document while following that methodology's reviewability, responsibility-allocation, and continuous-verification standards.

For this product, those standards require that:

- Consequential artifacts use a reviewable progression of visual summary, concise structured source, and detail on demand where it improves comprehension.
- Human approval and accountability, AI generation and reasoning, and deterministic software responsibilities remain explicit and separated.
- Deterministic worksheet behavior is implemented in code; variable behavior is configuration; curriculum facts and templates are maintained as knowledge; AI reasoning is reserved for generation, interpretation, and ambiguity review.
- Product decisions remain traceable from intent through requirements, design, implementation, verification, and run evidence.

**What are the most important user actions?**
1. Setup a Project and its persistent educational and operational defaults.
2. Setup the Yearly Curriculum for each supported grade/course.
3. Prepare an Instructional Cycle such as a weekly cycle, review cycle, diagnostic cycle, exam-prep cycle, or special cycle.
4. Resolve Weekly Curriculum from yearly progression, school calendar, district pacing evidence, standards, and source confidence.
5. Prepare a Batch defining the grades/courses and worksheets to generate together.
6. Prepare each Worksheet by selecting or accepting the default Worksheet Type, curriculum scope, counts, section structure, difficulty, content mix, template, and overrides.
7. Review and approve curriculum scope at Gate 1.
8. Review and edit generated questions at Gate 2.
9. Review independent verification results at Gate 3.
10. Review rendered worksheet/key artifacts at Gate 4.
11. Approve final publishing at Gate 5.
12. Regenerate or resume only the affected portion of a prior run after edits or failures.
13. Manage reusable templates and formatting profiles without editing master templates directly.

**What should the first version include?**
- Supported initial subject modules: Math and ELA. Math supports Grade 1, Grade 4, Grade 5, Grade 6, and combined Grades 9 & 10 unless configuration overrides the enabled set.
- Batch generation for one, several, or all enabled grades/courses.
- Functional Areas as the primary organizing model for requirements, design, workflows, configuration, and tests.
- Core entity model covering Project, Subject, Yearly Curriculum, Instructional Cycle, Weekly Curriculum, Batch, Worksheet, Section/Day, Question, Answer, Student Worksheet Document, and Answer Key.
- Supporting entities including Grade/Course, Worksheet Type, Standard, Skill/Concept, Curriculum Source, Template, Formatting Profile, Verification Result, Validation Result, Approval, Run, Output Artifact, and Destination.
- Weekly Worksheet as the default `worksheet_type`.
- Supported worksheet types: Weekly Worksheet, Class Worksheet, 4-Day Homework, Compact/Unbranded Worksheet, and Speed Math Worksheet.
- Supported Worksheet Types include SAT, SAT Mini, ACT, and ACT Mini. Each type defines its sections, counts, timing, scoring, template selection, and validation rules while reusing the shared lifecycle.
- Default Weekly Worksheet structure:
  - Monday — Foundation
  - Tuesday — Discover
  - Wednesday — Practice
  - Thursday — Apply & Review
  - Friday — Mastery
- Default weekly question counts:
  - Primary / Elementary: 10 questions/day, 50/week
  - Middle School: 8 questions/day, 40/week
  - High School: 5 questions/day, 25/week
  - Counts remain configurable and may be overridden per run.
- Natural pagination for Weekly Worksheets; readability and working space take precedence over forcing a fixed page count.
- Yearly curriculum setup using standards, concept progression, approximate sequence, prerequisites, and source metadata.
- Weekly curriculum resolution using yearly curriculum, CCS pacing evidence, NC standards, school calendar, progressive context, source provenance, and confidence labels.
- Cache-first curriculum resolution with controlled external fallback.
- Default instructional mix of current curriculum, spiral review, and reasoning/challenge as configured.
- Grade-appropriate question generation emphasizing understanding, mental math, number sense, patterns, progressive difficulty, application, reasoning, and variation.
- A single canonical Worksheet Spec as the source for both student worksheet and answer key.
- Independent verification of every approved answer, with deterministic verification where supported and reasoning review where required.
- Automatic reverification of affected questions after edits.
- Five explicit human approval gates.
- Template-copy rendering; master templates are never edited directly.
- Template revision tracking and targeted reinspection.
- Separate editable student worksheet and verified answer key.
- Plain readable math notation such as `3/8`; no raw LaTeX in student-facing documents.
- Targeted content QA and visual/layout QA.
- Staging versus final publishing semantics.
- Run manifest, resumability, invalidation rules, telemetry, and authoritative-only token reporting.
- Cross-model and cross-harness operation through thin adapters without duplicating governing behavior.
- Regression tests that protect behavior during workflow or repository changes.

**What should the first version exclude?**
- Automatic publishing without the configured final human approval.
- Editing master templates directly.
- Treating inferred district pacing as confirmed or official.
- A new teacher-facing web application or LMS/SIS integration.
- New subject or assessment behavior without approved subject requirements, configuration, templates, verification rules, and regression tests.
- Automatic PDF export unless explicitly configured or requested.
- Replacing approved visual templates solely to modernize styling.
- Major redesign of generation logic that cannot be regression-tested against the existing Math workflow.
- Unvalidated worksheet types or generation modes not represented in the supported configuration/workflow.
- Estimated token telemetry when authoritative usage data is unavailable.

**What quality expectations matter from the beginning?**
- 100% of approved questions and answers must receive independent verification before rendering.
- Worksheet and answer key must derive from the same canonical question objects and stay synchronized.
- Any changed question must invalidate and rerun its affected verification.
- Unresolved verification failures or ambiguities must block rendering.
- Curriculum scope must preserve source provenance and confidence; inference must never be presented as confirmed district pacing.
- Content must be grade-appropriate, unambiguous, sufficiently specified, and instructional rather than rote.
- Output must be editable, print-friendly, readable, and consistent with the approved template and formatting profile.
- Weekly Worksheets must preserve the five-day instructional progression and allow natural pagination.
- Master templates must never be modified during generation.
- Content QA and visual/layout QA are both required; one does not replace the other.
- Final names, dates, grade/course labels, question counts, numbering, worksheet/key correspondence, and destination folder must be validated before publishing.
- Enabled human gates are hard workflow transitions and cannot be silently bypassed for speed.
- Requirements and design must remain concise enough for human/AI review while preserving all unique behavior.
- The workflow must be model-neutral, harness-neutral, resumable, observable, and regression-testable.
- Adding a subject module or Worksheet Type must preserve shared gates, artifact synchronization, template protection, publication-pair semantics, and run evidence unless an approved cross-cutting requirement changes them.

**What risks or unknowns should be clarified before implementation?**
- Exact grade-band mapping for Primary / Elementary / Middle / High weekly question-count defaults, especially Grade 6.
- Whether combined Grades 9 & 10 will continue as one physical worksheet while maintaining independently resolved curricula.
- Whether dedicated Grade 1 and Grades 9/10 Weekly templates will replace current fallbacks.
- Final registered Weekly Worksheet master template IDs for each grade band.
- How approved user-edited worksheets are promoted into a new template revision.
- Exact regression baseline: semantic/content comparison only, or rendered visual comparison as well.
- Deterministic verifier coverage for advanced algebra, geometry, puzzles, and non-numeric reasoning.
- Whether publishing worksheet/key pairs must be transactional so partial publication cannot occur.
- The grade/course, section, timing, scoring, template, and verification requirements for ELA, SAT, SAT Mini, ACT, and ACT Mini.
- When the legacy repository can be retired after consolidated workflow validation.

---

## Functional Area Model

Functional Areas are the primary organizing dimension for product requirements, design, configuration, workflows, skills, tests, and traceability.

| # | Functional Area | Definition | Primary Entities / Contents |
|---:|---|---|---|
| 1 | Setup Project | Establish the long-lived project context, governance, educational defaults, and operating rules. | Project, Subject, academic year, district/state, grades/courses, Worksheet Types, guidelines, source policies, quality policies |
| 2 | Setup Yearly Curriculum | Establish the curriculum progression for the academic year. | Yearly Curriculum, Standard, Skill/Concept, prerequisites, progression, approximate sequence, curriculum sources |
| 3 | Prepare Instructional Cycle | Establish the bounded instructional period or event for which materials will be generated. | Instructional Cycle, dates, cycle type, school-calendar context, grades/courses, special overrides |
| 4 | Resolve Weekly Curriculum | Determine the actual curriculum scope for the specific instructional week. | Weekly Curriculum, yearly progression, pacing evidence, standards, spiral review, builds-from/leads-to, source confidence |
| 5 | Prepare Batch | Define the collection of worksheets to produce together. | Batch, target grades/courses, worksheet requests, shared cycle context, batch overrides, destination |
| 6 | Prepare Worksheet | Define the instructional and structural specification for one worksheet. | Worksheet, Worksheet Type, curriculum scope, Section/Day plan, question counts, content mix, difficulty, template/profile |
| 7 | Generate Worksheet | Create worksheet questions and expected answers from the approved specification. | Worksheet Spec, Section/Day, Question, Answer, Skill/Concept, Standard |
| 8 | Verify Worksheet | Independently establish mathematical/content correctness and question-answer validity. | Verification Result, recalculation, reasoning review, ambiguity checks, reverification |
| 9 | Format Worksheet | Render verified logical content into student and teacher documents. | Template, Formatting Profile, Student Worksheet Document, Answer Key |
| 10 | Validate Worksheet | Confirm the rendered product is complete, compliant, consistent, and ready for approval/publishing. | Validation Result, content QA, visual QA, pagination, numbering, worksheet/key correspondence |
| 11 | Publish Worksheet | Publish approved worksheet/key pairs to the canonical destination. | Approval, Output Artifact, Destination, published status |
| 12 | Manage Templates | Maintain reusable presentation assets and their lifecycle independently of worksheet runs. | Template, Formatting Profile, revision manifest, fallback, promoted template revision |
| 13 | Manage Workflow | Control state, human gates, retries, resumability, invalidation, telemetry, and auditability. | Run, Approval, Gate, state, telemetry, cache status |

---

## Core Entity Model

### Instructional hierarchy

```text
Project
└── Subject
    └── Yearly Curriculum
        └── Instructional Cycle
            └── Weekly Curriculum
```

### Worksheet-production hierarchy

```text
Instructional Cycle
└── Batch
    └── Worksheet
        └── Section / Day
            └── Question
                └── Answer
```

### Rendered outputs

```text
Worksheet
├── Student Worksheet Document
└── Answer Key
```

### Entity definitions

| Entity | Definition | Example |
|---|---|---|
| Project | Long-lived educational/product context containing reusable rules and defaults. | MTS Math 2026–27 |
| Subject | Academic discipline governed by the project. | Math |
| Yearly Curriculum | Planned grade/course progression across an academic year. | Grade 4 Math 2026–27 |
| Instructional Cycle | Bounded instructional period or event for which curriculum is resolved and materials may be produced. | Week of Aug 24, 2026 |
| Weekly Curriculum | Approved actual curriculum scope for a specific instructional week. | Place Value + Addition/Subtraction + Multiplicative Comparison |
| Batch | Collection of worksheets requested/generated together within an instructional cycle. | Math Weekly Batch — Aug 24 |
| Worksheet | One logical student practice product for a grade/course and Worksheet Type. | Grade 4 Weekly Worksheet |
| Section / Day | Ordered logical grouping inside a worksheet. | Monday — Foundation |
| Question | Atomic student activity. | Compare 54,321 and 54,231 using >, <, or =. |
| Answer | Expected correct response to a question. | 54,321 > 54,231 |
| Student Worksheet Document | Student-facing rendered representation of the Worksheet. | MTS-Math-4thGrade-WeeklyWorksheet-2026-08-24 |
| Answer Key | Teacher-facing rendered representation generated from the same Worksheet questions. | ..._KEY |

### Supporting entities

- **Grade / Course** — target instructional level, e.g. Grade 4 or Grades 9 & 10.
- **Worksheet Type** — Weekly, Class, 4-Day Homework, Compact/Unbranded, Speed Math.
- **Standard** — external curriculum expectation such as an NC Standard Course of Study identifier.
- **Skill / Concept** — instructional competency or mathematical idea.
- **Curriculum Source** — district/state/source evidence with authority, freshness, and provenance.
- **Template** — approved master document structure copied for rendering.
- **Formatting Profile** — reusable visual and print rules.
- **Verification Result** — evidence that content/answers have been independently checked.
- **Validation Result** — evidence that the completed artifact meets release requirements.
- **Approval** — explicit human decision permitting a workflow transition.
- **Run** — one technical execution attempt; distinct from an Instructional Cycle or Batch.
- **Output Artifact** — concrete generated file.
- **Destination** — approved publication or staging location.

---

## Canonical Vocabulary Decisions

- Use **Functional Area** as the grouping concept across requirements and design.
- Use **Worksheet Type**, not “worksheet archetype.”
- **Weekly Worksheet** is the default Worksheet Type.
- Use **Instructional Cycle**, not “Business Cycle.”
- Use **Setup Yearly Curriculum** before **Resolve Weekly Curriculum**.
- Keep **Batch** distinct from Instructional Cycle and Run.
- **Verify Worksheet** means establish correctness of questions/answers.
- **Validate Worksheet** means establish completeness, compliance, consistency, and release readiness of the rendered product.
