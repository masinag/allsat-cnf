import itertools
from collections import defaultdict
from typing import Iterable

from pysmt.fnode import FNode
from pysmt.formula import FormulaManager
from pysmt.typing import BOOL
from pysmt.walkers import DagWalker

from allsat_cnf.cnfizer import T_CLAUSE
from allsat_cnf.utils import simplify_clauses, unique_everseen

T_CNF = list[tuple[FNode, ...]]


class DefinitionUseCnfizer(DagWalker):
    def __init__(self, environment=None):
        DagWalker.__init__(self, environment, invalidate_memoization=True)
        self._clauses: T_CNF = []
        self._introduced_variables: dict[FNode, tuple[FNode, FNode]] = {}

    @property
    def mgr(self) -> FormulaManager:
        return self.env.formula_manager

    def key_var_pair(self, formula: FNode) -> tuple[FNode, FNode]:
        if formula not in self._introduced_variables:
            if formula.is_symbol(BOOL):
                template = formula.symbol_name()
            else:
                template = f"def{len(self._introduced_variables)}"
            k_plus = self.mgr.Symbol(f"{template}_p", BOOL)
            k_minus = self.mgr.Symbol(f"{template}_m", BOOL)
            self._introduced_variables[formula] = (k_plus, k_minus)
        return self._introduced_variables[formula]

    def convert_as_formula(self, formula: FNode) -> FNode:
        clauses = self.convert(formula)
        return self.mgr.And(map(self.mgr.Or, clauses))

    def convert(self, formula: FNode) -> T_CNF:
        tl: FNode = self.walk(formula)[0]
        clauses = self._clauses.copy()
        clauses += [(tl,)]
        clauses += self._get_mutex_clauses()
        clauses += self._get_minimality_clauses()

        clauses = simplify_clauses(clauses, tl, self.mgr)
        return list(unique_everseen(clauses))

    def map_model_back(self, model: Iterable[FNode], atoms: Iterable[FNode]) -> set[FNode]:
        """Maps a model over the introduced variables back to the original variables.
        :param model: The model to map.
        :param atoms: The original atoms.
        :return: The mapped model.
        """
        model_as_dict = dict((lit.arg(0), False) if lit.is_not() else (lit, True) for lit in model)
        original_model = set()
        for atom in atoms:
            k_plus, k_minus = self.key_var_pair(atom)
            assert k_plus in model_as_dict and k_minus in model_as_dict
            if model_as_dict[k_plus] and not model_as_dict[k_minus]:
                original_model.add(atom)
            elif not model_as_dict[k_plus] and model_as_dict[k_minus]:
                original_model.add(self.mgr.Not(atom))
            # else don't care
        return original_model

    def walk_symbol(self, formula: FNode, args: list[tuple[FNode, FNode]], **kwargs) -> tuple[FNode, FNode] | FNode:
        if formula.is_symbol(BOOL):
            return self.key_var_pair(formula)
        return formula

    def walk_not(self, formula: FNode, args: list[tuple[FNode, FNode]], **kwargs) -> tuple[FNode, FNode]:
        """NOT encoding:
         k_plus -> arg_minus
         k_minus -> arg_plus
        """
        arg_plus, arg_minus = args[0]
        k_plus, k_minus = self.key_var_pair(formula)
        self._clauses.append((self.mgr.Not(k_plus), arg_minus))
        self._clauses.append((self.mgr.Not(k_minus), arg_plus))

        return k_plus, k_minus

    def walk_and(self, formula: FNode, args: list[tuple[FNode, FNode]], **kwargs) -> tuple[FNode, FNode]:
        """AND encoding:
         k_plus -> big_and(args_plus)
         k_minus -> big_or(args_minus)
        """
        k_plus, k_minus = self.key_var_pair(formula)
        args_plus = [arg[0] for arg in args]
        args_minus = [arg[1] for arg in args]
        for arg_plus in args_plus:
            self._clauses.append((self.mgr.Not(k_plus), arg_plus))
        self._clauses.append(tuple([self.mgr.Not(k_minus)] + args_minus))

        return k_plus, k_minus

    def walk_or(self, formula: FNode, args: list[tuple[FNode, FNode]], **kwargs) -> tuple[FNode, FNode]:
        """OR encoding:
         k_plus -> big_or(args_plus)
         k_minus -> big_and(args_minus)
        """
        k_plus, k_minus = self.key_var_pair(formula)
        args_plus = [arg[0] for arg in args]
        args_minus = [arg[1] for arg in args]
        self._clauses.append(tuple([self.mgr.Not(k_plus)] + args_plus))
        for arg_minus in args_minus:
            self._clauses.append((self.mgr.Not(k_minus), arg_minus))

        return k_plus, k_minus

    def walk_iff(self, formula: FNode, args: list[tuple[FNode, FNode]], **kwargs) -> tuple[FNode, FNode]:
        """IFF encoding:
         k_plus -> ((arg1_minus | arg2_plus) & (arg1_plus | arg2_minus))
         k_minus -> ((arg1_plus | arg2_plus) & (arg1_minus | arg2_minus))
        """
        k_plus, k_minus = self.key_var_pair(formula)
        arg1_plus, arg1_minus = args[0]
        arg2_plus, arg2_minus = args[1]

        self._clauses.append((self.mgr.Not(k_plus), arg1_minus, arg2_plus))
        self._clauses.append((self.mgr.Not(k_plus), arg1_plus, arg2_minus))

        self._clauses.append((self.mgr.Not(k_minus), arg1_plus, arg2_plus))
        self._clauses.append((self.mgr.Not(k_minus), arg1_minus, arg2_minus))

        return k_plus, k_minus

    def _get_mutex_clauses(self) -> T_CNF:
        """Mutex clauses for dual-rail encoding:
        (!k_plus | !k_minus) for every defined variable k
        """
        return [(self.mgr.Not(k_plus), self.mgr.Not(k_minus)) for k_plus, k_minus in
                self._introduced_variables.values()]

    def _get_minimality_clauses(self) -> T_CNF:
        """Add clauses to ensure the encoding is satisfied only by minimal models.
        """
        # every clause has:
        # - exactly one negated literal (defined var)
        # - all other literals are positive (used vars)
        # get a mapping from each variable to the clauses where it is used
        minimality_clauses = []

        # map from variable to clauses where it is "used"
        var_to_usages: dict[FNode, list[T_CLAUSE]] = defaultdict(list)
        for clause in self._clauses:
            num_defined = 0
            for lit in clause:
                if not lit.is_not():
                    v = lit
                    var_to_usages[v].append(clause)
                else:
                    num_defined += 1
            assert num_defined == 1, "Each clause must have exactly one defined variable"

        dual_var: dict[FNode, FNode] = {}
        for k_plus, k_minus in self._introduced_variables.values():
            dual_var[k_plus] = k_minus
            dual_var[k_minus] = k_plus

        # clausify:
        # v -> ((defined_var1 & !used_var1_1 & ... ) | (defined_var2 & !used_var2_1 & ... ) | ...)
        # for every clause (defined_vari | !used_vari_1 | ... ) where v is used
        for v, usages in var_to_usages.items():
            minimality_cases = []
            for clause in usages:
                defined_vars = [lit.arg(0) for lit in clause if lit.is_not()]
                assert len(defined_vars) == 1
                defined_var = defined_vars[0]
                assert defined_var != v
                other_used_vars = [lit for lit in clause if lit not in (v, self.mgr.Not(defined_var))]
                case = [self.mgr.Not(used_var) for used_var in other_used_vars]
                case.append(defined_var)
                minimality_cases.append(case)

            # clauses are formed by: cross product of all cases, and to each add the negation of v
            for case_product in itertools.product(*minimality_cases):
                clause = {self.mgr.Not(v)} | set(case_product)
                if not self._clause_is_subsumed_by_mutex(clause, dual_var):
                    minimality_clauses.append(tuple(clause))

        return minimality_clauses

    def _clause_is_subsumed_by_mutex(self, clause: set[FNode], dual_var: dict[FNode, FNode]) -> bool:
        """
        Check if the clause is subsumed by (!k_plus) or (!k_minus) for any defined variable k
        """
        return any(self.mgr.Not(dual_var[var]) in clause for lit in clause if
                   lit.is_not() and (var := lit.arg(0)) in dual_var)
