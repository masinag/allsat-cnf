from pysmt.fnode import FNode

from local_tseitin.polarity_cnfizer import PolarityCNFizer
from local_tseitin.polarity_walker import Polarity


class LabelCNFizer(PolarityCNFizer):
    def _get_polarities(self, formula):
        polarities = super()._get_polarities(formula)
        for f in polarities:
            polarities[f] = Polarity.DOUBLE
        return polarities
