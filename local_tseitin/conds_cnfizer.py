import argparse
from pprint import pformat

from pysmt.shortcuts import *
from local_tseitin.cnfizer import LocalTseitinCNFizer

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-g", help="set how many guards to add", type=int,
                    action="store")


class LocalTseitinCNFizerConds(LocalTseitinCNFizer):

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     self.original_symb = None

    def manage_operator(self, formula, S, S1, S2, is_leaves, pol, polarizer):
        res = []
        if formula.is_and():
            # S <-> (S1 & S2)
            res.append({Not(S), S1})
            res.append({Not(S), S2})
            res.append({Not(S1), Not(S2), S})
        elif formula.is_or():
            # S <-> (S1 | S2)
            res.append({Not(S), S1, S2})
            res.append({Not(S1), S})
            res.append({Not(S2), S})
        elif formula.is_iff():
            res.append({Not(S), S1, Not(S2)})
            res.append({Not(S), S2, Not(S1)})
            res.append({S, S1, S2})
            res.append({S, Not(S2), Not(S1)})
        if not is_leaves:
            # OLD CONDITION
            # if (pol == 0 and formula.is_or()) or (pol == 1 and formula.is_and()):
            # S1 <-> !S2
            # res.append({Not(S), Not(S1), Not(S2)})
            # res.append({Not(S), S1, S2})
            if formula.is_and() and polarizer is not None:
                res.append({polarizer, S1, S2})
                res.append({polarizer, Not(S1), Not(S2)})
            elif formula.is_or() and polarizer is not None:
                res.append({Not(polarizer), S1, S2})
                res.append({Not(polarizer), Not(S1), Not(S2)})
            elif formula.is_or() and polarizer is None and pol == 0:
                res.append({S1, S2})
                res.append({Not(S1), Not(S2)})
            elif formula.is_and() and polarizer is None and pol == 1:
                res.append({S1, S2})
                res.append({Not(S1), Not(S2)})

        return res

    def polarity(self, formula, S):
        if formula.is_and():
            return S
        else:
            return Not(S)

    def local_tseitin(self, formula, conds, S, pol, count, assertions, polarizer):
        if self.verbose:
            print("{}local_tseitin({}, {}, {}, {}, {})".format(
                "--" * count, formula, conds, S, pol, polarizer))

        if self.is_literal(formula):
            return

        if formula.is_not():
            if polarizer is None:
                self.local_tseitin(formula.arg(0), conds, Not(S),
                                   1 - pol, count, assertions, polarizer)
            else:
                new_P = self._new_label()
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_P), Not(polarizer)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_P, polarizer})))
                self.local_tseitin(formula.arg(0), conds, Not(S), 1 - pol, count, assertions, new_P)
            return

        assert len(formula.args()) == 2, "{}".format(formula.serialize())
        left, right = formula.args()

        is_left_term = self.is_literal(left)
        is_right_term = self.is_literal(right)

        S1 = self._new_label() if not is_left_term else left
        S2 = self._new_label() if not is_right_term else right
        for tseit in self.manage_operator(formula, S, S1, S2, is_left_term and is_right_term, pol, polarizer):
            assertions.append(Or({Not(S_phi) for S_phi in conds}.union(tseit)))

        if formula.is_iff():
            # Left branch
            if polarizer is None:
                new_Pl = self._new_label()
                if pol == 0:
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), S2})))
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S2), new_Pl})))
                else:
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), Not(S2)})))
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({S2, new_Pl})))
                self.local_tseitin(left, conds, S1, pol, count + 1, assertions, new_Pl)
            else:
                new_Pl = self._new_label()
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), Not(polarizer), S2})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), polarizer, Not(S2)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pl, Not(polarizer), Not(S2)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pl, polarizer, S2})))
                self.local_tseitin(left, conds, S1, pol, count + 1, assertions, new_Pl)

            # Right branch
            if polarizer is None:
                new_Pr = self._new_label()
                if pol == 0:
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), S1})))
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S1), new_Pr})))
                else:
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), Not(S1)})))
                    assertions.append(Or({Not(S_phi) for S_phi in conds}.union({S1, new_Pr})))
                self.local_tseitin(right, conds, S2, pol, count + 1, assertions, new_Pr)
            else:
                new_Pr = self._new_label()
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), Not(polarizer), S1})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), polarizer, Not(S1)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pr, Not(polarizer), Not(S1)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pr, polarizer, S1})))
                self.local_tseitin(right, conds, S2, pol, count + 1, assertions, new_Pr)

            # self.local_tseitin(left, conds, S1, pol, count + 1, assertions, new_P)
            # self.local_tseitin(right, conds, S2, pol, count + 1, assertions, new_P)
        elif formula.is_and():
            # ORIGINAL COMMON PART
            # self.local_tseitin(left, conds.union({self.polarity(
            #    formula, S2)}), S1, pol, count + 1, assertions, polarizer)
            # self.local_tseitin(right, conds.union({self.polarity(
            #    formula, S1)}), S2, pol, count + 1, assertions, polarizer)
            self.local_tseitin(left, conds.union({S2}), S1, pol, count + 1, assertions, polarizer)
            self.local_tseitin(right, conds.union({S1}), S2, pol, count + 1, assertions, polarizer)
        else:
            self.local_tseitin(left, conds.union({Not(S2)}), S1, pol, count + 1, assertions, polarizer)
            self.local_tseitin(right, conds.union({Not(S1)}), S2, pol, count + 1, assertions, polarizer)

    def local_tseitin_rec(self, formula, conds, S, count, polarizer):
        if self.verbose:
            print("{}local_tseitin_rec({}, {}, {}, {})".format(
                "--" * count, formula, conds, S, polarizer))

        # CASO BASE 1: formula monovariabile
        if self.is_literal(formula):
            return formula

        left, right = formula.args()

        # CASO BASE 2: leaf operator
        if self.is_literal(left) and self.is_literal(right):
            S1 = left
            S2 = right
            clauses = []
            if formula.is_or():
                # And(conds) -> (S <-> S1 v S2)
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1, S2})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S1)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S2)})))
            if formula.is_and():
                # And(conds) -> (S <-> S1 ^ S2)
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S1), Not(S2)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S2})))
            if formula.is_iff():
                # And(conds) -> (S <-> S1 <-> S2)
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1, Not(S2)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S2, Not(S1)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, S1, S2})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S2), Not(S1)})))
            return And(clauses)

        assert len(formula.args()) == 2, "{}".format(formula.serialize())

        S1 = self._new_label() if not self.is_literal(left) else left
        S2 = self._new_label() if not self.is_literal(right) else right

        clauses = []
        if formula.is_or():
            # And(conds) -> (S <-> S1 v S2)
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(polarizer), Not(S), S1, S2})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({polarizer, S, Not(S1)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({polarizer, S, Not(S2)})))

            # NEW: not both true if it is actually a OR, using polarizer
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(polarizer), Not(S1), Not(S2)})))

            return And([c for c in clauses] +
                       ([c for c in self.local_tseitin_rec(left, conds.union({Not(S2)}), S1, count + 1,
                                                           polarizer).args()] if not self.is_literal(left) else []) +
                       ([c for c in self.local_tseitin_rec(right, conds.union({Not(S1)}), S2, count + 1,
                                                           polarizer).args()] if not self.is_literal(right) else [])
                       )

        if formula.is_and():
            # And(conds) -> (S <-> S1 ^ S2)
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({polarizer, S, Not(S1), Not(S2)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(polarizer), Not(S), S1})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(polarizer), Not(S), S2})))

            # NEW: not both false it is a AND negated, thus a OR, using polarizer
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({polarizer, S1, S2})))

            return And(
                [c for c in clauses] +
                ([c for c in self.local_tseitin_rec(left, conds.union({S2}), S1, count + 1,
                                                    polarizer).args()] if not self.is_literal(left) else []) +
                ([c for c in self.local_tseitin_rec(right, conds.union({S1}), S2, count + 1,
                                                    polarizer).args()] if not self.is_literal(right) else [])
            )

        if formula.is_iff():
            # And(conds) -> (S <-> S1 <-> S2)
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1, Not(S2)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S2, Not(S1)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, S1, S2})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S2), Not(S1)})))

            if not self.is_literal(left):
                new_Pl = self._new_polarizer()
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), Not(polarizer), S2})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pl), polarizer, Not(S2)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pl, Not(polarizer), Not(S2)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pl, polarizer, S2})))
            else:
                new_Pl = polarizer

            if not self.is_literal(right):
                new_Pr = self._new_polarizer()
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), Not(polarizer), S1})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_Pr), polarizer, Not(S1)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pr, Not(polarizer), Not(S1)})))
                clauses.append(Or({Not(S_phi) for S_phi in conds}.union({new_Pr, polarizer, S1})))
            else:
                new_Pr = polarizer

            return And(
                [c for c in clauses] +
                ([c for c in self.local_tseitin_rec(left, conds, S1, count + 1, new_Pl).args()] if not self.is_literal(
                    left) else []) +
                ([c for c in self.local_tseitin_rec(right, conds, S2, count + 1, new_Pr).args()] if not self.is_literal(
                    right) else [])
            )

    def lt_pol(self, formula, count):
        if self.verbose:
            print("{}local_tseitin_rec({})".format(
                "--" * count, formula))

        # CASO BASE 1: formula monovariabile
        if self.is_literal(formula):
            return [([Bool(True)], 0)], formula

        # CASO NOT formula
        if formula.is_not():
            formula_neg = formula.arg(0)
            cnf, S = self.lt_pol(formula_neg, count + 1)
            return cnf, Not(S).simplify()

        left, right = formula.args()
        S = self._new_label()
        not_S = Not(S).simplify()
        clauses = []

        # CASO BASE 2: leaf operator
        if self.is_literal(left) and self.is_literal(right):
            S1 = left
            not_S1 = Not(S1).simplify()
            S2 = right
            not_S2 = Not(S2).simplify()
            if formula.is_or():
                # (S <-> S1 v S2)
                clauses.append(([not_S, S1, S2], self.guards))
                clauses.append(([S, not_S1], self.guards))
                clauses.append(([S, not_S2], self.guards))
            if formula.is_and():
                # (S <-> S1 ^ S2)
                clauses.append(([S, not_S1, not_S2], self.guards))
                clauses.append(([not_S, S1], self.guards))
                clauses.append(([not_S, S2], self.guards))
            if formula.is_iff():
                # (S <-> S1 <-> S2)
                clauses.append(([not_S, S1, not_S2], self.guards))
                clauses.append(([not_S, S2, not_S1], self.guards))
                clauses.append(([S, S1, S2], self.guards))
                clauses.append(([S, not_S2, not_S1], self.guards))
            return clauses, S

        assert len(formula.args()) == 2, "{}".format(formula.serialize())

        cnf1, S1 = self.lt_pol(left, count + 1)
        not_S1 = Not(S1).simplify()
        cnf2, S2 = self.lt_pol(right, count + 1)
        not_S2 = Not(S2).simplify()

        if formula.is_or():
            # S <-> S1 v S2
            clauses.append(([not_S, S1, S2], self.guards))
            clauses.append(([S, not_S1], self.guards))
            clauses.append(([S, not_S2], self.guards))
            # -S2 -> CNF1
            for f in cnf1:
                if f[1] is None or f[1] > 0:
                    f = ([S2] + f[0], f[1] - 1) if f[1] is not None else ([S2] + f[0], f[1])
                clauses.append(f)
            # -S1 -> CNF2
            for f in cnf2:
                if f[1] is None or f[1] > 0:
                    f = ([S1] + f[0], f[1] - 1) if f[1] is not None else ([S1] + f[0], f[1])
                clauses.append(f)
            # S -> -S1 v -S2
            clauses.append(([not_S, not_S1, not_S2], self.guards))
        if formula.is_and():
            # S <-> S1 v S2
            clauses.append(([S, not_S1, not_S2], self.guards))
            clauses.append(([not_S, S1], self.guards))
            clauses.append(([not_S, S2], self.guards))
            # S2 -> CNF1
            for f in cnf1:
                if f[1] is None or f[1] > 0:
                    f = ([not_S2] + f[0], f[1] - 1) if f[1] is not None else ([not_S2] + f[0], f[1])
                clauses.append(f)
            # S1 -> CNF2
            for f in cnf2:
                if f[1] is None or f[1] > 0:
                    f = ([not_S1] + f[0], f[1] - 1) if f[1] is not None else ([not_S1] + f[0], f[1])
                clauses.append(f)
            # -S -> S1 v S2
            clauses.append(([S, S1, S2], self.guards))
        if formula.is_iff():
            # S <-> S1 <-> S2
            clauses.append(([not_S, S1, not_S2], self.guards))
            clauses.append(([not_S, S2, not_S1], self.guards))
            clauses.append(([S, S1, S2], self.guards))
            clauses.append(([S, not_S2, not_S1], self.guards))
            for f in cnf1:
                clauses.append(f)
            for f in cnf2:
                clauses.append(f)
        return clauses, S

    def convert_as_formula(self, formula):
        if self.verbose:
            print("Input formula:", formula.serialize())
        formula = self.preprocessor.convert_as_formula(formula)
        if self.verbose:
            print("Preprocessed formula:", formula.serialize())

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
        clauses, S = self.lt_pol(formula, 0)
        S_neg = Not(S).simplify()
        # print("SIZE NEW FORMULA:", len(cnf))
        cnf = []

        for clause in clauses:
            clause = clause[0]
            _clause = []
            for lit in clause:
                if lit == S:
                    # ignore clauses as !S -> ...
                    _clause.clear()
                    break
                elif lit == S_neg:
                    # convert S -> l1 v ... lk into l1 v ... lk
                    continue
                else:
                    _clause.append(lit)
            if _clause:
                cnf.append(_clause)
        cnf = And([Or(c) for c in cnf])

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()

        assert self.is_cnf(cnf), cnf.serialize()
        return cnf


