"""Tools for finding possible record breakers in different bases"""
import sys
#from sympy import divisors
from base_families import BASE_FAMILIES
import itertools
import operator
import functools
#import numba
import numpy as np
#from numba.core import types
#from numba.typed import List
import more_itertools
from toolz import itertoolz
from collections import defaultdict

#@numba.jit
def divisors(n):
    ret = [1]
    i = 2
    while i*i <= n:
        if n % i == 0:
            ret.append(i)
        i = i+1
    return ret

#@numba.jit
def can_be_transformed(first, second, base):
    if first > second:
        tmp = first
        first = second
        second = tmp
    # if any divisors of first * second are less than first,
    # and big / divisor < base,
    # then it can be transformed
    for divisor in divisors(first*second):
        if divisor < first and first*second // divisor < base:
            return True
    return False

# What power to check against
MAX_POWER = 5

def can_have_one(digit: int, base: int) -> bool:
    """Whether record breakers can have one of this digit"""
    if digit < 2:
        return False
    return True

def digit_value(digit: int, base: int) -> int:
    """Number of this digit that can appear in record breakers

    Either 0, 1, ..., MAX_POWER or -1 (meaning infinite)
    """
    if not can_have_one(digit, base):
        return 0
    if digit**2 <= base:
        return 1
    if can_be_transformed(digit, digit, base):
        return 1
    for i in range(1, MAX_POWER + 1):
        if digit ** i % base == 0:
            return i - 1
    return -1

def is_valid(ones: list[int], stars: list[int], base: int) -> bool:
    """Filter out invalid sequences"""
    if not len(ones + stars):
        return False
    for combination in itertools.combinations(ones, 2):
        if functools.reduce(operator.mul, combination) < base:
            return False
        first, second = list(combination)[0], list(combination)[1]
        if can_be_transformed(first, second, base):
            return False
    return True

def get_valid_stars(ones: list[int], stars: list[int], base: int) -> list[int]:
    """Get the maximal string of digits that can appear any number of times
    """
    onesprod = 1
    for i in ones:
        onesprod *= i
    ret = [1]
    ret = ret[1:]
    for d in stars:
        should_continue = False
        if onesprod * (d ** MAX_POWER) % base == 0:
            continue
        for o in ones:
            if can_be_transformed(o, d, base):
                should_continue = True
        if should_continue:
            continue
        ret.append(d)
    for i in range(1, len(ret) + 1):
        combinations = itertools.combinations(ret, i)
        for combo in combinations:
            if is_good_combo(combo, base, stars, onesprod, ones):
                yield combo

#@numba.njit('(int64, int64)')
def combCount(n, r):
    if r < 0:
        return 0
    res = 1
    if r > n - r:
        r = n - r
    for i in range(r):
        res *= (n - i)
        res //= (i + 1)
    return res

#@numba.njit(inline='always')
def genComb_generic(arr, r):
    n = arr.size
    out = np.empty((combCount(n, r), r), dtype=arr.dtype)
    idx = np.empty(r, dtype=np.int32)

    for i in range(r):
        idx[i] = i

    i = r - 1

    cur = 0
    while idx[0] < n - r + 1:
        while i > 0 and idx[i] == n - r + i:
            i -= 1
        for j in range(r):
            out[cur, j] = arr[idx[j]]
        cur += 1
        idx[i] += 1
        while i < r - 1:
            idx[i + 1] = idx[i] + 1
            i += 1
    return out

def is_good_combo(combination, base, stars, onesprod, ones):
    # if it is divisible by base, will end in zero
    comboprod = 1
    for i in combination:
        comboprod *= i
    if (comboprod ** MAX_POWER) * onesprod % base == 0:
        return False

    # if we can add any stars without making it a bad combo,
    # is not maximal
    for d in stars:
        should_continue = False
        if d not in combination:
            for o in ones:
                if can_be_transformed(o, d, base):
                    should_continue = True
            if should_continue:
                continue 
            if comboprod * onesprod * (d ** MAX_POWER) % base != 0:
                return False
    return True

def max_single_element(l: list[int]) -> int:
    """Count how many of each element are in l and return the max"""
    last = 0
    seen = 0
    ret = 0
    for i in l:
        if i == last:
            seen += 1
        else:
            if seen > ret:
                ret = seen
            seen = 0
            last = i
    return ret

