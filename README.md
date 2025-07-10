# CUDF Persistence Tools
A repository of tools for finding numbers with large multiplicative persistence.

Multiplicative persistence is the number of times you can multiply the digits of a number together before it reaches a single digit. E.g. 77 has persistence 4 because `7*7 = 49`, then `4*9 = 36`, then `3*6 = 18`, then `1*8 = 8`, taking 4 steps. 

This can be generalized to any base, not just base 10. Absolute persistence of a number is the maximum multiplicative persistence it achieves in any base. For example, 8 has absolute persistence 2 because in base 3, 8 is written as `22_3`. `2*2 = 11_3`, then `1*1=1_3`. 

We call the smallest base in which `n` achieves its absolute persistence `n`'s maximal base. For example, 8's maximal base is 3.

## Requirements
These tools require a GPU with a modern CUDA driver, python3, numpy, pandas, and cudf. While a requirements.txt is provided, you're probably better served installing cudf for your system according to its instructions: https://docs.rapids.ai/install/

### Tools

There are a number of tools available.

#### A330152.py
Run `python A330152.py` with no arguments to begin generating terms in the sequence A330152, the smallest numbers with each absolute persistence. Terms will be printed to stdout in CSV format, along with their absolute persistence and their maximal base.

You can adjust the `BLOCK_SIZE` constant at the top of the file to control how many numbers will be searched at once. Depending on your GPU's memory, you may need to adjust this to get the best performance.

#### A245760.py
Run `python A245760.py <start> <end>` to generate terms of A245760, the absolute persistence and maximal base of each `start<=n<end`.
Since this can quickly generate very large sequences, it dumps to a CSV called `start-end.csv` rather than logging to stdout.

#### persistence tools module

This module can be run as a standalone program to find the persistence of a number in a base, or can be imported and used in a repl or script to do more complex tasks.

`find_base` and `persistence_cutoff` can be used to easily find numbers with large absolute persistences. For an explanation of what they're doing internally, see `Lamont_Conjecture_2_Proof_Sketch.pdf`.

Example:
```
>>> from persistence_tools import *
>>> persistence_cutoff(42)
2597856311725074932406270678946101892812374015999999957
>>> bignum = persistence_cutoff(42)
>>> base = find_base(bignum + 31415, 42)
>>> find_base(bignum + 31415, 42)
60415263063373835637355132068513997507264512000000730
>>> print_persistence(bignum + 31415, base)
<snipped a bunch of lines showing each iteration of the sloan map>
Persistence for 2597856311725074932406270678946101892812374016000031372 in base 60415263063373835637355132068513997507264512000000730 is 42
```

Module documentation:
```
NAME
    persistence_tools - Various tools for working with persistence.

DESCRIPTION
    If run as a standalone program, e.g. python persistence_tools.py <num> <base>,
    will print the persistence of <num> in <base>

FUNCTIONS
    find_base(n, persistence)
        Find a base in which n has a given persistence

        Note that this does not check that n is above the cutoff for the given
        persistence, it'll give possibly incorrect answers

    in_base(n, base)
        Generate the list of digits of n in a given base.

        Each digit will be represented by an integer which is usually printed in base 10

    multiply_digits(n, base)
        Apply the sloan map in a given base

    persistence_cutoff(p)
        Determine the cutoff for persistence p

        if n is greater than the cutoff, then it has absolute persistence at least p.

    print_persistence(n, base)
        Repeatedly apply the sloan map to n in base b to determine persistence, printing each term
```

### Datasets
`1-10000000.csv.gz` contains a gzipped CSV of the absolute multiplicative persistence of each `n<10 million`, along with `n`'s maximal base.

`A330152.csv` contains the known terms of A330152. `A330152_heuristic.csv` contains a few conjectured following terms in the sequence. These terms definitely have at least the stated absolute persistence, but there may be smaller examples with such persistence that have not been found.

`persistence_plots.png` shows plots of the absolute persistence and maximal base for `1<=n<100 million`.

## References
http://neilsloane.com/doc/persistence.html

https://cs.uwaterloo.ca/journals/JIS/VOL24/Lamont/lamont5.html

https://oeis.org/A330152

https://oeis.org/A245760
