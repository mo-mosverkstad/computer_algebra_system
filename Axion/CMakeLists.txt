cmake_minimum_required(VERSION 3.16)
project(Axion LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_compile_options(-Wall -Wextra -Werror)

# Linenoise (C library)
add_library(linenoise STATIC third_party/linenoise/linenoise.c)
target_include_directories(linenoise PUBLIC third_party/linenoise)
set_target_properties(linenoise PROPERTIES
    C_STANDARD 99
    COMPILE_OPTIONS "-Wno-all;-Wno-extra"
)

set(AXION_SOURCES
    src/core/arena.cpp
    src/core/ast.cpp
    src/frontend/lexer.cpp
    src/frontend/parser.cpp
    src/engine/simplify.cpp
    src/engine/eval.cpp
    src/modules/calculus.cpp
    src/modules/polynomial.cpp
    src/modules/series.cpp
    src/modules/limits.cpp
    src/modules/integration.cpp
    src/modules/matrix.cpp
    src/modules/solver.cpp
    src/output/printer.cpp
)

add_executable(axion src/main.cpp ${AXION_SOURCES})
target_include_directories(axion PRIVATE src)
target_link_libraries(axion linenoise)

enable_testing()
find_package(GTest REQUIRED)

add_executable(axion_tests
    tests/test_main.cpp
    tests/test_lexer.cpp
    tests/test_parser.cpp
    tests/test_simplify.cpp
    tests/test_calculus.cpp
    tests/test_polynomial.cpp
    tests/test_series.cpp
    tests/test_eval.cpp
    ${AXION_SOURCES}
)
target_include_directories(axion_tests PRIVATE src)
target_link_libraries(axion_tests GTest::GTest GTest::Main)
add_test(NAME axion_tests COMMAND axion_tests)
