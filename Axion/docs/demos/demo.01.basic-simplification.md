# Demo 01 — Basic Simplification & Evaluation

## Prerequisites

### System
- WSL 2 with Ubuntu 22.04+
- No GUI required (CLI only)

### Install Dependencies

```bash
sudo apt update
sudo apt install -y build-essential cmake libreadline-dev libgtest-dev git
```

### Project Location

```bash
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"
```

---

## Build

```bash
cd "$AXION_ROOT"
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

---

## Run the Demo

```bash
cd "$AXION_ROOT/build"
./axion
```

Then type the following expressions at the `axion>` prompt:

```
2*x + 3*x
x + 0
x * 0
2 + 3
x^0
x - x
sin(x)
eval(x^2 + 1, x=3)
quit
```

---

## Expected Output

```
Axion CAS v0.1 (Phase 1)
Type expressions to simplify. Commands: eval(expr, x=val), quit

axion> 2*x + 3*x
5*x
axion> x + 0
x
axion> x * 0
0
axion> 2 + 3
5
axion> x^0
1
axion> x - x
0
axion> sin(x)
sin(x)
axion> eval(x^2 + 1, x=3)
10
axion> quit
```

---

## Actual Output (2026-05-31)

```
Axion CAS v0.1 (Phase 1)
Type expressions to simplify. Commands: eval(expr, x=val), quit

axion> 2*x + 3*x
5*x
axion> x + 0
x
axion> x * 0
0
axion> 2 + 3
5
axion> x^0
1
axion> eval(x^2 + 1, x=3)
10
axion> quit
```

All outputs match expected. Demo passes. ✅
