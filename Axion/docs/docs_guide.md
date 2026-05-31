# Documentation Guide

This folder contains all documentation for the Axion CAS project.
Each file serves a distinct purpose and targets a different reading context.

---

## File Index

### `study.md`
The design and planning document. Read this first if you want to understand
**what** the project is trying to achieve and **why** it is structured the way it is.

Contents:
- Feasibility assessment: technical feasibility per feature, risk analysis
- Architecture: layered pipeline, module design, AST core
- Module-by-module design (lexer, parser, simplifier, calculus, etc.)
- Phase implementation plan (Phase 1–4) with deliverables
- Technology stack choices and design decisions
- Testing strategy

---

### `ideas.md`
Initial brainstorming and raw ideas. Read this if you want to understand the
original motivation and early thinking before the design was formalized.

---

### `environment_setup.md`
How to prepare the development environment. Covers all dependencies,
build tools, and commands needed to compile and run Axion on WSL Ubuntu (CLI only).

---

### `history.md`
The change log. A chronological record of every meaningful change made to
the project, organised by phase.

Contents:
- What was added, changed, or removed per phase
- Bug fixes and the bugs they resolved
- Structural refactors
- Decisions reversed or revised

---

### `test.md`
The test record. Documents every test case, how to run it, and what happened.

Contents:
- How to build and run tests per phase
- Per-phase test cases — input, expected output, actual output
- Verdicts — pass / fail
- Issues found and how they were fixed

---

### `codebase_analysis.md`
The deep-dive technical reference. Written for readers who are new to the
codebase or to the underlying concepts (symbolic computation, expression trees,
rewrite systems, parsing algorithms).

Contents:
- Background knowledge — concepts behind each subsystem
- Module-by-module code walkthrough — every source file explained
- Key algorithms — with concept explanation, ASCII diagram, annotated code snippet
- Design decisions — why certain choices were made
- Per-phase additions — new concepts and code introduced in each phase
- Bug analysis — symptom, investigation, root cause, fix, and lesson for every bug found

**Writing rules (mandatory):**
- Write section by section, not in one batch.
- **Target reader: a complete beginner.** Assume the reader has never heard of
  an AST, a Pratt parser, canonical forms, or term rewriting.
  Every concept must be explained from first principles before the code is shown.
- Every algorithm must include ALL of the following:
  1. **Concept explanation** — what is this thing, why does it exist, what problem does it solve?
  2. **ASCII illustration/diagram** — draw the data flow, tree structure, or transformation.
  3. **Annotated code snippet** — show the actual code with inline comments on every non-obvious line.
  4. **Why it works** — explain the reasoning behind the design choice.
- Every bug must have a dedicated analysis section with ALL of the following:
  1. **Symptom** — exact output or error message observed
  2. **Investigation steps** — what was checked, printed, or inspected
  3. **Root cause** — the precise reason the bug occurred
  4. **Fix** — before/after code showing exactly what changed
  5. **Lesson** — the general principle that prevents this class of bug in future

---

### `demos/`
Per-phase demo documentation. Each file is a hands-on runbook with step-by-step
instructions for building, running, and verifying the demo for that phase.

Naming convention: `demo.<phase_no>.<brief_intro>.md`
(e.g. `demo.01.basic-simplification.md`, `demo.02.differentiation.md`)

Contents per demo file:
- Prerequisites and environment setup
- Build instructions
- How to run the demo
- Expected output and how to verify correctness
- Actual measured output

**Mandatory rule — Prerequisites must be fully self-contained:**
Every demo file must include all tool installation steps, WSL setup, directory
location, and build commands needed to run that demo from scratch. Do NOT refer
to another demo file — copy the steps in full.

---

### `workflow.md`
The development process definition. Describes the exact iteration loop
followed in every phase: coding → testing → demo → documentation →
notify and await approval.

---

## Reading Order

| Goal | Start here |
|------|-----------|
| Understand the project vision and plan | `study.md` |
| Set up the dev environment | `environment_setup.md` |
| Learn how the code works | `codebase_analysis.md` |
| Run or demo a phase | `demos/` |
| Check test results | `test.md` |
| See what changed recently | `history.md` |
| Understand the dev process | `workflow.md` |
| See original ideas | `ideas.md` |
