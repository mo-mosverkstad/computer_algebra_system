#include <cstdint>
#include <iostream>
#include <vector>
#include <stdint.h>
#include <cmath>

std::vector<uint64_t> generate_primes(uint64_t bound){
    std::vector<uint64_t> primes;
    primes.reserve(static_cast<int>(bound / std::log(bound) * 1.1));
    for (uint64_t i = 2; i < bound; i++){
        bool is_prime = true;
        for (uint64_t prime : primes){
            if (i % prime == 0){
                is_prime = false;
                break;
            }
        }
        if (is_prime) primes.push_back(i);
    }
    return primes;
}

template <typename T> void print_vec(std::vector<T> vec){
    std::cout << "[";
    if (vec.size() > 0){
        std::cout << vec.at(0);
        for (int i = 1; i < vec.size(); i++){
            std::cout << ", " << vec.at(i);
        }
    }
    std::cout << "]" << std::endl;
}

int main() {
    std::vector<uint64_t> v = generate_primes(10000);
    std::vector<int> slice(v.end() - 15, v.end());
    print_vec(slice);
    return 0;
}
