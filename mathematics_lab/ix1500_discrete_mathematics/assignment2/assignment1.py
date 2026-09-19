from typing import List, Tuple
from assignment1_consts import messages, keys

def factorize(factor_number: int) -> List[int]:
    prime_factors = []
    while factor_number % 2 == 0:
        prime_factors.append(2)
        factor_number = factor_number // 2
        
    i = 3
    while i * i <= factor_number:
        while factor_number % i == 0:
            prime_factors.append(i)
            factor_number = factor_number // i
        i = i + 2
        
    if factor_number > 1:
        prime_factors.append(factor_number)
        
    return prime_factors
    
def gcd_expansion(factor1: int, factor2: int) -> List[Tuple[int, int, int, int]]:
    factor_stack: List[Tuple[int, int, int, int]] = []
    while factor2 != 0:
        quotient = factor1 // factor2
        remainder = factor1 % factor2
        factor_stack.append((factor1, factor2, quotient, remainder))
        factor1 = factor2
        factor2 = remainder
    return factor_stack

    
def gcd_linear_comb(factor1: int, factor2: int) -> Tuple[int, int]:
    factor_stack: List[Tuple[int, int, int, int]] = gcd_expansion(factor1, factor2)
    x, y = 1, 0
    for factor1, factor2, quotient, remainder in reversed(factor_stack):
        # (x, y) in (a, b) = x*a + y*b = x*a + y*(c - q*a) 
        # = x*a + y*c - y*q*a = y*c + (x-y*q)*b = (y, x-y*q) in (c, b)
        x, y = y, x - quotient * y
    return x, y
    
def modulo_inverse(factor: int, modulo: int) -> int:
    inverse, other = gcd_linear_comb(factor, modulo)
    return inverse % modulo
    
def decrypt_message(message: List[int], d: int, n: int) -> List[int]:
    return [pow(c, d, n) for c in message]

def decode_message(plaintext: List[int]) -> str:
    return ''.join(chr(value) for value in plaintext)

def is_text(plaintext: List[int]) -> bool:
    return all(
        32 <= value <= 126 or value in (9, 10, 13)
        for value in plaintext
    )

    
def small():
    e = 7
    n = 17*23
    totient = 16*22
    c = 42
    d = modulo_inverse(e, totient)
    print("modulo_inverse", d)
    print("result:", pow(c, d, n))
    
# key_factors = [factorize(n) for _, n in keys] # too slow
key_factors = [
    [123456791, 812345927],
    [912345671, 967000009],
    [200000033, 912345671],
    [876543211, 912345671],
    [912345671, 987654319],
]

key_num = 0
for ((e, n), (factor1, factor2)) in zip(keys, key_factors):
    totient = (factor1 - 1)*(factor2 - 1)
    d = modulo_inverse(e, totient)
    print(f"--- KEY {key_num} ---")
    message_num = 0
    for message in messages:
        dec = decrypt_message(message, d, n)
        print(f"MESSAGE {message_num}:")
        print(dec)
        print(decode_message(dec))
        print()
        message_num += 1
    print()
    key_num += 1
    
