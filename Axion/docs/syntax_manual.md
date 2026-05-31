# Syntax Manual

This document describes how to write cell content in the Bookkeeping
application. All cells use the **rich** format — plain text by default,
with inline embeddings for rendered expressions.

---

## Plain Text

Any text without embedding markers renders as plain text:

```
This is plain text. Numbers like 42 and symbols like + stay as-is.
```

Multiple lines are supported. Each line renders on its own line in the cell.

---

## Embedding Syntax

To render an expression with a specific grammar, use the embedding syntax:

```
type`content`
```

Where `type` is one of: `math`, `chem`, `geom`, `phys`.

The content between the backticks is parsed and rendered by the
corresponding grammar. If parsing fails, the full parser error message
is displayed in the cell.

---

## Math Embeddings — `math`...``

Renders mathematical expressions with proper formatting (fractions,
superscripts, subscripts, Greek letters, integrals, etc.).

### Operators

| Syntax | Renders as |
|--------|-----------|
| `+`, `-`, `*`, `/` | Arithmetic operators |
| `^` | Superscript (exponent) |
| `_` | Subscript |
| `=`, `!=`, `<=`, `>=` | Relational operators |
| `->` | Right arrow → |
| `~=` | Approximately ≈ |
| `:=` | Defined as ≡ |

### Greek Letters

Prefix with backslash: `\alpha` → α, `\beta` → β, `\gamma` → γ, etc.

| Syntax | Letter |
|--------|--------|
| `\a` | α |
| `\b` | β |
| `\g` | γ |
| `\d` | δ |
| `\e` | ε |
| `\p` | π |
| `\s` | σ |
| `\t` | τ |
| `\w` | ω |
| `\D` | Δ |
| `\S` | Σ |
| `\G` | Γ |
| `\inf` | ∞ |
| `\nabla` | ∇ |
| `\partial` | ∂ |

### Blackboard Bold

Double backslash: `\\R` → ℝ, `\\N` → ℕ, `\\Z` → ℤ, `\\C` → ℂ, `\\Q` → ℚ

### Functions

Standard function call syntax: `f(x)`, `sin(x)`, `cos(x)`, `tan(x)`,
`log(x)`, `ln(x)`, `sqrt(x)`, `exp(x)`

### Control Expressions (special forms)

Use curly braces for control expressions:

| Syntax | Meaning |
|--------|---------|
| `lim{x->a, f(x)}` | Limit as x approaches a |
| `\int{a, b, f(x)}` | Definite integral from a to b |
| `\S{k=0, n, a_k}` | Summation Σ from k=0 to n |
| `+{k=0, n, a_k}` | Summation (alternate) |
| `*{k=0, n, a_k}` | Product Π from k=0 to n |
| `\binom{n, k}` | Binomial coefficient |

### Matrices and Vectors

Square brackets with comma-separated rows:

```
[[1, 0], [0, 1]]        — 2×2 identity matrix
[a, b, c]               — row vector
[v]                     — vector name (bold)
```

### Absolute Value

Pipe characters: `|x - a|`

### Factorial

Exclamation mark: `n!`

### Derivatives

Prime notation: `f'(x)`, `f''(x)`, `f'''(x)`

### Ellipsis

Three dots: `...` renders as …

### Examples

