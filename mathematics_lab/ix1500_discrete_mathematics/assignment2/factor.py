# factor.py
import ctypes
from typing import List

_lib = ctypes.CDLL("./libfactor.so")

_lib.factorize.argtypes = [
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.c_uint64),
    ctypes.c_size_t,
]
_lib.factorize.restype = ctypes.c_size_t

# naive trial division implemented in cpp
def factorize(n: int) -> List[int]:
    if n >= 2**64:
        raise TypeError(f"The factor n {n} is too large to fit as uint64")
    # A uint64 has at most 64 prime factors (all 2s)
    result = (ctypes.c_uint64 * 64)()

    count = _lib.factorize(n, result, 64)

    return list(result[:count])
