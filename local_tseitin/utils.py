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
            "preprocessor.simplification": "0"
        }
    else:
        solver_options = {}

    solver_options.update(options)
    if atoms is None:
        atoms = get_boolean_variables(formula)

    solver = Solver(name="msat", solver_options=solver_options)
    converter = solver.converter

    solver.add_assertion(formula)
    models = []
    mathsat.msat_all_sat(
        solver.msat_env(),
        [converter.convert(v) for v in atoms],
        lambda model: _allsat_callback(model, converter, models))

    total_models_count = sum(
        map(lambda model: 2**(len(atoms) - len(model)), models))
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


def check_models(models, phi):
    assert is_unsat(Not(Iff(Or(map(And, models)), phi)))
