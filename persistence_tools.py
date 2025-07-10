"""Various tools for working with persistence.

If run as a standalone program, e.g. python persistence_tools.py <num> <base>, 
will print the persistence of <num> in <base>
"""
import math
import fractions
import sys

def multiply_digits(n, base):
    """Apply the sloan map in a given base"""
    out = 1
    while n > 0:
        out *= n % base
        n = n // base
    return out

def in_base(n, base):
    """Generate the list of digits of n in a given base. 

    Each digit will be represented by an integer which is usually printed in base 10
    """
    out = []
    while n > 0:
        out.append(n % base)
        n = n // base
    return list(reversed(out))

def print_persistence(n, base):
    """Repeatedly apply the sloan map to n in base b to determine persistence, printing each term"""
    steps = 0
    current = n
    print(f"digits in non-10 bases are represented by base 10 numbers separated by commas")
    print("e.g. the base-16 number \"ff\" would be written as \"[15, 15]_16\"")

    print(f"---------Persistence for {n}_10 in base {base}---------")

    while current > base:
        print(f"Value in base: {in_base(current, base)}")
        print(f"Digits multiplied: {multiply_digits(current, base)}")
        current = multiply_digits(current, base)
        steps += 1

    print(f"Persistence for {n} in base {base} is {steps}")

def find_base(n, persistence):
    """Find a base in which n has a given persistence

    Note that this does not check that n is above the cutoff for the given 
    persistence, it'll give possibly incorrect answers
    """
    if n % persistence + 1:
      return math.ceil(fractions.Fraction(n, persistence+1))
    return n/(persistence+1) + 1

def persistence_cutoff(p):
    """Determine the cutoff for persistence p

    if n is greater than the cutoff, then it has absolute persistence at least p.
    """
    return (p+1)*(math.factorial(p+1)-1)


if __name__ == "__main__":
    N = int(sys.argv[-2])
    BASE = int(sys.argv[-1])
    print_persistence(N, BASE)
