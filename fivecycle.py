# Copyright (c) Andrew Li 2018. This file is licensed under the GPLv3.
# See https://github.com/andrew0x4c/fivecycle for more information,
# including the full LICENSE file.

# Barrington's paper:
# https://people.cs.umass.edu/~barrington/publications/bwbp.pdf

# representing a permutation on {0, 1, 2, 3, 4}
# (0-indexed to make the code easier)
class FivePerm(object):
    def __init__(self, mapping):
        assert set(mapping) == {0, 1, 2, 3, 4}
        self.mapping = mapping
    def __mul__(self, other):
        return FivePerm([other.mapping[self.mapping[x]] for x in range(5)])
        # note that the paper composes permutations left to right,
        # i.e. (1 2)(2 3) = (1 3 2) and not (1 2 3)
    def inv(self):
        result = [None] * 5
        for i, x in enumerate(self.mapping): result[x] = i
        return FivePerm(result)
    def __call__(self, val):
        return self.mapping[val]
    def cycles(self):
        # write as product of disjoint cycles
        seen = set()
        cycles = []
        for start in range(5):
            if start in seen: continue
            cycle = [start]
            x = self.mapping[start]
            seen.add(x)
            while x != start:
                cycle.append(x)
                x = self.mapping[x]
                seen.add(x)
            if len(cycle) > 1: cycles.append(cycle)
        return cycles
    def __repr__(self):
        cycles = self.cycles()
        if not cycles: return "id"
        return "".join("({})".format("".join(str(x) for x in cycle))
            for cycle in cycles)
    def __eq__(self, other):
        return self.mapping == other.mapping
    def __ne__(self, other):
        return self.mapping != other.mapping

# common permutations
identity = FivePerm([0, 1, 2, 3, 4])
rotate_r = FivePerm([1, 2, 3, 4, 0])

def from_cycle(cycle):
    result = list(range(5))
    for i, j in zip(cycle, cycle[1:] + [cycle[0]]):
        result[i] = j
    return FivePerm(result)

def commutator(x):
    # finds 5-cycles a, b such that a b a^-1 b^-1 = x
    cycles = x.cycles()
    assert len(cycles) == 1 and len(cycles[0]) == 5
    c = cycles[0]
    # example given in the paper:
    # (12345)(13542)(54321)(24531) = (13254)
    # relabeling the numbers, we have:
    # (02143)(01342)(34120)(24310) = (01234)
    return (
        from_cycle([c[0], c[2], c[1], c[4], c[3]]),
        from_cycle([c[0], c[1], c[3], c[4], c[2]]),
    )

# representing an instruction
class Instruction(object):
    def __init__(self, cond, if1, if0):
        self.cond = cond
        self.if1 = if1
        self.if0 = if0
    def __repr__(self):
        return "<{}, {}, {}>".format(self.cond, self.if1, self.if0)

# representing a boolean expression

class Expr(object):
    # this allows us to create expressions using
    #     Var(0) & ~Var(1)
    # instead of having to do
    #     And(Var(0), Not(Var(1)))
    def __invert__(self):
        return Not(self)
    def __and__(self, other):
        return And(self, other)
    def __or__(self, other):
        return Or(self, other)

class Var(Expr):
    def __init__(self, num):
        self.num = num
    def generate(self, output=rotate_r):
        return [Instruction(self.num, output, identity)]
    def __repr__(self):
        return "x_{}".format(self.num)

class Not(Expr):
    def __init__(self, expr):
        self.expr = expr
    def generate(self, output=rotate_r):
        # "unoptimized" version; may be easier to understand
        #return (
        #      self.expr.generate(output.inv())
        #    + [Instruction(None, output, output)]
        #)
        # "optimized" version
        expr_gen = self.expr.generate(output.inv())
        if not expr_gen: return [Instruction(None, output, output)]
        last = expr_gen[-1]
        return (
              expr_gen[:-1]
            + [Instruction(last.cond, last.if1 * output, last.if0 * output)]
        )
    def __repr__(self):
        return "~{}".format(self.expr)

class And(Expr):
    def __init__(self, expr1, expr2):
        self.expr1 = expr1
        self.expr2 = expr2
    def generate(self, output=rotate_r):
        a, b = commutator(output)
        return (
              self.expr1.generate(a)
            + self.expr2.generate(b)
            + self.expr1.generate(a.inv())
            + self.expr2.generate(b.inv())
        )
    def __repr__(self):
        return "({} & {})".format(self.expr1, self.expr2)

# at first, I just used this line:
#     def Or(expr1, expr2): return Not(And(Not(expr1), Not(expr2)))
# but actually defining an Or makes the repr better

class Or(Expr):
    def __init__(self, expr1, expr2):
        self.expr1 = expr1
        self.expr2 = expr2
    def generate(self, output=rotate_r):
        return (~(~self.expr1 & ~self.expr2)).generate(output)
    def __repr__(self):
        return "({} | {})".format(self.expr1, self.expr2)

def deduplicate(insts):
    # reduce sequences of instructions with the same condition.
    result = []
    # by keeping a "stack", we allow for a sequence of instructions
    # which perfectly undoes several previous instructions
    for inst in insts:
        if not result:
            # nothing to optimize
            result.append(inst)
        elif result[-1].cond == inst.cond:
            # both conditions are the same, merge the two cases
            result[-1] = Instruction(inst.cond,
                result[-1].if1 * inst.if1, result[-1].if0 * inst.if0)
        elif result[-1].if0 == result[-1].if1:
            # last instruction unconditional, merge into new instruction
            result[-1] = Instruction(inst.cond,
                result[-1].if1 * inst.if1, result[-1].if0 * inst.if0)
        elif inst.if0 == inst.if1:
            # new instruction unconditional, merge into last instruction
            result[-1] = Instruction(result[-1].cond,
                result[-1].if1 * inst.if1, result[-1].if0 * inst.if0)
        else:
            # can't merge
            result.append(inst)
        if result[-1].if0 == result[-1].if1 == identity:
            # the last instruction doesn't do anything, so we remove it
            result.pop(-1)
    return result

def clean_if0(insts):
    # makes all permutations in the false case be the identity.
    # we keep track of what permutation we "didn't do", and adjust
    # the other permutations based on that.
    # note that
    #     <c, p1, p0> = <c, p1 o p0^-1, id> (p0)
    #     (px) <c, p1, p0> = <c, px o p1, px o p0>
    # so
    #     (px) <c, p1, p0> = <c, px o p1 o p0^-1 o px^-1, id> (px o p0)
    perm = identity
    result = []
    for inst in insts:
        result.append(Instruction(inst.cond,
            perm * inst.if1 * inst.if0.inv() * perm.inv(), identity))
        if result[-1].if0 == result[-1].if1 == identity:
            result.pop(-1)
            # while this is actually done in deduplicate, we need this
            # here to avoid adding extra <None, id, id> instructions
            # if clean_if0 is called in a loop with a program which
            # is true when all inputs are false; ex. demo(~a, dedup=False)
        perm *= inst.if0
    if perm != identity:
        # a permutation will be applied when no conditions are true
        result.append(Instruction(None, perm, perm))
    return result
