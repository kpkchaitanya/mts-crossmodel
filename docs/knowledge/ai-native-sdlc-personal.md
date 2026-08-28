# AI-Native SDLC --- Personal

**Edition:** Personal **Engineering Methodology & Reference**\
**Canonical source for the AI SDLC Learnings Summary Diagram (ASLSD)**

-   **Version:** 2.2
-   **Status:** Evolving
-   **Last Updated:** 2026-08-27
-   **Authority:** This Markdown document is the semantic source of
    truth. ASLSD is its concise visual projection.
-   **Core Philosophy:** Reviewability Through Brevity & Visualization

**Personal Edition Rule:** Retain the separately maintained
Feynman-inspired comprehension layer and its corresponding ASLSD visual
elements. - **Guiding Goal:** Human-reviewable + AI-executable software
development.

## 1. Purpose

AI-Native SDLC is an opinionated, continuously improving
software-development methodology that combines proven SDLC practices
with AI-native development.

It exists to make software development:

-   concise and reviewable,
-   structured and traceable,
-   deterministic wherever practical,
-   configurable instead of repeatedly reasoned,
-   explicit about where human judgment, AI reasoning, and software
    logic belong,
-   continuously verified and improved.

## 2. Core Principles

### 2.1 Reviewability Through Brevity & Visualization

> What humans and AI cannot review and comprehend together, they cannot
> reliably verify or trust.

Brevity and visualization are **engineering controls**, not presentation
polish. Important artifacts SHOULD use the smallest useful level of
detail that preserves meaning and SHOULD use visualization when
relationships, flow, hierarchy, state, boundaries, comparison, or
traceability are easier to understand visually.

Artifacts SHOULD be concise, structured, visual where useful, traceable,
comprehensible, layered from summary to detail, and continuously
aligned.

**Preferred review pattern:**

`VISUAL / ONE-PAGE SUMMARY → CONCISE STRUCTURED SOURCE → DETAIL ON DEMAND`

The concise structured source remains authoritative unless another
source is explicitly designated. Visuals are review surfaces and SHOULD
be reconstructable from, or traceable to, authoritative structured
content.

### 2.2 Put Intelligence Only Where Intelligence Adds Value

Prefer the least complex mechanism that can reliably perform a
responsibility.

**Default implementation preference:**

`CODE → CONFIG → RETRIEVAL / KNOWLEDGE → AI REASONING`

-   Deterministic behavior SHOULD be implemented as code.
-   Variable behavior SHOULD be externalized as configuration.
-   Stable facts and reference material SHOULD be retrieved from
    knowledge.
-   AI reasoning SHOULD be used where interpretation, synthesis,
    ambiguity, or generation adds material value.

### 2.3 Preserve Human Intent

Human intent MUST remain authoritative, provenance-preserved, versioned,
reviewable, reconstructable, and auditable throughout the lifecycle.

### 2.4 Separate Concerns Before Implementing

The system SHOULD distinguish:

-   intent from implementation,
-   logic from data,
-   stable knowledge from variable configuration,
-   orchestration from reasoning,
-   deterministic computation from probabilistic AI behavior.

### 2.5 Prefer Minimum Technology Diversity

Use the smallest technology set that satisfies the requirements.

New languages, frameworks, databases, or infrastructure technologies
SHOULD be introduced only when they provide a material advantage or the
preferred stack cannot satisfy a mandatory requirement.

## 3. USSV --- Universal Problem Solving

The lifecycle follows the general problem-solving model:

  USSV Stage       SDLC Meaning                      Primary Modules
  ---------------- --------------------------------- -----------------
  **Understand**   Understand what and why           M1--M2
  **Strategize**   Make the right choices and plan   M3
  **Solve**        Design and build                  M4--M5
  **Verify**       Prove, observe, learn, improve    M6--M8

USSV is recursive: each significant problem inside a module MAY itself
be solved using Understand → Strategize → Solve → Verify.

## 4. Lifecycle Summary

  ----------------------------------------------------------------------
  Module                Name                  Primary Outcome
  --------------------- --------------------- --------------------------
  M0                    POC / Vibe Coding     Rapid learning and
                                              feasibility evidence

  M1                    Human Intent & Domain Shared intent, vocabulary,
                        Ontology Preservation concepts, relationships

  M2                    Requirements &        Functional requirements,
                        Constraints           NFRs, scenarios,
                                              acceptance criteria

  M3                    Architecture          Strategy, choices,
                                              boundaries, trade-offs and
                                              ADRs

  M4                    Detailed System       Implementable
                        Design                component/data/interface
                                              design

  M5                    Iterative Modular     Working bounded components
                        Implementation &      integrated continuously
                        Integration           

  M6                    Continuously Verified Tests, AI evals,
                        Development           regression protection,
                                              quality gates

  M7                    Operate, Observe &    Runtime evidence, metrics,
                        Evolve                feedback and learning

  M8                    Govern, Learn &       Governance, knowledge
                        Optimize              capture and continuous
                                              improvement
  ----------------------------------------------------------------------

