import argparse

from pysmt.shortcuts import *

from local_tseitin.cnfizer import LocalTseitinCNFizer
from local_tseitin.utils import is_literal, is_cnf, negate_literal

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-g", help="set how many guards to add", type=int,
                    action="store")


class LocalTseitinCNFizerConds(LocalTseitinCNFizer):

    def lt_pol(self, formula, count):
        if self.verbose:
            print("{}local_tseitin_rec({})".format(
                "--" * count, formula))

        # BASE CASE 1: literal-formula
        if is_literal(formula):
            return [([Bool(True)], 0)], formula

        # SIMPLE CASE: Not(formula)
        if formula.is_not():
            cnf, S = self.lt_pol(formula.arg(0), count + 1)
            return cnf, negate_literal(S)

        left, right = formula.args()
        S = self._new_label()
        not_S = negate_literal(S)
        clauses = []

        # BASE CASE 2: leaf operator
        if is_literal(left) and is_literal(right):
            S1 = left
            not_S1 = negate_literal(S1)
            S2 = right
            not_S2 = negate_literal(S2)
            if formula.is_or():
                # (S <-> S1 v S2)
                clauses.append(self.new_clause([not_S, S1, S2]))
                clauses.append(self.new_clause([S, not_S1]))
                clauses.append(self.new_clause([S, not_S2]))
            if formula.is_and():
                # (S <-> S1 ^ S2)
                clauses.append(self.new_clause([S, not_S1, not_S2]))
                clauses.append(self.new_clause([not_S, S1]))
                clauses.append(self.new_clause([not_S, S2]))
            if formula.is_iff():
                # (S <-> S1 <-> S2)
                clauses.append(self.new_clause([not_S, S1, not_S2]))
                clauses.append(self.new_clause([not_S, S2, not_S1]))
                clauses.append(self.new_clause([S, S1, S2]))
                clauses.append(self.new_clause([S, not_S2, not_S1]))
            return clauses, S

        assert len(formula.args()) == 2, formula.serialize()

        cnf1, S1 = self.lt_pol(left, count + 1)
        not_S1 = negate_literal(S1)
        cnf2, S2 = self.lt_pol(right, count + 1)
        not_S2 = negate_literal(S2)

        if formula.is_or():
            # S <-> S1 v S2
            clauses.append(self.new_clause([not_S, S1, S2]))
            clauses.append(self.new_clause([S, not_S1]))
            clauses.append(self.new_clause([S, not_S2]))
            # -S2 -> CNF1
            self.add_guard_to_clauses(cnf1, clauses, S2)
            # -S1 -> CNF2
            self.add_guard_to_clauses(cnf2, clauses, S1)
            # S -> -S1 v -S2
            clauses.append(self.new_clause([not_S, not_S1, not_S2]))
        if formula.is_and():
            # S <-> S1 v S2
            clauses.append(self.new_clause([S, not_S1, not_S2]))
            clauses.append(self.new_clause([not_S, S1]))
            clauses.append(self.new_clause([not_S, S2]))
            # S2 -> CNF1
            self.add_guard_to_clauses(cnf1, clauses, not_S2)
            # S1 -> CNF2
            self.add_guard_to_clauses(cnf2, clauses, not_S1)
            # -S -> S1 v S2
            clauses.append(self.new_clause([S, S1, S2]))
        if formula.is_iff():
            # S <-> S1 <-> S2
            clauses.append(self.new_clause([not_S, S1, not_S2]))
            clauses.append(self.new_clause([not_S, S2, not_S1]))
            clauses.append(self.new_clause([S, S1, S2]))
            clauses.append(self.new_clause([S, not_S2, not_S1]))
            for f in cnf1:
                clauses.append(f)
            for f in cnf2:
                clauses.append(f)
        return clauses, S

    def new_clause(self, literals):
        return literals, self.max_guards

    @staticmethod
    def get_clause_with_guard(clause, guard, guards_left):
        if guards_left is None or guards_left > 0:
            clause = [guard] + clause
            if guards_left is not None:
                guards_left -= 1
        return clause, guards_left

    def add_guard_to_clauses(self, unguarded_clauses, guarded_clauses, guard):
        for clause, guards_left in unguarded_clauses:
            clause, guards_left = self.get_clause_with_guard(clause, guard, guards_left)
            guarded_clauses.append((clause, guards_left))

    def convert_as_formula(self, formula, expand_iff=False, **kwargs):
        if self.verbose:
            print("Input formula:", formula.serialize())
        formula = self.preprocessor.convert_as_formula(formula, expand_iff=expand_iff)
        if self.verbose:
            print("Preprocessed formula:", formula.serialize())

        clauses, S = self.lt_pol(formula, 0)
        not_S = negate_literal(S)
        cnf = []

        for clause, _ in clauses:
            clean_clause = []
            for lit in clause:
                if lit == S:
                    # ignore clauses as !S -> ...
                    clean_clause.clear()
                    break
                elif lit == not_S:
                    # convert S -> l1 v ... lk into l1 v ... lk
                    continue
                else:
                    clean_clause.append(lit)
            if len(clean_clause) > 0:
                cnf.append(clean_clause)

        cnf = And([Or(c) for c in cnf])

        if self.verbose:
            print()
            print(f"{len(cnf.args())} encoded clauses:")
            for el in cnf.args():
                print(el)
            print()

        assert is_cnf(cnf), cnf.serialize()
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
        if is_literal(formula):
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
        if is_literal(left) and is_literal(right):
            if formula.is_or():
                # (S <-> S1 v S2)
                if self.verbose:
                    print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
                clauses.append(([Not(P), Not(S), S1, S2], self.max_guards))
                clauses.append(([Not(P), S, Not(S1)], self.max_guards))
                clauses.append(([Not(P), S, Not(S2)], self.max_guards))
            if formula.is_and():
                # (S <-> S1 ^ S2)
                if self.verbose:
                    print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
                clauses.append(([Not(P), S, Not(S1), Not(S2)], self.max_guards))
                clauses.append(([Not(P), Not(S), S1], self.max_guards))
                clauses.append(([Not(P), Not(S), S2], self.max_guards))
            if formula.is_iff():
                # (S <-> S1 <-> S2)
                if self.verbose:
                    print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))
                clauses.append(([Not(P), Not(S), S1, Not(S2)], self.max_guards))
                clauses.append(([Not(P), Not(S), S2, Not(S1)], self.max_guards))
                clauses.append(([Not(P), S, S1, S2], self.max_guards))
                clauses.append(([Not(P), S, Not(S2), Not(S1)], self.max_guards))
            self.hash_set[(S1, S2, formula.node_type())] = (S, P)
            self.activators[(S1, S2, formula.node_type())] = [P]
            return clauses, S, P, []

        if formula.is_or():
            # S <-> S1 v S2
            if self.verbose:
                print("{} -> ({} <-> {} or {})".format(P, S, S1, S2))
            clauses.append(([Not(P), Not(S), S1, S2], self.max_guards))
            clauses.append(([Not(P), S, Not(S1)], self.max_guards))
            clauses.append(([Not(P), S, Not(S2)], self.max_guards))
            # S -> -S1 v -S2
            if self.verbose:
                print("{} -> ({} -> {} xor {})".format(P, S, P1, P2))
            conditions.append(([Not(P), Not(S), Not(P1), Not(P2)], self.max_guards))
            conditions.append(([Not(P), Not(S), P1, P2], self.max_guards))
            if not is_literal(left):
                if self.verbose:
                    print("{} and {} -> {}".format(P, Not(S), P1))
                conditions.append([[Not(P), S, P1], self.max_guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, S, Not(S2), P1))
                conditions.append([[Not(P), Not(S), S2, P1], self.max_guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.max_guards])
            if not is_literal(right):
                if self.verbose:
                    print("{} and {} -> {}".format(P, Not(S), P2))
                conditions.append([[Not(P), S, P2], self.max_guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, S, Not(S1), P2))
                conditions.append([[Not(P), Not(S), S1, P2], self.max_guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.max_guards])
        if formula.is_and():
            # S <-> S1 and S2
            if self.verbose:
                print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
            clauses.append(([Not(P), S, Not(S1), Not(S2)], self.max_guards))
            clauses.append(([Not(P), Not(S), S1], self.max_guards))
            clauses.append(([Not(P), Not(S), S2], self.max_guards))
            # -S -> S1 v S2
            if P1 == S1:
                P1 = Not(P1)
            if P2 == S2:
                P2 = Not(P2)
            if self.verbose:
                print("{} -> ({} -> {} xor {})".format(P, Not(S), P1, P2))
            conditions.append(([Not(P), S, Not(P1), Not(P2)], self.max_guards))
            conditions.append(([Not(P), S, P1, P2], self.max_guards))

            if not is_literal(left):
                if self.verbose:
                    print("{} and {} -> {}".format(P, S, P1))
                conditions.append([[Not(P), Not(S), P1], self.max_guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, Not(S), S2, P1))
                conditions.append([[Not(P), S, Not(S2), P1], self.max_guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.max_guards])
            if not is_literal(right):
                if self.verbose:
                    print("{} and {} -> {}".format(P, S, P2))
                conditions.append([[Not(P), Not(S), P2], self.max_guards])
                if self.verbose:
                    print("{} and {} and {} -> {}".format(P, Not(S), S1, P2))
                conditions.append([[Not(P), S, Not(S1), P2], self.max_guards])
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.max_guards])
        if formula.is_iff():
            # S <-> S1 <-> S2
            if self.verbose:
                print("{} -> ({} <-> {} <-> {})".format(P, S, S1, S2))
            clauses.append(([Not(P), Not(S), S1, Not(S2)], self.max_guards))
            clauses.append(([Not(P), Not(S), S2, Not(S1)], self.max_guards))
            clauses.append(([Not(P), S, S1, S2], self.max_guards))
            clauses.append(([Not(P), S, Not(S2), Not(S1)], self.max_guards))

            if not is_literal(left):
                if self.verbose:
                    print("{} -> {}".format(P, P1))
                conditions.append(([Not(P), P1], self.max_guards))
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P1)))
                conditions.append([[P, Not(P1)], self.max_guards])
            if not is_literal(right):
                if self.verbose:
                    print("{} -> {}".format(P, P2))
                conditions.append(([Not(P), P2], self.max_guards))
                if self.verbose:
                    print("{} -> {}".format(Not(P), Not(P2)))
                conditions.append([[P, Not(P2)], self.max_guards])

        clauses.reverse()
        conditions.reverse()

        if not is_literal(left):
            for c in cnf1:
                clauses.append(c)
        if not is_literal(right):
            for c in cnf2:
                clauses.append(c)

        for c in cnd1:
            conditions.append(c)
        for c in cnd2:
            conditions.append(c)

        self.hash_set[(S1, S2, formula.node_type())] = (S, P)
        self.activators[(S1, S2, formula.node_type())] = [P]
        return clauses, S, P, conditions

    def convert_as_formula(self, formula, **kwargs):
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
                conditions.append(([p for p in self.activators[f]] + [Not(P_new)], self.max_guards))
                for p in self.activators[f]:
                    conditions.append(([Not(p), P_new], self.max_guards))

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
        assert is_cnf(cnf), cnf.serialize()
        return cnf
