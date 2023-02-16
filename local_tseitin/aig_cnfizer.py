import argparse
from typing import Dict, Tuple, Iterable, Union, Optional

from pysmt.shortcuts import *

from local_tseitin.cnfizer import LocalTseitinCNFizer
from local_tseitin.utils import is_cnf, AIGAdapter


class GuardedAIG(LocalTseitinCNFizer):
    INPUT_TEMPLATE = "I{:d}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash_set = dict()
        self.all_clauses = []
        self.symbols = dict()
        self.important_symbols = set()

    def get_index(self, var):
        return var // 2

    def _new_input(self, name: Optional[str] = None) -> Symbol:
        if name is None:
            name = self.INPUT_TEMPLATE.format(len(self.important_symbols))
        S = Symbol(name)
        self.important_symbols.add(S)
        return S

    def basic_tseitin(self, gate, left, right):
        # CLASSIC AND
        # CREATE VARIABLES FOR THIS GATE
        S = self._new_label()
        P = self._new_polarizer()
        self.symbols[self.get_index(gate)] = (S, P)

        S1, P1 = self.symbols[self.get_index(left)]
        S2, P2 = self.symbols[self.get_index(right)]

        if left % 2 == 1:
            S1 = Not(S1)
        if right % 2 == 1:
            S2 = Not(S2)

        # P -> (S <-> S1 and S2)
        if self.verbose:
            print("({} <-> {} and {})".format(S, S1, S2))
        self.all_clauses.append([S, Not(S1), Not(S2)])
        self.all_clauses.append([Not(S), S1])
        self.all_clauses.append([Not(S), S2])

    def guarded_tseitin(self, gate, left, right):
        # CLASSIC AND
        # CREATE VARIABLES FOR THIS GATE
        S = self._new_label()
        P = self._new_polarizer()
        self.symbols[self.get_index(gate)] = (S, P)

        S1, P1 = self.symbols[self.get_index(left)]
        S2, P2 = self.symbols[self.get_index(right)]
        left_leaf = S1 == P1
        right_leaf = S2 == P2
        if left % 2 == 1:
            S1 = Not(S1)
        if right % 2 == 1:
            S2 = Not(S2)

        # P -> (S <-> S1 and S2)
        if self.verbose:
            print("{} -> ({} <-> {} and {})".format(P, S, S1, S2))
        self.all_clauses.append([Not(P), S, Not(S1), Not(S2)])
        self.all_clauses.append([Not(P), Not(S), S1])
        self.all_clauses.append([Not(P), Not(S), S2])

        # P -> (Not(S) and Not(P1) and Not(P2) -> S1 or S2)
        if not left_leaf or not right_leaf:
            if self.verbose:
                print("{} and {} -> {} or {})".format(P, Not(S), P1, P2))
            self.all_clauses.append([Not(P), S, P1, P2])
            # self.all_clauses.append([Not(P), S, S1, S2])

        if not left_leaf:
            if self.verbose:
                print("{} and {} -> {}".format(P, S, P1))
            self.all_clauses.append((Not(P), P1, Not(S)))
            if self.verbose:
                print("{} and Not({}) and {} -> {}".format(P, S, S2, P1))
            self.all_clauses.append((Not(P), S, Not(S2), P1))
            # if self.verbose:
            #    print("{} and Not({}) and Not({}) -> Not({})".format(P, S, S2, P1))
            # self.all_clauses.append((Not(P), S, S2, Not(P1)))

        if not right_leaf:
            if self.verbose:
                print("{} and {} -> {}".format(P, S, P2))
            self.all_clauses.append((Not(P), P2, Not(S)))
            if self.verbose:
                print("{} and Not({}) and {} -> {}".format(P, S, S1, P2))
            self.all_clauses.append((Not(P), S, Not(S1), P2))
            # if self.verbose:
            #    print("{} and Not({}) and Not({}) -> Not({})".format(P, S, S1, P2))
            # self.all_clauses.append((Not(P), S, S1, Not(P2)))

    def convert_as_formula(self, aig: Union[AIGAdapter, str], use_tseitin=False):
        if isinstance(aig, str):
            aig = AIGAdapter.from_file(aig)

        inputs, output, gates = aig.gates()
        for i, name in inputs.items():
            S = self._new_input(name)
            self.important_symbols.add(S)
            self.symbols[self.get_index(i)] = (S, S)

        if self.verbose:
            print(aig)
            print(self.symbols)
            print(self.important_symbols)

        if not use_tseitin:
            for gate in gates:
                self.guarded_tseitin(gate[0], gate[1], gate[2])
        else:
            for gate in gates:
                self.basic_tseitin(gate[0], gate[1], gate[2])

        # self.all_clauses.reverse()

        cnf = [f for f in self.all_clauses]
        cnf = And([Or(c) for c in cnf])

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()

        S, P = self.symbols[self.get_index(output)]
        if output % 2 == 0:
            if self.verbose:
                print("{} and {}".format(S, P))
            cnf = substitute(cnf, {S: Bool(True), P: Bool(True)})
        else:
            if self.verbose:
                print("Not({}) and {}".format(S, P))
            cnf = substitute(cnf, {S: Bool(False), P: Bool(True)})

        cnf = simplify(cnf)

        assert is_cnf(cnf)
        self.hash_set.clear()
        self.all_clauses.clear()
        print(aig.to_pysmt().serialize())
        return cnf, self.important_symbols
