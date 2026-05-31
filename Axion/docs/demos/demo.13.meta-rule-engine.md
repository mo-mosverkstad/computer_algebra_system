# Demo 13 — Meta-Rule Engine (Complete)

## Prerequisites

```bash
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"
cd "$AXION_ROOT"
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

## Run

```bash
cd build && ./axion
```

## Demo Session

### Rest-matching with _rest wildcard

```
axion> rule(sin(_x)^2 + cos(_x)^2 + _rest, 1 + _rest)
Rule defined: _rest + sin(_x)^2 + cos(_x)^2 → 1 + _rest

axion> sin(a)^2 + cos(a)^2 + 5
6

axion> sin(t)^2 + cos(t)^2 + y
1 + y
```

### Typed wildcards (_n__num, _f__func, _s__sym)

```
axion> rule(log(_x) + log(_y) + _rest, log(_x*_y) + _rest)
Rule defined: _rest + log(_x) + log(_y) → log(_x*_y) + _rest

axion> log(2) + log(3) + log(5)
log(30)
```

### Context-aware wildcards (_c__const, _v__hasvar)

Available for use in pattern matching with `MatchContext` — enables rules
that distinguish constant vs variable-dependent subexpressions.

### Recognition functions (backward pattern detection)

```
axion> factor(a^2 + 2*a*b + b^2, a)
(a + b)^2

axion> factor(a^2 - 2*a*b + b^2, a)
(a - b)^2

axion> factor(x^2 + 2*x + 1, x)
(1 + x)^2

axion> factor(x^2 + 6*x + 9, x)
(3 + x)^2

axion> factor(9 + 6*x + x^2, x)
(3 + x)^2

axion> factor(x^2 + 2*x*y + y^2, x)
(x + y)^2
```

### Hyperbolic functions (added via rule tables only)

```
axion> diff(sinh(x), x)
cosh(x)

axion> diff(cosh(x), x)
sinh(x)

axion> diff(sinh(x^2), x)
2*x*cosh(x^2)

axion> int(cosh(x), x)
sinh(x)

axion> int(sinh(x), x)
cosh(x)

axion> sinh(0)
0

axion> cosh(0)
1
```

## All Tests

```
52 tests, all passing.
```


### Perfect cube recognition

```
axion> x^3 + 3*x^2 + 3*x + 1
(1 + x)^3

axion> x^3 + 3*x^2*y + 3*x*y^2 + y^3
(x + y)^3

axion> x^3 - 3*x^2 + 3*x - 1
(-1 + x)^3
```

### Common-factor recognition

```
axion> x*a + x*b
x*(a + b)

axion> x*a + x*b + x*c
x*(a + b + c)

axion> sin(x)*a + sin(x)*b
sin(x)*(a + b)
```

### Strategy engine (auto-factoring)

```
axion> x^2 + 2*x + 1
(1 + x)^2

axion> expand((x+1)^2)
1 + x^2 + 2*x
```

The strategy engine automatically recognizes factorable forms in direct input,
but `expand()` bypasses it to respect the user's intent.
