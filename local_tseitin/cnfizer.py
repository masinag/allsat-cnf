from abc import ABC, abstractmethod
from functools import reduce
from pysmt.shortcuts import *
from pysmt.walkers import IdentityDagWalker


class LocalTseitinCNFizer(ABC):
    VAR_TEMPLATE = "T{:d}"
    POL_TEMPLATE = "P{:d}"

    def __init__(self, verbose=False, max_guards=None, expand_iff=False):
        self.verbose = verbose
        self.vars = 0
        self.polvars = 0
        self.preprocessor = Preprocessor(expand_iff=expand_iff)
        self.labels = set()
        self.max_guards = max_guards

    def is_label(self, atom):
        return atom in self.labels

    def _new_label(self):
        self.vars += 1
        S = Symbol(LocalTseitinCNFizer.VAR_TEMPLATE.format(self.vars))
        self.labels.add(S)
        return S

    def _new_polarizer(self):
        self.polvars += 1
        S = Symbol(LocalTseitinCNFizer.POL_TEMPLATE.format(self.polvars))
        self.labels.add(S)
        return S

    @abstractmethod
    def convert_as_formula(self, phi):
        raise NotImplementedError()


class Preprocessor(IdentityDagWalker):
    """
    Simplify boolean constants and make operators binary
    """
    def __init__(self, expand_iff=False):
        IdentityDagWalker.__init__(self, invalidate_memoization=True)
        self.expand_iff = expand_iff

    def _get_key(self, formula, **kwargs):
        return formula

    def convert_as_formula(self, formula):
        return self.walk(formula)

    def walk_and(self, formula, args, **kwargs):
        res = []
        for arg in args:
            if arg.is_false():
                return arg
            elif not arg.is_true():
                res.append(arg)
        if len(res) == 0:
            return TRUE()
        return reduce(And, res)

    def walk_or(self, formula, args, **kwargs):
        res = []
        for arg in args:
            if arg.is_true():
                return arg
            elif not arg.is_false():
                res.append(arg)
        if len(res) == 0:
            return FALSE()
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
        left = self.walk_not(Not(left), (left,), **kwargs)
        return self.walk_or(formula, (left, right), **kwargs)

    def walk_iff(self, formula, args, **kwargs):
        left, right = args
        if left.is_true():
            return right
        elif right.is_true():
            return left
        elif left.is_false():
            return self.walk_not(formula.arg(1), (right,), **kwargs)
        elif right.is_false():
            return self.walk_not(formula.arg(0), (left,), **kwargs)
        elif self.expand_iff:
            l, r = formula.args()
            imp1 = Implies(l, r)
            imp2 = Implies(r, l)
            res1 = self.walk_implies(imp1, (left, right), **kwargs)
            res2 = self.walk_implies(imp2, (right, left), **kwargs)
            return self.walk_and(And(imp1, imp2), (res1, res2), **kwargs)
        else:
            return Iff(left, right)
