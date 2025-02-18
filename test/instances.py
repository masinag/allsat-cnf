from collections import namedtuple

from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.shortcuts import And, Or, Not

Example = namedtuple('Example', ['formula',
                                 'dm_expected_clauses', 'dm_expected_variables',
                                 'pol_expected_clauses', 'pol_expected_variables',
                                 'lab_expected_clauses', 'lab_expected_variables',
                                 'nnf_pol_expected_clauses', 'nnf_pol_expected_variables',
                                 'nnf_lab_expected_clauses', 'nnf_lab_expected_variables',
                                 'nnf_mutex_pol_expected_clauses', 'nnf_mutex_pol_expected_variables'])


def make_identity_examples(atoms: list[FNode]) -> list[Example]:
    A, B, C, D, *_ = atoms
    return [
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


def make_single_polarity_examples(atoms: list[FNode]) -> list[Example]:
    A, B, C, D, E, F, G, H, *_ = atoms
    return [
        Example(formula=And(Or(A, B), Or(C, D)),
                dm_expected_clauses=2,
                dm_expected_variables=4,
                pol_expected_clauses=4,
                pol_expected_variables=6,
                lab_expected_clauses=8,
                lab_expected_variables=6,
                nnf_pol_expected_clauses=4,
                nnf_pol_expected_variables=6,
                nnf_lab_expected_clauses=8,
                nnf_lab_expected_variables=6,
                nnf_mutex_pol_expected_clauses=4,
                nnf_mutex_pol_expected_variables=6),
        Example(formula=Or(And(A, B), And(C, D)),
                dm_expected_clauses=4,
                dm_expected_variables=4,
                pol_expected_clauses=5,
                pol_expected_variables=6,
                lab_expected_clauses=7,
                lab_expected_variables=6,
                nnf_pol_expected_clauses=5,
                nnf_pol_expected_variables=6,
                nnf_lab_expected_clauses=7,
                nnf_lab_expected_variables=6,
                nnf_mutex_pol_expected_clauses=5,
                nnf_mutex_pol_expected_variables=6),
        Example(formula=Not(Or(A, Not(And(B, Not(Or(C, D)))))),
                dm_expected_clauses=4,
                dm_expected_variables=4,
                pol_expected_clauses=6,
                pol_expected_variables=6,
                lab_expected_clauses=8,
                lab_expected_variables=6,
                nnf_pol_expected_clauses=6,
                nnf_pol_expected_variables=6,
                nnf_lab_expected_clauses=8,
                nnf_lab_expected_variables=6,
                nnf_mutex_pol_expected_clauses=6,
                nnf_mutex_pol_expected_variables=6),
        Example(formula=Or(Or(Or(And(A, B), And(C, D)), And(E, F)), Not(And(G, H))),
                dm_expected_clauses=8,
                dm_expected_variables=8,
                pol_expected_clauses=10,
                pol_expected_variables=14,
                lab_expected_clauses=19,
                lab_expected_variables=14,
                nnf_pol_expected_clauses=10,
                nnf_pol_expected_variables=14,
                nnf_lab_expected_clauses=19,
                nnf_lab_expected_variables=14,
                nnf_mutex_pol_expected_clauses=10,
                nnf_mutex_pol_expected_variables=14),
    ]


def make_double_polarity_examples(atoms: list[FNode]) -> list[Example]:
    A, B, C, D, E, F, G, H, *_ = atoms
    return [
        Example(formula=Or(And(A, B), And(C, Or(Not(And(A, B)), D))),
                dm_expected_clauses=2,
                dm_expected_variables=3,
                pol_expected_clauses=7,
                pol_expected_variables=7,
                lab_expected_clauses=10,
                lab_expected_variables=7,
                nnf_pol_expected_clauses=7,
                nnf_pol_expected_variables=8,
                nnf_lab_expected_clauses=13,
                nnf_lab_expected_variables=8,
                nnf_mutex_pol_expected_clauses=8,
                nnf_mutex_pol_expected_variables=8),
        Example(formula=Iff(And(C, D), Or(D, And(B, A))),
                dm_expected_clauses=3,
                dm_expected_variables=4,
                pol_expected_clauses=11,
                pol_expected_variables=7,
                lab_expected_clauses=11,
                lab_expected_variables=7,
                nnf_pol_expected_clauses=13,
                nnf_pol_expected_variables=12,
                nnf_lab_expected_clauses=26,
                nnf_lab_expected_variables=12,
                nnf_mutex_pol_expected_clauses=16,
                nnf_mutex_pol_expected_variables=12),
        Example(formula=Or(And(C, D), Not(Iff(And(C, D), Or(D, And(B, A))))),
                dm_expected_clauses=6,
                dm_expected_variables=4,
                pol_expected_clauses=12,
                pol_expected_variables=8,
                lab_expected_clauses=14,
                lab_expected_variables=8,
                nnf_pol_expected_clauses=15,
                nnf_pol_expected_variables=13,
                nnf_lab_expected_clauses=28,
                nnf_lab_expected_variables=13,
                nnf_mutex_pol_expected_clauses=18,
                nnf_mutex_pol_expected_variables=13),
        Example(
            formula=Not(
                Iff(And(Not(And(Not(A), C)), Or(Not(B), Not(D))), And(Not(And(D, Not(E))), Not(And(Not(B), E))))),
            dm_expected_clauses=11,
            dm_expected_variables=5,
            pol_expected_clauses=20,
            pol_expected_variables=11,
            lab_expected_clauses=20,
            lab_expected_variables=11,
            nnf_pol_expected_clauses=23,
            nnf_pol_expected_variables=19,
            nnf_lab_expected_clauses=43,
            nnf_lab_expected_variables=19,
            nnf_mutex_pol_expected_clauses=32,
            nnf_mutex_pol_expected_variables=19),
    ]


def make_bool_ite_examples(atoms: list[FNode]) -> list[Example]:
    A, B, C, D, E, F, G, H, *_ = atoms
    return [
        Example(
            formula=Ite(A, B, C),
            dm_expected_clauses=2,
            dm_expected_variables=3,
            pol_expected_clauses=2,
            pol_expected_variables=3,
            lab_expected_clauses=2,
            lab_expected_variables=3,
            nnf_pol_expected_clauses=4,
            nnf_pol_expected_variables=5,
            nnf_lab_expected_clauses=8,
            nnf_lab_expected_variables=5,
            nnf_mutex_pol_expected_clauses=4,
            nnf_mutex_pol_expected_variables=5
        ),
        Example(
            formula=Ite(Ite(A, B, C), Ite(Ite(D, B, C), E, F), G),
            dm_expected_clauses=13,
            dm_expected_variables=7,
            pol_expected_clauses=12,
            pol_expected_variables=10,
            lab_expected_clauses=14,
            lab_expected_variables=10,
            nnf_pol_expected_clauses=26,
            nnf_pol_expected_variables=24,
            nnf_lab_expected_clauses=53,
            nnf_lab_expected_variables=24,
            nnf_mutex_pol_expected_clauses=28,
            nnf_mutex_pol_expected_variables=24
        )
    ]


def make_lra_ite_examples(atoms, variables) -> list[Example]:
    A, B, C, D, E, F, G, H, *_ = atoms
    x, y, *_ = variables
    return [
        Example(
            formula=(y > Ite(x <= Real(0.5), Real(0.5), Real(1.0))),
            dm_expected_clauses=1,
            dm_expected_variables=1,
            pol_expected_clauses=1,
            pol_expected_variables=1,
            lab_expected_clauses=1,
            lab_expected_variables=1,
            nnf_pol_expected_clauses=1,
            nnf_pol_expected_variables=1,
            nnf_lab_expected_clauses=1,
            nnf_lab_expected_variables=1,
            nnf_mutex_pol_expected_clauses=1,
            nnf_mutex_pol_expected_variables=1
        ),
        Example(formula=And(Or(x > (Ite(A, Real(2.0), Real(1.0))), B),
                            Or(C, (x <= Ite(D, Ite(E, Real(0.5), Real(1.0)), y)))),
                # note: atoms within theory ITEs are not detected
                dm_expected_clauses=2,
                dm_expected_variables=4,
                pol_expected_clauses=4,
                pol_expected_variables=6,
                lab_expected_clauses=8,
                lab_expected_variables=6,
                nnf_pol_expected_clauses=4,
                nnf_pol_expected_variables=6,
                nnf_lab_expected_clauses=8,
                nnf_lab_expected_variables=6,
                nnf_mutex_pol_expected_clauses=4,
                nnf_mutex_pol_expected_variables=6),
        Example(
            formula=(x > Ite(And(A, B), Ite(Or(B, C), Real(1.0), Real(2.0)), y)),
            dm_expected_clauses=1,
            dm_expected_variables=1,
            pol_expected_clauses=1,
            pol_expected_variables=1,
            lab_expected_clauses=1,
            lab_expected_variables=1,
            nnf_pol_expected_clauses=1,
            nnf_pol_expected_variables=1,
            nnf_lab_expected_clauses=1,
            nnf_lab_expected_variables=1,
            nnf_mutex_pol_expected_clauses=1,
            nnf_mutex_pol_expected_variables=1
        ),
    ]


# initialize bool variables
boolean_variables = [Symbol(chr(i), BOOL) for i in range(ord("A"), ord("Z") + 1)]
real_variables = [Symbol(chr(i), REAL) for i in range(ord("a"), ord("z") + 1)]

boolean_atoms = boolean_variables
A, B, *_ = boolean_variables
x, y, z, *_ = real_variables
real_atoms = [
    x <= 0.5,
    y <= 0.5,
    x + 3 * y <= 0.5,
    x + 3 * y + 2 * z <= 0.5,
    x + 3 * y + 2 * z + 1 <= 0.5,
    A,
    B,
    x + 3 * y + 2 * z + 1 <= x + 3 * y + 2 * z,
]

bool_identity_examples = make_identity_examples(boolean_atoms)
lra_identity_examples = make_identity_examples(real_atoms)

bool_single_polarity_examples = make_single_polarity_examples(boolean_atoms)
lra_single_polarity_examples = make_single_polarity_examples(real_atoms)

bool_double_polarity_examples = make_double_polarity_examples(boolean_atoms)
lra_double_polarity_examples = make_double_polarity_examples(real_atoms)

bool_ite_examples = make_bool_ite_examples(boolean_atoms)
lra_ite_examples = make_lra_ite_examples(boolean_atoms, real_variables)
