# Demo 06 — Limits with L'Hôpital's Rule

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
lim(x^2, x, 3)
lim((x^2 - 1)/(x - 1), x, 1)
lim(sin(x)/x, x, 0)
lim((x^3 - 8)/(x - 2), x, 2)
lim(x + 1, x, 5)
quit
```

---

## Expected Output

```
9
2
1
12
6
```

---

## Actual Output (2026-05-31)

```
9
2
1
12
6
```

All outputs match. Demo passes. ✅
