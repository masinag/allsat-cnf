from pysmt.shortcuts import *

from collections import namedtuple

from pysmt.shortcuts import And, Or, Not

Example = namedtuple('Example', ['formula', 'pol_expected_clauses', 'pol_expected_variables',
                                 'lab_expected_clauses', 'lab_expected_variables'])
# initialize bool variables
boolean_variables = [Symbol(chr(i), BOOL)
                     for i in range(ord("A"), ord("Z") + 1)]
A, B, C, D, E, F, G, H, *_ = boolean_variables

identity_examples = [
    A,
    And(A, B),
    Or(A, B),
    And(A, B, C, D),
    Or(A, B, C, D),
    Not(A),
    Not(Not(A)),
    Not(Not(And(A, B))),
    Not(Not(Or(A, B))),
]

single_polarity_examples = [
    Example(formula=And(Or(A, B), Or(C, D)),
            pol_expected_clauses=4,
            pol_expected_variables=6,
            lab_expected_clauses=8,
            lab_expected_variables=6),
    Example(formula=Or(And(A, B), And(C, D)),
            pol_expected_clauses=5,
            pol_expected_variables=6,
            lab_expected_clauses=7,
            lab_expected_variables=6),
    Example(formula=Not(Or(A, Not(And(B, Not(Or(C, D)))))),
            pol_expected_clauses=6,
            pol_expected_variables=6,
            lab_expected_clauses=8,
            lab_expected_variables=6),
    Example(formula=Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H)),
            pol_expected_clauses=11,
            pol_expected_variables=14,
            lab_expected_clauses=19,
            lab_expected_variables=14),
]

double_polarity_examples = [
    Example(formula=Or(And(A, B), And(C, Or(Not(And(A, B)), D))),
            pol_expected_clauses=7,
            pol_expected_variables=7,
            lab_expected_clauses=10,
            lab_expected_variables=7),
    Example(formula=Iff(And(C, D), Or(D, And(B, A))),
            pol_expected_clauses=11,
            pol_expected_variables=7,
            lab_expected_clauses=11,
            lab_expected_variables=7),
]
