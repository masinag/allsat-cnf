import numpy as np

from benchmark.utils.logging import log
from local_tseitin.bench_adapter import BenchAdapter

import argparse
import os
import random
import time
from math import log10

from pysmt.shortcuts import write_smtlib, Not, And

from benchmark.utils.fileio import check_output_input, get_input_files
from benchmark.utils.parsing import arg_positive_0, arg_positive


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="Input file")
    parser.add_argument('-o', '--output', type=str, default=os.getcwd(),
                        help='Folder where all instances will be created (default: cwd)')
    parser.add_argument("-m", "--models",
                        help="Number of instances for each percentage to generate",
                        type=arg_positive, default=10)
    parser.add_argument("-s", "--seed", help="random seed", type=int, default=666)
    return parser.parse_args()


def generate_instances(circuit_outputs, percentage, n_instances):
    n_outputs_to_sample = int(len(circuit_outputs) * percentage)
    instances = []
    for i in range(n_instances):
        model = []
        for circuit_output in random.sample(circuit_outputs, n_outputs_to_sample):
            if random.random() < 0.5:
                model.append(circuit_output)
            else:
                model.append(Not(circuit_output))
        instances.append(And(model))
    return instances


def main():
    args = parse_args()
    if args.seed is None:
        args.seed = int(time.time())
    random.seed(args.seed)

    basename = os.path.basename(args.input)
    output_dir = '{}_m{}_s{}'.format(basename, args.models, args.seed)
    output_dir = os.path.join(args.output, output_dir)

    check_output_input(args.output, output_dir, args.input)
    os.mkdir(output_dir)

    # generate instances
    print("Starting creating instances")
    time_start = time.time()
    digits = int(log10(args.models)) + 1
    template = "{b}_s{s}_p{p}_{templ}.smt2".format(
        b=basename, s=args.seed, p="{p:03}", templ="{n:0{d}}")
    input_file = args.input
    _, circuit_outputs = BenchAdapter.from_file(input_file).to_pysmt()
    for percentage in np.arange(0.1, 1.1, 0.1):
        print("Generating {} instances for {} with {}% of the variables".format(
            args.models, input_file, percentage * 100))
        instances = generate_instances(circuit_outputs, percentage, args.models)
        for i, instance in enumerate(instances):
            file_name = os.path.join(output_dir, template.format(p=round(percentage * 10), n=i + 1, d=digits))
            write_smtlib(instance, file_name)
            print("\r" * 100, end='')
            print("Model {}/{}".format(i + 1, args.models), end='')

    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
