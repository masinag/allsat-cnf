from abc import abstractmethod
from typing import Iterable

from pysmt.fnode import FNode
from pysmt.formula import FormulaManager
from pysmt.walkers import DagWalker

T_Clause = tuple[FNode, ...]
T_CNF = Iterable[T_Clause]


class CNFizer(DagWalker):
    def __init__(self, environment=None, **kwargs):
        DagWalker.__init__(self, environment, **kwargs)
        self.mgr: FormulaManager = self.env.formula_manager

    @abstractmethod
    def convert(self, formula: FNode) -> T_CNF:
        pass

    def convert_as_formula(self, formula: FNode) -> FNode:
        clauses = self.convert(formula)
        return self.mgr.And(map(self.mgr.Or, clauses))
