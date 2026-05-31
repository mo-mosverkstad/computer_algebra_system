# History

Chronological record of changes to the Axion CAS project.

---

## Phase 1 — MVP (2026-05-31)

### Added

- **Project infrastructure**
  - `CMakeLists.txt` — CMake build system with C++17, `-Wall -Wextra -Werror`
  - `.gitignore` — ignores build artifacts, editor temps, Python cache
  - `docs/` — study.md, environment_setup.md, docs_guide.md, workflow.md

- **Core modules**
  - `src/core/arena.h/.cpp` — arena allocator (64KB blocks, placement new)
  - `src/core/ast.h/.cpp` — expression tree (NUM, SYM, ADD, MUL, POW, FUNC, NEG) with factory functions

- **Frontend**
  - `src/frontend/lexer.h/.cpp` — tokenizer (numbers, symbols, operators, parens)
  - `src/frontend/parser.h/.cpp` — Pratt parser with correct precedence (+/- < */÷ < ^), right-associative power, unary minus, function calls

- **Engine**
  - `src/engine/simplify.h/.cpp` — simplification engine: identity rules (x+0, x*1, x*0, x^0, x^1), constant folding, flattening nested ADD/MUL, like-term combination, canonical sorting
  - `src/engine/eval.h/.cpp` — numeric evaluation with variable environment

- **Output**
  - `src/output/printer.h/.cpp` — pretty printer with minimal parentheses, handles NEG as subtraction

- **REPL**
  - `src/main.cpp` — readline-based interactive loop, supports direct simplification and `eval(expr, var=val)` command

- **Tests**
  - `tests/test_lexer.cpp` — 3 tests
  - `tests/test_parser.cpp` — 6 tests
  - `tests/test_simplify.cpp` — 8 tests
  - `tests/test_eval.cpp` — 5 tests
  - Total: 22 tests, all passing

### Decisions

- Chose immutable AST with arena allocation for safety and performance
- Chose Pratt parser over recursive descent for extensibility
- Chose GNU Readline for REPL (line editing, history) — fits CLI-only WSL constraint
- NEG nodes converted to MUL(-1, x) during simplification for canonical form
- Like-term combination uses string-based expression keys for grouping

### Known Limitations

- No differentiation yet (Phase 2)
- No polynomial expansion (Phase 3)
- Division represented as `x * y^(-1)` — no dedicated DIV node
- Simplifier does not yet handle all edge cases (e.g. `x*x` → `x^2`)
