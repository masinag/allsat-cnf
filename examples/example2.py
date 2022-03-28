import random
from example_template import *

random.seed(42)

boolean_atoms = list(boolean_atoms)[:10]

def random_formula(depth):
    if depth == 0:
        return random.choice(boolean_atoms)
    operator = random.choice([Not, Or, And])
    if operator is Not:
        return Not(random_formula(depth - 1))
    left = random_formula(depth - 1)
    right = random_formula(depth - 1)
    return operator(left, right)

formula = random_formula(10)
main(formula)