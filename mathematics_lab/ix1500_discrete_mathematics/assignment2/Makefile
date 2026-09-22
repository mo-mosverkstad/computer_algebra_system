CXX = g++
CXXFLAGS = -O3 -fPIC

TARGET = libfactor.so
OBJECT = factor.o

all: $(TARGET)

$(TARGET): $(OBJECT)
	$(CXX) -shared -o $@ $^

$(OBJECT): factor.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECT) $(TARGET)