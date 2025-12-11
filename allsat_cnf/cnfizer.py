from typing import Protocol

from pysmt.fnode import FNode

T_CLAUSE = tuple[FNode, ...]
T_CNF = list[T_CLAUSE]


class CNFizer(Protocol):
    def convert(self, formula: FNode) -> T_CNF:
        ...

    def convert_as_formula(self, formula: FNode) -> FNode:
        ...
