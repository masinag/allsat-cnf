import argparse
import json
import os
import sys
import time
from os import path
from pysmt.rewritings import PolarityCNFizer, nnf

# from local_tseitin.activation_cnfizer import LocalTseitinCNFizerActivation
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import AIG, get_lra_atoms, get_boolean_variables, check_models
from local_tseitin.utils import get_allsat as allsat


def get_allsat(phi, mode, with_repetitions):
    atoms = get_lra_atoms(phi).union(get_boolean_variables(phi))
    use_ta = True
    expand_iff = False

    if mode.startswith("EXPAND_"):
        expand_iff = True
        mode = mode.lstrip("EXPAND_")

    if mode.startswith("NNF_"):
        phi = nnf(phi)
        mode = mode.lstrip("NNF_")

    if mode == "POL":
        phi = PolarityCNFizer().convert_as_formula(phi)
    elif mode == "CND":
        phi = LocalTseitinCNFizerConds(expand_iff=expand_iff).convert_as_formula(phi)
    # elif mode == "ACT":
    #     phi = LocalTseitinCNFizerActivation().convert_as_formula(phi)
    elif mode == "TTA":
        use_ta = False
    return allsat(phi, use_ta=use_ta, atoms=atoms,
                  options={"dpll.allsat_allow_duplicates": "true" if with_repetitions else "false"})


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
    modes = ["TTA", "AUTO", "POL", "NNF_POL", "CND", "NNF_CND", "EXPAND_CND"]

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
    return parser.parse_args()


def read_aig(filename):
    return AIG.from_file(filename).to_pysmt()


def main():
    args = parse_args()
    input_dir = args.input
    # input_type = args.input_type
    output_dir = args.output
    mode = args.mode
    with_repetitions = args.with_repetitions
    do_check_models = not args.no_check

    smode = f"{mode}{'_REP' if with_repetitions else ''}"
    output_file = "{}_{}_{}.json".format(
        os.path.split(input_dir.rstrip('/'))[1], smode, int(time.time()))
    output_file = path.join(output_dir, output_file)
    print("Creating... {}".format(output_file))
    check_input_output(input_dir, output_dir, output_file)

    elements = [path.join(input_dir, f) for f in sorted(os.listdir(input_dir))]
    files = [e for e in elements if not path.isdir(e)]

    print("Started computing")
    time_start = time.time()

    for i, filename in enumerate(files):
        phi = read_aig(filename)
        print("{}Problem {:3d}/{:3d} generating partial models...".format("\r" * 600, i + 1, len(files)), end="")
        time_init = time.time()
        models, n_models = get_allsat(phi, mode, with_repetitions)
        time_total = time.time() - time_init
        if do_check_models and mode not in ["TTA", "AUTO"]:
            # print("{}Problem {:3d}/{:3d} generating total models...".format("\r" * 600, i + 1, len(files)), end="")
            # tta, _ = get_allsat(phi, "TTA", False)
            print(
                "{}Problem {:3d}/{:3d} checking models ({}/{})...".format("\r" * 600, i + 1, len(files), len(models),
                                                                          n_models),
                end="")
            check_models(models, phi)
        res = {
            "filename": filename,
            "models": len(models),
            "time": time_total,
            "repetitions": with_repetitions,
        }
        write_result(smode, res, output_file)

    seconds = time.time() - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()