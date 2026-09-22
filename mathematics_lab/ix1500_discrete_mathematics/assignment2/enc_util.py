from typing import List

BYTE_BITS = 8
BYTE_MASK = (1 << BYTE_BITS) - 1


def block_size(modulo: int) -> int:
    size = 0
    limit = 1
    while limit * (BYTE_MASK + 1) <= modulo:
        limit *= BYTE_MASK + 1
        size += 1
    return size


def encode_message(message: str, modulo: int) -> List[int]:
    size = block_size(modulo)
    if size < 1:
        raise ValueError(f"modulus {modulo} is too small to hold one character")

    byte_values = [ord(character) for character in message]
    blocks: List[int] = []
    for start in range(0, len(byte_values), size):
        block = 0
        for value in byte_values[start:start + size]:
            block = (block << BYTE_BITS) | value
        blocks.append(block)
    return blocks


def decode_block(block: int) -> List[int]:
    byte_values: List[int] = []
    while block > 0:
        byte_values.append(block & BYTE_MASK)
        block >>= BYTE_BITS
    byte_values.reverse()
    return byte_values


def decode_message(blocks: List[int]) -> str:
    characters: List[str] = []
    for block in blocks:
        characters.extend(chr(value) for value in decode_block(block))
    return ''.join(characters)

def is_text(plaintext: List[int]) -> bool:
    return all(
        32 <= ord(value) <= 126 or ord(value) in (9, 10, 13)
        for value in plaintext
    )