class LocalTseitinCNFizerShared(LocalTseitinCNFizer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash_set = dict()
        self.activators = dict()

    def lt_pol(self, formula, count):
        if self.verbose:
            print("{}local_tseitin_rec({})".format(
                "--" * count, formula))

        # CASO BASE 1: formula monovariabile
        if self.is_literal(formula):
            return [([Bool(True)], 0)], formula, formula, []

        left, right = formula.args()
        cnf1, S1, P1, cnd1 = self.lt_pol(left, count + 1)
        cnf2, S2, P2, cnd2 = self.lt_pol(right, count + 1)
        # CASO BASE 2: already seen formula
        if (S1, S2, formula.node_type()) in self.hash_set:
            S, P = self.hash_set[(S1, S2, formula.node_type())]
            P_new = self._new_polarizer()
            self.activators[(S1, S2, formula.node_type())].append(P_new)
            return [], S, P_new, []
        if (S2, S1, formula.node_type()) in self.hash_set:
            S, P = self.hash_set[(S2, S1, formula.node_type())]
            P_new = self._new_polarizer()
            self.activators[(S2, S1, formula.node_type())].append(P_new)
            return [], S, P_new, []

        # CASO NOT(AND) PER AIG
        S = self._new_label()
        P = self._new_polarizer()
        clauses = []
        conditions = []

        # CASO BASE 2: leaf operator
        if self.is_literal(left) and self.is_literal(right):
            if formula.is_or():
                # (S <-> S1 v S2)
                if self.verbose:
                    print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
                clauses.append(([Not(P), Not(S), S1, S2], self.guards))
                clauses.append(([Not(P), S, Not(S1)], self.guards))
                clauses.append(([Not(P), S, Not(S2)], self.guards))
            if formula.is_and():
                # (S <-> S1 ^ S2)
                if self.verbose:
                    print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
                clauses.append(([Not(P), S, Not(S1), Not(S2)], self.guards))
                clauses.append(([Not(P), Not(S), S1], self.guards))
                clauses.append(([Not(P), Not(S), S2], self.guards))
            if formula.is_iff():
                # (S <-> S1 <-> S2)
                if self.verbose:
                    print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))
                clauses.append(([Not(P), Not(S), S1, Not(S2)], self.guards))
                clauses.append(([Not(P), Not(S), S2, Not(S1)], self.guards))
                clauses.append(([Not(P), S, S1, S2], self.guards))
                clauses.append(([Not(P), S, Not(S2), Not(S1)], self.guards))
            self.hash_set[(S1, S2, formula.node_type())] = (S, P)
            self.activators[(S1, S2, formula.node_type())] = [P]
            return clauses, S, P, []

        if formula.is_or():
            # S <-> S1 v S2
            if self.verbose:
                print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
            clauses.append(([Not(P), Not(S), S1, S2], self.guards))
            clauses.append(([Not(P), S, Not(S1)], self.guards))
            clauses.append(([Not(P), S, Not(S2)], self.guards))
            # S -> -S1 v -S2
            if self.verbose:
                print("{} -> ({} -> {} xor {})".format(P, S, P1, P2))
            conditions.append(([Not(P), Not(S), Not(P1), Not(P2)], self.guards))
            conditions.append(([Not(P), Not(S), P1, P2], self.guards))
            if not self.is_literal(left):
                if self.verbose:
                    print("{} and {} -> {}".format(P, Not(S), P1))
                conditions.append([[Not(P), S, P1], self.guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, S, Not(S2), P1))
                conditions.append([[Not(P), Not(S), S2, P1], self.guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.guards])
            if not self.is_literal(right):
                if self.verbose:
                    print("{} and {} -> {}".format(P, Not(S), P2))
                conditions.append([[Not(P), S, P2], self.guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, S, Not(S1), P2))
                conditions.append([[Not(P), Not(S), S1, P2], self.guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.guards])
        if formula.is_and():
            # S <-> S1 and S2
            if self.verbose:
                print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
            clauses.append(([Not(P), S, Not(S1), Not(S2)], self.guards))
            clauses.append(([Not(P), Not(S), S1], self.guards))
            clauses.append(([Not(P), Not(S), S2], self.guards))
            # -S -> S1 v S2
            if P1 == S1:
                P1 = Not(P1)
            if P2 == S2:
                P2 = Not(P2)
            if self.verbose:
                print("{} -> ({} -> {} xor {})".format(P, Not(S), P1, P2))
            conditions.append(([Not(P), S, Not(P1), Not(P2)], self.guards))
            conditions.append(([Not(P), S, P1, P2], self.guards))

            if not self.is_literal(left):
                if self.verbose:
                    print("{} and {} -> {}".format(P, S, P1))
                conditions.append([[Not(P), Not(S), P1], self.guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, Not(S), S2, P1))
                conditions.append([[Not(P), S, Not(S2), P1], self.guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.guards])
            if not self.is_literal(right):
                if self.verbose:
                    print("{} and {} -> {}".format(P, S, P2))
                conditions.append([[Not(P), Not(S), P2], self.guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, Not(S), S1, P2))
                conditions.append([[Not(P), S, Not(S1), P2], self.guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.guards])
        if formula.is_iff():
            # S <-> S1 <-> S2
            if self.verbose:
                print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))
            clauses.append(([Not(P), Not(S), S1, Not(S2)], self.guards))
            clauses.append(([Not(P), Not(S), S2, Not(S1)], self.guards))
            clauses.append(([Not(P), S, S1, S2], self.guards))
            clauses.append(([Not(P), S, Not(S2), Not(S1)], self.guards))

            if not self.is_literal(left):
                if self.verbose:
                    print("{} -> {}".format(P, P1))
                conditions.append(([Not(P), P1], self.guards))
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.guards])
            if not self.is_literal(right):
                if self.verbose:
                    print("{} -> {}".format(P, P2))
                conditions.append(([Not(P), P2], self.guards))
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.guards])

        clauses.reverse()
        conditions.reverse()

        if not self.is_literal(left):
            for c in cnf1:
                clauses.append(c)
        if not self.is_literal(right):
            for c in cnf2:
                clauses.append(c)

        for c in cnd1:
            conditions.append(c)
        for c in cnd2:
            conditions.append(c)

        self.hash_set[(S1, S2, formula.node_type())] = (S, P)
        self.activators[(S1, S2, formula.node_type())] = [P]
        return clauses, S, P, conditions

    def convert_as_formula(self, formula):
        if self.verbose:
            print("Input formula:", formula.serialize())
        formula = self.preprocessor.convert_as_formula(formula)
        if self.verbose:
            print("Preprocessed formula:", formula.serialize())

        # self.original_symb = S
        if self.verbose:
            print("Recursive calls to local_tseitin(formula, conds, symbol, polarity):")

        # cnf = self.local_tseitin_rec(formula, set(), S, 0, P)
        clauses, S, P, conditions = self.lt_pol(formula, 0)

        # clauses.reverse()
        # conditions.reverse()

        for f in self.activators:
            if len(self.activators[f]) > 1:
                P_new = self._new_polarizer()
                if self.verbose:
                    print("SWAP {} with {}".format(self.activators[f][0], P_new))
                    print("ADD And(Not({})) -> {}".format(self.activators[f], Not(P_new)))
                for c in clauses:
                    for i in range(len(c[0])):
                        if c[0][i] == self.activators[f][0]:
                            c[0][i] = P_new
                        elif c[0][i] == Not(self.activators[f][0]):
                            c[0][i] = Not(P_new)
                for c in conditions:
                    if c[0][0] == self.activators[f][0]:
                        c[0][0] = P_new
                    elif c[0][0] == Not(self.activators[f][0]):
                        c[0][0] = Not(P_new)
                conditions.append(([p for p in self.activators[f]] + [Not(P_new)], self.guards))
                for p in self.activators[f]:
                    conditions.append(([Not(p), P_new], self.guards))

        clauses.append((S, 0))
        clauses.append((P, 0))

        # print("SIZE NEW FORMULA:", len(cnf))
        cnf = conditions + clauses

        """
        for clause in clauses:
            clause = clause[0]
            _clause = []
            for lit in clause:
                if lit == S or lit == P:
                    # ignore clauses as !S -> ...
                    _clause.clear()
                    break
                elif (lit.is_not() and lit.arg(0) == S) or (lit.is_not() and lit.arg(0) == P):
                    # convert S -> l1 v ... lk into l1 v ... lk
                    continue
                else:
                    _clause.append(lit)
            if _clause:
                cnf.append(_clause)
        """
        cnf = And([Or(c[0]) for c in cnf])

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()

        # cnf = substitute(cnf, {S: Bool(True)})
        # cnf = simplify(cnf)

        # print("Clauses:\n", pformat(assertions))
        # cnf = And(assertions)
        assert self.is_cnf(cnf), cnf.serialize()
        return cnf
