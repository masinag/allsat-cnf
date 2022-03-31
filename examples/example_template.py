import argparse
import time
from pprint import pprint

from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import *
from pysmt.shortcuts import *


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
    "CND-CNF": LocalTseitinCNFizerConds,
}


def make_example(formula, atoms = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()

    print("Formula: {}".format(formula.serialize()))
    atoms = atoms or (get_boolean_variables(formula) | get_lra_atoms(formula))
    # total models
    start_time = time.time()
    total_models, count_tot = get_allsat(formula, use_ta=False, atoms=atoms)
    assert count_tot == len(total_models)
    print("{} total models ({:.02f}s)".format(
        len(total_models), time.time() - start_time))

    start_time = time.time()
    non_cnf_models, count_part = get_allsat(formula, use_ta=True, atoms=atoms)
    if not count_part == count_tot:
        print("Warning: model counting not correct ({} vs {})".format(count_part, count_tot))
    print("NON-CNFIZED MODELS: {}/{} ({:.02f}s)".format(len(non_cnf_models),
          len(total_models), time.time() - start_time))
    if args.v:
        pprint(non_cnf_models)

    for cname, cnfizer in cnfizers.items():
        cnf = cnfizer(verbose=args.v).convert(formula)
        start_time = time.time()
        cnf_models, count_part = get_allsat(cnf, use_ta=True, atoms=atoms)
        if not count_part == count_tot:
            print("Warning: model counting not correct ({} vs {})".format(count_part, count_tot))
        print("{}: {}/{} ({:.02f}s)".format(cname, len(cnf_models),
              len(total_models), time.time() - start_time))

        if args.v:
            pprint(cnf_models)
        check_models(cnf_models, formula)
    print()
