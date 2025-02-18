import itertools
from typing import Iterable

import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.typing import BOOL
from pysmt.walkers import handles

from allsat_cnf.cnfizer import T_CNF, CNFizer, T_Clause
from allsat_cnf.nnfizer import NNFizer
from allsat_cnf.utils import unique_everseen, negate, is_atom


class DistributiveCNF(CNFizer):
    """Converts a formula into CNF using the DeMorgan's laws and the distributive property."""
    TRUE_CLAUSE = None
    FALSE_CLAUSE = tuple()
    TRUE_CNF = []
    FALSE_CNF = [FALSE_CLAUSE]

    def __init__(self, environment=None):
        CNFizer.__init__(self, environment, invalidate_memoization=True)
        self.nnfizer = NNFizer(environment)

    def convert(self, formula: FNode) -> T_CNF:
        nnf_formula = self.nnfizer.convert(formula)
        clauses = self.walk(nnf_formula)

        return unique_everseen(clauses)

    def make_clause(self, literals: Iterable[FNode]) -> T_Clause:
        clause = list()
        for lit in unique_everseen(literals):
            if lit.is_true():
                return self.TRUE_CLAUSE
            elif lit.is_false():
                continue
            elif self.mgr.Not(lit) in clause:
                return self.TRUE_CLAUSE
            clause.append(lit)
        return tuple(clause)

    @handles(op.QUANTIFIERS)
    def walk_quantifier(self, formula: FNode, args, **kwargs):
        raise NotImplementedError("CNFizer does not support quantifiers")

    def walk_and(self, formula: FNode, args: list[T_CNF], **kwargs) -> T_CNF:
        clauses = []
        for cnf in args:
            if args == self.FALSE_CNF:
                return self.FALSE_CNF
            clauses.extend(cnf)
        return tuple(unique_everseen(clauses))

    def walk_or(self, formula: FNode, args: list[T_CNF], **kwargs) -> T_CNF:
        clauses = []
        args = [list(c) for c in args]
        for clause_product in itertools.product(*args):
            c = self.make_clause(itertools.chain(*clause_product))
            if c == self.TRUE_CLAUSE:
                continue
            elif c == self.FALSE_CLAUSE:
                return self.FALSE_CNF
            clauses.append(c)

        return tuple(unique_everseen(clauses))

    def walk_not(self, formula: FNode, args: list[T_CNF], **kwargs) -> T_CNF:
        assert is_atom(formula.arg(0))
        c = self.make_clause([negate(formula.arg(0), self.mgr)])
        if c == self.TRUE_CLAUSE:
            return self.TRUE_CNF
        if c == self.FALSE_CLAUSE:
            return self.FALSE_CNF
        return [c]

    def walk_implies(self, formula: FNode, args: list[FNode], **kwargs):
        raise NotImplementedError("The formula is not in NNF")

    def walk_iff(self, formula: FNode, args: list[FNode], **kwargs):
        raise NotImplementedError("The formula is not in NNF")

    def walk_ite(self, formula: FNode, args: list[FNode], **kwargs):
        if not self.env.stc.get_type(formula).is_bool_type():
            return [formula]
        raise NotImplementedError("The formula is not in NNF")

    @handles(op.FUNCTION)
    @handles(*op.CONSTANTS - {op.BOOL_CONSTANT})
    @handles(*op.THEORY_OPERATORS)
    def walk_identity(self, formula: FNode, **kwargs) -> FNode:
        return formula

    @handles(*op.RELATIONS)
    @handles(op.SYMBOL)
    def walk_unit_clause(self, formula: FNode, **kwargs) -> T_CNF | FNode:
        if formula.is_symbol() and not formula.is_symbol(BOOL):
            return self.walk_identity(formula, **kwargs)
        return [self.make_clause([formula])]

    @handles(op.BOOL_CONSTANT)
    def walk_bool_constant(self, formula: FNode, **kwargs) -> T_CNF:
        return self.TRUE_CNF if formula.is_true() else self.FALSE_CNF
