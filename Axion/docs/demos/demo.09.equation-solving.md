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
factor(x^2 - 5*x + 6, x)
factor(x^2 - 1, x)
quit
```

---

## Expected Output

```
-3
{3, 2}
{(1/2)*sqrt(8), (-1/2)*sqrt(8)}
(-3 + x)*(-2 + x)
(-1 + x)*(1 + x)
```

---

## Actual Output (2026-05-31)

```
-3
{3, 2}
{(1/2)*sqrt(8), (-1/2)*sqrt(8)}
(-3 + x)*(-2 + x)
(-1 + x)*(1 + x)
```

All outputs match. Demo passes. ✅
