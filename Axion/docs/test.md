# Test Record

---

## Phase 1 — MVP

### How to Build and Run Tests

```bash
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"
cd "$AXION_ROOT"
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
cd build && ctest --output-on-failure
```

### Test Results Summary

- **22 tests, 22 passed, 0 failed**
- Execution time: <0.01s

---

### Lexer Tests (3/3 passed)

| Test | Input | Checks | Verdict |
|------|-------|--------|---------|
| BasicTokens | `2*x + 3` | 6 tokens: NUMBER(2), STAR, SYMBOL(x), PLUS, NUMBER(3), END | ✅ Pass |
| FunctionToken | `sin(x)` | SYMBOL("sin"), LPAREN | ✅ Pass |
| PowerAndParens | `x^2 + (y - 1)` | SYMBOL, CARET, NUMBER, PLUS, LPAREN | ✅ Pass |

---

### Parser Tests (6/6 passed)

| Test | Input | Expected | Verdict |
|------|-------|----------|---------|
| SimpleAdd | `x + y` | type=ADD, 2 children | ✅ Pass |
| Precedence | `2 + 3*x` | ADD(2, MUL(3,x)) | ✅ Pass |
| Power | `x^2` | POW(SYM("x"), NUM(2)) | ✅ Pass |
| Function | `sin(x)` | FUNC("sin") | ✅ Pass |
| UnaryMinus | `-x` | NEG | ✅ Pass |
| ComplexExpr | `2*x^2 + 3*x + 1` | type=ADD | ✅ Pass |

---

### Simplification Tests (8/8 passed)

| Test | Input | Expected Output | Actual Output | Verdict |
|------|-------|-----------------|---------------|---------|
| AddZero | `x + 0` | `x` | `x` | ✅ Pass |
| MulOne | `x * 1` | `x` | `x` | ✅ Pass |
| MulZero | `x * 0` | `0` | `0` | ✅ Pass |
| ConstantFold | `2 + 3` | `5` | `5` | ✅ Pass |
| ConstantFold | `2 * 3` | `6` | `6` | ✅ Pass |
| CombineLikeTerms | `x + x` | `2*x` | `2*x` | ✅ Pass |
| CombineLikeTerms | `2*x + 3*x` | `5*x` | `5*x` | ✅ Pass |
| PowerRules | `x^0` | `1` | `1` | ✅ Pass |
| PowerRules | `x^1` | `x` | `x` | ✅ Pass |
| PowerRules | `2^3` | `8` | `8` | ✅ Pass |
| DoubleNeg | `--x` | `x` | `x` | ✅ Pass |
| SubtractSelf | `x - x` | `0` | `0` | ✅ Pass |

---

### Evaluation Tests (5/5 passed)

| Test | Input | Env | Expected | Actual | Verdict |
|------|-------|-----|----------|--------|---------|
| SimpleNum | `42` | {} | 42.0 | 42.0 | ✅ Pass |
| Variable | `x + 1` | x=2 | 3.0 | 3.0 | ✅ Pass |
| Polynomial | `x^2 + 2*x + 1` | x=3 | 16.0 | 16.0 | ✅ Pass |
| Function | `sin(0)` | {} | 0.0 | 0.0 | ✅ Pass |
| UndefinedVar | `x + y` | x=1 | throws | throws | ✅ Pass |

---

### Issues Found

None. All tests passed on first run after fixing one build warning (unused `prec_of` function removed from printer.cpp).

---

## Phase 2 — Calculus

### Regression Test

All 22 Phase 1 tests: ✅ Pass (no regressions)

### New Calculus Tests (12/12 passed)

