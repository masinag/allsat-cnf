from itertools import islice
from pprint import pformat
from pysmt.shortcuts import *
from pysmt.walkers import IdentityDagWalker, handles
from pysmt.rewritings import nnf
import pysmt.operators as op


class LocalTseitinCNFizerActivation(IdentityDagWalker):
    VAR_TEMPLATE = "TL{:d}"
    ACT_TEMPLATE = "TA{:d}"

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

    def convert(self, formula):
        assertions = []
        S, A = self.walk(formula, assertions=assertions)
        assertions.append(S)
        assertions.append(A)
        # print("\n".join(map(str, assertions)))
        return And(assertions)

    @handles(op.SYMBOL)
    @handles(op.RELATIONS)
    def walk_atom(self, formula, args, assertions, **kwargs):
        return formula, None

    def walk_not(self, formula, args, assertions, **kwargs):
        S, A = args[0]
        return Not(S), A

    def walk_and(self, formula, args, assertions, **kwargs):
        # if len(args) > 2:
        #     a1, a2 = args[0], args[1]
        #     ans = self.walk_or(None, (a1, a2), assertions, **kwargs)
        #     for arg in islice(args, 2, None):
        #         a1 = ans
        #         a2 = arg
        #         ans = self.walk_or(None, (a1, a2), assertions, **kwargs)
        #     return ans
        A = self._new_activation()
        S = self._new_label()

        for S_phi, A_phi in args:
            if A_phi is not None:
                # (A & S & S_phi) -> A_phi
                assertions.append(Or(Not(A), Not(S), Not(S_phi), A_phi))
                # (A & !S & !S_phi) -> A_phi
                assertions.append(Or(Not(A), S, S_phi, A_phi))
        # (A & And(S_phis)) -> S
        assertions.append(Or({Not(S_phi) for S_phi, _ in args}.
                             union({Not(A), S})))
        # (A & S) -> And(S_phis)
        for S_phi, _ in args:
            assertions.append(Or(Not(A), Not(S), S_phi))
        return S, A

    def walk_or(self, formula, args, assertions, **kwargs):
        # if len(args) > 2:
        #     a1, a2 = args[0], args[1]
        #     ans = self.walk_or(None, (a1, a2), assertions, **kwargs)
        #     for arg in islice(args, 2, None):
        #         a1 = ans
        #         a2 = arg
        #         ans = self.walk_or(None, (a1, a2), assertions, **kwargs)
        #     return ans
                
        A = self._new_activation()
        S = self._new_label()

        for S_phi, A_phi in args:
            if A_phi is not None:
                # (A & S & S_phi) -> A_phi
                assertions.append(Or(Not(A), Not(S), Not(S_phi), A_phi))
                # (A & !S & !S_phi) -> A_phi
                assertions.append(Or(Not(A), S, S_phi, A_phi))
        # A -> (S <-> Or(S_phis))
        # (A & S) -> Or(S_phis)
        assertions.append(Or({S_phi for S_phi, _ in args}.
                             union({Not(S), Not(A)})))
        # (A & Or(S_phis)) -> S
        for S_phi, _ in args:
            assertions.append(Or(Not(A), S, Not(S_phi)))
        return S, A

    # def walk_implies(self, formula, args, assertions, **kwargs):
    #     left, right = formula.args()
    #     left_arg, right_arg = args
    #     left = Not(left)
    #     left_arg = self.walk_not(left, left_arg, assertions, **kwargs)
    #     return self.walk_or(Or(left, right),
    #                         (left_arg, right_arg), assertions, **kwargs)


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

    formula = Or(Or(Or(And(A, B), And(C, D)), And(E, F)), And(G, H))
    print("Formula:", formula.serialize())

    atoms = {A, B, C, D, E, F, G, H}
    # total models
    total_models = []
    for model in wmi._get_allsat(formula, use_ta=False, atoms=atoms):
        total_models.append(model)

    print("NON-CNFIZED MODELS:")
    n_models = 0
    for model in wmi._get_allsat(formula, use_ta=True, atoms=atoms):
        # print(model)
        n_models += 1
    print("{}/{}".format(n_models, len(total_models)))

    cnf = cnfizer.convert(formula)
    # print("CNFized:", cnf.serialize())
    cnf_models = []
    print("CNFIZED MODELS:")
    n_models = 0
    for model in wmi._get_allsat(cnf, use_ta=True, atoms=atoms):
        # print(model)
        cnf_models.append(model)
        model = {a: Bool(v) for a, v in model.items()}
        assert simplify(substitute(formula, model)).is_true()
        n_models += 1
    print("{}/{}".format(n_models, len(total_models)))
    test_models(cnf_models, total_models)
