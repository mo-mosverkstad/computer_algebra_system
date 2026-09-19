import random
import time
from typing import List, Tuple

import enc_util
import util
from assignment2_consts import message


def create_key(bits: int, e: int = 65537) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    prime1 = util.random_prime(bits // 2)
    prime2 = util.random_prime(bits - bits // 2)
    while prime1 == prime2:
        prime2 = util.random_prime(bits - bits // 2)

    n = prime1 * prime2
    totient = (prime1 - 1) * (prime2 - 1)

    if e % 2 == 0:
        e += 1
    while e >= totient or util.gcd(e, totient) != 1:
        e += 2
        if e >= totient:
            e = 3

    d = util.modulo_inverse(e, totient)
    return (n, e), (n, d)


def timeable(function):
    def timed(repeats: int, *args) -> Tuple[float, object]:
        result = None
        start = time.perf_counter()
        for _ in range(repeats):
            result = function(*args)
        return (time.perf_counter() - start) / repeats, result
    return timed


@timeable
def encrypt_message(blocks: List[int], e: int, n: int) -> List[int]:
    return [util.power_modulo(m, e, n) for m in blocks]


@timeable
def decrypt_message(blocks: List[int], d: int, n: int) -> List[int]:
    return [util.power_modulo(c, d, n) for c in blocks]


def simple() -> None:
    (n, e), (_, d) = create_key(128)
    blocks = enc_util.encode_message(message, n)

    _, encrypted = encrypt_message(1, blocks, e, n)
    _, decrypted = decrypt_message(1, encrypted, d, n)
    recovered = enc_util.decode_message(decrypted)

    print("--- 2 Simple ---")
    print(f"n = {n}")
    print(f"e = {e}")
    print(f"d = {d}")
    print(f"characters per block: {enc_util.block_size(n)}")
    print(f"blocks: {len(blocks)}")
    print()
    print(f"plaintext:  {message}")
    print(f"ciphertext: {encrypted}")
    print(f"recovered:  {recovered}")
    print(f"recovered == message?: {recovered == message}")
    print()


def key_scale(repeats: int = 300) -> None:
    print("--- 2.2.1 cost against key size ---")
    print(f"{'size':>8}  {'bits of n':>9}  {'blocks':>6}  {'T_enc (us/block)':>16}  "
          f"{'T_dec (us/block)':>16}  {'d bits':>7}")
    encrypt_rows: List[Tuple[str, float]] = []
    decrypt_rows: List[Tuple[str, float]] = []
    for label, bits in (("small", 32), ("medium", 64), ("large", 128)):
        (n, e), (_, d) = create_key(bits)
        blocks = enc_util.encode_message(message, n)

        encrypt_time, encrypted = encrypt_message(repeats, blocks, e, n)
        decrypt_time, decrypted = decrypt_message(repeats, encrypted, d, n)

        if enc_util.decode_message(decrypted) != message:
            raise ValueError(f"{label} recovered != message")

        encrypt_block = encrypt_time / len(blocks) * 1e6
        decrypt_block = decrypt_time / len(blocks) * 1e6
        encrypt_rows.append((f"{label} ({bits})", encrypt_block))
        decrypt_rows.append((f"{label} ({bits})", decrypt_block))
        print(f"{label:>8}  {n.bit_length():>9}  {len(blocks):>6}  {encrypt_block:>16.2f}  "
              f"{decrypt_block:>16.2f}  {d.bit_length():>7}")
    print()


def exponent_scale(repeats: int = 300) -> None:
    print("--- 2.2.2 cost against exponent size, n fixed ---")
    prime1 = util.random_prime(64)
    prime2 = util.random_prime(64)
    n = prime1 * prime2
    totient = (prime1 - 1) * (prime2 - 1)
    blocks = enc_util.encode_message(message, n)
    candidates = (3, 17, 257, 65537, 16777259, 1099511627791)

    print(f"n = {n} ({n.bit_length()} bits)")
    print(f"{'e':>14}  {'e bits':>6}  {'d bits':>6}  {'T_enc (ms)':>11}  {'T_dec (ms)':>11}")
    chosen_e: List[Tuple[str, float]] = []
    for e in candidates:
        if util.gcd(e, totient) != 1:
            continue
        d = util.modulo_inverse(e, totient)

        encrypt_time, encrypted = encrypt_message(repeats, blocks, e, n)
        decrypt_time, decrypted = decrypt_message(repeats, encrypted, d, n)

        if enc_util.decode_message(decrypted) != message:
            raise ValueError(f"e = {e} recovered != message")
        chosen_e.append((f"e {e.bit_length()} bits", encrypt_time * 1000))
        print(f"{e:>14}  {e.bit_length():>6}  {d.bit_length():>6}  "
              f"{encrypt_time * 1000:>11.3f}  {decrypt_time * 1000:>11.3f}")
    print()

    print(f"{'d':>14}  {'d bits':>6}  {'e bits':>6}  {'T_enc (ms)':>11}  {'T_dec (ms)':>11}")
    chosen_d: List[Tuple[str, float]] = []
    for d in candidates:
        if util.gcd(d, totient) != 1:
            continue
        e = util.modulo_inverse(d, totient)

        encrypt_time, encrypted = encrypt_message(repeats, blocks, e, n)
        decrypt_time, decrypted = decrypt_message(repeats, encrypted, d, n)

        if enc_util.decode_message(decrypted) != message:
            raise ValueError(f"d = {d} recovered != message")
        chosen_d.append((f"d {d.bit_length()} bits", decrypt_time * 1000))
        print(f"{d:>14}  {d.bit_length():>6}  {e.bit_length():>6}  "
              f"{encrypt_time * 1000:>11.3f}  {decrypt_time * 1000:>11.3f}")
    print()


random.seed(20260919)  # reproducible keys
simple()
key_scale()
exponent_scale()