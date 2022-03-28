import random
from example_template import *

random.seed(42)

boolean_atoms = list(boolean_atoms)[:5]
real_variables = list(real_variables)[:5]


def random_coefficient(l=-1, u=1):
    coeff = 0
    while coeff == 0:
        coeff = random.uniform(l, u)
    return Real(coeff)


def random_atom():
    if random.random() < 0.5:
        return random.choice(boolean_atoms)
    else:
        minsize = 1
        maxsize = 3
        size = random.randint(minsize, maxsize)
        rvars = random.sample(real_variables, size)
        monomials = []
        for rvar in rvars:
            monomials.append(Times(random_coefficient(), rvar))

        bound = random_coefficient(0, len(real_variables))
        return LT(Plus(monomials), bound)


def random_formula(depth):
    if depth == 0:
        return random_atom()
    operator = random.choice([Not, Or, And])
    if operator is Not:
        return Not(random_formula(depth - 1))
    left = random_formula(depth - 1)
    right = random_formula(depth - 1)
    return operator(left, right)


formula = random_formula(6)
main(formula)
