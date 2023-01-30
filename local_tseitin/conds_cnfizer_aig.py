import argparse
from pprint import pformat

from pysmt.shortcuts import *
from local_tseitin.cnfizer import LocalTseitinCNFizer
from local_tseitin.utils import is_literal, is_cnf

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-g", help="set how many guards to add", type=int,
                    action="store")


class LocalTseitinCNFizerCondsAIG(LocalTseitinCNFizer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash_set = dict()
        self.all_clauses = []

    def get_type(self, formula):
        if formula.is_not():
            return "NOT"
        if formula.is_and():
            return "AND"
        if formula.is_or():
            return "OR"
        if formula.is_iff():
            return "IFF"

    def lt_pol(self, formula, count):
        if self.verbose:
            print("{}local_tseitin_rec({})".format(
                "--" * count, formula))

        # CASO BASE 1: formula monovariabile
        if is_literal(formula):
            return [([Bool(True)], 0)], formula, formula, True

        # CASO NOT(AND) PER AIG

        if formula.is_not():
            formula_neg = formula.arg(0)
            left, right = formula_neg.args()
            S = self._new_label()
            P = self._new_polarizer()
            clauses = []

            cnf1, S1, P1 = self.lt_pol(left, count + 1)
            cnf2, S2, P2 = self.lt_pol(right, count + 1)

            if formula_neg.is_and():
                # S <-> -S1 v -S2
                clauses.append(([Not(S), Not(S1), Not(S2)], self.max_guards))
                clauses.append(([S, S1], self.max_guards))
                clauses.append(([S, S2], self.max_guards))
                # S2 -> CNF1
                for f in cnf1:
                    if f[1] is None or f[1] > 0:
                        f = ([Not(S2)] + f[0], f[1] - 1) if f[1] is not None else ([Not(S2)] + f[0], f[1])
                    clauses.append(f)
                # S1 -> CNF2
                for f in cnf2:
                    if f[1] is None or f[1] > 0:
                        f = ([Not(S1)] + f[0], f[1] - 1) if f[1] is not None else ([Not(S1)] + f[0], f[1])
                    clauses.append(f)
                # S -> -S1 v -S2
                if not is_literal(left) or not is_literal(right):
                    clauses.append(([Not(S), S1, S2], self.max_guards))
                return clauses, S, P

        clauses = []
        left, right = formula.args()

        # CASO BASE 2: leaf operator
        if is_literal(left) and is_literal(right):
            S1 = left
            S2 = right

            if frozenset([S1, S2, get_type(formula)]) in self.hash_set:
                S, P = self.hash_set[frozenset([S1, S2, self.get_type(formula)])]
                return clauses, S, P, False

            S = self._new_label()
            P = self._new_polarizer()
            self.hash_set[frozenset([S1, S2, self.get_type(formula)])] = [S, P]
            if formula.is_or():
                # (S <-> S1 v S2)
                self.all_clauses.append(([Not(P), Not(S), S1, S2], self.max_guards))
                self.all_clauses.append(([Not(P), S, Not(S1)], self.max_guards))
                self.all_clauses.append(([Not(P), S, Not(S2)], self.max_guards))
                if self.verbose:
                    print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
            if formula.is_and():
                # (S <-> S1 ^ S2)
                self.all_clauses.append(([Not(P), S, Not(S1), Not(S2)], self.max_guards))
                self.all_clauses.append(([Not(P), Not(S), S1], self.max_guards))
                self.all_clauses.append(([Not(P), Not(S), S2], self.max_guards))
                if self.verbose:
                    print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
            if formula.is_iff():
                # (S <-> S1 <-> S2)
                self.all_clauses.append(([Not(P), Not(S), S1, Not(S2)], self.max_guards))
                self.all_clauses.append(([Not(P), Not(S), S2, Not(S1)], self.max_guards))
                self.all_clauses.append(([Not(P), S, S1, S2], self.max_guards))
                self.all_clauses.append(([Not(P), S, Not(S2), Not(S1)], self.max_guards))
                if self.verbose:
                    print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))
            return clauses, S, P, False

        assert len(formula.args()) == 2, "{}".format(formula.serialize())

        cnf1, S1, P1, leaf1 = self.lt_pol(left, count + 1)
        cnf2, S2, P2, leaf2 = self.lt_pol(right, count + 1)

        if S1 == S2:
            # Trivial case
            return cnf1, S1, P1, leaf1

        if frozenset([S1, S2, get_type(formula)]) in self.hash_set:
            S, P = self.hash_set[frozenset([S1, S2, self.get_type(formula)])]
            return clauses, S, P, False

        S = self._new_label()
        P = self._new_polarizer()
        self.hash_set[frozenset([S1, S2, self.get_type(formula)])] = [S, P]

        if formula.is_or():
            # S <-> S1 v S2
            if self.verbose:
                print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
            self.all_clauses.append(([Not(P), Not(S), S1, S2], self.max_guards))
            self.all_clauses.append(([Not(P), S, Not(S1)], self.max_guards))
            self.all_clauses.append(([Not(P), S, Not(S2)], self.max_guards))

            # S -> -S1 v -S2
            if self.verbose:
                print("{} -> ({} -> Not({}) or Not({}))".format(P, S, S1, S2))
                print("{} -> ({} -> Not({}) or Not({}))".format(P, S, P1, P2))

            self.all_clauses.append(([Not(P), Not(S), Not(S1), Not(S2)], self.max_guards))
            self.all_clauses.append(([Not(P), Not(S), Not(P1), Not(P2)], self.max_guards))

            if not leaf2:
                if self.verbose:
                    print("{} and Not({}) -> {})".format(P, S1, P2))
                    print("Not({}) -> Not({}))".format(P, P2))
                self.all_clauses.append(([Not(P), S1, P2], self.max_guards))
                self.all_clauses.append(([P, Not(P2)], self.max_guards))
            if not leaf1:
                if self.verbose:
                    print("{} and Not({}) -> {})".format(P, S2, P1))
                    print("Not({}) -> Not({}))".format(P, P1))
                self.all_clauses.append(([Not(P), S2, P1], self.max_guards))
                self.all_clauses.append(([P, Not(P1)], self.max_guards))
        if formula.is_and():
            # S <-> S1 v S2
            if self.verbose:
                print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
            self.all_clauses.append(([Not(P), S, Not(S1), Not(S2)], self.max_guards))
            self.all_clauses.append(([Not(P), Not(S), S1], self.max_guards))
            self.all_clauses.append(([Not(P), Not(S), S2], self.max_guards))
            # -S -> S1 v S2

            if self.verbose:
                print("{} -> (Not({}) -> {} or {})".format(P, S, S1, S2))
                print("{} -> (Not({}) -> {} or {})".format(P, S, P1, P2))

            self.all_clauses.append(([Not(P), S, S1, S2], self.max_guards))
            self.all_clauses.append(([Not(P), S, Not(P1), Not(P2)], self.max_guards))

            # self.all_clauses.append(([S, S1, S2], self.guards))
            if self.verbose:
                print("left branch {} is {}".format(left, leaf1))
                print("right branch {} is {}".format(right, leaf2))
            if not leaf2:
                if self.verbose:
                    print("{} and {} -> {}".format(P, S1, P2))
                    print("Not({}) -> Not({}))".format(P, P2))
                self.all_clauses.append(((Not(P), Not(S1), P2), self.max_guards))
                self.all_clauses.append(([P, Not(P2)], self.max_guards))

            if not leaf1:
                if self.verbose:
                    print("{} and {} -> {}".format(P, S2, P1))
                    print("Not({}) -> Not({}))".format(P, P1))
                self.all_clauses.append(((Not(P), P1, Not(S2)), self.max_guards))
                self.all_clauses.append(([P, Not(P1)], self.max_guards))
        if formula.is_iff():
            # S <-> S1 <-> S2
            self.all_clauses.append(([Not(P), Not(S), S1, Not(S2)], self.max_guards))
            self.all_clauses.append(([Not(P), Not(S), S2, Not(S1)], self.max_guards))
            self.all_clauses.append(([Not(P), S, S1, S2], self.max_guards))
            self.all_clauses.append(([Not(P), S, Not(S2), Not(S1)], self.max_guards))
            if self.verbose:
                print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))

            if not leaf1:
                # self.all_clauses.append(([P, Not(P1)], self.guards))
                self.all_clauses.append(([P1, Not(P)], self.max_guards))

                if self.verbose:
                    print("({} -> {})".format(P, P1))

            if not leaf2:
                # self.all_clauses.append(([P, Not(P2)], self.guards))
                self.all_clauses.append(([P2, Not(P)], self.max_guards))

                if self.verbose:
                    print("({} -> {})".format(P, P2))
        return clauses, S, P, False

    def convert_as_formula(self, formula):
        if self.verbose:
            print("Input formula:", formula.serialize())
            print(self.all_clauses)
            print(self.hash_set)
        formula = self.preprocessor.convert_as_formula(formula)
        if self.verbose:
            print("Preprocessed formula:", formula.serialize())
        assertions = []
        S = self._new_label()
        P = self._new_polarizer()
        # self.original_symb = S
        if self.verbose:
            print("Recursive calls to local_tseitin(formula, conds, symbol, polarity):")
        """
        if formula.is_not():
            self.local_tseitin(formula.arg(0), set(), S, 1, 0, assertions, None)
            assertions.append(Not(S))
        else:
            self.local_tseitin(formula, set(), S, 0, 0, assertions, None)
            assertions.append(S)
        """

        # cnf = self.local_tseitin_rec(formula, set(), S, 0, P)
        cnf, S, P, _ = self.lt_pol(formula, 0)
        # cnf, S = self.lt_pol_orig(formula, 0)
        if self.verbose:
            print("{} and {}".format(S, P))
        # print("SIZE NEW FORMULA:", len(cnf))
        self.all_clauses.reverse()
        cnf = [f[0] for f in self.all_clauses]
        cnf = And([Or(c) for c in cnf])

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()
        cnf = substitute(cnf, {S: Bool(True), P: Bool(True)})

        cnf = simplify(cnf)

        # cnf = And(assertions)
        assert is_cnf(cnf)
        self.hash_set.clear()
        self.all_clauses.clear()
        return cnf
