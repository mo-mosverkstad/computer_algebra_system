# Codebase Analysis

Deep-dive technical reference for the Axion CAS.
Target reader: a complete beginner who has never built a symbolic math system.

---

## Phase 1 — Core Concepts

---

### 1. What Is a Computer Algebra System?

A computer algebra system (CAS) manipulates mathematical expressions **symbolically** — it works with `x + x` as symbols, not numbers. Unlike a calculator that computes `2 + 3 = 5`, a CAS can simplify `x + x` into `2*x` without knowing what `x` is.

The core pipeline:

```
"2*x + 3*x"          (input string)
      │
      ▼ Lexer
[2, *, x, +, 3, *, x] (tokens)
      │
      ▼ Parser
  ADD(MUL(2,x), MUL(3,x))  (tree)
      │
      ▼ Simplifier
  MUL(5, x)           (simplified tree)
      │
      ▼ Printer
"5*x"                 (output string)
```

---

### 2. Arena Allocator (`src/core/arena.h`, `src/core/arena.cpp`)

#### Concept

A CAS creates thousands of small expression nodes during simplification. Using `new`/`delete` for each one is slow and error-prone. An **arena allocator** pre-allocates large memory blocks and hands out pieces sequentially. When done, the entire arena is freed at once.

#### ASCII Diagram

```
Arena:
┌─────────────────────────────────────────────────┐
│ Block 1 (64KB)                                  │
│ [Expr][Expr][Expr][Expr]....[free space]        │
│                             ↑ offset            │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Block 2 (64KB) — allocated when Block 1 is full │
└─────────────────────────────────────────────────┘
```

#### Annotated Code

```cpp
void* Arena::alloc(size_t size, size_t align) {
    // Round offset up to required alignment
    offset_ = (offset_ + align - 1) & ~(align - 1);

    // If this allocation won't fit in current block, allocate a new one
    if (offset_ + size > BLOCK_SIZE) {
        size_t block_size = (size > BLOCK_SIZE) ? size : BLOCK_SIZE;
        blocks_.push_back(std::make_unique<char[]>(block_size));
        offset_ = 0;
    }

    // Hand out pointer at current offset, advance offset
    void* ptr = blocks_.back().get() + offset_;
    offset_ += size;
    return ptr;
}
```

#### Why It Works

Sequential allocation is O(1) — just bump a pointer. No fragmentation. No per-object free. The `create<T>()` template uses placement new to construct objects in arena memory, combining allocation and construction in one call.

---

### 3. Abstract Syntax Tree (`src/core/ast.h`, `src/core/ast.cpp`)

#### Concept

An **AST** (Abstract Syntax Tree) represents the structure of a mathematical expression as a tree. Each node has a type (number, symbol, addition, etc.) and children. The tree captures precedence and grouping without needing parentheses.

#### ASCII Diagram

Expression: `2*x + 3*x`

```
        ADD
       /   \
     MUL   MUL
    / \    / \
   2   x  3   x
```

After simplification: `5*x`

```
    MUL
   / \
  5   x
```

#### Node Types

| Type | Meaning | Children |
|------|---------|----------|
| NUM | Numeric literal (e.g. 42) | none |
| SYM | Variable (e.g. x) | none |
| ADD | Sum | 2+ terms |
| MUL | Product | 2+ factors |
| POW | Power | 2: base, exponent |
| FUNC | Function call (sin, cos...) | 1: argument |
| NEG | Unary negation | 1: operand |

#### Why It Works

N-ary ADD and MUL (variable number of children) make flattening natural: `(a+b)+c` becomes `ADD(a,b,c)` without nested binary nodes. This simplifies like-term combination.

---

### 4. Lexer (`src/frontend/lexer.h`, `src/frontend/lexer.cpp`)

#### Concept

A **lexer** (tokenizer) converts a raw input string into a sequence of meaningful tokens. It handles whitespace, multi-character numbers, multi-character symbol names, and single-character operators.

#### ASCII Diagram

```
Input: "2*x + 3"

Scan:  2  *  x  ' '  +  ' '  3
       │  │  │        │        │
       ▼  ▼  ▼        ▼        ▼
     NUM STAR SYM    PLUS     NUM
```

#### Annotated Code

```cpp
if (std::isdigit(c) || c == '.') {
    size_t start = i;
    // Consume all digits and dots to form a number
    while (i < input.size() && (std::isdigit(input[i]) || input[i] == '.'))
        ++i;
    std::string text = input.substr(start, i - start);
    tokens.push_back({TokenType::NUMBER, text, std::stod(text)});
}
```

#### Why It Works

The lexer is stateless — it scans left to right, greedily consuming characters that belong to the current token type. This is simple, fast, and handles all cases needed for mathematical expressions.

---

### 5. Pratt Parser (`src/frontend/parser.h`, `src/frontend/parser.cpp`)

#### Concept

A **Pratt parser** (top-down operator precedence parser) handles operator precedence and associativity elegantly. Each operator has a "binding power" (precedence number). The parser recursively builds the tree, only consuming operators whose precedence meets the minimum threshold.

#### Precedence Table

| Level | Operators | Associativity |
|-------|-----------|---------------|
| 1 | `+`, `-` | Left |
| 2 | `*`, `/` | Left |
| 3 | unary `-` | Prefix |
| 4 | `^` | Right |

#### ASCII Diagram — Parsing `2 + 3 * x`

```
expr(min_prec=1):
  prefix() → NUM(2)
  peek = '+', prec=1 >= min_prec=1 → consume
    expr(min_prec=2):
      prefix() → NUM(3)
      peek = '*', prec=2 >= min_prec=2 → consume
        expr(min_prec=3):
          prefix() → SYM(x)
          peek = END, prec=0 < 3 → stop
        return SYM(x)
      left = MUL(3, x)
      peek = END, prec=0 < 2 → stop
    return MUL(3, x)
  left = ADD(2, MUL(3, x))
  peek = END, prec=0 < 1 → stop
return ADD(2, MUL(3, x))
```

#### Why It Works

Right-associativity for `^` is achieved by recursing with the same precedence (`expr(prec)`) instead of `expr(prec+1)`. This causes `2^3^4` to parse as `2^(3^4)`. Left-associative operators use `prec+1` to prevent re-consuming at the same level.

---

### 6. Simplification Engine (`src/engine/simplify.h`, `src/engine/simplify.cpp`)

#### Concept

The simplifier transforms an expression tree into a simpler equivalent form by applying algebraic rules bottom-up. It first simplifies all children, then applies rules to the current node.

#### Rules Applied

1. **Identity elimination:** `x+0→x`, `x*1→x`
2. **Annihilation:** `x*0→0`
3. **Power rules:** `x^0→1`, `x^1→x`
4. **Constant folding:** `2+3→5`, `2*3→6`, `2^3→8`
5. **Double negation:** `--x→x`
6. **NEG canonicalization:** `-x` becomes `MUL(-1, x)`
7. **Flattening:** `ADD(a, ADD(b,c))` → `ADD(a,b,c)`
8. **Like-term combination:** `2*x + 3*x` → `5*x`
9. **Canonical sorting:** numbers first, then symbols alphabetically

#### ASCII Diagram — Simplifying `x + x`

```
Input:  ADD(SYM(x), SYM(x))

Step 1: Extract coefficients
  term 1: coeff=1, base=x
  term 2: coeff=1, base=x

Step 2: Group by base key "Sx"
  group: coeff=1+1=2, base=x

Step 3: Rebuild
  MUL(NUM(2), SYM(x))

Output: "2*x"
```

#### Annotated Code (like-term combination)

```cpp
CoeffTerm ct = extract_coeff(t);  // split "3*x" into {coeff=3, base=x}
if (!ct.base) {
    num_sum += ct.coeff;          // pure number: accumulate
} else {
    std::string key = expr_key(ct.base);  // string key for grouping
    for (auto& g : groups) {
        if (expr_key(g.base) == key) {
            g.coeff += ct.coeff;  // same base: sum coefficients
            found = true;
            break;
        }
    }
}
```

#### Why It Works

By converting all terms to `(coefficient, base)` pairs and grouping by base, we naturally combine `2*x + 3*x` into `5*x`. The string-based key comparison is simple and correct for Phase 1; a structural equality check would be more robust for complex expressions (future improvement).

---

### 7. Evaluation Engine (`src/engine/eval.h`, `src/engine/eval.cpp`)

#### Concept

The evaluator substitutes numeric values for variables and computes the result. It recursively walks the tree, looking up each symbol in an environment map.

#### Annotated Code

```cpp
case NodeType::SYM: {
    auto it = env.find(e->name);       // look up variable
    if (it == env.end())
        throw std::runtime_error("Undefined variable: " + e->name);
    return it->second;                 // return its numeric value
}
```

#### Why It Works

Recursive evaluation mirrors the tree structure. Each node type has a clear numeric interpretation: ADD sums children, MUL multiplies them, POW uses `std::pow`, FUNC dispatches to `std::sin`/`std::cos`/etc.

---

### 8. Pretty Printer (`src/output/printer.h`, `src/output/printer.cpp`)

#### Concept

The printer converts an AST back into a human-readable string. It must insert parentheses only where needed (based on precedence context) and display subtraction naturally (`x - y` instead of `x + -1*y`).

#### Key Logic

- NEG children in ADD are printed as `" - X"` instead of `" + -X"`
- MUL children are joined with `*`
- Numbers that are integers are printed without decimal point

#### Why It Works

The `parent_prec` parameter tracks the precedence context. ADD nodes only get parenthesized when inside a higher-precedence context (e.g., as an argument to MUL or as the right side of subtraction).

---

### 9. REPL (`src/main.cpp`)

#### Concept

A Read-Eval-Print Loop that reads user input, parses and simplifies it, and prints the result. Uses GNU Readline for line editing (arrow keys, backspace) and command history.

#### Commands

