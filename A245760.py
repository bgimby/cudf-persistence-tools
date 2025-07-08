import cudf
import numpy
import time
import pandas
import sys
import numba

START, END = int(sys.argv[-2]), int(sys.argv[-1])

def maximalPersistenceBase(x):
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

starttime = time.time()
print("Calculating persistences and bases")
sr = cudf.Series(range(START, END), dtype="uint32")
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
persistences_and_bases.to_csv(f"{START}-{END}.csv", index=False)
print(f"Done, took {time.time() - starttime}s")
