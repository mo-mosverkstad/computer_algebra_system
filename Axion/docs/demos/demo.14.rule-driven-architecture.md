# Demo 14 — Rule-Driven Architecture

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

### Table-driven function evaluation

```
axion> sin(0)
0

axion> cos(pi)
-1

axion> exp(1)
e

axion> cosh(0)
1
```

### New function via rules.cpp only (cot)

```
axion> diff(cot(x), x)
-sin(x)^-2

axion> diff(cot(x^2), x)
-2*x*sin(x^2)^-2
```

No changes to calculus.cpp, simplify.cpp, or any other file — only rules.cpp.

### External rule file

```
axion> load("../rules/extra.rules")
Loaded 3 rules from ../rules/extra.rules

axion> tan(x)*cos(x)
sin(x)

axion> diff(sec(x), x)
sec(x)*tan(x)

axion> diff(sec(x^2), x)
2*x*sec(x^2)*tan(x^2)
```

### Arithmetic in bindings

```
axion> rule(2*_x__num, _x__num + _x__num)
Rule defined: 2*_x__num → _x__num + _x__num

axion> 2*5
10

axion> 2*3
6
```

## All Tests

```
52 tests, all passing.
```
