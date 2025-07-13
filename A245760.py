import multiprocessing
import numpy
import time
import pandas
import sys
import os
import numba

BLOCKSIZE = 1_000_000
CONCURRENCY = 8

def maximalPersistenceBase(x):
    """Find the absolute persistence and maximal base of x"""
    max_per = 1
    max_base = 2
    base = 2
    # for each base from 2 to x/max_per + 1, calculate persistence
    # x can only achieve persistence >= 2 if base b is less than half of x, because otherwise x would have the form 1d_b
    # which has persistence 1. By induction you can generalize this to show numbers of the form kd_b have persistence at
    # most k, so checking bases where x <= max_per*b is useless
    while base*max_per < x:
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
        if per > max_per:
            max_per = per
            max_base = base
        base += 1
    # cudf doesn't support returning multiple values, and I'm too lazy to go write
    # a numba kernel right now, so just combine both into a 64 bit int
    return max_per * (2 ** 32) + max_base

def top32(x):
    return x >> 32

def bottom32(x):
    return x & (2 ** 32 - 1)

def generate_series(start, end, filename):
    """Generate the absolute persistence and maximal base for a range of integers

    Dumps integer, absolute persistence, and maximal base into a csv called `filename`.
    Covers the range start <= n < end.
    Works incrementally, generating `BLOCKSIZE` rows at a time.
    """
    import cudf
    starttime = time.time()
    blockend = min(start+BLOCKSIZE, end)
    print(f"Calculating persistences and bases for range {start}, {blockend}")
    sr = cudf.Series(range(start, blockend), dtype="uint32")
    pers_and_bases_combined = sr.apply(maximalPersistenceBase)
    print(f"Done, took {time.time() - starttime}s")

    starttime = time.time()
    print("Splitting persistences from bases")
    persistences_and_bases = pandas.DataFrame({
        "Integer": sr.to_pandas(), 
        "Persistence": pers_and_bases_combined.to_pandas().apply(top32),
        "Base": pers_and_bases_combined.to_pandas().apply(bottom32),
    })
    print(f"Done, took {time.time() - starttime}s")

    print("Dumping to file")
    starttime = time.time()
    persistences_and_bases.to_csv(filename, index=False, mode='a', header=not os.path.exists(filename))
    print(f"Done, took {time.time() - starttime}s")
    if blockend < end:
        generate_series(blockend, end, filename)

def generate_series_parallel__impl(start, end, stepsize, offset):
    import cudf
    sr = cudf.Series(range(start+offset, end, stepsize), dtype="uint32")
    pers_and_bases_combined = sr.apply(maximalPersistenceBase)
    return pandas.DataFrame({
        "Integer": sr.to_pandas(), 
        "Persistence": pers_and_bases_combined.to_pandas().apply(top32),
        "Base": pers_and_bases_combined.to_pandas().apply(bottom32),
    })

def generate_series_parallel(start, end, filename, concurrency=CONCURRENCY, blocksize=BLOCKSIZE):
    starttime = time.time()
    blockend = min(start+blocksize*concurrency, end)
    print(f"Calculating persistences and bases for range {start}, {blockend}")
    with multiprocessing.Pool(concurrency) as p:
        inputs = [(start, blockend, concurrency, offset) for offset in range(concurrency)]
        ps_and_bases_list = p.starmap(generate_series_parallel__impl, inputs)
        df = pandas.concat(ps_and_bases_list).sort_values(by="Integer")
    print(f"Done, took {time.time() - starttime}s")
    print("Dumping to file")
    starttime = time.time()
    df.to_csv(filename, index=False, mode='a', header=not os.path.exists(filename))
    print(f"Done, took {time.time() - starttime}s")
    if blockend < end:
        generate_series_parallel(blockend, end, filename, concurrency, blocksize)


if __name__ == "__main__":
    START, END = int(sys.argv[-2]), int(sys.argv[-1])
    generate_series(START, END, f"START-END.csv")
