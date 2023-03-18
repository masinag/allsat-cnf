import argparse
import os
import random
import time
from math import log10
from os import path

from pysmt.shortcuts import Symbol, BOOL, Or, Not, And, Iff, write_smtlib

from benchmark.utils.fileio import check_output_input
from benchmark.utils.parsing import arg_positive_0, arg_positive


def random_formula(depth, atoms, operators, neg_prob):
    if depth == 0:
        leaf = random.choice(atoms)
        if random.random() < 0.5:
            leaf = Not(leaf)
        return leaf
    operator = random.choices(list(operators.keys()), weights=list(operators.values()))[0]

    left = random_formula(depth - 1, atoms, operators, neg_prob)
    right = random_formula(depth - 1, atoms, operators, neg_prob)
    node = operator(left, right)
    negate = random.random() < neg_prob
    if negate:
        node = Not(node)
    return node


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generates random support and models.')
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Folder where all models will be created (default: cwd)')
    parser.add_argument('-b', '--booleans', default=3, type=arg_positive_0,
                        help='Maximum number of bool variables (default: 3)')
    parser.add_argument('-d', '--depth', default=3, type=arg_positive,
                        help='Depth of the formula tree (default: 3)')
    parser.add_argument('--xnnf', action='store_true', default=False,
                        help='Set this flag to generate formulas in XNNF, i.e. formulas where negations occur only '
                             'at literal level (default: False)')
    parser.add_argument('-m', '--models', default=20, type=arg_positive,
                        help='Number of model files (default: 20)')
    parser.add_argument('-s', '--seed', type=arg_positive_0,
                        help='Random seed (optional)')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.seed is None:
        args.seed = int(time.time())

    random.seed(args.seed)

    output_dir = 'models_b{}_d{}_m{}_s{}'.format(
        args.booleans, args.depth, args.models, args.seed)
    output_dir = path.join(args.output, output_dir)

    check_output_input(args.output, output_dir)
    os.mkdir(output_dir)

    # init generator
    boolean_atoms = [Symbol(chr(i), BOOL) for i in range(ord("A"), ord("A") + args.booleans)]

    # generate models
    print("Starting creating models")
    time_start = time.time()
    digits = int(log10(args.models)) + 1
    template = "b{b}_d{d}_s{s}_{templ}.smt2".format(
        b=args.booleans, d=args.depth, s=args.seed, templ="{n:0{d}}")

    operators = {
        Iff: 1 / 10,
        Or: 9 / 20,
        And: 9 / 20,
    }
    weights_sum = sum(operators.values())
    for k in operators:
        operators[k] /= weights_sum
    neg_prob = 0.0 if args.xnnf else 0.5

    for i in range(args.models):
        problem = random_formula(args.depth, boolean_atoms, operators, neg_prob)
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