## 5. M0 --- POC / Vibe Coding

**Purpose:** Learn quickly before committing to architecture or
production implementation.

Typical activities:

-   rapid exploration,
-   feasibility validation,
-   disposable prototypes,
-   technology experiments,
-   unknown/risk reduction.

POC code MUST NOT automatically become production code. Useful learnings
SHOULD flow into requirements, architecture, knowledge, or ADRs.

## 6. M1 --- Human Intent & Domain Ontology Preservation

**Purpose:** Preserve what humans mean before implementation choices
distort it.

Capture:

-   intent and purpose,
-   functional areas,
-   domain vocabulary,
-   core concepts/entities,
-   relationships,
-   initial ontology.

The ontology establishes shared meaning. It MAY later be refined into
architectural information models and ERDs.

## 7. M2 --- Requirements & Constraints

Capture:

-   functional requirements,
-   constraints,
-   scenarios/use cases,
-   acceptance criteria,
-   non-functional requirements / quality attributes.

Requirements SHOULD state the need rather than prematurely prescribe
implementation technology unless a genuine technology constraint exists.

Examples:

-   Prefer: "Configuration must be human-reviewable and
    version-controlled."
-   Avoid as an NFR: "Configuration must use YAML."
-   Valid constraint when real: "The solution must deploy into the
    existing Azure environment."

## 8. M3 --- Architecture

**Purpose:** Strategize and choose before detailed design.

Architecture determines the consequential structural choices,
boundaries, patterns, trade-offs, technologies, and responsibility
allocations.

M3 contains five complementary architectural views.

### 8.1 Functional Architecture --- What Does It Do?

Defines the structural organization of system behavior.

Typical contents:

-   functional areas,
-   capabilities,
-   components/applications,
-   interactions,
-   system boundaries,
-   high-level C1/C2 views.

### 8.2 Informational Architecture --- What Does It Know?

Defines the important information concepts and relationships the
solution manages.

Typical contents:

-   domain ontology refinement,
-   core entities,
-   relationships,
-   information/data flows,
-   high-level ERD.

**Ontology and ERD are related but not identical:**

-   Ontology defines concepts, meaning, vocabulary and semantic
    relationships.
-   High-level ERD identifies the important data entities and structural
    relationships represented by the solution.

### 8.3 Non-Functional Architecture --- How Well Must It Work?

Translates critical NFRs and quality attributes into architectural
strategies, rules and measurable evidence.

Typical concerns:

-   determinism,
-   performance,
-   security,
-   reliability,
-   scalability,
-   availability,
-   maintainability,
-   portability,
-   observability,
-   cost efficiency,
-   AI/token efficiency,
-   human reviewability.

#### Fitness Functions

Critical non-functional characteristics SHOULD have measurable or
executable fitness functions where practical.

Relationship:

`NFR → Non-Functional Architecture → Fitness Function → Evidence`

Example:

-   NFR: generated answers must be reproducibly correct.
-   Architecture: deterministic calculations must not depend on LLM
    reasoning.
-   Fitness functions: same input produces the same calculated answer;
    all answers pass independent verification.

### 8.4 Technology Architecture --- What Should We Build It With?

Technology selection MUST follow requirements and architectural needs
rather than lead them.

For architecturally significant capabilities:

1.  Understand the functional responsibility.
2.  Identify relevant NFRs and constraints.
3.  Independently identify credible technology alternatives.
4.  Compare alternatives using explicit criteria.
5.  Apply preferred-stack alignment as one criterion---not as an
    automatic winner.
6.  Select the simplest technology that satisfies the need.
7.  Prefer the established stack when alternatives offer no material
    advantage.
8.  Record architecturally significant decisions and deviations in ADRs.

Typical evaluation criteria:

-   functional fit,
-   simplicity,
-   preferred-stack alignment,
-   maintainability,
-   determinism/testability,
-   maturity/ecosystem,
-   AI/tooling support,
-   performance,
-   portability,
-   security,
-   cost.

#### Preferred Technology Direction

Defaults SHOULD be maintained separately in machine-readable
configuration, for example `technology-stack.yaml`.

Current general preferences include:

