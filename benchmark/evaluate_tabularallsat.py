import argparse
import os
import sys
import time
from datetime import datetime
from typing import Iterable

from pysmt.environment import reset_env, get_env
from pysmt.fnode import FNode

from allsat_cnf.utils import SolverOptions, get_clauses
from benchmark.tabularallsat_interface import TabularAllSATInterface
from benchmark.io.file import get_output_filename, check_inputs_exist, write_result, get_input_files, \
    read_formula_from_file, check_output_can_be_created, result_exists
from benchmark.mode import Mode
from benchmark.parsing import arg_positive
from benchmark.preprocess import preprocess_formula
from benchmark.run import get_options

MC_CHECK_MSG = "Checking model count..."

RUNNING_LOG = "Running tabularallsat..."


def log_header(filename, i, input_files):
    return "Problem {:3d}/{:3d}: {}".format(i + 1, len(input_files), filename)


def log(msg, filename, i, input_files, *args):
    msg = "{} {}".format(
        log_header(filename, i, input_files),
        msg.format(*args))
    print("{}{: <100}".format("\r" * 100, msg), end="")


def parse_args():
    parser = argparse.ArgumentParser(description='Enumerate models of formulas using tabularallsat')
    parser.add_argument('input', help='Folder with .json files')
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-f', '--filename', default='',
                        help='Filename suffix (default: "")')
    parser.add_argument('-m', '--mode', choices=[m.value for m in Mode],
                        required=True, help='Mode to use')
    parser.add_argument('--timeout', type=arg_positive, default=3600,
                        help='Timeout for the solver')
    parser.add_argument('--tabularallsat-path', type=str, required=True, help='Path to the tabularallsat binary')

    return parser.parse_args()


def main():
    sys.setrecursionlimit(10000)
    args = parse_args()
    output_file = get_output_filename(args)
    check_output_can_be_created(output_file)
    print("Output file: {}".format(output_file))

    check_inputs_exist(args.input)
    input_files = get_input_files([args.input])

    time_start = time.time()

    for i, filename in enumerate(input_files):
        if result_exists(output_file, filename):
            log("Already computed, skipping...", filename, i, input_files)
            continue
        else:
            log("Processing...", filename, i, input_files)

        setup()
        phi = read_formula_from_file(filename)
        enum_timed_out = False
        count = None
        n_models = None

        preprocess_options, solver_options = get_options(args)
        phi_cnf, atoms = preprocess_formula(phi, preprocess_options)
        n_clauses = len(get_clauses(phi_cnf))
        try:
            log(RUNNING_LOG, filename, i, input_files)
            time_init = time.time()

            n_models, count = get_allsat_or_timeout(phi_cnf, atoms, solver_options, args.tabularallsat_path)
            total_time = time.time() - time_init
        except TimeoutError:
            total_time = args.timeout
            enum_timed_out = True

        res = {
            "filename": filename,
            "n_clauses": n_clauses,
            "models": n_models,
            "model_count": count,
            "time": total_time,
            "enum_timed_out": enum_timed_out,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        write_result(args, res, output_file)

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


def setup():
    reset_env()
    get_env().enable_infix_notation = True


def get_allsat_or_timeout(phi: FNode, atoms: Iterable[FNode], solver_options: SolverOptions, ta_path: str) -> tuple[
    int, int]:
    ta = TabularAllSATInterface(ta_path)
    return ta.projected_allsat(phi, set(atoms), solver_options.timeout)


if __name__ == '__main__':
    main()
