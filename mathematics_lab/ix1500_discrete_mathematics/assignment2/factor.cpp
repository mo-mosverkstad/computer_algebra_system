// factor.cpp
#include <cstdint>
#include <cstddef>

extern "C" {

// naive trial division
size_t factorize(uint64_t n, uint64_t* output, size_t capacity) {
    size_t count = 0;

    while (n % 2 == 0) {
        if (count < capacity)
            output[count] = 2;
        ++count;
        n /= 2;
    }

    for (uint64_t i = 3; i <= n / i; i += 2) {
        while (n % i == 0) {
            if (count < capacity)
                output[count] = i;
            ++count;
            n /= i;
        }
    }

    if (n > 1) {
        if (count < capacity)
            output[count] = n;
        ++count;
    }

    return count;
}

}
