from pysmt.shortcuts import *

from example_template import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P,
                              Q, R, S, T, U, V, W, X, Y, Z, main)
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import AllSATSolver

x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

formula = ((((0.0 <= x1) & (x1 < 1.0) & (0.0 <= x2) & (x2 < 2.0))) & (((A & B) & (((C & D)) | ((~(C & D))))) | ((~(A & B)) & (((E & F)) | ((~(E & F)))))))
main(formula)