import argparse
import json
import os
import sys
from typing import List, Literal

import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd

from benchmark.utils.fileio import get_input_files, check_output_input
from benchmark.utils.parsing import Mode
from benchmark.utils.plotting.cactus_plotter import CactusPlotter
from benchmark.utils.plotting.scatter_plotter import ScatterPlotter

plt.style.use("ggplot")

ORDER: List[Mode] = [Mode.TTA, Mode.LAB, Mode.NNF_LAB, Mode.POL, Mode.NNF_POL, Mode.CND, Mode.NNF_CND, Mode.EXPAND_CND]

COLOR = {
    Mode.LAB: "red",
    Mode.NNF_LAB: "black",
    Mode.TTA: "blue",
    Mode.POL: "orange",
    Mode.NNF_POL: "purple",
    Mode.CND: "brown",
    Mode.NNF_CND: "teal",
    Mode.EXPAND_CND: "gray",
}


def error(msg=""):
    print(msg)
    sys.exit(1)


def parse_inputs(input_files: List[str], with_repetitions: bool) -> pd.DataFrame:
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]
        if with_repetitions != ("REP" in mode):
            continue
        for result in result_out["results"]:
            result["mode"] = mode
        data.extend(result_out["results"])

    return pd.DataFrame(data)


def group_data(data: pd.DataFrame):
    # aggregate and compute the mean for each query
    data = data \
        .groupby(["filename", "mode"]) \
        .aggregate(time=("time", "min"),
                   models=("models", "min")) \
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
    # parser.add_argument("-r", "--with-repetitions", action="store_true", default=False,
    #                     help="Plot results for TA with repetitions")
    return parser.parse_args()


def main():
    args = parse_args()
    inputs: List[str] = args.input
    output_dir: str = args.output
    filename: str = args.filename

    check_output_input(output_dir, "", inputs)

    input_files = get_input_files(inputs)
    data: pd.DataFrame = parse_inputs(input_files, with_repetitions=False)
    data: pd.DataFrame = group_data(data)

    cactus_plotter = CactusPlotter(data, output_dir, filename, COLOR, ORDER)
    cactus_plotter.plot_models()
    cactus_plotter.plot_time()

    scatter_plotter = ScatterPlotter(data, output_dir, filename, COLOR, ORDER)
    scatter_plotter.plot_models_all_vs_all()
    scatter_plotter.plot_time_all_vs_all()


if __name__ == "__main__":
    main()
