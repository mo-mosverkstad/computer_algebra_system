"""IX1500 Project 2, task 2.1.2.

Recover the private keys from the given RSA public keys, determine which key
belongs to which ciphertext, and decrypt the hidden messages.

Only basic arithmetic is used: no library implements RSA, modular inverses,
modular exponentiation or factorisation on our behalf.
"""

from typing import Dict, List, Optional, Tuple

from assignment1_consts import messages, keys

BYTE_BITS = 8
BYTE_MASK = (1 << BYTE_BITS) - 1


def factorize(factor_number: int) -> List[int]:
    """Trial division. n = p*q with p, q ~ 30 bits, so this needs ~sqrt(n) steps."""
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
    factor_stack = gcd_expansion(factor1, factor2)
    x, y = 1, 0
    for factor1, factor2, quotient, remainder in reversed(factor_stack):
        # (x, y) in (a, b) = x*a + y*b = x*a + y*(c - q*a)
        # = x*a + y*c - y*q*a = y*c + (x-y*q)*b = (y, x-y*q) in (c, b)
        x, y = y, x - quotient * y
    return x, y


def modulo_inverse(factor: int, modulo: int) -> int:
    inverse, _ = gcd_linear_comb(factor, modulo)
    return inverse % modulo


def modulo_power(base: int, exponent: int, modulo: int) -> int:
    """Square-and-multiply, so we do not lean on pow(b, e, m)."""
    result = 1
    base = base % modulo
    while exponent > 0:
        if exponent & 1:
            result = (result * base) % modulo
        base = (base * base) % modulo
        exponent >>= 1
    return result


def private_exponent(e: int, prime1: int, prime2: int) -> int:
    totient = (prime1 - 1) * (prime2 - 1)
    return modulo_inverse(e, totient)


def decrypt_message(message: List[int], d: int, n: int) -> List[int]:
    return [modulo_power(c, d, n) for c in message]


def unpack_block(block: int) -> List[int]:
    """A plaintext block is several characters packed base-256, most significant first."""
    byte_values: List[int] = []
    while block > 0:
        byte_values.append(block & BYTE_MASK)
        block >>= BYTE_BITS
    byte_values.reverse()
    return byte_values


def unpack_blocks(plaintext: List[int]) -> List[int]:
    byte_values: List[int] = []
    for block in plaintext:
        byte_values.extend(unpack_block(block))
    return byte_values


def is_text(byte_values: List[int]) -> bool:
    return len(byte_values) > 0 and all(
        32 <= value <= 126 or value in (9, 10, 13) for value in byte_values
    )


def decode_message(plaintext: List[int]) -> str:
    return ''.join(chr(value) for value in unpack_blocks(plaintext))


def small() -> None:
    """Task 2.1.1 cross-check: n = 391, e = 7, c = 42."""
    e, n, c = 7, 391, 42
    prime1, prime2 = factorize(n)
    d = private_exponent(e, prime1, prime2)
    print(f"n = {n} = {prime1} * {prime2}")
    print(f"phi(n) = {(prime1 - 1) * (prime2 - 1)}")
    print(f"d = {d}")
    print(f"m = {modulo_power(c, d, n)}")


def match_keys_to_messages() -> Dict[int, Tuple[int, str]]:
    """Try every (key, message) pair and keep the ones that decrypt to printable text.

    Two cheap filters do most of the work:
      1. every ciphertext block must be < n, otherwise that key cannot have produced it;
      2. the decrypted blocks must unpack into printable ASCII.
    """
    key_factors = [factorize(n) for _, n in keys]

    results: Dict[int, Tuple[int, str]] = {}
    for key_index, ((e, n), factors) in enumerate(zip(keys, key_factors)):
        if len(factors) != 2:
            print(f"key {key_index + 1}: unexpected factorisation {factors}")
            continue
        d = private_exponent(e, factors[0], factors[1])
        print(f"key {key_index + 1}: n = {factors[0]} * {factors[1]}, e = {e}, d = {d}")

        for message_index, message in enumerate(messages):
            if any(c >= n for c in message):
                continue  # block out of range: wrong modulus
            plaintext = decrypt_message(message, d, n)
            byte_values = unpack_blocks(plaintext)
            if not is_text(byte_values):
                continue
            text = ''.join(chr(value) for value in byte_values)
            results[message_index] = (key_index, text)

    return results


def main() -> None:
    print("--- 2.1.1 hand exercise, verified by code ---")
    small()

    print()
    print("--- 2.1.2 key recovery ---")
    results = match_keys_to_messages()

    print()
    print("--- 2.1.2 decrypted messages ---")
    for message_index in range(len(messages)):
        match: Optional[Tuple[int, str]] = results.get(message_index)
        if match is None:
            print(f"message {message_index + 1}: no key produced printable text")
            continue
        key_index, text = match
        e, n = keys[key_index]
        print(f"message {message_index + 1} <- key {key_index + 1} (e = {e}, n = {n})")
        print(text.strip())
        print()


if __name__ == '__main__':
    main()
