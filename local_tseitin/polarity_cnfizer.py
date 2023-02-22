from itertools import chain
from typing import Tuple, List

import pysmt.operators as op
import pysmt.typing as types
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles

from local_tseitin.utils import unique_everseen

T_CNF = Tuple[Tuple[FNode]]


class PolarityDagWalker(DagWalker):
    def iter_walk(self, formula: FNode, **kwargs) -> FNode:
        self.stack.append((False, formula, True))
        self._process_stack(**kwargs)
        res_key = self._get_key(formula, pol=True, **kwargs)
        return self.memoization[res_key]

    def _push_with_children_to_stack(self, formula: FNode, pol: bool = True, **kwargs) -> None:
        self.stack.append((True, formula, pol))

        for s, p in self._get_children(formula, pol):
            # Add only if not memoized already
            key = self._get_key(s, p, **kwargs)
            if key not in self.memoization:
                self.stack.append((False, s, p))

    def _process_stack(self, **kwargs) -> None:
        while self.stack:
            (was_expanded, formula, pol) = self.stack.pop()
            if was_expanded:
                self._compute_node_result(formula, pol, **kwargs)
            else:
                self._push_with_children_to_stack(formula, pol, **kwargs)

    def _get_key(self, formula: FNode, pol: bool = True, **kwargs) -> Tuple[FNode, bool]:
        return formula, pol

    def _compute_node_result(self, formula: FNode, pol: bool = True, **kwargs):
        key = self._get_key(formula, pol, **kwargs)
        if key not in self.memoization:
            try:
                f = self.functions[formula.node_type()]
            except KeyError:
                f = self.walk_error

            args = [self.memoization[self._get_key(s, p, **kwargs)] \
                    for s, p in self._get_children(formula, pol)]

            self.memoization[key] = f(formula, args=args, pol=pol, **kwargs)
        else:
            pass

    def _get_children(self, formula: FNode, pol: bool = True):
        if formula.is_not():
            return [(formula.arg(0), not pol)]

        elif formula.is_implies():
            return [(formula.arg(0), not pol), (formula.arg(1), pol)]

        elif formula.is_iff():
            return [(formula.arg(0), pol), (formula.arg(0), not pol),
                    (formula.arg(1), pol), (formula.arg(1), not pol)]

        elif formula.is_and() or formula.is_or() or formula.is_quantifier():
            return [(a, pol) for a in formula.args()]

        elif formula.is_ite():
            assert self.env.stc.get_type(formula).is_bool_type()
            i, t, e = formula.args()
            return [(i, pol), (i, not pol), (t, pol), (e, not pol)]

        else:
            assert formula.is_str_op() or \
                   formula.is_symbol() or \
                   formula.is_function_application() or \
                   formula.is_bool_constant() or \
                   formula.is_theory_relation(), str(formula)
            return []


