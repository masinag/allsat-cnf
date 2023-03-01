import os

from pysmt.shortcuts import Or, Not, Solver
from tqdm import tqdm

from benchmark.utils.fileio import read_formula_from_file
from benchmark.utils.run import run_with_timeout

MAX_VARS = 50


def get_relevant_benchmarks(data_dir):
    relevant_benchmarks = []
    for filename in (pbar := tqdm(os.listdir(data_dir))):
        pbar.set_description(f"Found {len(relevant_benchmarks)}, processing {filename}")
        full_path = os.path.join(data_dir, filename)
        if is_relevant_benchmark(full_path):
            relevant_benchmarks.append(full_path)
    return relevant_benchmarks


def is_relevant_benchmark(filename):
    header = get_header(filename)
    m, i, l, o, a = parse_header(header)
    if not (0 < i <= MAX_VARS):
        return False
    try:
        return has_at_least_two_models(filename)
    except (RecursionError, TimeoutError):
        return False


def get_header(filename):
    with open(filename, "rb") as f:
        header = f.readline().decode("ascii")
    return header


def parse_header(header):
    header = header.strip()
    header = header.split(" ")[1:]
    header = [int(x) for x in header]
    return header


def has_at_least_two_models(filename):
    phi = read_formula_from_file(filename)
    return find_n_models_or_timeout(phi, 2)


def find_n_models_or_timeout(phi, n):
    return run_with_timeout(find_n_models, 600, phi, n)


def find_n_models(phi, n):
    with Solver(name="msat") as solver:
        solver.add_assertion(phi)
        for _ in range(n):
            if not solver.solve():
                return False
            msat_model = solver.get_model()
            model = [atom if value else Not(atom) for atom, value in msat_model]
            conflict_clause = Or([Not(a) for a in model])
            solver.add_assertion(conflict_clause)
    return True


def write_relevant_benchmarks(relevant_benchmarks, filename):
    with open(filename, "w") as f:
        for benchmark in relevant_benchmarks:
            f.write(f"{os.path.basename(benchmark)}\n")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "aig-bench/data/smtqfbv-aigs/")
    relevant_benchmarks = get_relevant_benchmarks(data_dir)
    print(f"Found {len(relevant_benchmarks)} relevant benchmarks")
    relevant_benchmarks_file = os.path.join(here, "small-benchmarks.txt")
    write_relevant_benchmarks(relevant_benchmarks, relevant_benchmarks_file)


if __name__ == '__main__':
    main()
