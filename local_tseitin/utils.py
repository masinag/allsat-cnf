from pprint import pformat
from typing import *
from collections import defaultdict

import mathsat
from pysmt.fnode import FNode
from pysmt.shortcuts import *
from pysmt.typing import PySMTType


class AllSATSolver:
    def __init__(self):
        self.list_norm = set()
        self.norm_aliases = dict()

    def normalize_coefficient(self, val, normalizing_coefficient):
        midvalue = round(float(val)/abs(normalizing_coefficient), 10)
        if abs(midvalue - round(float(midvalue))) < 0.00000001:
            return round(float(midvalue))
        return midvalue

    def normalize_assignment(self, assignment, add_to_norms_aliases):
        self.list_norm.add(assignment)
        if not assignment.is_lt():
            list_terms = [(assignment.args()[0], 1),
                          (assignment.args()[1], -1)]
        else:
            list_terms = [(assignment.args()[0], -1),
                          (assignment.args()[1], 1)]
        symbols = defaultdict(float)
        normalizing_coefficient = 0.0
        for term, coeff in list_terms:
            if term.is_real_constant():
                normalizing_coefficient += (term.constant_value() * coeff)
            elif term.is_plus():
                list_terms.extend([(atom, coeff) for atom in term.args()])
            elif term.is_minus():
                child1 = term.args()[0]
                child2 = term.args()[1]
                list_terms.append((child1, coeff))
                list_terms.append((child2, -1.0*coeff))
            elif term.is_times():
                child1 = term.args()[0]
                child2 = term.args()[1]

                if child1.is_real_constant() and child2.is_real_constant():
                    #constant += child1.constant_value() * child2.constant_value()
                    list_terms.append(child1.constant_value()
                                      * child2.constant_value(), coeff)
                elif child1.is_real_constant():
                    list_terms.append((child2, coeff*child1.constant_value()))
                elif child2.is_real_constant():
                    list_terms.append((child1, coeff*child2.constant_value()))
            else:
                symbols[term] += coeff

        normalized_assignment = list()
        normalized_assignment2 = list()

        if assignment.is_equals():
            normalized_assignment.append(("="))
            normalized_assignment2.append(("="))
        else:
            normalized_assignment.append(("<=/>="))

        if normalizing_coefficient == 0.0:
            normalized_assignment.append((0.0))
            normalizing_coefficient = 1.0
            if assignment.is_equals():
                normalized_assignment2.append((0.0))
        else:
            normalized_assignment.append(
                normalizing_coefficient/abs(normalizing_coefficient))
            if assignment.is_equals():
                normalized_assignment2.append(
                    (-normalizing_coefficient/abs(normalizing_coefficient)))

        for term in symbols:
            normalized_assignment.append(
                (term, self.normalize_coefficient(symbols[term], normalizing_coefficient)))
            if assignment.is_equals():
                normalized_assignment2.append(
                    (term, self.normalize_coefficient(-symbols[term], normalizing_coefficient)))

        if add_to_norms_aliases:
            if frozenset(normalized_assignment) not in self.norm_aliases:
                self.norm_aliases[frozenset(normalized_assignment)] = list()
            self.norm_aliases[frozenset(
                normalized_assignment)].append(assignment)
            if assignment.is_equals():
                if frozenset(normalized_assignment2) not in self.norm_aliases:
                    self.norm_aliases[frozenset(
                        normalized_assignment2)] = list()
                self.norm_aliases[frozenset(
                    normalized_assignment2)].append(assignment)

        return None if add_to_norms_aliases else normalized_assignment

    def get_allsat(self, formula: FNode, use_ta=False, atoms=None, options={}):
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

        for atom in atoms:
            if not atom.is_symbol(BOOL) and atom not in self.list_norm:
                _ = self.normalize_assignment(atom, True)

        solver = Solver(name="msat", solver_options=solver_options)
        converter = solver.converter

        solver.add_assertion(formula)
        models = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in atoms],
            lambda model: _allsat_callback(model, converter, models))
        
        for i, model in enumerate(models):
            assignments = {}
            for atom in model:
                if atom.is_not():
                    atom = atom.arg(0)
                    value = False
                else:
                    value = True

                if atom.is_symbol(BOOL):
                    assignments[atom] = value
                else:
                    subterms = self.normalize_assignment(atom, False)

                    assert frozenset(subterms) in self.norm_aliases, \
                        "Atom {}\n(subterms: {})\nnot found in\n{}"\
                        .format(atom.serialize(), subterms, "\n".join(str(x) for x in self.norm_aliases.keys()))
                    for element_of_normalization in self.norm_aliases[frozenset(subterms)]:
                        assignments[element_of_normalization] = not value if element_of_normalization.is_lt(
                        ) else value
            models[i] = {a if v else Not(a) for a, v in assignments.items()}
        return models

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
