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

### Phase 6 — Limits (Weeks 25–28) ✅ COMPLETE

- [x] Limit computation: `lim(expr, var, point)`
- [x] One-sided limits: `lim(expr, var, point, right)`, `lim(expr, var, point, left)`
- [x] Infinity support: `inf` as a symbolic constant
- [x] L'Hôpital's rule for 0/0 and ∞/∞ forms
- [x] Basic limit rules (sum, product, quotient of limits)
- [ ] Complex number support: `i` as imaginary unit (deferred)

**Deliverable:** `lim(sin(x)/x, x, 0)` → `1`, `lim((x^2-1)/(x-1), x, 1)` → `2` ✅

### Phase 7 — Symbolic Integration (Weeks 29–34) ✅ COMPLETE

- [x] Table-based integration (power, trig, exp, ln)
- [x] Linearity: `int(a*f + b*g) = a*int(f) + b*int(g)`
- [x] Substitution (linear: sin(a*x), cos(a*x), exp(a*x))
- [x] Definite integrals: `int(expr, var, a, b)`
- [ ] Partial fraction decomposition: `apart(expr, var)` (deferred)
- [ ] Integration by parts (deferred)

**Deliverable:** `int(x^2, x)` → `(1/3)*x^3`, `int(sin(x), x, 0, pi)` → `2` ✅

### Phase 8 — Matrices & Vectors (Weeks 35–40) ✅ COMPLETE

- [x] Matrix literal syntax: `[[1,0],[0,1]]`
- [x] Vector syntax: `[a, b, c]`
- [x] Matrix operations: addition, scalar multiplication, matrix multiplication
- [x] Dot product: `dot([a,b,c], [d,e,f])`
- [x] Cross product: `cross([a,b,c], [d,e,f])`
- [x] Determinant: `det([[a,b],[c,d]])`
- [x] Transpose: `transpose(M)`
- [x] Inverse (2×2)
- [ ] Eigenvalues (deferred)

**Deliverable:** `det([[1,2],[3,4]])` → `-2`, `dot([1,2,3],[4,5,6])` → `32` ✅

### Phase 9 — Equation Solving (Weeks 41–46) ✅ COMPLETE

- [x] Linear equations: `solve(a*x + b = 0, x)`
- [x] Quadratic equations: `solve(a*x^2 + b*x + c = 0, x)`
- [x] Cubic/quartic/higher via Rational Root Theorem + synthetic division
- [x] `factor(expr, var)` — polynomial factorization via root-finding (any degree)
- [x] Systems of linear equations: `solve(eq1, eq2, x, y)` (Gaussian elimination)
- [x] Inequality solving (linear): `solve(2*x + 1 > 0, x)` → `x > -1/2`

**Deliverable:** `solve(x^3 - 6*x^2 + 11*x - 6 = 0, x)` → `{1, 3, 2}`, `solve(x + y = 5, x - y = 1, x, y)` → `{x = 3, y = 2}` ✅

### Phase 10 — Pattern Matching & Rewrite Engine (Weeks 47–52) ✅ COMPLETE

- [x] Pattern language: wildcards (`_x`, `_y` — any symbol starting with `_`)
- [x] Rule definition: `rule(pattern, replacement)`
- [x] User-defined simplification rules (applied automatically)
- [x] Commutative matching (ADD/MUL match in any order)
- [x] Recursive application (matches at any depth in expression tree)
- [x] `rules()` — list all defined rules
- [ ] Configurable Pratt parser (deferred — current system sufficient)

**Deliverable:** `rule(sin(_x)^2 + cos(_x)^2, 1)` then `sin(a)^2 + cos(a)^2` → `1` ✅

### Phase 11 — Advanced Calculus ✅ COMPLETE

- [x] Higher-order: `diff(f, x, 2)` for d²f/dx²
- [x] Taylor/Maclaurin series: `taylor(expr, var, point, order)`
- [x] Trigonometric simplification: `trigsimp(expr)`
- [x] Partial derivatives: `diff(f, x, y)` for mixed partials
- [x] Gradient: `grad(f, x, y, z)` → vector of partial derivatives
- [x] Divergence: `div([Fx, Fy, Fz], x, y, z)` → scalar
- [x] Curl: `curl([Fx, Fy, Fz], x, y, z)` → vector
- [ ] Differential equations (deferred — requires dedicated solver architecture)

**Deliverable:** `taylor(sin(x), x, 0, 5)` → `x + (-1/6)*x^3 + (1/120)*x^5`, `grad(x^2+y^2+z^2, x, y, z)` → `[2*x, 2*y, 2*z]` ✅

