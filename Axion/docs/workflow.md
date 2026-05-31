# Workflow

This file defines the development process for the Axion CAS project.
Every phase follows this workflow exactly, in order.
Do not skip steps.

---

## Entry Point

```
docs/study.md
```

`study.md` is the source of truth for the project. It contains:
- Feasibility assessment and risk analysis
- Architecture: AST core, pipeline, module design
- Phase implementation plan with deliverables
- Technology stack and design decisions

Before starting any phase, the relevant phase section in `study.md` must
be complete and agreed upon. Coding does not begin until the phase scope is defined.

---

## Per-Phase Iteration

```
docs/study.md  (phase scope defined and agreed)
      │
      ▼
  1. Coding
  2. Testing
  3. Demo
  4. Documentation
      │
      ▼
  5. Notify — await signal to proceed to next phase
```

---

### Step 1 — Coding

Implement everything listed under the phase's **Deliverables** section in `study.md`.

- All C++ code must compile with zero warnings (`-Wall -Wextra -Werror`) before moving to testing
- Use `cmake --build build` to build the project

---

### Step 2 — Testing

Testing is done in two sequential sub-steps. Do not skip or reverse the order.

#### 2.1 — Regression Testing First

Before writing any new test cases, run all existing tests to confirm
no regression from previous phases:

```bash
cd build && ctest --output-on-failure
```

All previous tests must still pass before any new test cases are written or run.

If a regression is found:
1. Diagnose the root cause
2. Fix the code
3. Rerun all previous tests
4. Repeat until all pass
5. Record the bug in `docs/codebase_analysis.md`

**Do not write new test cases until all regression tests pass.**

#### 2.2 — New Test Cases

Once regression passes, implement and run the new test cases for this phase.

If a test fails:
1. Diagnose the bug
2. Fix the code
3. Rerun all tests
4. Repeat until every test passes
5. Record any bug in `docs/codebase_analysis.md`

**All tests — regression and new — must pass before proceeding to the demo.**

Whenever a bug is found during testing or demo:
1. Record it in `docs/test.md` — symptom, root cause, fix, test output
2. Record it in `docs/codebase_analysis.md` — deep explanation of root cause
3. Record it in `docs/history.md` — what changed and why

---

### Step 3 — Demo

Run the demo as specified in the phase's **Demo** section in `study.md`.

The demo must work end-to-end. A phase is not complete until its demo passes.

- Verify the expected output matches the demo spec in `study.md`
- Record the actual output in `docs/demos/demo.XX.<brief-intro>.md`

---

### Step 4 — Documentation

Update all documentation files. All must be updated before notifying.
Do not skip any file.

**IMPORTANT — Write documents section by section, not in one batch.**
When document content is large, write one section or concept at a time,
verify it, then continue to the next.

#### 4.1 — `docs/codebase_analysis.md`
- Explanation of new knowledge and concepts introduced in this phase
- Code analysis: walk through every new or changed file and explain it
- **Target reader: a complete beginner with zero prior knowledge.**
- Write one module or concept at a time
- **Every algorithm must include ALL four of the following:**
  1. Concept explanation
  2. ASCII diagram/illustration
  3. Annotated code snippet
  4. Why it works
- **Every bug must have ALL five of the following:**
  1. Symptom
  2. Investigation steps
  3. Root cause
  4. Fix
  5. Lesson

#### 4.2 — `docs/test.md`
- Record all testing activities for this phase
- Each test case: input, expected output, actual output, verdict
- Issues found, how they were diagnosed, and how they were fixed

#### 4.3 — `docs/demos/demo.XX.<brief-intro>.md`
- One demo file per phase
- Include: prerequisites, build steps, run steps, expected output, actual output
- **Prerequisites must be fully self-contained.** Do NOT refer to another demo file.

#### 4.4 — `docs/history.md`
- Record all activities in this phase: coding, testing, demo
- What was added, changed, removed
- Bugs found and fixed
- Decisions made and why

---

### Step 5 — Notify

Notify that the phase is complete. State:
- Which phase was completed
- Demo command and where output can be verified
- Whether all tests passed
- Any known issues or deviations from the plan in `study.md`

**Wait for explicit approval before starting the next phase.**

---

## Build System

```bash
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"
cd "$AXION_ROOT"

cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build            # build all targets
cd build && ctest --output-on-failure  # run all tests
./axion                        # run the REPL
```

---

## File Writing Techniques

When writing large content to files (documentation, source code, config),
use these techniques to avoid getting stuck mid-write.

### Technique 1 — Append section by section

For building up a large new document:

1. Append one section at a time
2. Each append is a small, self-contained write
3. Verify after each append

### Technique 2 — Write to a temp file, then apply with a script

For large targeted replacements in an existing file:

1. Write the new content to a temp file (e.g. `docs/patch_study.py`)
2. The script reads the target file, finds the anchor text, replaces it
3. Run the script: `python3 docs/patch_study.py`
4. Verify the result, then delete the temp script

### General Rules

- **Always verify after writing.**
- **Always delete temp scripts and temp files** after use.

---

## Git Hygiene

### What is ignored

| Pattern | What it ignores |
|---------|----------------|
| `build/` | CMake build directory |
| `*.o`, `*.a` | Object files and archives |
| `*.swp`, `*~`, `.DS_Store` | Editor and OS temp files |

### Before every commit

```bash
git status
git diff --cached --name-only | grep -E '\.o$|\.a$|build/'
```

If any artifact appears, it was accidentally staged. Remove with:

```bash
git rm --cached <file>
```

### Line endings

This repo uses LF line endings. Always use WSL for file operations to avoid
CRLF corruption.
