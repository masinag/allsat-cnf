from itertools import filterfalse
from pprint import pformat
from typing import Dict, Tuple, Iterable

import funcy as fn
from aiger import AIG as _AIG, to_aig as _to_aig
from aiger.aig import Input as _Input
from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.shortcuts import Not, Symbol, And, Bool, Iff
from pysmt.typing import PySMTType, BOOL
from pysmt.walkers import IdentityDagWalker


def get_allsat(formula: FNode, use_ta=False, atoms=None, options=None):
    if options is None:
        options = {}
    if atoms is None:
        atoms = get_boolean_variables(formula)
    atoms = sorted(atoms, key=lambda x: x.symbol_name())

    solver_options = get_solver_options(use_ta)
    solver_options.update(options)

    models = []
    with Solver(name="msat", solver_options=solver_options) as solver:
        solver.add_assertion(formula)
        solver.all_sat(important=atoms, callback=lambda model: _allsat_callback(model, solver.converter, models))

    total_models_count = sum(
        map(lambda model: 2 ** (len(atoms) - len(model)), models)
    )
    return models, total_models_count


def get_solver_options(use_ta):
    if use_ta:
        solver_options = {
            "dpll.allsat_minimize_model": "true",
            "dpll.allsat_allow_duplicates": "false",
            "preprocessor.toplevel_propagation": "false",
            "dpll.branching_initial_phase": "0",
        }
    else:
        solver_options = {}
    return solver_options


def get_boolean_variables(formula: FNode):
    return _get_variables(formula, BOOL)


def get_real_variables(formula: FNode):
    return _get_variables(formula, REAL)


def _get_variables(formula: FNode, type_: PySMTType):
    return {a for a in formula.get_free_variables() if a.get_type() == type_}


def get_lra_atoms(formula: FNode):
    return {a for a in formula.get_atoms() if a.is_theory_relation()}


def get_functions(formula: FNode):
    return {a for a in formula.get_atoms() if a.is_function_application()}


def _allsat_callback(model, converter, models):
    py_model = {converter.back(v) for v in model}
    assert IdentityDagWalker().walk(And(py_model)) == And(py_model)
    models.append(py_model)
    return 1


def get_dict_model(mu):
    mu_dict = {}
    for a in mu:
        if a.is_not():
            mu_dict[a.arg(0)] = FALSE()
        else:
            mu_dict[a] = TRUE()
    return mu_dict


def check_models(ta, phi):
    # check every model in ta satisfies phi
    assert ta_is_correct(phi, ta), "ta is not correct: {}\n{}".format(phi, pformat(ta))
    assert ta_is_complete(phi, ta), "ta is not complete: {}\n{}".format(phi, pformat(ta))


def ta_is_correct(phi, ta):
    for mu in ta:
        model = And(mu)
        formula = And(phi, model)
        if not _is_sat(formula):
            return False
    return True


def ta_is_complete(phi, ta):
    tta, _ = get_allsat(phi, use_ta=False)
    # check that for every model in tta there is a corresponding supermodel in ta
    for eta in tta:
        if not any(eta.issuperset(rewalk(mu)) for mu in ta):
            return False
    return True
    # equiv = Iff(phi, Or(map(And, ta)))
    # return _is_valid(equiv)


def _is_sat(phi):
    phi = rewalk(phi)
    return is_sat(phi)


def rewalk(phi):
    if isinstance(phi, list):
        return [rewalk(a) for a in phi]
    if isinstance(phi, tuple):
        return tuple(rewalk(a) for a in phi)
    if isinstance(phi, set):
        return {rewalk(a) for a in phi}
    return IdentityDagWalker().walk(phi)


def _is_valid(phi):
    phi = rewalk(phi)
    return is_valid(phi)


def is_atom(atom):
    return atom.is_symbol(BOOL) or atom.is_theory_relation() or atom.is_bool_constant()


def is_literal(literal):
    return is_atom(literal) or (literal.is_not() and is_atom(literal.arg(0)))


def is_clause(phi):
    return is_literal(phi) or (phi.is_or() and all(is_literal(a) for a in phi.args()))


def is_cnf(phi):
    return is_clause(phi) or (phi.is_and() and all(is_clause(a) for a in phi.args()))


def negate_literal(literal):
    return Not(literal).simplify()


class AIGAdapter:
    def __init__(self, aig: _AIG):
        assert len(aig.outputs) == 1
        # assert len(aig.latches) == 0
        self.aig = aig
        self.inputs: Dict[_Input, Symbol] = {}

    def __repr__(self):
        return repr(self.aig)

    @classmethod
    def from_file(cls, file) -> "AIGAdapter":
        return cls(_to_aig(file))

    def gates(self) -> Tuple[Dict[int, str], int, Iterable[Tuple[int, int, int]]]:
        gates = []
        count = 0

        class NodeAlg:
            def __init__(self, lit: int):
                self.lit = lit

            @fn.memoize
            def __and__(self, other):
                nonlocal count
                nonlocal gates
                count += 1
                new = NodeAlg(count << 1)
                right, left = sorted([self.lit, other.lit])
                gates.append((new.lit, left, right))
                return new

            def __invert__(self):
                return NodeAlg(self.lit ^ 1)

        def lift(obj) -> NodeAlg:
            if isinstance(obj, bool):
                return NodeAlg(int(obj))
            elif isinstance(obj, NodeAlg):
                return obj
            raise NotImplementedError

        circ = self.aig
        start = 1
        inputs = {k: NodeAlg(i << 1) for i, k in enumerate(sorted(circ.inputs), start)}
        count += len(inputs)

        # Interpret circ over Algebra.
        omap, _ = circ(inputs=inputs, lift=lift)
        output = omap.get(next(iter(circ.outputs))).lit
        inputs = {inputs[k].lit: k for k in sorted(circ.inputs)}

        return inputs, output, gates

    def to_pysmt(self) -> FNode:
        count = 0

        class NodeAlg:
            def __init__(self, node: FNode):
                self.node = node

            @fn.memoize
            def __and__(self, other):
                return NodeAlg(And(self.node, other.node))

            def __invert__(self):
                return NodeAlg(Not(self.node))

        def lift(obj) -> NodeAlg:
            if isinstance(obj, bool):
                return NodeAlg(Bool(obj))
            if isinstance(obj, FNode):
                return NodeAlg(obj)
            elif isinstance(obj, NodeAlg):
                return obj
            raise NotImplementedError

        circ = self.aig

        inputs = {}
        start = 1
        for i, k in enumerate(sorted(circ.inputs), start):
            inputs[k] = NodeAlg(Symbol(k, BOOL))
        count += len(inputs)

        # Interpret circ over Algebra.
        omap, _ = circ(inputs=inputs, lift=lift)
        output = omap.get(next(iter(circ.outputs))).node

        return output


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
