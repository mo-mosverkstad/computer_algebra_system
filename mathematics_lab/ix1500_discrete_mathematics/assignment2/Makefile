CXX = g++
PYTHON ?= python3

PYBIND11_INCLUDE := $(shell $(PYTHON) -c "import pybind11; print(pybind11.get_include())" 2>/dev/null)
PYTHON_INCLUDE   := $(shell $(PYTHON) -c "from sysconfig import get_config_var as g; print(g('INCLUDEPY'))")
EXT_SUFFIX       := $(shell $(PYTHON) -c "from sysconfig import get_config_var as g; print(g('EXT_SUFFIX'))")

CXXFLAGS = -O3 -fPIC -std=c++17 -I$(PYBIND11_INCLUDE) -I$(PYTHON_INCLUDE)

TARGET = factor_ext$(EXT_SUFFIX)
OBJECTS = factor.o factor_shim.o

all: $(TARGET)

# Fail with if pybind11 is not installed
check-deps:
	@$(PYTHON) -c "import pybind11" 2>/dev/null || (echo "pybind11 is missing for $(PYTHON). Install it with: $(PYTHON) -m pip install -r requirements.txt"; exit 1)

$(TARGET): $(OBJECTS)
	$(CXX) -shared -o $@ $^

factor.o: factor.cpp | check-deps
	$(CXX) $(CXXFLAGS) -c $< -o $@

factor_shim.o: factor_shim.cpp | check-deps
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

.PHONY: all clean check-deps