### Phase 12 — Number Theory & Discrete Math ✅ COMPLETE

- [x] Integer factorization: `factorize(360)` → `2^3 * 3^2 * 5`
- [x] GCD, LCM: `gcd(48, 18)` → `6`, `lcm(12, 8)` → `24`
- [x] Modular arithmetic: `mod(17, 5)` → `2`, `powmod(2, 10, 1000)` → `24`
- [x] Binomial coefficients: `binom(10, 3)` → `120`
- [x] Combinatorial functions: `perm(5, 3)` → `60`

**Deliverable:** `binom(10, 3)` → `120`, `gcd(48, 18)` → `6`, `factorize(360)` → `2^3 * 3^2 * 5` ✅

---

### Phase 13 — Meta-Rule Engine & Bidirectional Rewriting (Partial ✅ / Future)

**Implemented:**
- [x] Rest-matching: `_rest` wildcard matches remaining children in ADD/MUL
- [x] Typed wildcards: `_n__num` matches only numbers, `_f__func` matches only functions
- [x] Pattern simplification: patterns are flattened before storage
- [x] Subset matching in commutative operations (1 or 2 fixed + rest)

**Remaining (future):**
- [ ] Recursive markers in replacement (`diff(_f)` triggers recursion)
- [ ] Recognition functions (binomial pattern detection)
- [ ] Strategy engine (direction tags, "simplify = try both, pick shorter")
- [ ] Bidirectional rules

This phase addresses the fundamental limitation of simple pattern→replacement rules:
some mathematical transformations are **bidirectional**, **context-dependent**, or
require **non-trivial recognition**.

#### The Problem: Bidirectional Rules

The binomial theorem works in BOTH directions:

```
Forward (expand):   (a + b)^n  →  Σ binom(n,k) * a^k * b^(n-k)
Backward (factor):  a^2 + 2*a*b + b^2  →  (a + b)^2
```

The forward direction is straightforward expansion. The backward direction requires
**recognizing** that a sum of terms happens to match the binomial pattern — this is
pattern recognition on a variable-length sum where terms may be in any order.

#### Other Bidirectional Examples

| Forward | Backward | Difficulty |
|---------|----------|-----------|
| `(a+b)^2 → a²+2ab+b²` | `a²+2ab+b² → (a+b)^2` | Must recognize coefficients match binomial |
| `sin(a+b) → sin(a)cos(b)+cos(a)sin(b)` | Reverse: recognize sum-product pattern | Must match across multiple terms |
| `ln(a*b) → ln(a)+ln(b)` | `ln(a)+ln(b) → ln(a*b)` | Easy forward, backward needs grouping |
| `a*(b+c) → a*b+a*c` | `a*b+a*c → a*(b+c)` | Backward = factoring common terms |

#### Why Simple Rewrite Rules Can't Handle This

1. **Variable-length matching:** `a²+2ab+b²` has 3 terms, but `(a+b)^3` expansion has 4 terms. The pattern length depends on the exponent.

2. **Coefficient verification:** To recognize `x²+6x+9` as `(x+3)²`, you must verify that `6 = 2*1*3` and `9 = 3²`. This is arithmetic, not pattern matching.

3. **Ambiguity:** `x²+5x+6` could be `(x+2)(x+3)` but NOT `(x+a)²` for any `a`. The system must try multiple factoring strategies.

4. **Direction choice:** Given `a²+2ab+b²`, should the system factor it? Only if the user asks (or if it leads to simplification). Automatic bidirectional rewriting can loop.

#### Proposed Implementation Architecture

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Simple Rewrite Rules (current)        │
│  Pattern → Replacement (unidirectional)         │
│  sin(0) → 0, exp(ln(x)) → x                   │
└─────────────────────────────────────────────────┘
         │
┌─────────────────────────────────────────────────┐
│  Layer 2: Structural Meta-Rules                 │
│  Recursive patterns with typed wildcards        │
│  diff(_f + _g) → diff(_f) + diff(_g)           │
│  Requires: rest-matching, recursion markers     │
└─────────────────────────────────────────────────┘
         │
┌─────────────────────────────────────────────────┐
│  Layer 3: Recognition Rules (backward)          │
│  Algorithmic pattern detectors                  │
│  "Does this sum match a binomial expansion?"    │
│  "Can these terms be factored?"                 │
│  Requires: hypothesis testing, verification     │
└─────────────────────────────────────────────────┘
         │