-   Python for general deterministic programming,
-   YAML for human-edited configuration,
-   JSON for machine interchange/contracts,
-   Markdown for knowledge/documentation,
-   pytest for Python testing,
-   Playwright for browser automation,
-   SQLite for simple local structured persistence and PostgreSQL when
    server/multi-user relational needs justify it.

These are preferences, not unconditional mandates.

### 8.5 Responsibility Architecture --- Who Does What, Where?

Responsibility Architecture allocates behavior across actors and
implementation mechanisms.

#### Actor

Three primary actor classes:

  ---------------------------------------------------------------------
  Actor                              Best suited for
  ---------------------------------- ----------------------------------
  **Human**                          Intent, accountability, approval,
                                     judgment, exceptions

  **AI**                             Interpretation, synthesis,
                                     generation, ambiguity, reasoning

  **Software**                       Deterministic logic, computation,
                                     validation, repeatable execution
  ---------------------------------------------------------------------

Actor taxonomy MAY later expand into roles such as domain expert,
architect, developer, reviewer, architect agent, coding agent, testing
agent, service, validator, and rules engine.

#### Implementation Placement

  ---------------------------------------------------------------------
  Mechanism                          Responsibility
  ---------------------------------- ----------------------------------
  **Knowledge**                      Facts, references, curriculum,
                                     ontology, examples, stable context

  **Config**                         Variables, rules, parameters and
                                     changeable behavior

  **Command**                        Thin user/agent entry points,
                                     invocation and parameters

  **Workflow**                       Process sequencing, orchestration,
                                     steps and flow

  **Skill**                          AI reasoning tasks, prompts,
                                     input/output contracts and tool
                                     use

  **Code**                           Deterministic logic, algorithms,
                                     services and libraries
  ---------------------------------------------------------------------

Responsibility allocation SHOULD answer three questions:

1.  **WHO** performs the responsibility? --- Human, AI, or Software.
2.  **WHAT** is the responsibility? --- Decide, reason, configure,
    orchestrate, calculate, validate, approve, etc.
3.  **WHERE/HOW** should it live? --- Knowledge, Config, Command,
    Workflow, Skill, or Code.

### 8.6 Cross-Cutting Architecture Decisions

Across all five views, architecture MUST make important decisions
explicit:

-   boundaries,
-   patterns,
-   trade-offs,
-   dependencies,
-   technology choices,
-   responsibility allocation,
-   architecturally significant constraints.

Architecturally significant decisions SHOULD be captured as ADRs.

## 9. M4 --- Detailed System Design

**Purpose:** Turn architectural choices into implementable design.

Typical contents:

-   C3/C4 component views,
-   detailed ERD,
-   APIs,
-   contracts,
-   schemas,
-   workflows,
-   states/state machines,
-   algorithms,
-   pseudocode.

Architecture chooses the strategy; detailed design solves within those
choices.

## 10. M5 --- Iterative Modular Implementation & Integration

Implementation SHOULD favor:

-   bounded components,
-   deterministic code and externalized configuration,
-   contract-based integration,
-   continuous integration,
-   small reviewable increments.

Generated implementation MUST remain traceable to design, architecture,
requirements, and human intent.

## 11. M6 --- Continuously Verified Development

Verification is continuous rather than a final phase.

Typical mechanisms:

-   unit tests,
-   integration tests,
-   Playwright/browser tests,
-   regression tests,
-   AI evaluations,
-   traces,
-   architecture fitness functions,
-   quality gates.

AI-generated output MUST NOT be considered correct merely because it was
generated successfully.

## 12. M7 --- Operate, Observe & Evolve

Production/runtime evidence feeds learning back into the lifecycle.

Capture:

-   monitoring,
-   metrics,
-   observability,
-   feedback,
-   runtime behavior,
-   incidents,
-   learning,
-   evolution/improvement opportunities.

## 13. M8 --- Govern, Learn & Optimize

Use accumulated evidence to improve both the product and the development
methodology.

Typical concerns:

-   governance,
-   compliance,
-   knowledge capture,
-   architecture evolution,
-   methodology refinement,
-   cost/token optimization,
-   continuous improvement.

## 14. AI-Native Artifact Model

Artifacts SHOULD have clear responsibilities and MUST reflect
**Reviewability Through Brevity & Visualization**.

### 14.1 Artifact Reviewability Standard

For architecturally or operationally significant artifacts, prefer three
layers:

1.  **Visual / One-Page View** --- rapid orientation and a shared mental
    model.
2.  **Concise Structured Source** --- authoritative Markdown, YAML,
    JSON, schema, ADR, code, or configuration.
3.  **Detail on Demand** --- specifications, traces, examples,
    implementation detail, and evidence.

