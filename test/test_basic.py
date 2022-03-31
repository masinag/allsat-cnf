import sys
from itertools import product

import pytest
from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import get_boolean_variables, get_lra_atoms

from pysmt.shortcuts import *

from utils import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T,
                   U, V, W, X, Y, Z, check_models, get_allsat)

formulas_to_test = [
    And(A, B),
    Or(A, B),
    And(Or(A, B), Or(C, D)),
    Or(And(A, B), And(C, D)),
    Not(Or(A, Not(And(B, Not(Or(C, D)))))),
    Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
    Or(Or(And(A, B), And(C, D)), Not(Or(And(E, F), And(G, H)))),
    And(Iff(And(C, D), Or(D, And(B, A))), Or(A, B))
]

cnfizers = [
    LocalTseitinCNFizerActivation(),
    LocalTseitinCNFizerConds(),
]


@pytest.mark.parametrize("CNFizer, phi", product(cnfizers, formulas_to_test))
def test_correctness(CNFizer, phi):
    atoms = get_boolean_variables(phi) | get_lra_atoms(phi)

    total_models, count_tot = get_allsat(phi, use_ta=False, atoms=atoms)
    assert count_tot == len(total_models)
    cnf = CNFizer.convert(phi)
    partial_models, count_part = get_allsat(cnf, use_ta=True, atoms=atoms)
    assert count_part == count_tot

    check_models(partial_models, phi)
    # assert phi
