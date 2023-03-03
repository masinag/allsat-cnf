from typing import Tuple, List

import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles

from local_tseitin.polarity_finder import PolarityFinder, PolarityDict
from local_tseitin.polarity_walker import Polarity
from local_tseitin.utils import unique_everseen

T_CNF = List[Tuple[FNode]]


class PolarityCNFizer(DagWalker):
    def __init__(self, environment=None):
        DagWalker.__init__(self, environment, invalidate_memoization=True)
        self.mgr = self.env.formula_manager
        self._introduced_variables = {}
        self._clauses: T_CNF = []
        self._polarity_finder = PolarityFinder(environment)

    def convert(self, formula) -> T_CNF:
        self._clauses.clear()
        polarities = self._polarity_finder.find(formula)
        tl: FNode = self.walk(formula, polarities=polarities)

        if len(self._clauses) == 0:
            return [tuple([tl])]
        res = []
        for clause in self._clauses:
            simp = []
            for lit in clause:
                if lit.is_true():
                    # Prune clauses that are trivially TRUE
                    simp = None
                    break
                elif lit == tl:
                    # Prune clauses as ~tl -> l1 v ... v lk
                    simp = None
                    break
                elif lit == self.mgr.Not(tl).simplify():
                    # Simplify tl -> l1 v ... v lk
                    # into l1 v ... v lk
                    continue
                elif not lit.is_false():
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(tuple(unique_everseen(simp)))
        return list(unique_everseen(res))

    def key_var(self, formula: FNode) -> FNode:
        if formula not in self._introduced_variables:
            self._introduced_variables[formula] = self.mgr.FreshSymbol()
        return self._introduced_variables[formula]

    def _get_key(self, formula: FNode, **kwargs):
        return formula

    def convert_as_formula(self, formula):
        clauses = self.convert(formula)
        return self.mgr.And(map(self.mgr.Or, clauses))

    @handles(op.QUANTIFIERS)
    def walk_quantifier(self, formula: FNode, args, **kwargs):
        raise NotImplementedError("CNFizer does not support quantifiers")

    def walk_and(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula)
        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([self.mgr.Not(k), a]) for a in args]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k] + [self.mgr.Not(a).simplify() for a in args])]
        return k

    def walk_or(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula)
        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([self.mgr.Not(k)] + [a for a in args])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, self.mgr.Not(a).simplify()]) for a in args]
        return k

    def walk_not(self, formula: FNode, args, **kwargs):
        a = args[0]
        if a.is_true():
            return self.mgr.FALSE()
        elif a.is_false():
            return self.mgr.TRUE()
        else:
            return self.mgr.Not(a).simplify()

    def walk_implies(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        a, b = args
        k = self.key_var(formula)
        not_k = self.mgr.Not(k)
        not_a = self.mgr.Not(a).simplify()
        not_b = self.mgr.Not(b).simplify()

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_a, b])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, a]), tuple([k, not_b])]
        return k

    def walk_iff(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        a, b = args
        k = self.key_var(formula)
        not_k: FNode = self.mgr.Not(k)
        not_a: FNode = self.mgr.Not(a).simplify()
        not_b: FNode = self.mgr.Not(b).simplify()

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_a, b]),
                              tuple([not_k, a, not_b])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, not_a, not_b]),
                              tuple([k, a, b])]
        return k

    def walk_ite(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        if not self.env.stc.get_type(formula).is_bool_type():
            return formula

        i, t, e = args
        k = self.key_var(formula)
        not_k = self.mgr.Not(k)
        not_i = self.mgr.Not(i).simplify()
        not_t = self.mgr.Not(t).simplify()
        not_e = self.mgr.Not(e).simplify()

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_i, t]), tuple([not_k, i, e])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, not_i, not_t]), tuple([k, i, not_e])]

        return k

    @handles(op.SYMBOL, op.FUNCTION)
    @handles(*op.CONSTANTS)
    @handles(*op.THEORY_OPERATORS)
    @handles(*op.RELATIONS)
    def walk_identity(self, formula: FNode, **kwargs):
        return formula