Do not create diagrams merely for decoration. Visualize when an artifact
contains relationships, hierarchy, flow, states, boundaries,
comparisons, lifecycle, responsibility allocation, or traceability.

AI-generated visuals MUST remain semantically aligned with their
authoritative structured source. When a visual cannot be
deterministically regenerated, the structured source MUST contain enough
information to reconstruct and verify it.

Artifacts SHOULD have clear responsibilities.

  -----------------------------------------------------------------------
  Artifact                Preferred Location      Purpose
  ----------------------- ----------------------- -----------------------
  Knowledge               `knowledge/`, `*.md`,   Facts, references,
                          `*.yaml`                curriculum, ontologies,
                                                  examples

  Config                  `config/`, `*.yaml`,    Variables, rules,
                          `*.json`                parameters

  Command                 `commands/`, `*.md`     Thin entry points,
                                                  usage, parameters

  Workflow                `workflows/`, `*.yaml`, Orchestration, sequence
                          `*.md`                  and flow

  Skill                   `skills/*/SKILL.md`     AI reasoning tasks,
                                                  prompts, I/O schema,
                                                  tool guidance

  Code                    `src/`, `**/*.py`       Deterministic logic,
                                                  services and libraries

  Tests & Evals           `tests/`, `evals/`      Unit/integration tests,
                                                  AI evals, traces

  Templates & Output      `templates/`, `output/` Documents, PDFs, assets
                                                  and deliverables
  -----------------------------------------------------------------------

### 14.2 Visualization & Feynman Review

Before accepting a significant artifact, ask:

-   Can its purpose and essential model be explained simply?
-   Can reviewers see the important relationships quickly?
-   Would a diagram, flow, hierarchy, matrix, state model, ERD, or
    one-page summary improve comprehension?
-   Are concrete examples available where abstraction is insufficient?
-   Does the representation expose rather than hide uncertainty and
    gaps?
-   Can humans and AI trace the summary back to authoritative detail?

Every visual SHOULD answer a specific review question and SHOULD avoid
unnecessary decorative complexity.

### 14.3 Placement Rule

Before putting behavior into an AI prompt or skill, ask:

1.  Can it be deterministic code?
2.  Can variability be configuration?
3.  Is it stable knowledge that should be retrieved?
4.  Does it genuinely require AI reasoning?

This rule SHOULD reduce token use, variability and maintenance cost.

## 15. Human Intent Preservation & Governance

Important artifacts SHOULD be:

-   authoritative,
-   provenance-preserved,
-   versioned,
-   human-approved where consequential,
-   reconstructable,
-   audit-ready.

AI SHOULD transform and implement intent without silently replacing
authoritative human intent.

## 16. Traceability & Production Assurance

The lifecycle SHOULD preserve end-to-end lineage:

`Intent → Requirements → Architecture → Design → Implementation → Verification → Runtime Evidence → Learning`

Cross-cutting production concerns include:

-   CI/CD,
-   security,
-   reliability,
-   observability,
-   governance,
-   cost/token efficiency.

## 17. AI Execution Guidelines

AI agents operating under this methodology MUST:

1.  Preserve authoritative human intent.
2.  Read applicable requirements and architecture before detailed design
    or implementation.
3.  Separate deterministic logic from AI reasoning.
4.  Prefer code/config/knowledge over repeated AI reasoning when
    appropriate.
5.  Avoid introducing new technologies without evaluating the existing
    preferred stack.
6.  Evaluate alternatives independently for architecturally significant
    technology choices.
7.  Record significant trade-offs and decisions using ADRs.
8.  Define or preserve fitness functions for critical NFRs.
9.  Keep artifacts concise, structured and traceable.
10. Reuse authoritative knowledge rather than regenerate stable facts.
11. Externalize changeable rules and parameters into configuration where
    practical.
12. Keep commands thin and workflows explicit.
13. Use skills for genuine AI reasoning responsibilities, not
    deterministic computation.
14. Continuously verify generated artifacts and implementation.
15. Feed operational evidence and learnings back into the methodology.

## 18. Relationship to Other Repository Documents

`ai-native-sdlc.md` defines the overarching development methodology.

Other documents SHOULD specialize it rather than duplicate it:

-   `constitution.md` --- governing invariants and non-negotiable
    principles.
-   `AGENTS.md` --- harness/agent operating instructions and
    repository-specific guidance.
-   `architecture.md` --- project-specific architectural choices.
-   `design.md` --- project-specific detailed design.
-   `technology-stack.yaml` --- preferred/default technology choices and
    evaluation policy.
