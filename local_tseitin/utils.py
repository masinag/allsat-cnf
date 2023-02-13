from typing import Dict, Tuple, Iterable

import funcy as fn
from aiger import AIG as _AIG, to_aig as _to_aig
from aiger.aig import Input as _Input
from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.shortcuts import Not, Symbol, And, Bool
from pysmt.typing import PySMTType, BOOL


def get_allsat(formula: FNode, use_ta=False, atoms=None, options={}):
    if use_ta:
        solver_options = {
            "dpll.allsat_minimize_model": "true",
            "dpll.allsat_allow_duplicates": "false",
            "preprocessor.toplevel_propagation": "false",
            "dpll.branching_initial_phase": "0",
            # "debug.api_call_trace": "2",
            # "preprocessor.simplification": "0"
        }
    else:
        solver_options = {}

    solver_options.update(options)
    if atoms is None:
        atoms = get_boolean_variables(formula)

    atoms = sorted(atoms, key=lambda x: x.symbol_name())

    # print(solver_options, atoms)

    with Solver(name="msat", solver_options=solver_options) as solver:
        converter = solver.converter

        solver.add_assertion(formula)
        models = []
        solver.all_sat(important=atoms, callback=lambda model: _allsat_callback(model, converter, models))
        # mathsat.msat_all_sat(solver.msat_env(),
        #                      [converter.convert(a) for a in atoms],
        #                      lambda model: _allsat_callback(model, converter, models))

    total_models_count = sum(
        map(lambda model: 2 ** (len(atoms) - len(model)), models))
    return models, total_models_count


def get_boolean_variables(formula: FNode):
    return _get_variables(formula, BOOL)


def get_real_variables(formula: FNode):
    return _get_variables(formula, REAL)


def _get_variables(formula: FNode, type_: PySMTType):
    return {a for a in formula.get_free_variables() if a.get_type() == type_}


def get_lra_atoms(formula: FNode):
    return {a for a in formula.get_atoms() if a.is_theory_relation()}


def _allsat_callback(model, converter, models):
    py_model = {converter.back(v) for v in model}
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
    for mu in ta:
        assert is_sat(And(mu) & phi)
    assert is_valid(Iff(phi, Or(map(And, ta))))
    # # check:
    # # 0. every mu in ta evaluates phi to true:
    # for mu in ta:
    #     mu_dict = get_dict_model(mu)
    #     assert phi.substitute(mu_dict).simplify().is_true(), \
    #         "Error: model {} does not evaluate {} to true".format(mu, phi.serialize())
    # # 1. every total truth assignment in tta is a super-assignment of one in ta
    # for mu in tta:
    #     assert any(mu.issuperset(nu) for nu in ta), "Error: mu={} is not a super-assignment of any nu in ta".format(mu)
    #
    # # 2. every pair of models in ta assigns opposite truth values to at least one element

    # NOTE: Very expensive! We can trust mathsat on this part
    # for mu, nu in itertools.combinations(ta, 2):
    #     assert not mu.isdisjoint(map(lambda x: Not(x).simplify(),
    #                                  nu)), "Error: mu={} and nu={} are overlapping".format(mu, nu)


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


class AIG:
    def __init__(self, aig: _AIG):
        assert len(aig.outputs) == 1
        # assert len(aig.latches) == 0
        self.aig = aig
        self.inputs: Dict[_Input, Symbol] = {}

    def __repr__(self):
        return repr(self.aig)

    @classmethod
    def from_file(cls, file) -> "AIG":
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
