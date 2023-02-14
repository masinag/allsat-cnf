from itertools import product
from typing import List, Callable

import pytest
from pysmt.fnode import FNode
from pysmt.shortcuts import *

from local_tseitin.cnfizer import LocalTseitinCNFizer, Preprocessor
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import check_models, get_allsat
from local_tseitin.utils import get_boolean_variables, get_lra_atoms
from utils import boolean_variables

A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z = boolean_variables

formulas_to_test: List[FNode] = [
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
    # LocalTseitinCNFizerActivation(),
    LocalTseitinCNFizerConds(),
]

preprocessings = [
    lambda f: f,
    lambda f: Preprocessor(expand_iff=True).walk(f),
    lambda f: Preprocessor(binary_operators=True).walk(f),
]


@pytest.mark.parametrize("preprocess, cnfizer, phi", product(preprocessings, cnfizers, formulas_to_test))
def test_correctness(preprocess: Callable[[FNode], FNode], cnfizer: LocalTseitinCNFizer, phi: FNode):
    atoms = get_boolean_variables(phi) | get_lra_atoms(phi)
    phi = preprocess(phi)

    total_models, count_tot = get_allsat(phi, use_ta=False, atoms=atoms)
    assert count_tot == len(total_models)
    cnf = cnfizer.convert_as_formula(phi)
    partial_models, count_part = get_allsat(cnf, use_ta=True, atoms=atoms)
    assert count_part == count_tot, f"{phi.serialize()}\n{cnf.serialize()}"

    check_models(partial_models, phi)
    # assert phi
# ((T1 | (! A)) &
#  (T1 | T2) &
#  True &
#  (A | T2 | (! B) | T3) &
#  (A | (! T2) | B) &
#  (A | (! T2) | (! T3)) &
#  True &
#  (A | (! B) | (! T3) | C | D) &
#  (A | (! B) | T3 | (! C)) &
#  (A | (! B) | T3 | (! D)) &
#  (A | T2 | B | (! T3)))
