# Demo 08 — Matrices & Vectors

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
[1, 2, 3]
[[1,2],[3,4]]
det([[1,2],[3,4]])
det([[1,2,3],[4,5,6],[7,8,0]])
dot([1,2,3],[4,5,6])
cross([1,0,0],[0,1,0])
transpose([[1,2],[3,4]])
inverse([[1,2],[3,4]])
quit
```

---

## Expected Output

```
[1, 2, 3]
[[1, 2], [3, 4]]
-2
27
32
[0, 0, 1]
[[1, 3], [2, 4]]
[[-2, 1], [3/2, -1/2]]
```

---

## Actual Output (2026-05-31)

```
[1, 2, 3]
[[1, 2], [3, 4]]
-2
27
32
[0, 0, 1]
[[1, 3], [2, 4]]
[[-2, 1], [3/2, -1/2]]
```

All outputs match. Demo passes. ✅
