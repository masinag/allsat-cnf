import json
import os
import sys
import time
from os import path

from pysmt.shortcuts import read_smtlib

from benchmark.utils.parsing import get_full_name_mode
from local_tseitin.utils import AIGAdapter


def get_output_filename(args):
    output_dir = args.output
    output_file = generate_output_filename_from_args(args)
    return path.join(output_dir, output_file)


def generate_output_filename_from_args(args):
    input_filename = os.path.split(args.input.rstrip('/'))[1]
    output_file = "{}_{}_{}.json".format(
        input_filename,
        get_full_name_mode(args),
        int(time.time()))
    return output_file


def check_output_input(output_dir, output_file, input_dir=None):
    if not path.exists(output_dir):
        print("'{}' does not exists".format(output_dir))
        sys.exit(1)

    if path.exists(output_file):
        print("'{}' already exists. Remove it and retry".format(output_file))
        sys.exit(1)

    if input_dir is not None and not path.exists(input_dir):
        print("Folder '{}' does not exists".format(input_dir))
        sys.exit(1)


def write_result(args, res, output_file):
    if not os.path.exists(output_file):
        info = {
            "mode": get_full_name_mode(args),
            "results": [res]
        }
    else:
        with open(output_file, 'r') as f:
            info = json.load(f)
        info["results"].append(res)

    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)


def read_aig(filename):
    return AIGAdapter.from_file(filename).to_pysmt()


def read_formula_from_file(filename):
    if filename.endswith(".aig"):
        return read_aig(filename)
    elif filename.endswith(".smt2"):
        return read_smtlib(filename)
    else:
        raise ValueError("Unknown file extension: {}".format(filename))


def get_input_files(input_dir):
    elements = [path.join(input_dir, f) for f in sorted(os.listdir(input_dir))]
    return [e for e in elements if not path.isdir(e)]
