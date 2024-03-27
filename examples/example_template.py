import time

from pysmt.shortcuts import Symbol

from allsat_cnf.label_cnfizer import LabelCNFizer
from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.utils import *

boolean_atoms = []
for i in range(ord("A"), ord("Z") + 1):
    name = chr(i)
    a = Symbol(name, BOOL)
    globals()[name] = a
    boolean_atoms.append(a)

real_variables = []
for i in range(20):
    name = "x{}".format(i)
    x = Symbol(name, REAL)
    globals()[name] = x
    real_variables.append(x)

cnfizers = {
    "LAB": LabelCNFizer(),
    # "POL": PolarityCNFizer(),
    "LABELNEG_POL": PolarityCNFizer(label_neg_polarity=True),
    # "NNF_POL": PolarityCNFizer(nnf=True),
    "NNF_MUTEX_POL": PolarityCNFizer(nnf=True, mutex_nnf_labels=True),
}


def make_example(formula, atoms=None):
    print("Formula: {}".format(formula.serialize()))
    atoms = atoms or (get_boolean_variables(formula) | get_lra_atoms(formula))
    # total models
    start_time = time.time()
    total_models, count_tot = get_allsat(formula, atoms=atoms, solver_options=SolverOptions(use_ta=False))
    assert count_tot == len(total_models)
    final_time = time.time() - start_time
    print("{} total models ({:.02f}s)".format(len(total_models), final_time))

    start_time = time.time()
    non_cnf_models, count_part = get_allsat(formula, atoms=atoms, solver_options=SolverOptions(use_ta=True))
    if not count_part == count_tot:
        print("Warning: model counting not correct ({} vs {})".format(count_part, count_tot))

    print("Solver-CNFization models: {}/{} ({:.02f}s)".format(len(non_cnf_models),
                                                              len(total_models), time.time() - start_time))

    for cname, cnfizer in cnfizers.items():
        cnf = cnfizer.convert_as_formula(formula)
        start_time = time.time()
        cnf_models, count_part = get_allsat(cnf, atoms=atoms, solver_options=SolverOptions(use_ta=True))
        final_time_cnf = time.time() - start_time
        if not count_part == count_tot:
            print("Warning: model counting not correct ({} vs {})".format(count_part, count_tot))
        print("{}: {}/{} ({:.02f}s)".format(cname, len(cnf_models), len(total_models), final_time_cnf))
        check_models(cnf_models, formula)
