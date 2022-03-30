from functools import reduce
from pysmt.shortcuts import *
from pysmt.walkers import IdentityDagWalker


class LocalTseitinCNFizer():
    VAR_TEMPLATE = "T{:d}"

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.vars = 0
        self.preprocessor = Preprocessor()

    def _new_label(self):
        self.vars += 1
        return Symbol(LocalTseitinCNFizer.VAR_TEMPLATE.format(self.vars))

    def convert(self, phi):
        raise NotImplemented

    def is_atom(self, atom):
        return atom.is_symbol(BOOL) or atom.is_theory_relation()

    def is_literal(self, literal):
        return self.is_atom(literal) or (literal.is_not() and self.is_atom(literal.arg(0)))

    def is_cnf(self, phi):
        if self.is_literal(phi):
            return True


class Preprocessor(IdentityDagWalker):
    """
    Simplify boolean constants and make operators binary
    """
    def convert(self, formula):
        return self.walk(formula)

    def walk_and(self, formula, args, **kwargs):
        res = []
        for arg in args:
            if arg.is_false():
                return arg
            elif not arg.is_true():
                res.append(arg)
        return reduce(And, res)
    
    def walk_or(self, formula, args, **kwargs):
        res = []
        for arg in args:
            if arg.is_true():
                return arg
            elif not arg.is_false():
                res.append(arg)
        return reduce(Or, res)

    def walk_not(self, formula, args, **kwargs):
        arg = args[0]
        if arg.is_true():
            return FALSE()
        elif arg.is_false():
            return TRUE()
        else:
            return Not(arg)

    def walk_implies(self, formula, args, **kwargs):
        left, right = args
        left = self.walk_not(Not(left), left, **kwargs)
        return self.walk_or(formula, (left, right), **kwargs)

    def walk_iff(self, formula, args, **kwargs):
        left, right = args
        if left.is_true():
            return right
        elif right.is_true():
            return left
        elif left.is_false():
            return self.walk_not(formula.arg(1), right, **kwargs)
        elif right.is_false():
            return self.walk_not(formula.arg(0), left, **kwargs)
        else:
            return Iff(left, right)