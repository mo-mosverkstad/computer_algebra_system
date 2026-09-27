# factor.py
import sys
from pathlib import Path
from typing import List

# Run `make` first to build the pybind11 extension module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import factor_ext


# naive trial division implemented in cpp
def factorize(n: int) -> List[int]:
    if n >= 2**64:
        raise TypeError(f"The factor n {n} is too large to fit as uint64")
    return factor_ext.factorize(n)
