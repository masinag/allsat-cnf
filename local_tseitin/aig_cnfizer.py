import argparse
from pprint import pformat

from pysmt.shortcuts import *
from local_tseitin.cnfizer import LocalTseitinCNFizer

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                    action="store_true")
parser.add_argument("-g", help="set how many guards to add", type=int,
                    action="store")


class AIGER():
    def __init__(self):
        self.inputs = []
        self.outputs = []
        self.latches = []
        self.gates = []
        self.M = 0
        self.I = 0
        self.L = 0
        self.O = 0
        self.A = 0

    def add_input(self, name):
        self.inputs.append(name)

    def add_output(self, name, expr):
        self.outputs.append((name, expr))

    def add_latch(self, name, init, next):
        self.latches.append((name, init, next))

    def add_and(self, out, left, right):
        self.gates.append((out, left, right)) 

    def __str__(self):
        s = "aag {} {} {} {} {}\n".format(self.M, self.I, self.L, self.O, self.A)
        for i in self.inputs:
            s += "{} ".format(i)
            s += "\n"
        for o in self.outputs:
            s += "{} ".format(o)
            s += "\n"
        for a in self.gates:
            s += "{} {} {} ".format(a[0], a[1], a[2])
            s += "\n"
        return s


class GuardedAIG(LocalTseitinCNFizer):
    INPUT_TEMPLATE = "I{:d}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash_set = dict()
        self.all_clauses = []
        self.symbols = dict()
        self.important_symbols = set()
        self.input_vars = 0
        self.basic_tseitin = False

    def get_type(self, formula):
        if formula.is_not():
            return "NOT"
        if formula.is_and():
            return "AND"
        if formula.is_or():
            return "OR"
        if formula.is_iff():
            return "IFF"

    def get_index(self, var):
        return (var - 1) // 2 if var % 2 == 1 else var // 2

    def _new_input(self):
        self.input_vars += 1
        S = Symbol(self.INPUT_TEMPLATE.format(self.input_vars))
        self.important_symbols.add(S)
        return S
    
    def preprocess(self, aig_file):
        aig = AIGER()
        with open(aig_file, "r") as f:
            lines = f.readlines()
            lines = [l.strip() for l in lines]
            header = lines[0].split()
            assert((header[0] == "aag" or header[0] == "aig") and len(header) == 6)
            aig.M = int(header[1])
            aig.I = int(header[2])
            aig.L = int(header[3])
            aig.O = int(header[4])
            aig.A = int(header[5])
            for line in lines[1:aig.I+1]:
                aig.inputs.append(int(line))
                S = self._new_input()
                self.symbols[self.get_index(int(line))] = (S,S)
                self.important_symbols.add(S)
            assert(aig.L == 0)
            for line in lines[aig.I+1:aig.I+aig.O+1]:
                aig.outputs.append(int(line))
            for line in lines[aig.I+aig.O+1:]:
                aig.gates.append([int(x) for x in line.split()])
        return aig

    def basicTseitin(self, gate, left, right):
        # CLASSIC AND
        # CREATE VARIABLES FOR THIS GATE
        S = self._new_label()
        P = self._new_polarizer()
        self.symbols[self.get_index(gate)] = (S,P)
        S1, P1, S2, P2 = None, None, None, None
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
            print("({} <-> {} and {})".format(S, S1, S2))
        self.all_clauses.append( [S, Not(S1), Not(S2)] )
        self.all_clauses.append( [Not(S), S1] )
        self.all_clauses.append( [Not(S), S2] )

    def guardedTseitin(self, gate, left, right):
        # CLASSIC AND
        # CREATE VARIABLES FOR THIS GATE
        S = self._new_label()
        P = self._new_polarizer()
        self.symbols[self.get_index(gate)] = (S,P)
        S1, P1, S2, P2 = None, None, None, None
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
        self.all_clauses.append( [Not(P), S, Not(S1), Not(S2)] )
        self.all_clauses.append( [Not(P), Not(S), S1] )
        self.all_clauses.append( [Not(P), Not(S), S2] )

        if(True):
            # P -> (Not(S) and Not(P1) and Not(P2) -> S1 or S2)
            if not left_leaf or not right_leaf:
                if self.verbose:
                    print("{} -> (({} and {} and {})-> {} or {})".format(P, Not(S), Not(P1), Not(P2), S1, S2))
                self.all_clauses.append([Not(P), S, P1, P2, S1, S2])
                #self.all_clauses.append([Not(P), S, S1, S2])
        else:
         # P -> (Not(S) and Not(P1) -> S1 or S2)
            if not left_leaf or not right_leaf:
                if self.verbose:
                    print("{} -> (({} and {})-> {} or {})".format(P, Not(S), Not(P1), S1, S2))
                self.all_clauses.append([Not(P), S, P1, S1, S2])


        if not left_leaf:
            if self.verbose:
                print("{} and {} -> {}".format(P, S, P1))
            self.all_clauses.append((Not(P), P1, Not(S)))
            if self.verbose:
                print("{} and Not({}) and {} -> {}".format(P, S, S2, P1))
            self.all_clauses.append((Not(P), S, Not(S2), P1))
            #if self.verbose:
            #    print("{} and Not({}) and Not({}) -> Not({})".format(P, S, S2, P1))
            #self.all_clauses.append((Not(P), S, S2, Not(P1)))

        if not right_leaf:
            if self.verbose:
                print("{} and {} -> {}".format(P, S, P2))
            self.all_clauses.append((Not(P), P2, Not(S)))
            if self.verbose:
                print("{} and Not({}) and {} -> {}".format(P, S, S1, P2))
            self.all_clauses.append((Not(P), S, Not(S1), P2))
            #if self.verbose:
            #    print("{} and Not({}) and Not({}) -> Not({})".format(P, S, S1, P2))
            #self.all_clauses.append((Not(P), S, S1, Not(P2)))


    def convert(self, aig_file):
        aig = self.preprocess(aig_file)
        print(aig)
        print(self.symbols)
        print(self.important_symbols)
        
        cnf = []
        if not self.basic_tseitin:
            for gate in aig.gates:
                self.guardedTseitin(gate[0], gate[1], gate[2])
        else:
            for gate in aig.gates:
                self.basicTseitin(gate[0], gate[1], gate[2])

        #self.all_clauses.reverse()

        cnf = [f for f in self.all_clauses]
        cnf = And([Or(c) for c in cnf])

        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()

        S, P = self.symbols[self.get_index(aig.outputs[0])]
        if aig.outputs[0] % 2 == 0:
            if self.verbose:
                print("{} and {}".format(S, P))
            cnf = substitute(cnf, {S:Bool(True), P:Bool(True)})
        else:
            if self.verbose:
                print("Not({}) and {}".format(S, P))
            cnf = substitute(cnf, {S:Bool(False), P:Bool(True)})

        cnf = simplify(cnf)
        
        assert self.is_cnf(cnf)
        self.hash_set.clear()
        self.all_clauses.clear()
        return cnf, self.important_symbols
