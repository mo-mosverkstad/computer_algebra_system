import sys

N = 60               # U = {1, ..., N}
K = 11               # |S|
TARGET_SUM = 330     # required sum
N_EVEN = 5           # required |E(S)|
N_ODD = K - N_EVEN   # hence |O(S)| = 6
DIVISOR = [(2, 6), (3, 3), (5, 2), (7, 1)]

# valuation(120, 2)
# 3
# 120 contains 2**3
def valuation(n, p):
    """v_p(n): retrieve the exponent of the prime p in n."""
    e = 0
    while n % p == 0:
        n //= p
        e += 1
    return e

# needed = [6, 3, 2, 1]
# vals = [9, 1, 4, 0]
# cap_vector(vals, needed) -> (6, 1, 2, 0)
# 6<9:6, 3<1:else 1, ...
def cap_vector(vals, needed):
    """Valuations capped at the value of needed"""
    out = []
    for t in range(len(needed)):
        out.append(vals[t] if vals[t] < needed[t] else needed[t])
    return tuple(out)

# needed=[6, 2, 1, 0]
# all_capped_states(needed)
# [(0, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 1, 1, 0), (0, 2, 0, 0), (0, 2, 1, 0), 
# === could be skipped ===
# (1, 0, 0, 0), (1, 0, 1, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 2, 0, 0), (1, 2, 1, 0), (2, 0, 0, 0), (2, 0, 1, 0), (2, 1, 0, 0), (2, 1, 1, 0), (2, 2, 0, 0), (2, 2, 1, 0), (3, 0, 0, 0), (3, 0, 1, 0), (3, 1, 0, 0), (3, 1, 1, 0), (3, 2, 0, 0), (3, 2, 1, 0), (4, 0, 0, 0), (4, 0, 1, 0), (4, 1, 0, 0), (4, 1, 1, 0), (4, 2, 0, 0), (4, 2, 1, 0), (5, 0, 0, 0), (5, 0, 1, 0), (5, 1, 0, 0), (5, 1, 1, 0), (5, 2, 0, 0), (5, 2, 1, 0), 
# === could be skipped ===
# (6, 0, 0, 0), (6, 0, 1, 0), (6, 1, 0, 0), (6, 1, 1, 0), (6, 2, 0, 0), (6, 2, 1, 0)]
def all_capped_states(needed):
    """Every capped valuation vector, enumerated once."""
    states = [()]
    for t in range(len(needed)):
        states = [s + (v,) for s in states for v in range(needed[t] + 1)]
    return states


# sum_bounds([i for i in range(2, 61, 2)], 5)
# (30, 280)
# min = 2+4+6+8+10 = 30
# max = 52+54+56+58+60 = 280
#
# sum_bounds([i for i in range(1, 61, 2)], 6)
# (36, 324)
def sum_bounds(pool, size):
    """(smallest, largest) sum of a `size`-subset of the ascending `pool`."""
    lo = hi = 0
    for i in range(size):
        lo += pool[i]
        hi += pool[len(pool) - 1 - i]
    return lo, hi
    

def combinations_with_sum(lower_bound, upper_bound, size, target_sum):
    """Retrieves all possible subset combinations that fulfills the target_sum with size
    The elements must exist inside the set {lower_bound to upper_bound}
    """
    if size == 0: return [[]] if target_sum == 0 else []

    # check size
    if (upper_bound - lower_bound) // 2 + 1 < size: return []

    # check parity
    if (target_sum - size * lower_bound) % 2 != 0: return []

    # is target_sum inside the reachable window [min_sum, max_sum], using arithmetic sum
    if target_sum < size * lower_bound + size * (size - 1): return []
    if target_sum > size * upper_bound - size * (size - 1): return []

    # restrict the window by calculating highest possible starting point
    highest_start = (target_sum - size * (size - 1)) // size
    if highest_start > upper_bound:
        highest_start = upper_bound

    # restrict the window by calculating lowest possible starting point
    max_rest = (size - 1) * upper_bound - (size - 1) * (size - 2)
    lowest_start = target_sum - max_rest
    start = lower_bound
    if lowest_start > start:
        start += ((lowest_start - start + 1) // 2) * 2

    result = []
    # looping over in a narrower window [start, highest_start] instead of [lower_bound, upper_bound]
    for value in range(start, highest_start + 1, 2):
        for rest in combinations_with_sum(value + 2, upper_bound, size - 1,
                                          target_sum - value):
            result.append([value] + rest)
    return result

def calculate_key(sum_array, primes):
    target_key = [0] * len(primes)
    for n in sum_array:
        for prime_index in range(len(primes)):
            prime = primes[prime_index]
            target_key[prime_index] += valuation(n, prime)
    return target_key

def enumerate_half(pool_lower_bound, pool_upper_bound, subset_size, primes, needed, low, high):
    buckets = {}
    target_range = range(low, high+1, 1)
    target_range_size = len(target_range)
    
    for target in target_range:
        print(round((target-low)/target_range_size * 100, 2))
        sys.stdout.write("\033[F")
        for target_result in combinations_with_sum(pool_lower_bound, pool_upper_bound, subset_size, target):
            target_key = (target,) + cap_vector(calculate_key(target_result, primes), needed)
            entry = buckets.get(target_key, None)
            if entry is None:
                buckets[target_key] = [1, [target_result]]
            else:
                entry[0] += 1
                entry[1].append(target_result)
    return buckets
    

primes = [2, 3, 5, 7]
needed = [6, 3, 2, 1]
even_buckets = enumerate_half(2, 60, 5, primes, needed, 30, 280)
odd_buckets = enumerate_half(1, 59, 6, primes, needed, 50, 300)

def alter_tuple_index(tuple_obj, index, value):
    return tuple(value if i == index else tuple_obj[i] for i in range(len(tuple_obj)))

def loop_over_traversal(buckets, needed, traverse_key, traverse_index = 0, count = 0):
    start = traverse_key[traverse_index + 1]
    end = needed[traverse_index]
    for offset in range(start, end + 1):
        traverse_key = alter_tuple_index(traverse_key, traverse_index + 1, offset) # similar to traverse_key[traverse_index + 1] = offset
        if traverse_index == len(needed) - 1:
            entry = buckets.get(traverse_key)
            if entry is not None:
                count = count + entry[0]
        else:
            count = loop_over_traversal(buckets, needed, traverse_key, traverse_index + 1, count)
    traverse_key = alter_tuple_index(traverse_key, traverse_index + 1, start) # traverse_key[traverse_index + 1] = start
    return count

count = 0
for (even_key, even_value) in even_buckets.items():
    self_entry = even_buckets.get(even_key)
    if self_entry is None: continue
    self_count = self_entry[0]
    
    complement_sum = TARGET_SUM - even_key[0]
    complement_prime_exponents = tuple((needed[i-1] - even_key[i]) for i in range(1, len(even_key)))
    complement_key = (complement_sum,) + complement_prime_exponents
    
    complement_count = loop_over_traversal(odd_buckets, needed, complement_key)
    count += complement_count * self_count
    # print(f"even_key = {even_key}, complement_key = {complement_key}, self_entry = {self_entry}, complement_count = {complement_count}")


print(len(even_buckets), len(odd_buckets))
print(f"count = {count}")
# print(odd_bucket_keys)