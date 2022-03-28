import argparse
from pprint import pprint

from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import *
from pysmt.shortcuts import *

for i in range(ord("A"), ord("Z") + 1):
    name = chr(i)
    a = Symbol(name, BOOL)
    globals()[name] = a

cnfizers = {
    "ACT-CNF": LocalTseitinCNFizerActivation,
    "CND-CNF": LocalTseitinCNFizerConds,
}


def main(formula):
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()

    print("Formula: {}".format(formula.serialize()))
    atoms = get_boolean_variables(formula)
    # total models
    total_models = get_allsat(formula, use_ta=False, atoms=atoms)

    non_cnf_models = get_allsat(formula, use_ta=True, atoms=atoms)
    print("NON-CNFIZED MODELS: {}/{}".format(len(non_cnf_models), len(total_models)))
    if args.v:
        pprint(non_cnf_models)

    for cname, cnfizer in cnfizers.items():
        cnf = cnfizer().convert(formula)
        cnf_models = get_allsat(cnf, use_ta=True, atoms=atoms)
        print("{}: {}/{}".format(cname, len(cnf_models), len(total_models)))

        if args.v:
            pprint(cnf_models)
        check_eval_true(formula, cnf_models)
        check_models(cnf_models, total_models)
    print()
