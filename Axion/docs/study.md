# Axion CAS — Feasibility Study & Implementation Proposal

## 1. Project Summary

**Axion** is a computer algebra system (CAS) implemented in C/C++, targeting a CLI-only environment (WSL Ubuntu, no GUI). The system will parse, represent, simplify, differentiate, and evaluate symbolic mathematical expressions via a text-based REPL.

---

## 2. Feasibility Assessment

### 2.1 What Is Feasible (Solo Developer, C/C++)

| Feature | Feasibility | Estimated Effort |
|---------|-------------|-----------------|
| Expression lexer/parser | ✅ High | 1–2 weeks |
| AST representation | ✅ High | 1 week |
| Basic simplification (identity rules) | ✅ High | 2–3 weeks |
| Symbolic differentiation | ✅ High | 1–2 weeks |
| Numeric evaluation | ✅ High | 1 week |
| Polynomial expansion | ✅ High | 2 weeks |
| Pretty printer (text) | ✅ High | 1 week |
| CLI REPL | ✅ High | 1 week |
| Relational operators & factorial | ✅ High | 1–2 weeks |
| Subscript/indexed variables | ✅ High | 1 week |
| Finite summation/product | ✅ High | 2–3 weeks |
| Closed-form sums | 🟡 Medium | 2–3 weeks |
| Limits (basic rules, L'Hôpital) | 🟡 Medium | 3–4 weeks |
| Table-based integration | 🟡 Medium | 3–4 weeks |
| Integration by substitution | 🟡 Medium | 4–6 weeks |
| Matrix operations | ✅ High | 3–4 weeks |
| Determinant & inverse | ✅ High | 2 weeks |
| Linear equation solving | ✅ High | 2 weeks |
| Quadratic equation solving | ✅ High | 1–2 weeks |
| Systems of equations | 🟡 Medium | 3–4 weeks |
| Term canonicalization | 🟡 Medium | 3–4 weeks |
| Pattern-matching rewrite engine | 🟡 Medium | 4–6 weeks |
| Taylor series | 🟡 Medium | 2–3 weeks |
| Partial derivatives & vector calculus | 🟡 Medium | 3–4 weeks |
| Basic factorization | 🟡 Medium | 4–6 weeks |
| Number theory (GCD, binomial) | ✅ High | 2–3 weeks |
| General symbolic integration | 🔴 Low (research-level) | months+ |
| General equation solving | 🔴 Low | months+ |
| Differential equations | 🔴 Low | months+ |

### 2.2 Risk Analysis

| Risk | Mitigation |
|------|-----------|
| Simplification complexity explodes | Start with hardcoded rules; defer pattern engine |
| Canonical form is hard to get right | Define strict ordering early; test extensively |
| Memory pressure from tree allocations | Use arena allocator from the start |
| Scope creep | Strict phased roadmap; MVP first |
| No GUI for output | Use ASCII pretty-printing; optionally emit LaTeX strings |

### 2.3 Conclusion

Building a CAS with parsing, simplification, differentiation, polynomial algebra, and numeric evaluation is **fully feasible** for a solo developer in C/C++ within 3–6 months. Advanced features (integration, general solving) are deferred to later phases.

---

## 3. Software Architecture

```
┌─────────────────────────────┐
│         CLI / REPL          │   ← User interaction (readline-based)
└─────────────┬───────────────┘
              │ input string
┌─────────────▼───────────────┐
│     Frontend (Lexer+Parser) │   ← Tokenize & build AST
└─────────────┬───────────────┘
              │ AST
┌─────────────▼───────────────┐
│     Core Symbolic Engine    │   ← Simplify, canonicalize, rewrite
└─────────────┬───────────────┘
              │ simplified AST
┌─────────────▼───────────────┐
│      Domain Modules         │   ← Calculus, Polynomial, Linear Algebra
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Evaluation / Output       │   ← Numeric eval, pretty-print
└─────────────────────────────┘
```

---

## 4. Module Design

### 4.1 AST Core (`src/core/ast.h`)

The central data structure. All modules operate on this.

```cpp
enum class NodeType { NUM, SYM, ADD, MUL, POW, FUNC, NEG,
                      REL, FACTORIAL, ABS, SUBSCRIPT,
                      SUM, PROD, LIM, INTEGRAL,
                      MATRIX, VECTOR, EQUATION };

struct Expr {
    NodeType type;
    double num_val;              // for NUM
    std::string name;           // for SYM / FUNC / REL operator
    std::vector<Expr*> children;
};
```

Design decisions:
- **Immutable** — transformations produce new nodes.
- **Arena-allocated** — all `Expr` nodes live in a pool; no individual `delete`.
- **Canonical ordering** — children of ADD/MUL sorted by a defined order (numbers first, then symbols alphabetically, then compound expressions by structure).

### 4.2 Memory Arena (`src/core/arena.h`)

```cpp
class Arena {
    std::vector<std::unique_ptr<char[]>> blocks;
public:
    Expr* alloc();
    void reset(); // free all at once
};
```

Avoids per-node `new`/`delete`. Entire expression trees are freed in bulk.

### 4.3 Lexer (`src/frontend/lexer.h`)

Converts input string to token stream.

Tokens: `NUMBER`, `SYMBOL`, `PLUS`, `MINUS`, `STAR`, `CARET`, `LPAREN`, `RPAREN`, `COMMA`, `END`.

### 4.4 Parser (`src/frontend/parser.h`)

**Pratt parser** (top-down operator precedence). Handles:
- Infix operators with correct precedence: `+` < `*` < `^`
- Prefix minus
- Function calls: `sin(x)`, `diff(expr, x)`
- Parentheses

### 4.5 Simplification Engine (`src/engine/simplify.h`)

The core of the CAS. Applies rules bottom-up:

Phase 1 (hardcoded rules):
- `x + 0 → x`, `x * 1 → x`, `x * 0 → 0`, `x ^ 1 → x`, `x ^ 0 → 1`
- Flatten nested ADD/MUL: `(a + (b + c)) → (a + b + c)`
- Combine like terms: `a*x + b*x → (a+b)*x`
- Combine numeric constants: `2 + 3 → 5`
- Sort children into canonical order

Phase 2 (future): pattern-matching rewrite engine.

### 4.6 Calculus Module (`src/modules/calculus.h`)

Symbolic differentiation via recursive rules:
- `d/dx(c) = 0`
- `d/dx(x) = 1`
- `d/dx(f+g) = f' + g'`
- `d/dx(f*g) = f'g + fg'`
- `d/dx(f^n) = n*f^(n-1)*f'`
- `d/dx(sin(f)) = cos(f)*f'`
- `d/dx(cos(f)) = -sin(f)*f'`
- `d/dx(ln(f)) = f'/f`

Symbolic integration (Phase 7):
- Table lookup for standard forms
- Linearity rule
- Basic substitution via pattern matching

Always followed by simplification.

### 4.7 Polynomial Module (`src/modules/polynomial.h`)

Represents polynomials as `map<vector<int>, Rational>` (monomial exponent vector → coefficient).

Operations: add, multiply, expand, collect terms.

### 4.8 Evaluation Engine (`src/engine/eval.h`)

Substitutes numeric values for symbols and computes result:

```cpp
double evaluate(const Expr* e, const std::unordered_map<std::string, double>& env);
```

### 4.9 Summation & Product Module (`src/modules/series.h`)

Handles finite and symbolic sums/products:
- `sum(expr, var, lower, upper)` — evaluate finite sums, recognize closed forms
- `prod(expr, var, lower, upper)` — evaluate finite products
- Known closed forms: arithmetic series, geometric series, sum of squares/cubes

### 4.10 Limits Module (`src/modules/limits.h`)

Computes limits symbolically:
- Direct substitution
- L'Hôpital's rule for indeterminate forms (0/0, ∞/∞)
- One-sided limits
- Limits at infinity

### 4.11 Matrix Module (`src/modules/matrix.h`)

Matrix and vector algebra:
- Matrix literal representation (2D vector of Expr*)
- Addition, scalar multiplication, matrix multiplication
- Determinant (cofactor expansion)
- Transpose, inverse
- Eigenvalues for small matrices

### 4.12 Equation Solver (`src/modules/solver.h`)

Solves equations symbolically:
- Linear: isolate variable
- Quadratic: quadratic formula
- Systems: Gaussian elimination
- Polynomial: rational root theorem

### 4.13 Pretty Printer (`src/output/printer.h`)

Converts AST back to human-readable string with correct precedence and minimal parentheses.

### 4.10 REPL / CLI Driver (`src/main.cpp`)

Interactive loop using GNU Readline for line editing and history.

Commands:
- Direct expression input → simplify and print
- `diff(expr, x)` → differentiate
- `eval(expr, x=2)` → numeric evaluation
- `expand(expr)` → polynomial expansion
- `sum(expr, var, lo, hi)` → summation
- `prod(expr, var, lo, hi)` → product
- `lim(expr, var, point)` → limit
- `integrate(expr, var)` → indefinite integral
- `integrate(expr, var, a, b)` → definite integral
- `solve(equation, var)` → equation solving
- `det(matrix)` → determinant
- `quit` / `exit`

---

## 5. Directory Structure

```
Axion/
├── CMakeLists.txt
├── docs/
│   ├── ideas.md
│   ├── study.md
│   ├── environment_setup.md
│   ├── docs_guide.md
│   ├── workflow.md
│   ├── history.md
│   ├── test.md
│   ├── codebase_analysis.md
│   └── demos/
├── src/
│   ├── main.cpp
│   ├── core/
│   │   ├── ast.h / ast.cpp
│   │   ├── arena.h / arena.cpp
│   │   └── symbols.h / symbols.cpp
│   ├── frontend/
│   │   ├── lexer.h / lexer.cpp
│   │   └── parser.h / parser.cpp
│   ├── engine/
│   │   ├── simplify.h / simplify.cpp
│   │   └── eval.h / eval.cpp
│   ├── modules/
│   │   ├── calculus.h / calculus.cpp
│   │   ├── polynomial.h / polynomial.cpp
│   │   ├── series.h / series.cpp
│   │   ├── limits.h / limits.cpp
│   │   ├── matrix.h / matrix.cpp
│   │   └── solver.h / solver.cpp
│   └── output/
│       └── printer.h / printer.cpp
└── tests/
    ├── test_lexer.cpp
    ├── test_parser.cpp
    ├── test_simplify.cpp
    ├── test_calculus.cpp
    ├── test_eval.cpp
    ├── test_polynomial.cpp
    ├── test_series.cpp
    ├── test_limits.cpp
    ├── test_matrix.cpp
    └── test_solver.cpp
```

---

## 6. Build System

**CMake** (minimum version 3.16).

- C++17 standard
- Dependencies: GNU Readline (for REPL), Google Test (for unit tests)
- Single executable target: `axion`
- Separate test executable: `axion_tests`

---

## 7. Implementation Roadmap

### Phase 1 — MVP (Weeks 1–6) ✅ COMPLETE

- [x] Project setup (CMake, directory structure)
- [x] Arena allocator
- [x] AST definition
- [x] Lexer
- [x] Parser (Pratt)
- [x] Pretty printer
- [x] Basic simplification (identity rules, constant folding, flattening)
- [x] Numeric evaluation
- [x] REPL with readline

**Deliverable:** User types `2*x + 3*x`, gets `5*x`.

### Phase 2 — Calculus (Weeks 7–10) ✅ COMPLETE

- [x] Symbolic differentiation
- [x] Chain rule, product rule
- [x] Trigonometric derivatives
- [x] Post-differentiation simplification

**Deliverable:** `diff(sin(x^2), x)` → `2*x*cos(x^2)`

### Phase 3 — Algebra (Weeks 11–16) ✅ COMPLETE

- [x] Polynomial representation
- [x] Expand: `(x+1)^3`
- [x] Collect terms
- [x] Canonical form improvements
- [x] Like-term combination for multivariate expressions
- [x] Replace GNU Readline with linenoise (copy from NordDB/third_party/linenoise)
  - Removes `libreadline-dev` dependency
  - Supports line editing, history, multi-line input
  - Bundled as `third_party/linenoise/` (linenoise.c, linenoise.h)

**Deliverable:** `expand((x+1)*(x+2))` → `2 + x^2 + 3*x` ✅

### Phase 4 — Extended Operators & Relations (Weeks 17–20) ✅ COMPLETE

- [x] Relational operators: `=`, `!=`, `<`, `>`, `<=`, `>=`
- [x] Assignment operator: `:=` (session variable binding)
- [x] User-defined functions: `f(x) := x^2`
- [x] Factorial operator: `n!`
- [x] Absolute value: `abs(x)`
- [x] Subscript identifiers: `x_1`, `x_(12)`
- [x] Mathematical constants: `pi`, `e` (symbolic, evaluate with `approx`)
- [x] Previous result: `%` refers to last output
- [x] Numeric approximation: `approx(expr)` or `approx(expr, digits)`
- [x] Rational arithmetic: `1/3` stays exact (not 0.333...)
- [x] Short aliases: `int` for `integrate`, `simp` for `simplify`

**Syntax decisions locked:**
- `=` means equality/equation; `:=` means assignment
- `diff(f, x, 2)` for 2nd derivative; `diff(f, [x, y])` for mixed partials
- `lim(f, x, 0, right)` / `lim(f, x, 0, left)` for one-sided limits
- `x_1` and `x_(12)` are single identifier names

**Deliverable:** `5!` → `120`, `a := 3` then `a + 1` → `4`, `approx(pi)` → `3.14159265358979`, `1/3 + 1/6` → `1/2`

### Phase 5 — Summation & Product (Weeks 21–24) ✅ COMPLETE

- [x] Symbolic summation: `sum(expr, var, lower, upper)`
- [x] Symbolic product: `prod(expr, var, lower, upper)`
- [x] Evaluate finite sums/products numerically
- [x] Known closed-form sums (arithmetic, geometric series)
- [x] Summation simplification rules
- [x] `collect(expr, var)` — group terms by powers of a variable

**Deliverable:** `sum(k, k, 1, 10)` → `55`, `collect(x^2 + 2*x + 3*x + 1, x)` → `1 + 5*x + x^2` ✅

### Phase 6 — Limits (Weeks 25–28)

- [ ] Limit computation: `lim(expr, var, point)`
- [ ] One-sided limits: `lim(expr, var, point, right)`, `lim(expr, var, point, left)`
- [ ] Infinity support: `inf` as a symbolic constant
- [ ] L'Hôpital's rule for 0/0 and ∞/∞ forms
- [ ] Basic limit rules (sum, product, quotient of limits)
- [ ] Complex number support: `i` as imaginary unit, `2 + 3*i`

**Deliverable:** `lim(sin(x)/x, x, 0)` → `1`, `lim(1/x, x, 0, right)` → `inf`

### Phase 7 — Symbolic Integration (Weeks 29–34)

- [ ] Table-based integration (power, trig, exp, ln)
- [ ] Linearity: `int(a*f + b*g) = a*int(f) + b*int(g)`
- [ ] Substitution (basic pattern matching)
- [ ] Integration by parts (heuristic)
- [ ] Definite integrals: `integrate(expr, var, a, b)` / `int(expr, var, a, b)`
- [ ] Partial fraction decomposition: `apart(expr, var)`

**Deliverable:** `int(x^2, x)` → `x^3/3`, `int(sin(x), x, 0, pi)` → `2`

### Phase 8 — Matrices & Vectors (Weeks 35–40)

- [ ] Matrix literal syntax: `[[1,0],[0,1]]`
- [ ] Vector syntax: `[a, b, c]`
- [ ] Matrix operations: addition, scalar multiplication, matrix multiplication
- [ ] Dot product: `dot([a,b,c], [d,e,f])`
- [ ] Cross product: `cross([a,b,c], [d,e,f])`
- [ ] Determinant: `det([[a,b],[c,d]])`
- [ ] Transpose: `transpose(M)`
- [ ] Inverse (2×2, 3×3)
- [ ] Eigenvalues (2×2)

**Deliverable:** `det([[1,2],[3,4]])` → `-2`, `dot([1,2,3],[4,5,6])` → `32`

### Phase 9 — Equation Solving (Weeks 41–46)

- [ ] Linear equations: `solve(a*x + b = 0, x)`
- [ ] Quadratic equations: `solve(a*x^2 + b*x + c = 0, x)`
- [ ] Systems of linear equations (Gaussian elimination)
- [ ] Polynomial roots (rational root theorem)
- [ ] Inequality solving (linear)
- [ ] `factor(expr)` — polynomial factorization

**Deliverable:** `solve(x^2 - 5*x + 6 = 0, x)` → `{2, 3}`, `factor(x^2 - 1)` → `(x - 1)*(x + 1)`

### Phase 10 — Pattern Matching & Rewrite Engine (Weeks 47–52)

- [ ] Pattern language: wildcards, typed placeholders
- [ ] Rule definition: `rule(pattern, replacement)`
- [ ] User-defined simplification rules
- [ ] Conditional rules (with guards)
- [ ] Rule ordering and priority
- [ ] Configurable Pratt parser: data-driven precedence table and handler registration
  - Users can define custom operators at runtime
  - Keeps O(n) performance of Pratt parsing
  - No PEG overhead or backtracking

**Deliverable:** User defines `rule(sin(x)^2 + cos(x)^2, 1)` and it applies automatically.

### Phase 11 — Advanced Calculus (Future)

- [ ] Partial derivatives: `diff(f, [x, y])` (mixed partials)
- [ ] Higher-order: `diff(f, x, 2)` for d²f/dx²
- [ ] Gradient, divergence, curl (vector calculus)
- [ ] Taylor/Maclaurin series expansion: `taylor(expr, var, point, order)`
- [ ] Trigonometric simplification: `trigsimp(expr)`
- [ ] Differential equations (basic separable, first-order linear)

**Deliverable:** `taylor(sin(x), x, 0, 5)` → `x - x^3/6 + x^5/120`, `diff(x^2*y, x, 2)` → `2*y`

### Phase 12 — Number Theory & Discrete Math (Future)

- [ ] Integer factorization
- [ ] GCD, LCM
- [ ] Modular arithmetic
- [ ] Binomial coefficients: `binom(n, k)`
- [ ] Combinatorial functions: permutations, combinations

**Deliverable:** `binom(10, 3)` → `120`, `gcd(48, 18)` → `6`

---

## 8. Testing Strategy

- **Unit tests** per module using Google Test.
- **Regression tests** — a file of `input → expected_output` pairs run automatically.
- **Fuzz testing** (optional) — random expression generation to catch crashes.

Key test cases:
```
simplify("x + 0")          → "x"
simplify("x + x")          → "2*x"
simplify("2 + 3")          → "5"
diff("x^3", "x")           → "3*x^2"
diff("sin(x)", "x")        → "cos(x)"
eval("x^2 + 1", {x=3})    → "10"
expand("(x+1)*(x-1)")      → "x^2 - 1"
```

---

## 9. Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | C++17 | Performance, control, modern features |
| AST mutability | Immutable | Safer transformations, easier debugging |
| Memory | Arena allocator | Avoid fragmentation, fast bulk free |
| Parser type | Pratt parser | Simple, extensible, handles precedence |
| Simplification | Bottom-up rule application | Predictable, debuggable |
| Canonical form | Sorted children, numbers first | Enables term combination |
| Build system | CMake | Standard, cross-platform |
| Testing | Google Test | Widely used, good C++ support |
| UI | CLI REPL with readline | Matches WSL/no-GUI constraint |

---

## 10. References & Inspirations

- **GiNaC** (C++ symbolic library) — architecture reference
- **SymPy** (Python CAS) — algorithm reference
- **Maxima** — classic CAS design
- "Modern Computer Algebra" by von zur Gathen & Gerhard
- "A = B" by Petkovsek, Wilf, Zeilberger (for algorithmic identities)
