from pysmt.shortcuts import And, Or, Not, Iff

from example_template import boolean_atoms, make_example

A, B, C, D, E, F, G, H, *_ = boolean_atoms

formulas = [
    And(A, Or(B, C)),
    And(Not(A), Or(Not(B), Not(C))),
    Or(And(A, B), And(C, D)),
    Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
    Or(A, Or(Not(B), And(Not(C), Not(D)))),
    Iff(Iff(A, B), Iff(C, D)),
    Iff(Iff(Or(A, B), C), D),
    Iff(Or(And(Or(A, B), C), D), E),
    Iff(A, Or(B, Iff(C, Or(D, E)))),
    Iff(A, Or(B, Iff(C, Or(D, And(E, Or(F, G)))))),
    Or(And(Or(A, C), B), And(Or(A, C), B)),
    Iff(Iff(Iff(A, B), Iff(C, D)), Iff(Iff(E, F), Or(G, H))),
    Not(And(Not(And(A, B)), Not(And(B, C)))),
    And(B, Not(And(Not(A), Not(C)))),
    And(Not(And(Not(A), Not(B))), Not(And(A, B)))
]

for formula in formulas:
    make_example(formula)
    print()
