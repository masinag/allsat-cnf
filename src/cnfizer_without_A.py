from pprint import pformat
from pysmt.shortcuts import *
from pysmt.walkers import IdentityDagWalker, handles
import pysmt.operators as op


class LocalTseitinCNFizerActivation(IdentityDagWalker):
    VAR_TEMPLATE = "T{:d}"
    ACT_TEMPLATE = "TA{:d}"
    original_symb = None

    def __init__(self, env=None, invalidate_memoization=None):
        super().__init__(env, invalidate_memoization)
        self.vars = 0
        self.acts = 0

    def _new_label(self):
        self.vars += 1
        return Symbol(LocalTseitinCNFizerActivation.VAR_TEMPLATE.format(self.vars))

    def _new_activation(self):
        self.acts += 1
        return Symbol(LocalTseitinCNFizerActivation.ACT_TEMPLATE.format(self.acts))

    def _get_key(self, formula, **kwargs):
        return super()._get_key(formula)

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
    

    def local_tseitin(self, formula, conds, S, pol, assertions):
        #print("local_tseitin({}, {}, {})".format(formula, conds, S))
        if formula.is_symbol() or (formula.is_not() and formula.arg(0).is_symbol()):
            return

        if formula.is_not():
            self.local_tseitin(formula.arg(0), conds, Not(S), 1-pol, assertions)
            return

        is_left_term = formula.args()[0].is_symbol() or (formula.arg(0).is_not() and formula.arg(0).arg(0).is_symbol())
        is_right_term = formula.args()[1].is_symbol() or (formula.arg(1).is_not() and formula.arg(1).arg(0).is_symbol())
    
        S1 = self._new_label() if not is_left_term else formula.args()[0] 
        S2 = self._new_label() if not is_right_term else formula.args()[1]
        for tseit in self.manage_operator(formula, S, S1, S2, is_left_term and is_right_term, pol):
            assertions.append(Or({Not(S_phi) for S_phi in conds}.union(tseit)))

        self.local_tseitin(formula.args()[0],conds.union({self.polarity(formula, S2), S if pol == 0 else Not(S)}), S1, pol, assertions)
        self.local_tseitin(formula.args()[1],conds.union({self.polarity(formula, S1), S if pol == 0 else Not(S)}), S2, pol, assertions)

    def convert(self, formula):
        assertions = []
        S = self._new_label()
        self.original_symb = S
        if formula.is_not():
            self.local_tseitin(formula.arg(0), set(), S, 1, assertions)
            assertions.append(Not(S))
        else:
            self.local_tseitin(formula, set(), S, 0, assertions)
            assertions.append(S)

        #for el in assertions:
        #    print(el)
        return And(assertions)


def model_to_set(model):
    return frozenset(a if v else Not(a) for a, v in model.items())


def is_model_in_models(model, models):
    for m in models:
        if m.issubset(model):
            return True
    return False


def test_models(cnf_models, total_models):
    cnf_models = list(map(model_to_set, cnf_models))
    total_models = list(map(model_to_set, total_models))
    for model in total_models:
        assert is_model_in_models(model, cnf_models), \
            "Model:\n{}\nNot found in:\n{}".format(
                pformat(model), pformat(cnf_models))
    print("Correct!")


if __name__ == "__main__":
    from wmipa import WMI
    wmi = WMI(None)
    cnfizer = LocalTseitinCNFizerActivation()
    A = Symbol("A", BOOL)
    B = Symbol("B", BOOL)
    C = Symbol("C", BOOL)
    D = Symbol("D", BOOL)
    E = Symbol("E", BOOL)
    F = Symbol("F", BOOL)
    G = Symbol("G", BOOL)
    H = Symbol("H", BOOL)

    #formula = Or(And(A, B), And(C, D), And(E, F), And(G, H))
    #formula = Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H))
    #atoms = {A, B, C, D, E, F, G, H}
    
    #formula = Or(And(A,B), And(C,D))
    #formula = Or(Not(And(A,B)), And(C,D))
    #atoms = {A,B, C, D}

    #formula = Not(Or(A,And(B, C)))
    #formula = And(Not(A), Or(Not(B), Not(C)))
    #atoms = {A, B, C}

    # NOT WORKING FOMRULAE BELOW (now working)!
    #formula = Or(A, Not(And(B, Or(C,D))))
    formula = Not(Or(A, Not(And(B, Not(Or(C,D))))))
    #formula = Or(A, Or(Not(B), And(Not(C),Not(D))))
    atoms = {A,B, C, D}

    #formula = And(A,Or(B, C))
    #formula = And(A,Not(Or(B, C)))
    #formula = Or(A, Not(And(B,C)))
    #atoms = {A,B,C}
    # total models
    total_models = []
    for model in wmi._get_allsat(formula, use_ta=False, atoms=atoms):
        total_models.append(model)

    print("Formula:", formula.serialize())
    print("NON-CNFIZED MODELS:")
    n_models = 0
    for model in wmi._get_allsat(formula, use_ta=True, atoms=atoms):
        #print(model)
        n_models += 1
    print("{}/{}".format(n_models, len(total_models)))

    cnf = cnfizer.convert(formula)
    # print("CNFized:", cnf.serialize())
    cnf_models = []
    print("CNFIZED MODELS:")
    n_models = 0
    for model in wmi._get_allsat(cnf, use_ta=True, atoms=atoms):
        #print(model)
        cnf_models.append(model)
        model = {a: Bool(v) for a, v in model.items()}
        assert simplify(substitute(formula, model)).is_true()
        n_models += 1
    print("{}/{}".format(n_models, len(total_models)))
    test_models(cnf_models, total_models)