class PolarityCNFizer(PolarityDagWalker):
    THEORY_PLACEHOLDER = "__Placeholder__"

    TRUE_CNF: T_CNF = tuple()
    FALSE_CNF: T_CNF = tuple([tuple()])

    def __init__(self, environment=None):
        DagWalker.__init__(self, environment)
        self.mgr = self.env.formula_manager
        self._introduced_variables = {}

    def convert(self, formula) -> T_CNF:
        tl: FNode
        _cnf: T_CNF
        tl, _cnf = self.walk(formula)
        if len(_cnf) == 0:
            return tuple([tuple([tl])])
        res = []
        for clause in _cnf:
            if len(clause) == 0:
                return PolarityCNFizer.FALSE_CNF
            simp = []
            for lit in clause:
                if lit.is_true():
                    # Prune clauses that are trivially TRUE
                    simp = None
                    break
                elif lit == tl:
                    # Prune clauses as ~tl -> l1 v ... v lk
                    simp = None
                    break
                elif lit == self.mgr.Not(tl).simplify():
                    # Simplify tl -> l1 v ... v lk
                    # into l1 v ... v lk
                    continue
                elif not lit.is_false():
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(tuple(unique_everseen(simp)))
        return tuple(unique_everseen(res))

    def convert_as_formula(self, formula):
        lsts = self.convert(formula)
        return self.mgr.And(map(self.mgr.Or, lsts))

    def _key_var(self, formula: FNode) -> FNode:
        if formula not in self._introduced_variables:
            self._introduced_variables[formula] = self.mgr.FreshSymbol()
        return self._introduced_variables[formula]

    @handles(op.QUANTIFIERS)
    def walk_quantifier(self, formula: FNode, args, **kwargs):
        raise NotImplementedError("CNFizer does not support quantifiers")

    def walk_and(self, formula: FNode, args: List[Tuple[FNode, T_CNF]], pol: bool = True, **kwargs):
        if len(args) == 1:
            return args[0]
        args_labels, args_cnfs = zip(*args)

        k = self._key_var(formula)
        if pol:
            # noinspection PyTypeChecker
            _cnf = tuple(tuple([self.mgr.Not(k), a]) for a in args_labels)
        else:
            _cnf = tuple([tuple([k] + [self.mgr.Not(a).simplify() for a in args_labels])])

        return k, self._merge_cnfs(_cnf, *args_cnfs)

    def walk_or(self, formula: FNode, args: List[Tuple[FNode, T_CNF]], pol: bool = True, **kwargs):
        if len(args) == 1:
            return args[0]
        args_labels, args_cnfs = zip(*args)

        k = self._key_var(formula)
        if pol:
            _cnf = tuple([tuple([self.mgr.Not(k)] + [a for a in args_labels])])
        else:
            # noinspection PyTypeChecker
            _cnf = tuple(tuple([k, self.mgr.Not(a).simplify()]) for a in args_labels)

        return k, self._merge_cnfs(_cnf, *args_cnfs)

    def walk_not(self, formula: FNode, args, **kwargs):
        a, _cnf = args[0]
        if a.is_true():
            return self.mgr.FALSE(), PolarityCNFizer.TRUE_CNF
        elif a.is_false():
            return self.mgr.TRUE(), PolarityCNFizer.TRUE_CNF
        else:
            return self.mgr.Not(a).simplify(), _cnf

    def walk_implies(self, formula: FNode, args: List[Tuple[FNode, T_CNF]], pol: bool = True, **kwargs):
        a, cnf_a = args[0]
        b, cnf_b = args[1]

        k = self._key_var(formula)
        not_a = self.mgr.Not(a).simplify()
        not_b = self.mgr.Not(b).simplify()
        not_k = self.mgr.Not(k)
        if pol:
            _cnf = tuple([tuple([not_a, b, not_k])])
        else:
            _cnf = tuple([tuple([a, k]), tuple([not_b, k])])

        return k, self._merge_cnfs(_cnf, cnf_a, cnf_b)

    def walk_iff(self, formula: FNode, args: List[Tuple[FNode, T_CNF]], pol: bool = True, **kwargs):
        a, cnf_ap = args[0]
        _, cnf_an = args[1]
        b, cnf_bp = args[2]
        _, cnf_bn = args[3]

        k = self._key_var(formula)
        not_a: FNode = self.mgr.Not(a).simplify()
        not_b: FNode = self.mgr.Not(b).simplify()
        not_k: FNode = self.mgr.Not(k)

        _cnf = tuple([tuple([not_a, not_b, k]),
                      tuple([not_a, b, not_k]),
                      tuple([a, not_b, not_k]),
                      tuple([a, b, k])])

        return k, self._merge_cnfs(_cnf, cnf_ap, cnf_an, cnf_bp, cnf_bn)

    def walk_symbol(self, formula: FNode, **kwargs):
        if formula.is_symbol(types.BOOL):
            return formula, PolarityCNFizer.TRUE_CNF
        else:
            return PolarityCNFizer.THEORY_PLACEHOLDER

    def walk_function(self, formula: FNode, **kwargs):
        ty = formula.function_name().symbol_type()
        if ty.return_type.is_bool_type():
            return formula, PolarityCNFizer.TRUE_CNF
        else:
            return PolarityCNFizer.THEORY_PLACEHOLDER

    def walk_ite(self, formula: FNode, args: List[Tuple[FNode, T_CNF]], pol: bool = True, **kwargs):
        if any(a == PolarityCNFizer.THEORY_PLACEHOLDER for a in args):
            return PolarityCNFizer.THEORY_PLACEHOLDER
        (i, cnf_ip), (_, cnf_in), (t, cnf_t), (e, cnf_e) = args
        k = self._key_var(formula)
        not_i = self.mgr.Not(i).simplify()
        not_t = self.mgr.Not(t).simplify()
        not_e = self.mgr.Not(e).simplify()
        not_k = self.mgr.Not(k)

        if pol:
            _cnf = tuple([tuple([not_i, t, not_k]), tuple([i, e, not_k])])
        else:
            _cnf = tuple([tuple([not_i, not_t, k]), tuple([i, not_e, k])])

        return k, self._merge_cnfs(_cnf, cnf_ip, cnf_in, cnf_t, cnf_e)

    @handles(op.THEORY_OPERATORS)
    def walk_theory_op(self, formula: FNode, **kwargs):
        # pylint: disable=unused-argument
        return PolarityCNFizer.THEORY_PLACEHOLDER

    @handles(op.CONSTANTS)
    def walk_constant(self, formula: FNode, **kwargs):
        # pylint: disable=unused-argument
        if formula.is_true():
            return formula, PolarityCNFizer.TRUE_CNF
        elif formula.is_false():
            return formula, PolarityCNFizer.TRUE_CNF
        else:
            return PolarityCNFizer.THEORY_PLACEHOLDER

    @handles(op.RELATIONS)
    def walk_theory_relation(self, formula: FNode, args, **kwargs):
        # pylint: disable=unused-argument
        assert all(a == PolarityCNFizer.THEORY_PLACEHOLDER for a in args)
        return formula, PolarityCNFizer.TRUE_CNF

    def _merge_cnfs(self, *cnfs: T_CNF) -> T_CNF:
        """Merge CNFs into a single CNF."""
        return tuple(unique_everseen(chain(*cnfs)))
