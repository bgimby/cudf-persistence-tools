"""Calculate terms in the sequence A330152 using GPU acceleration"""
import time
import sys

import numpy
import pandas
import numba
import cudf

# Adjust to control how many numbers will be checked per block
BLOCK_SIZE = 1_000_000

def maximalPersistenceBase(x, last_per):
    base = 2
    max_per = 0 
    max_base = 2
    # for each base from 2 to x/last_per, calculate persistence
    # x can only achieve persistence >= 2 if base b is less than half of x, because otherwise x would have the form 1d_b
    # which has persistence 1. You can generalize this to show numbers of the form kd_b have persistence at
    # most k, so checking bases where x >= base*last_per is useless
    while base*last_per < x:
        per = 0
        # calculate persistence in base
        y = x
        while y >= base:
            # multiply digits in base
            out = 1
            nextdiv = y
            while nextdiv > 0:
                out *= nextdiv % base
                nextdiv = nextdiv // base
            y = out
            per += 1
        if per > last_per and per > max_per:
            # cudf doesn't support returning multiple values, and I'm too lazy to go write
            # a numba kernel right now, so just combine both into a 64 bit int
            max_per = per
            max_base = base
        base += 1

    if max_per > last_per:
        return max_per * (2 ** 32) + max_base
    return 0

def top32(x):
    return x >> 32

def bottom32(x):
    return x & (2 ** 32 - 1)

def next_term(start, last_persistence):
    last_start = start
    while True:
        starttime = time.time()
        #print(f"Calculating persistences for {last_start} to {last_start + BLOCK_SIZE}")
        possibilities = cudf.Series(range(last_start, last_start + BLOCK_SIZE), dtype="uint32")
        last_start = last_start + BLOCK_SIZE
        pers_and_bases_combined = possibilities.apply(maximalPersistenceBase, args=(last_persistence,))
        nonzero = pers_and_bases_combined[pers_and_bases_combined > 0]
        nonzero_ints = possibilities[pers_and_bases_combined > 0]
        #print(f"Done, took {time.time() - starttime}s")

        persistences_and_bases = pandas.DataFrame({
            "Integer": nonzero_ints.to_pandas(), 
            "Persistence": nonzero.to_pandas().apply(top32),
            "Base": nonzero.to_pandas().apply(bottom32),
        }).dropna().sort_values(by="Integer")
        while len(persistences_and_bases) > 0:
            yield persistences_and_bases.iloc[0]
            last_persistence = persistences_and_bases.iloc[0]["Persistence"]
            persistences_and_bases = persistences_and_bases[persistences_and_bases["Persistence"] > last_persistence]

def generate_series(num_terms):
    # CSV header
    print("Persistence,Integer,Base")
    # Start with 0 to match OEIS series
    print("0,0,0")
    last_term = 1
    last_persistence = 1
    last_base = 2
    iterator = iter(next_term(last_term, last_persistence))
    for i in range(num_terms):
        print(f"{last_persistence},{last_term},{last_base}")
        next_term_row = next(iterator)
        last_term, last_persistence, last_base = next_term_row["Integer"], next_term_row["Persistence"], next_term_row["Base"]
    print(f"{last_persistence},{last_term},{last_base}")

if __name__ == "__main__":
    generate_series(10000)
