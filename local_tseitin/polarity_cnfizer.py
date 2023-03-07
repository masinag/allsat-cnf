from typing import Tuple, List

import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.rewritings import NNFizer
from pysmt.walkers import DagWalker, handles

from local_tseitin.polarity_finder import PolarityFinder, PolarityDict
from local_tseitin.polarity_walker import Polarity
from local_tseitin.utils import unique_everseen

T_CNF = List[Tuple[FNode]]


class PolarityCNFizer(DagWalker):
    def __init__(self, environment=None, nnf=False, mutex_nnf_labels=False, label_neg_polarity=False):
        DagWalker.__init__(self, environment, invalidate_memoization=True)
        self.mgr = self.env.formula_manager
        if mutex_nnf_labels and not nnf:
            raise ValueError("Mutex NNF labels only makes sense if NNF is enabled")
        self._nnf = nnf
        self._mutex_nnf_labels = mutex_nnf_labels
        self._label_neg_polarity = label_neg_polarity

        self._introduced_variables = {}
        self._clauses: T_CNF = []
        self._polarity_finder = PolarityFinder(environment)
        self._nnfizer = NNFizer(environment)

    def convert(self, formula) -> T_CNF:
        self._clauses.clear()
        formula = self._pre_process(formula)
        polarities = self._get_polarities(formula)
        tl: FNode = self.walk(formula, polarities=polarities)
        self._post_process(polarities)

        clauses = self._simplify_clauses(tl)
        return list(unique_everseen(clauses))

    def _get_polarities(self, formula):
        return self._polarity_finder.find(formula)

    def _simplify_clauses(self, tl):
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
        return res

    def convert_as_formula(self, formula):
        clauses = self.convert(formula)
        return self.mgr.And(map(self.mgr.Or, clauses))

    def key_var(self, formula: FNode, polarities: PolarityDict) -> FNode:
        if formula not in self._introduced_variables:
            k = self.mgr.FreshSymbol()
            if self._label_neg_polarity and polarities[formula] == Polarity.NEG:
                k = self.mgr.Not(k)
            self._introduced_variables[formula] = k
        return self._introduced_variables[formula]

    def _get_key(self, formula: FNode, **kwargs):
        return formula

    @handles(op.QUANTIFIERS)
    def walk_quantifier(self, formula: FNode, args, **kwargs):
        raise NotImplementedError("CNFizer does not support quantifiers")

    def walk_and(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula, polarities)
        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([self.mgr.Not(k), a]) for a in args]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k] + [self.mgr.Not(a).simplify() for a in args])]
        return k

    def walk_or(self, formula: FNode, args: List[FNode], polarities: PolarityDict, **kwargs):
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula, polarities)
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
        k = self.key_var(formula, polarities)
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
        k = self.key_var(formula, polarities)
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
        k = self.key_var(formula, polarities)
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

    def _pre_process(self, formula):
        if self._nnf:
            formula = self._nnfizer.convert(formula)
        return formula

    def _post_process(self, polarities: PolarityDict):
        if self._mutex_nnf_labels:
            self._add_mutex_on_nnf_labels(polarities)

    def _add_mutex_on_nnf_labels(self, polarities):
        double_polarity_sub_formulas = [f for f, p in polarities.items() if p == Polarity.DOUBLE
                                        and f in self._introduced_variables]
        for f in double_polarity_sub_formulas:
            f_pos = self._nnfizer.convert(f)
            f_neg = self._nnfizer.convert(self.mgr.Not(f))
            k_pos = self.key_var(f_pos, polarities)
            k_neg = self.key_var(f_neg, polarities)
            self._clauses.append((self.mgr.Not(k_pos), self.mgr.Not(k_neg)))
