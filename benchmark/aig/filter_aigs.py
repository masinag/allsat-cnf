import os

from tqdm import tqdm
from pysmt.shortcuts import is_sat

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


def should_skip_by_name(filename):
    basename = os.path.basename(filename)
    return basename.startswith("count") or basename.startswith("mul")


def is_relevant_benchmark(filename):
    if should_skip_by_name(filename):
        return False
    header = get_header(filename)
    m, i, l, o, a = parse_header(header)
    if not (0 < i <= MAX_VARS):
        return False
    try:
        phi = read_formula_from_file(filename)
        return is_sat_or_timeout(phi)
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


def is_sat_or_timeout(phi):
    return run_with_timeout(is_sat, 600, phi)


def create_subdir_for_relevant_benchmarks(relevant_benchmarks, relevant_benchmarks_dir):
    if os.path.exists(relevant_benchmarks_dir):
        print(f"Directory {relevant_benchmarks_dir} already exists")
        return
    os.mkdir(relevant_benchmarks_dir)
    for filename in relevant_benchmarks:
        basename = os.path.basename(filename)
        dest_filename = os.path.join(relevant_benchmarks_dir, basename)
        os.symlink(filename, dest_filename)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "aig-bench/data/smtqfbv-aigs/")
    relevant_benchmarks = get_relevant_benchmarks(data_dir)
    relevant_benchmarks_dir = os.path.join(here, "aig-bench/data/smtqfbv-aigs-small/")
    create_subdir_for_relevant_benchmarks(relevant_benchmarks, relevant_benchmarks_dir)


if __name__ == '__main__':
    main()
