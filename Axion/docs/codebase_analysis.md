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

### 30. Test Results

| Input | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| `solve(2*x + 6 = 0, x)` | -3 | -3 | ✅ |
| `solve(x^2 - 5*x + 6 = 0, x)` | {3, 2} | {3, 2} | ✅ |
| `solve(x^2 - 2 = 0, x)` | symbolic sqrt | symbolic sqrt | ✅ |
| `factor(x^2 - 5*x + 6, x)` | (x-3)(x-2) | (-3+x)(-2+x) | ✅ |
| `factor(x^2 - 1, x)` | (x-1)(x+1) | (-1+x)(1+x) | ✅ |
