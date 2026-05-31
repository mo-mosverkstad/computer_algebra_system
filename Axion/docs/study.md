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
| Term canonicalization | 🟡 Medium | 3–4 weeks |
| Pattern-matching rewrite engine | 🟡 Medium | 4–6 weeks |
| Basic factorization | 🟡 Medium | 4–6 weeks |
| General symbolic integration | 🔴 Low (research-level) | months+ |
| General equation solving | 🔴 Low | months+ |

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
enum class NodeType { NUM, SYM, ADD, MUL, POW, FUNC };

struct Expr {
    NodeType type;
    double num_val;              // for NUM
    std::string name;           // for SYM / FUNC
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

Always followed by simplification.

### 4.7 Polynomial Module (`src/modules/polynomial.h`)

Represents polynomials as `map<vector<int>, Rational>` (monomial exponent vector → coefficient).

Operations: add, multiply, expand, collect terms.

### 4.8 Evaluation Engine (`src/engine/eval.h`)

Substitutes numeric values for symbols and computes result:

```cpp
double evaluate(const Expr* e, const std::unordered_map<std::string, double>& env);
```

### 4.9 Pretty Printer (`src/output/printer.h`)

Converts AST back to human-readable string with correct precedence and minimal parentheses.

### 4.10 REPL / CLI Driver (`src/main.cpp`)

Interactive loop using GNU Readline for line editing and history.

Commands:
- Direct expression input → simplify and print
- `diff(expr, x)` → differentiate
- `eval(expr, x=2)` → numeric evaluation
- `expand(expr)` → polynomial expansion
- `quit` / `exit`

---

## 5. Directory Structure

```
Axion/
├── CMakeLists.txt
├── docs/
│   ├── ideas.md
│   ├── study.md
│   └── environment_setup.md
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
│   │   └── polynomial.h / polynomial.cpp
│   └── output/
│       └── printer.h / printer.cpp
└── tests/
    ├── test_lexer.cpp
    ├── test_parser.cpp
    ├── test_simplify.cpp
    ├── test_calculus.cpp
    └── test_eval.cpp
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

### Phase 1 — MVP (Weeks 1–6)

- [x] Project setup (CMake, directory structure)
- [ ] Arena allocator
- [ ] AST definition
- [ ] Lexer
- [ ] Parser (Pratt)
- [ ] Pretty printer
- [ ] Basic simplification (identity rules, constant folding, flattening)
- [ ] Numeric evaluation
- [ ] REPL with readline

**Deliverable:** User types `2*x + 3*x`, gets `5*x`.

### Phase 2 — Calculus (Weeks 7–10)

- [ ] Symbolic differentiation
- [ ] Chain rule, product rule
- [ ] Trigonometric derivatives
- [ ] Post-differentiation simplification

**Deliverable:** `diff(sin(x^2), x)` → `2*x*cos(x^2)`

### Phase 3 — Algebra (Weeks 11–16)

- [ ] Polynomial representation
- [ ] Expand: `(x+1)^3`
- [ ] Collect terms
- [ ] Canonical form improvements
- [ ] Like-term combination for multivariate expressions

**Deliverable:** `expand((x+1)*(x+2))` → `x^2 + 3*x + 2`

### Phase 4 — Advanced (Future)

- [ ] Pattern-matching rewrite engine
- [ ] Basic factorization (GCD-based)
- [ ] Rational expressions
- [ ] Equation solving (linear, quadratic)
- [ ] Limited symbolic integration (table-based)

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