┌─────────────────────────────────────────────────┐
│  Layer 4: Strategy Engine                       │
│  Decides WHEN to apply which direction          │
│  "User asked to factor" → try Layer 3           │
│  "User asked to expand" → try Layer 1 forward   │
│  "Simplify" → try both, pick shorter result     │
└─────────────────────────────────────────────────┘
```

#### Layer 3: How Recognition Rules Would Work

Unlike simple pattern matching (which walks one tree), recognition requires **hypothesis generation and verification**:

```
recognize_binomial_square(expr):
  1. Check: is expr an ADD with 3 terms?
  2. Find the two "square" terms: a² and b²
     - For each term, check if it's X^2 for some X
  3. Extract a and b from the squares
  4. Verify: does the remaining term equal 2*a*b?
  5. If yes: return (a + b)^2
  6. If no: try (a - b)^2 (check if remaining = -2*a*b)
```

This is NOT pattern matching — it's a **verification algorithm**. Each recognition rule is a small function that:
- Generates a hypothesis ("maybe this is (a+b)²")
- Extracts parameters (a, b)
- Verifies the hypothesis (check middle term = 2ab)

#### Layer 4: The Strategy Problem

The hardest part: **when** to apply which direction.

```
Input: x^2 + 2*x + 1

Without context:
  - Could stay as-is (already simplified)
  - Could factor to (x+1)^2
  - Both are valid "simplified" forms

With context:
  - "factor(...)" → try backward rules → (x+1)^2
  - "expand(...)" → try forward rules → stays as-is
  - "simplify(...)" → pick shorter? pick canonical? user preference?
```

**Proposed solution:** Rules are tagged with a **direction**:

```cpp
struct MetaRule {
    std::string name;
    Direction direction;  // FORWARD, BACKWARD, BOTH
    // FORWARD: applied during expand()
    // BACKWARD: applied during factor()/collect()
    // BOTH: applied during simplify() if result is "simpler"
};
```

#### Implementation Roadmap for Phase 13

- [x] Typed wildcards: `_n__num`, `_c__const`, `_v__hasvar`, `_s__sym`, `_f__func`
- [x] Rest-matching: `_rest` matches remaining children in ADD/MUL
- [ ] Recursive markers: `diff(_f)` in replacement triggers recursion (deferred to Phase 14)
- [x] Recognition functions: register C++ functions as "backward rules"
- [x] Binomial recognition: detect `(a+b)^n` patterns (n=2, n=3)
- [x] Common-factor recognition: detect `a*X + b*X` → `(a+b)*X`
- [x] Strategy engine: `simplify_smart()` tries both directions, picks shorter result
- [ ] User-definable bidirectional rules

**Estimated effort:** 4–8 weeks (research-level complexity)

**Key insight:** This is where a CAS transitions from "collection of algorithms" to
"intelligent mathematical reasoning." Most open-source CAS (Maxima, SymPy) solve this
with hundreds of hand-written heuristics. A clean data-driven approach would be novel.

---

### Phase 14 — Rule-Driven Architecture Refactor

**Goal:** Transform Axion from a "collection of algorithms with some rules" into a
"rule engine with algorithmic helpers." All mathematical knowledge should be expressed
as data (rules/tables) wherever possible, with procedural code only for structural
algorithms that cannot be expressed declaratively.

#### 14.1 Motivation

Currently, mathematical knowledge is scattered across the codebase in three forms:

| Form | Location | Example |
|------|----------|---------|
| Hardcoded `if` chains | `simplify.cpp` | `sin(0)→0`, constant folding |
| Rule tables (data) | `rules.cpp` | diff/int tables, identity rules |
| Procedural algorithms | `calculus.cpp`, `solver.cpp` | product rule, Gaussian elimination |

The first form should be eliminated entirely — all leaf-level transformations should
be data. The second form should be expanded. The third form stays (algorithms are
inherently procedural), but should be minimized.

#### 14.2 Design: Phased Rule Application (inspired by math.js)

math.js organizes simplification into **ordered rule groups** that run sequentially:

```
Phase 1: STRUCTURE   — flatten, canonicalize (algorithmic, stays as code)
Phase 2: FOLD        — constant arithmetic (rule: _c1 + _c2 → eval)
Phase 3: COMBINE     — like-term grouping (algorithmic, stays as code)
Phase 4: IDENTITY    — mathematical identities (rules: sin²+cos²→1, exp(ln(x))→x)
Phase 5: DOMAIN      — domain-specific (rules: log(a)+log(b)→log(ab))
```

Each phase runs to fixpoint before the next starts. This prevents rules from
fighting each other (e.g., an identity rule undoing a combination).

**Axion mapping:**

| Phase | Current implementation | Target |
|-------|----------------------|--------|
| STRUCTURE | `simplify()` — flatten, sort | Keep as code |
| FOLD | `simplify()` — constant arithmetic in ADD/MUL | Keep as code (performance-critical) |
| COMBINE | `simplify()` — like-term, like-base | Keep as code |
| IDENTITY | `rules.cpp` identity table | ✅ Already data-driven |
| DOMAIN | Scattered in modules | Move to rule tables |

#### 14.3 Deliverables

##### 14.3.1 Extended Wildcard Types

Add context-aware wildcard constraints to the pattern engine:

| Wildcard | Matches | Use case |
|----------|---------|----------|
| `_x` | Any expression | General (existing) |
| `_n__num` | Numeric literal only | Existing |
| `_s__sym` | Symbol only | Existing |
| `_f__func` | Function call only | Existing |
| `_c__const` | Expression free of active variable | `∫ _c*f(x) dx → _c * ∫ f(x) dx` |
| `_v__hasvar` | Expression containing active variable | Distinguish variable-dependent terms |
| `_nz__nonzero` | Numeric, not zero | Safe division rules |
| `_pos__pos` | Numeric, positive | `sqrt(_pos^2) → _pos` |

Implementation: extend `check_type_constraint()` in `rewrite.cpp`. The `_c__const`
and `_v__hasvar` types require a **context variable** passed to the matcher:

```cpp
struct MatchContext {
    std::string active_var;  // the variable of interest (e.g., "x" for integration)
};

