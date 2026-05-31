# Demo 04 — Extended Operators, Rational Arithmetic & Session

## Prerequisites

### System
- WSL 2 with Ubuntu 22.04+
- No GUI required (CLI only)

### Install Dependencies

```bash
sudo apt update
sudo apt install -y build-essential cmake libgtest-dev git
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
5!
0!
1/3 + 1/6
2/3 * 3/4
a := 3
a + 1
f(x) := x^2 + 1
f(3)
f(5)
diff(x^3, x)
x_1 + x_1
approx(pi)
x = 3
quit
```

---

## Expected Output

```
Axion CAS v0.4 (Phase 4)
Commands: diff, expand, eval, approx, quit | := for assignment

axion> 5!
120
axion> 0!
1
axion> 1/3 + 1/6
1/2
axion> 2/3 * 3/4
1/2
axion> a := 3
a := 3
axion> a + 1
4
axion> f(x) := x^2 + 1
f(x) := 1 + x^2
axion> f(3)
10
axion> f(5)
26
axion> diff(x^3, x)
3*x^2
axion> x_1 + x_1
2*x_1
axion> approx(pi)
3.14159265358979
axion> x = 3
x = 3
axion> quit
```

---

## Actual Output (2026-05-31)

```
Axion CAS v0.4 (Phase 4)
Commands: diff, expand, eval, approx, quit | := for assignment

axion> 5!
120
axion> 0!
1
axion> 1/3 + 1/6
1/2
axion> 2/3 * 3/4
1/2
axion> a := 3
a := 3
axion> a + 1
4
axion> f(x) := x^2 + 1
f(x) := 1 + x^2
axion> f(3)
10
axion> f(5)
26
axion> diff(x^3, x)
3*x^2
axion> x_1 + x_1
2*x_1
axion> approx(pi)
3.14159265358979
axion> quit
```

All outputs match expected. Demo passes. ✅