| Test | Input | Var | Expected | Actual | Verdict |
|------|-------|-----|----------|--------|---------|
| ConstantDerivative | `5` | x | `0` | `0` | ✅ Pass |
| VariableDerivative | `x` | x | `1` | `1` | ✅ Pass |
| OtherVariable | `y` | x | `0` | `0` | ✅ Pass |
| LinearTerm | `3*x` | x | `3` | `3` | ✅ Pass |
| PowerRule | `x^3` | x | `3*x^2` | `3*x^2` | ✅ Pass |
| SumRule | `x^2 + x` | x | `1 + 2*x` | `1 + 2*x` | ✅ Pass |
| ProductRule | `x*x` | x | `2*x` | `2*x` | ✅ Pass |
| SinDerivative | `sin(x)` | x | `cos(x)` | `cos(x)` | ✅ Pass |
| CosDerivative | `cos(x)` | x | `-sin(x)` | `-sin(x)` | ✅ Pass |
| ChainRule | `sin(x^2)` | x | `2*x*cos(x^2)` | `2*x*cos(x^2)` | ✅ Pass |
| ExpDerivative | `exp(x)` | x | `exp(x)` | `exp(x)` | ✅ Pass |
| LnDerivative | `ln(x)` | x | `x^-1` | `x^-1` | ✅ Pass |

### Issues Found

1. **Initial failure: `CosDerivative` produced `-1*sin(x)` instead of `-sin(x)`**
   - Root cause: MUL simplifier did not convert `MUL(-1, f)` to `NEG(f)`
   - Fix: Added check in MUL simplification to emit NEG when coefficient is -1
   - After fix: all tests pass

2. **Initial failure: `SumRule` produced `1 + 2*x` — test expected `2*x + 1`**
   - Root cause: canonical ordering sorts numbers before symbols (correct behavior)
   - Fix: Updated test expectation to match canonical output
   - Not a bug — correct behavior

---

## Phase 3 — Algebra

### Regression Test

All 34 Phase 1+2 tests: ✅ Pass (no regressions)

### New Polynomial Tests (6/6 passed)

| Test | Input | Verification | Verdict |
|------|-------|-------------|---------|
| ExpandSimpleProduct | `(x+1)*(x+2)` | eval at x=5 → 42 | ✅ Pass |
| ExpandSquare | `(x+1)^2` | eval at x=3 → 16 | ✅ Pass |
| ExpandCube | `(x+1)^3` | eval at x=2 → 27 | ✅ Pass |
| ExpandDiffOfSquares | `(x+1)*(x-1)` | eval at x=4 → 15 | ✅ Pass |
| ExpandMultivar | `(x+y)*(x-y)` | eval at x=3,y=2 → 5 | ✅ Pass |
| NoExpansionNeeded | `x^2 + 1` | output = `1 + x^2` | ✅ Pass |

### Issues Found

1. **`(x+1)^3` gave wrong numeric result (21 instead of 27)**
   - Root cause: `expand` reused same base pointer; `simplify` mutated shared nodes
   - Fix: deep-copy base before each multiplication
   - Lesson: immutable AST requires explicit copying when reusing subtrees

2. **`MUL(2, x, x)` lost during like-term combination**
   - Root cause: `extract_coeff` returned nullptr base for 3+ child MUL nodes
   - Fix: strip numeric child and return remaining MUL as base
   - Lesson: coefficient extraction must handle all MUL arities

---

## Phase 4 — Extended Operators & Relations

### Regression Test

All 40 Phase 1–3 tests rewritten for new rational AST: ✅ Pass (no regressions)

### New Tests (6 additional, 46 total)

| Test | Input | Expected | Actual | Verdict |
|------|-------|----------|--------|---------|
| Lexer.Factorial | `5!` | BANG token | BANG token | ✅ Pass |
| Lexer.Relational | `x <= 3` | LEQ token | LEQ token | ✅ Pass |
| Lexer.Assignment | `a := 5` | ASSIGN token | ASSIGN token | ✅ Pass |
| Lexer.Subscript | `x_1 + x_(12)` | "x_1", "x_(12)" | "x_1", "x_(12)" | ✅ Pass |
| Parser.Factorial | `5!` | FACTORIAL node | FACTORIAL node | ✅ Pass |
| Parser.Relational | `x = 3` | REL("=") node | REL("=") node | ✅ Pass |
| Parser.MultiArgFunc | `diff(x^2, x)` | FUNC, 2 children | FUNC, 2 children | ✅ Pass |
| Simplify.Factorial | `5!` → `120`, `0!` → `1` | 120, 1 | 120, 1 | ✅ Pass |
| Simplify.RationalAdd | `1/3 + 1/6` → `1/2` | `1/2` | `1/2` | ✅ Pass |
| Simplify.RationalMul | `(2/3) * (3/4)` → `1/2` | `1/2` | `1/2` | ✅ Pass |
| Eval.Factorial | `5!` → 120.0 | 120.0 | 120.0 | ✅ Pass |
| Eval.Rational | `1/3 + 1/6` → 0.5 | 0.5 | 0.5 | ✅ Pass |

