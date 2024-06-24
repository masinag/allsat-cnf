import argparse
import os
import random
import tempfile
import time
import urllib.request
from math import log10

from pysmt.shortcuts import write_smtlib, Not, And

from ..io.bench_adapter import BenchAdapter
from ..io.file import check_inputs_exist, check_output_can_be_created
from ..parsing import arg_positive

FILES = [
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c432.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c499.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c880.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c1355.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c1908.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c2670.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c3540.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c5315.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c6288.bench",
    "https://computing.ece.vt.edu/~mhsiao/ISCAS85/c7552.bench",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default=os.getcwd(),
                        help='Folder where all instances will be created (default: cwd)')
    parser.add_argument("-m", "--models",
                        help="Number of instances for each percentage to generate",
                        type=arg_positive, default=5)
    parser.add_argument("-s", "--seed", help="random seed", type=int, default=666)
    return parser.parse_args()


def generate_instances(circuit_outputs, percentage, n_instances):
    n_outputs_to_sample = int(len(circuit_outputs) * percentage / 100)
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


def get_iscas_files():
    with tempfile.TemporaryDirectory() as tmp_dir:
        for file_url in FILES:
            file_name = os.path.join(tmp_dir, os.path.basename(file_url))
            file_path, _ = urllib.request.urlretrieve(file_url, file_name)
            yield file_path


def main():
    args = parse_args()
    random.seed(args.seed)

    os.makedirs(args.output, exist_ok=True)

    for input_file in get_iscas_files():
        basename = os.path.basename(input_file)
        output_dir = '{}_m{}_s{}'.format(basename, args.models, args.seed)
        output_dir = os.path.join(args.output, output_dir)

        check_inputs_exist(input_file)
        check_output_can_be_created(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        # generate instances
        print("Starting creating instances")
        time_start = time.time()
        digits = int(log10(args.models)) + 1
        template = "{b}_s{s}_p{p}_{templ}.smt2".format(
            b=basename, s=args.seed, p="{p:03}", templ="{n:0{d}}")
        _, circuit_outputs = BenchAdapter.from_file(input_file).to_pysmt()
        for percentage in range(60, 101, 10):
            print("Generating {} instances for {} with {}% of the variables".format(
                args.models, input_file, percentage))
            instances = generate_instances(circuit_outputs, percentage, args.models)
            for i, instance in enumerate(instances):
                file_name = os.path.join(output_dir, template.format(p=round(percentage), n=i + 1, d=digits))
                write_smtlib(instance, file_name)
                print("\r" * 100, end='')
                print("Model {}/{}".format(i + 1, args.models), end='')

        print()
        time_end = time.time()
        seconds = time_end - time_start
        print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
