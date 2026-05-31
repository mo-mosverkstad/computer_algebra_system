# Demo 10 — Pattern Matching & Rewrite Rules

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
rule(sin(_x)^2 + cos(_x)^2, 1)
sin(a)^2 + cos(a)^2
sin(t)^2 + cos(t)^2
rule(log(_x) + log(_y), log(_x * _y))
log(2) + log(3)
log(a) + log(b)
rules()
quit
```

---

## Expected Output

```
Rule defined: sin(_x)^2 + cos(_x)^2 → 1
1
1
Rule defined: log(_x) + log(_y) → log(_x*_y)
log(6)
log(a*b)
1: sin(_x)^2 + cos(_x)^2 → 1
2: log(_x) + log(_y) → log(_x*_y)
```

---

## Actual Output (2026-05-31)

```
Rule defined: sin(_x)^2 + cos(_x)^2 → 1
1
1
Rule defined: log(_x) + log(_y) → log(_x*_y)
log(6)
log(a*b)
1: sin(_x)^2 + cos(_x)^2 → 1
2: log(_x) + log(_y) → log(_x*_y)
```

All outputs match. Demo passes. ✅
