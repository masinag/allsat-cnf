from pysmt.shortcuts import *

from example_template import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P,
                              Q, R, S, T, U, V, W, X, Y, Z, main)

formulas = [
    Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
    Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
    Or(And(A, B), And(C, D)),
    Or(Not(And(A, B)), And(C, D)),
    Not(Or(A, And(B, C))),
    And(Not(A), Or(Not(B), Not(C))),
    Or(A, Not(And(B, Or(C, D)))),
    Not(Or(A, Not(And(B, Not(Or(C, D)))))),
    Or(A, Or(Not(B), And(Not(C), Not(D)))),
    And(A, Not(Or(B, C))),
    Or(A, Not(And(B, C))),
    And(A, Or(B, C)),
    Iff(Iff(A,B), Iff(C,D))
]

for formula in formulas:
    main(formula)