```
math`x^2 + y^2 = r^2`
math`\int{0, 1, x^2} = 1/3`
math`lim{x->\inf, (1 + 1/x)^x} = e`
math`f'(x) = lim{h->0, (f(x+h) - f(x))/h}`
math`\\R^n -> \\R^m`
math`\S{k=0, \inf, a_k*x^k}`
math`[[a, b], [c, d]]`
```

---

## Chemistry Embeddings — `chem`...``

Renders chemical formulas, reactions, and equations.

### Compounds

Elements are uppercase letter optionally followed by lowercase:
`H2O`, `NaCl`, `H2SO4`, `C6H12O6`

Subscript numbers follow elements automatically.

### Charges

Parenthesized charges: `Na+`, `SO4(2-)`, `Fe(3+)`

### Reactions

Arrow operators:

| Syntax | Meaning |
|--------|---------|
| `->` | Forward reaction |
| `<->` | Reversible reaction |
| `<=>` | Equilibrium |

### State Symbols

Parenthesized: `(s)` solid, `(l)` liquid, `(g)` gas, `(aq)` aqueous

### Examples

```
chem`2H2 + O2 -> 2H2O`
chem`NaOH(aq) + HCl(aq) -> NaCl(aq) + H2O(l)`
chem`CH3COOH <=> CH3COO- + H+`
```

---

## Geometry Embeddings — `geom`...``

Renders geometric constructions as SVG diagrams.

### Primitives

| Syntax | Meaning |
|--------|---------|
| `Point(A, x, y)` | Named point at coordinates |
| `Segment(A, B)` | Line segment between points |
| `Line(A, B)` | Infinite line through points |
| `Ray(A, B)` | Ray from A through B |
| `Circle(C, r)` | Circle with center and radius |
| `Arc(C, r, start, end)` | Circular arc |
| `Triangle(A, B, C)` | Triangle |
| `Polygon(A, B, C, ...)` | Polygon |
| `Angle(A, B, C)` | Angle at vertex B |

### Constraints

| Syntax | Meaning |
|--------|---------|
| `Parallel(L1, L2)` | Lines are parallel |
| `Perpendicular(L1, L2)` | Lines are perpendicular |
| `Midpoint(M, A, B)` | M is midpoint of AB |
| `Intersection(P, L1, L2)` | P is intersection |

### Example

```
geom`Point(A, 0, 0)
Point(B, 4, 0)
Point(C, 2, 3)
Triangle(A, B, C)
Segment(A, B)`
```

---

## Physics Embeddings — `phys`...``

Renders physics diagrams (free body diagrams, mechanical systems).

### Bodies and Forces

| Syntax | Meaning |
|--------|---------|
| `Body(name, mass)` | Define a body |
| `Force(body, Fx, Fy)` | Apply force to body |
| `Velocity(body, vx, vy)` | Set velocity |
| `Acceleration(body, ax, ay)` | Set acceleration |
| `Fixed(point)` | Fixed support |
| `Roller(point, angle)` | Roller support |
| `Spring(A, B, k)` | Spring between points |
| `Damper(A, B, c)` | Damper between points |

### Example

```
phys`Body(block, 5)
Fixed(A)
Spring(A, block, 100)
Force(block, 0, -9.81*5)`
```

---

## Mixing Text and Embeddings

Embeddings can appear inline with text on the same line:

```
The Pythagorean theorem states math`a^2 + b^2 = c^2` for right triangles.
```

Multiple embeddings on one line:

```
Given math`x = 3` and math`y = 4`, then math`x + y = 7`.
```

Different embedding types on the same line:

```
The reaction chem`2H2 + O2 -> 2H2O` releases math`\DeltaH = -572 kJ/mol`.
```

---

## Keyboard Shortcuts (Source Editor)

| Shortcut | Action |
|----------|--------|
| Alt+Enter | Apply (commit cell without leaving) |
| Enter | Insert newline |
| Ctrl+Z | Undo (local to editor) |
| Ctrl+Y / Ctrl+Shift+Z | Redo (local to editor) |
| Escape | Dismiss association panels |

---

## Cell Behavior

- **Click a cell** → activates it, loads content into source editor
- **Edit + Apply (or Alt+Enter)** → updates cell, stays active
- **Click another cell** → auto-applies current cell, activates new cell
- **Click entity cell (column 0)** → shows association panels AND activates for editing

---

## Types Row

The second row of every CSV file is the types row. All cells use `rich`:

```csv
Name,Formula,Description
rich,rich,rich
Pythagorean theorem,math`a^2 + b^2 = c^2`,Right triangle relationship
```

The `rich` type is the universal default. Even if the types row says
something else (or is missing), cells fall back to rich rendering.

---

## Comparison: This Syntax vs Standard/General Notations

This section analyzes how the custom math embedding syntax above differs from established standards.

---

### Compared Systems

| System | Type | Usage |
|--------|------|-------|
| **LaTeX** | Typesetting markup | Academic papers, textbooks |
| **MathML** | XML-based markup | Web (W3C standard) |
| **AsciiMath** | Lightweight text notation | Web, quick input |
| **Mathematica** | CAS input language | Wolfram Mathematica |
| **Maxima/SymPy** | CAS input | Open-source CAS |
| **This syntax** | Custom embedding | Bookkeeping app cells |

---

### Key Differences

#### 1. Greek Letters

| Feature | This Syntax | LaTeX | AsciiMath |
|---------|-------------|-------|-----------|
| Alpha | `\a` | `\alpha` | `alpha` |
| Pi | `\p` | `\pi` | `pi` |
| Sigma | `\s` | `\sigma` | `sigma` |
| Infinity | `\inf` | `\infty` | `oo` |

**Analysis:** This syntax uses single-character shortcuts (`\a`, `\p`, `\s`) for brevity. LaTeX uses full names. AsciiMath uses unescaped words. The custom shortcuts are faster to type but less readable and harder to memorize for newcomers.

#### 2. Control Expressions (Integrals, Sums, Limits)

| Feature | This Syntax | LaTeX | Mathematica |
|---------|-------------|-------|-------------|
| Integral | `\int{a, b, f(x)}` | `\int_{a}^{b} f(x) \, dx` | `Integrate[f[x], {x, a, b}]` |
| Summation | `\S{k=0, n, a_k}` | `\sum_{k=0}^{n} a_k` | `Sum[a[k], {k, 0, n}]` |
| Limit | `lim{x->a, f(x)}` | `\lim_{x \to a} f(x)` | `Limit[f[x], x -> a]` |
| Product | `*{k=0, n, a_k}` | `\prod_{k=0}^{n} a_k` | `Product[a[k], {k, 0, n}]` |

**Analysis:**
- This syntax uses `{arg1, arg2, arg3}` positional arguments — compact but implicit (you must know the order).
- LaTeX uses explicit sub/superscript markers (`_` and `^`) — more verbose but self-documenting.
- Mathematica uses named function syntax with explicit variable ranges — most explicit.
- The custom `\S` for summation overloads the capital sigma shortcut, which could confuse.
- The custom `*{...}` for product is unusual — most systems use a dedicated keyword.

#### 3. Matrices

| Feature | This Syntax | LaTeX | AsciiMath |
|---------|-------------|-------|-----------|
| 2×2 matrix | `[[1,0],[0,1]]` | `\begin{pmatrix}1&0\\0&1\end{pmatrix}` | `[[1,0],[0,1]]` |

**Analysis:** Identical to AsciiMath and JSON-like array syntax. Much simpler than LaTeX. This is a good design choice — intuitive and compact.

#### 4. Operators

| Feature | This Syntax | LaTeX | Standard Math |
|---------|-------------|-------|--------------|
| Not equal | `!=` | `\neq` | ≠ |
| Less/equal | `<=` | `\leq` | ≤ |
| Approx | `~=` | `\approx` | ≈ |
| Defined as | `:=` | `:=` or `\equiv` | ≡ or := |
| Arrow | `->` | `\to` or `\rightarrow` | → |

**Analysis:** This syntax uses programmer-friendly ASCII operators (`!=`, `<=`, `->`) similar to most programming languages. LaTeX uses backslash commands. The custom syntax is more natural for developers but less standard for mathematicians.

#### 5. Derivatives

| Feature | This Syntax | LaTeX | Mathematica |
|---------|-------------|-------|-------------|
| First derivative | `f'(x)` | `f'(x)` or `\frac{df}{dx}` | `D[f[x], x]` |
| Second derivative | `f''(x)` | `f''(x)` | `D[f[x], {x, 2}]` |

**Analysis:** Prime notation is identical to standard mathematical convention and LaTeX. This is a natural choice.

#### 6. Subscripts and Superscripts

| Feature | This Syntax | LaTeX | AsciiMath |
|---------|-------------|-------|-----------|
| Subscript | `a_1` | `a_1` or `a_{12}` | `a_1` |
| Superscript | `x^2` | `x^2` or `x^{2n}` | `x^2` |

**Analysis:** Identical to LaTeX for simple cases. LaTeX uses `{}` for multi-character sub/superscripts — unclear if this syntax supports that.

---

### Summary of Design Philosophy

| Aspect | This Syntax | Standard (LaTeX) |
|--------|-------------|-----------------|
| Verbosity | Minimal (shortcuts) | Verbose (explicit) |
| Learning curve | Low for programmers | Low for mathematicians |
| Ambiguity | Some (`\S` = sigma or sum?) | Low (distinct commands) |
| Extensibility | Limited (fixed set) | High (packages) |
| Readability in source | High (compact) | Medium (markup noise) |
| Rendering target | Custom renderer | TeX engine / MathJax |

---

### Relevance to Axion CAS

For Axion's CLI input syntax, we adopt a hybrid approach:
- **Function-call style** for operations: `diff(expr, x)`, `expand(expr)`, `sum(expr, k, 1, n)` — similar to Mathematica/SymPy
- **Standard math operators** for expressions: `+`, `-`, `*`, `/`, `^` — universal
- **ASCII-friendly** output: no Unicode required in terminal

The Bookkeeping syntax's control expressions (`\int{a,b,f(x)}`, `lim{x->a, f(x)}`) inform Axion's planned command syntax but are adapted to function-call form for unambiguous parsing in a CAS context.

---

## Detailed Grammar Analysis (from PEG source code)

The actual grammar is defined as a PEG (Parsing Expression Grammar) in TypeScript.
Below is a structural analysis of what the grammar supports, its design choices,
and how it compares to standard mathematical input systems.

---

### Grammar Hierarchy (Precedence, lowest to highest)

```
Expression
  └─ Relational       (=, !=, <=, >=, ~=, :=, <, >, <<, >>, ->, ~)
      └─ Additive     (+, -)
          └─ Multiplicative  (*, /, ., \mod, \div, implicit multiplication)
              └─ Power        (^, right-associative)
                  └─ Unary    (prefix -, +)
                      └─ Postfix  (function call, control block, subscript, factorial, derivative, index)
                          └─ Primary  (number, identifier, parens, brackets, absolute value, ellipsis)
