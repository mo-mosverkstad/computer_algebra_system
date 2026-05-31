# Demo 05 — Summation, Product & Collect

## Prerequisites

### System
- WSL 2 with Ubuntu 22.04+

### Install & Build

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
cd "$AXION_ROOT/build"
./axion
```

```
sum(k, k, 1, 10)
sum(k^2, k, 1, 5)
prod(k, k, 1, 5)
prod(k+1, k, 0, 4)
sum(1/k, k, 1, 4)
collect(x^2 + 2*x + 3*x + 1, x)
quit
```

---

## Expected Output

```
55
55
120
120
25/12
1 + 5*x + x^2
```

---

## Actual Output (2026-05-31)

```
55
55
120
120
25/12
1 + 5*x + x^2
```

All outputs match. Demo passes. ✅
