import random
from sympy import isprime


def generate_prime(bits: int = 64) -> int:
    lower = 1 << (bits - 1)
    upper = (1 << bits) - 1

    while True:
        candidate = random.randrange(lower, upper) | 1

        if isprime(candidate):
            return candidate


p = generate_prime()
q = generate_prime()

while p == q:
    q = generate_prime()

print("p =", p)
print("q =", q)