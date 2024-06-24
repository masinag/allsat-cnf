import argparse
import os
import pathlib
import shutil
import tempfile

import git

REPO_URL = "https://github.com/yogevshalmon/allsat-circuits.git"
DATA_DIR = "data"
BENCH_DIR = "benchmarks"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Folder where all instances will be created (default: cwd)')
    return parser.parse_args()


def copy_files(src_dir: str, dest_dir: str, extension: str):
    src_path = pathlib.Path(src_dir)
    dest_path = pathlib.Path(dest_dir)
    for file in src_path.glob(f'**/*{extension}'):
        shutil.copy(file, dest_path)


def download_directory_from_repo(repo_url, download_dir):
    print(f"Downloading files from {repo_url}  to {download_dir}")
    repo = git.Repo.init(download_dir)
    origin = repo.create_remote('origin', repo_url)
    origin.fetch()
    repo.git.checkout('b57c2d6cba244460008dc6400beef2604a720c24', '--', 'benchmarks')


def organize_files(download_dir, data_dir):
    print(f"Organizing files in {data_dir}")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'random_aig_large_cir_or'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'sta_benchmarks'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'sta_benchmarks_large'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'islis_benchmarks_arithmetic_or'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'islis_benchmarks_arithmetic_xor'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'islis_benchmarks_random_control_or'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'islis_benchmarks_random_control_xor'), exist_ok=True)

    copy_files(os.path.join(download_dir, 'benchmarks', 'random_aig', 'large_cir_or'),
               os.path.join(data_dir, 'random_aig_large_cir_or'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'sta_benchmarks'),
               os.path.join(data_dir, 'sta_benchmarks'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'sta_benchmarks_large'),
               os.path.join(data_dir, 'sta_benchmarks_large'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'islis_benchmarks', 'arithmetic_or'),
               os.path.join(data_dir, 'islis_benchmarks_arithmetic_or'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'islis_benchmarks', 'arithmetic_xor'),
               os.path.join(data_dir, 'islis_benchmarks_arithmetic_xor'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'islis_benchmarks', 'random_control_or'),
               os.path.join(data_dir, 'islis_benchmarks_random_control_or'), '.aag')
    copy_files(os.path.join(download_dir, 'benchmarks', 'islis_benchmarks', 'random_control_xor'),
               os.path.join(data_dir, 'islis_benchmarks_random_control_xor'), '.aag')


def main():
    args = parse_args()
    with tempfile.TemporaryDirectory() as tmp_dir:
        download_directory_from_repo(REPO_URL, tmp_dir)
        organize_files(tmp_dir, args.output)


if __name__ == '__main__':
    main()
