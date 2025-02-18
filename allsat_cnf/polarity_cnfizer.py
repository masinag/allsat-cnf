import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.walkers import handles

from allsat_cnf.cnfizer import CNFizer, T_CNF, T_Clause
from allsat_cnf.nnfizer import NNFizer
from allsat_cnf.polarity_finder import PolarityFinder, PolarityDict
from allsat_cnf.polarity_walker import Polarity
from allsat_cnf.utils import unique_everseen, negate


class PolarityCNFizer(CNFizer):
    """Converts a formula into CNF using the Plaisted and Greenbaum algorithm."""

    def __init__(self, environment=None, nnf=False, mutex_nnf_labels=False, label_neg_polarity=False):
        CNFizer.__init__(self, environment, invalidate_memoization=True)
        if mutex_nnf_labels and not nnf:
            raise ValueError("Mutex NNF labels only makes sense if NNF is enabled")
        self._nnf = nnf
        self._mutex_nnf_labels = mutex_nnf_labels
        self._label_neg_polarity = label_neg_polarity

        self._introduced_variables = {}
        self._clauses: list[T_Clause] = []
        self._polarity_finder = PolarityFinder(environment)
        self._nnfizer = NNFizer(environment)

    def convert(self, formula: FNode) -> T_CNF:
        self._clauses = []
        pre_polarities = self._get_polarities(formula)
        formula = self._pre_process(formula)
        polarities = self._get_polarities(formula)
        tl: FNode = self.walk(formula, polarities=polarities)
        self._post_process(pre_polarities)

        clauses = self._simplify_clauses(tl)
        return list(unique_everseen(clauses))

    def _get_children(self, formula):
        if formula.is_ite() and not self.env.stc.get_type(formula).is_bool_type():
            return []
        return super()._get_children(formula)

    def _get_polarities(self, formula: FNode) -> PolarityDict:
        return self._polarity_finder.find(formula)

    def _simplify_clauses(self, tl) -> T_CNF:
        if len(self._clauses) == 0:
            return [tuple([tl])]
        res = []
        for clause in self._clauses:
            simp = []
            for lit in clause:
                if lit.is_true() or self.negate(lit) in simp:
                    # Prune clauses that are trivially TRUE
                    simp = None
                    break
                elif lit == tl:
                    # Prune clauses as ~tl -> l1 v ... v lk
                    simp = None
                    break
                elif lit == self.negate(tl):
                    # Simplify tl -> l1 v ... v lk
                    # into l1 v ... v lk
                    continue
                elif not lit.is_false():
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(tuple(unique_everseen(simp)))
        return res

    def key_var(self, formula: FNode, polarities: PolarityDict) -> FNode:
        if formula not in self._introduced_variables:
            k = self.mgr.FreshSymbol()
            if self._label_neg_polarity and polarities[formula] == Polarity.NEG:
                k = self.negate(k)
            self._introduced_variables[formula] = k
        return self._introduced_variables[formula]

    def _get_key(self, formula: FNode, **kwargs):
        return formula

    @handles(op.QUANTIFIERS)
    def walk_quantifier(self, formula: FNode, args, **kwargs):
        raise NotImplementedError("CNFizer does not support quantifiers")

    def walk_and(self, formula: FNode, args: list[FNode], polarities: PolarityDict, **kwargs) -> FNode:
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula, polarities)
        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([self.negate(k), a]) for a in args]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k] + [self.negate(a) for a in args])]
        return k

    def walk_or(self, formula: FNode, args: list[FNode], polarities: PolarityDict, **kwargs) -> FNode:
        if len(args) == 1:
            return args[0]

        k = self.key_var(formula, polarities)
        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([self.negate(k)] + [a for a in args])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, self.negate(a)]) for a in args]
        return k

    def walk_not(self, formula: FNode, args, **kwargs):
        return self.negate(args[0])

    def walk_implies(self, formula: FNode, args: list[FNode], polarities: PolarityDict, **kwargs) -> FNode:
        a, b = args
        k = self.key_var(formula, polarities)
        not_k = self.negate(k)
        not_a = self.negate(a)
        not_b = self.negate(b)

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_a, b])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, a]), tuple([k, not_b])]
        return k

    def negate(self, term):
        return negate(term, self.mgr)

    def walk_iff(self, formula: FNode, args: list[FNode], polarities: PolarityDict, **kwargs) -> FNode:
        a, b = args
        k = self.key_var(formula, polarities)
        not_k: FNode = self.negate(k)
        not_a: FNode = self.negate(a)
        not_b: FNode = self.negate(b)

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_a, b]),
                              tuple([not_k, a, not_b])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, not_a, not_b]),
                              tuple([k, a, b])]
        return k

    def walk_ite(self, formula: FNode, args: list[FNode], polarities: PolarityDict, **kwargs) -> FNode:
        if not self.env.stc.get_type(formula).is_bool_type():
            return formula
        k = self.key_var(formula, polarities)

        i, t, e = args
        not_k = self.negate(k)
        not_i = self.negate(i)
        not_t = self.negate(t)
        not_e = self.negate(e)

        if Polarity.POS in polarities[formula]:
            self._clauses += [tuple([not_k, not_i, t]), tuple([not_k, i, e])]
        if Polarity.NEG in polarities[formula]:
            self._clauses += [tuple([k, not_i, not_t]), tuple([k, i, not_e])]

        return k

    @handles(op.SYMBOL, op.FUNCTION)
    @handles(*op.CONSTANTS)
    @handles(*op.THEORY_OPERATORS)
    @handles(*op.RELATIONS)
    def walk_identity(self, formula: FNode, **kwargs) -> FNode:
        return formula

    def _pre_process(self, formula: FNode) -> FNode:
        if self._nnf:
            formula = self._nnfizer.convert(formula)
        return formula

    def _post_process(self, polarities: PolarityDict):
        if self._mutex_nnf_labels:
            self._add_mutex_on_nnf_labels(polarities)

    def _add_mutex_on_nnf_labels(self, polarities: PolarityDict):
        double_polarity_sub_formulas = [f for f, p in polarities.items() if p == Polarity.DOUBLE]
        for f in double_polarity_sub_formulas:
            f_pos = self._nnfizer.convert(f)
            f_neg = self._nnfizer.convert(self.negate(f))
            if f_pos in self._introduced_variables and f_neg in self._introduced_variables:
                k_pos = self.key_var(f_pos, polarities)
                k_neg = self.key_var(f_neg, polarities)
                self._clauses.append((self.negate(k_pos), self.negate(k_neg)))
