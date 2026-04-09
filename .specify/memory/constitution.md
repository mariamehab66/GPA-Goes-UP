<!-- Sync Impact Report
Version change: N/A (unfilled template) → 1.0.0 (initial ratification)
Modified principles: N/A — first fill; no prior principles to rename
Added sections:
  - Core Principles (I. Academic Rules Supremacy, II. Rule Engine Before ML,
    III. Data Integrity & Accuracy, IV. Transparent AI Assistance,
    V. Realistic Behavioral Modeling)
  - Data & ML Standards
  - Development Workflow
  - Governance
Removed sections: N/A
Templates checked:
  ✅ .specify/templates/plan-template.md — Constitution Check gate section present;
     aligns with Principles I–III enforcement requirement.
  ✅ .specify/templates/spec-template.md — Functional Requirements section
     compatible with rule-accuracy principle; no conflicting mandatory sections.
  ✅ .specify/templates/tasks-template.md — Phase structure (Foundational before
     User Stories) supports rule-engine-first ordering per Principle II.
Deferred TODOs: None — all placeholders resolved.
-->

# GPA Goes UP Constitution

## Core Principles

### I. Academic Rules Supremacy (NON-NEGOTIABLE)

University academic regulations are STRICT, non-overridable constraints.
Every system component MUST enforce these rules before any optimization occurs.
Machine Learning MUST NOT violate any academic rule; it ONLY selects the best
option among those already validated as rule-compliant.

Non-negotiable rules include: prerequisite chains, credit hour limits
(regular: 12–21 hrs depending on GPA/status; summer: max 6 hrs; probation: max 12 hrs),
GPA thresholds (graduation CGPA ≥ 2.0; pass score ≥ 60%), retake eligibility
(grades F/Abs/W/I only; ≤ 12 credit hours retake cap with grade capped at D after limit),
semester cross-registration restrictions, and graduation requirements
(140 credit hours total).

### II. Rule Engine Before ML

The system MUST apply the rule engine first to produce a valid candidate course set,
then pass that set to ML for scoring and ranking.
ML scoring MUST NOT receive or rank invalid course options.
This two-stage pipeline (rule validation → ML optimization) MUST be enforced
architecturally — no shortcut that routes student data directly to ML output
without rule-engine filtering.

### III. Data Integrity & Accuracy

All GPA values MUST be calculated from actual grades using the official formula:
`GPA = Σ(Quality Points) / Σ(Credits)`. GPA MUST NOT be randomly assigned.
Grade mapping MUST follow the official scale (A=4.00 … D=2.00 … F=0.00;
P excluded from GPA calculation entirely).
Relational integrity MUST be maintained: no enrollment without a valid student record,
no enrollment without a valid course record, no enrollment violating the prerequisite
chain. Arabic transcript symbols (e.g., غ → Abs) MUST be correctly normalized
before any downstream processing or storage.

### IV. Transparent AI Assistance

The AI chatbot MUST explain its recommendations, not merely state them.
Every recommendation output MUST include a score and a rationale covering:
why the course is suggested, its expected GPA impact, and any relevant rule context.
The chatbot MUST function as a full academic advisor — capable of answering questions
about academic rules, the GPA system, registration eligibility, and graduation
requirements — not only as a wrapper for ML result display.

### V. Realistic Behavioral Modeling

Synthetic training data MUST simulate realistic student behavior, including
non-optimal course choices, random decisions, and imperfect scheduling.
Training data MUST represent all performance tiers: high achievers (CGPA ~3.3+),
average students (~2.5–3.3), and struggling students (~1.9–2.4).
Generated CGPA values MUST follow natural variation (±0.4 from the reference
distribution) and MUST NOT be uniformly distributed or artificially linear.
This principle exists to prevent ML overfitting on idealized, always-optimal data.

## Data & ML Standards

The ML component operates strictly as an optimizer within rule-validated candidate sets.

- Course scoring MUST incorporate: student academic history, course difficulty
  (learned from historical grades and failure rates — NEVER manually hardcoded),
  similar-student patterns, and the full feature set defined in
  `docs/rules/Academic rules.md` (core academic, performance, semester, course type,
  behavior, learning, and constraint features).
- ML models MUST be trained on synthetic data that satisfies all academic rules
  and behavioral realism requirements (Principle V).
- Course difficulty MUST be derived from historical data; hardcoded difficulty
  values are prohibited.
- Summer semester recommendations MUST only include courses where the student's
  current grade is F.
- Elective selection MUST use ML scoring when multiple courses satisfy identical
  type/level/semester constraints; exactly ONE elective MUST be selected per group.
- Alternative courses (graduation-necessity cases) MUST each carry an ML score
  and expected GPA impact; students MUST be able to substitute lower-scoring
  primary courses with higher-scoring alternatives.

## Development Workflow

- The rule engine MUST be implemented and independently validated before ML
  integration begins on any feature that involves course eligibility.
- Any change to academic regulations MUST be reviewed against
  `docs/rules/Academic rules.md` and reflected in both the rule engine and
  any affected ML feature definitions before the change is merged.
- PDF extraction for Arabic transcripts MUST correctly map all grade symbols
  (including Arabic characters) and MUST be validated against real transcript
  samples before integration.
- All data generation scripts MUST enforce relational integrity and produce
  GPA values via calculation, never direct assignment.
- Code reviews for features touching the rule engine, ML pipeline, or data
  generation layer MUST include an explicit Constitution Check verification
  (Principles I–III) before merge approval.

## Governance

This constitution supersedes all other development practices and guidelines for
the GPA Goes UP project. It encodes the architectural and academic integrity
requirements that define system correctness.

**Amendment procedure**:

1. Propose the change with a rationale referencing the specific principle affected.
2. Update `CONSTITUTION_VERSION` per semantic versioning:
   - MAJOR: removal or incompatible redefinition of an existing principle.
   - MINOR: addition of a new principle or section, or materially expanded guidance.
   - PATCH: clarification, wording improvement, or non-semantic refinement.
3. Set `LAST_AMENDED_DATE` to the ISO date of the amendment.
4. Propagate the change to dependent templates (plan-template, spec-template,
   tasks-template) and prepend an updated Sync Impact Report to this file.

**Compliance review**: Every implementation plan's Constitution Check section MUST
verify all applicable gates against this document. All PRs touching the rule engine,
ML pipeline, or data generation layer MUST include a constitution compliance statement
in the PR description.

For runtime development guidance and the authoritative academic rule reference,
see `docs/rules/Academic rules.md`.

**Version**: 1.0.0 | **Ratified**: 2026-04-09 | **Last Amended**: 2026-04-09
