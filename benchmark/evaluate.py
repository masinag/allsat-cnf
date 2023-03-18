import argparse
import os
import sys
import time
from typing import Iterable, List, Set, Tuple

from pysmt.environment import reset_env, get_env
from pysmt.fnode import FNode

from local_tseitin.cnfizer import Preprocessor
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.label_cnfizer import LabelCNFizer
from local_tseitin.polarity_cnfizer import PolarityCNFizer
from local_tseitin.utils import get_allsat, is_cnf, SolverOptions
from local_tseitin.utils import get_lra_atoms, get_boolean_variables, check_models
from utils.fileio import get_output_filename, check_output_input, write_result, get_input_files, \
    read_formula_from_file
from utils.logging import log
from utils.parsing import get_options, Mode, arg_positive, PreprocessOptions
from utils.run import run_with_timeout

MODELS_CHECK_MSG = "Checking models..."

PARTIAL_MODELS_MSG = "Generating partial models..."


def parse_args():
    parser = argparse.ArgumentParser(description='Enumerate models of formulas')
    parser.add_argument('input', help='Folder with .json files')
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-m', '--mode', choices=[m.value for m in Mode],
                        required=True, help='Mode to use')
    parser.add_argument('-r', '--with-repetitions', action='store_true',
                        help='Allow generating models with repetitions')
    parser.add_argument('--no-check', action='store_true',
                        help='Do not check the models')
    parser.add_argument('--timeout', type=arg_positive, default=1200,
                        help='Timeout for the solver')
    return parser.parse_args()


def main():
    sys.setrecursionlimit(10000)
    args = parse_args()
    output_file = get_output_filename(args)
    print("Output file: {}".format(output_file))

    check_output_input(args.output, output_file, args.input)
    input_files = get_input_files([args.input])

    time_start = time.time()

    for i, filename in enumerate(input_files):
        setup()
        phi = read_formula_from_file(filename)
        log(PARTIAL_MODELS_MSG, filename, i, input_files)
        enum_timed_out = False
        models = None
        preprocess_options, solver_options = get_options(args)
        phi_cnf, atoms = preprocess_formula(phi, preprocess_options)
        n_clauses = len(phi_cnf.args())
        try:
            time_init = time.time()
            models = get_allsat_or_timeout(phi_cnf, atoms, solver_options)
            total_time = time.time() - time_init
        except TimeoutError:
            total_time = args.timeout
            enum_timed_out = True

        check_timed_out = False
        if not enum_timed_out and should_check_models(args):
            log(MODELS_CHECK_MSG, filename, i, input_files, len(models))
            try:
                check_models_or_timeout(models, phi, args)
            except TimeoutError:
                check_timed_out = True

        res = {
            "filename": filename,
            "n_clauses": n_clauses,
            "models": None if models is None else len(models),
            "time": total_time,
            "enum_timed_out": enum_timed_out,
            "check_timed_out": check_timed_out,
        }
        write_result(args, res, output_file)

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


def setup():
    reset_env()
    get_env().enable_infix_notation = True


def get_allsat_or_timeout(phi: FNode, atoms: Iterable[FNode], solver_options: SolverOptions) -> List[Set[FNode]]:
    models, _ = run_with_timeout(
        get_allsat,
        solver_options.timeout,
        phi,
        atoms=atoms,
        solver_options=solver_options,
    )
    return models


def should_check_models(args) -> bool:
    return not args.no_check and args.mode != "TTA"


def check_models_or_timeout(models, phi, args) -> None:
    return run_with_timeout(check_models, args.timeout, models, phi)


def preprocess_formula(phi, preprocess_options: PreprocessOptions) -> Tuple[FNode, Iterable[FNode]]:
    atoms = get_boolean_variables(phi).union(
        {a for a in get_lra_atoms(phi) if not a.is_equals()}
    )
    if preprocess_options.expand_iff:
        Preprocessor(expand_iff=True).convert_as_formula(phi)
    if preprocess_options.cnf_type == "POL":
        phi = PolarityCNFizer(nnf=preprocess_options.do_nnf, mutex_nnf_labels=preprocess_options.mutex_nnf_labels,
                              label_neg_polarity=preprocess_options.label_neg_polarity).convert_as_formula(phi)
    elif preprocess_options.cnf_type == "LAB":
        phi = LabelCNFizer(nnf=preprocess_options.do_nnf,
                           mutex_nnf_labels=preprocess_options.mutex_nnf_labels).convert_as_formula(phi)
    elif preprocess_options.cnf_type == "CND":
        phi = Preprocessor(binary_operators=True).convert_as_formula(phi)
        phi = LocalTseitinCNFizerConds().convert_as_formula(phi)
    else:
        raise ValueError("Unknown CNF type: {}".format(preprocess_options.cnf_type))
    assert is_cnf(phi)

    return phi, atoms


if __name__ == '__main__':
    main()
