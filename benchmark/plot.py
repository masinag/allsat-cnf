import argparse
import json
import os
import sys
from typing import List, Optional

import matplotlib
import pandas as pd

from benchmark.utils.fileio import get_input_files, check_output_input
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

ORDER: List[Mode] = [Mode.TTA, Mode.LAB, Mode.NNF_LAB, Mode.POL, Mode.NNF_POL, Mode.LABELNEG_POL, Mode.NNF_MUTEX_POL,
                     Mode.NOPC_POL, Mode.NOPC_LABELNEG_POL, Mode.NOPC_NNF_POL, Mode.NOPC_NNF_MUTEX_POL]

COLOR = {
    Mode.LAB: "#ff7f00",
    Mode.NNF_LAB: "black",
    Mode.TTA: "blue",
    Mode.POL: "orange",
    Mode.NNF_POL: "purple",
    Mode.NNF_MUTEX_POL: "#4daf4a",
    Mode.LABELNEG_POL: "#377eb8",
    Mode.NOPC_POL: "olive",
    Mode.NOPC_LABELNEG_POL: "cyan",
    Mode.NOPC_NNF_POL: "magenta",
    Mode.NOPC_NNF_MUTEX_POL: "lime",
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


def parse_inputs(input_files: List[str], timeout: Optional[int], timeout_models: Optional[int]) -> pd.DataFrame:
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]
        for result in result_out["results"]:
            result["mode"] = mode
            if result["enum_timed_out"]:
                result["models"] = timeout_models
                result["time"] = timeout

        data.extend(result_out["results"])

    return pd.DataFrame(data)


def group_data(data: pd.DataFrame):
    # aggregate and compute the mean for each query
    data = data \
        .groupby(["filename", "mode"]) \
        .aggregate(time=("time", "min"),
                   models=("models", "min"),
                   n_clauses=("n_clauses", "min"),
                   enum_timed_out=("enum_timed_out", "any"),
                   ) \
        .unstack().reset_index(drop=True)

    # sort by increasing number of models
    modes = data.columns.get_level_values(0).unique()
    modes = [mode for mode in ORDER if mode in modes]

    sort_by = [("models", mode) for mode in modes]
    data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    return data


def parse_args():
    parser = argparse.ArgumentParser(description="Plot results")
    parser.add_argument(
        "input", nargs="+", help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Output folder where to put the plots (default: cwd)")
    parser.add_argument("-f", "--filename", default="",
                        help="Filename suffix (default: '')")
    parser.add_argument("-t", "--timeout", type=int, default=None, help="Timeout (default: None)")
    parser.add_argument("-tm", "--timeout-models", type=int, default=None,
                        help="Number of models to plot for timeouts (default: None)")
    return parser.parse_args()


def count_timeouts(data: pd.DataFrame):
    modes = data.columns.get_level_values(1).unique()
    modes = [mode for mode in ORDER if mode.value in modes]
    for mode in modes:
        n_timeouts = data[("enum_timed_out", mode.value)].sum()
        print(f"{mode}: {n_timeouts} timeouts")


def main():
    args = parse_args()
    inputs: List[str] = args.input
    output_dir: str = args.output
    filename: str = args.filename
    timeout: int = args.timeout
    timeout_models: int = args.timeout_models

    check_output_input(output_dir, "", inputs)

    input_files = get_input_files(inputs)
    data: pd.DataFrame = parse_inputs(input_files, timeout=timeout, timeout_models=timeout_models)
    data: pd.DataFrame = group_data(data)

    ecdf_plotter = ECDFPlotter(data, output_dir, filename, COLOR, [Mode.NNF_MUTEX_POL, Mode.LABELNEG_POL, Mode.LAB],
                               timeout, timeout_models, NAME_MAPPING, LINESTYLES)
    ecdf_plotter.plot_time()

    scatter_plotter = ScatterPlotter(data, output_dir, filename, COLOR, ORDER, timeout, timeout_models, NAME_MAPPING, LINESTYLES)
    scatter_plotter.plot_models_all_vs_all()
    scatter_plotter.plot_time_all_vs_all()
    # scatter_plotter.plot_size_all_vs_all()

    count_timeouts(data)


if __name__ == "__main__":
    main()
