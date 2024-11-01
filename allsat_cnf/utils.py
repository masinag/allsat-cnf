from dataclasses import dataclass
from enum import Enum
from itertools import filterfalse
from pprint import pformat
from typing import Iterable

import mathsat
from pysmt.environment import get_env
from pysmt.fnode import FNode
from pysmt.shortcuts import Solver, get_atoms, substitute
from pysmt.simplifier import Simplifier as Simplifier_
from pysmt.solvers.msat import MathSAT5Solver
from pysmt.typing import PySMTType, BOOL, REAL
from pysmt.walkers import IdentityDagWalker


@dataclass
class SolverOptions:
    class FirstAssign(Enum):
        NONE = 0
        RELEVANT = 1
        IRRELEVANT = 2

    timeout: int = None
    with_repetitions: bool = False
    use_ta: bool = False
    phase_caching: bool = True
    first_assign: FirstAssign = FirstAssign.NONE


class Normalizer:
    """A class for normalizing terms."""

    def __init__(self):
        self._solver = Solver(name="msat")
        self._cache = {}

    def __del__(self):
        self._solver.exit()

    def normalize(self, phi):
        if phi not in self._cache:
            converter = self._solver.converter
            normalized_term = converter.back(converter.convert(phi))
            self._cache[phi] = normalized_term
        return self._cache[phi]

    def normalize_assigment(self, mu):
        return {self.normalize(literal) for literal in mu}


class Simplifier(Simplifier_):
    """A class for simplifying terms.

    This class is a wrapper around the pysmt.simplifier.Simplifier class,
    complementing it with additional Boolean simplifications.
    """

    def walk_iff(self, formula, args, **kwargs):
        sl = args[0]
        sr = args[1]

        if negate(sl, self.manager) == sr or negate(sr, self.manager) == sl:
            return self.manager.FALSE()
        return super().walk_iff(formula, args, **kwargs)


def get_allsat(formula: FNode, atoms: Iterable[FNode] | None = None,
               solver_options: SolverOptions | None = None) -> tuple[list[set[FNode]], int]:
    """
    Enumerates a list of (partial) assignments of the given formula.
    :param formula: the formula to enumerate assignments for
    :param atoms: the atoms to project the assignments on (if None, all atoms in the formula are used)
    :param solver_options: options for the solver
    :return: a list of assignments and the total number of assignments
    """
    formula = rewalk(formula)

    if atoms is None:
        atoms = get_atoms(formula)
    else:
        atoms = rewalk(atoms)
    if len(atoms) == 0:
        return [], 0
    atoms = sorted(atoms, key=lambda x: x.node_id())

    if solver_options is not None:
        solver_options_dict = get_solver_options_dict(solver_options)
    else:
        solver_options_dict = {}

    preferred_atoms = set()
    if solver_options is not None:
        boolean_variables = get_boolean_variables(formula)
        if solver_options.first_assign is SolverOptions.FirstAssign.RELEVANT:
            preferred_atoms = boolean_variables & set(atoms)  # MathSAT allows only boolean variables to be relevant
        elif solver_options.first_assign is SolverOptions.FirstAssign.IRRELEVANT:
            preferred_atoms = boolean_variables - set(atoms)
    preferred_atoms = sorted(preferred_atoms, key=lambda x: x.node_id())

    assignments = []
    with Solver(name="msat", solver_options=solver_options_dict) as solver:
        solver: MathSAT5Solver
        solver.add_assertion(formula)
        for atom in preferred_atoms:
            solver.set_preferred_var(atom)
        # solver.all_sat(important=atoms, callback=lambda model: _allsat_callback(model, solver.converter, assignments))
        mathsat.msat_all_sat(solver.msat_env(), [solver.converter.convert(a) for a in atoms],
                             lambda model: _allsat_callback(model, solver.converter, assignments))

    total_models_count = sum(
        map(lambda assignment: 2 ** (len(atoms) - len(assignment)), assignments)
    )
    return assignments, total_models_count


def _allsat_callback(model, converter, models):
    py_model = {converter.back(v) for v in model}
    # assert IdentityDagWalker().walk(And(py_model)) == And(py_model)
    models.append(py_model)
    return 1


def check_sat(formula: FNode):
    formula = rewalk(formula)
    with Solver(name="msat") as solver:
        return solver.is_sat(formula)


def check_valid(formula: FNode):
    formula = rewalk(formula)
    with Solver(name="msat") as solver:
        return solver.is_valid(formula)


def get_solver_options_dict(solver_options: SolverOptions) -> dict[str, str]:
    # necessary to disable non-validity preserving simplifications
    solver_options_dict = {
        "preprocessor.toplevel_propagation": "false",
        "preprocessor.simplification": "0"
    }

    if solver_options.with_repetitions:
        solver_options_dict["dpll.allsat_allow_duplicates"] = "true"
    else:
        solver_options_dict["dpll.allsat_allow_duplicates"] = "false"

    if not solver_options.phase_caching:
        solver_options_dict["dpll.branching_cache_phase"] = "0"
        solver_options_dict["dpll.branching_random_frequency"] = "0"

    if solver_options.use_ta:
        solver_options_dict["dpll.allsat_minimize_model"] = "true"
    else:
        solver_options_dict["dpll.allsat_minimize_model"] = "false"

    # enforce splitting on negative phase first
    solver_options_dict["dpll.branching_initial_phase"] = "0"

    return solver_options_dict


