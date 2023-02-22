from pysmt.shortcuts import *

from example_template import boolean_atoms, make_example

A, *_ = boolean_atoms

x1 = Symbol("x1", REAL)
x2 = Symbol("x2", REAL)

formula = Or(And(A, TRUE()), And(Not(A), TRUE()))
atoms = {A}
make_example(formula, atoms=atoms)