bool check_type_constraint(const Expr* expr, const std::string& type, const MatchContext& ctx);
```

##### 14.3.2 Rule-Driven Integration

Replace the procedural `if` chains in `integration.cpp` with declarative rules:

```cpp
// Current (procedural):
if (is_var(e, var))
    return make_mul(arena, {make_num(arena, 1, 2), make_pow(arena, make_sym(arena, var), make_num(arena, 2))});

// Target (declarative):
IntegrationRule rules[] = {
    { "_x",           "(1/2)*_x^2" },           // ∫x dx
    { "_x^_n__num",   "_x^(_n+1) / (_n+1)" },  // ∫x^n dx (n≠-1)
    { "_c__const * _f__hasvar", "_c * int(_f)" }, // linearity
    { "sin(_x)",      "-cos(_x)" },              // table
    { "cos(_x)",      "sin(_x)" },               // table
    { "exp(_x)",      "exp(_x)" },               // table
};
```

Challenge: the replacement `_x^(_n+1) / (_n+1)` requires **arithmetic on bound
metavariables** during substitution. This needs a `compute_binding()` step:

```cpp
// After matching, before substitution:
// If replacement contains _n+1, compute it from the bound value of _n
bindings["_n+1"] = simplify(arena, make_add(arena, {bindings["_n"], make_num(arena, 1)}));
```

##### 14.3.3 Rule-Driven Differentiation (Structural Rules)

Express the structural differentiation rules as data:

```cpp
struct DiffStructuralRule {
    NodeType node_type;          // ADD, MUL, POW, NEG
    std::string pattern;         // structural pattern
    std::string replacement;     // with diff() markers for recursion
};

DiffStructuralRule structural_diff_rules[] = {
    { NodeType::ADD, "_a + _b",     "diff(_a) + diff(_b)" },
    { NodeType::NEG, "-_a",         "-diff(_a)" },
    // MUL and POW are algorithmic (n-ary product rule, general power rule)
};
```

The `diff()` markers in the replacement trigger recursive differentiation.
This is a **meta-rule** — the replacement is not a simple substitution but
invokes the differentiation engine recursively.

Note: The n-ary product rule and general `f^g` rule remain procedural because
they iterate over children in ways that flat patterns cannot express.

##### 14.3.4 Simplification Rule Audit

Audit `simplify.cpp` and extract any remaining leaf-level transformations into
the rule table. After this phase, `simplify()` should contain ONLY:

1. Recursive child simplification
2. Flattening (structural)
3. Canonical sorting (structural)
4. Constant folding (arithmetic — could be a rule but kept for performance)
5. Like-term combination (algorithmic grouping)
6. Like-base power collection (algorithmic grouping)
7. Computational function evaluation (sin(0)→0, etc. — trivial, kept for performance)

Everything else moves to the identity rule table.

##### 14.3.5 Rule File Format (Optional)

Allow rules to be loaded from an external file rather than hardcoded in C++:

```
# rules/identities.rules
# Format: pattern → replacement [; condition]

