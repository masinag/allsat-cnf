import random

from pysmt.shortcuts import And, Or, Not, Iff

from example_template import boolean_atoms, make_example

boolean_atoms = list(boolean_atoms)[:5]


def random_formula(depth):
    if depth == 0:
        operator = random.choice([Or, Not])
        if operator is Or:
            return random.choice(boolean_atoms)
        else:
            return Not(random.choice(boolean_atoms))
    operator = random.choices([Or, And, Iff], weights=[8 / 17, 8 / 17, 1 / 17], k=1)[0]
    if operator is Not:
        return Not(random_formula(depth - 1))
    left = random_formula(depth - 1)
    right = random_formula(depth - 1)
    return operator(left, right)


random.seed(666)
for i in range(0, 5):
    formula = random_formula(3)
    make_example(formula)
    print()
