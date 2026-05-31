# Axion CAS — Environment Setup Guide

Target platform: **WSL Ubuntu (no desktop/GUI, CLI only)**

---

## 1. System Requirements

- WSL 2 with Ubuntu 22.04+ (or Ubuntu 24.04)
- At least 2 GB free disk space
- Internet access (for package installation)

---

## 2. Install Build Tools & Dependencies

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install C/C++ compiler toolchain
sudo apt install -y build-essential gcc g++

# Install CMake (build system)
sudo apt install -y cmake

# Install GNU Readline (for REPL line editing and history)
# Replaced by linenoise later, it is not needed.
sudo apt install -y libreadline-dev

# Install Google Test (unit testing framework)
sudo apt install -y libgtest-dev

# Install git (version control)
sudo apt install -y git

# Optional: install gdb for debugging
sudo apt install -y gdb

# Optional: install valgrind for memory leak detection
sudo apt install -y valgrind
```

---

## 3. Verify Installation

```bash
g++ --version        # Should show g++ 11+ or 12+
cmake --version      # Should show 3.16+
```

---

## 4. Build Google Test from Source (if needed)

On some Ubuntu versions, `libgtest-dev` only installs source. Build it:

```bash
cd /usr/src/gtest
sudo cmake .
sudo make
sudo cp lib/*.a /usr/lib/
```

If the above path doesn't exist or libraries are already in `/usr/lib`, skip this step.

---

## 5. Project Setup

```bash
# Set project root (adjust if your path differs)
export AXION_ROOT="/mnt/c/Users/EWANBIN/OneDrive - Ericsson/misc/backup2/Sanders.Wang/github/computer_algebra_system/Axion"

# Enter project directory
cd "$AXION_ROOT"

# Create directory structure
mkdir -p src/core src/frontend src/engine src/modules src/output tests docs
```

---

## 6. CMakeLists.txt (Root)

Create `CMakeLists.txt` in the project root:

```cmake
cmake_minimum_required(VERSION 3.16)
project(Axion LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Main executable
add_executable(axion
    src/main.cpp
    src/core/ast.cpp
    src/core/arena.cpp
    src/frontend/lexer.cpp
    src/frontend/parser.cpp
    src/engine/simplify.cpp
    src/engine/eval.cpp
    src/modules/calculus.cpp
    src/modules/polynomial.cpp
    src/output/printer.cpp
)

target_include_directories(axion PRIVATE src)
target_link_libraries(axion readline)

# Tests
enable_testing()
find_package(GTest REQUIRED)

add_executable(axion_tests
    tests/test_lexer.cpp
    tests/test_parser.cpp
    tests/test_simplify.cpp
    tests/test_calculus.cpp
    tests/test_eval.cpp
    src/core/ast.cpp
    src/core/arena.cpp
    src/frontend/lexer.cpp
    src/frontend/parser.cpp
    src/engine/simplify.cpp
    src/engine/eval.cpp
    src/modules/calculus.cpp
    src/modules/polynomial.cpp
    src/output/printer.cpp
)

target_include_directories(axion_tests PRIVATE src)
target_link_libraries(axion_tests GTest::GTest GTest::Main readline)
add_test(NAME axion_tests COMMAND axion_tests)
```

---

## 7. Build & Run

```bash
cd "$AXION_ROOT"

# Configure
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# Build
cmake --build build

# Run the CAS
./build/axion

# Run tests
cd build && ctest --output-on-failure
```

---

## 8. Development Workflow

```bash
# Edit source files
vim src/core/ast.cpp    # or use any terminal editor (nano, emacs, etc.)

# Rebuild (incremental)
cmake --build build

# Run
./build/axion

# Debug a crash
gdb ./build/axion

# Check for memory leaks
valgrind --leak-check=full ./build/axion
```

---

## 9. Optional Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `clang-format` | Code formatting | `sudo apt install clang-format` |
| `clang-tidy` | Static analysis | `sudo apt install clang-tidy` |
| `ccache` | Faster rebuilds | `sudo apt install ccache` |
| `bear` | Generate compile_commands.json | `sudo apt install bear` |

To generate `compile_commands.json` (useful for editors/LSP):

```bash
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

---

## 10. Summary of Dependencies

| Dependency | Package | Purpose |
|-----------|---------|---------|
| GCC/G++ | `build-essential` | C/C++ compiler |
| CMake | `cmake` | Build system |
| GNU Readline | `libreadline-dev` | REPL line editing, history, tab completion, replaced by Linenoise |
| Google Test | `libgtest-dev` | Unit testing |
| Git | `git` | Version control |
| Linenoise | bundled (`third_party/`) | REPL line editing, history |


[DEPRECATED]: All dependencies are available from the default Ubuntu APT repositories. No third-party PPAs or manual compilation required (except possibly GTest on older Ubuntu).

All dependencies are available from the default Ubuntu APT repositories. Linenoise is bundled in the source tree — no external installation needed.
