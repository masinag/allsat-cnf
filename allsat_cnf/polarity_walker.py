import enum
from typing import Tuple

from pysmt.fnode import FNode
from pysmt.walkers import DagWalker


class Polarity(enum.Flag):
    POS = enum.auto()
    NEG = enum.auto()
    DOUBLE = POS | NEG

    def __invert__(self):
        if self is Polarity.DOUBLE:
            return self
        return super().__invert__()


class PolarityDagWalker(DagWalker):
    """
    Walk the formula as a DAG, keeping the information about the polarity of the sub-formulas.
    """
    def iter_walk(self, formula: FNode, top_pol: Polarity = Polarity.POS, **kwargs) -> FNode:
        self.stack.append((False, formula, top_pol))
        self._process_stack(**kwargs)
        res_key = self._get_key(formula, pol=top_pol, **kwargs)
        return self.memoization[res_key]

    def _get_key(self, formula: FNode, pol: Polarity = Polarity.POS, **kwargs) -> Tuple[FNode, Polarity]:
        return formula, pol

    def _process_stack(self, **kwargs) -> None:
        while self.stack:
            (was_expanded, formula, pol) = self.stack.pop()
            if was_expanded:
                self._compute_node_result(formula, pol, **kwargs)
            else:
                self._push_with_children_to_stack(formula, pol, **kwargs)

    def _push_with_children_to_stack(self, formula: FNode, pol: Polarity = Polarity.DOUBLE, **kwargs) -> None:
        self.stack.append((True, formula, pol))

        for s, p in self._get_children(formula, pol):
            # Add only if not memoized already
            key = self._get_key(s, p, **kwargs)
            if key not in self.memoization:
                self.stack.append((False, s, p))

    def _compute_node_result(self, formula: FNode, pol: Polarity = Polarity.DOUBLE, **kwargs):
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

    def _get_children(self, formula: FNode, pol: Polarity = Polarity.DOUBLE):
        eq_pol, inv_pol = pol, ~pol

        if formula.is_not():
            return [(formula.arg(0), inv_pol)]

        elif formula.is_implies():
            return [(formula.arg(0), inv_pol), (formula.arg(1), eq_pol)]

        elif formula.is_iff():
            return [(formula.arg(0), Polarity.DOUBLE), (formula.arg(1), Polarity.DOUBLE)]

        elif formula.is_and() or formula.is_or() or formula.is_quantifier():
            return [(a, eq_pol) for a in formula.args()]

        elif formula.is_ite():
            assert self.env.stc.get_type(formula).is_bool_type()
            i, t, e = formula.args()
            return [(i, Polarity.DOUBLE), (t, eq_pol), (e, inv_pol)]

        else:
            assert formula.is_str_op() or \
                   formula.is_symbol() or \
                   formula.is_function_application() or \
                   formula.is_bool_constant() or \
                   formula.is_theory_relation(), str(formula)
            return []
