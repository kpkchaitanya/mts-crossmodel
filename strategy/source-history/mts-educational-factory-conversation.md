---
document_id: HIST-MTS-EDU-001
title: MTS Educational Factory — Conversation History and Decision Handoff
artifact_type: historical-context
status: historical-reference
version: 1.0
prepared_on: 2026-11-01
source_context: MTS-ELA-RC-Ready-Made-Sources project conversation and referenced MTS work
authority: fallback-only
target_project: MTS Software Factory
proposed_target_repository: kpkchaitanya/mts-software-factory
current_repository: kpkchaitanya/mts-crossmodel
---

# MTS Educational Factory — Historical Conversation Handoff

> **Read this first:** This is a *curated reconstruction of the architecture discussion and selected prior MTS ELA/Math context*, **not** a verbatim or exhaustive transcript. It is a cross-model fallback for ChatGPT, Codex, Copilot, Claude and human reviewers. Where there is any conflict, use the latest **explicitly approved authoritative strategy, requirement, ADR, specification or verified code/evidence**. Historical assistant proposals are **not** approvals. Reinspect sources before implementation.
>
> **No automatic authority:** Being written to GitHub does not turn a draft proposal into an architectural decision. Unresolved items below require review and ADRs. The original conversation remains the deeper fallback where accessible.

## 1. Executive handoff

The discussion evolved from repairing recurring **MTS ELA reading-comprehension worksheet generation** defects into defining a **cross-subject MTS Educational Content Factory**, then into adopting a broader **AI-native, model-agnostic MTS Software Factory**. The user supplied three inputs to rationalize, rather than combine blindly:

