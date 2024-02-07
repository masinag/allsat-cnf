import argparse
import os
import random
import time
from math import log10

from pysmt.shortcuts import write_smtlib
from wmibench.synthetic import synthetic_pa as synthetic_exp
from wmipa.weightconverter import WeightConverterEUF as WeightConverter
from wmipa.wmivariables import WMIVariables

from benchmark.utils.fileio import check_output_can_be_created
from benchmark.utils.parsing import arg_positive_0, arg_positive


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=os.getcwd(),
                        help='Folder where all models will be created (default: cwd)')
    parser.add_argument("-b", "--booleans", required=True, help="number of boolean variables", type=arg_positive_0)
    parser.add_argument("-r", "--reals", required=True, help="number of real variables", type=arg_positive_0)
    parser.add_argument("-d", "--depth", required=True, help="depth of the formula tree", type=arg_positive)
    parser.add_argument("-n", "--number", help="number of problems to generate", type=arg_positive, default=20)
    parser.add_argument("-s", "--seed", help="random seed", type=int, default=666)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.seed is None:
        args.seed = int(time.time())
    random.seed(args.seed)

    weightconverter = WeightConverter(WMIVariables())
    generator = synthetic_exp.ModelGenerator(
        n_reals=args.reals,
        n_bools=args.booleans,
        seedn=args.seed,
    )
    generator.MAX_MONOMIALS = 1

    output_dir = 'models_b{}_r{}_d{}_m{}_s{}'.format(
        args.booleans, args.reals, args.depth, args.number, args.seed)
    output_dir = os.path.join(args.output, output_dir)

    check_output_can_be_created(output_dir)
    os.mkdir(output_dir)

    # generate models
    print("Starting creating models")
    time_start = time.time()
    digits = int(log10(args.number)) + 1
    template = "b{b}_d{d}_s{s}_{templ}.smt2".format(
        b=args.booleans, d=args.depth, s=args.seed, templ="{n:0{d}}")

    for i in range(args.number):
        weight = generator.generate_weights_tree(args.depth)
        skeleton = weightconverter.convert(weight)
        file_name = os.path.join(output_dir, template.format(n=i + 1, d=digits))
        write_smtlib(skeleton, file_name)
        print("\r" * 100, end='')
        print("Model {}/{}".format(i + 1, args.number), end='')

    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
