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

---

## Phase 2 — Calculus (2026-05-31)

### Added

- **Calculus module**
  - `src/modules/calculus.h/.cpp` — symbolic differentiation engine
  - Supports: power rule, sum rule, product rule (n-ary), chain rule
  - Functions: sin, cos, tan, ln, log, exp, sqrt
  - General case: `f^g` via logarithmic differentiation

- **REPL update**
  - `diff(expr, var)` command added
  - Version bumped to v0.2

- **Tests**
  - `tests/test_calculus.cpp` — 12 new tests (constant, variable, linear, power, sum, product, sin, cos, chain rule, exp, ln)
  - Total: 34 tests, all passing

### Changed

- **Simplifier fix:** `MUL(-1, x)` now reduces to `NEG(x)` for cleaner output (`-sin(x)` instead of `-1*sin(x)`)
- **NEG handling:** NEG nodes are no longer converted to MUL(-1, x) during simplification — they remain as NEG for readable output

### Bugs Found and Fixed

1. **`-1*sin(x)` instead of `-sin(x)`**
   - Cause: simplifier did not recognize `MUL(-1, f)` as negation
   - Fix: added check in MUL simplification to convert `MUL(-1, x)` → `NEG(x)`

### Known Limitations

- No polynomial expansion (Phase 3)
- Division represented as `x * y^(-1)` — no dedicated DIV node
- Simplifier does not yet handle `x*x` → `x^2`
- Canonical ordering puts constants before terms: `1 + 2*x` not `2*x + 1`

---

## Phase 3 — Algebra (2026-05-31)

### Added

- **Polynomial module**
  - `src/modules/polynomial.h/.cpp` — `expand()` function
  - Distributes products over sums: `(x+1)*(x+2)` → `x^2 + 3x + 2`
  - Expands integer powers of compound expressions: `(x+1)^3`
  - Deep-copies base before repeated multiplication to avoid aliasing
  - Distributes NEG over ADD: `-(a+b)` → `-a + -b`

- **Linenoise integration**
  - Replaced GNU Readline with bundled linenoise (`third_party/linenoise/`)
  - Removes `libreadline-dev` system dependency
  - Supports line editing, history, multi-line input

- **REPL update**
  - `expand(expr)` command added
  - Version bumped to v0.3

- **Tests**
  - `tests/test_polynomial.cpp` — 6 new tests (simple product, square, cube, diff of squares, multivariate, no-expansion)
  - Total: 40 tests, all passing

### Changed

- **CMakeLists.txt** — now builds linenoise as static C library, removed readline link
- **`extract_coeff` fix** — now correctly handles MUL nodes with 3+ children (e.g. `MUL(2, x, x)`) by stripping the numeric coefficient and returning the remaining factors as base

### Bugs Found and Fixed

1. **`(x+1)^3` produced wrong result (21 instead of 27 at x=2)**
   - Cause: `expand` reused the same `base` pointer across iterations; `simplify` mutated shared nodes
   - Fix: deep-copy base before each multiplication iteration

2. **`MUL(2, x, x)` treated as pure number 2 in like-term combination**
   - Cause: `extract_coeff` returned `{2.0, nullptr}` for MUL with 3+ children, and `nullptr` base was added to `num_sum`
   - Fix: strip numeric first child from the MUL node and return remaining children as base

### Known Limitations

- Canonical ordering puts constants before terms: `2 + x^2 + 3*x` not `x^2 + 3*x + 2`

### Additional Fixes (completing Phase 3 checklist)

3. **Power collection:** `x*x` → `x^2`, `x*x*x` → `x^3`
   - Added like-base grouping in MUL simplifier: factors with same base have exponents summed
   - `MUL(x, x)` → `POW(x, 2)`, `MUL(x, POW(x, 2))` → `POW(x, 3)`

4. **NEG flattening in MUL:** `MUL(x, NEG(y))` → `MUL(-1, x, y)` → `NEG(MUL(x, y))`
   - Extracts -1 from NEG children during MUL simplification
   - Enables `expand((x+y)*(x-y))` → `x^2 - y^2` (terms cancel correctly)

---

## Phase 4 — Extended Operators & Relations (2026-05-31)

### Added

- **Rational arithmetic**
  - Numbers stored as `int64_t num/den` (exact fractions)
  - `1/3 + 1/6` → `1/2` (no floating-point loss)
  - GCD-based reduction after every operation
  - Printer shows `1/2` for fractions, plain integers otherwise

- **Factorial operator**
  - Postfix `!` in lexer/parser
  - `FACTORIAL` node type in AST
  - Simplifies to integer for n=0..20: `5!` → `120`

- **Relational operators**
  - `=`, `!=`, `<`, `>`, `<=`, `>=` parsed as `REL` nodes
  - Used in `eval(expr, x=3)` and future `solve()`

