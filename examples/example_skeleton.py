from pysmt.shortcuts import *

from example_template import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P,
                              Q, R, S, T, U, V, W, X, Y, Z, make_example)
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import AllSATSolver

x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

formula = Or(And(A, TRUE()), And(Not(A), TRUE()))
atoms = {A}
make_example(formula, atoms=atoms)