1. **AI-SDLC Software Factory Strategy** — the user-authored `AI-SDLC-SOFTWARE-FACTORY-STRATEGY.md`, governing methodology and target way of working. Its M0–M8 station model, 3D architecture, atomic artifacts/IDs, traceability, observability, evidence gates, human authority and continuous learning should anchor design. **The attachment is not yet asserted to exist in this GitHub repository.**
2. **[`kpkchaitanya/mts-crossmodel`](https://github.com/kpkchaitanya/mts-crossmodel)** — earlier partially implemented, model-agnostic MTS software and AI SDLC experiment. Has useful working or partially working Math/shared assets, specifications, workflow logic, tests, instructions and a cross-model philosophy. Must be inventoried and tested, not copied uncritically.
3. **The MTS Educational Factory experience** from preceding Math and ELA projects — the domain goals, curricula, subject capabilities, format rules, YPQA method, verified November 2026 artifacts, defects, QA gates and lessons. This is the empirical product/domain input, not the governing software engineering method.

**Proposed repository destination:** `kpkchaitanya/mts-software-factory`. The conversation's latest recommendation was to **create a new repository and selectively migrate** working assets, rather than rename the old repository. **This is a recommendation, not completed work or final authorization**. The existing `mts-crossmodel` must be preserved during comparison and migration.

**Historical project boundary:** The MTS educational product family is the initial proving ground. Whether the *platform* ultimately supports non-educational products is a design question, not a settled expansion commitment.

## 2. Status taxonomy for reading this history

- **Confirmed user direction** — stated by the user or explicitly accepted in the discussion; still subject to formal specification/ADR as appropriate.
- **Observed / verified** — a result documented by tests, published artifacts or connected system readback; validity scoped to the tested release.
- **Proposed** — architectural suggestions discussed but not yet approved or built.
- **Open** — unresolved decision, required inspection, incomplete integration or risk.
- **Superseded** — a previously discussed approach replaced by later user direction.

## 3. Confirmed directions and design constraints

| ID | Historical decision or direction | Status | Interpretation / follow-up |
|---|---|---|---|
| H-001 | Use the **MTS Software Factory** name; candidate repository `mts-software-factory` | Confirmed user naming direction | New repository has not been created |
| H-002 | Do not restrict factory scope to ELA or worksheets | Confirmed | Include Math and future subjects; avoid hardcoded ELA assumptions |
| H-003 | ELA encompasses **Reading, Writing, Vocabulary**; grammar/editing has also been identified as a capability | Confirmed | Preserve each area's own pedagogy, inputs and verification |
| H-004 | **Curriculum, Lesson Plans, Diagnostics, Cheatsheets, Mock Testing** should be available to **all subjects** | Confirmed | Worksheets/practice, study guides and performance analysis were additionally proposed as universal capabilities |
| H-005 | Support **ChatGPT, Codex, GitHub Copilot, Claude**, and future models without duplicating domain rules | Confirmed | Thin tool-specific adapters; portable specs, schemas, code and tests |
| H-006 | Treat the attached **AI-SDLC Software Factory Strategy** as the desired target engineering approach | Confirmed | Use M0–M8, 3D analysis and traceability rather than only new folders or prompts |
| H-007 | Rationalize the **three sources** before migration | Confirmed | Compare ownership, reuse, conflicts, evidence and gaps |
| H-008 | Start a **new ChatGPT Project and chat** with durable onboarding instructions | Confirmed | Keep ChatGPT Project instructions short and non-prescriptive |
| H-009 | Store onboarding in GitHub `strategy/project-starting-instructions.md` | Completed | [Starting instructions](https://github.com/kpkchaitanya/mts-crossmodel/blob/master/strategy/project-starting-instructions.md) |
| H-010 | Preserve this conversation's essential background as a **fallback historical source** | Confirmed | This document implements the chosen Option C |
| H-011 | Favor requirements, architecture, design, evidence, observations and delta-driven iteration; do not implement a migration without review | Confirmed working direction | Record material decisions as ADRs / approved artifacts |

### Three independent modeling axes

The discussion established the importance of **Subject × Learning Capability × Educational Product/Output**, while recognizing that some capabilities (curriculum, diagnostics and mock testing) are also products or workflows. The final ontology and cardinalities **remain to be resolved**, not forced into a rigid three-field schema.

Examples:

- Math × Algebra × Diagnostic test
- ELA × Reading comprehension × Weekly worksheet
- ELA × Vocabulary × Practice / assessment
- ELA × Writing × Lesson plan / rubric
- Physics × Waves and Sound × Study guide or mock assessment

**Important distinction:** Factory services (governance, source management, orchestration, evaluation, release and observability) are not the same as subject domain knowledge or rendered educational artifacts.

## 4. Source-rationalization logic developed in the conversation

| Input | Strongest contribution | Risk if copied verbatim | Intended handling |
|---|---|---|---|
| AI-SDLC strategy | Product/production/engineering/learning systems, M0–M8 stations, 3D architecture, human-reviewable atomic artifacts, intent-to-outcome observability and feedback | Large aspirational architecture without proven vertical slices | Treat as governing method; implement proportionately |
| `mts-crossmodel` | Real repository, Math modules, shared curriculum/worksheet/verification/publishing packages, configs, schemas, tests, cross-model adapter conventions | Legacy scope, unverified code paths, incomplete ELA registration, overlapping rules | Inventory; Adopt / Refactor / Replace / Archive individually |
| MTS Educational context | Grade/course requirements, curriculum progression, source integrity, ELA RC/YPQA standards, demonstrated PDFs and specific defects | Treating a good November snapshot as a fully reusable autonomous product | Encode governed requirements and negative tests; integrate into shared factory |

**Suggested decision procedure:** preserve an asset only after documenting source path, authority, behavior, current test evidence, dependency/ownership, target path, disposition, verification and migration risk.

## 5. Facts inspected in `mts-crossmodel`

During the architecture conversation the connected GitHub account was accessed and `kpkchaitanya/mts-crossmodel` was inspected. At that point it was **public**, default branch **`master`**, with existing directories including `src/mts/`, `data/config/`, `schemas/`, `specs/`, `docs/`, `commands/`, `tests/`, `skills/`, `workflows/` and `.github/`.

Noteworthy observed files/modules:

- `constitution.md`, `ontology.md`, `program.md`, `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`: model-independent intent and thin adapter patterns already exist.
- `src/mts/curriculum/`, `src/mts/infrastructure/`, `src/mts/instructional_cycles/`, `src/mts/publishing/`, `src/mts/setup_project/`, `src/mts/template_management/`, `src/mts/verification/`, `src/mts/workflow_management/`, `src/mts/worksheets/`: candidate reusable modules.
- `src/mts/subjects/math/` exists. An equivalent implemented `src/mts/subjects/ela/` was **not present in that inspection**.
- `docs/subjects/ela/requirements.md` exists but is high-level; `data/config/subjects/ela.yaml` includes weekly arc, verification settings, publishing naming and printing configuration.
- `schemas/worksheet-spec.schema.json` and `schemas/run-manifest.schema.json` support a shared **Worksheet Spec / Run Manifest** design.
- `specs/generate_math_worksheets/` shows significant prior Math-specific work.
- The existing README described Math functionality more mature than ELA; its generic `/generate-worksheet` path was reported as not yet registering ELA generation.
- Existing `outputs/ela` is a repository staging/output concept, while the ELA November 2 release used a designated **Google Drive publication folder**. These need distinct configurable roles.

**Do not conflate inspected existence with independent functional verification.** Re-run baseline tests before migrating modules, and check the latest repository HEAD.

## 6. MTS educational-domain scope and rationale

### 6.1 Cross-subject horizontal capabilities

The user explicitly named five universally applicable capabilities:

1. **Curriculum** — standards, goals, prerequisite progression, pacing and mastery plans.
2. **Lesson Plans** — instructional objectives, teaching strategies, practice and reflection.
3. **Diagnostics** — identify initial proficiency, gaps and misconceptions.
4. **Cheatsheets** — concise, reviewed conceptual and procedural references.
5. **Mock Testing** — realistic full or partial assessment simulations.

The discussion **proposed** also treating **Worksheets/Practice**, **Study Guides** and **Performance Analysis** as shared capabilities. Whether these are their own domain services, subcapabilities, or product templates is an explicit ontology decision for the new project.

The educational lifecycle discussed was:

`Curriculum / objectives → Lesson planning → Learning/practice/reference → Diagnostic and mock assessment → Performance evidence → Remediation or progression → Curriculum update`.

Diagnostics can occur *before* teaching as well as *after* practice; this is not a fixed sequential conveyor.

### 6.2 Subject-specific depth

- **Math:** elementary through SAT/ACT; concept mastery, reasoning, number sense, algebra/geometry, correct math solutions, problem difficulty, spiraling/review, visual learning, diagnostics and cheatsheets.
- **ELA:** reading comprehension, poetry, fiction/nonfiction, vocabulary-in-context, writing, grammar/editing, evidence-backed explanations, YPQA/poetry analysis and grade-appropriate complexity.
- **Future subjects:** Physics/Science were discussed as examples, **not** confirmed migrated subject modules.

### 6.3 Educational quality is primary

A repeated user emphasis: optimize **student understanding and reasoning** over superficial formatting or memorization. Print efficiency supports learning but cannot override passage substance, answer correctness or readable typography.

## 7. Concrete ELA RC learnings and verified release baseline

The latest ELA discussion produced a specific Style A PDF baseline for the week of **2026-11-02**, for Grade 4 and Grade 6.

### 7.1 Style A educational/format decisions

- **Student worksheet:** US Letter, exactly **two pages**, typically **9.5 pt** passage/questions, **bold stems**, regular choices.
- Prose: **two balanced reading columns**, paragraph labels `[1]`, `[2]`, etc., no first-line indent, **3.5 pt** paragraph spacing.
- Poetry: preserve verse lineation, label **stanzas** rather than individual lines; reset numbering for each passage.
- Fiction planning range approximately **500–650 words**; under **400** requires an exception. Grade 4/6 poetry target at least **32 nonblank verse lines**.
- Aim for **10 questions per passage**; allow **8–10** based on real fit and coverage-preserving backfill; protect vocabulary-in-context coverage (normally two items).
- Teacher key: separate **two-page enhanced YPQA**, including three poetry-reading passes, scope/stanza map, question keyword, prediction, evidence and **POE** (process of elimination).
- Maintain original question IDs separately from printed numbers. Both artifacts must derive from the same selected question set.
- For **ready-made source preserving** mode, do **not** impose Style A reflow or paragraph labels on publisher pages; preserve original source content/layout/questions/answers. This is distinct from generated/adapted RC.

### 7.2 Verified November 2 delivery (scope-specific)

| Grade | Poetry | Prose | Selected question counts | Published files |
|---|---|---|---|---|
| 4 | `The Village Blacksmith` (48 lines) | `The Secret Garden` Chapter IX educational adaptation (566 words) | **10 poetry + 10 fiction** | [Student](https://drive.google.com/file/d/1Q3ldZTvhCBhLbU9Yio9Fn2S3c1ofmkmq/view), [YPQA key](https://drive.google.com/file/d/1vN7RhtWT-tiDeoGCjz3rs5UNIWBusMRz/view) |
| 6 | `A Psalm of Life` (36 lines) | `The Wild Robot` Chapters 18–20 educational adaptation (591 words) | **10 poetry + 9 fiction** | [Student](https://drive.google.com/file/d/1jNvHCmpNkJuyAH9pqtdqHocaA3J6n0QB/view), [YPQA key](https://drive.google.com/file/d/1HfWTs9XYzF1Km8U5l8dK8OR2E9vSvCPO/view) |

Published into authorized Drive folder: [MTS official output](https://drive.google.com/drive/folders/1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS). Older versions were archived; Drive parent/filename readback succeeded. A consolidated release check and **seven regression tests** were reported passing. The Grade 6 fiction worksheet deliberately selected original question IDs **[1,3,4,5,6,7,8,9,10]**, excluding original Q2. The answer key was regenerated to match **nine**, not ten, fiction questions.

**Evidence boundary:** The PDF QA and regressions validate that release's recorded checks; they do **not** prove literary interpretation correct in every case, complete historical negative-test coverage or fully unattended future-week generation.

Relevant ELA source artifacts:

- [Canonical package snapshot](https://drive.google.com/file/d/1cM6VkbJLPtD119upIeuywCM7r1WDAHtv/view)
- [ELA governance](https://drive.google.com/file/d/1PaDTgjGV8483HQFDTsfgDncBFg20XLbZ/view)
- [Canonical RC config](https://drive.google.com/file/d/13jFjIIAkJOcowxym6khsIzsYpRzaepzf/view)
- [Student template](https://drive.google.com/file/d/1t2_tpiMtAjmWYyIQP1PO6Vwg0H91FRTn/view)
- [YPQA template](https://drive.google.com/file/d/1DIDd5T-sa8rNsWDKK0jnXXTaopewy0OR/view)
- [Release verifier](https://drive.google.com/file/d/1OyB4cDd2h3OB3BdEEEcxplpF6W_xLEdl/view)
- [Regression tests](https://drive.google.com/file/d/1rfYqwByVuZUTtjitEIGGA67RL2tA2TGo/view)
- [Learnings register](https://drive.google.com/file/d/1_X12CE4H7mQr8s9OrHvLEj_GZSjY2Xej/view)
- [ELA curriculum tracker](https://docs.google.com/spreadsheets/d/1LJIF0Ebb1WJtsYVOIC1zifm73wbq0L4eXytOclGUNGY/edit)

### 7.3 Recurring observations to preserve

| Historical ID | Failure / pressure | Generalizable architectural need |
|---|---|---|
| ELA-POETRY-001 | Poems too short for target depth | Source-length and complexity validation |
| ELA-FICTION-003 | Fiction too short | Grade-target minimum and exception |
| ELA-SERIES-004 | Wrong book/chapter progression | Persistent curriculum/source continuity |
| ELA-LAYOUT-005 | Fiction rendered as full-width instead of two-column | Render geometry inspection |
| ELA-LAYOUT-006 | Spurious third student page | Measured pagination gate |
| ELA-NAME-007 | Inconsistent PDF naming | Canonical naming contract |
| ELA-KEY-008 | Abbreviated YPQA explanation | Teacher-key semantics and coverage |
| ELA-QA-009 | Output generated without adequate inspection | Release artifact QA |
| ELA-KEY-LAYOUT-010 | Key exceeded two pages | Key-specific pagination gate |
| ELA-PUBLISH-011 | Published to wrong folder | Destination allowlist + remote readback |
| ELA-TYPOGRAPHY-012 | Question stems not bold / typography drift | Text span / visual QA |
| ELA-LAYOUT-013 | Valuable questions dropped despite whitespace | Actual-fit selection and backfill |
| ELA-STRUCTURE-014 | Missing passage/stanza locators | Structural labels and evidence locators |
| ELA-KEY-ALIGN-015 | Nine fiction questions vs ten key rationales | One canonical selected-question manifest |

Earlier observation narratives also described **large page whitespace** (pilot estimates approximately **47%, 45%, 39%** for Grades 1, 4 and 6), and content/choices missing despite superficially successful PDF generation. Treat historical percentages as **observation estimates requiring original report verification**, not current SLO baselines.

**Observation lesson:** A file existing, compiling or having two pages is *necessary but insufficient*. Verification must cover content, alignment, visual geometry, provenance, release placement and human educational judgment. Maintain defect → root cause → requirement/config/code update → negative regression test → release evidence → learning/requirement delta.

## 8. Architecture and process concepts proposed in this conversation

### 8.1 C4 and 3D architecture

Previous responses sketched:

- **C1:** Educator/curriculum owner, students, teachers/parents, sources, Google Drive and curriculum tracker around the MTS content system.
- **C2:** Orchestrator; curriculum/source manager; content/question engine; layout/rendering; quality/release gate; publication/tracker; observation/learning manager.
- **C3:** Mode resolver, source selector, passage normalizer, question/evidence authoring, canonical bank, coverage/prioritizer, measured-fit optimizer, synchronized student/teacher renderers, QA and publisher.
- **C4:** Canonical YAML, schemas, question-selector and release-verifier modules, test suite; proposed unified future pipeline and renderers.

**These diagrams were exploratory architecture sketches for the educational product**. They must be reconciled with the attached strategy's 3D architecture and M0–M8 station ownership; do not assume the exact box boundaries were approved.

### 8.2 Educational process

The working RC flow was:

`Weekly intent → load curriculum and source history → choose mode/source → prepare passage/question bank → verify content and provenance → measure real layout fit → select/backfill → render worksheet/key from same manifest → structural/semantic/visual QA → review → archive/publish → Drive readback → tracker update → observe/learn`.

Different modes matter:
- `generated_adapted_rc` uses approved templates and selected/revised questions.
- `ready_made_source` preserves original workbook page content and answers.
- `integrated_ela` is a broader multi-skill weekly instruction rotation; RC-specific constraints must not automatically govern writing and grammar.

### 8.3 Universal factory lifecycle (from the supplied strategy)

`M0 Explore/POC → M1 Intent & Domain → M2 Requirements & Quality → M3 Structured Product & Process → M4 3D Architecture & Trade-offs → M5 Detailed Design → M6 Vertical-Slice Build → M7 Continuous Verification → M8 Observe/Learn/Adapt → Requirement Delta back upstream`.

Stations are *logical capabilities/gates*, not fixed sequential departments. Each has a human-reviewable one-page brief, canonical primary artifact, atomic IDs, evidence and owner. Preserve the requirement-to-outcome trace graph. Automation is promoted based on evidence, not aspiration.

## 9. Proposed `mts-software-factory` repository layout (NOT approved)

The latest conversation reviewed a candidate target layout. Its **roles** matter more than these exact directories:

```text
mts-software-factory/
├── README.md                  # human entry
├── PRODUCT.md                 # product intent/anti-scope
├── constitution.md            # enduring principles
├── AGENTS.md                  # thin universal agent entry
├── CLAUDE.md                  # thin Claude adapter
├── .github/                   # Copilot adapter + CI
├── strategy/
│   ├── ai-sdlc-software-factory-strategy.md
│   ├── project-starting-instructions.md
│   ├── source-history/
│   │   └── mts-educational-factory-conversation.md
│   ├── migration-strategy.md
│   └── roadmap.md
├── docs/
│   ├── product/               # intent, ontology, exploration
│   ├── requirements/          # req/AC/quality scenarios
│   ├── process/               # M0–M8 station and phase contracts
│   ├── architecture/          # C1/C2/3D/ERD/ADRs
│   ├── design/                # C3/C4 and slice design
│   ├── implementation/
│   ├── verification/
│   ├── learning/              # observations/deltas
│   └── operations/
├── capabilities/              # education capability semantics/contracts
├── subjects/                  # Math / ELA / Physics domain specialization
├── src/                       # executable shared and subject/plugin code
├── specs/                     # feature/slice specs
├── contracts/                 # APIs/events/schemas
├── config/                    # governed variability
├── extensions/                # bounded customization, only if needed
├── workflows/
├── skills/
├── templates/
├── tests/
├── observability/
├── scripts/
└── infra/
```

**Anti-pattern to avoid:** `capabilities/`, `subjects/` and `src/` each implementing a separate version of worksheet generation. Use semantic ownership in the first two and code ownership in the third unless a better, reviewed package layout replaces it. No empty-folder forest or duplicate facts.

## 10. Migration questions and known gaps

1. **New repo vs rename:** The latest recommendation favors a new `mts-software-factory` repo, preserving `mts-crossmodel` as read-only/source until proven migration. Create only after explicit decision.
2. **Foundation ownership:** Is the factory a general-purpose software factory with MTS education as first product, or specifically an education software factory? Preserve this as an unresolved product boundary.
3. **Ontology:** Separate *Subject*, *Learning Domain*, *Universal Capability*, *Artifact/Product Type*, *Curriculum Objective*, *Assessment*, *Run*, *Evidence* and *Release* without artificial conflation.
4. **Current GitHub reality:** Inspect full Math modules and tests, real entry points, dependencies, data and schemas; assess which are production-ready.
5. **ELA integration:** Standardized ELA files were stored in Google Drive, not automatically incorporated into `mts-crossmodel` executable structure. They need validated migration with their provenance.
6. **Complete automation:** A successful November 2 release and some shared code do not mean new weeks can be generated autonomously. The reusable source acquisition, editorial quality, rendering, publication and tracker updates need end-to-end integration.
7. **QA completeness:** Individual regression tests exist; full coverage of all historical observations and editorial interpretation is not established.
8. **Security and rights:** Audit source-book copyright/license, personal/student data, API credentials, private files, large PDFs and repository visibility before making a new repository public.
9. **Human gates:** Define who approves product intent, curriculum, source adaptation, architecture exceptions and external publication.
10. **Traceability:** Persist atomic IDs and coverage ledger linking M0–M8 with implementation, negative tests, released outputs and observed outcomes.
11. **Source-of-truth precedence:** Distinguish Drive as authoritative source/release storage, GitHub as versioned engineering truth, and chat as historical/working context. Define sync and failure policies.
12. **Portability:** Confirm each AI model can locate needed context using standard repository files; don't assume a connector, command or model-specific agent is available in every environment.

## 11. Suggested next review sequence, without executing migration

1. Inventory the exact three sources and identify documentary/implementation gaps.
2. Review the factory product boundary and ontology before changing repo layout.
3. Produce the **Adopt / Refactor / Replace / Archive** matrix, with source paths and verification evidence.
4. Review target repository structure, artifact ownership, station contracts, interfaces and 3D/C1–C4 architecture; record ADRs.
5. Select one **bounded verifiable vertical slice** that exercises the real product path, ideally preserving already working Math behavior and incorporating one established ELA workflow.
6. Specify trace/evidence, tests, human approval and migration rollback.
7. Create the new repo only upon approved migration plan; promote confirmed assets incrementally, keeping historical source intact.

## 12. Source references and fallback navigation

### Primary strategy and engineering sources

- [AI-SDLC strategy source attachment](https://github.com/kpkchaitanya/mts-crossmodel) — the **original strategy was attached in the predecessor ChatGPT conversation**; this repository link is only the current engineering source, **not a claim that the strategy file was committed here**. Upload the strategy to the new project and, following approval, version it under `strategy/`.
- [Existing engineering repo](https://github.com/kpkchaitanya/mts-crossmodel)
- [Version-controlled project starting instructions](https://github.com/kpkchaitanya/mts-crossmodel/blob/master/strategy/project-starting-instructions.md)

### Historical product evidence

- [ELA canonical snapshot](https://drive.google.com/file/d/1cM6VkbJLPtD119upIeuywCM7r1WDAHtv/view)
- [ELA governance](https://drive.google.com/file/d/1PaDTgjGV8483HQFDTsfgDncBFg20XLbZ/view)
- [ELA learning register](https://drive.google.com/file/d/1_X12CE4H7mQr8s9OrHvLEj_GZSjY2Xej/view)
- [ELA curriculum tracker](https://docs.google.com/spreadsheets/d/1LJIF0Ebb1WJtsYVOIC1zifm73wbq0L4eXytOclGUNGY/edit)
- [November 2 published PDF folder](https://drive.google.com/drive/folders/1OncoWGkuBzmDDMURq6P9WsJ_ycnRmlXS)

### Original conversation reference

The original MTS ELA/Software Factory architecture conversation is **not embedded** and no share URL was supplied. Keep it in the original ChatGPT project where possible. Add an authorized share/reference URL here if one is created. A chat link does not guarantee that arbitrary model harnesses can retrieve the chat's full content. This curated file provides portable essential context in the meantime.

## 13. Future edits and provenance

This document is historical context. When new decisions are approved, **put them in the authoritative product, requirements, ADR, design or implementation file**, and add links here if they clarify lineage. Do not update this fallback to masquerade as the latest spec.

When adding a historical correction, record its source, timestamp and whether it is a correction to the historical record or a newly approved decision. Favor traceable, append-only observations over retroactive rewriting of rationale.