### Issues Found

None.


---

## Phase 5 — Summation & Product

### Regression Test

All 46 Phase 1–4 tests: ✅ Pass (no regressions)

### New Series Tests (6/6 passed)

| Test | Input | Expected | Actual | Verdict |
|------|-------|----------|--------|---------|
| SumIntegers | `sum(k, k, 1, 10)` | 55 | 55 | ✅ Pass |
| SumSquares | `sum(k^2, k, 1, 5)` | 55 | 55 | ✅ Pass |
| SumConstant | `sum(3, k, 1, 4)` | 12 | 12 | ✅ Pass |
| ProdIntegers | `prod(k, k, 1, 5)` | 120 | 120 | ✅ Pass |
| ProdExpression | `prod(k+1, k, 0, 3)` | 24 | 24 | ✅ Pass |
| CollectSimple | `collect(x^2+2*x+3*x, x)` at x=2 | 14 | 14 | ✅ Pass |

### Issues Found

None.


---

## Phase 6 — Limits

### Regression Test

All 52 Phase 1–5 tests: ✅ Pass (no regressions)

### Limits Verification (manual REPL tests)

| Input | Expected | Actual | Method | Verdict |
|-------|----------|--------|--------|---------|
| `lim(x^2, x, 3)` | 9 | 9 | Direct substitution | ✅ |
| `lim((x^2-1)/(x-1), x, 1)` | 2 | 2 | L'Hôpital (0/0) | ✅ |
| `lim(sin(x)/x, x, 0)` | 1 | 1 | L'Hôpital (0/0) | ✅ |
| `lim((x^3-8)/(x-2), x, 2)` | 12 | 12 | L'Hôpital (0/0) | ✅ |
| `lim(x+1, x, 5)` | 6 | 6 | Direct substitution | ✅ |


---

## Phase 7 — Symbolic Integration

### Regression Test

All 52 Phase 1–6 tests: ✅ Pass (no regressions)

### Integration Verification (manual REPL tests)

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `int(x^2, x)` | `(1/3)*x^3` | `(1/3)*x^3` | ✅ |
| `int(x^3, x)` | `(1/4)*x^4` | `(1/4)*x^4` | ✅ |
| `int(sin(x), x)` | `-cos(x)` | `-cos(x)` | ✅ |
| `int(cos(x), x)` | `sin(x)` | `sin(x)` | ✅ |
| `int(exp(x), x)` | `exp(x)` | `exp(x)` | ✅ |
| `int(1/x, x)` | `ln(abs(x))` | `ln(abs(x))` | ✅ |
| `int(3*x^2 + 2*x, x)` | `x^3 + x^2` | `x^3 + x^2` | ✅ |
| `int(x^2, x, 0, 1)` | `1/3` | `1/3` | ✅ |
| `int(sin(x), x, 0, pi)` | `2` | `2` | ✅ |
| `int(cos(x), x, 0, pi)` | `0` | `0` | ✅ |

### Issues Found

1. **`int(sin(x), x, 0, pi)` initially returned `1 - cos(pi)` instead of `2`**
   - Cause: `cos(pi)` did not simplify to `-1`
   - Fix: Added `cos(pi)→-1`, `sin(pi)→0`, `cos(n*pi)→(-1)^n`, `sin(n*pi)→0` rules


---

## Phase 9 — Equation Solving (extended)

