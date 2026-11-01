# MTS Software Factory — Project Starting Instructions

> **Status:** Draft onboarding/handoff for a new ChatGPT Project; not the permanent project constitution, approved architecture, or implementation authorization.
>
> **Current source home:** `kpkchaitanya/mts-crossmodel` (temporary). **Proposed destination:** `kpkchaitanya/mts-software-factory` (new repository, not yet created).
>
> **Purpose:** Restore enough context to make the next decisions rigorously, without locking the future factory into a short-term migration plan or a particular AI model.

## 1. Start from the problem, not a predetermined implementation

We seek a reusable, governed, observable **MTS Software Factory** that develops and continually improves educational products and may eventually serve further product domains. Educational capabilities are the first concrete product family, **not** a hard-coded limit on the factory's applicability.

The existing MTS scope includes **Math, ELA (reading, writing, vocabulary and grammar)** and potential additional subjects such as Physics and Science. Across subjects, the intended educational capabilities include **Curriculum, Lesson Plans, Worksheets/Practice, Diagnostics, Cheatsheets/Study Guides, Mock Testing, and Performance Analysis**. Their exact interfaces, boundaries and maturity must be discovered and validated rather than assumed.

A successful result preserves human intent and instructional quality, makes software and content reproducible and reviewable, and carries evidence and feedback back into evolving specifications.

## 2. Three starting sources and their distinct authority

