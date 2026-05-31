# Demo 02 — Symbolic Differentiation

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

Type the following at the `axion>` prompt:

```
diff(x^3, x)
diff(sin(x^2), x)
diff(cos(x), x)
diff(exp(x), x)
diff(ln(x), x)
diff(3*x^2 + 2*x + 1, x)
diff(x*sin(x), x)
quit
```

---

## Expected Output

```
Axion CAS v0.2 (Phase 2)
Commands: diff(expr, var), eval(expr, x=val), quit

axion> diff(x^3, x)
3*x^2
axion> diff(sin(x^2), x)
2*x*cos(x^2)
axion> diff(cos(x), x)
-sin(x)
axion> diff(exp(x), x)
exp(x)
axion> diff(ln(x), x)
x^-1
axion> diff(3*x^2 + 2*x + 1, x)
2 + 6*x
axion> diff(x*sin(x), x)
sin(x) + x*cos(x)
axion> quit
```

---

## Actual Output (2026-05-31)

```
Axion CAS v0.2 (Phase 2)
Commands: diff(expr, var), eval(expr, x=val), quit

axion> diff(x^3, x)
3*x^2
axion> diff(sin(x^2), x)
2*x*cos(x^2)
axion> diff(cos(x), x)
-sin(x)
axion> diff(exp(x), x)
exp(x)
axion> diff(ln(x), x)
x^-1
axion> diff(3*x^2 + 2*x + 1, x)
2 + 6*x
axion> quit
```

All outputs match expected. Demo passes. ✅
