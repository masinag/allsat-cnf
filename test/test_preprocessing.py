import sys
from itertools import product
from typing import List, Callable, Tuple

import pytest
from pysmt.fnode import FNode

from local_tseitin.cnfizer import LocalTseitinCNFizer, Preprocessor
# from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import get_boolean_variables, get_lra_atoms

from pysmt.shortcuts import *

from utils import boolean_variables
from local_tseitin.utils import check_models, get_allsat

A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z = boolean_variables


@pytest.mark.parametrize("phi, expected", [
    (A, A),
    (And(A, B), And(A, B)),
    (Or(A, B), Or(A, B)),
    (And(Or(A, B), Or(C, D)), And(Or(A, B), Or(C, D))),
    (Iff(A, B), And(Or(Not(A), B), Or(Not(B), A))),
    (And(Iff(A, B), Iff(C, D)), And(And(Or(Not(A), B), Or(Not(B), A)), And(Or(Not(C), D), Or(Not(D), C)))),
])
def test_expand_iff(phi: FNode, expected: FNode):
    assert Preprocessor(expand_iff=True).walk(phi) == expected


@pytest.mark.parametrize("phi, expected", [
    (A, A),
    (And(A, B), And(A, B)),
    (Or(A, B), Or(A, B)),
    (And(Or(A, B), Or(C, D)), And(Or(A, B), Or(C, D))),
    (And(A, B, C), And(And(A, B), C)),
    (Or(A, B, C), Or(Or(A, B), C)),
    (And(Or(A, B), Or(C, D), Or(E, F)), And(And(Or(A, B), Or(C, D)), Or(E, F))),
])
def test_binary_operators(phi: FNode, expected: FNode):
    assert Preprocessor(binary_operators=True).walk(phi) == expected
