from itertools import product

import pytest
from pysmt.shortcuts import is_sat

from local_tseitin.label_cnfizer import LabelCNFizer
from local_tseitin.polarity_cnfizer import PolarityCNFizer
from utils import identity_examples
from utils import single_polarity_examples, double_polarity_examples


@pytest.fixture(scope="function")
def cnfizer():
    return PolarityCNFizer()


@pytest.mark.parametrize("cnfizer, phi", product([PolarityCNFizer(), LabelCNFizer()], identity_examples))
def test_identity(cnfizer, phi):
    cnf = cnfizer.convert_as_formula(phi)
    assert cnf == phi


@pytest.mark.parametrize("cnfizer, phi, n, n_vars",
                         [(PolarityCNFizer(), e.formula, e.pol_expected_clauses, e.pol_expected_variables)
                          for e in single_polarity_examples] +
                         [(LabelCNFizer(), e.formula, e.lab_expected_clauses, e.lab_expected_variables)
                          for e in single_polarity_examples])
def test_number_of_clauses_single_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert n == len(cnf.args())
    assert n_vars == len(cnf.get_free_variables())
    assert is_sat(phi) == is_sat(cnf)


@pytest.mark.parametrize("cnfizer, phi, n, n_vars",
                         [(PolarityCNFizer(), e.formula, e.pol_expected_clauses, e.pol_expected_variables)
                          for e in double_polarity_examples] +
                         [(LabelCNFizer(), e.formula, e.lab_expected_clauses, e.lab_expected_variables)
                          for e in double_polarity_examples])
def test_number_of_clauses_double_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert n == len(cnf.args())
    assert n_vars == len(cnf.get_free_variables())
    assert is_sat(phi) == is_sat(cnf)