| Input | Action |
|-------|--------|
| Any expression | Parse → simplify → print |
| `eval(expr, x=val)` | Parse → simplify → evaluate numerically |
| `quit` or `exit` | Exit |

---

## Build Warning Fixed

During initial build, the compiler flagged an unused `prec_of()` function in `printer.cpp`. It was a leftover from an earlier design. Removed to satisfy `-Werror`.

---

## Phase 2 — Calculus Module

---

### 10. Symbolic Differentiation (`src/modules/calculus.h`, `src/modules/calculus.cpp`)

#### Concept

Symbolic differentiation computes the derivative of an expression **as a formula**, not a number. It applies the rules of calculus recursively on the AST. Each node type has a corresponding differentiation rule.

#### Rules Implemented

| Expression | Derivative | Rule Name |
|-----------|-----------|-----------|
| `c` (constant) | `0` | Constant rule |
| `x` (the variable) | `1` | Identity |
| `y` (other variable) | `0` | Constant rule |
| `f + g` | `f' + g'` | Sum rule |
| `f * g` | `f'*g + f*g'` | Product rule |
| `f^n` (n constant) | `n * f^(n-1) * f'` | Power + chain rule |
| `f^g` (general) | `f^g * (g'*ln(f) + g*f'/f)` | Logarithmic differentiation |
| `sin(u)` | `cos(u) * u'` | Chain rule |
| `cos(u)` | `-sin(u) * u'` | Chain rule |
| `exp(u)` | `exp(u) * u'` | Chain rule |
| `ln(u)` | `u'/u` | Chain rule |

#### ASCII Diagram — Differentiating `sin(x^2)`

```
Input AST:          FUNC("sin")
                        │
                      POW
                     /   \
                   SYM(x) NUM(2)

Apply chain rule: d/dx sin(u) = cos(u) * u'
  where u = x^2, u' = 2*x^1*1 = 2*x

Result AST:         MUL
                   /   \
              FUNC("cos")  MUL
                  │       /   \
                POW    NUM(2) SYM(x)
               /   \
             SYM(x) NUM(2)

After simplification: 2*x*cos(x^2)
```

#### Annotated Code (power rule with chain rule)

```cpp
case NodeType::POW: {
    Expr* base = e->children[0];
    Expr* exp = e->children[1];

    if (exp->is_num()) {
        // d/dx(f^n) = n * f^(n-1) * f'
        Expr* f_prime = differentiate(arena, base, var);
        return make_mul(arena, {
            make_num(arena, exp->num),           // n
            make_pow(arena, base, make_num(arena, exp->num - 1)),  // f^(n-1)
            f_prime                              // f' (chain rule)
        });
    }
    // ... general case
}
```

#### Why It Works

The recursive structure mirrors the mathematical rules exactly. Each node dispatches to its rule, and the chain rule is handled naturally: when differentiating `sin(u)`, we compute `u'` by recursing into `u`. The simplifier then cleans up the result (e.g., `x^1` → `x`, `1*x` → `x`).

#### Key Design Decision

Differentiation always produces an unsimplified result. The caller must run `simplify()` afterward. This keeps the differentiation code clean and focused on correctness, while the simplifier handles canonicalization.

---

### 11. Bug Fix: MUL(-1, f) → NEG(f)

#### Symptom

`diff(cos(x), x)` produced `-1*sin(x)` instead of `-sin(x)`.

#### Investigation

The cos derivative rule creates `NEG(sin(x))`. During simplification, NEG was being converted to `MUL(-1, sin(x))`. But the MUL simplifier didn't convert it back.

#### Root Cause

The simplifier had a rule `NEG(x) → MUL(-1, x)` for canonical form, but no reverse rule in MUL to emit NEG when the coefficient is exactly -1.

#### Fix

1. Removed the `NEG → MUL(-1, x)` conversion (NEG stays as NEG)
2. Added a check in MUL simplification: if result is `MUL(-1, x)`, emit `NEG(x)` instead

#### Lesson

Canonical form conversions must be bidirectional or avoided. If you convert A→B, you need B→A or you lose information about the original intent.

---

## Phase 3 — Polynomial Expansion

---

### 12. Polynomial Expansion (`src/modules/polynomial.h`, `src/modules/polynomial.cpp`)

#### Concept

Polynomial expansion takes a factored expression like `(x+1)*(x+2)` and distributes all products to produce a sum of terms: `x^2 + 3x + 2`. This is the inverse of factoring.

#### Algorithm

The expansion works by repeated distribution:

1. For `(a+b)*(c+d)`: multiply every term of the left by every term of the right
2. For `(expr)^n`: repeatedly multiply the expanded result by a fresh copy of the base

#### ASCII Diagram — Expanding `(x+1)*(x+2)`

```
    MUL
   /   \
 ADD   ADD
 / \   / \
x   1 x   2

Distribute:
  x*x, x*2, 1*x, 1*2

Result:
  ADD(MUL(x,x), MUL(x,2), MUL(1,x), MUL(1,2))

After simplification:
  x*x + 3*x + 2
```

#### Annotated Code

```cpp
Expr* mul_expand(Arena& arena, Expr* a, Expr* b) {
    // Collect terms from each side
    std::vector<Expr*> a_terms = a->is_add() ? a->children : std::vector{a};
    std::vector<Expr*> b_terms = b->is_add() ? b->children : std::vector{b};

    // Distribute: each term of a * each term of b
    std::vector<Expr*> result;
    for (auto* at : a_terms)
        for (auto* bt : b_terms)
            result.push_back(make_mul(arena, {at, bt}));

    if (result.size() == 1) return result[0];
    return make_add(arena, std::move(result));
}
```

#### Why It Works

Distribution is the fundamental algebraic identity `a*(b+c) = a*b + a*c` applied recursively. By collecting all terms from both sides and forming every pairwise product, we get the fully expanded form.

---

### 13. Deep Copy for Safe Expansion

#### Symptom

`expand((x+1)^3)` produced `3 + 3x + x³ + x²` (wrong) instead of `1 + 3x + 3x² + x³`.

#### Investigation

The expansion loop `result = mul_expand(result, base)` followed by `simplify(result)` was corrupting the `base` tree because `simplify` modifies children in-place.

#### Root Cause

AST nodes are shared by pointer. When `mul_expand` builds new MUL nodes containing pointers to `base`'s children, and then `simplify` rearranges those children, subsequent iterations see a corrupted base.

#### Fix

Deep-copy the base before each multiplication:

```cpp
Expr* deep_copy(Arena& arena, const Expr* e) {
    auto* n = arena.create<Expr>();
    n->type = e->type; n->num = e->num; n->name = e->name;
    for (auto* c : e->children)
        n->children.push_back(deep_copy(arena, c));
    return n;
}
```

#### Lesson

In an arena-allocated AST where "immutability" is by convention, any operation that reuses subtrees must deep-copy them first if any subsequent operation might mutate the tree.

---

### 14. Coefficient Extraction Fix for N-ary MUL

#### Symptom

`expand((x+1)^3)` still produced wrong results after the deep-copy fix.

#### Investigation

After expansion, terms like `MUL(2, x, x)` were being treated as the pure number `2` during like-term combination.

#### Root Cause

`extract_coeff` returned `{2.0, nullptr}` for MUL nodes with 3+ children. The `nullptr` base caused the term to be added to `num_sum` instead of being grouped with other `x*x` terms.

#### Fix

Strip the numeric first child from the MUL and return the remaining children as the base:

```cpp
if (e->children.size() > 2) {
    e->children.erase(e->children.begin()); // remove numeric
    if (e->children.size() == 1) return {c, e->children[0]};
    return {c, e};  // MUL of remaining factors
}
```

#### Lesson

Coefficient extraction must handle all arities of MUL nodes, not just the binary case.

---

### 15. Linenoise Integration

#### Concept

Linenoise is a minimal line-editing library (single C file) that provides readline-like functionality without external dependencies. It supports:
- Line editing (arrow keys, backspace, delete)
- Command history (up/down arrows)
- Multi-line editing

#### Why the Switch

GNU Readline requires `libreadline-dev` as a system dependency. Linenoise is bundled directly in the project (`third_party/linenoise/`), making the build self-contained — only a C/C++ compiler and CMake are needed.


---

## Phase 4 — Extended Operators & Rational Arithmetic

---

### 16. Rational Number Representation

#### Concept

Instead of storing numbers as `double` (which loses precision: `1/3` becomes `0.333...`),
Axion stores every number as an exact fraction `num/den` (two `int64_t` values). After
every arithmetic operation, the fraction is reduced by dividing both by their GCD.

#### ASCII Diagram

```
Before (Phase 1–3):          After (Phase 4):
  Expr.num = 0.333...          Expr.num = 1
  (double, lossy)              Expr.den = 3
                               (exact rational)

  1/3 + 1/6                   1/3 + 1/6
  = 0.333 + 0.166             = (1*6 + 1*3) / (3*6)
  = 0.5 (lucky)               = 9/18
                               = 1/2 (reduced by GCD=9)
```

#### Annotated Code

```cpp
void reduce_fraction(int64_t& num, int64_t& den) {
    if (den < 0) { num = -num; den = -den; }  // normalize sign
    if (num == 0) { den = 1; return; }         // 0/n = 0/1
    int64_t g = gcd_val(num, den);             // find GCD
    num /= g; den /= g;                       // reduce
}
```

#### Why It Works

Rational arithmetic is closed: adding, multiplying, or dividing two rationals always
produces another rational. By reducing after every operation, we keep fractions in
lowest terms and can detect exact equality (e.g., `2/4 == 1/2` after reduction).

---

### 17. Factorial Operator

#### Concept

Factorial `n!` is a postfix operator: `5!` = 120. It's parsed as a new AST node type
`FACTORIAL` and simplified to an integer when the operand is a non-negative integer ≤ 20.

#### Implementation

