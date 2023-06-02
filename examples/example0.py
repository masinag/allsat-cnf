from pysmt.shortcuts import Iff, Symbol, BOOL, And, Or

from example_template import make_example

A1, A2, A3, A4, A5, A6, A7 = [Symbol("A{}".format(i), BOOL) for i in range(1, 8)]

phi = Or(
    And(A1, A2),
    Iff(And(Or(A3, A4), Or(A5, A6)), A7)
)

make_example(phi)
