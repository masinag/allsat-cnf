from typing import Iterable

from pysmt.fnode import FNode

from allsat_cnf.label_cnfizer import LabelCNFizer
from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.utils import get_boolean_variables, get_lra_atoms, is_cnf
from .run import PreprocessOptions


def preprocess_formula(phi, preprocess_options: PreprocessOptions) -> tuple[FNode, Iterable[FNode]]:
    atoms = get_boolean_variables(phi).union(
        {a for a in get_lra_atoms(phi) if not a.is_equals()}  # NOTICE: exclude equalities for WMI problems
    )

    if preprocess_options.cnf_type == "POL":
        phi = PolarityCNFizer(nnf=preprocess_options.do_nnf, mutex_nnf_labels=preprocess_options.mutex_nnf_labels,
                              label_neg_polarity=preprocess_options.label_neg_polarity).convert_as_formula(phi)
    elif preprocess_options.cnf_type == "LAB":
        phi = LabelCNFizer(nnf=preprocess_options.do_nnf,
                           mutex_nnf_labels=preprocess_options.mutex_nnf_labels).convert_as_formula(phi)
    else:
        raise ValueError("Unknown CNF type: {}".format(preprocess_options.cnf_type))
    assert is_cnf(phi)

    return phi, atoms