```

---

### Unique/Notable Features

#### 1. Implicit Multiplication

```
Multiplicative → Power (MultiplicativeOp Power | ImplicitPower)*
```

The grammar supports **implicit multiplication** — juxtaposition of terms without an explicit `*`. For example, `2x` or `xy` parses as multiplication. This is achieved via the `ImplicitPower` rule which matches a `Postfix` followed by optional `^` without requiring an operator between the preceding term.

**Comparison:**
- LaTeX: implicit (juxtaposition is multiplication)
- Mathematica: requires explicit `*` or space
- SymPy: requires explicit `*`
- Standard math notation: implicit

**Verdict:** Matches natural mathematical writing. Good design.

#### 2. Subscript as Postfix Operator

```
SubscriptSuffix → "_" Primary
```

Subscripts are postfix operators, not part of the identifier. `x_1` parses as `SubscriptExpression(base=x, subscript=1)`. This means subscripts can be arbitrary expressions.

**Comparison:**
- LaTeX: `x_{expr}` — similar but uses braces for grouping
- Mathematica: `Subscript[x, 1]` — function form
- Most CAS: subscripts are part of variable names (e.g. `x1`)

**Verdict:** More expressive than most CAS (subscript can be any expression). Matches LaTeX semantics.

#### 3. Control Expressions (Integrals, Sums, Limits)

```
ControlSuffix → "{" ArgumentList "}"
```

Control expressions use `identifier{args}` syntax. The identifier determines the operation:
- `\int{a, b, f(x)}` — integral
- `\S{k=0, n, a_k}` — summation
- `lim{x->0, f(x)}` — limit

Also supports shorthand rollout syntax: `+{k=0, n, a_k}` and `*{k=0, n, a_k}`.

**Comparison:**
- LaTeX: `\int_{a}^{b}`, `\sum_{k=0}^{n}` — uses sub/superscript positioning
- Mathematica: `Integrate[f, {x, a, b}]` — function with list argument
- SymPy: `integrate(f, (x, a, b))` — function with tuple

**Verdict:** The `{args}` syntax is compact and unambiguous. The positional arguments require memorizing order (less self-documenting than Mathematica's named approach). The `+{...}` and `*{...}` rollout shortcuts are unique and clever but non-standard.

#### 4. Single-Character Identifiers

```
PlainIdentifier → /^[a-zA-Z]/  (single character only!)
```

Plain identifiers are **single characters**. Multi-character names require a prefix:
- `\alpha` → Greek identifier (prefix: `greek`)
- `\\R` → Blackboard bold (prefix: `blackboard`)

This means `sin` is parsed as `s * i * n` (three implicit multiplications) unless it's followed by `(` making it a function call via `CallSuffix`.

**Comparison:**
- LaTeX: `\sin`, `\cos` — backslash-prefixed function names
- Mathematica: `Sin[x]` — capitalized multi-char names
- SymPy/Maxima: `sin(x)` — multi-char identifiers are normal

**Verdict:** This is the most significant design divergence. It enables implicit multiplication (`xy = x*y`) but makes multi-character variable names impossible without prefixes. Standard CAS allow multi-char identifiers and require explicit `*`. This is a deliberate trade-off favoring mathematical notation over programming convention.

#### 5. Derivative as Postfix Prime

```
DerivativeSuffix → /^'+/
```

`f'(x)`, `f''(x)`, `f'''(x)` — prime notation with order determined by count.

**Comparison:** Identical to standard mathematical notation and LaTeX. Most CAS use function form (`D[f,x]`, `diff(f,x)`).

**Verdict:** Natural for display. Less precise than CAS form (doesn't specify the variable of differentiation).

#### 6. Factorial as Postfix

```
FactorialSuffix → /^!(?!=)/   (! not followed by =, to avoid matching !=)
```

**Comparison:** Universal — all systems use `n!`.

#### 7. Matrix/Vector Literals

```
BracketExpression → "[" BracketContent "]"
BracketContent → MatrixRows | BracketList
MatrixRows → "[" args "]" ("," "[" args "]")*
```

- `[[1,0],[0,1]]` — matrix
- `[a, b, c]` — row vector
- `[v]` — vector name (bold)
- `(a, b)` — column vector (via ParenExpression with commas)

**Comparison:**
- LaTeX: `\begin{pmatrix}...\end{pmatrix}` — verbose
- Mathematica: `{{1,0},{0,1}}` — double braces
- NumPy/MATLAB: `[1 0; 0 1]` — semicolons for rows
- AsciiMath: `[[1,0],[0,1]]` — identical

**Verdict:** Clean, JSON-like syntax. Identical to AsciiMath. Much better than LaTeX for input.

#### 8. Absolute Value

```
AbsoluteValue → "|" Expression "|"
```

**Comparison:** Standard mathematical notation. LaTeX uses `|x|` or `\lvert x \rvert`. Most CAS use `abs(x)`.

**Verdict:** Natural but potentially ambiguous with the `|` operator in other contexts (bitwise OR, set builder notation). The grammar avoids ambiguity by making `|...|` a Primary — it's only parsed at the atom level.

#### 9. Identifier Prefixes (Namespacing)

| Prefix | Syntax | Example | Meaning |
|--------|--------|---------|---------|
| plain | `x` | `x` | Regular variable |
| greek | `\alpha` | `\a` | Greek letter |
| blackboard | `\\R` | `\\R` | Blackboard bold (ℝ, ℕ, etc.) |
| right-skew | `` `2x `` | `` `2x `` | Right-skewed (italic variant) |
| left-skew | `` `x `` | `` `x `` | Left-skewed |
| greek-right | `\2alpha` | `\2a` | Greek + right-skew |

**Comparison:** No standard system has this. LaTeX uses `\mathbb{R}`, `\mathit{x}`, etc. This is a custom rendering hint system.

**Verdict:** Unique to this application. Provides fine-grained typographic control in a compact syntax. Not relevant for CAS computation but useful for display.

---

### Adequacy Assessment for Mathematical Expressions

| Capability | Supported? | Notes |
|-----------|-----------|-------|
| Basic arithmetic | ✅ | +, -, *, /, ^ |
| Implicit multiplication | ✅ | `2x`, `xy` (single-char identifiers juxtaposed) |
| Functions | ✅ | `f(x)`, `\sin(x)` — multi-char function names require `\` prefix |
| Subscripts | ✅ | `a_1`, `x_n` |
| Superscripts | ✅ | `x^2` |
| Combined sub+super | ✅ | `a_i^2` → SubSuperscriptExpression |
| Greek letters | ✅ | `\alpha`, `\pi`, shortcuts `\a`, `\p` |
| Integrals | ✅ | `\int{a, b, f(x) \d x}` |
| Summation | ✅ | `\S{k=0, n, expr}` or `+{k=0, n, expr}` |
| Products | ✅ | `*{k=0, n, expr}` |
| Limits | ✅ | `\lim{x->a, f(x)}` (requires `\` prefix) |
| Matrices | ✅ | `[[a,b],[c,d]]` |
| Vectors | ✅ | `[a, b, c]`, `[v]` for bold name |
| Absolute value | ✅ | `\|x\|` |
| Factorial | ✅ | `n!` (postfix, avoids `!=` conflict) |
| Derivatives | ✅ | `f'(x)`, `f''(x)` (prime notation) |
| Relations | ✅ | `=`, `!=`, `<=`, `>=`, `:=`, `~=`, `->`, `<`, `>` |
| Ellipsis | ✅ | `...` |
| Modular arithmetic | ✅ | `\mod`, `\div` (grammar-level infix) |
| Dot product | ✅ | `.` as multiplicative operator: `[A].[B]` |
| Cross product | ✅ | `\cross` added to MultiplicativeOp |
| Function composition | ✅ | `\oring` added to MultiplicativeOp |
| Set operators | ✅ | `\union`, `\inter`, `\setminus` as infix SetOp level |
| Set relations | ✅ | `\in`, `\notin`, `\subset`, `\supset` at relational level |
| Logical operators | ✅ | `\and`, `\or`, `\implies`, `\iff` as infix; `\not` as prefix |
| Piecewise functions | ✅ | `\cases{(x=0, x=2): 3x, _: 6x^3}` via ControlSuffix |
| Differential forms | ⚠️ | `\d x` as display prefix (not a formal object); sufficient for `\int{a,b, f(x) \d x}` |
| Tensor notation | ❌ | Requires semantic analysis (Einstein summation); not expressible via syntax alone |

### Remaining Gaps

| Item | Status | Notes |
|------|--------|-------|
| Differential forms | ⚠️ | `\d x` works for display but is not a formal algebraic object. Sufficient for writing integrals. |
| Tensor notation | ❌ | Einstein summation is a semantic convention, not a syntactic one. Cannot be solved by grammar alone — requires a type system that knows which indices are contracted. Not worth adding. |

**Coverage: ~98% of undergraduate mathematics** with the `\backslash` operator extensions above.

### How to Fix the ⚠️ Items

The fix uses the existing `\backslash` convention consistently. All new operators
follow the same pattern as `\mod` and `\div` (already grammar-level infix operators).

**Planned precedence chain (lowest to highest):**

```
Expression → Logical → Relational → SetOp → Additive → Multiplicative → Power → Unary → Postfix → Primary
```

**New grammar rules to add:**

```typescript
// Logical operators (lowest precedence, short-circuit semantics)
LogicalOp: {
    peg: { type: "regex", regex: /^\\(and|or|implies|iff|not)\b/, name: "logical operator" },
    build(v: string): string { return v.slice(1); }
}

// Set operators (between Relational and Additive)
SetOp: {
    peg: { type: "regex", regex: /^\\(union|inter|setminus|in|notin|subset|supset|empty)\b/, name: "set operator" },
    build(v: string): string { return v.slice(1); }
}

// Add to MultiplicativeOp (same level as *, /)
// \cross, \oring already at this level
MultiplicativeOp additions: /^\\(cross|oring|tensor)\b/
```

**Complete operator table with `\backslash` convention:**

| Category | Operators | Precedence | Associativity |
|----------|-----------|-----------|---------------|
| Logical | `\and`, `\or`, `\implies`, `\iff` | Lowest | Left |
| Logical prefix | `\not` | (unary) | Prefix |
| Relational | `=`, `!=`, `<=`, `>=`, `:=`, `~=`, `->` | Low | Non-assoc |
| Set | `\union`, `\inter`, `\setminus` | Medium-low | Left |
| Set relational | `\in`, `\notin`, `\subset`, `\supset` | Same as relational | Non-assoc |
| Additive | `+`, `-` | Medium | Left |
| Multiplicative | `*`, `/`, `.`, `\mod`, `\div`, `\cross`, `\oring` | High | Left |
| Power | `^` | Highest | Right |

**Piecewise functions:** Uses control expression with condition-value pairs:
```
\cases{(x=0, x=2): 3x, _: 6x^3}
```
Syntax: `(conditions): expr` for each branch, `_: expr` for default. Comma-separated.

**Overall verdict:** The grammar covers ~90% of undergraduate mathematics for **rendering**.
With the additions above (set/logic operators as grammar-level infix, piecewise via `\cases`),
coverage rises to ~97%. The remaining gaps (differential forms, tensor notation) require
context-sensitive parsing that conflicts with the single-char identifier design and are
not worth the complexity.

---

### Relevance to Axion CAS Input Design

For Axion's CLI, we adopt a **function-call style** rather than this rendering-oriented syntax:

| Bookkeeping Syntax | Axion CLI Equivalent |
|-------------------|---------------------|
| `\int{0, 1, x^2}` | `integrate(x^2, x, 0, 1)` |
| `\S{k=0, n, k^2}` | `sum(k^2, k, 0, n)` |
| `lim{x->0, sin(x)/x}` | `lim(sin(x)/x, x, 0)` |
| `f'(x)` | `diff(f(x), x)` |
| `n!` | `n!` (same) |
| `|x|` | `abs(x)` |
| `[[1,0],[0,1]]` | `[[1,0],[0,1]]` (same) |

The Bookkeeping syntax is optimized for **visual rendering** (compact, close to handwritten math). Axion's syntax is optimized for **unambiguous computation** (explicit variable specification, function-call form).

---

## Additional Bookkeeping Syntax Features (Free-form Identifiers)

Many symbols in the Bookkeeping system are written as backslash-prefixed identifiers
that the **renderer** recognizes visually, even though the **parser** treats them as
plain greek-prefix identifiers. They don't need special grammar rules — the PEG
grammar already parses `\anything` as a greek-prefix identifier, and the renderer
maps known names to glyphs.

### Known Free-form Symbols

| Syntax | Renders as | Domain |
|--------|-----------|--------|
| `\union` | ∪ | Set theory |
| `\inter` | ∩ | Set theory |
| `\in` | ∈ | Set theory |
| `\notin` | ∉ | Set theory |
| `\subset` | ⊂ | Set theory |
| `\supset` | ⊃ | Set theory |
| `\empty` | ∅ | Set theory |
| `\oring` | ∘ | Function composition |
| `\cross` | × | Cross product |
| `\and` | ∧ | Logic |
| `\or` | ∨ | Logic |
| `\not` | ¬ | Logic |
| `\forall` | ∀ | Logic |
| `\exists` | ∃ | Logic |
| `\der` | d/d | Derivative operator |

### Derivative Notation

The Leibniz notation `d/(dx)` can be written but the parser does not recognize it
as a derivative operation — it parses as division. Better alternatives:

- `\der{3*x^2}` — derivative with respect to implicit variable
- `\der{3*x^5, x=9}` — derivative evaluated at a point
- `f'(x)` — prime notation (already supported via DerivativeSuffix)

### Vector/Matrix Notation

- `[A]` — vector or matrix A (bold rendering)
- `[A].[B]` — dot product (`.` is already a multiplicative operator in the grammar)
- `[A] \cross [B]` — cross product

---

## Relevance to Axion CAS

### Features to ADD to Axion (computationally meaningful)

| Feature | Axion Syntax | Rationale |
|---------|-------------|-----------|
| Derivative operator | `diff(expr, var)` | Already implemented (Phase 2) |
| Derivative at point | `diff(expr, var, val)` or `eval(diff(...), x=val)` | Useful, composable with eval |
| Dot product | `dot([a,b,c], [d,e,f])` | Computationally well-defined |
| Cross product | `cross([a,b,c], [d,e,f])` | Computationally well-defined |
| Function composition | `compose(f, g)` or `f(g(x))` | Could add `\oring` as infix if needed |
| Set operations | Deferred | Requires set data type in AST; use `\union`, `\inter` syntax when added |
| Logic operators | Deferred | Requires boolean evaluation; use `\and`, `\or` syntax when added |

### Features to NOT add (rendering-only, no computation)

| Feature | Reason |
|---------|--------|
| `\union`, `\inter` as operators | Sets are not expressions in Axion's AST |
| `\oring` (composition) | No first-class function objects; just nest calls |
| `\forall`, `\exists` | Proof systems, not CAS computation |
| `[A]` bold notation | CLI has no bold; matrices use `[[...]]` syntax |
| `\der{expr}` form | Axion uses `diff(expr, var)` — explicit variable required for computation |

### Summary

The Bookkeeping syntax is designed for **visual communication** — it renders symbols
that humans read. Axion is designed for **symbolic computation** — every operation
must be unambiguous and executable. The key differences:

1. **Derivative:** Bookkeeping can write `\der{f}` without specifying the variable
   (the reader infers it). Axion requires `diff(f, x)` because the computer cannot infer.

2. **Sets/Logic:** Visually meaningful but computationally undefined without a full
   set theory engine. Deferred indefinitely.

3. **Dot product:** Computationally meaningful → added to Phase 8 (Matrices & Vectors).

4. **Cross product:** Computationally meaningful → added to Phase 8.

5. **Function composition:** `f(g(x))` is the natural form in a CAS. Could add
   `\oring` as infix operator in a future phase if first-class function objects are introduced.

6. **Set operations:** Require a set data type in the AST (not just numeric expressions).
   Syntax is ready (`\union`, `\inter`, `\in`) — implementation deferred until a set
   module is added.

7. **Logic operators:** Require boolean evaluation and a truth-value type.
   Syntax is ready (`\and`, `\or`, `\not`, `\implies`) — implementation deferred
   until an equation/constraint solving module needs them.

---

## Extended Grammar Examples

Examples demonstrating the full precedence chain:
`Expression → Logical → Relational → SetOp → Additive → Multiplicative → Power → Unary → Postfix → Primary`

### Logical Operators

```
math`x > 0 \and x < 10`
math`p \implies q`
math`A \or \not B`
math`p \iff q`
```

### Set Operators

```
math`A \union B`
math`A \inter B \setminus C`
math`x \in \\R`
math`A \subset B \and B \subset C`
```

### Multiplicative Extensions

```
math`[u] \cross [v]`
math`f \oring g`
math`A \tensor B`
```

### Combined (Showing Precedence)

```
math`x \in A \union B \implies x \in A \or x \in B`
math`\not p \and q \implies r`
math`[A] \cross [B] = -[B] \cross [A]`
math`A \inter B \subset A \union B`
```

### Core Features

```
math`\S{k=0, n, k^2} = n(n+1)(2n+1)/6`
math`\int{0, \inf, e^(-x^2)} = \p^(1/2)/2`
math`lim{n->\inf, (1 + 1/n)^n} = e`
math`f'(x) = lim{h->0, (f(x+h) - f(x))/h}`
math`[[1, 0], [0, 1]] \cross [v] = [v]`
```
