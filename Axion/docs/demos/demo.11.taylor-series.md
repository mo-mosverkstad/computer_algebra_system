# Demo 11 — Taylor Series & Advanced Calculus

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
taylor(sin(x), x, 0, 5)
taylor(exp(x), x, 0, 4)
taylor(cos(x), x, 0, 4)
taylor(1/(1-x), x, 0, 4)
diff(x^5, x, 3)
diff(x^2*y, x, 2)
trigsimp(sin(a)^2 + cos(a)^2)
trigsimp(sin(x)^2 + cos(x)^2 + 3)
quit
```

---

## Expected Output

```
x + (-1/6)*x^3 + (1/120)*x^5
1 + x + (1/2)*x^2 + (1/6)*x^3 + (1/24)*x^4
1 + (-1/2)*x^2 + (1/24)*x^4
1 + x + x^2 + x^3 + x^4
60*x^2
2*y
1
4
```

---

## Actual Output (2026-05-31)

```
x + (-1/6)*x^3 + (1/120)*x^5
1 + x + (1/2)*x^2 + (1/6)*x^3 + (1/24)*x^4
1 + (-1/2)*x^2 + (1/24)*x^4
1 + x + x^2 + x^3 + x^4
60*x^2
2*y
1
4
```

All outputs match. Demo passes. ✅
