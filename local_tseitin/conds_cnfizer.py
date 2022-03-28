import argparse

from pysmt.shortcuts import *

from local_tseitin.cnfizer import LocalTseitinCNFizer

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")


class LocalTseitinCNFizerConds(LocalTseitinCNFizer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_symb = None

    def manage_operator(self, formula, S, S1, S2, is_leaves, pol):
        res = []
        if pol == 0:
            if formula.is_and():
                res.append({Not(S), S1})
                res.append({Not(S), S2})
                res.append({Not(S1), Not(S2), S})
                if not is_leaves:
                    res.append({Not(S1), S2})
                    res.append({Not(S2), S1})
            elif formula.is_or():
                res.append({Not(S), S1, S2})
                res.append({Not(S1), S})
                res.append({Not(S2), S})
                if not is_leaves:
                    res.append({Not(S1), Not(S2)})
                    res.append({S1, S2})
        else:
            if formula.is_and():
                res.append({Not(S), S1})
                res.append({Not(S), S2})
                res.append({Not(S1), Not(S2), S})
                if not is_leaves:
                    res.append({Not(S1), Not(S2)})
                    res.append({S1, S2})
            elif formula.is_or():
                res.append({Not(S), S1, S2})
                res.append({Not(S1), S})
                res.append({Not(S2), S})
                if not is_leaves:
                    res.append({Not(S1), S2})
                    res.append({Not(S2), S1})
        return res

    def polarity(self, formula, S):
        if formula.is_and():
            return S
        else:
            return Not(S)

    def local_tseitin(self, formula, conds, S, pol, count, assertions):
        if self.verbose:
            print("".join(["--" for i in range(count)]) +
                  "local_tseitin({}, {}, {}, {})".format(formula, conds, S, pol))
        if formula.is_symbol() or (formula.is_not() and formula.arg(0).is_symbol()):
            return

        if formula.is_not():
            self.local_tseitin(formula.arg(0), conds, Not(S),
                               1-pol, count, assertions)
            return

        is_left_term = formula.args()[0].is_symbol() or (
            formula.arg(0).is_not() and formula.arg(0).arg(0).is_symbol())
        is_right_term = formula.args()[1].is_symbol() or (
            formula.arg(1).is_not() and formula.arg(1).arg(0).is_symbol())

        S1 = self._new_label() if not is_left_term else formula.args()[0]
        S2 = self._new_label() if not is_right_term else formula.args()[1]
        for tseit in self.manage_operator(formula, S, S1, S2, is_left_term and is_right_term, pol):
            assertions.append(Or({Not(S_phi) for S_phi in conds}.union(tseit)))

        self.local_tseitin(formula.args()[0], conds.union({self.polarity(
            formula, S2), S if pol == 0 else Not(S)}), S1, pol, count + 1, assertions)
        self.local_tseitin(formula.args()[1], conds.union({self.polarity(
            formula, S1), S if pol == 0 else Not(S)}), S2, pol, count + 1, assertions)

    def convert(self, formula):
        assertions = []
        S = self._new_label()
        self.original_symb = S
        if self.verbose:
            print("Recursive calls to local_tseitin(formula, conds, symbol, polarity):")
        if formula.is_not():
            self.local_tseitin(formula.arg(0), set(), S, 1, 0, assertions)
            assertions.append(Not(S))
        else:
            self.local_tseitin(formula, set(), S, 0, 0, assertions)
            assertions.append(S)

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in assertions:
                print(el)
            print()
        return And(assertions)