@functools.cache
def all_valid_strings(base: int) -> list[int]:
    """All possible bitstrings for record breakers in the base

    Assumes record breakers can have 0, 1 or infinitely many of each digit
    Does not yet consider complex transformations to make the number smaller
    e.g. 44 -> 28
    """
    ret = []
    digit_values = {}
    ones = []
    twos = []
    for digit in range(base):
        digit_values[digit] = digit_value(digit, base)
        if digit_values[digit] == -1:
            twos.append(digit)
        else:
            for i in range(digit_values[digit]):
                ones.append(digit)

    for i in range(0, len(ones) + 1):
        # TODO: make this faster
        ones_combos = set((s for s in itertools.combinations(ones, i)))
        for ones_combo in ones_combos:
            if any(can_be_transformed(o, p, base) for o, p in itertools.combinations(ones_combo, 2)):
                continue
            if i > MAX_POWER:
                if max_single_element(ones_combo) > MAX_POWER:
                    continue
            star_combos = list(get_valid_stars(ones_combo, twos, base))
            for star_combo in star_combos:
                ret.append((list(ones_combo), list(star_combo)))
    return ret

def lists_to_string(ones, stars):
    digit_to_string = {}
    for one in set(ones):
        digit_to_string[one] = " ".join([str(one)]*ones.count(one))
    for star in stars:
        digit_to_string[star] = str(star) + "*"
    sorted_digit_strings = []
    for digit in sorted(digit_to_string.keys()):
        sorted_digit_strings.append(digit_to_string[digit])
    return " ".join(sorted_digit_strings)

def lists_to_string__multistar(ones, stars):
    ones_str = " ".join(str(one) for one in ones)
    star_strs = []
    for star in stars:
        star_strs.append("(" + " ".join(str(s) for s in star) + ")*")
    stars_str = " ".join(star_strs)
    return " ".join((ones_str, stars_str))

def possible_record_breakers(base: int) -> list[int]:
    """Get all valid strings"""
    ret = []
    for ones, stars in all_valid_strings(base):
        if not is_valid(ones, stars, base):
            continue
        ones = [int(i) for i in ones]
        stars = [int(i) for i in stars]
        ret.append((ones, stars))
    return ret

def print_possible_record_breakers(base: int) -> None:
    for s in possible_record_breakers(base):
        print(lists_to_string(*s))

def generate_from(ones, stars) -> list[int]:
    prefix = [int(i) for i in ones]
    for i in range(10_000):
        for suffix in itertools.combinations_with_replacement(stars, i):
            yield prefix + [int(j) for j in suffix]

def generate_from__multistar(ones, stars) -> list[int]:
    prefix = [int(i) for i in ones]
    for i in range(10_000):
        for suffix in itertools.combinations_with_replacement(stars, i):
            yield prefix + [int(j) for l in suffix for j in l]

def get_persistence(num: int, base: int) -> int:
    persistence = 0
    while num >= base:
        num = digit_multiply(num, base)
        persistence += 1
    return persistence

def digit_multiply(num: int, base: int) -> int:
    ret = 1
    while num > 1:
        ret *= num % base
        num = num // base
    return ret

def list_to_int(num: list[int], base: int) -> int:
    ret = 0
    for power, digit in enumerate(reversed(list(num))):
        ret += digit * base ** power
    return ret

def sort_key(l):
    return 1_000_000*len(l) + sum(l)

def get_ring_size(star, base, onesmod):
    ret = 1
    val = onesmod
    seen = set()
    while val not in seen:
        seen.add(val)
        val = (val * star) % base
        ret += 1
    return ret

def expand_string(ones, stars, base, max_power):
    # If n % b^k < b^(k-1), then kth digit of n will be zero
    # so n can't have persistence > 2

    ones_mod = functools.reduce(operator.mul, ones, 1) % base ** max_power
    valid_ones = []

    if len(stars) == 1:
        # look for string lengths where modulus is large enough
        star = stars[0]  
        size = get_ring_size(star, base ** max_power, ones_mod)
        for i in range(size):
            if all(ones_mod * star ** i % base ** power > base ** (power - 1) for power in range(2, max_power + 1)):
                valid_ones.append([star]*i)
        minstar = [star] * size
        return [(ones + s, [minstar]) for s in valid_ones]

    # More than 1 star
    ret = []
    largest = max(get_ring_size(star, base ** max_power, n) for n in range(base ** max_power) for star in stars) 
    for i in range(largest):
        for combo in itertools.combinations_with_replacement(stars, i):
            combomod = ones_mod * functools.reduce(operator.mul, combo, 1) % base ** max_power
            if any(combomod % base ** power < base ** (power - 1) for power in range(2, max_power + 1)):
                continue
            minstars = []
            should_continue = False
            for star in stars:
                size = get_ring_size(star, base ** max_power, combomod)
                if combo.count(star) > size:
                    should_continue = True
                minstars.append([star] * size)
            if should_continue:
                continue
            ret.append((ones + list(combo), minstars))
    return ret

