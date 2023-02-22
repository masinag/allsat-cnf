import random
from example_template import *

A, B, C, D, E, *_ = boolean_atoms
random.seed(666)

boolean_atoms = list(boolean_atoms)[:4]


def random_formula(depth):
    if depth == 0:
        operator = random.choice([Or, Not])
        if operator is Or:
            return random.choice(boolean_atoms)
        else:
            return Not(random.choice(boolean_atoms))
            # operator = random.choice([Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Iff])
    operator = random.choices([Or, And, Iff], weights=[8 / 17, 8 / 17, 1 / 17], k=1)[0]
    if operator is Not:
        return Not(random_formula(depth - 1))
    left = random_formula(depth - 1)
    right = random_formula(depth - 1)
    return operator(left, right)


for i in range(1, 2):
    formula = random_formula(3)
    nmodels_mathsat, time_mathsat, nmodels_local, time_local = make_example(formula)