exp(ln(_x))         → _x
ln(exp(_x))         → _x
sin(_x)^2+cos(_x)^2 → 1
ln(_x)+ln(_y)       → ln(_x*_y)
_n__num*ln(_x)      → ln(_x^_n__num)

# Differentiation rules (function table)
@diff sin(_u)       → cos(_u)
@diff cos(_u)       → -sin(_u)
@diff exp(_u)       → exp(_u)
@diff ln(_u)        → _u^(-1)
@diff tan(_u)       → cos(_u)^(-2)

# Integration rules (function table)
@int sin(_u)        → -cos(_u)
@int cos(_u)        → sin(_u)
@int exp(_u)        → exp(_u)
```

This separates mathematical knowledge from C++ code entirely. Rules can be
edited, extended, or swapped without recompilation.

#### 14.4 What Stays Procedural (Non-Goals)

These algorithms are inherently iterative/recursive and should NOT be converted
to flat rewrite rules:

| Algorithm | Why it stays as code |
|-----------|---------------------|
| N-ary product rule | Iterates over N children, differentiating one at a time |
| Like-term combination | Groups by key, sums coefficients — map-reduce pattern |
| Canonical sorting | Comparison-based sort |
| Gaussian elimination | Row operations on augmented matrix |
| Rational Root Theorem | Trial division loop |
| L'Hôpital iteration | Recursive with depth limit and 0/0 detection |
| Taylor series | Loop: differentiate, evaluate, accumulate |
| Cofactor expansion | Recursive matrix decomposition |
| Polynomial long division | Iterative degree reduction |

#### 14.5 Architecture After Refactor

```
┌─────────────────────────────────────────────────────────┐
│                    Rule Database                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Identities  │  │  Diff Table  │  │  Int Table   │  │
│  │  (pattern →  │  │  (func →     │  │  (func →     │  │
│  │   replace)   │  │   deriv)     │  │   antideriv) │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  Domain Rules│  │  User Rules  │                     │
│  │  (log, trig) │  │  (REPL)      │                     │
│  └──────────────┘  └──────────────┘                     │
└────────────────────────┬────────────────────────────────┘
                         │ read
┌────────────────────────▼────────────────────────────────┐
│              Rewrite Engine (single engine)               │
│                                                          │
│  pattern_match() → apply_bindings() → simplify()         │
│  Supports: wildcards, typed constraints, _rest,          │
│            context variable, arithmetic in bindings       │
└────────────────────────┬────────────────────────────────┘
                         │ used by
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  simplify()  │ │differentiate()│ │  integrate() │
│              │ │              │ │              │
│ Algorithmic: │ │ Structural:  │ │ Structural:  │
│ - flatten    │ │ - sum rule   │ │ - linearity  │
│ - sort       │ │ - product    │ │ - const pull │
│ - combine    │ │ - chain rule │ │              │
│ - fold       │ │              │ │ Leaf lookup: │
│              │ │ Leaf lookup: │ │ - int table  │
│ Then apply:  │ │ - diff table │ │              │
│ - identities │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

#### 14.6 Success Criteria

After this phase:

1. `rules.cpp` contains ALL mathematical knowledge as data tables
2. `simplify.cpp` contains ONLY structural algorithms (flatten, sort, combine, fold)
3. `calculus.cpp` contains ONLY the recursive structure (sum/product/chain rule dispatch)
4. `integration.cpp` contains ONLY linearity + constant extraction logic
5. Adding a new function (e.g., `sinh`) requires ONLY adding entries to the rule tables — zero changes to algorithmic code
6. A new identity (e.g., `cosh²-sinh²=1`) requires ONLY adding one line to the identity table

**Test:** Add `sinh`, `cosh`, `tanh` support by ONLY editing `rules.cpp`. If any
`.cpp` file other than `rules.cpp` needs changes, the architecture is not yet
sufficiently data-driven.

#### 14.7 Implementation Order

1. Extended wildcard types (`_c__const`, `_v__hasvar`) — ✅ Done in Phase 13
2. Arithmetic in bindings — ✅ Works naturally via simplify() after substitution
3. Migrate integration leaf rules to table format — ✅ Already table-driven
4. Migrate remaining simplify leaf rules to table — ✅ Done (func_eval, func_sym tables)
5. External rule file parser — ✅ `load("path")` command
6. Validation: add `sinh`/`cosh`/`tanh` by editing only `rules.cpp` — ✅ Verified
7. Validation: add `cot` by editing only `rules.cpp` — ✅ Verified
8. Validation: add `sec`/`csc` via external rule file — ✅ Verified

**Estimated effort:** 3–5 weeks

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
