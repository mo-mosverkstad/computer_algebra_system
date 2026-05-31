# Demo 07 — Symbolic Integration

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
int(x^2, x)
int(x^3, x)
int(sin(x), x)
int(cos(x), x)
int(exp(x), x)
int(1/x, x)
int(3*x^2 + 2*x, x)
int(x^2, x, 0, 1)
int(sin(x), x, 0, pi)
int(cos(x), x, 0, pi)
quit
```

---

## Expected Output

```
(1/3)*x^3
(1/4)*x^4
-cos(x)
sin(x)
exp(x)
ln(abs(x))
x^3 + x^2
1/3
2
0
```

---

## Actual Output (2026-05-31)

```
(1/3)*x^3
(1/4)*x^4
-cos(x)
sin(x)
exp(x)
ln(abs(x))
x^3 + x^2
1/3
2
0
```

All outputs match. Demo passes. ✅
