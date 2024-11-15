import json
import os
import os.path
import sys

from pysmt.shortcuts import read_smtlib

from ..io.aig import AIGAdapter
from ..parsing import get_full_name_mode


def get_output_filename(args):
    output_dir = args.output
    output_file = generate_output_filename_from_args(args)
    return os.path.join(output_dir, output_file)


def generate_output_filename_from_args(args):
    input_filename = os.path.split(args.input.rstrip('/'))[1]
    output_file = "{}_{}{}.json".format(
        input_filename,
        get_full_name_mode(args),
        args.filename
    )
    return output_file


def check_inputs_exist(input_dir: str | list[str]):
    if input_dir is not None:
        if isinstance(input_dir, str):
            input_dir = [input_dir]
        for input_dir in input_dir:
            if not os.path.exists(input_dir):
                print("Folder '{}' does not exists".format(input_dir))
                sys.exit(1)


def check_output_can_be_created(output_path):
    """Given an output_path in the form <path>/<basename>, check that path exists
    """
    path, _ = os.path.split(output_path)
    if not os.path.exists(path):
        print("'{}' does not exists, creating it...".format(path))


def write_result(args, res, output_file):
    if not os.path.exists(output_file):
        with_repetitions = args.with_repetitions if "with_repetitions" in args else False
        info = {
            "mode": args.mode,
            "with_repetitions": with_repetitions,
            "results": [res]
        }
    else:
        with open(output_file, 'r') as f:
            info = json.load(f)
        info["results"].append(res)

    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)


def result_exists(output_file, filename):
    if not os.path.exists(output_file):
        return False
    with open(output_file, 'r') as f:
        info = json.load(f)
    return any(r["filename"] == filename for r in info["results"])


def read_formula_from_file(filename):
    if filename.endswith(".aig") or filename.endswith(".aag"):
        return AIGAdapter.from_file(filename).to_pysmt()
    elif filename.endswith(".smt2"):
        return read_smtlib(filename)
    else:
        raise ValueError("Unknown file extension: {}".format(filename))


def get_input_files(input_dirs: list[str]) -> list[str]:
    input_files = []
    for input_dir in input_dirs:
        if not os.path.exists(input_dir):
            raise IOError("Input folder '{}' does not exists".format(input_dir))
        if not os.path.isdir(input_dir):
            input_files.append(input_dir)
            continue
        for filename in os.listdir(input_dir):
            filepath = os.path.join(input_dir, filename)
            if not os.path.isdir(filepath):
                input_files.append(filepath)
            else:
                input_dirs.append(filepath)
    if not input_files:
        raise IOError("No file found: {}".format(input_dirs))
    input_files = sorted(input_files)
    print(f"{len(input_files)} Files found")
    return input_files
