# Demo 09 — Equation Solving & Factoring

## Prerequisites

```bash
sudo apt install -y build-essential cmake libgtest-dev git
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"
cd "$AXION_ROOT"
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

---

## Run

```bash
cd "$AXION_ROOT/build" && ./axion
```

```
solve(2*x + 6 = 0, x)
solve(x^2 - 5*x + 6 = 0, x)
solve(x^2 - 2 = 0, x)
solve(x^3 - 6*x^2 + 11*x - 6 = 0, x)
solve(x^4 - 5*x^2 + 4 = 0, x)
solve(2*x + 1 > 0, x)
solve(3*x - 6 <= 0, x)
solve(-x + 5 > 0, x)
solve(x + y = 5, x - y = 1, x, y)
factor(x^3 - 6*x^2 + 11*x - 6, x)
factor(x^4 - 5*x^2 + 4, x)
factor(x^2 - 1, x)
quit
```

---

## Expected Output

```
-3
{3, 2}
{(1/2)*sqrt(8), (-1/2)*sqrt(8)}
{1, 3, 2}
{1, 2, -1, -2}
x > -1/2
x <= 2
x < 5
{x = 3, y = 2}
(-1 + x)*(-3 + x)*(-2 + x)
(-1 + x)*(-2 + x)*(1 + x)*(2 + x)
(-1 + x)*(1 + x)
```

---

## Actual Output (2026-05-31)

```
-3
{3, 2}
{(1/2)*sqrt(8), (-1/2)*sqrt(8)}
{1, 3, 2}
{1, 2, -1, -2}
x > -1/2
x <= 2
x < 5
{x = 3, y = 2}
(-1 + x)*(-3 + x)*(-2 + x)
(-1 + x)*(-2 + x)*(1 + x)*(2 + x)
(-1 + x)*(1 + x)
```

All outputs match. Demo passes. ✅