```cpp
// Parser: after parsing a primary expression, check for trailing '!'
while (peek().type == TokenType::BANG) {
    advance();
    left = make_factorial(arena_, left);
}

// Simplifier: compute if possible
if (e->is_factorial() && inner->is_num() && inner->den == 1 && inner->num >= 0)
    return make_num(arena, factorial_val(inner->num));
```

---

### 18. Session Variables & User Functions

#### Concept

The REPL maintains a session with persistent variable bindings and user-defined functions.
`:=` creates a binding that persists across inputs.

#### Examples

```
a := 3          → stores a=3 in session
a + 1           → substitutes a=3, simplifies to 4
f(x) := x^2    → stores function definition
f(5)            → substitutes x=5 into body, returns 25
```

#### Implementation

The session stores:
- `vars`: map of name → Expr* (variable bindings)
- `func_bodies`: map of name → Expr* (function body)
- `func_params`: map of name → vector<string> (parameter names)

Before simplification, all symbols are substituted with their session values.

---

### 19. Subscript Identifiers

#### Concept

Variables like `x_1`, `x_(12)`, `a_ij` are parsed as single identifier strings.
The `_` character is part of the name, not a separate operator.

#### Lexer Rule

```cpp
// Allow _ in identifiers, with optional (multi-char) subscript
if (std::isalpha(c) || c == '_') {
    while (std::isalnum(input[i]) || input[i] == '_') ++i;
    if (input[i] == '(' && input[i-1] == '_') {
        // consume x_(12) as one token
        ++i; while (input[i] != ')') ++i; ++i;
    }
}
```

---

### 20. Constants & Numeric Approximation

#### Concept

`pi` and `e` are symbolic constants — they remain as symbols during algebraic
manipulation but can be evaluated numerically with `approx()`.

```
pi + pi         → 2*pi (symbolic)
approx(pi)     → 3.14159265358979 (numeric)
```

The `approx` command substitutes `pi=3.14159...` and `e=2.71828...` then evaluates.


---

## Phase 5 — Summation, Product & Collect

---

### 21. Finite Summation (`src/modules/series.h`, `src/modules/series.cpp`)

#### Concept

`sum(expr, var, lo, hi)` computes a finite sum by substituting each integer value
of `var` from `lo` to `hi` into `expr`, simplifying each term, then adding them all.

#### ASCII Diagram

```
sum(k^2, k, 1, 3):

  k=1: 1^2 = 1
  k=2: 2^2 = 4
  k=3: 3^2 = 9
  
  Result: 1 + 4 + 9 = 14
```

#### Annotated Code

```cpp
Expr* eval_sum(Arena& arena, Expr* body, const std::string& var, int64_t lo, int64_t hi) {
    std::vector<Expr*> terms;
    for (int64_t k = lo; k <= hi; ++k) {
        Expr* val = make_num(arena, k);
        Expr* term = subst_var(arena, body, var, val);  // replace var with k
        term = simplify(arena, term);                   // simplify (e.g. k^2 → 9)
        terms.push_back(term);
    }
    Expr* result = make_add(arena, std::move(terms));
    return simplify(arena, result);  // combine: 1 + 4 + 9 = 14
}
```

#### Why It Works

By substituting and simplifying each term individually, we get exact rational results.
The final simplification combines all numeric terms into one. For expressions with
symbolic parts, like `sum(k*x, k, 1, 3)`, the result is `6*x` (since 1+2+3=6).

---

### 22. Finite Product

Same approach as summation but multiplies instead of adding.
`prod(k, k, 1, 5)` = 1×2×3×4×5 = 120.

---

### 23. Collect (`collect(expr, var)`)

#### Concept

`collect` groups terms of a polynomial by powers of a specified variable.
For example, `x^2 + 2*x + 3*x + 1` becomes `1 + 5*x + x^2` (the two `x` terms
are combined into `5*x`).

#### Algorithm

1. For each term in the ADD, determine its power of `var` (0, 1, 2, ...)
2. Group terms by power
3. For each group, sum the coefficients (the non-var parts)
4. Rebuild: `coeff_sum * var^power` for each group

#### Why It's Different from Simplify

The simplifier already combines `2*x + 3*x` → `5*x`. But `collect` is explicit
about which variable to group by, which matters for multivariate expressions where
you might want to collect by `x` or by `y`.


---

## Phase 6 — Limits

---

### 24. Limit Computation (`src/modules/limits.h`, `src/modules/limits.cpp`)

#### Concept

A **limit** asks: "what value does f(x) approach as x approaches a point?"
If direct substitution gives a valid number, that's the limit. If it gives
an indeterminate form like 0/0, we apply L'Hôpital's rule.

#### Algorithm

```
compute_limit(expr, var, point):
  1. Simplify expr
  2. Check if expr is a quotient (f/g form)
     - If f(point)=0 AND g(point)=0:
       Apply L'Hôpital: lim(f/g) = lim(f'/g')
       Recurse (max 5 times)
  3. Try direct substitution: replace var with point, simplify
  4. If result is a valid number, return it
  5. Otherwise: "undefined"
```

#### ASCII Diagram — L'Hôpital on sin(x)/x at x=0

```
sin(x)/x at x=0:
  sin(0) = 0, denominator = 0  → 0/0 indeterminate!

Apply L'Hôpital:
  d/dx sin(x) = cos(x)
  d/dx x = 1

  lim cos(x)/1 at x=0 = cos(0)/1 = 1/1 = 1 ✓
```

#### Annotated Code

```cpp
// Check 0/0 form
bool num_zero = eval_is_zero(arena, numerator, var, point);
bool den_zero = eval_is_zero(arena, denominator, var, point);

if (num_zero && den_zero) {
    // L'Hôpital: differentiate top and bottom
    Expr* f_prime = differentiate(arena, numerator, var);
    Expr* g_prime = differentiate(arena, denominator, var);
    // Build f'/g' and try again
    Expr* new_expr = make_mul(arena, {f_prime, make_pow(arena, g_prime, make_num(arena, -1))});
    Expr* result = try_direct(arena, new_expr, var, point);
    if (result) return result;
    return try_lhopital(arena, new_expr, var, point, depth + 1);  // recurse
}
```

#### Why It Works

L'Hôpital's rule states that if lim f(x)/g(x) is 0/0 or ∞/∞, then
lim f(x)/g(x) = lim f'(x)/g'(x) (provided the latter exists). By differentiating
and re-evaluating, we often resolve the indeterminate form in 1–2 iterations.


---

## Phase 7 — Symbolic Integration

---

### 25. Integration Engine (`src/modules/integration.h`, `src/modules/integration.cpp`)

#### What Is Symbolic Integration?

When you differentiate `x^3`, you get `3*x^2`. Integration is the **reverse**: given `3*x^2`,
find the function whose derivative is `3*x^2` — that's `x^3` (plus a constant).

Unlike differentiation (which always works mechanically), integration is **hard**. There's no
universal algorithm. Instead, we maintain a **table of known patterns** and try to match the
input against them.

#### How the Module Is Structured

```
integrate(expr, var)
    │
    ├─ Is it a constant? (no var) ──→ c*x
    │
    ├─ Is it just x? ──→ x²/2
    │
    ├─ Is it e^x? ──→ e^x
    │
    ├─ Is it e^(a*x)? ──→ e^(a*x)/a
    │
    ├─ Is it x^n? ──→ x^(n+1)/(n+1)
    │   └─ Special case: x^(-1) ──→ ln|x|
    │
    ├─ Is it a sum? (ADD) ──→ integrate each term separately
    │
    ├─ Is it a product? (MUL)
    │   ├─ Constants × f(x) ──→ constants × integrate(f(x))
    │   └─ sin(x)*cos(x) ──→ sin(x)²/2
    │
    ├─ Is it -f(x)? (NEG) ──→ -integrate(f(x))
    │
    ├─ Is it sin(x)? ──→ -cos(x)
    ├─ Is it cos(x)? ──→ sin(x)
    ├─ Is it exp(x)? ──→ exp(x)
    │
    ├─ Is it sin(a*x)? ──→ -cos(a*x)/a
    ├─ Is it cos(a*x)? ──→ sin(a*x)/a
    ├─ Is it exp(a*x)? ──→ exp(a*x)/a
    │
    └─ None matched ──→ "cannot integrate"
```

Each branch is a simple `if` statement that checks the structure of the AST node.

#### The Key Insight: Pattern Matching on the AST

Integration works by **looking at the shape of the tree**. For example:

```
Input: 3*x^2

AST:  MUL
     /   \
   NUM(3) POW
          / \
        SYM(x) NUM(2)

The integrator sees:
  - It's a MUL ──→ enter the "product" branch
  - One factor is a constant (3) ──→ pull it out
  - The other factor is x^2 ──→ apply power rule
  - Power rule: x^(2+1)/(2+1) = x^3/3
  - Result: 3 * x^3/3 = x^3
```

#### Annotated Code: The Power Rule

```cpp
// x^n → x^(n+1)/(n+1) for n != -1
if (e->is_pow() && is_var(e->children[0], var) && e->children[1]->is_num()) {
    int64_t n_num = e->children[1]->num;   // numerator of exponent
    int64_t n_den = e->children[1]->den;   // denominator of exponent

    // Compute n+1 as a fraction: n_num/n_den + 1 = (n_num + n_den)/n_den
    int64_t new_n = n_num + n_den;
    int64_t new_d = n_den;
    reduce_fraction(new_n, new_d);

    // Special case: n = -1 means x^(-1) = 1/x, integral is ln|x|
    if (new_n == 0) {
        return make_func(arena, "ln", make_func(arena, "abs", make_sym(arena, var)));
    }

    // General case: (1/(n+1)) * x^(n+1)
    // The coefficient is the reciprocal of (n+1): new_d/new_n
    return make_mul(arena, {
        make_num(arena, new_d, new_n),                          // 1/(n+1)
        make_pow(arena, make_sym(arena, var), make_num(arena, new_n, new_d))  // x^(n+1)
    });
}
```