### Additional Tests (higher degree)

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `solve(x^3 - 6*x^2 + 11*x - 6 = 0, x)` | {1, 2, 3} | {1, 3, 2} | ✅ |
| `solve(x^3 - 1 = 0, x)` | 1 | 1 | ✅ |
| `solve(x^4 - 5*x^2 + 4 = 0, x)` | {±1, ±2} | {1, 2, -1, -2} | ✅ |
| `factor(x^3 - 6*x^2 + 11*x - 6, x)` | (x-1)(x-2)(x-3) | (-1+x)(-3+x)(-2+x) | ✅ |
| `factor(x^4 - 5*x^2 + 4, x)` | 4 factors | 4 factors | ✅ |


### Systems & Inequalities

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `solve(2*x + 1 > 0, x)` | x > -1/2 | x > -1/2 | ✅ |
| `solve(3*x - 6 <= 0, x)` | x <= 2 | x <= 2 | ✅ |
| `solve(-x + 5 > 0, x)` | x < 5 | x < 5 | ✅ |
| `solve(x + y = 5, x - y = 1, x, y)` | {x=3, y=2} | {x=3, y=2} | ✅ |


---

## Phase 11 — Advanced Calculus

### Regression Test

All 52 Phase 1–10 tests: ✅ Pass (no regressions)

### Phase 11 Verification

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `taylor(sin(x), x, 0, 5)` | x - x³/6 + x⁵/120 | `x + (-1/6)*x^3 + (1/120)*x^5` | ✅ |
| `taylor(exp(x), x, 0, 4)` | 1+x+x²/2+x³/6+x⁴/24 | `1 + x + (1/2)*x^2 + (1/6)*x^3 + (1/24)*x^4` | ✅ |
| `taylor(cos(x), x, 0, 4)` | 1-x²/2+x⁴/24 | `1 + (-1/2)*x^2 + (1/24)*x^4` | ✅ |
| `diff(x^5, x, 3)` | 60x² | `60*x^2` | ✅ |
| `diff(x^2*y, x, 2)` | 2y | `2*y` | ✅ |
| `trigsimp(sin(t)^2 + cos(t)^2)` | 1 | `1` | ✅ |

### Issues Found

1. **Taylor initially returned `0` for `sin(x)` at x=0**
   - Cause: `substitute` function mutated the tree in place, corrupting the body for subsequent derivatives
   - Fix: use deep-copy lambda before substitution to avoid aliasing


---

## Phase 12 — Number Theory & Discrete Math

### Regression Test

All 52 Phase 1–11 tests: ✅ Pass (no regressions)

### Phase 12 Verification

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `gcd(48, 18)` | 6 | 6 | ✅ |
| `lcm(12, 8)` | 24 | 24 | ✅ |
| `binom(10, 3)` | 120 | 120 | ✅ |
| `binom(5, 2)` | 10 | 10 | ✅ |
| `perm(5, 3)` | 60 | 60 | ✅ |
| `mod(17, 5)` | 2 | 2 | ✅ |
| `powmod(2, 10, 1000)` | 24 | 24 | ✅ |
| `factorize(360)` | 2^3 * 3^2 * 5 | 2^3 * 3^2 * 5 | ✅ |
| `factorize(97)` | 97 (prime) | 97 | ✅ |

### Issues Found

None.


---

## Phase 13 — Meta-Rule Engine (Complete)

### Regression Test

All 52 Phase 1–12 tests: ✅ Pass (no regressions)

### Phase 13 Verification

#### Context-aware wildcards

| Feature | Test | Verdict |
|---------|------|---------|
| `_c__const` | Matches expressions free of active variable | ✅ Implemented |
| `_v__hasvar` | Matches expressions containing active variable | ✅ Implemented |
| `MatchContext` | Overloaded `pattern_match` with context | ✅ Implemented |