def expand_strings(strings, base, max_power):
    try:
        ret = []
        for string in strings:
            ret.extend(expand_string(string[0], string[1], base, max_power))
        return ret
    except:
        import pdb;pdb.post_mortem()

def find_record_breakers__multistar(base: int, max_power: int):
    possible_strings = expand_strings(BASE_FAMILIES[base], base, max_power)
    max_persistence = 0
    last = 0
    max_length = 0
    printed_length_last = False
    print("Possible record breaker strings")
    [print(lists_to_string__multistar(possible[0], possible[1])) for possible in possible_strings]
    print("Number of strings:", len(possible_strings))
    grouped_iterator = itertoolz.merge_sorted(*(
        generate_from__multistar(possible[0], possible[1])
        for possible in possible_strings
    ), key=sort_key)
    for l in grouped_iterator:
        if (persistence := get_persistence(list_to_int(l, base), base)) > max_persistence:
            max_persistence = persistence
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
            last = list_to_int(sorted(list(l)), base)
        if (persistence == max_persistence) and (i := list_to_int(sorted(list(l)), base)) < last:
            last = i
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
        if len(l) > max_length:
            max_length = len(l)
            printed_length_last = True
            print(f"Searching strings of length: {max_length}", end='\r')
#        if len(l) < max_length:
#            print("Borken")

def find_record_breakers(base: int) -> None:
    max_persistence = 0
    last = 0
    max_length = 0
    printed_length_last = False
    possible_strings = list(
        a for a in all_valid_strings(base)
        if is_valid(a[0], a[1], base)
    )
    print("Possible record breaker strings")
    [print(lists_to_string(possible[0], possible[1])) for possible in possible_strings]
    grouped_iterator = itertoolz.merge_sorted(*(
        generate_from(possible[0], possible[1])
        for possible in possible_strings
    ), key=sort_key)
    for l in grouped_iterator:
        if (persistence := get_persistence(list_to_int(l, base), base)) > max_persistence:
            max_persistence = persistence
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
            last = list_to_int(sorted(list(l)), base)
        if (persistence == max_persistence) and (i := list_to_int(sorted(list(l)), base)) < last:
            last = i
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
        if len(l) > max_length:
            max_length = len(l)
            printed_length_last = True
            print(f"Searching strings of length: {max_length}", end='\r')
        if len(l) < max_length:
            print("Borken")

def find_record_breakers__precomputed(base: int) -> None:
    max_persistence = 0
    last = 0
    max_length = 0
    possible_strings = BASE_FAMILIES[base]
    printed_length_last = False
    print("Possible record breaker strings")
    [print(lists_to_string(possible[0], possible[1])) for possible in possible_strings]
    grouped_iterator = itertoolz.merge_sorted(*(
        generate_from(possible[0], possible[1])
        for possible in possible_strings
    ), key=sort_key)
    for l in grouped_iterator:
        if (persistence := get_persistence(list_to_int(l, base), base)) > max_persistence:
            max_persistence = persistence
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
            last = list_to_int(sorted(list(l)), base)
        if (persistence == max_persistence) and (i := list_to_int(sorted(list(l)), base)) < last:
            last = i
            if printed_length_last:
                print("\n", end="")
            printed_length_last = False
            print(f"{persistence}: {list_to_int(sorted(list(l)), base)} {sorted(list(l))}")
        if len(l) > max_length:
            max_length = len(l)
            printed_length_last = True
            print(f"Searching strings of length: {max_length}", end='\r')
        if len(l) < max_length:
            print("Borken")

if __name__ == "__main__":
    print(find_record_breakers(int(sys.argv[-1])))
