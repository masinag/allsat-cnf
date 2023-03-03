from pysmt.fnode import FNode

from local_tseitin.polarity_cnfizer import PolarityCNFizer
from local_tseitin.polarity_walker import Polarity


class LabelCNFizer(PolarityCNFizer):
    def iter_walk(self, formula: FNode, **kwargs) -> FNode:
        return super().iter_walk(formula, top_pol=Polarity.DOUBLE, **kwargs)
