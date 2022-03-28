from itertools import islice

import pysmt.operators as op
from pysmt.shortcuts import *
from pysmt.walkers import IdentityDagWalker, handles

from local_tseitin.cnfizer import LocalTseitinCNFizer


class LocalTseitinCNFizerActivation(LocalTseitinCNFizer, IdentityDagWalker):
    ACT_TEMPLATE = "TA{:d}"

    def __init__(self, env=None, invalidate_memoization=True, **kwargs):
        LocalTseitinCNFizer.__init__(self, **kwargs)
        IdentityDagWalker.__init__(self, env, invalidate_memoization)
        self.acts = 0

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
