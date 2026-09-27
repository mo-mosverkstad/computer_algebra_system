CXX = g++
PYTHON ?= python3

# Header paths and the ABI-specific suffix (e.g. .cpython-312-x86_64-linux-gnu.so)
# that CPython requires for importable extension modules.
PYBIND11_INCLUDE := $(shell $(PYTHON) -c "import pybind11; print(pybind11.get_include())")
PYTHON_INCLUDE   := $(shell $(PYTHON) -c "from sysconfig import get_config_var as g; print(g('INCLUDEPY'))")
EXT_SUFFIX       := $(shell $(PYTHON) -c "from sysconfig import get_config_var as g; print(g('EXT_SUFFIX'))")

CXXFLAGS = -O3 -fPIC -std=c++17 -I$(PYBIND11_INCLUDE) -I$(PYTHON_INCLUDE)

TARGET = factor_ext$(EXT_SUFFIX)
OBJECTS = factor.o factor_shim.o

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) -shared -o $@ $^

# factor.cpp is used as-is; factor_shim.cpp wraps it with pybind11 bindings.
factor.o: factor.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

factor_shim.o: factor_shim.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