def get_boolean_variables(formula: FNode) -> set[FNode]:
    return _get_variables(formula, BOOL)


def get_real_variables(formula: FNode) -> set[FNode]:
    return _get_variables(formula, REAL)


def _get_variables(formula: FNode, type_: PySMTType) -> set[FNode]:
    return {a for a in formula.get_free_variables() if a.get_type() == type_}


def get_lra_atoms(formula: FNode):
    return {a for a in formula.get_atoms() if a.is_theory_relation()}


def get_functions(formula: FNode):
    return {a for a in formula.get_atoms() if a.is_function_application()}


def check_models(ta: list[FNode], phi: FNode, relevant_atoms: set[FNode] | None = None):
    """
    Check that the given list of models is correct and complete for the given formula.
    :param ta: the list of models
    :param phi: the formula
    :param relevant_atoms: the atoms relevant for the formula (if None, all atoms in the formula are used)
    :return: True if the list of models is correct and complete for the given formula, False otherwise
    """
    ta = rewalk(ta)
    phi = rewalk(phi)
    if relevant_atoms is None:
        relevant_atoms = get_atoms(phi)
    is_correct, err = ta_is_correct(phi, ta, relevant_atoms)
    assert is_correct, "ta is not correct: {}\n{}\n{}".format(phi.serialize(), pformat(ta), err)
    is_complete, err = ta_is_complete(phi, ta)
    assert is_complete, "ta is not complete: {}\n{}\n{}".format(phi.serialize(), pformat(ta), err)


_normalizer = Normalizer()


def ta_is_correct(phi: FNode, ta: list[FNode], relevant_atoms: set[FNode]) -> tuple[bool, str | None]:
    """
    Check that each model in the list satisfies the formula.
    :param phi: the formula
    :param ta: the list of models
    :param relevant_atoms: the atoms relevant for the formula
    :return: True if each model in the list satisfies the formula, False otherwise
    """
    mgr = get_env().formula_manager
    phi = _normalizer.normalize(phi)
    for mu in ta:
        mu = _normalizer.normalize_assigment(mu)
        subs = {}
        for literal in mu:
            if literal.is_not():
                subs[literal.arg(0)] = mgr.FALSE()
            else:
                subs[literal] = mgr.TRUE()
        res = Simplifier().simplify(substitute(phi, subs))
        res_atoms = get_atoms(res)
        if len(res_atoms & relevant_atoms) != 0:
            err = "mu: {}\nsubstituting {}\ngot: {}\nres_atoms {}".format(mu, subs, res, res_atoms)
            return False, err
    return True, None


def ta_is_complete(phi: FNode, ta: list[FNode]) -> tuple[bool, str | None]:
    """
    Check that each total model of the formula is a super-model of one of the models in the list.
    :param phi: the formula
    :param ta: the list of models
    :return: True if each total model of the formula is a super-model of one of the models in the list, False otherwise
    """
    ta = [_normalizer.normalize_assigment(mu) for mu in ta]
    atoms = get_boolean_variables(phi).union({a for a in get_lra_atoms(phi)})
    tta, _ = get_allsat(phi, atoms=atoms, solver_options=SolverOptions(with_repetitions=False, use_ta=False))
    # check that for every model in tta there is a corresponding supermodel in ta
    for eta in tta:
        eta = _normalizer.normalize_assigment(eta)
        err = "{} not covered"
        if not any(eta.issuperset(mu) for mu in ta):
            return False, err
    return True, None


def rewalk(phi: FNode | Iterable[FNode]) -> FNode | Iterable[FNode]:
    if isinstance(phi, FNode):
        return IdentityDagWalker().walk(phi)
    return phi.__class__(rewalk(a) for a in phi)


def is_atom(atom: FNode) -> bool:
    return atom.is_symbol(BOOL) or atom.is_theory_relation() or atom.is_bool_constant()


def is_literal(literal: FNode) -> bool:
    return is_atom(literal) or (literal.is_not() and is_atom(literal.arg(0)))


def is_clause(phi: FNode) -> bool:
    return is_literal(phi) or (phi.is_or() and all(is_literal(a) for a in phi.args()))


def is_cnf(phi: FNode) -> bool:
    return is_clause(phi) or (phi.is_and() and all(is_clause(a) for a in phi.args()))


def get_clauses(phi: FNode) -> list[FNode]:
    if is_clause(phi):
        return [phi]
    return phi.args()


def get_literals(clause: FNode) -> list[FNode]:
    if is_literal(clause):
        return [clause]
    return clause.args()


def negate(term, mgr=None):
    if mgr is None:
        mgr = get_env().formula_manager
    if term.is_not():
        return term.arg(0)

    if term.is_bool_constant():
        return mgr.TRUE() if term.is_false() else mgr.FALSE()

    return mgr.Not(term)


def unique_everseen(iterable, key=None):
    """
    Source: https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element
