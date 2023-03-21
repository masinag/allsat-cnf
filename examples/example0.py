import itertools

from pysmt.shortcuts import Iff, Symbol, BOOL, FALSE, TRUE, Implies, And, Not, Or

from example_template import make_example

G = Symbol("G", BOOL)
B = Symbol("B", BOOL)
G1 = Symbol("G1", BOOL)
G2 = Symbol("G2", BOOL)
B1 = Symbol("B1", BOOL)
B2 = Symbol("B2", BOOL)
phi1 = Symbol("phi1", BOOL)
phi2 = Symbol("phi2", BOOL)

psi = And(
    Implies(G, Iff(B, And(B1, B2))),
    Implies(And(G, B), And(G1, G2)),
    Implies(And(G, Not(B)), Or(B1, B2)),
    Implies(And(G, Not(B)), Iff(B2, G1)),
    Implies(And(G, Not(B)), Iff(B1, G2)),
    Implies(G1, Iff(B1, phi1)),
    Implies(G2, Iff(B2, phi2)),
)

make_example(psi)