#### Recognition functions

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `factor(a^2 + 2*a*b + b^2, a)` | `(a + b)^2` | `(a + b)^2` | ✅ |
| `factor(a^2 - 2*a*b + b^2, a)` | `(a - b)^2` | `(a - b)^2` | ✅ |
| `factor(x^2 + 2*x + 1, x)` | `(1 + x)^2` | `(1 + x)^2` | ✅ |
| `factor(x^2 - 2*x + 1, x)` | `(1 - x)^2` | `(1 - x)^2` | ✅ |
| `factor(x^2 + 6*x + 9, x)` | `(3 + x)^2` | `(3 + x)^2` | ✅ |
| `factor(x^2 + 4*x + 4, x)` | `(2 + x)^2` | `(2 + x)^2` | ✅ |
| `factor(x^2 + 2*x*y + y^2, x)` | `(x + y)^2` | `(x + y)^2` | ✅ |
| `factor(x^2 - 1, x)` | `(-1+x)*(1+x)` | `(-1+x)*(1+x)` | ✅ (falls through to root-finding) |

#### Hyperbolic functions (rule-table driven)

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `sinh(0)` | `0` | `0` | ✅ |
| `cosh(0)` | `1` | `1` | ✅ |
| `tanh(0)` | `0` | `0` | ✅ |
| `diff(sinh(x), x)` | `cosh(x)` | `cosh(x)` | ✅ |
| `diff(cosh(x), x)` | `sinh(x)` | `sinh(x)` | ✅ |
| `diff(tanh(x), x)` | `cosh(x)^-2` | `cosh(x)^-2` | ✅ |
| `diff(sinh(x^2), x)` | `2*x*cosh(x^2)` | `2*x*cosh(x^2)` | ✅ |
| `int(sinh(x), x)` | `cosh(x)` | `cosh(x)` | ✅ |
| `int(cosh(x), x)` | `sinh(x)` | `sinh(x)` | ✅ |

#### Rule-driven simplification

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `sin(pi/2)` | `1` | `1` | ✅ |
| `cos(pi/2)` | `0` | `0` | ✅ |
| `exp(ln(x))` | `x` | `x` | ✅ |
| `ln(exp(x))` | `x` | `x` | ✅ |
| `sin(x)^2 + cos(x)^2` | `1` | `1` | ✅ |
| `ln(2) + ln(3)` | `ln(6)` | `ln(6)` | ✅ |
| `2*ln(x)` | `ln(x^2)` | `ln(x^2)` | ✅ |

#### Rest-matching and user rules

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `rule(sin(_x)^2+cos(_x)^2+_rest, 1+_rest)` then `sin(a)^2+cos(a)^2+5` | `6` | `6` | ✅ |
| `rule(log(_x)+log(_y)+_rest, log(_x*_y)+_rest)` then `log(2)+log(3)+log(5)` | `log(30)` | `log(30)` | ✅ |

### Issues Found

None — all features implemented cleanly.


#### Perfect cube recognition

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `x^3 + 3*x^2 + 3*x + 1` | `(1 + x)^3` | `(1 + x)^3` | ✅ |
| `x^3 + 3*x^2*y + 3*x*y^2 + y^3` | `(x + y)^3` | `(x + y)^3` | ✅ |
| `x^3 - 3*x^2 + 3*x - 1` | `(-1 + x)^3` | `(-1 + x)^3` | ✅ |

#### Common-factor recognition

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `x*a + x*b` | `x*(a + b)` | `x*(a + b)` | ✅ |
| `x*a + x*b + x*c` | `x*(a + b + c)` | `x*(a + b + c)` | ✅ |
| `sin(x)*a + sin(x)*b` | `sin(x)*(a + b)` | `sin(x)*(a + b)` | ✅ |

#### Strategy engine (simplify_smart)

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `x^2 + 2*x + 1` (direct input) | `(1 + x)^2` | `(1 + x)^2` | ✅ (auto-factored) |
| `expand((x+1)^2)` | `1 + x^2 + 2*x` | `1 + x^2 + 2*x` | ✅ (stays expanded) |
| `3*x + 5` | `5 + 3*x` | `5 + 3*x` | ✅ (no factoring needed) |