1. **AI-SDLC Software Factory Strategy** (`AI-SDLC-SOFTWARE-FACTORY-STRATEGY.md`, attached in the originating conversation): architectural *methodology*. It describes the M0–M8 lifecycle, four systems (product, production, engineering, learning), 3D architecture, artifact contracts and atomic IDs, traceability, human review, controlled automation, and iterative constraint resolution. Read the original in full; don't rely solely on this synopsis.
2. **Existing engineering implementation:** [`kpkchaitanya/mts-crossmodel`](https://github.com/kpkchaitanya/mts-crossmodel). Inventory rather than assume. Useful assets include `constitution.md`, `AGENTS.md`, `CLAUDE.md`, Copilot instructions, Math code, structured worksheet specs, manifests, schemas, tests, configurations, commands and workflows. Distinguish working code from aspirations, snapshots, and unverified designs.
3. **MTS Educational Factory experience:** the preceding MTS ELA/Math project and verified reading-comprehension releases. Preserve subject and capability requirements, curriculum progression, visual templates, question/answer synchronization, YPQA teaching method, publication checks, QA defects and observation-derived regression lessons. Refer to the canonical MTS ELA Drive folder and its release artifacts; verify before reusing or claiming completion.

**Precedence by responsibility:** Strategy governs the engineering method, MTS domain artifacts govern educational behavior, and validated implementations supply reusable code. When facts conflict, record the conflict, alternatives, ownership and decision; never silently overwrite source truth.

## 3. Working method: use the factory strategy to build the factory

- Start with **intent, ontology, outcomes and scope**, including explicit anti-scope.
- Apply the **M0–M8 station model** proportionately; these are logical capabilities and gates, not necessarily nine serial teams.
- Maintain **C1–C4** views within the strategy's **3D architecture**: functionality/process, applications/interfaces/technology, information/entities; overlay quality attributes and human/agent responsibility.
- Prefer **bounded vertical slices** and real executable evidence to a fully scaffolded folder forest.
- Track `Intent → Requirement → Architecture/ADR → Slice → Code/Config → Test/Eval → Build/Release → Runtime Outcome → Observation → Learning → Requirement Delta`.
- Every material observation should have an owner, reproducible symptom, root cause, governing fix, regression test and outcome. The **Requirement Coverage Ledger** distinguishes implemented, verified, released, observed and accepted.
- Human authority remains explicit at intent, risk, architecture exception and release decisions.
- Keep substantive truth in **one authoritative artifact**; generate one-page review lenses linked to atomic entities and evidence. Avoid duplicated instructions across model providers.
- Support ChatGPT, Codex, GitHub Copilot, Claude and future tools through **thin adapters**, with all governing behavior in portable Markdown, schemas, configuration, executable code and tests.
- Do not mistake a manually successful ELA release for an automated reusable factory; mark actual maturity and gaps accurately.

## 4. Candidate target repository layout — review before adoption

The following is a **logical design proposal**, not an approved directory creation task:

```text
mts-software-factory/
├── README.md
├── PRODUCT.md
├── constitution.md
├── AGENTS.md
├── CLAUDE.md
├── strategy/
│   ├── ai-sdlc-software-factory-strategy.md
│   ├── project-starting-instructions.md
│   ├── migration-strategy.md
│   └── roadmap.md
├── docs/
│   ├── product/             # M0/M1: exploration, intent, ontology, outcomes
│   ├── requirements/        # M2: requirements, criteria, quality scenarios
│   ├── process/             # M3: phases, rules, responsibility/automation modes
│   ├── architecture/        # M4: C1/C2, 3D analysis, ERD, interfaces, ADRs
│   ├── design/              # M5: slices, contracts, C3/C4
│   ├── implementation/      # M6: implementation records, build provenance
│   ├── verification/        # M7: coverage and evidence
│   ├── learning/            # M8: observations, deltas, constraints
│   └── operations/
├── capabilities/            # Shared educational capability semantics/contracts
│   ├── curriculum/
│   ├── lesson-plans/
│   ├── worksheets/
│   ├── diagnostics/
│   ├── cheatsheets/
│   ├── mock-testing/
│   └── performance-analysis/
├── subjects/                # Subject specialization/ontology/config (not duplicate engines)
│   ├── math/
│   ├── ela/
│   │   ├── reading/
│   │   ├── vocabulary/
│   │   ├── writing/
│   │   └── grammar/
│   └── physics/             # Candidate; materialize when required
├── src/                     # Shared executable implementations + subject plugins
├── specs/                   # Governed slice/feature specs
├── contracts/               # Schemas, API/event/file contracts
├── config/                  # Validated variability
├── extensions/              # Deliberately bounded extension points, as needed
├── workflows/               # Restartable, gate-aware factory workflows
├── skills/                  # Specialized, versioned reasoning and methods
├── templates/               # Versioned station and educational product templates
├── tests/                   # Unit, integration, contract, E2E and AI evals
├── observability/           # Trace/coverage schemas and telemetry contracts
├── scripts/
├── infra/
└── .github/                 # CI, CODEOWNERS and thin Copilot adapter
```

**Structural decision to validate:** `docs/` owns the M-station artifact lifecycle; `capabilities/` and `subjects/` own educational semantics and customization; `src/` owns executable realization. Avoid `capabilities/` and `subjects/` becoming competing implementations or copies of requirements. Don't create empty directories without demonstrable need.

## 5. Initial conversation agenda (not a permanent backlog)

1. **Three-source inventory and rationalization:** compare strategy, GitHub, and educational project; identify overlaps, contradictions, evidence, reusable code and missing requirements. Produce an **Adopt / Refactor / Replace / Archive** matrix with source URI, target location, reason, risk and verification.
2. **Product and factory identity:** clarify whether the factory is a platform serving the educational product family or a narrowly educational factory, including intended future expansion. Establish `PRODUCT.md` boundaries and ontology.
3. **Review target folders and artifact ownership:** validate M0–M8 mappings, subject × capability × artifact dimensions, atomic entity IDs, and 3D/C1–C4 views. Record ADRs for nontrivial choices.
4. **Specify the first verifiable vertical slice**, likely migrating one proven MTS educational workflow while retaining existing working Math functionality. Define tests, human approvals and rollback before migration.
5. **Plan the new GitHub repository and migration** only after the review; do not create, rename, delete, bulk-copy or archive the source repo by implication.
6. **Establish continuous learning:** turn historical ELA/Math defects into linked observations, tests and requirement deltas.

Favor concise executive one-page summaries linked to full details. Separate **existing**, **proposed**, **verified** and **approved** decisions.

## 6. Project onboarding and instruction scope

For a new ChatGPT Project, use short project instructions such as:

> The governing starting context for this initiative is `strategy/project-starting-instructions.md` in `kpkchaitanya/mts-crossmodel` (temporary source repository). Read it together with the attached `AI-SDLC-SOFTWARE-FACTORY-STRATEGY.md` and the current repository artifacts. These are starting inputs for joint design, not immutable product decisions. Work toward a reviewed, model-agnostic `mts-software-factory`; record decisions in authoritative versioned files. Do not modify repositories without an explicit implementation request.

**Connection caveat:** A GitHub URL in Project instructions is a pointer, not guaranteed automatic ingestion. Attach the Markdown to the Project, or connect GitHub/enable appropriate repository access, and read the latest version at the beginning of a new design session.

## 7. Explicit non-decisions

- The target repository has **not** been created by this document.
- The exact folder structure is **not approved** merely because it appears here.
- No existing Math or ELA implementation is deprecated, migrated or deleted.
- A model adapter does not own requirements or override the canonical strategy.
- The initial educational use cases do not prevent future non-educational applications of the factory.
