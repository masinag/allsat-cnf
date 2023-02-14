import argparse
import os
import time

from pysmt.environment import reset_env, get_env
from pysmt.rewritings import PolarityCNFizer, nnf

from benchmark.utils.fileio import get_output_filename, check_input_output, write_result, get_input_files, \
    read_formula_from_file
from benchmark.utils.logging import log
from benchmark.utils.parsing import parse_mode
from local_tseitin.cnfizer import Preprocessor
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import get_allsat as allsat
from local_tseitin.utils import get_lra_atoms, get_boolean_variables, check_models
from utils.run import run_with_timeout

MODELS_CHECK_MSG = "Checking models..."

PARTIAL_MODELS_MSG = "Generating partial models..."


def parse_args():
    modes = ["TTA", "AUTO", "NNF_AUTO", "POL", "NNF_POL", "CND", "NNF_CND", "EXPAND_CND"]

    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input', help='Folder with .json files')
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-m', '--mode', choices=modes,
                        required=True, help='Mode to use')
    parser.add_argument('-r', '--with-repetitions', action='store_true',
                        help='Allow generating models with repetitions')
    parser.add_argument('--no-check', action='store_true',
                        help='Do not check the models')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Timeout for the solver')
    return parser.parse_args()


def main():
    args = parse_args()
    output_file = get_output_filename(args)
    print("Output file: {}".format(output_file))

    check_input_output(args.input, args.output, output_file)
    input_files = get_input_files(args.input)

    time_start = time.time()

    for i, filename in enumerate(input_files):
        setup()
        phi = read_formula_from_file(filename)
        log(PARTIAL_MODELS_MSG, filename, i, input_files)
        try:
            total_time, models = get_allsat_or_timeout(phi, args)
            if should_check_models(args):
                log(MODELS_CHECK_MSG, filename, i, input_files, len(models))
                check_models_or_timeout(models, phi, args)
        except TimeoutError:
            total_time = args.timeout
            models = []

        res = {
            "filename": filename,
            "models": len(models),
            "time": total_time,
        }
        write_result(args, res, output_file)

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


def setup():
    reset_env()
    get_env().enable_infix_notation = True


def get_allsat_or_timeout(phi, args):
    atoms = get_lra_atoms(phi).union(get_boolean_variables(phi))
    mode, expand_iff, do_nnf = parse_mode(args.mode)
    phi = preprocess_formula(phi, expand_iff, do_nnf, mode)
    options = {}
    if args.with_repetitions:
        options["dpll.allsat_allow_duplicates"] = "true"
    use_ta = mode != "TTA"

    time_init = time.time()

    models, _ = run_with_timeout(
        allsat,
        args.timeout,
        phi,
        use_ta=use_ta,
        atoms=atoms,
        options=options
    )
    time_total = time.time() - time_init

    return time_total, models


def should_check_models(args):
    return not args.no_check and args.mode not in ["TTA", "AUTO"]


def check_models_or_timeout(models, phi, args):
    return run_with_timeout(check_models, args.timeout, models, phi)


def preprocess_formula(phi, expand_iff, do_nnf, mode):
    if expand_iff:
        Preprocessor(expand_iff=True).convert_as_formula(phi)
    if do_nnf:
        phi = nnf(phi)
    if mode == "POL":
        phi = PolarityCNFizer().convert_as_formula(phi)
    elif mode == "CND":
        phi = LocalTseitinCNFizerConds().convert_as_formula(phi)

    return phi


if __name__ == '__main__':
    main()
