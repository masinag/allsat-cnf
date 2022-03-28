from pprint import pformat
from typing import *

import mathsat
from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.typing import PySMTType


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
    return models


def _is_model_in_models(model, models):
    for m in models:
        if m.issubset(model):
            return True
    return False


def _model_to_dict(model):
    dct = {}
    for a in model:
        if a.is_not():
            dct[a.arg(0)] = FALSE()
        else:
            dct[a] = TRUE()
    return dct


def check_models(cnf_models, total_models):
    for model in total_models:
        assert _is_model_in_models(model, cnf_models), \
            "Total model\n{}\nnot found in partial models\n{}". \
            format(model, pformat(cnf_models))


def check_eval_true(phi, models):
    for model in models:
        subst = _model_to_dict(model)
        assert simplify(substitute(phi, subst)).is_true(
        ), "Formula\n{}\nnot simplified with\n{}".format(phi.serialize(), model)
