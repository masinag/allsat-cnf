import sys
from itertools import product

import pytest
from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import get_boolean_variables, get_lra_atoms

from pysmt.shortcuts import *

from utils import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T,
                   U, V, W, X, Y, Z, check_eval_true, check_models, solver)

formulas_to_test = [
    And(A, B),
    Or(A, B),
    And(Or(A, B), Or(C, D)),
    Or(And(A, B), And(C, D)),
    Not(Or(A, Not(And(B, Not(Or(C, D)))))),
    Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
    Or(Or(And(A, B), And(C, D)), Not(Or(And(E, F), And(G, H)))),
]

cnfizers = [
    LocalTseitinCNFizerActivation(),
    LocalTseitinCNFizerConds(),
]


@pytest.mark.parametrize("CNFizer, phi", product(cnfizers, formulas_to_test))
def test_correctness(CNFizer, phi):
    atoms = get_boolean_variables(phi) | get_lra_atoms(phi)

    total_models = solver.get_allsat(phi, use_ta=False, atoms=atoms)
    cnf = CNFizer.convert(phi)
    print(CNFizer, phi.serialize(), atoms, cnf.serialize(), file=sys.stderr)
    partial_models = solver.get_allsat(cnf, use_ta=True, atoms=atoms)

    check_eval_true(phi, partial_models)

    check_models(partial_models, total_models)
    # assert phi
