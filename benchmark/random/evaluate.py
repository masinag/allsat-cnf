
import argparse
import sys
import os
import time
import json
from os import path
from pysmt.shortcuts import read_smtlib
from local_tseitin.utils import AllSATSolver
from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import *

def get_allsat(phi, mode):
    atoms = get_lra_atoms(phi).union(get_boolean_variables(phi))
    use_ta = True
    if mode == "CND":
        phi = LocalTseitinCNFizerConds().convert(phi)
    elif mode == "ACT":
        phi = LocalTseitinCNFizerActivation().convert(phi)
    elif mode == "TTA":
        use_ta = False
    return AllSATSolver().get_allsat(phi, use_ta=use_ta, atoms=atoms)

def check_input_output(input_dir, output_dir, output_file):
    # check if input dir exists
    if not path.exists(input_dir):
        print("Folder '{}' does not exists".format(input_dir))
        sys.exit(1)

    # check if output dir exists
    if not path.exists(output_dir):
        print("Folder '{}' does not exists".format(output_dir))
        sys.exit(1)

    if output_file is not None:
        output_file = path.join(output_dir, output_file)
        if path.exists(output_file):
            print("File '{}' already exists".format(output_file))


def write_result(mode, res, output_file):
    if not os.path.exists(output_file):
        info = {
            "mode": mode,
            "results": [res]
        }
    else:
        with open(output_file, 'r') as f:
            info = json.load(f)
        info["results"].append(res)

    with open(output_file, 'w') as f:
        json.dump(info, f, indent=4)


def parse_args():
    modes = ["TTA", "AUTO", "ACT", "CND"]

    parser = argparse.ArgumentParser(description='Compute WMI on models')
    parser.add_argument('input', help='Folder with .json files')
    # parser.add_argument('-i', '--input-type', required=True,
    #                     help='Input type', choices=input_types.keys())
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Output folder where to save the result (default: cwd)')
    parser.add_argument('-m', '--mode', choices=modes,
                        required=True, help='Mode to use')
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = args.input
    # input_type = args.input_type
    output_dir = args.output
    mode = args.mode

    output_file = "{}_{}_{}.json".format(
        os.path.split(input_dir.rstrip('/'))[1], mode, int(time.time()))
    output_file = path.join(output_dir, output_file)
    print("Creating... {}".format(output_file))
    check_input_output(input_dir, output_dir, output_file)


    elements = [path.join(input_dir, f) for f in os.listdir(input_dir)]
    files = [e for e in elements if path.isfile(e)]

    print("Started computing")
    time_start = time.time()

    for i, filename in enumerate(files):
        print("{}Problem {:3d}/{:3d}".format("\r"* 300, i + 1, len(files)), end="")
        time_init = time.time()
        phi = read_smtlib(filename)
        models, _ = get_allsat(phi, mode)
        time_total = time.time() - time_init
        res = {
            "filename": filename,
            "models": len(models),
            "time": time_total,
        }
        write_result(mode, res, output_file)

    

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