-   `skills/` --- reusable AI reasoning capabilities.
-   `workflows/` --- repeatable orchestration.
-   `config/` --- variable behavior.
-   `src/` --- deterministic implementation.
-   `tests/` and `evals/` --- verification and evidence.

If duplication is necessary for execution, the authoritative source MUST
be clearly identified.

## 19. ASLSD Relationship

**ASLSD --- AI SDLC Learnings Summary Diagram** is the one-page visual
summary of this methodology.

-   `ai-native-sdlc.md` is authoritative.
-   ASLSD is optimized for rapid human comprehension and is the primary
    one-page visualization of the methodology.
-   Material changes to the methodology SHOULD trigger review/update of
    ASLSD.
-   If ASLSD and this document conflict, this document wins.

## 20. Evolution and Change Policy

This methodology is intentionally evolutionary.

Changes SHOULD be driven by:

-   research,
-   implementation experience,
-   experiments,
-   failures,
-   production evidence,
-   AI capability changes,
-   developer/user feedback,
-   measurable improvements in quality, speed, cost, reviewability or
    reliability.

Significant methodology changes SHOULD be versioned and summarized
below.

## Appendix A --- Feynman-Inspired Comprehension Model

> **Personal-edition inspiration layer.** This section is intentionally
> isolated from the core AI-Native SDLC so it can be reviewed, evolved,
> or removed without changing the underlying professional methodology.

### 2.2 Feynman-Inspired Comprehension

The methodology is inspired by Richard Feynman's emphasis on deep
understanding through **simple explanation, first-principles reasoning,
concrete models/examples, and exposing gaps in understanding**.

For consequential concepts and artifacts:

1.  Explain the idea in plain language.
2.  Reduce it to essential concepts and relationships.
3.  Visualize the model when a diagram communicates structure better
    than prose.
4.  Test understanding with concrete examples.
5.  Identify ambiguity, assumptions, and gaps exposed by the
    explanation.
6.  Return to facts or first principles and refine.
7.  Preserve necessary complexity while removing accidental complexity.

**Feynman check:** If a knowledgeable reviewer cannot explain the
artifact's essential model simply after reviewing it, simplify,
restructure, visualize, or decompose it before adding more detail.

### Personal ASLSD Representation

The **ASLSD --- Personal** visual SHOULD retain:

-   a Richard Feynman photo inset,
-   the Feynman quotation/reference used in the personal visual,
-   the Feynman-inspired comprehension flow,
-   the connection between simple explanation, first principles,
    visualization, examples, gap discovery, and refinement.

The Feynman-inspired material is an explanatory mental model layered on
top of the core methodology; it is not required for the Professional
edition.

## 21. Change History

### 2.2 --- 2026-08-27

-   Revised the core philosophy to **Reviewability Through Brevity &
    Visualization**.
-   Established visualization as an engineering/review mechanism rather
    than presentation decoration.
-   Added **Visual Summary → Concise Structured Source → Detail on
    Demand** as the preferred artifact pattern.
-   Added Feynman-inspired comprehension checks: simple explanation,
    first-principles reasoning, examples, visualization where useful,
    and gap discovery.
-   Strengthened artifact and AI execution guidance to apply this
    philosophy.

### 2.1 --- 2026-08-27

-   Established five architecture views:
    -   Functional Architecture,
    -   Informational Architecture,
    -   Non-Functional Architecture,
    -   Technology Architecture,
    -   Responsibility Architecture.
-   Positioned fitness functions within Non-Functional Architecture.
-   Added independent technology evaluation followed by preferred-stack
    alignment.
-   Added Human / AI / Software responsibility allocation.
-   Folded Knowledge / Config / Command / Workflow / Skill / Code
    placement into Responsibility Architecture.
-   Clarified M3 Architecture → M4 Detailed Design → M5 Implementation
    lifecycle.
-   Established this Markdown file as the semantic source of truth and
    ASLSD as its visual summary.

------------------------------------------------------------------------

## Compact Mental Model

**UNDERSTAND** - Preserve intent. - Establish vocabulary/ontology. -
Define functional requirements, NFRs and constraints.

**STRATEGIZE** - Functional Architecture --- what does it do? -
Informational Architecture --- what does it know? - Non-Functional
Architecture --- how well must it work? - Technology Architecture ---
what should we build it with? - Responsibility Architecture --- who does
what, where?

**SOLVE** - Detailed design. - Modular implementation and integration.

**VERIFY** - Continuously test and evaluate. - Operate and observe. -
Govern, learn and optimize.

> **Preserve intent. Make it brief enough to review and visual enough to
> understand. Choose deliberately. Implement deterministically where
> possible. Use AI where reasoning adds value. Verify continuously.
> Learn and evolve.**
