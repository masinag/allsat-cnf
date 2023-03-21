from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.polarity_walker import Polarity


class LabelCNFizer(PolarityCNFizer):
    def _get_polarities(self, formula):
        polarities = super()._get_polarities(formula)
        for f in polarities:
            polarities[f] = Polarity.DOUBLE
        return polarities
