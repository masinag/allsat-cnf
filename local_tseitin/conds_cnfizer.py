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
            #if (pol == 0 and formula.is_or()) or (pol == 1 and formula.is_and()):
                # S1 <-> !S2
                #res.append({Not(S), Not(S1), Not(S2)})
                #res.append({Not(S), S1, S2})
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
                                   1-pol, count, assertions, polarizer)
            else:
                new_P = self._new_label()
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({Not(new_P), Not(polarizer)})))
                assertions.append(Or({Not(S_phi) for S_phi in conds}.union({new_P, polarizer})))
                self.local_tseitin(formula.arg(0), conds, Not(S), 1-pol, count, assertions, new_P)
            return

        assert len(formula.args()) ==2, "{}".format(formula.serialize())
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

            #self.local_tseitin(left, conds, S1, pol, count + 1, assertions, new_P)
            #self.local_tseitin(right, conds, S2, pol, count + 1, assertions, new_P)
        elif formula.is_and():
            # ORIGINAL COMMON PART
            #self.local_tseitin(left, conds.union({self.polarity(
            #    formula, S2)}), S1, pol, count + 1, assertions, polarizer)
            #self.local_tseitin(right, conds.union({self.polarity(
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

        #CASO BASE 2: leaf operator
        if self.is_literal(left) and self.is_literal(right):
            S1 = left; S2 = right;
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

        assert len(formula.args()) ==2, "{}".format(formula.serialize())

        S1 = self._new_label() if not self.is_literal(left)  else left
        S2 = self._new_label() if not self.is_literal(right)  else right

        clauses = []
        if formula.is_or():
            # And(conds) -> (S <-> S1 v S2)
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1, S2})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S1)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S2)})))
            
            # NEW: not both true if it is actually a OR, using polarizer
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(polarizer), Not(S1), Not(S2)})))

            return And([c for c in clauses] + 
                ([c for c in self.local_tseitin_rec(left, conds.union({Not(S2)}), S1, count + 1, polarizer).args()] if not self.is_literal(left) else []) + 
                ([c for c in self.local_tseitin_rec(right, conds.union({Not(S1)}), S2, count + 1, polarizer).args()] if not self.is_literal(right) else [])
            )

        if formula.is_and():
            # And(conds) -> (S <-> S1 ^ S2)
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({S, Not(S1), Not(S2)})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S1})))
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({Not(S), S2})))

            # NEW: not both false it is a AND negated, thus a OR, using polarizer
            clauses.append(Or({Not(S_phi) for S_phi in conds}.union({polarizer, S1, S2})))

            return And(
                [c for c in clauses] + 
                ([c for c in self.local_tseitin_rec(left, conds.union({S2}), S1, count + 1, polarizer).args()] if not self.is_literal(left) else []) + 
                ([c for c in self.local_tseitin_rec(right, conds.union({S1}), S2, count + 1, polarizer).args()] if not self.is_literal(right) else [])
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
                ([c for c in self.local_tseitin_rec(left, conds, S1, count + 1, new_Pl).args()] if not self.is_literal(left) else []) +
                ([c for c in self.local_tseitin_rec(right, conds, S2, count + 1, new_Pr).args()] if not self.is_literal(right) else [])
            )  


    def convert(self, formula):
        if self.verbose:
            print("Input formula:", formula.serialize())
        formula = self.preprocessor.convert(formula)
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

        cnf = self.local_tseitin_rec(formula, set(), S, 0, P)
        cnf = And([c for c in cnf.args()] + [S, P])

        
        if self.verbose:
            print()
            print("Encoded clauses:")
            for el in cnf.args():
                print(el)
            print()
        
        # print("Clauses:\n", pformat(assertions))
        # cnf = And(assertions)
        assert self.is_cnf(cnf)
        return cnf
