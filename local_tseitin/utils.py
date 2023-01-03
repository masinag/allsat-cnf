import itertools
from pprint import pformat
from typing import *
from collections import defaultdict

import mathsat
from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.typing import PySMTType


def get_allsat(formula: FNode, use_ta=False, atoms=None, options={}):
    if use_ta:
        solver_options = {
            "dpll.allsat_minimize_model": "true",
            "dpll.allsat_allow_duplicates": "false",
            "preprocessor.toplevel_propagation": "false",
            # "preprocessor.simplification": "0"
        }
    else:
        solver_options = {}

    solver_options.update(options)
    if atoms is None:
        atoms = get_boolean_variables(formula)

    # print(solver_options, atoms)

    solver = Solver(name="msat", solver_options=solver_options)
    converter = solver.converter

    solver.add_assertion(formula)
    models = []
    mathsat.msat_all_sat(
        solver.msat_env(),
        [converter.convert(v) for v in atoms],
        lambda model: _allsat_callback(model, converter, models))

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
            mu[a.arg(0)] = FALSE()
        else:
            mu[a] = TRUE()
    return mu_dict


def check_models(tta, ta, phi):
    # assert is_valid(Iff(phi, Or(map(And), ta)))
    # check:
    # 0. every mu in ta evaluates phi to true:
    for mu in ta:
        mu_dict = get_dict_model(mu)
        assert phi.substitute(mu_dict).simplify().is_true(), \
            "Error: model {} does not evaluate {} to true".format(mu, phi.serialize())
    # 1. every total truth assignment in tta is a super-assignment of one in ta
    for mu in tta:
        assert any(mu.issuperset(nu) for nu in ta), "Error: mu={} is not a super-assignment of any nu in ta".format(mu)

    # 2. every pair of models in ta assigns opposite truth values to at least one element

    # NOTE: Very expensive! We can trust mathsat on this part
    # for mu, nu in itertools.combinations(ta, 2):
    #     assert not mu.isdisjoint(map(lambda x: Not(x).simplify(),
    #                                  nu)), "Error: mu={} and nu={} are overlapping".format(mu, nu)