**Why rational arithmetic matters here:** If n = 1/2 (i.e., `sqrt(x) = x^(1/2)`),
then n+1 = 3/2, and the integral is `(2/3)*x^(3/2)`. With floating-point, this
would accumulate rounding errors. With exact rationals, it's always precise.

#### Annotated Code: Linearity (Sum Rule)

```cpp
// int(a + b + c) = int(a) + int(b) + int(c)
if (e->is_add()) {
    std::vector<Expr*> terms;
    for (auto* c : e->children) {
        Expr* t = integrate(arena, c, var);  // integrate each term
        if (!t) return nullptr;               // if ANY term fails, give up
        terms.push_back(t);
    }
    return make_add(arena, std::move(terms));
}
```

This is why `int(3*x^2 + 2*x, x)` works: it splits into `int(3*x^2)` + `int(2*x)`,
integrates each separately, then combines.

#### Annotated Code: Constant Multiple

```cpp
if (e->is_mul()) {
    // Separate factors into constants (no var) and var-dependent
    std::vector<Expr*> const_factors;
    std::vector<Expr*> var_factors;
    for (auto* f : e->children) {
        if (contains_var(f, var))
            var_factors.push_back(f);    // depends on x
        else
            const_factors.push_back(f);  // just a number/other symbol
    }

    // If we have constants AND var parts: pull constants out
    // int(5 * x^2) = 5 * int(x^2)
    if (!const_factors.empty() && !var_factors.empty()) {
        Expr* var_part = /* combine var_factors */;
        Expr* integral = integrate(arena, var_part, var);
        if (!integral) return nullptr;
        const_factors.push_back(integral);
        return make_mul(arena, std::move(const_factors));
    }
}
```

#### Annotated Code: Linear Substitution

```cpp
// sin(a*x) → -cos(a*x)/a
// This handles cases like sin(3*x), where the "inner function" is linear (a*x)
if (e->is_func() && e->name == "sin" && e->children[0]->is_mul()) {
    auto* inner = e->children[0];  // the a*x part
    std::vector<Expr*> consts;
    bool has_var = false;
    for (auto* f : inner->children) {
        if (is_var(f, var)) has_var = true;  // found x
        else consts.push_back(f);            // everything else is the "a"
    }
    if (has_var && !consts.empty()) {
        Expr* a = /* combine consts */;
        // Result: (1/a) * (-cos(a*x))
        return make_mul(arena, {
            make_pow(arena, a, make_num(arena, -1)),  // 1/a
            make_neg(arena, make_func(arena, "cos", inner))  // -cos(a*x)
        });
    }
}
```

**Why this works:** By the chain rule, d/dx[-cos(a*x)] = sin(a*x) * a.
So ∫sin(a*x)dx = -cos(a*x)/a. This is called "linear substitution" because
the inner function `a*x` is linear (its derivative `a` is constant).

#### Annotated Code: Definite Integral (Fundamental Theorem of Calculus)

```cpp
Expr* integrate_definite(Arena& arena, Expr* e, const std::string& var, Expr* a, Expr* b) {
    // Step 1: Find the antiderivative F(x)
    Expr* antideriv = integrate(arena, e, var);
    if (!antideriv) return nullptr;
    antideriv = simplify(arena, antideriv);

    // Step 2: Compute F(b) - F(a)
    Expr* fb = subst_int(arena, antideriv, var, b);  // F(b): replace x with upper bound
    Expr* fa = subst_int(arena, antideriv, var, a);  // F(a): replace x with lower bound
    fb = simplify(arena, fb);
    fa = simplify(arena, fa);

    // Step 3: Subtract
    Expr* result = make_add(arena, {fb, make_neg(arena, fa)});  // F(b) - F(a)
    return simplify(arena, result);
}
```

**Example:** `int(sin(x), x, 0, pi)`
1. Antiderivative: F(x) = -cos(x)
2. F(pi) = -cos(pi) = -(-1) = 1
3. F(0) = -cos(0) = -(1) = -1
4. F(pi) - F(0) = 1 - (-1) = 2 ✓

#### What This Module CANNOT Do

| Expression | Why it fails |
|-----------|-------------|
| `int(x*sin(x), x)` | Requires integration by parts |
| `int(1/(x^2+1), x)` | Requires arctan (not in table) |
| `int(exp(-x^2), x)` | No closed form exists |
| `int(ln(x), x)` | Requires integration by parts |

These would need more advanced techniques (integration by parts, partial fractions,
special function recognition) which are planned for future phases.

---

### 26. Trig Simplification at π

#### Rules Added

```
sin(pi) → 0       cos(pi) → -1
sin(n*pi) → 0     cos(n*pi) → (-1)^n   (for integer n)
```

These are essential for definite integrals with bounds involving π.
Without them, `int(sin(x), x, 0, pi)` would return `1 - cos(pi)` instead of `2`.

#### How It's Implemented

```cpp
// In simplify(): check if FUNC argument is the symbol "pi"
if (e->is_func() && e->children[0]->is_sym() && e->children[0]->name == "pi") {
    if (e->name == "sin") return make_num(arena, 0);    // sin(π) = 0
    if (e->name == "cos") return make_num(arena, -1);   // cos(π) = -1
}

// Check for cos(n*pi) where n is integer
if (e->is_func() && e->name == "cos" && e->children[0]->is_mul()) {
    // Look for pattern: MUL(integer, SYM("pi"))
    if (/* matches */) {
        return make_num(arena, (n % 2 == 0) ? 1 : -1);  // (-1)^n
    }
}
```


---

## Phase 8 — Matrices & Vectors

---

### 27. Matrix Representation (`src/modules/matrix.h`, `src/modules/matrix.cpp`)

#### Concept

A **matrix** is a 2D grid of numbers (or expressions). A **vector** is a 1D list.
In Axion, matrices are stored as a special FUNC node with a name encoding the dimensions
and children being the elements in row-major order (left to right, top to bottom).

#### How Matrices Are Stored in the AST

```
[[1, 2], [3, 4]]  →  FUNC node:
                        name = "__matrix__2x2"
                        children = [NUM(1), NUM(2), NUM(3), NUM(4)]

[5, 6, 7]         →  FUNC node:
                        name = "__matrix__1x3"
                        children = [NUM(5), NUM(6), NUM(7)]
```

The name `__matrix__RxC` encodes rows (R) and columns (C). To access element at
row i, column j: `children[i * cols + j]`.

#### Why This Design?

We reuse the existing FUNC node type instead of adding a new NodeType. This means:
- No changes needed to the simplifier, printer, or evaluator for basic handling
- Matrix-specific operations are in their own module
- The `__matrix__` prefix prevents collision with user-defined functions

#### ASCII Diagram — Matrix Multiplication

```
A = [[1,2],[3,4]]    B = [[5,6],[7,8]]

A * B:
  result[0][0] = 1*5 + 2*7 = 19
  result[0][1] = 1*6 + 2*8 = 22
  result[1][0] = 3*5 + 4*7 = 43
  result[1][1] = 3*6 + 4*8 = 50

  = [[19, 22], [43, 50]]
```

#### Annotated Code: Determinant (Cofactor Expansion)

```cpp
Expr* matrix_det(Arena& arena, Expr* m) {
    int n = matrix_rows(m);

    // Base case: 1×1 matrix
    if (n == 1) return matrix_at(m, 0, 0);

    // Base case: 2×2 matrix → ad - bc
    if (n == 2) {
        Expr* ad = make_mul(arena, {matrix_at(m, 0, 0), matrix_at(m, 1, 1)});
        Expr* bc = make_mul(arena, {matrix_at(m, 0, 1), matrix_at(m, 1, 0)});
        return simplify(arena, make_add(arena, {ad, make_neg(arena, bc)}));
    }

    // General case: expand along first row
    // det = Σ (-1)^j * a[0][j] * det(minor[0][j])
    std::vector<Expr*> terms;
    for (int j = 0; j < n; ++j) {
        // Build (n-1)×(n-1) minor by removing row 0 and column j
        std::vector<Expr*> minor_elems;
        for (int r = 1; r < n; ++r)        // skip row 0
            for (int c = 0; c < n; ++c)
                if (c != j)                  // skip column j
                    minor_elems.push_back(matrix_at(m, r, c));

        Expr* minor = make_matrix(arena, n-1, n-1, std::move(minor_elems));
        Expr* cofactor = make_mul(arena, {matrix_at(m, 0, j), matrix_det(arena, minor)});
        if (j % 2 == 1) cofactor = make_neg(arena, cofactor);  // alternating sign
        terms.push_back(cofactor);
    }
    return simplify(arena, make_add(arena, std::move(terms)));
}
```

**How cofactor expansion works:**
1. Pick any row (we use row 0)
2. For each element in that row, compute the "minor" (the matrix without that row and column)
3. Multiply the element by the determinant of its minor
4. Alternate signs: +, -, +, -, ...
5. Sum all terms

This is recursive: a 3×3 det calls three 2×2 dets, a 4×4 calls four 3×3 dets, etc.

#### Annotated Code: Dot Product

```cpp
Expr* vector_dot(Arena& arena, Expr* a, Expr* b) {
    int n = a->children.size();
    // dot([a1,a2,a3], [b1,b2,b3]) = a1*b1 + a2*b2 + a3*b3
    std::vector<Expr*> terms;
    for (int i = 0; i < n; ++i)
        terms.push_back(make_mul(arena, {a->children[i], b->children[i]}));
    return simplify(arena, make_add(arena, std::move(terms)));
}
```

#### Annotated Code: Cross Product

```cpp
Expr* vector_cross(Arena& arena, Expr* a, Expr* b) {
    // Only defined for 3D vectors
    // [a1,a2,a3] × [b1,b2,b3] = [a2*b3 - a3*b2, a3*b1 - a1*b3, a1*b2 - a2*b1]
    std::vector<Expr*> elems = {
        simplify(arena, a[1]*b[2] - a[2]*b[1]),  // i component
        simplify(arena, a[2]*b[0] - a[0]*b[2]),  // j component
        simplify(arena, a[0]*b[1] - a[1]*b[0]),  // k component
    };
    return make_matrix(arena, 1, 3, std::move(elems));
}
```

