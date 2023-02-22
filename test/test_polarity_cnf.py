import pytest
from pysmt.shortcuts import And, Iff, Not, Or, is_sat

from local_tseitin.polarity_cnfizer import PolarityCNFizer
from utils import boolean_variables

A, B, C, D, E, F, G, H, *_ = boolean_variables


@pytest.fixture(scope="function")
def cnfizer():
    return PolarityCNFizer()


@pytest.mark.parametrize("phi", [
    A,
    And(A, B),
    Or(A, B),
    And(A, B, C, D),
    Or(A, B, C, D),
    Not(A),
    Not(Not(A)),
    Not(Not(And(A, B))),
    Not(Not(Or(A, B))),
])
def test_identity(phi, cnfizer):
    cnf = cnfizer.convert_as_formula(phi)
    assert cnf == phi


@pytest.mark.parametrize("phi, n, n_vars", [
    (And(Or(A, B), Or(C, D)), 4, 6),
    (Or(And(A, B), And(C, D)), 5, 6),
    (Not(Or(A, Not(And(B, Not(Or(C, D)))))), 6, 6),
    (Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)), 11, 14),
])
def test_number_of_clauses_single_polarity(phi, n, n_vars, cnfizer):
    cnf = cnfizer.convert_as_formula(phi)
    assert n == len(cnf.args())
    assert n_vars == len(cnf.get_free_variables())
    assert is_sat(phi) == is_sat(cnf)


@pytest.mark.parametrize("phi, n, n_vars", [
    (Or(And(A, B), And(C, Or(Not(And(A, B)), D))), 7, 7),
    (Iff(And(C, D), Or(D, And(B, A))), 11, 7),
])
def test_number_of_clauses_double_polarity(phi, n, n_vars, cnfizer):
    cnf = cnfizer.convert_as_formula(phi)
    assert n == len(cnf.args())
    assert n_vars == len(cnf.get_free_variables())
    assert is_sat(phi) == is_sat(cnf)
