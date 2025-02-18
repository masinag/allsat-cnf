from typing import Iterable

from pysmt.fnode import FNode
from pysmt.rewritings import NNFizer as _NNFizer

T_Clause = tuple[FNode, ...]
T_CNF = Iterable[T_Clause]


class NNFizer(_NNFizer):
    def __init__(self, environment=None, **kwargs):
        _NNFizer.__init__(self, environment)

    def _get_children(self, formula):
        """Handle theory if-then-else.        """
        mgr = self.mgr
        if formula.is_not():
            s = formula.arg(0)
            if s.is_ite():
                assert self.env.stc.get_type(s).is_bool_type()
                i, t, e = s.args()
                return [i, mgr.Not(i), mgr.Not(t), mgr.Not(e)]
        if formula.is_ite() and not self.env.stc.get_type(formula).is_bool_type():
            return []
        return super()._get_children(formula)

    def walk_not(self, formula, args, **kwargs):
        s = formula.arg(0)
        if s.is_ite():
            i, ni, nt, ne = args
            return self.mgr.Or(self.mgr.And(i, nt), self.mgr.And(ni, ne))
        return super().walk_not(formula, args, **kwargs)

    def walk_ite(self, formula, args, **kwargs):
        if not self.env.stc.get_type(formula).is_bool_type():
            return formula
        return super().walk_ite(formula, args, **kwargs)
