# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/fivecycle for more information,
# including the full LICENSE file.

# some helper functions and variables to use on the REPL

from fivecycle import *
from drawinsts import *

def demo(expr, dedup=True, clean=True, show=True, prog=False,
    *args, **kwargs):
    insts = expr.generate()
    while True:
        # one iteration may not work for things like (a & ~a) | b
        length = len(insts)
        if dedup: insts = deduplicate(insts)
        if clean: insts = clean_if0(insts)
        if len(insts) == length: break
    if prog:
        for inst in insts: print inst
    else:
        plot(insts, *args, **kwargs)
        if show: plt.show()

a, b, c, d, e, f, g, h = [Var(i) for i in range(8)]

def generate_examples():
    import os
    if not os.path.isdir("examples"): os.mkdir("examples")
    for name, expr, options in [
        # and-like
        ("and", a & b, {}),
        ("and_not", a & ~b, {}),
        ("nand", ~(a & b), {}),
        # or-like
        ("or", a | b, {}),
        ("or_not", a | ~b, {}),
        ("nor", ~(a | b), {}),
        # xor-like
        ("xor", (~a & b) | (a & ~b), {}),
        ("xnor", ~((~a & b) | (a & ~b)), {}),
        ("xor_opt", (~a & b) | (~b & a), {}),
        ("xnor_opt", ~((~a & b) | (~b & a)), {}),
        # and-chain
        ("and3", (a & b) & c, {}),
        ("and4", (a & b) & (c & d), {}),
        ("and4_unbalanced", ((a & b) & c) & d, {}),
        # or-chain
        ("or3", (a | b) | c, {}),
        ("or4", (a | b) | (c | d), {}),
        ("or4_unbalanced", ((a | b) | c) | d, {}),
        # clean/deduplication
        ("or_no_clean", a | b, {"clean": False}),
        ("redundant_a", (a | a) & (a | a), {"dedup": False}),
        ("just_a", a, {}),
        # other
        ("and_or_and_not", (a & b) | (c & ~d), {}),
    ]:
        demo(expr, show=False, **options)
        plt.title("Expression {}".format(name))
        # make the plot wide to make the permutations easier to read
        plt.gcf().set_size_inches(16, 8)
        plt.savefig("examples/{}.png".format(name), bbox_inches="tight")
        print "Generated '{}'".format(name)
