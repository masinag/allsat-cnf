from pysmt.fnode import FNode

from local_tseitin.polarity_cnfizer import PolarityCNFizer


class LabelCNFizer(PolarityCNFizer):
    def iter_walk(self, formula: FNode, **kwargs) -> FNode:
        return super().iter_walk(formula, top_pol=None, **kwargs)
