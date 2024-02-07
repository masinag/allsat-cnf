import argparse
import json
import os
import sys
from typing import List, Optional

import matplotlib
import pandas as pd

from benchmark.utils.fileio import get_input_files, check_inputs_exist
from benchmark.utils.parsing import Mode
from benchmark.utils.plotting.ecdf_plotter import ECDFPlotter
from benchmark.utils.plotting.scatter_plotter import ScatterPlotter

matplotlib.use("pgf")
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'text.usetex': True,
    'pgf.rcfonts': False,
})

ORDER: List[Mode] = [Mode.TTA, Mode.LAB, Mode.NNF_LAB, Mode.POL, Mode.NNF_POL, Mode.LABELNEG_POL, Mode.NNF_MUTEX_POL, ]
# Mode.NOPC_POL, Mode.NOPC_LABELNEG_POL, Mode.NOPC_NNF_POL, Mode.NOPC_NNF_MUTEX_POL]

COLOR = {
    Mode.LAB: "#ff7f00",
    Mode.NNF_LAB: "black",
    Mode.TTA: "blue",
    Mode.POL: "orange",
    Mode.NNF_POL: "purple",
    Mode.NNF_MUTEX_POL: "#4daf4a",
    Mode.LABELNEG_POL: "#377eb8",
    # Mode.NOPC_POL: "olive",
    # Mode.NOPC_LABELNEG_POL: "cyan",
    # Mode.NOPC_NNF_POL: "magenta",
    # Mode.NOPC_NNF_MUTEX_POL: "lime",
}

NAME_MAPPING = {
    Mode.LAB: r"$\mathsf{CNF_{Ts}}(\varphi)$",
    Mode.LABELNEG_POL: r"$\mathsf{CNF_{PG}}(\varphi)$",
    Mode.NNF_MUTEX_POL: r"$\mathsf{CNF_{PG}}(\mathsf{NNF}(\varphi))$",
}

LINESTYLES = {
    Mode.LAB: "--",
    Mode.LABELNEG_POL: "-",
    Mode.NNF_MUTEX_POL: "-.",
}


def error(msg=""):
    print(msg)
    sys.exit(1)


def parse_inputs(input_files: dict[str, list[str]], with_repetitions: bool, timeout: Optional[int],
                 timeout_models: Optional[int]) -> pd.DataFrame:
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

    # pivot
    pivot_data = data.pivot(index=['problem_set', 'filename'], columns='mode', values=['time', 'models', 'enum_timed_out'])
    # data = data \
    #     .groupby(["problem_set", "filename", "mode"]) \
    #     .aggregate(time=("time", "min"),
    #                models=("models", "min"),
    #                n_clauses=("n_clauses", "min"),
    #                enum_timed_out=("enum_timed_out", "any"),
    #                ) \
    #     .unstack()  # .reset_index(drop=True)
    return pivot_data

    # # sort by increasing number of models
    # modes = data.columns.get_level_values(0).unique()
    # modes = [mode for mode in ORDER if mode in modes]
    #
    # sort_by = [("models", mode) for mode in modes]
    # data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    # return data


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
    modes = data.columns.get_level_values(1).unique()
    modes = [mode for mode in ORDER if mode.value in modes]
    tot_data = data[("enum_timed_out", modes[0].value)].count()
    for mode in modes:
        n_timeouts = data[("enum_timed_out", mode.value)].sum()
        print(f"{mode}: {n_timeouts}/{tot_data} timeouts")


def main():
    args = parse_args()
    print(args.problem_set)
    problem_sets: dict[str, List[str]] = args.problem_set
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
    # find entries where Mode.LABELNEG_POL < Mode.NNF_MUTEX_POL wrt 'models'
    anomalous = data[data[('models', Mode.LABELNEG_POL.value)] < data[('models', Mode.NNF_MUTEX_POL.value)]]


    # print("Anomalous entries filenames:")
    # print(anomalous.index.get_level_values(1).unique())

    # ecdf_plotter = ECDFPlotter(data, output_dir, filename, COLOR, [Mode.NNF_MUTEX_POL, Mode.LABELNEG_POL, Mode.LAB],
    #                            timeout, timeout_models, NAME_MAPPING, LINESTYLES)
    # ecdf_plotter.plot_time()

    scatter_plotter = ScatterPlotter(data, output_dir, filename, COLOR, ORDER, timeout, timeout_models, NAME_MAPPING, LINESTYLES)
    scatter_plotter.plot_models_all_vs_all()
    scatter_plotter.plot_time_all_vs_all()

    # count_timeouts(data)


if __name__ == "__main__":
    main()
