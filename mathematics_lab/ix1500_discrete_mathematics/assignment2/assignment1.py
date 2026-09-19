import util

from typing import List, Tuple
from assignment1_consts import messages, keys
    
def decrypt_message(message: List[int], d: int, n: int) -> List[int]:
    return [util.power_modulo(c, d, n) for c in message]

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
    d = util.modulo_inverse(e, totient)
    print("modulo_inverse", d)
    print("result:", util.power_modulo(c, d, n))
    
key_factors = util.recover_factors([n for _, n in keys])

matches = {}

key_num = 0
for ((e, n), (factor1, factor2)) in zip(keys, key_factors):
    totient = (factor1 - 1)*(factor2 - 1)
    d = util.modulo_inverse(e, totient)
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