**Memory trick:** The cross product formula comes from the determinant of:
```
| i   j   k  |
| a1  a2  a3 |
| b1  b2  b3 |
```

#### Annotated Code: 2×2 Inverse

```cpp
Expr* matrix_inverse(Arena& arena, Expr* m) {
    Expr* det = matrix_det(arena, m);
    if (det->is_num() && det->num == 0) return nullptr;  // singular!

    // For [[a,b],[c,d]], inverse = (1/det) * [[d,-b],[-c,a]]
    Expr* inv_det = make_pow(arena, det, make_num(arena, -1));  // 1/det
    std::vector<Expr*> elems = {
        matrix_at(m, 1, 1),              //  d
        make_neg(arena, matrix_at(m, 0, 1)),  // -b
        make_neg(arena, matrix_at(m, 1, 0)),  // -c
        matrix_at(m, 0, 0),              //  a
    };
    Expr* adj = make_matrix(arena, 2, 2, std::move(elems));
    return matrix_scalar_mul(arena, simplify(arena, inv_det), adj);
}
```

**Example:** `inverse([[1,2],[3,4]])`
- det = 1×4 - 2×3 = -2
- adjugate = [[4, -2], [-3, 1]]
- inverse = (1/-2) × [[4, -2], [-3, 1]] = [[-2, 1], [3/2, -1/2]]

Note how rational arithmetic gives exact results: `3/2` and `-1/2` instead of `1.5` and `-0.5`.

---

### 28. Matrix Parsing

#### How `[[1,2],[3,4]]` Is Parsed

The Pratt parser's `prefix()` function recognizes `[` as the start of a bracket expression:

```cpp
if (t.type == TokenType::LBRACKET) {
    advance();
    return parse_bracket();
}
```

`parse_bracket()` then checks:
- If next token is `[` → it's a matrix `[[...],[...]]`
- Otherwise → it's a vector `[a, b, c]`

For matrices, it reads each row as a comma-separated list inside `[...]`,
counts rows and columns, and builds the `__matrix__RxC` FUNC node.


---

## Phase 9 — Equation Solving

---

### 29. Equation Solver (`src/modules/solver.h`, `src/modules/solver.cpp`)

#### Concept

An equation solver takes an equation like `x^2 - 5*x + 6 = 0` and finds the values
of `x` that make it true. Axion handles linear and quadratic equations.

#### Algorithm

```
solve(equation, var):
  1. Move everything to LHS: lhs - rhs = 0
  2. Expand and simplify the LHS
  3. Extract polynomial coefficients: a*x^2 + b*x + c
  4. Based on degree:
     - Degree 1 (linear): x = -b/a
     - Degree 2 (quadratic): x = (-b ± sqrt(b²-4ac)) / 2a
```

#### ASCII Diagram — Solving x² - 5x + 6 = 0

```
Input: x^2 - 5*x + 6 = 0

Step 1: Extract coefficients
  a = 1 (coefficient of x^2)
  b = -5 (coefficient of x)
  c = 6 (constant term)

Step 2: Compute discriminant
  disc = b² - 4ac = 25 - 24 = 1

Step 3: sqrt(disc) = 1 (perfect square!)

Step 4: Apply quadratic formula
  x = (-(-5) ± 1) / (2*1)
  x = (5 + 1) / 2 = 3
  x = (5 - 1) / 2 = 2

Result: {3, 2}
```

#### Annotated Code: Polynomial Coefficient Extraction

```cpp
// For each term in the expression, determine its power of var and coefficient
TermInfo analyze_term(Arena& arena, Expr* e, const std::string& var) {
    // "5" → coeff=5, power=0 (constant)
    if (!contains_var(e, var)) return {e, 0};

    // "x" → coeff=1, power=1
    if (e->is_sym() && e->name == var) return {make_num(arena, 1), 1};

    // "x^3" → coeff=1, power=3
    int p = get_power(e, var);
    if (p >= 0) return {make_num(arena, 1), p};

    // "3*x^2" → coeff=3, power=2
    if (e->is_mul()) {
        // Separate constant factors from the x^n factor
        // ...
    }
}
```

#### Annotated Code: Factoring via Root-Finding

```cpp
Expr* factor(Arena& arena, Expr* e, const std::string& var) {
    // Step 1: Find roots by solving expr = 0
    Expr* eq = make_rel(arena, "=", e, make_num(arena, 0));
    auto roots = solve(arena, eq, var);

    // Step 2: Build factored form: a*(x - r1)*(x - r2)
    if (roots.size() == 2) {
        Expr* a = leading_coefficient;
        Expr* f1 = (x - roots[0]);
        Expr* f2 = (x - roots[1]);
        return a * f1 * f2;
    }
}
```

**Why this works:** A polynomial of degree n has exactly n roots (counting multiplicity).
If we know the roots r1, r2, ..., then the polynomial equals `a*(x-r1)*(x-r2)*...`
where `a` is the leading coefficient.

---

### 30. Rational Root Theorem & Synthetic Division

#### Concept

For polynomials of degree 3 or higher, there's no simple formula like the quadratic formula.
Instead, we use the **Rational Root Theorem**: if a polynomial with integer coefficients has
a rational root p/q, then p divides the constant term and q divides the leading coefficient.

#### Algorithm

```
For polynomial a_n*x^n + ... + a_1*x + a_0:
  1. List all factors of |a_0| (constant term): p = ±1, ±2, ...
  2. List all factors of |a_n| (leading coeff): q = ±1, ±2, ...
  3. Try each candidate p/q:
     - Evaluate polynomial at p/q
     - If result = 0, it's a root!
  4. When a root r is found, divide out (x - r) using synthetic division
  5. Repeat on the reduced polynomial until degree ≤ 2
  6. Solve remaining quadratic with the formula
```

#### ASCII Diagram — Solving x³ - 6x² + 11x - 6 = 0

```
Constant term = -6, factors: ±1, ±2, ±3, ±6
Leading coeff = 1, factors: ±1
Candidates: ±1, ±2, ±3, ±6

Try x=1: 1 - 6 + 11 - 6 = 0 ✓  → root found!

Synthetic division by (x - 1):
  [1, -6, 11, -6] ÷ (x-1) = [1, -5, 6]
  
Remaining: x² - 5x + 6
  Discriminant: 25 - 24 = 1
  Roots: (5±1)/2 = 3, 2

All roots: {1, 3, 2}
```

#### Annotated Code (synthetic division)

```cpp
// When root num/den is found, divide polynomial by (x - num/den)
std::vector<int64_t> new_coeffs(current_degree);
new_coeffs[current_degree - 1] = current_coeffs[current_degree];  // leading stays
for (int i = current_degree - 2; i >= 0; --i) {
    // Each new coefficient = old coefficient + root * previous new coefficient
    new_coeffs[i] = current_coeffs[i + 1] + new_coeffs[i + 1] * num / den;
}
current_coeffs = new_coeffs;
current_degree--;
```

#### Test Results

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `solve(x^3 - 6*x^2 + 11*x - 6 = 0, x)` | {1, 2, 3} | {1, 3, 2} | ✅ |
| `solve(x^3 - 1 = 0, x)` | 1 (rational only) | 1 | ✅ |
| `solve(x^4 - 5*x^2 + 4 = 0, x)` | {±1, ±2} | {1, 2, -1, -2} | ✅ |
| `factor(x^3 - 6*x^2 + 11*x - 6, x)` | (x-1)(x-2)(x-3) | (-1+x)(-3+x)(-2+x) | ✅ |
| `factor(x^4 - 5*x^2 + 4, x)` | (x-1)(x+1)(x-2)(x+2) | (-1+x)(-2+x)(1+x)(2+x) | ✅ |


---

## Phase 10 — Pattern Matching & Rewrite Engine

---

### 31. File Structure

Phase 10 adds two files:
- `src/modules/rewrite.h` — public API (5 functions + 2 types)
- `src/modules/rewrite.cpp` — implementation (~130 lines)

The module has **no dependencies** on other modules except `simplify.h` (called after
each rewrite to re-canonicalize). It does not modify the parser, lexer, or AST.

---

### 32. Data Structures

#### `RewriteRule` (rewrite.h, line 12)

```cpp
struct RewriteRule {
    Expr* pattern;       // AST tree with wildcards (e.g. sin(_x)^2 + cos(_x)^2)
    Expr* replacement;   // AST tree with same wildcards (e.g. NUM(1))
    std::string name;    // display name ("rule1", "rule2", ...)
};
```

A rule is just two AST trees. The pattern tree contains wildcard symbols (`_x`, `_y`).
The replacement tree uses the same wildcards — they get substituted with whatever
the pattern matched.

**Storage:** Rules live in `Session::rules` (a `std::vector<RewriteRule>`) in main.cpp.
When the user types `rule(pattern, replacement)`, the REPL parses both arguments as
normal expressions and stores them as a new RewriteRule.

#### `Bindings` (rewrite.h, line 20)

```cpp
using Bindings = std::unordered_map<std::string, Expr*>;
```

A map from wildcard name (e.g. `"_x"`) to the expression it matched.
Created empty at the start of each match attempt, filled during matching.

---

### 33. Implementation: `is_wildcard` (rewrite.cpp, line 8)

```cpp
bool is_wildcard(const Expr* e) {
    return e->is_sym() && !e->name.empty() && e->name[0] == '_';
}
```

A wildcard is any SYM node whose name starts with underscore. This is a convention —
the parser doesn't treat `_x` specially; it's just a normal symbol. The rewrite engine
gives it special meaning during matching.

