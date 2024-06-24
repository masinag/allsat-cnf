import argparse
import json
import os
import sys
from collections import namedtuple

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from benchmark.io.file import get_input_files, check_inputs_exist
from benchmark.benchmark.mode import Mode
from benchmark.plotting.ecdf_plotter import ECDFPlotter
from benchmark.plotting.scatter_plotter import ScatterPlotter

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})

Style = namedtuple("Style", ["color", "marker", "linestyle", "label", "order_index"])

MODE_STYLES = {
    Mode.TTA: Style("blue", None, None, r"$\mathsf{TTA}(\varphi)$", 3),
    Mode.LAB: Style("#ff7f00", None, "--", r"$\mathsf{CNF_{Ts}}(\varphi)$", 2),
    # Mode.NNF_LAB: Style("black", None, None, r"$\mathsf{CNF_{Ts}}(\mathsf{NNF}(\varphi))$", 2),
    # Mode.POL: Style("orange", None, None, r"$\mathsf{CNF_{PG}}(\varphi)$", 3),
    # Mode.NNF_POL: Style("purple", None, None, r"$\mathsf{CNF_{PG}}(\mathsf{NNF}(\varphi))$", 4),
    Mode.LABELNEG_POL: Style("#377eb8", None, "-", r"$\mathsf{CNF_{PG}}(\varphi)$", 0),
    Mode.NNF_MUTEX_POL: Style("#4daf4a", None, "-.", r"$\mathsf{CNF_{PG}}(\mathsf{NNF}(\varphi))$", 1),
}

_cm = plt.colormaps["Set2"].colors

PROBLEM_SET_STYLES = {
    "syn-bool": Style(_cm[2], "s", None, "Syn-Bool", 0),
    "iscas85": Style(_cm[1], "o", None, "ISCAS85", 1),
    "aig": Style(_cm[0], "^", None, "AIG", 2),
    "syn-lra": Style(_cm[3], "D", None, "Syn-LRA", 3),
    "wmi": Style(_cm[4], "v", None, "WMI", 4),
}


def error(msg=""):
    print(msg)
    sys.exit(1)


def parse_inputs(input_files: dict[str, list[str]], with_repetitions: bool, timeout: int | None,
                 timeout_models: int | None) -> pd.DataFrame:
    data = []
    for ps_name, input_files in input_files.items():
        print(f"Problem set: {ps_name}")
        for filename in input_files:
            with open(filename) as f:
                result_out = json.load(f)
            if result_out["with_repetitions"] != with_repetitions:
                continue
            print(f"Found {filename}")
            mode = result_out["mode"]
            for result in result_out["results"]:
                result["problem_set"] = ps_name
                result["mode"] = mode
                if type(result["enum_timed_out"]) != bool:
                    print("--------------", result)
                if result["enum_timed_out"]:
                    result["models"] = timeout_models
                    result["time"] = timeout

            data.extend(result_out["results"])

    return pd.DataFrame(data)


def group_data(data: pd.DataFrame) -> pd.DataFrame:
    pivot_data = data.pivot(index=['problem_set', 'filename'], columns='mode',
                            values=['time', 'models', 'enum_timed_out'])
    return pivot_data


def parse_args():
    parser = argparse.ArgumentParser(description="Plot results")
    parser.add_argument(
        "-problem_set", nargs="+", action="append", metavar=("name", "dirs"),
        help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Output folder where to put the plots (default: cwd)")
    parser.add_argument("-f", "--filename", default="",
                        help="Filename suffix (default: '')")
    parser.add_argument("-t", "--timeout", type=int, default=None, help="Timeout (default: None)")
    parser.add_argument("-tm", "--timeout-models", type=int, default=None,
                        help="Number of models to plot for timeouts (default: None)")
    parser.add_argument("--with-repetitions", action="store_true",
                        help="Whether to plot results allowing non-disjoint models (default: False)")
    parser.add_argument("--scatter", action="store_true", help="Plot scatter plots")
    parser.add_argument("--ecdf", action="store_true", help="Plot ECDF plots")
    args = parser.parse_args()

    problem_sets = {}
    for ps in args.problem_set:
        if len(ps) < 2:
            error("Problem set must contain at least a name and a folder or a file")
        else:
            problem_sets[ps[0]] = ps[1:]
    args.problem_set = problem_sets
    return args


def count_timeouts(data: pd.DataFrame):
    # for each problem set, count the number of timeouts and the number of problems
    # remember: data has a multiindex with levels "problem_set" and "filename", and columns ("enum_timed_out", mode)
    # for each mode
    # compute sum and count of timeouts
    timeouts = data["enum_timed_out"].groupby("problem_set").sum()
    n_problems = data["enum_timed_out"].groupby("problem_set").count()

    print("Timeouts:")
    print(timeouts)
    print("Total problems:")
    print(n_problems)


def main():
    args = parse_args()
    print(args.problem_set)
    problem_sets: dict[str, list[str]] = args.problem_set
    output_dir: str = args.output
    filename: str = args.filename
    timeout: int = args.timeout
    timeout_models: int = args.timeout_models
    with_repetitions: bool = args.with_repetitions

    for dirs in problem_sets.values():
        check_inputs_exist(dirs)

    print(problem_sets)

    input_files = {name: get_input_files(dirs) for name, dirs in problem_sets.items()}
    data = parse_inputs(input_files, with_repetitions, timeout=timeout, timeout_models=timeout_models)
    data = group_data(data)

    if args.ecdf:
        ecdf_plotter = ECDFPlotter(data, output_dir, filename, timeout, timeout_models, MODE_STYLES, PROBLEM_SET_STYLES)
        ecdf_plotter.plot_time()

    if args.scatter:
        scatter_plotter = ScatterPlotter(data, output_dir, filename, timeout, timeout_models, MODE_STYLES,
                                         PROBLEM_SET_STYLES)

        scatter_plotter.plot_models_all_vs_all(separate_problem_sets=True)
        scatter_plotter.plot_models_all_vs_all(separate_problem_sets=False)
        scatter_plotter.plot_time_all_vs_all(separate_problem_sets=True)
        scatter_plotter.plot_time_all_vs_all(separate_problem_sets=False)

    count_timeouts(data)


if __name__ == "__main__":
    main()
