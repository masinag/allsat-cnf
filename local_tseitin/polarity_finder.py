from typing import List, Dict

from pysmt import operators as op, typing as types
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles

from local_tseitin.polarity_walker import PolarityDagWalker, Polarity

PolarityDict = Dict[FNode, Polarity]


class PolarityFinder(PolarityDagWalker):
    """Finds the polarity of each subformula in a formula."""

    def __init__(self, environment=None):
        DagWalker.__init__(self, environment, invalidate_memoization=True)
        self.mgr = self.env.formula_manager
        self.polarity: PolarityDict = {}

    def find(self, formula: FNode) -> PolarityDict:
        self.polarity.clear()
        self.walk(formula)
        return self.polarity

    @handles(op.AND, op.OR, op.ITE, op.IMPLIES, op.IFF, op.NOT)
    @handles(op.RELATIONS)
    def walk_sub_formula(self, formula: FNode, args: List[None], pol: Polarity, **kwargs):
        self.polarity[formula] = self.polarity.get(formula, pol) | pol

    def walk_symbol(self, formula: FNode, args: List[None], pol: Polarity, **kwargs):
        if formula.is_symbol(types.BOOL):
            self.polarity[formula] = self.polarity.get(formula, pol) | pol

    def walk_function(self, formula: FNode, args: List[None], pol: Polarity, **kwargs):
        ty = formula.function_name().symbol_type()
        if ty.return_type.is_bool_type():
            self.polarity[formula] = self.polarity.get(formula, pol) | pol

    @handles(*op.THEORY_OPERATORS)
    @handles(*op.CONSTANTS)
    def walk_identity(self, formula: FNode, args: List[None], pol: Polarity, **kwargs):
        pass
