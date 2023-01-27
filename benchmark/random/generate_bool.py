import random
from math import log10

from pysmt.shortcuts import Symbol, BOOL, Or, Not, And, Iff, write_smtlib
import argparse
import time
from os import path
import sys
import os


def random_formula(depth, atoms, operators, weights):
    if depth == 0:
        operator = random.choice([Or, Not])
        if operator is Or:
            return random.choice(atoms)
        else:
            return Not(random.choice(atoms))
    # operator = random.choice([Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Or, And, Iff])
    operator = random.choices(operators, weights=weights, k=1)[0]
    if operator is Not:
        return Not(random_formula(depth - 1, atoms, operators, weights))
    left = random_formula(depth - 1, atoms, operators, weights)
    right = random_formula(depth - 1, atoms, operators, weights)
    return operator(left, right)


def parse_args():
    def positive_0(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError(
                'Expected positive integer, found {}'.format(value))
        return ivalue

    def positive(value):
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(
                'Expected positive integer (no 0), found {}'.format(value))
        return ivalue

    parser = argparse.ArgumentParser(
        description='Generates random support and models.')
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Folder where all models will be created (default: cwd)')
    parser.add_argument('-b', '--booleans', default=3, type=positive_0,
                        help='Maximum number of bool variables (default: 3)')
    parser.add_argument('-d', '--depth', default=3, type=positive,
                        help='Depth of the formula tree (default: 3)')
    parser.add_argument('--no-xnnf', action='store_true', default=False,
                        help='Set this flag to generate formulas with negations also not '
                             'at literal level (default: False)')
    parser.add_argument('-m', '--models', default=20, type=positive,
                        help='Number of model files (default: 20)')
    parser.add_argument('-s', '--seed', type=positive_0,
                        help='Random seed (optional)')

    return parser.parse_args()


def check_input_output(output_path, output_dir):
    # check if dir exists
    if (not path.exists(output_path)):
        print("Folder '{}' does not exists".format(output_path))
        sys.exit(1)
    # check if this model is already created
    if (path.exists(output_dir)):
        print("A dataset of models with this parameters already exists in the output folder. Remove it and retry")
        sys.exit(1)
    # create dir
    os.mkdir(output_dir)
    print("Created folder '{}'".format(output_dir))


def main():
    args = parse_args()

    if args.seed is None:
        args.seed = int(time.time())

    random.seed(args.seed)

    output_dir = 'models_b{}_d{}_m{}_s{}'.format(
        args.booleans, args.depth, args.models, args.seed)
    output_dir = path.join(args.output, output_dir)

    check_input_output(args.output, output_dir)

    # init generator
    boolean_atoms = [Symbol(chr(i), BOOL) for i in range(ord("A"), ord("A") + args.booleans)]

    # generate models
    print("Starting creating models")
    time_start = time.time()
    digits = int(log10(args.models)) + 1
    template = "b{b}_d{d}_s{s}_{templ}.smt2".format(
        b=args.booleans, d=args.depth, s=args.seed, templ="{n:0{d}}")

    operators = [Or, And, Iff]
    weights = [10, 10, 2]
    if not args.no_xnnf:
        operators += [Not]
        weights += [4]
    weights_sum = sum(weights)
    normalized_weights = [w / weights_sum for w in weights]

    for i in range(args.models):
        problem = random_formula(args.depth, boolean_atoms, operators, normalized_weights)
        file_name = path.join(output_dir, template.format(n=i + 1, d=digits))
        write_smtlib(problem, file_name)
        print("\r" * 100, end='')
        print("Model {}/{}".format(i + 1, args.models), end='')

    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