**Design choice:** Using a naming convention (prefix `_`) instead of a new NodeType
means no changes to the parser, printer, or simplifier. The downside: users can't
have variables named `_x` (they'd be treated as wildcards in rules).

---

### 34. Implementation: `expr_equal` (rewrite.cpp, line 12)

```cpp
bool expr_equal(const Expr* a, const Expr* b) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    if (a->type != b->type) return false;
    if (a->is_num()) return a->num == b->num && a->den == b->den;
    if (a->is_sym()) return a->name == b->name;
    if (a->name != b->name) return false;
    if (a->children.size() != b->children.size()) return false;
    for (size_t i = 0; i < a->children.size(); ++i)
        if (!expr_equal(a->children[i], b->children[i])) return false;
    return true;
}
```

Deep recursive equality. Used when a wildcard appears twice in a pattern —
the second occurrence must match the exact same tree as the first.

Example: In `sin(_x)^2 + cos(_x)^2`, `_x` appears twice. If the first match
binds `_x = a`, the second match checks `expr_equal(a, a)` → true.
But `sin(a)^2 + cos(b)^2` would fail because `expr_equal(a, b)` → false.

---

### 35. Implementation: `pattern_match` (rewrite.cpp, line 73)

This is the core function. It walks two trees in parallel:

```cpp
bool pattern_match(const Expr* expr, const Expr* pattern, Bindings& bindings) {
```

**Case 1: Wildcard** (line 77)
```cpp
    if (is_wildcard(pattern)) {
        auto it = bindings.find(pattern->name);
        if (it != bindings.end())
            return expr_equal(expr, it->second);  // already bound: must match same
        bindings[pattern->name] = const_cast<Expr*>(expr);  // new binding
        return true;
    }
```
If the pattern node is `_x`, either bind it (first time) or verify consistency (second time).

**Case 2: Literal number** (line 86)
```cpp
    if (pattern->is_num())
        return expr->is_num() && expr->num == pattern->num && expr->den == pattern->den;
```
Numbers must match exactly. `2` in pattern only matches `2` in expression.

**Case 3: Named symbol** (line 91)
```cpp
    if (pattern->is_sym())
        return expr->is_sym() && expr->name == pattern->name;
```
Non-wildcard symbols (like `x` or `pi`) must match by name.

**Case 4: Commutative nodes** (line 97)
```cpp
    if (expr->is_add() || expr->is_mul())
        return match_commutative(expr->children, pattern->children, bindings);
```
ADD and MUL are commutative — `a + b` equals `b + a`. So we try permutations.

**Case 5: Everything else** (line 101)
```cpp
    if (expr->children.size() != pattern->children.size()) return false;
    for (size_t i = 0; i < expr->children.size(); ++i)
        if (!pattern_match(expr->children[i], pattern->children[i], bindings))
            return false;
    return true;
```
POW, FUNC, NEG, etc. — match children in order (not commutative).

---

### 36. Implementation: `match_commutative` (rewrite.cpp, line 30)

The challenge: `ADD(sin(a)^2, cos(a)^2)` must match pattern `ADD(sin(_x)^2, cos(_x)^2)`
regardless of child order.

```cpp
bool match_commutative(const vector<Expr*>& expr_children,
                       const vector<Expr*>& pat_children,
                       Bindings& bindings) {
    if (expr_children.size() != pat_children.size()) return false;
```

**Optimization for 2 children** (most common case):
```cpp
    // Try in-order first
    Bindings trial = bindings;
    if (match all in order) { bindings = trial; return true; }

    // Try swapped
    trial = bindings;
    if (match(expr[0], pat[1]) && match(expr[1], pat[0])) { bindings = trial; return true; }
```

**General case (3-4 children):** Uses `std::next_permutation` to try all orderings.
The `trial = bindings` save/restore pattern ensures failed attempts don't corrupt
the binding state.

**Why limit to 4?** Permutations grow as n! (24 for 4, 120 for 5). Patterns with
5+ terms in a single ADD/MUL are rare in practice.

---

### 37. Implementation: `apply_bindings` (rewrite.cpp, line 108)

After matching succeeds, we have bindings like `{_x → a, _y → b}`.
Now we build the replacement by copying the template and substituting wildcards:

```cpp
Expr* apply_bindings(Arena& arena, const Expr* tmpl, const Bindings& bindings) {
    if (is_wildcard(tmpl)) {
        auto it = bindings.find(tmpl->name);
        if (it != bindings.end()) return it->second;  // substitute!
        return const_cast<Expr*>(tmpl);
    }
    // Deep copy everything else
    auto* n = arena.create<Expr>();
    n->type = tmpl->type; n->num = tmpl->num; n->den = tmpl->den; n->name = tmpl->name;
    for (auto* c : tmpl->children)
        n->children.push_back(apply_bindings(arena, c, bindings));
    return n;
}
```

Example: template `log(_x * _y)` with bindings `{_x→2, _y→3}` produces `log(2*3)`.
After simplification: `log(6)`.

---

### 38. Implementation: `apply_rule_recursive` (rewrite.cpp, line 126)

A rule might match deep inside an expression. This function walks the tree top-down:

```cpp
Expr* apply_rule_recursive(Arena& arena, Expr* expr, const RewriteRule& rule) {
    // Try at current node first (top-down priority)
    Expr* result = apply_rule(arena, expr, rule);
    if (result) return result;

    // Try in each child
    bool changed = false;
    for (auto& child : expr->children) {
        Expr* new_child = apply_rule_recursive(arena, child, rule);
        if (new_child) {
            child = new_child;   // mutate in place
            changed = true;
        }
    }
    return changed ? expr : nullptr;
}
```

**Note:** This mutates the tree in place (sets `child = new_child`). This is safe
because we're in the arena — old nodes aren't freed, just abandoned.

---

### 39. Implementation: `apply_rules` (rewrite.cpp, line 140)

The outer loop that applies all rules repeatedly:

```cpp
Expr* apply_rules(Arena& arena, Expr* expr, const vector<RewriteRule>& rules, int max_iter) {
    for (int iter = 0; iter < max_iter; ++iter) {
        bool changed = false;
        for (const auto& rule : rules) {
            Expr* result = apply_rule_recursive(arena, expr, rule);
            if (result) {
                expr = simplify(arena, result);  // re-simplify after rewrite
                changed = true;
                break;  // restart from first rule
            }
        }
        if (!changed) break;  // fixed point reached
    }
    return expr;
}
```

**Key design decisions:**
1. **`break` after first match** — restart from rule 1 because a rewrite may enable earlier rules
2. **`simplify` after each rewrite** — ensures canonical form before next match attempt
3. **`max_iter = 100`** — prevents infinite loops from circular rules (e.g. `rule(a, b)` + `rule(b, a)`)

---

### 40. Integration with REPL (main.cpp)

**Defining a rule** (main.cpp, ~line 315):
```cpp
if (fname == "rule" && e->children.size() == 2) {
    RewriteRule r;
    r.pattern = e->children[0];      // first arg is the pattern
    r.replacement = e->children[1];  // second arg is the replacement
    session.rules.push_back(r);      // store in session
}
```

**Applying rules** (main.cpp, ~line 437):
```cpp
// After normal simplification, apply user rules
e = simplify(session.arena, e);
if (!session.rules.empty())
    e = apply_rules(session.arena, e, session.rules);
```

Rules are applied **after** the built-in simplifier. This means the simplifier
canonicalizes the expression first (sorting terms, combining like terms), which
makes pattern matching more reliable — the pattern only needs to match one
canonical form, not all equivalent orderings.


---

## Phase 11 — Advanced Calculus

---

### 41. Taylor Series Implementation (main.cpp, taylor handler)

#### Concept

A Taylor series approximates a function as a polynomial around a point:

```
f(x) ≈ f(a) + f'(a)*(x-a) + f''(a)/2!*(x-a)² + f'''(a)/3!*(x-a)³ + ...
```

#### How It's Implemented

The taylor command doesn't have its own module — it's implemented directly in the
REPL handler because it composes existing primitives (differentiate + substitute + simplify):

```
taylor(expr, var, point, order):
  current = expr
  for k = 0 to order:
    1. Evaluate current at var=point (deep-copy + substitute + simplify)
    2. Build term: value/k! * (x-point)^k
    3. Add to result if non-zero
    4. Differentiate current for next iteration
```

#### The Deep-Copy Problem

The original implementation used `substitute()` which mutates the tree in place.
This corrupted the `current` expression, making subsequent derivatives wrong.

**Fix:** A lambda `eval_at_point` deep-copies the expression before substituting:

```cpp
auto eval_at_point = [&](Expr* expr) -> Expr* {
    std::function<Expr*(const Expr*)> dcopy = [&](const Expr* node) -> Expr* {
        if (!node) return nullptr;
        if (node->is_sym() && node->name == var) return point;  // substitute here
        auto* n = session.arena.create<Expr>();
        n->type = node->type; n->num = node->num; n->den = node->den; n->name = node->name;
        for (auto* c : node->children) n->children.push_back(dcopy(c));
        return n;
    };
    return simplify(session.arena, dcopy(expr));
};
```

This combines deep-copy and substitution in one pass: when it encounters the variable
symbol, it returns the point value instead of copying the symbol.

#### Why Exact Rational Arithmetic Matters

Taylor coefficients are fractions: 1/2, 1/6, 1/24, 1/120, etc.
With floating-point, these would accumulate rounding errors.
With exact rationals, `(1/6)*x^3` stays exactly `(1/6)*x^3`.

#### Trace: `taylor(sin(x), x, 0, 5)`

```
k=0: current = sin(x), eval at 0 → sin(0) = 0         → skip (zero)
k=1: current = cos(x), eval at 0 → cos(0) = 1         → term: 1/1! * x = x
k=2: current = -sin(x), eval at 0 → -sin(0) = 0       → skip
k=3: current = -cos(x), eval at 0 → -cos(0) = -1      → term: -1/6 * x^3
k=4: current = sin(x), eval at 0 → sin(0) = 0         → skip
k=5: current = cos(x), eval at 0 → cos(0) = 1         → term: 1/120 * x^5

Result: x + (-1/6)*x^3 + (1/120)*x^5
```

---

### 42. Trigonometric Simplification (main.cpp, trigsimp handler)

#### Implementation

`trigsimp` reuses the Phase 10 rewrite engine with built-in trig rules:

```cpp
if (fname == "trigsimp") {
    static std::vector<RewriteRule> trig_rules;
    if (trig_rules.empty()) {
        trig_rules.push_back({
            parse(arena, "sin(_x)^2 + cos(_x)^2"),  // pattern
            make_num(arena, 1),                       // replacement
            "pythagorean"
        });
    }
    expr = apply_rules(arena, expr, trig_rules);
}
```

The rules are created once (static) and reused. This demonstrates how the rewrite
engine from Phase 10 enables new simplification capabilities without modifying the
core simplifier.

---

### 43. Higher-Order Derivatives

Already implemented in Phase 4's REPL handler:

```cpp
if (fname == "diff" && e->children.size() >= 2) {
    int order = 1;
    if (e->children.size() >= 3 && e->children[2]->is_num())
        order = static_cast<int>(e->children[2]->num);
    for (int i = 0; i < order; ++i) {
        expr = differentiate(arena, expr, var);
        expr = simplify(arena, expr);
    }
}
```

Simply loops: differentiate N times, simplifying after each step.
`diff(x^5, x, 3)` = d³/dx³(x⁵) = d/dx(d/dx(5x⁴)) = d/dx(20x³) = 60x².


---

## Architecture Decision: Why Not Everything Is Data-Driven

---

### 44. The Rule Table vs Code Boundary

After the refactoring, Axion has two kinds of mathematical knowledge:

1. **Data-driven rules** (in `src/engine/rules.cpp`) — pure pattern→replacement
2. **Algorithmic logic** (in module `.cpp` files) — recursive procedures

A natural question: why not put EVERYTHING in the rule table?

---

### 45. What IS in the Rule Table (and why)

These are things you might want to **extend** — add new functions, new identities:

```cpp
// rules.cpp — easy to add new entries:
{"sin",   "cos(_u)"},        // d/dx sin(u) = cos(u) * u'
{"asin",  "(1 - _u^2)^(-1/2)"},  // just add one line for arcsin!
add_id("sinh(0)", "0");      // just add one line for new identity!
```

**Why these are data:** They're function-specific facts. There are infinitely many
possible functions (sin, cos, arctan, Bessel, ...) and you want to add new ones
without touching the differentiation algorithm.

---

### 46. What IS NOT in the Rule Table (and why)

These structural rules remain as code in `calculus.cpp`:

```cpp
// Sum rule: d/dx(f + g + h) = f' + g' + h'
case NodeType::ADD: {
    for (auto* c : e->children)
        terms.push_back(differentiate(arena, c, var));  // RECURSIVE CALL
    return make_add(arena, std::move(terms));
}

// Product rule: d/dx(f*g) = f'*g + f*g'
case NodeType::MUL: {
    for (size_t i = 0; i < e->children.size(); ++i) {
        // differentiate the i-th factor, keep others unchanged
        // RECURSIVE + PERMUTATION LOGIC
    }
}
```

**Why these can't be data:**

1. **Recursion.** The right-hand side calls `differentiate()` again. A simple
   pattern→replacement rule can't express "apply this same transformation recursively
   to subexpressions." You'd need a Turing-complete rule language — at which point
   you've just reinvented C++ with worse syntax.

2. **Variable-length children.** The product rule for `f*g*h` generates 3 terms
   (one for each factor). The number of terms depends on the input structure.
   A fixed pattern can't express "for each child, do X."

3. **Arithmetic on the AST.** The power rule `d/dx(f^n) = n*f^(n-1)*f'` requires
   computing `n-1` from the exponent node. This is arithmetic on the tree structure,
   not pattern matching.

4. **They never change.** The product rule is a mathematical law. You will never
   need to "add a new product rule" or "swap it for a different one." It's been
   the same since Leibniz invented it in 1684. Making it data-driven adds complexity
   with zero practical benefit.

---

### 47. The Design Principle

```
┌─────────────────────────────────────────────────────────┐
│  CHANGES FREQUENTLY          │  NEVER CHANGES           │
│  (new functions, identities) │  (structural algorithms) │
│                              │                          │
│  → Put in rules.cpp          │  → Keep as code          │
│    (data table)              │    (module .cpp files)   │
│                              │                          │
│  Examples:                   │  Examples:               │
│  • sin → cos                 │  • Product rule          │
│  • cos(pi) → -1             │  • Chain rule            │
│  • exp(ln(x)) → x           │  • Linearity             │
│  • sin²+cos² → 1            │  • Cofactor expansion    │
│  • new user rules            │  • Gaussian elimination  │
│                              │  • L'Hôpital iteration   │
└─────────────────────────────────────────────────────────┘
```

**Rule of thumb:** If you can express it as `pattern → replacement` without
recursion or loops, it belongs in `rules.cpp`. If it requires recursion,
iteration over children, or arithmetic on the tree structure, it belongs in code.

---

### 48. How to Add New Mathematical Knowledge

| I want to... | Where to edit | Example |
|-------------|---------------|---------|
| Add a new function derivative | `rules.cpp` diff_rules | `{"sinh", "cosh(_u)"}` |
| Add a new integral | `rules.cpp` int_rules | `{"sec", "ln(sec(_u) + tan(_u))"}` |
| Add a new identity | `rules.cpp` add_id() | `add_id("cosh(0)", "1")` |
| Add a new trig identity | `rules.cpp` add_id() | `add_id("1 + tan(_x)^2", "sec(_x)^2")` |
| Add a new structural rule | Module .cpp file | (rare — only if math itself changes) |


---

## Phase 12 — Number Theory & Discrete Math

---

### 49. Number Theory Module (`src/modules/number_theory.h`, `src/modules/number_theory.cpp`)

#### What This Module Provides

Pure integer arithmetic functions for number theory and combinatorics.
All functions operate on `int64_t` — no symbolic expressions, just numbers.

#### File Structure

```
number_theory.h  — function declarations (7 functions)
number_theory.cpp — implementations (~60 lines total)
```

---

### 50. GCD and LCM

#### Implementation

GCD uses the Euclidean algorithm (already in `ast.cpp` as `gcd_val`):
```cpp
int64_t gcd_val(int64_t a, int64_t b) {
    a = std::abs(a); b = std::abs(b);
    while (b) { a %= b; std::swap(a, b); }
    return a;
}
```

LCM uses the identity `lcm(a,b) = |a*b| / gcd(a,b)`:
```cpp
int64_t lcm_val(int64_t a, int64_t b) {
    return std::abs(a / gcd_val(a, b) * b);  // divide first to avoid overflow
}
```

---

### 51. Binomial Coefficient

#### Why Not Use Factorials Directly

`binom(10,3) = 10!/(3!*7!) = 3628800/(6*5040) = 120`

But computing `10!` then dividing risks overflow for large n.
Instead, use iterative multiplication with early division:

```cpp
int64_t binom_val(int64_t n, int64_t k) {
    if (k > n - k) k = n - k;  // binom(10,7) = binom(10,3)
    int64_t r = 1;
    for (int64_t i = 0; i < k; ++i)
        r = r * (n - i) / (i + 1);  // always divides evenly
    return r;
}
```

The division `r * (n-i) / (i+1)` always produces an integer because the
partial product of k consecutive integers is always divisible by k!.

---

### 52. Prime Factorization

#### Algorithm: Trial Division

```cpp
std::vector<std::pair<int64_t, int64_t>> prime_factorize(int64_t n) {
    std::vector<std::pair<int64_t, int64_t>> factors;
    for (int64_t d = 2; d * d <= n; ++d) {  // only check up to √n
        if (n % d == 0) {
            int64_t count = 0;
            while (n % d == 0) { n /= d; ++count; }  // divide out all copies
            factors.push_back({d, count});
        }
    }
    if (n > 1) factors.push_back({n, 1});  // remaining prime factor
    return factors;
}
```

**Why trial division is sufficient:** For `int64_t` (max ~9.2×10^18), the largest
prime factor we need to trial-divide up to is √(9.2×10^18) ≈ 3×10^9. This takes
at most ~3 billion iterations in the worst case (for a large prime), but in practice
most numbers factor quickly.

**Output format:** `factorize(360)` prints `2^3 * 3^2 * 5` — human-readable.

---

### 53. Modular Exponentiation

#### Algorithm: Binary (Square-and-Multiply)

Computing `2^10 mod 1000` naively would compute `2^10 = 1024` then mod.
For large exponents (e.g. `powmod(2, 1000000, 97)`), this overflows.

Binary exponentiation keeps numbers small by reducing mod at each step:

```cpp
int64_t powmod_val(int64_t base, int64_t exp, int64_t mod) {
    int64_t result = 1;
    base = base % mod;
    while (exp > 0) {
        if (exp % 2 == 1)           // if current bit is 1
            result = (result * base) % mod;  // multiply and reduce
        exp /= 2;                   // shift to next bit
        base = (base * base) % mod; // square and reduce
    }
    return result;
}
```

**Time complexity:** O(log exp) — only ~20 multiplications for exp=10^6.

---

### 54. REPL Integration

All number theory functions are dispatched in main.cpp by function name.
They extract integer arguments, call the pure function, and print the result.
No symbolic manipulation needed — these are purely computational.

---

## Phase 13 — Meta-Rule Engine

---

### 55. Context-Aware Wildcards (`src/modules/rewrite.cpp`)

#### Concept

Standard wildcards (`_x`) match any expression. But for integration and differentiation rules, we need to distinguish between expressions that **contain** a variable and those that are **constant** with respect to it. For example, in `∫ 3*sin(x) dx`, the `3` is constant and `sin(x)` depends on `x`.

Context-aware wildcards solve this by carrying a **match context** — the name of the "active variable" — and checking whether a matched expression contains it.

#### ASCII Diagram

```
Expression: 3 * sin(x)     Active variable: "x"

Pattern: _c__const * _f__hasvar

_c__const matches 3       ← does NOT contain "x" ✓
_f__hasvar matches sin(x) ← DOES contain "x" ✓
```

#### Annotated Code

```cpp
struct MatchContext {
    std::string active_var;  // variable of interest
};

static MatchContext g_match_ctx;  // thread-local context

bool contains_var(const Expr* e, const std::string& var) {
    if (!e) return false;
    if (e->is_sym() && e->name == var) return true;
    for (auto* c : e->children)
        if (contains_var(c, var)) return true;
    return false;
}

bool check_type_constraint(const Expr* expr, const std::string& type) {
    // ...existing checks...
    if (type == "const") return !contains_var(expr, g_match_ctx.active_var);
    if (type == "hasvar") return contains_var(expr, g_match_ctx.active_var);
    return true;
}
```

#### Why It Works

The `contains_var` function recursively walks the expression tree looking for the active variable. If found, the expression "has" the variable; if not, it's "constant" with respect to it. The context is set before matching and restored after, allowing nested matches with different contexts.

---

### 56. Recognition Functions (`src/engine/rules.cpp`)

#### Concept

Pattern matching works **forward** — given a pattern, find expressions that match it. But some mathematical transformations work **backward** — given an expression, recognize that it has a special structure. For example, recognizing that `x² + 6x + 9` is a perfect square `(x+3)²`.

Recognition functions are C++ functions registered as "backward rules." They examine an expression and, if they detect a known pattern, return the simplified form.

#### ASCII Diagram

```
Input: ADD(x^2, 6*x, 9)

recognize_perfect_square():
  1. Find square terms: x^2 (base=x), 9 (base=3, since 3²=9)
  2. Compute expected middle: 2*x*3 = 6*x
  3. Compare with actual middle: 6*x ✓
  4. Return: POW(ADD(x, 3), 2)

Output: (x + 3)^2
```

#### Annotated Code

```cpp
// Type for recognition functions
using RecognitionFn = Expr* (*)(Arena& arena, Expr* expr);

// Apply recognizers bottom-up at every subexpression
Expr* apply_recognizers(Arena& arena, Expr* expr, const std::vector<RecognitionFn>& fns) {
    for (auto& child : expr->children) {
        Expr* r = apply_recognizers(arena, child, fns);
        if (r) child = r;
    }
    for (auto fn : fns) {
        Expr* r = fn(arena, expr);
        if (r) return r;
    }
    return expr;
}
```

The perfect square recognizer:

```cpp
Expr* recognize_perfect_square(Arena& arena, Expr* expr) {
    if (!expr->is_add() || expr->children.size() != 3) return nullptr;

    // Find two "square" terms (x^2 or numeric perfect squares like 9)
    std::vector<SquareInfo> squares;
    for (size_t i = 0; i < 3; ++i) {
        BaseExp be = get_base_exp(expr->children[i]);
        if (be.exp_n == 2 && be.exp_d == 1)
            squares.push_back({be.base, i});
        else if (t->is_num() && is_perfect_square(t->num))
            squares.push_back({make_num(arena, sqrt(t->num)), i});
    }
    if (squares.size() != 2) return nullptr;

    // Verify middle term = ±2*a*b
    Expr* pos_mid = simplify(arena, make_mul(arena, {make_num(arena, 2), a, b}));
    if (print(mid) == print(pos_mid))
        return make_pow(arena, make_add(arena, {a, b}), make_num(arena, 2));
}
```

#### Why It Works

The recognizer uses a **hypothesis-and-verify** approach:
1. **Hypothesis:** "This 3-term sum might be a perfect square trinomial"
2. **Extract:** Find the two square terms and compute their roots
3. **Verify:** Check that the remaining term equals exactly `2*root1*root2`
4. **Return:** If verified, return the factored form

This cannot be expressed as a flat rewrite rule because it requires arithmetic verification (checking that `6 = 2*1*3`).

---

### 57. Two-Tier Simplification Architecture

#### Concept

The simplification system is split into two tiers:

| Tier | Function | Speed | Rules |
|------|----------|-------|-------|
| Fast | `simplify()` | O(n) | Algorithmic: flatten, sort, fold, combine |
| Full | `simplify_full()` | O(n × rules × iterations) | Algorithmic + identity rule table |

The fast tier handles structural transformations (flattening nested ADD/MUL, sorting children, combining like terms, constant folding). The full tier additionally applies the declarative identity rules from `rules.cpp` via the pattern-matching rewrite engine.

#### ASCII Diagram

```
simplify(expr):                    simplify_full(expr):
┌──────────────────┐              ┌──────────────────┐
│ 1. Recurse       │              │ 1. simplify()    │
│ 2. Flatten       │              │ 2. init_rules()  │
│ 3. Sort          │              │ 3. apply_rules() │ ← identity table
│ 4. Fold constants│              │    (repeat until  │
│ 5. Combine terms │              │     stable)       │
│ 6. Eval funcs    │              └──────────────────┘
│    (sin(0)→0)    │
└──────────────────┘

Used by:                           Used by:
- Internal loops                   - User-facing output
- Intermediate steps               - Module boundaries
- apply_rules() itself             - REPL final result
```

#### Why It Works

Separating the tiers prevents infinite recursion: `apply_rules()` calls `simplify()` after each rule application (to normalize the result), but `simplify()` does NOT call `apply_rules()`. If it did, applying a rule would trigger more rule applications, which would trigger more, ad infinitum.

The fast tier is called ~100× more often than the full tier (inside solver loops, matrix operations, series computation), so keeping it lightweight is critical for performance.

---

### 58. Rule Table Design (`src/engine/rules.cpp`)

#### Concept

All mathematical knowledge is centralized in `rules.cpp` as data tables. The tables are initialized once at startup and read by all modules.

#### Table Categories

| Table | Purpose | Consumer |
|-------|---------|----------|
| `identities` | Pattern→replacement rules | `simplify_full()` |
| `diff_rules` | Function derivative table | `calculus.cpp` |
| `int_rules` | Function antiderivative table | `integration.cpp` |
| `recognizers` | Backward pattern detectors | `factor()` |

#### Key Design Decision: Pattern Simplification

Rule patterns are `simplify()`-ed at initialization time:

```cpp
auto add_id = [&](const char* pattern, const char* replacement) {
    g_rules.identities.push_back({
        simplify(g_rule_arena, parse(g_rule_arena, pattern)),  // ← simplified!
        parse(g_rule_arena, replacement), ""
    });
};
```

This ensures patterns are in canonical form and will match expressions that have also been simplified. Without this, `sin(pi/2)` (which parses as `sin(MUL(pi, POW(2,-1)))`) would never match the simplified form `sin(MUL(1/2, pi))`.

#### Adding New Functions

To add a new function (e.g., `sinh`), only `rules.cpp` needs editing:

```cpp
// Differentiation
{"sinh", "cosh(_u)"},

// Integration
{"sinh", "cosh(_u)"},

// Identity (in simplify.cpp for computational eval)
if (e->name == "sinh") return make_num(arena, 0);  // sinh(0)=0
```

This validates the data-driven architecture: mathematical knowledge is separated from algorithmic code.


---

### 59. Common-Factor Recognition (`src/engine/rules.cpp`)

#### Concept

Given a sum like `a*x + b*x + c*x`, extract the common symbolic factor `x` to produce `x*(a+b+c)`. This is the **reverse** of distribution — it cannot be expressed as a simple rewrite rule because it requires inspecting ALL terms to find what's shared.

#### ASCII Diagram

```
Input: ADD(MUL(a, x), MUL(b, x), MUL(c, x))

Step 1: Get factors of first term: {a, x}
Step 2: For candidate "x", check all other terms:
  - MUL(b, x) contains x ✓
  - MUL(c, x) contains x ✓
Step 3: Divide each term by x:
  - a*x / x = a
  - b*x / x = b
  - c*x / x = c
Step 4: Return MUL(x, ADD(a, b, c))

Output: x*(a + b + c)
```

#### Why It Works

The algorithm iterates over factors of the first term as candidates. For each non-numeric candidate, it checks whether that factor appears in every other term. If found, it divides each term by the candidate (removing one occurrence) and wraps the result in a product.

---

### 60. Perfect Cube Recognition

#### Concept

Extends the perfect square recognizer to detect `(a+b)³ = a³ + 3a²b + 3ab² + b³`. The algorithm finds two cube terms, then verifies the two middle terms match the expected binomial coefficients.

#### Why It Works

Same hypothesis-verify approach as the square recognizer:
1. Find terms with exponent 3 (or numeric perfect cubes)
2. Extract roots `a` and `b`
3. Compute expected middle terms: `3a²b` and `3ab²`
4. Compare against actual middle terms using `print()` for canonical comparison

---

### 61. Strategy Engine (`simplify_smart`)

#### Concept

The strategy engine decides **when** to apply backward rules (factoring). The principle: after simplification, try recognizers. If the recognized form is shorter or equal in length, prefer it (factored forms are generally more useful).

#### ASCII Diagram

```
Input: x^2 + 2*x + 1

simplify_full() → "1 + x^2 + 2*x"  (15 chars)
                         │
                         ▼
apply_recognizers() → "(1 + x)^2"    (9 chars)
                         │
                         ▼ shorter!
Output: (1 + x)^2
```

```
Input: expand((x+1)^2)

expand() uses simplify_full() directly → "1 + x^2 + 2*x"
(bypasses simplify_smart, so no re-factoring)
```

#### Why It Works

By comparing string lengths of the original vs. recognized form, the engine makes a simple but effective heuristic decision. Factored forms are almost always shorter than expanded forms for perfect powers and common-factor expressions. The `expand()` command deliberately bypasses this to respect the user's intent.