- **Assignment & user functions**
  - `:=` operator for session variable binding: `a := 3`
  - User-defined functions: `f(x) := x^2 + 1` then `f(3)` → `10`
  - Session state persists across REPL inputs

- **Subscript identifiers**
  - `x_1`, `x_(12)`, `a_ij` parsed as single identifier names
  - `_` followed by alphanumeric, or `_(...)` for multi-char subscripts

- **Constants & approximation**
  - `pi` and `e` as symbolic constants
  - `approx(pi)` → `3.14159265358979`
  - `approx(expr)` evaluates with pi=π, e=e numerically

- **Previous result**
  - `%` refers to last computed result

- **Multi-argument function parsing**
  - `diff(x^3, x)`, `eval(x^2, x=3)` parsed as FUNC with multiple children
  - Commands handled by REPL dispatcher

- **Tests**
  - 46 tests total, all passing
  - New: Lexer (factorial, relational, assignment, subscript), Parser (factorial, relational, multi-arg), Simplify (factorial, rational add/mul), Eval (factorial, rational)

### Changed

- **AST rewrite:** `double num` → `int64_t num, int64_t den` (rational representation)
- **Lexer rewrite:** supports `!`, `:=`, `<=`, `>=`, `!=`, `=`, `%`, `_` in identifiers
- **Parser rewrite:** Pratt parser extended with postfix `!`, relational precedence level, multi-arg functions, assignment parsing
- **Simplifier rewrite:** all arithmetic now uses exact rational operations
- **Evaluator update:** handles FACTORIAL node, rational num_val()
- **Printer update:** displays fractions as `n/d`, factorial as `n!`, relational as `a = b`

### Bugs Found and Fixed

None — clean implementation on first build (after fixing missing `<iomanip>` include and removing unused functions).


---

## Phase 5 — Summation & Product (2026-05-31)

### Added

- **Series module** (`src/modules/series.h/.cpp`)
  - `eval_sum(arena, body, var, lo, hi)` — finite summation by substitution
  - `eval_prod(arena, body, var, lo, hi)` — finite product by substitution
  - `collect(arena, expr, var)` — group terms by powers of a variable
  - Safety limit: max 10000 iterations

- **REPL commands**
  - `sum(expr, var, lo, hi)` — compute finite sum
  - `prod(expr, var, lo, hi)` — compute finite product
  - `collect(expr, var)` — collect by variable

- **Tests**
  - `tests/test_series.cpp` — 6 new tests
  - Total: 52 tests, all passing

### Key Results

```
sum(k, k, 1, 10)        → 55
sum(k^2, k, 1, 5)       → 55
prod(k, k, 1, 5)        → 120
sum(1/k, k, 1, 4)       → 25/12  (exact rational!)
collect(x^2+2*x+3*x+1, x) → 1 + 5*x + x^2
```


---

## Phase 6 — Limits (2026-05-31)

### Added

- **Limits module** (`src/modules/limits.h/.cpp`)
  - `compute_limit(arena, expr, var, point, direction)` 
  - Direct substitution for continuous functions
  - L'Hôpital's rule for 0/0 indeterminate forms (recursive, max depth 5)
  - Detects quotient structure in MUL(numerator, POW(denominator, -1))

- **Simplifier enhancement**
  - `sin(0)` → `0`, `cos(0)` → `1`, `tan(0)` → `0`
  - `exp(0)` → `1`, `exp(1)` → `e`, `ln(1)` → `0`

- **REPL command**
  - `lim(expr, var, point)` — two-sided limit
  - `lim(expr, var, point, right)` / `lim(expr, var, point, left)` — one-sided

### Key Results

```
lim(x^2, x, 3)              → 9   (direct substitution)
lim((x^2-1)/(x-1), x, 1)   → 2   (L'Hôpital: 2x/1 at x=1)
lim(sin(x)/x, x, 0)         → 1   (L'Hôpital: cos(x)/1 at x=0)
lim((x^3-8)/(x-2), x, 2)   → 12  (L'Hôpital: 3x²/1 at x=2)
```

### Bugs Found and Fixed

1. **`lim((x^2-1)/(x-1), x, 1)` returned 0 instead of 2**
   - Cause: direct substitution ran first, simplifier computed `0 * (1/0) = 0`
   - Fix: try L'Hôpital before direct substitution

2. **`sin(0)` did not simplify to 0**
   - Cause: simplifier only evaluated `abs()` for numeric FUNC args
   - Fix: added sin(0)→0, cos(0)→1, exp(0)→1, ln(1)→0 rules

### Known Limitations

- Limits at infinity not yet implemented
- Complex numbers deferred to future phase
