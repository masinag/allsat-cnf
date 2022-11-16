from pysmt.shortcuts import *
from pysmt.formula import FNode

Formula = FNode
Symbol = FNode


def new_label() -> Formula:
    return FreshSymbol()


def is_literal(phi: Formula) -> bool:
    return not phi.args() or phi.is_not() and not phi.args(0).args()


def de_morgan(phi: Formula) -> Formula:
    pass


def tseitin_rec(phi: Formula) -> tuple[Symbol, Formula]:
    if is_literal(phi):
        return phi, TRUE()

    S = new_label()

    match phi:
        # leaf nodes
        case And(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, And(lit1, lit2)))
        case Or(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, Or(lit1, lit2)))
        case Iff(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, Iff(lit1, lit2)))
        # internal nodes
        case Not(phi1):
            S1, cnf1 = tseitin_rec(phi1)
            return Not(S1), cnf1
        case And(phi1, phi2):
            S1, cnf1 = tseitin_rec(phi1)
            S2, cnf2 = tseitin_rec(phi2)
            return S, And(de_morgan(Iff(S, And(S1, S2))), cnf1, cnf2)
        case Or(phi1, phi2):
            S1, cnf1 = tseitin_rec(phi1)
            S2, cnf2 = tseitin_rec(phi2)
            return S, And(de_morgan(Iff(S, Or(S1, S2))), cnf1, cnf2)
        case Iff(phi1, phi2):
            S1, cnf1 = tseitin_rec(phi1)
            S2, cnf2 = tseitin_rec(phi2)
            return S, And(de_morgan(Iff(S, Iff(S1, S2))), cnf1, cnf2)


def tseitin(phi: Formula) -> Formula:
    S, cnf = tseitin_rec(phi)
    return And(S, cnf)


def local_tseitin_rec(phi: Formula) -> tuple[Symbol, Formula]:
    if is_literal(phi):
        return phi, TRUE()

    S = new_label()

    match phi:
        # leaf nodes
        case And(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, And(lit1, lit2)))
        case Or(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, Or(lit1, lit2)))
        case Iff(lit1, lit2) if is_literal(lit1) and is_literal(lit2):
            return S, de_morgan(Iff(S, Iff(lit1, lit2)))
        # internal nodes
        case Not(phi1):
            S1, cnf1 = local_tseitin_rec(phi1)
            return Not(S1), cnf1
        case And(phi1, phi2):
            S1, cnf1 = local_tseitin_rec(phi1)
            S2, cnf2 = local_tseitin_rec(phi2)
            # manca il polarizer
            return S, And(
                de_morgan(Iff(S, And(S1, S2))),
                de_morgan(Or(Not(S2), cnf1)),
                de_morgan(Or(Not(S1), cnf2))
            )
        case Or(phi1, phi2):
            S1, cnf1 = local_tseitin_rec(phi1)
            S2, cnf2 = local_tseitin_rec(phi2)
            # manca il polarizer
            return S, And(
                de_morgan(Iff(S, Or(S1, S2))),
                Or(Not(S1), Not(S2)),
                de_morgan(Or(S2, cnf1)),
                de_morgan(Or(S1, cnf2))
            )

        case Iff(phi1, phi2):
            S1, cnf1 = local_tseitin_rec(phi1)
            S2, cnf2 = local_tseitin_rec(phi2)
            return S, And(de_morgan(Iff(S, Or(S1, S2))), cnf1, cnf2)