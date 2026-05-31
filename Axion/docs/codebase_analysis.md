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
