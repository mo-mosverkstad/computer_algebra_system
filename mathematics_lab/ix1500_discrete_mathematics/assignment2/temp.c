#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void factorize(uint64_t n) {
    printf("[");

    int first = 1;

    while (n % 2 == 0) {
        if (!first) printf(", ");
        printf("2");
        first = 0;
        n /= 2;
    }

    for (uint64_t i = 3; i <= n / i; i += 2) {
        while (n % i == 0) {
            if (!first) printf(", ");
            printf("%llu", (unsigned long long)i);
            first = 0;
            n /= i;
        }
    }

    if (n > 1) {
        if (!first) printf(", ");
        printf("%llu", (unsigned long long)n);
    }

    printf("]\n");
}

int main(void) {
    uint64_t numbers[] = {
        100289621329340257ULL,
        882238272068111039ULL,
        182469164307407143ULL,
        799710404000289581ULL,
        901082142384103049ULL
    };

    size_t count = sizeof(numbers) / sizeof(numbers[0]);

    for (size_t i = 0; i < count; i++) {
        printf("%llu: ", (unsigned long long)numbers[i]);
        factorize(numbers[i]);
    }

    return 0;
}
