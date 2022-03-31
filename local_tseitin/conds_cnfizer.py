import argparse
from pprint import pformat

from pysmt.shortcuts import *
from local_tseitin.cnfizer import LocalTseitinCNFizer

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")


class LocalTseitinCNFizerConds(LocalTseitinCNFizer):

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     self.original_symb = None

    def manage_operator(self, formula, S, S1, S2, is_leaves, pol):
        res = []
        if formula.is_and():
            # S <-> (S1 & S2)
            if pol == 0:
                res.append({Not(S), S1})
                res.append({Not(S), S2})
            else:
                res.append({Not(S1), Not(S2), S})
        elif formula.is_or():
            # S <-> (S1 | S2)
            if pol == 0:
                res.append({Not(S), S1, S2})
            else:
                res.append({Not(S1), S})
                res.append({Not(S2), S})
        elif formula.is_iff():
            res.append({Not(S), S1, Not(S2)})
            res.append({Not(S), S2, Not(S1)})
            res.append({S, S1, S2})
            res.append({S, Not(S2), Not(S1)})
        if not is_leaves:
            if (pol == 0 and formula.is_and()) or (pol == 1 and formula.is_or()):
                # S1 <-> S2
                res.append({Not(S1), S2})
                res.append({Not(S2), S1})
            elif (pol == 0 and formula.is_or()) or (pol == 1 and formula.is_and()):
                # S1 <-> !S2
                res.append({Not(S1), Not(S2)})
                res.append({S1, S2})
        return res

    def polarity(self, formula, S):
        if formula.is_and():
            return S
        else:
            return Not(S)

    def local_tseitin(self, formula, conds, S, pol, count, assertions):
        if self.verbose:
            print("{}local_tseitin({}, {}, {}, {})".format(
                "--" * count, formula, conds, S, pol))
    
        if self.is_literal(formula):
            return

        if formula.is_not():
            self.local_tseitin(formula.arg(0), conds, Not(S),
                               1-pol, count, assertions)
            return

        assert len(formula.args()) ==2, "{}".format(formula.serialize())
        left, right = formula.args()

        is_left_term = self.is_literal(left)
        is_right_term = self.is_literal(right)

        S1 = self._new_label() if not is_left_term else left
        S2 = self._new_label() if not is_right_term else right
        for tseit in self.manage_operator(formula, S, S1, S2, is_left_term and is_right_term, pol):
            assertions.append(Or({Not(S_phi) for S_phi in conds}.union(tseit)))

        if formula.is_iff():
            self.local_tseitin(left, conds.union({S if pol == 0 else Not(S)}), S1, pol, count + 1, assertions)
            self.local_tseitin(right, conds.union({S if pol == 0 else Not(S)}), S2, pol, count + 1, assertions)
        else:
            self.local_tseitin(left, conds.union({self.polarity(
                formula, S2), S if pol == 0 else Not(S)}), S1, pol, count + 1, assertions)
            self.local_tseitin(right, conds.union({self.polarity(
                formula, S1), S if pol == 0 else Not(S)}), S2, pol, count + 1, assertions)

    def convert(self, formula):
        if self.verbose:
            print("Input formula:", formula.serialize())
        formula = self.preprocessor.convert(formula)
        if self.verbose:
            print("Preprocessed formula:", formula.serialize())
        assertions = []
        S = self._new_label()
        # self.original_symb = S
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
        # print("Clauses:\n", pformat(assertions))
        cnf = And(assertions)
        assert self.is_cnf(cnf)
        return cnf
