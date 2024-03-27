from pysmt.fnode import FNode

from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.polarity_finder import PolarityDict
from allsat_cnf.polarity_walker import Polarity


class LabelCNFizer(PolarityCNFizer):
    """Converts a formula into CNF using the Tseitin algorithm."""

    def _get_polarities(self, formula: FNode) -> PolarityDict:
        # trick: force all polarities to be DOUBLE
        polarities = super()._get_polarities(formula)
        for f in polarities:
            polarities[f] = Polarity.DOUBLE
        return polarities
