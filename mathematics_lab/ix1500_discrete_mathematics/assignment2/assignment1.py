from typing import List, Tuple
from assignment1_consts import messages, keys

def gcd(factor1: int, factor2: int) -> int:
    while factor2 != 0:
        factor1, factor2 = factor2, factor1 % factor2
    return factor1

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

def recover_factors(moduli: List[int]) -> List[Tuple[int, int]]:
    """Recover p, q for each modulus.

    Several of the given moduli reuse the same prime, so a pairwise gcd splits
    them immediately and no factoring is needed. Only moduli that share nothing
    with the others fall back to trial division.
    """
    factors: List[Tuple[int, int]] = [(0, 0)] * len(moduli)

    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            shared = gcd(moduli[i], moduli[j])
            if shared > 1:
                factors[i] = (shared, moduli[i] // shared)
                factors[j] = (shared, moduli[j] // shared)

    for i, modulus in enumerate(moduli):
        if factors[i] == (0, 0):
            prime_factors = factorize(modulus)
            factors[i] = (prime_factors[0], prime_factors[1])

    return factors


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

def power_modulo(base: int, exponent: int, modulo: int) -> int:
    result = 1
    base = base % modulo
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulo
        base = (base * base) % modulo
        exponent >>= 1
    return result
    
def decrypt_message(message: List[int], d: int, n: int) -> List[int]:
    return [power_modulo(c, d, n) for c in message]

def decode_block(value: int) -> str:
    width = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(width, "big").decode("latin-1")

def decode_message(plaintext: List[int]) -> str:
    return ''.join(decode_block(value) for value in plaintext)

def is_text(plaintext: List[int]) -> bool:
    return all(
        32 <= ord(value) <= 126 or ord(value) in (9, 10, 13)
        for value in plaintext
    )
    
def small():
    e = 7
    n = 17*23
    totient = 16*22
    c = 42
    d = modulo_inverse(e, totient)
    print("modulo_inverse", d)
    print("result:", power_modulo(c, d, n))
    
key_factors = recover_factors([n for _, n in keys])

matches = {}

key_num = 0
for ((e, n), (factor1, factor2)) in zip(keys, key_factors):
    totient = (factor1 - 1)*(factor2 - 1)
    d = modulo_inverse(e, totient)
    print(f"--- KEY {key_num} --- n = {factor1} * {factor2}, d = {d}")
    message_num = 0
    for message in messages:
        dec = decrypt_message(message, d, n)
        dec_text = decode_message(dec)
        readable = is_text(dec_text)
        print(f"decrypted message: {dec}")
        print(f"decrypted in extended ASCII: {dec_text}")
        print(f"readable?: {readable}")
        print(f"MESSAGE {message_num}: is_text?: {readable}")
        if readable:
            matches[message_num] = (key_num, dec_text)
        message_num += 1
    print()
    key_num += 1

print("--- DECRYPTED MESSAGES ---")
for message_num in range(len(messages)):
    if message_num not in matches:
        print(f"MESSAGE {message_num}: no key produced readable text")
        continue
    key_num, dec_text = matches[message_num]
    e, n = keys[key_num]
    print(f"MESSAGE {message_num} was encrypted with KEY {key_num} (e = {e}, n = {n})")
    print(dec_text.strip())
    print()
