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
