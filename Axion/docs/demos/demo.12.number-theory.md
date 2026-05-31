# Demo 12 — Number Theory & Discrete Math

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
gcd(48, 18)
lcm(12, 8)
binom(10, 3)
binom(5, 2)
perm(5, 3)
mod(17, 5)
mod(-3, 7)
powmod(2, 10, 1000)
powmod(3, 100, 97)
factorize(360)
factorize(97)
factorize(1000000)
quit
```

---

## Expected Output

```
6
24
120
10
60
2
4
24
35
2^3 * 3^2 * 5
97
2^6 * 5^6
```

---

## Actual Output (2026-05-31)

```
6
24
120
10
60
2
4
24
35
2^3 * 3^2 * 5
97
2^6 * 5^6
```

All outputs match. Demo passes. ✅
